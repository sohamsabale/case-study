import streamlit as st
import pandas as pd

# Colors for product tiles
product_colors = {
    "Mailchimp": "#FFE01B",
    "TurboTax": "#355ebe",
    "QuickBook": "#14324F",
    "Mint": "#3EB489"
}

# Sample data for metrics
metrics_data = {
    "Product": ["Mailchimp", "TurboTax", "QuickBook", "Mint"],
    "Active Users": [2059, 1994, 2145, 2043],
    "Churn Rate (%)": [25, 24, 24, 23],
}

# Create a DataFrame for metrics
metrics_df = pd.DataFrame(metrics_data)

# Streamlit app with tabs
st.title("Intuit Dashboard")

tab1, tab2 = st.tabs(["Intuit Overview", "Mailchimp Deep Dive"])

# Tab 1: Intuit Overview
with tab1:
    st.header("Intuit Overview")
    st.markdown("### Executive Dashboard")

    # Create the grid header with icons
    rows = st.columns([1.5, 1, 1, 1, 1])  # Adjust ratios to make the product column wider
    with rows[0]:
        st.markdown("<p style='text-align:center; font-weight:bold; font-size:16px;'>Product</p>", unsafe_allow_html=True)
    with rows[1]:
        st.markdown("<p style='text-align:center; font-weight:bold; font-size:16px;'>👥 Active Users</p>", unsafe_allow_html=True)
    with rows[2]:
        st.markdown("<p style='text-align:center; font-weight:bold; font-size:16px;'>📉 Churn Rate</p>", unsafe_allow_html=True)
    with rows[3]:
        st.markdown("<p style='text-align:center; font-weight:bold; font-size:16px;'>🚀 Coming Soon</p>", unsafe_allow_html=True)
    with rows[4]:
        st.markdown("<p style='text-align:center; font-weight:bold; font-size:16px;'>🔍 Insights</p>", unsafe_allow_html=True)

    # Loop through each product to populate the grid
    for i, product in enumerate(metrics_df["Product"]):
        rows = st.columns([1, 1, 1, 1, 1])  # Wider first column for product names

        # Product Name tile
        with rows[0]:
            st.markdown(
                f"""
                <div style='background-color:#FFFFFF; display: flex; justify-content: center; align-items: center; border-radius: 10px; border: 1px solid #d3d3d3; width:100%; padding:20px;'>
                    <h3 style='text-align:center; color:black; font-size:18px;'>{product}</h3>
                </div>
                """,
                unsafe_allow_html=True,
            )

        # Active Users tile
        with rows[1]:
            st.markdown(
                f"""
                <div style='background-color:{product_colors[product]}; display: flex; justify-content: center; align-items: center; border-radius: 10px; width:100%; padding:20px;'>
                    <h3 style='text-align:center; color:black; font-size:25px;'>{metrics_df.loc[i, 'Active Users']:,}</h3>
                </div>
                """,
                unsafe_allow_html=True,
            )

        # Churn Rate tile
        with rows[2]:
            st.markdown(
                f"""
                <div style='background-color:{product_colors[product]}; display: flex; justify-content: center; align-items: center; border-radius: 10px; width:100%; padding:20px;'>
                    <h3 style='text-align:center; color:black; font-size:25px;'>{metrics_df.loc[i, 'Churn Rate (%)']}%</h3>
                </div>
                """,
                unsafe_allow_html=True,
            )

        # Placeholder for additional metrics
        with rows[3]:
            st.markdown(
                f"""
                <div style='background-color:#e0e0e0; display: flex; justify-content: center; align-items: center; border-radius: 10px; width:100%; padding:20px;'>
                    <h3 style='text-align:center; color:black; font-size:25px;'>-</h3>
                </div>
                """,
                unsafe_allow_html=True,
            )

        # Placeholder for insights
        with rows[4]:
            st.markdown(
                f"""
                <div style='background-color:#e0e0e0; display: flex; justify-content: center; align-items: center; border-radius: 10px; width:100%; padding:20px;'>
                    <h3 style='text-align:center; color:black; font-size:25px;'>-</h3>
                </div>
                """,
                unsafe_allow_html=True,
            )

        # Add vertical space between rows
        st.markdown("<div style='height:30px;'></div>", unsafe_allow_html=True)

# Tab 2: Mailchimp Deep Dive
with tab2:
    st.header("Mailchimp Deep Dive")
    st.markdown("### Coming Soon")
