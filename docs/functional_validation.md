| Test ID | Objective | Expected Result | Result |
|---|---|---|---|
| FT-01 | Query builder - canonical boolean | Valid boolean with quotes and AND | Pass |
| FT-02 | Query builder - plain keyword | Space-joined keywords, no booleans | Pass |
| FT-03 | Query builder - simple OR | "a" OR "b" | Pass |
| FT-04 | Query builder - per-source adaptation | DOAJ receives simple OR + year params | Pass |
| FT-05 | Deduplication - by DOI | Identical DOI merged | Pass |
| FT-06 | Deduplication - by title | Case-insensitive title merge | Pass |
| FT-07 | Screening - include/exclude | 1 in, 1 out | Pass |
| FT-08 | Screening - minimum match threshold | Only 2-match paper included | Pass |
| FT-09 | BibTeX - citation key format | khan2024reinforcement | Pass |
| FT-10 | BibTeX - @article entry | Valid @article block | Pass |
| FT-11 | Abstract truncation - default 300 chars | Truncated with ellipsis | Pass |
| FT-12 | Abstract truncation - disabled | Full text preserved when 0 | Pass |
| FT-13 | PRISMA diagram rendering | PNG > 10 KB produced | Pass |
| FT-14 | Search connectors - all 6 importable | All callables present | Pass |
| FT-15 | OpenAlex live search | Returns >0 papers | Pass |
| FT-16 | Crossref live search | Returns >0 papers | Pass |
| FT-17 | DOAJ live search | Returns >0 papers | Pass |
| FT-18 | Europe PMC live search | Returns >0 papers | Pass |