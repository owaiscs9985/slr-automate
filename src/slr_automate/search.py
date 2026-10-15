"""Search connectors for open-access academic databases."""

import requests
import time
import socket
import re
import xml.etree.ElementTree as ET
from typing import List, Dict
from dataclasses import dataclass, asdict


USER_AGENT = "SLR-Automate/0.1 (https://github.com/yourname/slr-automate; mailto:researcher@example.com)"


@dataclass
class Paper:
    """Unified paper record across all sources."""
    title: str
    authors: str
    year: int
    doi: str
    abstract: str
    source: str
    url: str
    venue: str

    def to_dict(self):
        return asdict(self)


def _safe_get(d, *keys, default=""):
    for k in keys:
        if not isinstance(d, dict):
            return default
        d = d.get(k)
    return d if d is not None else default


def _host_reachable(host, port=443, timeout=3.0):
    try:
        socket.create_connection((host, port), timeout=timeout).close()
        return True
    except (OSError, socket.gaierror):
        return False


def _reconstruct_abstract(inverted_index):
    if not inverted_index:
        return ""
    word_positions = []
    for word, positions in inverted_index.items():
        for pos in positions:
            word_positions.append((pos, word))
    word_positions.sort()
    return " ".join(w for _, w in word_positions)


def _get_with_retry(url, params, headers=None, max_retries=3, base_delay=5):
    for attempt in range(max_retries):
        try:
            r = requests.get(url, params=params, headers=headers, timeout=30)
            if r.status_code in (429, 503):
                retry_after = r.headers.get("Retry-After")
                if retry_after and str(retry_after).isdigit():
                    wait = int(retry_after)
                else:
                    wait = base_delay * (2 ** attempt)
                print("[HTTP] Status " + str(r.status_code) + ", retrying in " + str(wait) + "s...")
                time.sleep(wait)
                continue
            r.raise_for_status()
            return r
        except requests.RequestException as e:
            if attempt == max_retries - 1:
                print("[HTTP] Failed after retries: " + str(e))
                return None
            time.sleep(base_delay)
    return None


def search_openalex(query, max_results=100, mailto=None, extra_params=None):
    base_url = "https://api.openalex.org/works"
    papers = []
    per_page = 50
    cursor = "*"
    extra_params = extra_params or {}

    use_mailto = mailto if (mailto and "example.com" not in mailto) else None

    while len(papers) < max_results:
        params = {
            "search": query,
            "per-page": min(per_page, max_results - len(papers)),
            "cursor": cursor,
        }
        if use_mailto:
            params["mailto"] = use_mailto
        if extra_params.get("filter"):
            params["filter"] = extra_params["filter"]

        r = _get_with_retry(base_url, params, headers={"User-Agent": USER_AGENT})
        if r is None:
            break
        data = r.json()

        results = data.get("results", [])
        if not results:
            break

        for item in results:
            authors = ", ".join(
                _safe_get(a, "author", "display_name")
                for a in item.get("authorships", [])[:5]
            )
            abstract = _reconstruct_abstract(item.get("abstract_inverted_index"))
            venue = _safe_get(item, "primary_location", "source", "display_name")
            papers.append(Paper(
                title=item.get("title") or "",
                authors=authors,
                year=item.get("publication_year") or 0,
                doi=(item.get("doi") or "").replace("https://doi.org/", ""),
                abstract=abstract,
                source="OpenAlex",
                url=item.get("id") or "",
                venue=venue,
            ))

        cursor = _safe_get(data, "meta", "next_cursor")
        if not cursor:
            break
        time.sleep(0.2)

    return papers[:max_results]


def search_semantic_scholar(query, max_results=100, api_key=None, extra_params=None):
    host = "api.semanticscholar.org"
    if not _host_reachable(host):
        print("[S2] Host unreachable. Skipping.")
        return []

    base_url = "https://" + host + "/graph/v1/paper/search"
    headers = {"User-Agent": USER_AGENT}
    if api_key:
        headers["x-api-key"] = api_key
    extra_params = extra_params or {}

    papers = []
    offset = 0
    limit = 100

    while len(papers) < max_results:
        params = {
            "query": query,
            "offset": offset,
            "limit": min(limit, max_results - len(papers)),
            "fields": "title,authors,year,abstract,externalIds,venue,url",
        }
        if extra_params.get("year"):
            params["year"] = extra_params["year"]

        try:
            r = requests.get(base_url, params=params, headers=headers, timeout=15)
            if r.status_code == 429:
                print("[S2] Rate limited. Skipping source.")
                return papers
            r.raise_for_status()
            data = r.json()
        except requests.RequestException as e:
            print("[S2] Error: " + str(e))
            break

        results = data.get("data", [])
        if not results:
            break

        for item in results:
            authors = ", ".join(a.get("name", "") for a in (item.get("authors") or [])[:5])
            papers.append(Paper(
                title=item.get("title") or "",
                authors=authors,
                year=item.get("year") or 0,
                doi=(item.get("externalIds") or {}).get("DOI") or "",
                abstract=item.get("abstract") or "",
                source="Semantic Scholar",
                url=item.get("url") or "",
                venue=item.get("venue") or "",
            ))

        offset += len(results)
        if len(results) < limit:
            break
        time.sleep(1)

    return papers[:max_results]


def search_arxiv(query, max_results=100, extra_params=None):
    host = "export.arxiv.org"
    if not _host_reachable(host, port=443):
        print("[arXiv] Host unreachable. Skipping.")
        return []

    base_url = "https://" + host + "/api/query"
    papers = []
    start = 0
    batch = 50

    while len(papers) < max_results:
        params = {
            "search_query": query,
            "start": start,
            "max_results": min(batch, max_results - len(papers)),
        }
        r = _get_with_retry(base_url, params, headers={"User-Agent": USER_AGENT},
                            max_retries=3, base_delay=30)
        if r is None:
            print("[arXiv] Giving up after retries.")
            break

        try:
            root = ET.fromstring(r.content)
        except ET.ParseError as e:
            print("[arXiv] XML parse error: " + str(e))
            break

        ns = {"atom": "http://www.w3.org/2005/Atom"}
        entries = root.findall("atom:entry", ns)
        if not entries:
            break

        for entry in entries:
            title = (entry.findtext("atom:title", "", ns) or "").strip().replace("\n", " ")
            abstract = (entry.findtext("atom:summary", "", ns) or "").strip().replace("\n", " ")
            published = entry.findtext("atom:published", "", ns) or ""
            year = int(published[:4]) if published[:4].isdigit() else 0
            authors = ", ".join(
                a.findtext("atom:name", "", ns) or ""
                for a in entry.findall("atom:author", ns)[:5]
            )
            url = entry.findtext("atom:id", "", ns) or ""
            papers.append(Paper(
                title=title,
                authors=authors,
                year=year,
                doi="",
                abstract=abstract,
                source="arXiv",
                url=url,
                venue="arXiv preprint",
            ))

        start += len(entries)
        if len(entries) < batch:
            break
        time.sleep(5)

    return papers[:max_results]


def search_crossref(query, max_results=100, mailto=None, extra_params=None):
    base_url = "https://api.crossref.org/works"
    papers = []
    rows = 50
    offset = 0
    headers = {"User-Agent": USER_AGENT}
    extra_params = extra_params or {}

    use_mailto = mailto if (mailto and "example.com" not in mailto) else None

    while len(papers) < max_results:
        params = {
            "query": query,
            "rows": min(rows, max_results - len(papers)),
            "offset": offset,
        }
        if use_mailto:
            params["mailto"] = use_mailto
        if extra_params.get("from-pub-date"):
            params["filter"] = "from-pub-date:" + extra_params["from-pub-date"]
        if extra_params.get("until-pub-date"):
            existing = params.get("filter", "")
            sep = "," if existing else ""
            params["filter"] = existing + sep + "until-pub-date:" + extra_params["until-pub-date"]

        r = _get_with_retry(base_url, params, headers=headers)
        if r is None:
            break
        data = r.json()

        items = _safe_get(data, "message", "items", default=[])
        if not items:
            break

        for item in items:
            title_list = item.get("title") or []
            title = title_list[0] if title_list else ""

            authors_list = item.get("author") or []
            authors = ", ".join(
                (a.get("given", "") + " " + a.get("family", "")).strip()
                for a in authors_list[:5]
            )

            year = 0
            date_parts = _safe_get(item, "issued", "date-parts", default=[])
            if date_parts and date_parts[0]:
                year = date_parts[0][0] or 0

            abstract = item.get("abstract") or ""
            if abstract.startswith("<"):
                abstract = re.sub(r"<[^>]+>", "", abstract)

            papers.append(Paper(
                title=title,
                authors=authors,
                year=year,
                doi=item.get("DOI") or "",
                abstract=abstract,
                source="Crossref",
                url=item.get("URL") or "",
                venue=(item.get("container-title") or [""])[0] if item.get("container-title") else "",
            ))

        offset += len(items)
        if len(items) < rows:
            break
        time.sleep(0.5)

    return papers[:max_results]

def search_doaj(query, max_results=100, extra_params=None):
    """Search DOAJ (Directory of Open Access Journals). Free, no key required."""
    host = "doaj.org"
    if not _host_reachable(host, port=443):
        print("[DOAJ] Host unreachable. Skipping.")
        return []

    base_url = "https://" + host + "/api/search/articles/"
    papers = []
    page_size = 100
    page = 1
    extra_params = extra_params or {}

    doaj_query = query
    from_year = extra_params.get("from_year")
    to_year = extra_params.get("to_year")
    if from_year or to_year:
        f = str(from_year or 1900)
        t = str(to_year or 2100)
        doaj_query = "(" + query + ") AND bibjson.year:[" + f + " TO " + t + "]"

    while len(papers) < max_results:
        import urllib.parse
        encoded_query = urllib.parse.quote(doaj_query, safe="")
        url = base_url + encoded_query
        params = {
            "pageSize": min(page_size, max_results - len(papers)),
            "page": page,
        }
        r = _get_with_retry(url, params, headers={"User-Agent": USER_AGENT}, max_retries=3, base_delay=5)
        if r is None:
            break

        try:
            data = r.json()
        except ValueError:
            print("[DOAJ] Invalid JSON response.")
            break

        results = data.get("results", [])
        if not results:
            break

        for item in results:
            bib = item.get("bibjson", {})
            title = bib.get("title") or ""

            author_list = bib.get("author") or []
            authors = ", ".join(a.get("name", "") for a in author_list[:5] if a.get("name"))

            year = 0
            year_str = bib.get("year") or ""
            if str(year_str).isdigit():
                year = int(year_str)

            doi = ""
            for ident in bib.get("identifier", []):
                if ident.get("type") == "doi":
                    doi = ident.get("id", "")
                    break

            abstract = bib.get("abstract") or ""
            if abstract.startswith("<"):
                abstract = re.sub(r"<[^>]+>", "", abstract)

            links = bib.get("link") or []
            url = ""
            for link in links:
                if link.get("type") == "fulltext":
                    url = link.get("url", "")
                    break
            if not url and links:
                url = links[0].get("url", "")

            venue = ""
            journal = bib.get("journal") or {}
            if journal:
                venue = journal.get("title", "") or ""

            papers.append(Paper(
                title=title,
                authors=authors,
                year=year,
                doi=doi,
                abstract=abstract,
                source="DOAJ",
                url=url,
                venue=venue,
            ))

        total = data.get("total", 0)
        if page * page_size >= total:
            break
        page += 1
        time.sleep(0.5)

    return papers[:max_results]

def search_europepmc(query, max_results=100, extra_params=None):
    """Search Europe PMC. Free, no API key required."""
    host = "www.ebi.ac.uk"
    if not _host_reachable(host, port=443):
        print("[EuropePMC] Host unreachable. Skipping.")
        return []

    base_url = "https://" + host + "/europepmc/webservices/rest/search"
    papers = []
    page_size = 100
    cursor = "*"
    extra_params = extra_params or {}

    epmc_query = query
    from_year = extra_params.get("from_year")
    to_year = extra_params.get("to_year")
    if from_year or to_year:
        f_y = str(from_year or 1900)
        t_y = str(to_year or 2100)
        epmc_query = "(" + query + ") AND (PUB_YEAR:[" + f_y + " TO " + t_y + "])"

    while len(papers) < max_results:
        params = {
            "query": epmc_query,
            "format": "json",
            "pageSize": min(page_size, max_results - len(papers)),
            "cursorMark": cursor,
            "resultType": "core",
        }
        r = _get_with_retry(base_url, params, headers={"User-Agent": USER_AGENT}, max_retries=3, base_delay=5)
        if r is None:
            break

        try:
            data = r.json()
        except ValueError:
            print("[EuropePMC] Invalid JSON response.")
            break

        results = _safe_get(data, "resultList", "result", default=[])
        if not results:
            break

        for item in results:
            title = item.get("title") or ""
            author_string = item.get("authorString") or ""
            authors = ", ".join([a.strip() for a in author_string.split(",")[:5] if a.strip()])
            year = 0
            pub_year = item.get("pubYear") or ""
            if str(pub_year).isdigit():
                year = int(pub_year)
            doi = item.get("doi") or ""
            abstract = item.get("abstractText") or ""
            if abstract.startswith("<"):
                abstract = re.sub(r"<[^>]+>", "", abstract)
            venue = ""
            if isinstance(item.get("journalInfo"), dict):
                venue = item.get("journalInfo", {}).get("journal", {}).get("title", "")
            url = ""
            if doi:
                url = "https://doi.org/" + doi
            elif item.get("pmid"):
                url = "https://pubmed.ncbi.nlm.nih.gov/" + str(item.get("pmid"))
            papers.append(Paper(
                title=title,
                authors=authors,
                year=year,
                doi=doi,
                abstract=abstract,
                source="Europe PMC",
                url=url,
                venue=venue,
            ))

        next_cursor = data.get("nextCursorMark")
        if not next_cursor or next_cursor == cursor:
            break
        cursor = next_cursor
        time.sleep(0.5)

    return papers[:max_results]
