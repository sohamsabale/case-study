import streamlit as st
import plotly.graph_objects as go
import plotly.graph_objects as go
from plotly.subplots import make_subplots

import pandas as pd

import pandas as pd

# Load the datasets
customer_data = pd.read_csv("data/customer_data.csv", low_memory=False)
usage_data = pd.read_csv("data/usage_data.csv", low_memory=False)

# Define the North Star Metrics for each product
north_star_metrics = {
    "TurboTax": "Tax Filings Completed",
    "Mailchimp": "Email Campaigns Successfully Sent",
    "Mint": "Active Budget Plans",
    "QuickBooks": "Invoices Paid"
}

# Map the North Star metric actions for easier aggregation
action_keys = {
    3: "Filing Completed",
    2: "Email Campaigns Sent",
    5: "Budget Created",
    5: "Invoice Created"  # Assuming Invoice Created is also key 5 for QuickBooks
}

# Map action type IDs to names in usage_data
usage_data["Action_Type"] = usage_data["action_type_id"].map(action_keys)


# Calculate lifetime activated customers (first_activation_date is not null)
lifetime_activated_customers = customer_data[~customer_data['first_activation_date'].isna()]
lifetime_activated_by_product = lifetime_activated_customers.groupby('product_name').size()

# Calculate current active customers (first_activation_date is not null and cancel_date is null)
current_active_customers = customer_data[
    (~customer_data['first_activation_date'].isna()) & (customer_data['cancel_date'].isna())
]
current_active_by_product = current_active_customers.groupby('product_name').size()

# Calculate churned users by product
churned_users_by_product = customer_data[~customer_data['cancel_date'].isna()].groupby('product_name').size()

# Calculate churn rate: churned users / lifetime activated customers
churn_rate_by_product = (churned_users_by_product / lifetime_activated_by_product * 100).fillna(0)



# Prepare the customer_summary DataFrame
customer_summary = pd.DataFrame({
    "Lifetime_Activated_Customers": lifetime_activated_by_product,
    "Current_Active_Customers": current_active_by_product,
    "Churn_Rate (%)": churn_rate_by_product
}).fillna(0).astype({
    "Lifetime_Activated_Customers": int,
    "Current_Active_Customers": int,
    "Churn_Rate (%)": float
})

# Add the North Star Metric description
customer_summary["NorthStar_Metric"] = customer_summary.index.map(north_star_metrics)

# Debug: Inspect intermediate outputs
print("Lifetime Activated Customers By Product:")
print(lifetime_activated_by_product)

# Group by product name and calculate the sum of the usage counts for the relevant actions
north_star_values = usage_data.groupby(["product_name", "Action_Type"])["usage_count"].sum().reset_index()

# Debug: Check north_star_values
print("\nNorth Star Values Before Filtering:")
print(north_star_values)

# Extract the relevant North Star metric counts for each product
north_star_actuals = north_star_values[north_star_values["Action_Type"].isin(action_keys.values())]
north_star_actuals = north_star_actuals.groupby("product_name")["usage_count"].sum()

# Debug: Check north_star_actuals
print("\nNorth Star Actuals After Filtering:")
print(north_star_actuals)

# Normalize indices for mapping
north_star_actuals.index = north_star_actuals.index.str.strip()
customer_summary.index = customer_summary.index.str.strip()

# Map North Star Metric Value
customer_summary["NorthStar_Metric_Value"] = customer_summary.index.map(north_star_actuals).fillna(0).astype(int)

# Reset index for better readability
customer_summary.reset_index(inplace=True)

# Debug: Final customer_summary DataFrame
print("\nFinal Customer Summary:")
print(customer_summary)


data = customer_summary

# Product tile colors
product_colors = {
    "Mailchimp": "#FFE01B",
    "TurboTax": "#355ebe",
    "QuickBooks": "#14324F",
    "Mint": "#3EB489"
}

# Lifetime NorthStar Metric Descriptions
descriptions = {
    "Mailchimp": "Total emails campaigns successfully sent by all users.",
    "TurboTax": "Total tax forms filed by all users.",
    "QuickBooks": "Total invoices paid by all users.",
    "Mint": "Total budgets created by all users."
}

mailchimp_actions_key = {
    5: "Campaigns Started", 
    7: "Campaigns Created",
    4: "Subscribers Added",
    3: "Templates Edited",
    2: "Email Campaigns Sent", 
    1: "Campaigns Deleted",
    6: "Forms Drafted"
}
mailchimp_data = customer_data[customer_data["product_name"] == "Mailchimp"]
mailchimp_usage = usage_data[usage_data['product_name'] == 'Mailchimp']


# Count the occurrences of each action ID using the correct column name
mailchimp_action_counts = mailchimp_usage['action_type_id'].value_counts()

# Map the action IDs to their names using the provided key
mailchimp_funnel = mailchimp_action_counts.rename(index=mailchimp_actions_key)

# Sort actions by their frequency in descending order
mailchimp_funnel = mailchimp_funnel.sort_values(ascending=False)

# Filter data for Mailchimp
mailchimp_data = customer_data[customer_data["product_name"] == "Mailchimp"]

# Recalculate start and end dates
start_date = pd.Timestamp("2021-05-01")
end_date = pd.Timestamp("2022-06-30")
full_date_range = pd.date_range(start=start_date, end=end_date, freq="D")

# Convert dates to datetime format
mailchimp_data["first_activation_date"] = pd.to_datetime(
    mailchimp_data["first_activation_date"], errors="coerce"
)
mailchimp_data["cancel_date"] = pd.to_datetime(
    mailchimp_data["cancel_date"], errors="coerce"
)

# Debug: Check unique dates in the data
print("Unique First Activation Dates:")
print(mailchimp_data["first_activation_date"].dropna().unique())
print("\nUnique Cancel Dates:")
print(mailchimp_data["cancel_date"].dropna().unique())

# Group by and calculate cumulative activated customers
grouped_activated_customers = mailchimp_data.groupby("first_activation_date").size()
cumulative_activated_customers_mailchimp = grouped_activated_customers.reindex(full_date_range, fill_value=0).cumsum()

# Debug: Check intermediate results for activated customers
print("\nGrouped Activated Customers:")
print(grouped_activated_customers)
print("\nCumulative Activated Customers:")
print(cumulative_activated_customers_mailchimp.head())

# Group by and calculate cumulative cancelled customers
grouped_cancelled_customers = mailchimp_data.groupby("cancel_date").size()
cumulative_cancelled_customers_mailchimp = grouped_cancelled_customers.reindex(full_date_range, fill_value=0).cumsum()

# Debug: Check intermediate results for cancelled customers
print("\nGrouped Cancelled Customers:")
print(grouped_cancelled_customers)
print("\nCumulative Cancelled Customers:")
print(cumulative_cancelled_customers_mailchimp.head())

# Calculate daily active customers
active_customers_daily_mailchimp = cumulative_activated_customers_mailchimp - cumulative_cancelled_customers_mailchimp

# Debug: Check final active customers
print("\nActive Customers Daily (Mailchimp):")
print(active_customers_daily_mailchimp.head())



# Streamlit App
st.title("Intuit Dashboard")

# Create tab for Intuit Overview
tab1, tab2 = st.tabs(["Intuit Overview", "Mailchimp Deep Dive"])

with tab1:
    st.header("Intuit Overview")
    st.markdown("### Executive Dashboard")

    # Create the grid headers
    rows = st.columns([1, 1, 1, 1, 1])
    with rows[0]:
        st.markdown("<p style='text-align:center; font-weight:bold; font-size:16px;'>Product</p>", unsafe_allow_html=True)
    with rows[1]:
        st.markdown("<p style='text-align:center; font-weight:bold; font-size:16px;'>👥 Lifetime Activated</p>", unsafe_allow_html=True)
    with rows[2]:
        st.markdown("<p style='text-align:center; font-weight:bold; font-size:16px;'>Current Active</p>", unsafe_allow_html=True)
    with rows[3]:
        st.markdown("<p style='text-align:center; font-weight:bold; font-size:16px;'>📉Churn Rate</p>", unsafe_allow_html=True)
    with rows[4]:
        st.markdown("<p style='text-align:center; font-weight:bold; font-size:16px;'>Lifetime NorthStar Metric</p>", unsafe_allow_html=True)

    # Loop through products to create tiles
    for i, row in data.iterrows():
        rows = st.columns([1, 1, 1, 1, 1])

        # Product name tile
        with rows[0]:
            st.markdown(
                f"""
                <div style='background-color:#FFFFFF; display: flex; justify-content: center; align-items: center; border-radius: 10px; border: 1px solid #d3d3d3; width:100%; height:150px; padding:20px;'>
                    <h3 style='text-align:center; color:black; font-size:16px;'>{row['product_name']}</h3>
                </div>
                """,
                unsafe_allow_html=True,
            )

        # Lifetime Activated Customers tile
        with rows[1]:
            st.markdown(
                f"""
                <div style='background-color:{product_colors[row['product_name']]}; display: flex; justify-content: center; align-items: center; flex-direction: column; border-radius: 10px; width:100%; height:150px; padding:20px;'>
                    <h3 style='text-align:center; color:white; font-size:22px; font-weight:bold; text-shadow: 0px 0px 1px black;'>{row['Lifetime_Activated_Customers']:,}</h3>
                </div>
                """,
                unsafe_allow_html=True,
            )

        # Current Active Customers tile
        with rows[2]:
            st.markdown(
                f"""
                <div style='background-color:{product_colors[row['product_name']]}; display: flex; justify-content: center; align-items: center; flex-direction: column; border-radius: 10px; width:100%; height:150px; padding:20px;'>
                    <h3 style='text-align:center; color:white; font-size:22px; font-weight:bold; text-shadow: 0px 0px 1px black;'>{row['Current_Active_Customers']:,}</h3>
                </div>
                """,
                unsafe_allow_html=True,
            )

        # Churn Rate tile
        with rows[3]:
            st.markdown(
                f"""
                <div style='background-color:{product_colors[row['product_name']]}; display: flex; justify-content: center; align-items: center; flex-direction: column; border-radius: 10px; width:100%; height:150px; padding:20px;'>
                    <h3 style='text-align:center; color:white; font-size:22px; font-weight:bold; text-shadow: 0px 0px 1px black;'>{row['Churn_Rate (%)']:.2f}%</h3>
                </div>
                """,
                unsafe_allow_html=True,
            )

        # Lifetime NorthStar Metric tile
        with rows[4]:
            st.markdown(
                f"""
                <div style='background-color:{product_colors[row['product_name']]}; display: flex; flex-direction: column; justify-content: center; align-items: center; border-radius: 10px; width:100%; height:150px; padding:20px;'>
                    <h3 style='text-align:center; color:white; font-size:22px; font-weight:bold; text-shadow: 0px 0px 1px black;'>{row['NorthStar_Metric_Value']:,}</h3>
                    <h6 style='text-align:center; color:white; font-size:14px; margin-top:0.5px;'>{descriptions[row['product_name']]}</h6>
                </div>
                """,
                unsafe_allow_html=True,
            )

        # Add vertical space between rows
        st.markdown("<div style='height:20px;'></div>", unsafe_allow_html=True)

with tab2:
    st.header("Mailchimp Deep Dive")

    # Wireframe for tiles
    st.markdown("### Metrics Overview")
    rows = st.columns([1, 1, 1, 1, 1])

    # Create the grid headers for tiles
    with rows[0]:
        st.markdown("<p style='text-align:center; font-weight:bold; font-size:16px;'>Product</p>", unsafe_allow_html=True)
    with rows[1]:
        st.markdown("<p style='text-align:center; font-weight:bold; font-size:16px;'>Lifetime Activated</p>", unsafe_allow_html=True)
    with rows[2]:
        st.markdown("<p style='text-align:center; font-weight:bold; font-size:16px;'>Current Active</p>", unsafe_allow_html=True)
    with rows[3]:
        st.markdown("<p style='text-align:center; font-weight:bold; font-size:16px;'>Churn Rate</p>", unsafe_allow_html=True)
    with rows[4]:
        st.markdown("<p style='text-align:center; font-weight:bold; font-size:16px;'>Lifetime NorthStar Metric</p>", unsafe_allow_html=True)

    # Populate the tiles with color
    for i, row in data[data['product_name'] == "Mailchimp"].iterrows():
        rows = st.columns([1, 1, 1, 1, 1])

        # Product name tile
        with rows[0]:
            st.markdown(
                f"""
                <div style='background-color:#FFFFFF; display: flex; justify-content: center; align-items: center; border-radius: 10px; border: 1px solid #d3d3d3; width:100%; height:150px; padding:20px;'>
                    <h3 style='text-align:center; color:black; font-size:18px;'>{row['product_name']}</h3>
                </div>
                """,
                unsafe_allow_html=True,
            )

        # Lifetime Activated Customers tile
        with rows[1]:
            st.markdown(
                f"""
                <div style='background-color:{product_colors[row['product_name']]}; display: flex; justify-content: center; align-items: center; flex-direction: column; border-radius: 10px; width:100%; height:150px; padding:20px;'>
                    <h3 style='text-align:center; color:white; font-size:22px; font-weight:bold; text-shadow: 0px 0px 1px black;'>{row['Lifetime_Activated_Customers']:,}</h3>
                </div>
                """,
                unsafe_allow_html=True,
            )

        # Current Active Customers tile
        with rows[2]:
            st.markdown(
                f"""
                <div style='background-color:{product_colors[row['product_name']]}; display: flex; justify-content: center; align-items: center; flex-direction: column; border-radius: 10px; width:100%; height:150px; padding:20px;'>
                    <h3 style='text-align:center; color:white; font-size:22px; font-weight:bold; text-shadow: 0px 0px 1px black;'>{row['Current_Active_Customers']:,}</h3>
                </div>
                """,
                unsafe_allow_html=True,
            )

        # Churn Rate tile
        with rows[3]:
            st.markdown(
                f"""
                <div style='background-color:{product_colors[row['product_name']]}; display: flex; justify-content: center; align-items: center; flex-direction: column; border-radius: 10px; width:100%; height:150px; padding:20px;'>
                    <h3 style='text-align:center; color:white; font-size:22px; font-weight:bold; text-shadow: 0px 0px 1px black;'>{row['Churn_Rate (%)']:.2f}%</h3>
                </div>
                """,
                unsafe_allow_html=True,
            )

        # Lifetime NorthStar Metric tile
        with rows[4]:
            st.markdown(
                f"""
                <div style='background-color:{product_colors[row['product_name']]}; display: flex; flex-direction: column; justify-content: center; align-items: center; border-radius: 10px; width:100%; height:150px; padding:20px;'>
                    <h3 style='text-align:center; color:white; font-size:22px; font-weight:bold; text-shadow: 0px 0px 1px black;'>{row['NorthStar_Metric_Value']:,}</h3>
                    <h6 style='text-align:center; color:white; font-size:14px; margin-top:0.5px;'>{descriptions[row['product_name']]}</h6>
                </div>
                """,
                unsafe_allow_html=True,
            )

    # Create a 2x2 Grid
    st.markdown("### Charts")
    chart_rows_top = st.columns(2)

    # Chart 1: Cumulative Lifetime Customers (Top Left)
    with chart_rows_top[0]:
        fig1 = go.Figure()
        fig1.add_trace(
            go.Scatter(
                x=cumulative_activated_customers_mailchimp.index,
                y=cumulative_activated_customers_mailchimp.values,
                mode="lines",
                name="Cumulative Lifetime Customers",
                line=dict(color="blue", width=3)
            )
        )
        fig1.update_layout(
            title="Cumulative Lifetime Customers",
            xaxis_title="Date",
            yaxis_title="Number of Customers",
            legend_title="Metrics",
            template="plotly_white"
        )
        st.plotly_chart(fig1, use_container_width=True)

    # Chart 2: Active Customers by Date (Top Right)
    with chart_rows_top[1]:
        fig2 = go.Figure()
        fig2.add_trace(
            go.Scatter(
                x=active_customers_daily_mailchimp.index,
                y=active_customers_daily_mailchimp.values,
                mode="lines",
                name="Active Customers by Date",
                line=dict(color="green", width=3)
            )
        )
        fig2.update_layout(
            title="Daily Active Customers",
            xaxis_title="Date",
            yaxis_title="Number of Active Customers",
            legend_title="Metrics",
            template="plotly_white"
        )
        st.plotly_chart(fig2, use_container_width=True)

    #  Bottom Row
    chart_rows_bottom = st.columns(2)
    # Bottom Left Chart: Funnel Chart for User Actions
    with chart_rows_bottom[0]:
        fig_funnel = go.Figure(go.Funnel(
            y=mailchimp_funnel.index,  # Action names
            x=mailchimp_funnel.values,  # Counts of users performing each action
            textinfo="value+percent initial",  # Display both values and percentages
            marker=dict(color=["#FFE01B", "#FFC30F", "#FFB000", "#FF8000", "#FF6000", "#FF4000", "#FF2000"])
        ))

        fig_funnel.update_layout(
            title="Mailchimp User Actions Funnel",
            yaxis_title="Actions",
            xaxis_title="Users",
            margin=dict(l=50, r=50, t=50, b=50)
        )

        st.plotly_chart(fig_funnel, use_container_width=True)

    with chart_rows_bottom[1]:
        st.empty()
