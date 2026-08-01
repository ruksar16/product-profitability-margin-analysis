import streamlit as st
import pandas as pd
import numpy as np
import matplotlib.pyplot as plt
import seaborn as sns
import time
import plotly.express as px
import plotly.graph_objects as go

st.set_page_config(layout="wide", page_title="Nassau Candy Distributor Analysis")

st.markdown("""
<style>
.stApp, [data-testid="stAppViewContainer"] {
    background: linear-gradient(135deg, #0b1a2d, #06111f) !important;
    color: #e2e8f0 !important;
    font-family: 'Segoe UI', Tahoma, Geneva, Verdana, sans-serif;
}
            
[data-testid="stSidebar"] {
    background: rgba(14, 29, 47, 0.7) !important;
    border-right: 1px solid rgba(255, 255, 255, 0.08) !important;
}

[data-testid="stMetric"], 
[data-testid="stDataFrame"] {
    background: rgba(14, 29, 47, 0.7) !important;
    border-radius: 8px !important;
    padding: 20px !important;
    border: 1px solid rgba(255, 255, 255, 0.08) !important;
    box-shadow: 0 4px 20px rgba(0, 0, 0, 0.25) !important;
}

[data-testid="stTextInput"] input, 
[data-testid="stDateInput"] input,
[data-baseweb="select"] {
    background-color: #0F172A !important;
    color: #ffffff !important;
    border-radius: 6px !important;
    border: 1px solid rgba(255, 255, 255, 0.2) !important;
}

[data-baseweb="tag"] {
    background-color: rgba(59, 130, 246, 0.15) !important;
    color: #60a5fa !important;
    border: 1px solid rgba(59, 130, 246, 0.3) !important;
}

h1, h2, h3 {
    color: #ffffff !important;
    font-weight: 600 !important;
}

.stButton>button {
    background: linear-gradient(135deg, #1e3554, #112238) !important;
    color: #ffffff !important;
    border: 1px solid rgba(255, 255, 255, 0.15) !important;
    border-radius: 6px !important;
}
.stButton>button:hover {
    border-color: #3b82f6 !important;
}

[data-testid="stSlider"] div[aria-valuenow] {
    background-color: #3b82f6  !important;
}

::-webkit-scrollbar { width: 6px; height: 6px; }
::-webkit-scrollbar-thumb { background: #1e3554; border-radius: 10px; }
::-webkit-scrollbar-track { background: #06111f; }
</style>

""", unsafe_allow_html=True)

st.title("🍬 Nassau Candy Distributor: Financial Performance Dashboard")
st.markdown("This dashboard provides insights into product-level profitability, margin performance, and cost structure.")

@st.cache_data
def load_data():
    DATA_PATH = 'Nassau Candy Distributor.csv'
    df = pd.read_csv(DATA_PATH)

    df['Sales'] = pd.to_numeric(df['Sales'], errors='coerce')
    df['Cost'] = pd.to_numeric(df['Cost'], errors='coerce')
    df = df.dropna(subset=['Sales', 'Cost'])
    df = df[(df['Sales'] >= 0) & (df['Cost'] >= 0)]

    df['Profit'] = df['Sales'] - df['Cost']
    df['Gross_Margin_%'] = np.where(
    df['Sales'] == 0,
    0,
    ((df['Sales'] - df['Cost']) / df['Sales']) * 100
    )
    df = df[df['Profit'].notna()]

    df['Product Name'] = df['Product Name'].str.strip().str.lower()
    df['Division'] = df['Division'].str.strip().str.title()

    df['Order Date'] = pd.to_datetime(df['Order Date'], dayfirst=True, errors='coerce')
    df['Ship Date'] = pd.to_datetime(df['Ship Date'], dayfirst=True, errors='coerce')
    df = df.dropna(subset=['Order Date', 'Ship Date'])

    return df

df = load_data()

# Sidebar
st.sidebar.header('Filter Options')

min_date = df['Order Date'].min().to_pydatetime()
max_date = df['Order Date'].max().to_pydatetime()
date_range = st.sidebar.date_input(
    "Select Date Range",
    value=(min_date, max_date),
    min_value=min_date,
    max_value=max_date
)
if len(date_range) == 2:
    start_date, end_date = date_range
    df_filtered = df[(df['Order Date'] >= pd.Timestamp(start_date)) & (df['Order Date'] <= pd.Timestamp(end_date))]
else:
    df_filtered = df.copy()

all_divisions = ['All'] + list(df['Division'].unique())
selected_divisions = st.sidebar.multiselect(
    "Select Division(s)",
    options=all_divisions,
    default=['All']
)
if 'All' not in selected_divisions:
    df_filtered = df_filtered[df_filtered['Division'].isin(selected_divisions)]

min_margin = float(df_filtered['Gross_Margin_%'].min()) if not df_filtered.empty else 0.0
max_margin = float(df_filtered['Gross_Margin_%'].max()) if not df_filtered.empty else 100.0
margin_threshold = st.sidebar.slider(
    "Minimum Gross Margin %",
    min_value=min_margin,
    max_value=max_margin,
    value=min_margin,
    step=0.1
)
df_filtered = df_filtered[df_filtered['Gross_Margin_%'] >= margin_threshold]

search_product = st.sidebar.text_input("Search Product")
if search_product:
    df_filtered = df_filtered[
        df_filtered['Product Name'].str.contains(search_product, case=False, na=False)
    ]

# Exit smoothly if filters isolate zero matching data rows
if df_filtered.empty:
    st.warning("⚠️ No data available matching the selected filter criteria.")
    st.stop()

# KPI
st.markdown("""
<style>
.stApp { background-color: #030a14; color: #f8fafc; font-family: sans-serif; }
.section-header { font-size: 16px; font-weight: 500; color: #94a3b8; margin-top: 25px; margin-bottom: 15px; }
.kpi-container { background-color: #07111e; border: 1px solid #132237; border-radius: 4px; padding: 16px; height: 175px; display: flex; flex-direction: column; justify-content: space-between; }
.kpi-header { display: flex; align-items: center; gap: 10px; }
.kpi-title { font-size: 13px; color: #64748b; font-weight: 500; }
.kpi-value-block { margin-top: 8px; }
.kpi-value { font-size: 26px; font-weight: 700; }
.kpi-subtitle { font-size: 11px; color: #475569; margin-top: 2px; }
.kpi-footer { font-size: 12px; font-weight: 500; margin-top: auto; padding-top: 8px; }
.trend-up { color: #10b981; }
.trend-down { color: #f43f5e; }
.meta-caption { font-size: 11px; color: #475569; padding-top: 4px; }
</style>
""", unsafe_allow_html=True)

df_filtered = df_filtered.copy()
filtered_sales = df_filtered['Sales'].sum()
filtered_profit = df_filtered['Profit'].sum()
gross_profit = (df_filtered['Sales'] - df_filtered['Cost']).sum()
df_filtered['Gross_Profit'] = df_filtered['Sales'] - df_filtered['Cost']
global_margin = (gross_profit / filtered_sales * 100) if filtered_sales > 0 else 0.0
total_units = df_filtered['Units'].sum()
profit_per_unit = filtered_profit / total_units if total_units > 0 else 0
product_sales = df['Sales'].sum()

if 'All' in selected_divisions:
    selected_data = df.copy()
    revenue_contribution = 1.0
    profit_contribution = 1.0
else:
    selected_data = df[df['Division'].isin(selected_divisions)]
    revenue_contribution = selected_data['Sales'].sum() / df['Sales'].sum()
    profit_contribution = selected_data['Profit'].sum() / df['Profit'].sum()


selected_sales = selected_data['Sales'].sum()
selected_profit = selected_data['Profit'].sum()
total_sales = df['Sales'].sum() 
total_profit = df['Profit'].sum()             
revenue_contribution = selected_sales / total_sales
profit_contribution = selected_profit / total_profit 
margin_over_time = df_filtered.groupby(df_filtered['Order Date'].dt.date)['Gross_Margin_%'].mean()

def generate_sparkline(df, value_col, line_color):
    df_sorted = df_filtered.sort_values('Order Date')
    
    if value_col == 'Gross_Margin_%':
        spark_data = df_sorted.groupby(df_sorted['Order Date'].dt.date)[value_col].mean().reset_index()
    else:
        spark_data = df_sorted.groupby(df_sorted['Order Date'].dt.date)[value_col].sum().reset_index()
        
    fig = go.Figure(go.Scatter(
        x=spark_data['Order Date'],
        y=spark_data[value_col],
        mode='lines',
        line=dict(color=line_color, width=2),
        line_shape='spline',
        hoverinfo='y',
        hovertemplate='Value: %{y:.2f}<extra></extra>',
        fill='tozeroy',
        fillcolor=f"rgba({int(line_color[1:3],16)}, {int(line_color[3:5],16)}, {int(line_color[5:7],16)}, 0.1)" if len(line_color)==7 else "rgba(16, 185, 129, 0.1)"
    ))

    y_min = spark_data[value_col].min()
    y_max = spark_data[value_col].max()
    y_range = [y_min * 0.95, y_max * 1.05] if y_min != y_max else None

    fig.update_layout(
        margin=dict(l=2, r=2, t=4, b=2), 
        height=50,
        xaxis=dict(visible=False, fixedrange=True),
        yaxis=dict(visible=False, fixedrange=True, range=y_range),
        plot_bgcolor='rgba(0,0,0,0)',
        paper_bgcolor='rgba(0,0,0,0)',
        showlegend=False,
        hoverlabel=dict(
            bgcolor="black",
            font_size=11,
            font_color="white"
        )
    )
    return fig


def calculate_trend(df, value_col, agg='sum'):
    temp = df.copy()
    temp['Month'] = temp['Order Date'].dt.to_period('M')

    if agg == 'sum':
        monthly = temp.groupby('Month')[value_col].sum()
    elif agg == 'mean':
        monthly = temp.groupby('Month')[value_col].mean()

    if len(monthly) > 1:
        prev = monthly.iloc[-2]
        curr = monthly.iloc[-1]
    else:
        prev = curr = monthly.iloc[-1]

    diff = curr - prev
    trend_class = "trend-up" if diff >= 0 else "trend-down"
    arrow = "↑" if diff >= 0 else "↓"

    return f"{arrow} {abs(diff):.1f} vs last month", trend_class


trend_text_gm, trend_class_gm = calculate_trend(df_filtered, 'Gross_Margin_%', 'mean')
df_filtered['Profit_per_Unit'] = df_filtered['Profit'] / df_filtered['Units']
trend_text_ppu, trend_class_ppu = calculate_trend(df_filtered, 'Profit_per_Unit', 'mean')

temp = df_filtered.copy()
temp['Month'] = temp['Order Date'].dt.to_period('M')

monthly = temp.groupby('Month').agg({
    'Sales': 'sum',
    'Profit': 'sum'
})

total_monthly = df.copy()
total_monthly['Month'] = total_monthly['Order Date'].dt.to_period('M')
total_monthly = total_monthly.groupby('Month').agg({
    'Sales': 'sum',
    'Profit': 'sum'
})

# Contribution calculate
monthly['Revenue_Contribution'] = monthly['Sales'] / total_monthly['Sales']
monthly['Profit_Contribution'] = monthly['Profit'] / total_monthly['Profit']

def calculate_ratio_trend(series):
    if len(series) > 1:
        prev = series.iloc[-2]
        curr = series.iloc[-1]
    else:
        prev = curr = series.iloc[-1]

    diff = curr - prev
    trend_class = "trend-up" if diff >= 0 else "trend-down"
    arrow = "↑" if diff >= 0 else "↓"

    return f"{arrow} {abs(diff)*100:.1f}% vs last month", trend_class

trend_text_rev, trend_class_rev = calculate_ratio_trend(monthly['Revenue_Contribution'])
trend_text_pc, trend_class_pc = calculate_ratio_trend(monthly['Profit_Contribution'])
trend_text_vol, trend_class_vol = calculate_trend(df_filtered, 'Gross_Margin_%', 'mean')

def render_kpi(title, value, subtitle, color, spark_col, df, trend_text, trend_class,value_shift="0px"):
    st.markdown(f"""
    <div class="kpi-container">
        <div class="kpi-header">
            <span class="kpi-title">{title}</span>
        </div>
        <div class="kpi-value-block">
            <div class="kpi-value" style="color: {color};margin-top: {value_shift};">{value}</div>
            <div class="kpi-subtitle">{subtitle}</div>
        </div>
    """, unsafe_allow_html=True)

    st.plotly_chart(
        generate_sparkline(df, spark_col, color),
        use_container_width=True,
        config={'displayModeBar': False}
    )

    st.markdown(f"""
        <div class="kpi-footer {trend_class}">
            {trend_text}
        </div>
    </div>
    """, unsafe_allow_html=True)


df_sorted = df_filtered.sort_values('Order Date')


st.markdown('<div class="section-header">Key Performance Indicators (KPIs)</div>', unsafe_allow_html=True)
kpi_cols = st.columns(5)

with kpi_cols[0]:
    render_kpi(
    "Gross Margin (%)",
    f"{global_margin:.1f}%",
    "Gross Profit ÷ Sales",
    "#10b981",
    "Gross_Margin_%",
    df_filtered,
    trend_text_gm,
    trend_class_gm,
    value_shift="-80px"
    )

with kpi_cols[1]:
    render_kpi(
    "Profit per Unit",
    f"₹{profit_per_unit:,.2f}",
    "Gross Profit ÷ Units",
    "#3b82f6",
    "Profit",
    df_filtered,
    trend_text_ppu,
    trend_class_ppu,
    value_shift="-80px"
    )

with kpi_cols[2]:
    render_kpi(
    "Revenue Contribution",
    f"{revenue_contribution:.1%}",
    "Product sales ÷ Total sales",
    "#a855f7",
    "Sales",
    df_filtered,
    trend_text_rev,
    trend_class_rev
    )

with kpi_cols[3]:
    render_kpi(
    "Profit Contribution",
    f"{profit_contribution:.1%}",
    "Product profit ÷ Total profit",
    "#eab308",
    "Profit",
    df_filtered,
    trend_text_pc,
    trend_class_pc
    )
    
with kpi_cols[4]:
    margin_std = margin_over_time.std()
    render_kpi(
    "Margin Volatility (Std Dev)",
    f"{margin_std:.2f}%",
    "Variability of margin over time",
    "#f43f5e",
    "Gross_Margin_%",
    df_filtered,
    trend_text_vol,
    trend_class_vol
    )

# Financial Overview
st.markdown('<div class="section-header">Financial Overview (Pie Charts)</div>', unsafe_allow_html=True)
pie_col1, pie_col2, pie_col3 = st.columns(3)
pie_colors = ['#1e6b7b', '#248277', '#ecba53', '#d05a3f', '#3b82f6', '#64748b']

def render_dynamic_pie(df, value_col, title_label, total_val):
    # Map directly onto your target column 'Product Name'
    grouped = df.groupby('Product Name')[value_col].sum().reset_index()
    grouped = grouped.sort_values(by=value_col, ascending=False).reset_index(drop=True)
    # Isolate Top 3 records dynamically and consolidate the remaining 12 into "Others"
    if len(grouped) > 4:
        top_3 = grouped.iloc[:3].copy()
        others_val = grouped.iloc[3:][value_col].sum()
        others_row = pd.DataFrame([{"Product Name": "Others", value_col: others_val}])
        plot_df = pd.concat([top_3, others_row], ignore_index=True)
    else:
        plot_df = grouped

    plot_df['Product Name'] = plot_df['Product Name'].str.title()

    fig = px.pie(
        plot_df, values=value_col, names='Product Name',
        color_discrete_sequence=pie_colors
    )

    fig.update_traces(scalegroup='one', selector=dict(type='pie'))
    fig.update_layout(
        title=dict(
            text=f"<b>{title_label}</b>",
            font=dict(color="#ffffff", size=14),
            x=0.02,  
            y=0.95
        ),
        annotations=[
            dict(
                text=f"Total: ₹{plot_df[value_col].sum():,.0f}",
                font=dict(color="#94a3b8", size=12),
                showarrow=False,
                xref="paper", yref="paper",
                x=0.98, y=1.15,  
                xanchor="right", yanchor="top"
            )
        ],
        margin=dict(l=5, r=25, t=50, b=40), 
        height=280,                         
        plot_bgcolor='rgba(0,0,0,0)', 
        paper_bgcolor='#07111e',
        legend=dict(
            font=dict(color="#94a3b8", size=10), 
            orientation="h",            
            yanchor="top",                  
            y=-0.1,                         
            xanchor="center",               
            x=0.5
        )
    )
    fig.update_traces(
        textposition='inside', 
        textinfo='percent',
        hovertemplate="<b>%{label}</b><br>Value: $%{value:,.0f}<extra></extra>"
    )
    return fig

with pie_col1:
    st.plotly_chart(render_dynamic_pie(df_filtered, 'Sales', 'Total Sales', total_sales), use_container_width=True, config={'displayModeBar': False})

with pie_col2:
    st.plotly_chart(render_dynamic_pie(df_filtered, 'Profit', 'Total Profit', total_profit), use_container_width=True, config={'displayModeBar': False})

with pie_col3:
    total_cost = df_filtered['Cost'].sum()
    st.plotly_chart(render_dynamic_pie(df_filtered, 'Cost', 'Total Cost Structure', total_cost), use_container_width=True, config={'displayModeBar': False})

# Sales & Profit Macro Trends
st.markdown('<div class="section-header">Sales & Profit Macro Trends</div>', unsafe_allow_html=True)
df_filtered = df_filtered.copy()
df_filtered['Month_Year'] = df_filtered['Order Date'].dt.to_period('M')
full_range = pd.period_range(
    start=df_filtered['Order Date'].min().to_period('M'),
    end=df_filtered['Order Date'].max().to_period('M'),
    freq='M'
)
df_trend = df_filtered.groupby('Month_Year').agg({
    'Sales': 'sum',
    'Profit': 'sum',
    'Cost': 'sum'
})
df_trend = df_trend.reindex(full_range, fill_value=0).reset_index()
df_trend.rename(columns={'index': 'Month_Year'}, inplace=True)
df_trend['Month_Year'] = df_trend['Month_Year'].dt.strftime('%b %Y')
df_trend['Margin %'] = np.where(
    df_trend['Sales'] == 0,
    0,
    (df_trend['Profit'] / df_trend['Sales']) * 100
)
fig_trend = go.Figure()

fig_trend.add_trace(go.Bar(
    x=df_trend['Month_Year'], y=df_trend['Sales'],
    name='Total Sales', marker_color='#1e6b7b',
    hovertemplate="<b>%{x}</b><br>Sales: $%{y:,.0f}<extra></extra>"
))

fig_trend.add_trace(go.Bar(
    x=df_trend['Month_Year'], y=df_trend['Profit'],
    name='Total Profit', marker_color='#248277',
    hovertemplate="<b>%{x}</b><br>Profit: $%{y:,.0f}<extra></extra>"
))

fig_trend.add_trace(go.Bar(
    x=df_trend['Month_Year'], y=df_trend['Cost'],
    name='Total Cost', marker_color='#ecba53',
    hovertemplate="<b>%{x}</b><br>Cost: $%{y:,.0f}<extra></extra>"
))

fig_trend.add_trace(go.Scatter(
    x=df_trend['Month_Year'],
    y=df_trend['Margin %'],
    name='Margin %',
    mode='lines+markers',
    yaxis='y2',
    line=dict(color='#38bdf8', width=2),
    connectgaps=True,
    hovertemplate="<b>%{x}</b><br>Margin: %{y:.1f}%<extra></extra>"
))

fig_trend.update_layout(
    barmode='group',
    height=320,
    margin=dict(l=50, r=50, t=30, b=40),
    plot_bgcolor='#07111e',
    paper_bgcolor='#07111e',
    legend=dict(
        orientation="h",
        yanchor="bottom",
        y=1.05,
        xanchor="left",
        x=0.02,
        font=dict(color="#94a3b8")
    ),
    xaxis=dict(
        tickfont=dict(color="#64748b", size=11),
        showgrid=False,
        tickangle=-45
    ),
    yaxis=dict(
        title="Amount (₹)",
        tickfont=dict(color="#64748b", size=11),
        gridcolor="#132237",
        tickformat="~s"
    ),
    yaxis2=dict(
        title="Margin %",
        overlaying='y',
        side='right',
        tickfont=dict(color="#38bdf8"),
        showgrid=False
    ),
    bargap=0.25
)

st.plotly_chart(fig_trend, use_container_width=True, config={'displayModeBar': False})      

# Calculations for Dashboard Modules (based on filtered data)

# Recalculate product_profit after filtering
product_profit = df_filtered.groupby('Product Name').agg({
    'Sales': 'sum',
    'Cost': 'sum',
    'Profit': 'sum',
    'Units': 'sum'
}).reset_index()

product_profit['Gross_Margin_%'] = (
    product_profit['Profit'] / product_profit['Sales']
) * 100

# Recalculate medians for risk flags
sales_median = product_profit['Sales'].median()
profit_median = product_profit['Profit'].median()
margin_median = product_profit['Gross_Margin_%'].median()

# Dashboard Layout

# Tab interface for main sections
tab1, tab2, tab3, tab4 = st.tabs([
    "Product Profitability",
    "Division Performance",
    "Cost & Margin Diagnostics",
    "Profit Concentration"
])

with tab1:
    st.header('Product Profitability Overview')

    # Product-Level Margin Leaderboard
    st.subheader('Product-Level Margin Leaderboard')
    df_display = product_profit[['Product Name', 'Gross_Margin_%']].sort_values(
        by='Gross_Margin_%', ascending=False
    ).reset_index(drop=True)

    st.dataframe(
        df_display,
        column_config={
            "Gross_Margin_%": st.column_config.ProgressColumn(
                "Gross Margin (%)",
                help="The profit margin percentage for the product",
                format="%.2f%%",
                min_value=0,
                max_value=100, 
                color="#46ACAC"
            ),
            "Product Name": st.column_config.TextColumn("Product Name")
        },
        hide_index=True,
        use_container_width=True
    )

    # Top 10 Products by Profit Contribution
    st.subheader('Top 10 Products by Profit Contribution')
    top_products_profit = product_profit.sort_values(by='Profit', ascending=False).head(10).reset_index(drop=True)
    fig_profit_contrib, ax_profit_contrib = plt.subplots(figsize=(10, 6), facecolor='#0F172A')
    ax_profit_contrib.set_facecolor('#0F172A')  
    bars = ax_profit_contrib.bar(
    top_products_profit['Product Name'], 
    top_products_profit['Profit'],
    color='#b88915'   
    )
    ax_profit_contrib.set_xticks(range(len(top_products_profit['Product Name'])))
    ax_profit_contrib.set_xticklabels(top_products_profit['Product Name'], rotation=45, ha='right')
    ax_profit_contrib.tick_params(axis='x', colors='white')
    ax_profit_contrib.tick_params(axis='y', colors='white')
    ax_profit_contrib.set_title("Top 10 Products by Profit Contribution", color='white')
    ax_profit_contrib.set_xlabel("Product Name", color='white')
    ax_profit_contrib.set_ylabel("Profit", color='white')
    for bar in bars:
        height = bar.get_height()
        ax_profit_contrib.text(bar.get_x() + bar.get_width()/2, height, f'{height:,.0f}', ha='center', va='bottom', fontsize=9, color='white')
    plt.tight_layout()
    st.pyplot(fig_profit_contrib)

with tab2:
    st.header('Division Performance Dashboard')

    # Division-wise Sales vs Profit
    division_profit = df_filtered.groupby('Division').agg({
        'Sales': 'sum',
        'Profit': 'sum'
    }).reset_index()

    st.subheader('Division-wise Sales vs Profit')
    fig_div_sales_profit, ax_div_sales_profit = plt.subplots(figsize=(10, 6), facecolor='#0F172A')
    ax_div_sales_profit.set_facecolor('#0F172A')
    sns.scatterplot(
        data=division_profit,
        x='Sales',
        y='Profit',
        hue='Division',
        s=200,
        alpha=0.8,
        ax=ax_div_sales_profit
    )
    for i in range(division_profit.shape[0]):
        ax_div_sales_profit.text(
            division_profit['Sales'][i],
            division_profit['Profit'][i],
            f"({division_profit['Sales'][i]:,.0f}, {division_profit['Profit'][i]:,.0f})",
            fontsize=9,
            color='white',
            ha='center',
            va='bottom'
        )
    ax_div_sales_profit.set_title("Division-wise Sales vs Profit", color='white')
    ax_div_sales_profit.set_xlabel("Total Sales", color='white')
    ax_div_sales_profit.set_ylabel("Total Profit", color='white')
    ax_div_sales_profit.tick_params(axis='x', colors='white')
    ax_div_sales_profit.tick_params(axis='y', colors='white')
    ax_div_sales_profit.grid(True, color='white', alpha=0.05)
    legend = ax_div_sales_profit.legend(title="Division", bbox_to_anchor=(1.05, 1), loc='upper left')
    legend.get_frame().set_facecolor('none')
    legend.get_frame().set_edgecolor('none')
    plt.setp(legend.get_texts(), color='white')
    plt.setp(legend.get_title(), color='white')
    plt.tight_layout()
    st.pyplot(fig_div_sales_profit)

    # Gross Margin % Distribution per Division
    st.subheader('Gross Margin % Distribution per Division')
    fig_div_margin_dist, ax_div_margin_dist = plt.subplots(figsize=(10, 6), facecolor='#0F172A')
    ax_div_margin_dist.set_facecolor('#0F172A')
    sns.boxplot(
    data=df_filtered,
    x='Division',
    y='Gross_Margin_%',
    ax=ax_div_margin_dist,
    color="#00C4DF"   
    )
    for i, div_name in enumerate(df_filtered['Division'].unique()):
        median_val = df_filtered[df_filtered['Division']==div_name]['Gross_Margin_%'].median()
        ax_div_margin_dist.text(i, median_val, f"{median_val:.1f}", ha='center', va='bottom', color='white')
        
    ax_div_margin_dist.set_title('Gross Margin % Distribution per Division', color='white')
    ax_div_margin_dist.set_xlabel('Division', color='white')
    ax_div_margin_dist.set_ylabel('Gross Margin %', color='white')
    ax_div_margin_dist.grid(True, color='white', alpha=0.05)
    ax_div_margin_dist.tick_params(axis='x', rotation=45, colors='white')
    ax_div_margin_dist.tick_params(axis='y', colors='white')
    plt.tight_layout()
    st.pyplot(fig_div_margin_dist)

with tab3:
    st.header('Cost vs Margin Diagnostics')

    # Cost vs Sales Scatter Analysis
    st.subheader('Cost vs Sales Scatter Analysis')
    fig_cost_sales, ax_cost_sales = plt.subplots(figsize=(10, 6), facecolor='#0F172A')
    ax_cost_sales.set_facecolor('#0F172A')
    ax_cost_sales.scatter(df_filtered['Sales'], df_filtered['Cost'], color='#79BD9A')
    ax_cost_sales.set_xlabel('Sales', color='white')
    ax_cost_sales.set_ylabel('Cost', color='white')
    ax_cost_sales.set_title('Cost vs Sales Scatter Analysis', color='white')
    ax_cost_sales.tick_params(colors='white')
    st.pyplot(fig_cost_sales)
    st.subheader('Margin Risk Flags')

    # High-profit / high-margin products
    high_profit_high_margin = product_profit[
        (product_profit['Profit'] >= profit_median) &
        (product_profit['Gross_Margin_%'] >= margin_median)
    ]
    with st.expander("High Profit / High Margin Products"): 
        st.write("These products are performing well in both profitability and margin:")
        st.dataframe(high_profit_high_margin[['Product Name', 'Profit', 'Gross_Margin_%']].round(2))

    # High Sales / Low Margin Products
    high_sales_low_margin = product_profit[
        (product_profit['Sales'] >= sales_median) &
        (product_profit['Gross_Margin_%'] < margin_median)
    ]
    with st.expander("High Sales / Low Margin Products (Review Needed)"):
        st.write("Products that generate high sales but have lower margins. Investigate cost structures or pricing:")
        st.dataframe(high_sales_low_margin[['Product Name', 'Sales', 'Gross_Margin_%']].round(2))

    # Low Sales / Low Profit Products
    low_sales_low_profit = product_profit[
        (product_profit['Sales'] < sales_median) &
        (product_profit['Profit'] < profit_median)
    ]
    with st.expander("Low Sales / Low Profit Products (Consider Discontinuation)"):
        st.write("Products with minimal contribution in both sales and profit:")
        st.dataframe(low_sales_low_profit[['Product Name', 'Sales', 'Profit']].round(2))

    # Discontinuing Products
    product_discontinue_df = product_profit.copy()
    sales_cut = product_discontinue_df['Sales'].quantile(0.25)
    profit_cut = product_discontinue_df['Profit'].quantile(0.25)
    margin_cut = product_discontinue_df['Gross_Margin_%'].quantile(0.25)

    product_discontinue_df['Discontinue'] = np.where(
        (product_discontinue_df['Sales'] <= sales_cut) &
        (product_discontinue_df['Profit'] <= profit_cut) &
        (product_discontinue_df['Gross_Margin_%'] < margin_cut),
        True,
        False
    )
    discontinue_df = product_discontinue_df[product_discontinue_df['Discontinue'] == True].drop_duplicates(subset=['Product Name'])
    
    # Products Recommended for Discontinuation
    with st.expander("Products Recommended for Discontinuation"): 
        st.write("These products show low sales, low profit, and low margins, making them candidates for discontinuation:")
        st.dataframe(discontinue_df[['Product Name', 'Sales', 'Cost', 'Profit', 'Gross_Margin_%']].round(2))

with tab4:
    st.header('Profit Concentration Analysis')

    # Revenue Pareto
    st.subheader('Pareto Chart - Sales Concentration')
    product_pareto_sales = product_profit.sort_values(by='Sales', ascending=False)
    product_pareto_sales['cum_sales'] = product_pareto_sales['Sales'].cumsum()
    product_pareto_sales['cum_sales_pct'] = 100 * product_pareto_sales['cum_sales'] / product_pareto_sales['Sales'].sum()

    fig_sales_pareto, ax1_sales = plt.subplots(figsize=(12, 6), facecolor='#0F172A')
    ax1_sales.set_facecolor('#0F172A')
    ax1_sales.bar(product_pareto_sales['Product Name'], product_pareto_sales['Sales'], color='skyblue')
    ax1_sales.set_xticks(range(len(product_pareto_sales['Product Name'])))
    ax1_sales.set_xticklabels(product_pareto_sales['Product Name'], rotation=60, ha='right')
    ax1_sales.set_ylabel('Sales', color='white')

    ax2_sales = ax1_sales.twinx()
    ax2_sales.plot(product_pareto_sales['Product Name'], product_pareto_sales['cum_sales_pct'], color='red', marker='o', zorder=1 )
    ax2_sales.set_ylabel('Cumulative %', color='white')
    ax2_sales.set_ylim(0, 120)

    ax2_sales.axhline(80, color='green', linestyle='--', label='80% Cumulative Sales')
    legend = ax2_sales.legend(loc='upper right')
    legend.get_frame().set_facecolor('none')
    legend.get_frame().set_edgecolor('none')
    plt.setp(legend.get_texts(), color='white')
    ax1_sales.tick_params(axis='x', colors='white')
    ax1_sales.tick_params(axis='y', colors='white')
    ax2_sales.tick_params(axis='y', colors='white')
    ax1_sales.set_title("Pareto Chart - Sales Concentration", color='white')
    plt.tight_layout()
    st.pyplot(fig_sales_pareto)

    # Profit Pareto
    st.subheader('Pareto Chart - Profit Concentration')
    product_pareto_profit = product_profit.sort_values(by='Profit', ascending=False)
    product_pareto_profit['cum_profit'] = product_pareto_profit['Profit'].cumsum()
    product_pareto_profit['cum_profit_pct'] = (product_pareto_profit['cum_profit'] / product_pareto_profit['Profit'].sum()) * 100

    fig_profit_pareto, ax1_profit = plt.subplots(figsize=(12, 6), facecolor='none')
    ax1_profit.set_facecolor('none')
    ax1_profit.bar(product_pareto_profit['Product Name'], product_pareto_profit['Profit'], color='skyblue')
    ax1_profit.set_xticks(range(len(product_pareto_profit['Product Name'])))
    ax1_profit.set_xticklabels(product_pareto_profit['Product Name'], rotation=60, ha='right')
    ax1_profit.set_ylabel('Profit', color='white')
    ax1_profit.tick_params(axis='x', colors='white')
    ax1_profit.tick_params(axis='y', colors='white')

    ax2_profit = ax1_profit.twinx()
    ax2_profit.plot(product_pareto_profit['Product Name'], product_pareto_profit['cum_profit_pct'], color='red', marker='o')
    ax2_profit.set_ylabel('Cumulative %', color='white')
    ax2_profit.tick_params(axis='y', colors='white')
    ax2_profit.set_ylim(0, 120)
    ax2_profit.axhline(80, color='green', linestyle='--', label='80% Cumulative Profit')
    legend = ax2_profit.legend(loc='upper right')
    legend.get_frame().set_facecolor('none')
    legend.get_frame().set_edgecolor('none')
    plt.setp(legend.get_texts(), color='white')
    ax1_profit.set_title("Pareto Chart - Profit Concentration", color='white')
    plt.tight_layout()
    st.pyplot(fig_profit_pareto)

    # Dependency Indicators (Regional)
    st.subheader('Regional Revenue Dependency Indicator')
    region_df = df_filtered.groupby('Region').agg({
        'Sales': 'sum',
        'Profit': 'sum'
    }).reset_index()
    region_df = region_df.sort_values(by='Sales', ascending=False)
    region_df['Revenue_%'] = region_df['Sales'] / region_df['Sales'].sum() * 100
    region_df['Cum_Revenue_%'] = region_df['Revenue_%'].cumsum()
    
    top_regions = region_df.head(2)
    dependency = top_regions['Revenue_%'].sum()

    st.write(f"**Top 2 Regions Contribution: {dependency:.2f}%**")
    if dependency > 70:
        st.warning("⚠️ Over-dependency Risk: Few regions dominate revenue. Consider diversification.")
    else:
        st.info("✅ Balanced regional distribution.")
    st.dataframe(region_df[['Region', 'Sales', 'Revenue_%', 'Cum_Revenue_%']].round(2))
