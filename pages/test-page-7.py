# --------------------------- Performance Metrics Styling --------------------------- #

# Custom CSS for Glassmorphism effect
st.markdown("""
    <style>
    /* Glassmorphism Metric Card */
    .metric-card {
        background: rgba(255, 255, 255, 0.05);
        backdrop-filter: blur(10px);
        border: 1px solid rgba(255, 255, 255, 0.1);
        border-radius: 20px;
        padding: 20px;
        margin: 10px 0;
        transition: transform 0.3s ease;
        text-align: center;
        box-shadow: 0 8px 32px 0 rgba(0, 0, 0, 0.1);
    }

    .metric-card:hover {
        transform: translateY(-5px);
    }

    .metric-label {
        font-size: 0.85rem;
        color: rgba(255, 255, 255, 0.6);
        letter-spacing: 0.1em;
        text-transform: uppercase;
    }

    .metric-value {
        font-size: 1.8rem;
        font-weight: 700;
        color: #ffffff;
        margin: 8px 0;
    }

    .metric-trend {
        font-size: 0.85rem;
        display: flex;
        justify-content: center;
        align-items: center;
        gap: 5px;
    }
    </style>
""", unsafe_allow_html=True)

# --------------------------- Fetch and Display Performance Metrics --------------------------- #

if go_clicked:
    metrics = fetch_performance_metrics(symbol)
    if metrics:
        st.subheader("Performance Metrics")

        # Define color and trend arrows based on values
        win_percent = metrics["win_percentage"]
        total_trades = metrics["total_trades"]
        profit_factor = metrics["profit_factor"]

        win_color = "#00ff9f" if win_percent >= 50 else "#ff4b4b"
        profit_color = "#00ff9f" if profit_factor > 1 else "#ff4b4b"

        # Create a 3-column layout
        col1, col2, col3 = st.columns(3)

        with col1:
            st.markdown(f"""
                <div class="metric-card">
                    <div class="metric-label">Win %</div>
                    <div class="metric-value" style="color: {win_color};">{win_percent}%</div>
                </div>
            """, unsafe_allow_html=True)

        with col2:
            st.markdown(f"""
                <div class="metric-card">
                    <div class="metric-label">No. of Trades</div>
                    <div class="metric-value">{total_trades}</div>
                </div>
            """, unsafe_allow_html=True)

        with col3:
            profit_trend = "↑" if profit_factor > 1 else "↓"
            st.markdown(f"""
                <div class="metric-card">
                    <div class="metric-label">Profit Factor</div>
                    <div class="metric-value" style="color: {profit_color};">{profit_factor}</div>
                    <div class="metric-trend" style="color: {profit_color};">
                        {profit_trend}
                    </div>
                </div>
            """, unsafe_allow_html=True)

# --------------------------- Ensure Table Display --------------------------- #

    cumulative_pl_df = fetch_cumulative_pl(symbol)
    if cumulative_pl_df is not None and not cumulative_pl_df.empty:
        st.subheader("Equity Curve")  # Keep existing title
        st.plotly_chart(create_cumulative_pl_chart(cumulative_pl_df), use_container_width=True)
    
    for tab, model_name in zip(tabs, ["gtrends", "news", "twitter", "overall"]):
        with tab:
            st.subheader(f"{model_name.capitalize()} Data")
            df = fetch_model_data(symbol, model_name)
            if df is not None and not df.empty:
                st.dataframe(df, use_container_width=True)
            else:
                st.warning(f"No data found for {model_name.capitalize()}.")
