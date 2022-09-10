from datetime import datetime
import streamlit as st

import pandas as pd
import numpy as np

from shroomdk import ShroomDK

import plotly.express as px
import plotly.graph_objects as go
from plotly.subplots import make_subplots
import plotly.io as pio

import os

pio.templates.default = "plotly_dark"

API_KEY = os.getenv("API_KEY")

st.set_page_config(
    page_title="Ethereum - Miners",
    page_icon=":hammer:",
    layout="wide",
    menu_items=dict(About="it's a work of joker#2418"),
)
st.title("::hammer: Ethereum Miners ::hammer:")

hide_st_style = """
            <style>
            #MainMenu {visibility: hidden;}
            footer {visibility: hidden;}
            header {visibility: hidden;}
            </style>
            """
st.markdown(hide_st_style, unsafe_allow_html=True)

sdk = ShroomDK(API_KEY)


@st.cache(allow_output_mutation=True, show_spinner=False, ttl=30 * 60)
def load_data(sql):
    return pd.DataFrame(sdk.query(sql).records)


with st.spinner("Mining some data, Please wait..."):
    df_daily_miners = load_data(
        """ 
    select 
        block_timestamp::date as date,
        count(distinct miner) as miners,
        sum(tx_count) as txs
    from ethereum.core.fact_blocks
    group by date
    order by date
            """
    )

    df_year_summary = load_data(
        """
select
    date_trunc(year, block_timestamp) as year,
    avg(tx_count) as avg,
    min(tx_count) as min,
    max(tx_count) as max,
    median(tx_count) as median,
    count(case when tx_count < 10 then miner end) as "less than 10 transactions",
    count(case when tx_count >= 10 and tx_count < 100 then miner end) as "10 to 100 transactions",
    count(case when tx_count >= 100 and tx_count < 200 then miner end) as "100 to 200 transactions",
    count(case when tx_count >= 200 and tx_count < 300 then miner end) as "200 to 300 transactions",
    count(case when tx_count >= 300 and tx_count < 500 then miner end) as "300 to 500 transactions",
    count(case when tx_count >= 500 then miner end) as "more than 500 transactions"
  from ethereum.core.fact_blocks
  group by year
  order by year
    """
    )
    df_miner_category = load_data(
        """
    select miner,
    count(tx_count) as tot,
    date_trunc(year, block_timestamp) as year,
    avg(tx_count) as avg,
    min(tx_count) as min,
    max(tx_count) as max,
    median(tx_count) as median,
  count(case when tx_count < 10 then miner end) as "less than 10 transactions",
  count(case when tx_count >= 10 and tx_count < 100 then miner end) as "10 to 100 transactions",
  count(case when tx_count >= 100 and tx_count < 200 then miner end) as "100 to 200 transactions",
  count(case when tx_count >= 200 and tx_count < 300 then miner end) as "200 to 300 transactions",
  count(case when tx_count >= 300 and tx_count < 500 then miner end) as "300 to 500 transactions",
  count(case when tx_count >= 500 then miner end) as "more than 500 transactions"
  from ethereum.core.fact_blocks
  group by miner, year
    """
    )

df_daily_miners.date = pd.to_datetime(df_daily_miners.date)

col1, col2 = st.columns(2)
slider_start = col1.slider(
    "Start date:",
    min_value=min(df_daily_miners.date).to_pydatetime(),
    max_value=max(df_daily_miners.date).to_pydatetime(),
    value=min(df_daily_miners.date).to_pydatetime(),
    format="YYYY/MM/DD",
)

slider_end = col2.slider(
    "End Date:",
    min_value=slider_start,
    max_value=max(df_daily_miners.date).to_pydatetime(),
    value=max(df_daily_miners.date).to_pydatetime(),
    format="YYYY/MM/DD",
)
st.markdown("---")
st.subheader("Block summary")
mchart1, mchart2 = st.columns(2)
df_daily_miners_vis = df_daily_miners[df_daily_miners.date >= slider_start]
df_daily_miners_vis = df_daily_miners_vis[df_daily_miners_vis.date <= slider_end]
fig_miners = make_subplots(specs=[[{"secondary_y": True}]])
fig_miners.add_trace(
    go.Scatter(
        x=df_daily_miners_vis.date,
        y=df_daily_miners_vis.miners,
        name="Number of miners",
    )
)
fig_miners.add_trace(
    go.Scatter(
        x=df_daily_miners_vis.date,
        y=df_daily_miners_vis.txs,
        name="Number of transactions",
    ),
    secondary_y=True,
)

fig_miners.update_xaxes(title="Year")
fig_miners.update_yaxes(title="Miners")
fig_miners.update_yaxes(title="Transactions", secondary_y=True)
fig_miners.update_layout(
    title="Daily transactions and miners",
    legend=dict(yanchor="top", y=0.99, xanchor="left", x=0.01),
)
mchart1.plotly_chart(fig_miners, use_container_width=True)

df_year_summary.year = pd.to_datetime(df_year_summary.year)
df_year_summary_vis = df_year_summary[df_year_summary.year >= slider_start]
df_year_summary_vis = df_year_summary_vis[df_year_summary_vis.year <= slider_end]
fig_year_summary = px.line(
    df_year_summary_vis,
    x="year",
    y=["max", "median", "avg"],
    title="Per block summary of transactions mined by year",
    labels=dict(max="Max", median="Median", avg="Average"),
)
fig_year_summary.update_xaxes(title="Year")
fig_year_summary.update_yaxes(title="Transactions")
fig_year_summary.update_layout(
    legend=dict(orientation="h", yanchor="bottom", y=1.02, xanchor="right", x=1),
    legend_title_text="",
)
mchart2.plotly_chart(fig_year_summary, use_container_width=True)
st.info(
    f"The number of transactions that were mined in early stages of Ethereum seems to be very low compared to the amount of transactions"
    f" We have today, the transaction count per block mined seems to have risen since late 2017 with the end of the 2017 crypto winter. The max transactions had peaked in 2021 and current average is {round(df_year_summary[-1:].avg.values[0], 2)} transactions per minded block"
    " However the number of miners have fallen sharply since the beginning.",
    icon="💹",
)

chart3, chart4 = st.columns(2)
df_miner_category.year = pd.to_datetime(df_miner_category.year)
df_miner_category_vis = df_miner_category[df_miner_category.year >= slider_start]
df_miner_category_vis = df_miner_category_vis[df_miner_category_vis.year <= slider_end]
cats = [
    "less than 10 transactions",
    "10 to 100 transactions",
    "100 to 200 transactions",
    "200 to 300 transactions",
    "300 to 500 transactions",
    "more than 500 transactions",
]

yearly_categories = df_miner_category_vis.groupby("year").sum()[cats].reset_index()

fig_yearly_cats = px.bar(yearly_categories, x="year", y=cats, text_auto=True)
fig_yearly_cats.update_layout(
    legend_title_text="Catgories",
    title="Number of transactions per mined block changed overtime",
)
fig_yearly_cats.update_xaxes(title="Year")
fig_yearly_cats.update_yaxes(title="Number of transactions")
chart3.plotly_chart(fig_yearly_cats, use_container_width=True)

yearly_categories["10 or less transactions %"] = (
    yearly_categories["less than 10 transactions"]
    * 100
    / (
        yearly_categories["less than 10 transactions"]
        + yearly_categories["10 to 100 transactions"]
        + yearly_categories["100 to 200 transactions"]
        + yearly_categories["200 to 300 transactions"]
        + yearly_categories["300 to 500 transactions"]
        + yearly_categories["more than 500 transactions"]
    )
)
yearly_categories["10 to 100 transactions %"] = (
    yearly_categories["10 to 100 transactions"]
    * 100
    / (
        yearly_categories["less than 10 transactions"]
        + yearly_categories["10 to 100 transactions"]
        + yearly_categories["100 to 200 transactions"]
        + yearly_categories["200 to 300 transactions"]
        + yearly_categories["300 to 500 transactions"]
        + yearly_categories["more than 500 transactions"]
    )
)
yearly_categories["100 to 200 transactions %"] = (
    yearly_categories["100 to 200 transactions"]
    * 100
    / (
        yearly_categories["less than 10 transactions"]
        + yearly_categories["10 to 100 transactions"]
        + yearly_categories["100 to 200 transactions"]
        + yearly_categories["200 to 300 transactions"]
        + yearly_categories["300 to 500 transactions"]
        + yearly_categories["more than 500 transactions"]
    )
)
yearly_categories["200 to 300 transactions %"] = (
    yearly_categories["200 to 300 transactions"]
    * 100
    / (
        yearly_categories["less than 10 transactions"]
        + yearly_categories["10 to 100 transactions"]
        + yearly_categories["100 to 200 transactions"]
        + yearly_categories["200 to 300 transactions"]
        + yearly_categories["300 to 500 transactions"]
        + yearly_categories["more than 500 transactions"]
    )
)
yearly_categories["300 to 500 transactions %"] = (
    yearly_categories["300 to 500 transactions"]
    * 100
    / (
        yearly_categories["less than 10 transactions"]
        + yearly_categories["10 to 100 transactions"]
        + yearly_categories["100 to 200 transactions"]
        + yearly_categories["200 to 300 transactions"]
        + yearly_categories["300 to 500 transactions"]
        + yearly_categories["more than 500 transactions"]
    )
)
yearly_categories["more than 500 transactions %"] = (
    yearly_categories["more than 500 transactions"]
    * 100
    / (
        yearly_categories["less than 10 transactions"]
        + yearly_categories["10 to 100 transactions"]
        + yearly_categories["100 to 200 transactions"]
        + yearly_categories["200 to 300 transactions"]
        + yearly_categories["300 to 500 transactions"]
        + yearly_categories["more than 500 transactions"]
    )
)

fig_year_perc = px.area(
    yearly_categories,
    x="year",
    y=[
        "10 or less transactions %",
        "10 to 100 transactions %",
        "100 to 200 transactions %",
        "200 to 300 transactions %",
        "300 to 500 transactions %",
        "more than 500 transactions %",
    ],
)
fig_year_perc.update_traces(line_width=0)
fig_year_perc.update_layout(
    legend_title_text="Catgories", title="Percentage of block transactions overtime"
)
fig_year_perc.update_yaxes(title="Percentage (%)")
fig_year_perc.update_xaxes(title="Year")
chart4.plotly_chart(fig_year_perc, use_container_width=True)

st.info(
    "It's clear that transaction per mined block has risen since the beginning. There were mostly blocks with less than 10 "
    "transaction per mined block at the beginning but overtime those blocks with smaller number of transactions has reduced significantly "
    "since 2020 we even see blocks that were mined with more than 500 transactions were going up. Overall 300 - 500 transaction block percentage has risen significantly since 2020."
    " 2021 is an interesting year as it sees only 16.3% of the blocks having 100 or less transaction compared to 33% in 2022, this could indicate the DeFi summer we had during that period."
)
st.markdown("---")
st.subheader("Miner activities")
miner_categories = df_miner_category_vis.groupby("miner").sum()[cats].reset_index()
miner_categories["10 or less transactions %"] = (
    miner_categories["less than 10 transactions"]
    * 100
    / (
        miner_categories["less than 10 transactions"]
        + miner_categories["10 to 100 transactions"]
        + miner_categories["100 to 200 transactions"]
        + miner_categories["200 to 300 transactions"]
        + miner_categories["300 to 500 transactions"]
        + miner_categories["more than 500 transactions"]
    )
)
miner_categories["10 to 100 transactions %"] = (
    miner_categories["10 to 100 transactions"]
    * 100
    / (
        miner_categories["less than 10 transactions"]
        + miner_categories["10 to 100 transactions"]
        + miner_categories["100 to 200 transactions"]
        + miner_categories["200 to 300 transactions"]
        + miner_categories["300 to 500 transactions"]
        + miner_categories["more than 500 transactions"]
    )
)
miner_categories["100 to 200 transactions %"] = (
    miner_categories["100 to 200 transactions"]
    * 100
    / (
        miner_categories["less than 10 transactions"]
        + miner_categories["10 to 100 transactions"]
        + miner_categories["100 to 200 transactions"]
        + miner_categories["200 to 300 transactions"]
        + miner_categories["300 to 500 transactions"]
        + miner_categories["more than 500 transactions"]
    )
)
miner_categories["200 to 300 transactions %"] = (
    miner_categories["200 to 300 transactions"]
    * 100
    / (
        miner_categories["less than 10 transactions"]
        + miner_categories["10 to 100 transactions"]
        + miner_categories["100 to 200 transactions"]
        + miner_categories["200 to 300 transactions"]
        + miner_categories["300 to 500 transactions"]
        + miner_categories["more than 500 transactions"]
    )
)
miner_categories["300 to 500 transactions %"] = (
    miner_categories["300 to 500 transactions"]
    * 100
    / (
        miner_categories["less than 10 transactions"]
        + miner_categories["10 to 100 transactions"]
        + miner_categories["100 to 200 transactions"]
        + miner_categories["200 to 300 transactions"]
        + miner_categories["300 to 500 transactions"]
        + miner_categories["more than 500 transactions"]
    )
)
miner_categories["more than 500 transactions %"] = (
    miner_categories["more than 500 transactions"]
    * 100
    / (
        miner_categories["less than 10 transactions"]
        + miner_categories["10 to 100 transactions"]
        + miner_categories["100 to 200 transactions"]
        + miner_categories["200 to 300 transactions"]
        + miner_categories["300 to 500 transactions"]
        + miner_categories["more than 500 transactions"]
    )
)
fig_miner_dist = px.box(
    miner_categories,
    y=[
        "10 or less transactions %",
        "10 to 100 transactions %",
        "100 to 200 transactions %",
        "200 to 300 transactions %",
        "300 to 500 transactions %",
        "more than 500 transactions %",
    ],
    boxmode="overlay",
)
fig_miner_dist.update_xaxes(title="Mined block size category")
fig_miner_dist.update_yaxes(title="Percentage (%)")
st.plotly_chart(fig_miner_dist, use_container_width=True)
st.info(
    "This chart shows that how different miners interested in mining blocks with different transaction counts, for example there is ONLY 1 miner who has mined 92.3% of their blocks with 500+ transactions."
    " While there are miners who have 100% of their mined blocks had less than 10 transactions, but as we saw the transactions per block increased significantly since 2020, we see that miners who mined less than 10 transaction block reduced dramatically"
)

fig_10orless = px.histogram(
    miner_categories,
    x="10 or less transactions %",
    title="Do miners mine only smaller blocks",
)
fig_10orless.update_yaxes(title="Miners")
cat1, cat2 = st.columns(2)
cat1.plotly_chart(fig_10orless, use_container_width=True)

fig_500more = px.histogram(
    miner_categories,
    x="more than 500 transactions %",
    title="Or what percentage of larger blocks do miners mine",
)
fig_500more.update_yaxes(title="Miners")
cat2.plotly_chart(fig_500more, use_container_width=True)
st.info(
    "Looking at the smallest and largest block mines, we see that since 2020 only 9 miners had mined 90%+ of their blocks with less than 10 transactions"
    " while there are only 2 miners having more than 50% of their mined blocks with 500 or more transcations."
)

st.subheader(
    "Miners with 50%+ of their mined blocks which having more than 500 transactions in each block"
)
st.write(
    f"Here are the {len(miner_categories[miner_categories['more than 500 transactions %'] >= 50])} miners"
)
st.dataframe(
    miner_categories[
        miner_categories["more than 500 transactions %"] >= 50
    ].reset_index(drop=True)
)

st.subheader(
    "Miners with 90%+ of their mined blocks which having less than 60 transactions in each block"
)
st.write(
    f"Here are the {len(miner_categories[miner_categories['10 or less transactions %'] >= 90])} miners"
)
st.dataframe(
    miner_categories[miner_categories["10 or less transactions %"] >= 90].reset_index(
        drop=True
    )
)
st.subheader("")

st.warning(
    "To conclude, there's no general pattern where miners are either trying to mine only relatively large blocks or small blocks."
    " due to the fact that early days of Ethereum having blocks with smaller number of transactions we saw that many have higher percentage of "
    "mined blocks with smaller amount of transactions but with the cxplosion of number of transactions mined in a block since "
    "2020 we don't see any particular tendency of miners for either go for bigger or smaller blocks in terms of transaction counts. However, we found fe anomalies "
    "where 2 users had significantly higher 50%+ (and one with 90%+) of their mined blocks having 500 or more transactions and there are also 9 miners since 2020 with 90%+ of the their mined blocks containing less than 10 transactions."
)
with st.expander("Resources"):
    st.markdown(
        "Following velocity page has the queries used in this analysis: https://app.flipsidecrypto.com/velocity/queries/19b75d3b-aeec-4a7b-903b-2b560907a7ef"
    )
