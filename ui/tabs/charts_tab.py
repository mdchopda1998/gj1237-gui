import streamlit as st


def render(config: dict, results):
    if results is None:
        st.info("Set your parameters and click **Run Analysis** to see charts.")
        return
    if getattr(results, "error", None) or not results.figures:
        st.info("No charts to show - see the error above, or try different settings.")
        return

    st.subheader(f"{config['ticker']} - Zones & Price Action")

    tf_labels = {"1d": "Daily", "1wk": "Weekly", "1mo": "Monthly"}
    tf_tabs = st.tabs(list(tf_labels.values()))

    for (tf_key, tf_label), tf_tab in zip(tf_labels.items(), tf_tabs):
        with tf_tab:
            fig = results.figures.get(tf_key)
            if fig is None:
                st.info(f"No {tf_label.lower()} data available.")
                continue
            st.plotly_chart(fig, use_container_width=True)

            zone_df = results.zones.get(tf_key)
            if zone_df is not None:
                n_zones = int(zone_df["Zone_Created"].sum())
                source = results.data_sources.get(tf_key, "unknown")
                source_note = {
                    "csv": "local saved CSV",
                    "live": "live yfinance fetch",
                    "synthetic": "synthetic placeholder - no CSV found and live fetch failed",
                }.get(source, source)
                st.caption(f"{n_zones} zone(s) identified · data source: {source_note}")
