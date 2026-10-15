"""SLR-Automate Streamlit GUI with dashboard."""

import streamlit as st
import pandas as pd
import yaml
import tempfile
import io
import contextlib
from pathlib import Path

from src.slr_automate.cli import run as run_pipeline
from src.slr_automate.query_builder import build_canonical_query
from src.slr_automate import dashboard as dash


st.set_page_config(page_title="SLR-Automate", layout="wide")

st.title("SLR-Automate")
st.caption("Automated Systematic Literature Review pipeline")

tab_pipeline, tab_dashboard, tab_results = st.tabs(["Pipeline", "Dashboard", "Results"])


# ============================================================
# TAB 1: PIPELINE
# ============================================================
with tab_pipeline:
    st.sidebar.header("Sources")
    use_openalex = st.sidebar.checkbox("OpenAlex", value=True)
    use_crossref = st.sidebar.checkbox("Crossref", value=True)
    use_s2 = st.sidebar.checkbox("Semantic Scholar", value=False)
    use_arxiv = st.sidebar.checkbox("arXiv", value=True)
    s2_key = st.sidebar.text_input("Semantic Scholar API key (optional)", type="password")

    st.sidebar.header("Retrieval")
    max_per_source = st.sidebar.slider("Max results per source", 10, 200, 50, step=10)

    st.sidebar.header("Year range")
    use_year = st.sidebar.checkbox("Filter by year", value=True)
    from_year = st.sidebar.number_input("From year", 1900, 2100, 2018) if use_year else None
    to_year = st.sidebar.number_input("To year", 1900, 2100, 2024) if use_year else None

    st.sidebar.header("Screening")
    min_matches = st.sidebar.slider("Minimum include keyword matches", 1, 5, 2)

    st.header("Query Builder")

    if "concepts" not in st.session_state:
        st.session_state.concepts = [
            {"name": "reinforcement learning", "synonyms": "RL, Q-learning, deep reinforcement learning"},
            {"name": "MAC protocol", "synonyms": "medium access control, MAC layer"},
            {"name": "wireless sensor network", "synonyms": "WSN, sensor network"},
        ]

    col1, col2 = st.columns([3, 1])
    with col2:
        if st.button("Add concept"):
            st.session_state.concepts.append({"name": "", "synonyms": ""})
            st.rerun()
        if st.button("Clear all"):
            st.session_state.concepts = [{"name": "", "synonyms": ""}]
            st.rerun()

    with col1:
        concepts_dict = {}
        for i, c in enumerate(st.session_state.concepts):
            cc1, cc2, cc3 = st.columns([2, 3, 1])
            with cc1:
                name = st.text_input("Concept " + str(i + 1), value=c["name"], key="cname_" + str(i))
            with cc2:
                syns = st.text_input("Synonyms (comma-separated)", value=c["synonyms"], key="csyn_" + str(i))
            with cc3:
                st.write("")
                st.write("")
                if st.button("Remove", key="rm_" + str(i)) and len(st.session_state.concepts) > 1:
                    st.session_state.concepts.pop(i)
                    st.rerun()

            if name.strip():
                syn_list = [s.strip() for s in syns.split(",") if s.strip()]
                concepts_dict[name.strip()] = syn_list

    if concepts_dict:
        canonical = build_canonical_query(concepts_dict)
        st.subheader("Generated boolean query")
        st.code(canonical, language="text")

    st.header("Screening keywords")
    kw1, kw2 = st.columns(2)
    with kw1:
        include_text = st.text_area(
            "Include keywords (one per line)",
            value="reinforcement learning\nMAC protocol\nwireless sensor network\nWSN\nduty cycle\nenergy efficiency\nmedium access control",
            height=180,
        )
    with kw2:
        exclude_text = st.text_area(
            "Exclude keywords (one per line)",
            value="editorial\nerratum\nretraction",
            height=180,
        )

    st.header("Run")
    output_dir = st.text_input("Output folder", value="gui_output")

    include_kw_check = [l.strip() for l in include_text.splitlines() if l.strip()]

    if not include_kw_check and min_matches > 1:
        st.warning("You set minimum matches to " + str(min_matches) + " but provided 0 include keywords. Screening will include everything. Either add include keywords or set the minimum to 1.")

    if st.button("Run SLR pipeline", type="primary"):
        if not concepts_dict:
            st.error("Please add at least one concept before running.")
        else:
            sources = []
            if use_openalex:
                sources.append("openalex")
            if use_crossref:
                sources.append("crossref")
            if use_s2:
                sources.append("semantic_scholar")
            if use_arxiv:
                sources.append("arxiv")

            include_kw = [l.strip() for l in include_text.splitlines() if l.strip()]
            exclude_kw = [l.strip() for l in exclude_text.splitlines() if l.strip()]

            cfg = {
                "concepts": concepts_dict,
                "from_year": int(from_year) if from_year else None,
                "to_year": int(to_year) if to_year else None,
                "max_per_source": int(max_per_source),
                "sources": sources,
                "output_dir": output_dir,
                "include_keywords": include_kw,
                "exclude_keywords": exclude_kw,
                "min_include_matches": int(min_matches),
            }
            if s2_key:
                cfg["semantic_scholar_api_key"] = s2_key

            tmp_cfg = Path(tempfile.gettempdir()) / "slr_automate_gui_config.yaml"
            with open(tmp_cfg, "w", encoding="utf-8") as f:
                yaml.safe_dump(cfg, f, allow_unicode=True)

            st.subheader("Progress")
            buf = io.StringIO()
            try:
                with contextlib.redirect_stdout(buf):
                    run_pipeline(str(tmp_cfg))
                progress_lines = buf.getvalue().splitlines()
            except Exception as e:
                progress_lines = buf.getvalue().splitlines() + ["ERROR: " + str(e)]

            st.code("\n".join(progress_lines[-40:]), language="text")
            st.success("Pipeline finished. Check the Dashboard and Results tabs.")


# ============================================================
# TAB 2: DASHBOARD
# ============================================================
with tab_dashboard:
    st.header("Descriptive analysis")

    dash_dir = st.text_input("Results folder for dashboard", value="gui_output", key="dash_dir")

    df_all = dash.load_results(str(Path(dash_dir) / "results_all.csv"))
    df_inc = dash.load_results(str(Path(dash_dir) / "results_included.csv"))

    if df_inc.empty and df_all.empty:
        st.info("No results found. Run the pipeline first, or check the folder path.")
    else:
        st.subheader("Which results to visualize?")
        which = st.radio("Choose dataset", ["Included only", "All deduplicated"],
                         horizontal=True, key="which_data")
        df = df_inc if which == "Included only" else df_all

        if df.empty:
            st.warning("The selected dataset is empty.")
        else:
            m = dash.summary_metrics(df)
            c1, c2, c3, c4 = st.columns(4)
            c1.metric("Total papers", m["total"])
            c2.metric("Year range", m["years"])
            c3.metric("Sources", m["sources"])
            c4.metric("Unique venues", m["venues"])

            st.divider()

            r1c1, r1c2 = st.columns(2)
            with r1c1:
                fig = dash.chart_papers_per_year(df)
                if fig:
                    st.plotly_chart(fig, use_container_width=True)
            with r1c2:
                fig = dash.chart_papers_per_source(df)
                if fig:
                    st.plotly_chart(fig, use_container_width=True)

            fig = dash.chart_year_source_heatmap(df)
            if fig:
                st.plotly_chart(fig, use_container_width=True)

            r2c1, r2c2 = st.columns(2)
            with r2c1:
                fig = dash.chart_top_venues(df, 10)
                if fig:
                    st.plotly_chart(fig, use_container_width=True)
            with r2c2:
                fig = dash.chart_top_authors(df, 10)
                if fig:
                    st.plotly_chart(fig, use_container_width=True)

            fig = dash.chart_keyword_frequency(df, 20)
            if fig:
                st.plotly_chart(fig, use_container_width=True)


# ============================================================
# TAB 3: RESULTS
# ============================================================
with tab_results:
    st.header("Results table")
    res_dir = st.text_input("Results folder", value="gui_output", key="res_dir")
    res_file = st.radio("Show", ["Included only", "All deduplicated"], horizontal=True, key="res_which")

    filename = "results_included.csv" if res_file == "Included only" else "results_all.csv"
    csv_path = Path(res_dir) / filename
    xlsx_path = Path(res_dir) / "results_included.xlsx"

    if not csv_path.exists():
        st.info("No results file found at " + str(csv_path))
    else:
        df = pd.read_csv(csv_path, encoding="utf-8")
        st.write("Rows: " + str(len(df)))

        search_term = st.text_input("Filter by title contains...")
        if search_term:
            df = df[df["title"].str.contains(search_term, case=False, na=False)]
            st.write("Filtered rows: " + str(len(df)))

        cols_to_show = [c for c in ["title", "authors", "year", "source", "venue", "doi"] if c in df.columns]
        st.dataframe(df[cols_to_show], use_container_width=True, height=500)

        st.subheader("Downloads")
        dl1, dl2 = st.columns(2)
        with dl1:
            with open(csv_path, "rb") as f:
                st.download_button("Download CSV", f.read(),
                                   file_name=filename, mime="text/csv")
        with dl2:
            if xlsx_path.exists():
                with open(xlsx_path, "rb") as f:
                    st.download_button("Download Excel", f.read(),
                                       file_name="results_included.xlsx",
                                       mime="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet")

        prisma_path = Path(res_dir) / "prisma_flow.png"
        if prisma_path.exists():
            st.subheader("PRISMA diagram")
            st.image(str(prisma_path), use_container_width=True)
