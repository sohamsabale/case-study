import pandas as pd
import streamlit as st
import plotly as plt
import plotly.graph_objects as go
import plotly.express as px
from plotly.subplots import make_subplots

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
    (3, "TurboTax"): "Filing Completed",
    (2, "Mailchimp"): "Email Campaigns Sent",
    (5, "Mint"): "Budget Created",
    (5, "QuickBooks"): "Invoice Created"
}
# Map action type IDs to names in usage_data
usage_data["Action_Type"] = usage_data.apply(
    lambda row: action_keys.get((row["action_type_id"], row["product_name"]), "Unknown Action"), axis=1
)

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

customer_summary = pd.DataFrame({
    "Lifetime_Activated_Customers": lifetime_activated_by_product,
    "Current_Active_Customers": current_active_by_product,
    "Churn_Rate (%)": churn_rate_by_product
}).fillna(0).astype({
    "Lifetime_Activated_Customers": int,
    "Current_Active_Customers": int,
    "Churn_Rate (%)": float
})
customer_summary.reset_index(inplace=True)


# Group by product name and calculate the sum of the usage counts for the relevant actions
north_star_values = usage_data.groupby(["product_name", "Action_Type","action_type_id"])["usage_count"].sum().reset_index()

valid_combinations = set(action_keys.keys())

north_star_actuals = north_star_values[
    north_star_values.apply(
        lambda row: (row["action_type_id"], row["product_name"]) in valid_combinations, axis=1
    )
]

north_star_actuals = north_star_actuals[["product_name", "usage_count"]]

# Merge customer_summary with north_star_actuals on product_name
customer_summary = pd.merge(
    customer_summary, 
    north_star_actuals, 
    how="left",  # Left join to preserve all rows in customer_summary
    on="product_name"
)

# Rename usage_count column for clarity
customer_summary.rename(columns={"usage_count": "NorthStar_Metric_Value"}, inplace=True)

# Fill any NaN values in the NorthStar_Metric_Value column with 0
customer_summary["NorthStar_Metric_Value"] = customer_summary["NorthStar_Metric_Value"].fillna(0).astype(int)

# Reset index for better readability
customer_summary.reset_index(inplace=True)


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
    5: "Log-Ins", 
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


# Group by and calculate cumulative activated customers
grouped_activated_customers = mailchimp_data.groupby("first_activation_date").size()
cumulative_activated_customers_mailchimp = grouped_activated_customers.reindex(full_date_range, fill_value=0).cumsum()


# Group by and calculate cumulative cancelled customers
grouped_cancelled_customers = mailchimp_data.groupby("cancel_date").size()
cumulative_cancelled_customers_mailchimp = grouped_cancelled_customers.reindex(full_date_range, fill_value=0).cumsum()

# Calculate daily active customers
active_customers_daily_mailchimp = cumulative_activated_customers_mailchimp - cumulative_cancelled_customers_mailchimp


# Group by acquisition channel and count customers
channel_breakdown = mailchimp_data.groupby("channel").size().reset_index(name="Customer_Count")

# Sort by Customer Count
channel_breakdown = channel_breakdown.sort_values(by="Customer_Count", ascending=False)

# Filter churned Mailchimp users
churned_mailchimp_users = mailchimp_data[~mailchimp_data["cancel_date"].isna()]

# Filter non-churned Mailchimp users
non_churned_mailchimp_users = mailchimp_data[mailchimp_data["cancel_date"].isna()]

# Merge churned Mailchimp users with usage_data
churned_mailchimp_usage = usage_data.merge(churned_mailchimp_users[["customerid"]], on="customerid")

# Merge non-churned Mailchimp users with usage_data
non_churned_mailchimp_usage = usage_data.merge(non_churned_mailchimp_users[["customerid"]], on="customerid")

# Group and calculate action counts for churned and non-churned users
churned_actions = churned_mailchimp_usage.groupby("action_type_id")["usage_count"].sum().reset_index()
non_churned_actions = non_churned_mailchimp_usage.groupby("action_type_id")["usage_count"].sum().reset_index()

# Total actions
churned_total = churned_actions["usage_count"].sum()
non_churned_total = non_churned_actions["usage_count"].sum()

# Normalize to percentages
churned_actions["Percentage"] = churned_actions["usage_count"] / churned_total * 100
non_churned_actions["Percentage"] = non_churned_actions["usage_count"] / non_churned_total * 100

# Merge churned and non-churned action percentages
action_comparison = pd.merge(
    churned_actions.rename(columns={"Percentage": "Churned_Percentage"}),
    non_churned_actions.rename(columns={"Percentage": "Non_Churned_Percentage"}),
    on="action_type_id",
    how="outer"
).fillna(0)

# Map action_type_id to descriptive names
action_type_mapping = {
    5: "Campaigns Created ", 
    7: "Log-Ins",
    4: "Subscribers Added",
    3: "Templates Edited",
    2: "Email Campaigns Sent", 
    1: "Campaigns Deleted",
    6: "Forms Drafted"
}
action_comparison["Action_Type"] = action_comparison["action_type_id"].map(action_type_mapping)

# Data for plotting
action_types = action_comparison["Action_Type"]
churned_percentage = action_comparison["Churned_Percentage"]
non_churned_percentage = action_comparison["Non_Churned_Percentage"]

lifetime_activated_customers_mailchimp = mailchimp_data[~mailchimp_data['first_activation_date'].isna()]
lifetime_activated_by_channel_mailchimp = lifetime_activated_customers_mailchimp.groupby('channel').size()
churned_users_by_channel_mailchimp = mailchimp_data[~mailchimp_data['cancel_date'].isna()].groupby('channel').size()
# Calculate churn rate: churned users / lifetime activated customers
churn_rate_by_channel_mailchimp = (churned_users_by_channel_mailchimp / lifetime_activated_by_channel_mailchimp * 100).fillna(0)

# Streamlit App
st.title("Mailchimp Case Study")

# Create tab for Intuit Overview
tab1, tab2, tab3 = st.tabs(["Intuit Overview", "Mailchimp Deep Dive", "Mailchimp Churned Users Analysis"])

with tab1:
    st.header("Intuit Executive Overview")
    st.markdown("#### How is the business doing?")

    # Create the grid headers
    rows = st.columns([1, 1, 1, 1, 1])
    with rows[0]:
        st.markdown("<p style='text-align:center; font-weight:bold; font-size:16px;'>Product</p>", unsafe_allow_html=True)
    with rows[1]:
        st.markdown("<p style='text-align:center; font-weight:bold; font-size:16px;'>👥 Lifetime Activated</p>", unsafe_allow_html=True)
    with rows[2]:
        st.markdown("<p style='text-align:center; font-weight:bold; font-size:16px;'>⚡Current Active</p>", unsafe_allow_html=True)
    with rows[3]:
        st.markdown("<p style='text-align:center; font-weight:bold; font-size:16px;'>📉Churn Rate</p>", unsafe_allow_html=True)
    with rows[4]:
        st.markdown("<p style='text-align:center; font-weight:bold; font-size:16px;'>⭐ Lifetime NorthStar Metric</p>", unsafe_allow_html=True)

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
    st.markdown("### Insights")
    st.write(
        "From the metrics above, it seems like all products have roughly equal number of lifetime activated(~2K) and current active(~1.4K) users. Additoinally, churn rates(~30%) are also similar."
    )

with tab2:
    st.header("Mailchimp Deep Dive")
    st.markdown("#### How is Mailchimp doing?")
    # Wireframe for tiles
    st.markdown("### Metrics Overview")
    rows = st.columns([1, 1, 1, 1, 1])

    # Create the grid headers for tiles
    with rows[0]:
        st.markdown("<p style='text-align:center; font-weight:bold; font-size:16px;'>Product</p>", unsafe_allow_html=True)
    with rows[1]:
        st.markdown("<p style='text-align:center; font-weight:bold; font-size:16px;'>👥 Lifetime Activated</p>", unsafe_allow_html=True)
    with rows[2]:
        st.markdown("<p style='text-align:center; font-weight:bold; font-size:16px;'>⚡Current Active</p>", unsafe_allow_html=True)
    with rows[3]:
        st.markdown("<p style='text-align:center; font-weight:bold; font-size:16px;'>📉Churn Rate</p>", unsafe_allow_html=True)
    with rows[4]:
        st.markdown("<p style='text-align:center; font-weight:bold; font-size:16px;'>⭐ Lifetime NorthStar Metric</p>", unsafe_allow_html=True)

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
         # Create a bar chart for channel breakdown
        fig_channel = px.bar(
            channel_breakdown,
            x="channel",
            y="Customer_Count",
            title="Mailchimp Customer Channel Breakdown",
            labels={"channel": "Acquisition Channel", "Customer_Count": "Number of Customers"},
            color="Customer_Count",
            color_continuous_scale="Blues"
        )

        # Add the chart to Streamlit
        st.plotly_chart(fig_channel, use_container_width=True)
    
    

with tab3:
    st.header("Mailchimp Deep Dive - Churned Users")
    st.markdown("#### What can we learn about churned users?")
    # Wireframe for tiles
    # Create a 2x2 Grid
    chart_rows_top = st.columns(1)

    # Chart 1: Cumulative Lifetime Customers (Top Left)
    with chart_rows_top[0]:
        # Define the Plotly figure
        fig_comparison = go.Figure()

        # Add bars for churned users
        fig_comparison.add_trace(
            go.Bar(
                x=action_types,
                y=churned_percentage,
                name="Churned Users",
                marker=dict(color="red"),
                text=[f"{v:.1f}%" for v in churned_percentage],
                textposition="outside",
            )
        )

        # Add bars for non-churned users
        fig_comparison.add_trace(
            go.Bar(
                x=action_types,
                y=non_churned_percentage,
                name="Non-Churned Users",
                marker=dict(color="green"),
                text=[f"{v:.1f}%" for v in non_churned_percentage],
                textposition="outside",
            )
        )

        # Update layout
        fig_comparison.update_layout(
            barmode="group",
            title="Churned vs Active User Actions (Percentages)",
            xaxis_title="Action Type",
            yaxis_title="Percentage of Actions (%)",
            legend_title="User Type",
            template="plotly_white",
            xaxis=dict(tickangle=45),  # Rotate x-axis labels
        )

        # Render the chart in Streamlit
        st.plotly_chart(fig_comparison, use_container_width=True)
    
    chart_rows_bottom = st.columns(1)
    with chart_rows_bottom[0]:
        # Define the Plotly figure
        fig_comparison = go.Figure()

        # Add bars for churned users
        fig_comparison.add_trace(
            go.Bar(
                x=churned_users_by_channel_mailchimp.index,
                y=churned_users_by_channel_mailchimp.values,
                name="Number of Churned Users",
                marker=dict(color="red"),
                text=[f"{v}" for v in churned_users_by_channel_mailchimp.values],
                textposition="outside",
            )
        )

        # Add a line for churn rate with labels
        fig_comparison.add_trace(
            go.Scatter(
                x=churn_rate_by_channel_mailchimp.index,
                y=churn_rate_by_channel_mailchimp.values,
                mode="lines+markers+text",
                name="Churn Rate (%)",
                marker=dict(color="blue"),
                line=dict(width=2),
                text=[f"{v:.1f}%" for v in churn_rate_by_channel_mailchimp.values],
                textposition="top center",
                textfont=dict(color="black")
            )
        )

        # Update layout
        fig_comparison.update_layout(
            barmode="group",
            title="Churned Users and Churn Rate by Channel",
            xaxis_title="Channel",
            yaxis=dict(title="Number of Churned Users", side="left"),
            yaxis2=dict(
                title="Churn Rate (%)",
                overlaying="y",
                side="right",
                range=[0, 40],  # Set churn rate axis to 0-40%
                tickformat=".0f%%",  # Display as percentage
            ),
            legend_title="Metrics",
            template="plotly_white",
            xaxis=dict(tickangle=45),
        )

        # Render the chart in Streamlit
        st.plotly_chart(fig_comparison, use_container_width=True)
    st.markdown("### Insights")
    st.write(
        "From the charts above, we can see that the churned users login activity rate is lower compared to active users. However, the rest of the activity types are equivalent to active users. Implaying that the churned users just dont login to the product UI. This represents an opportunity to reduce churn by identifying users with low login rates."
    )