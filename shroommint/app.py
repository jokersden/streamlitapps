from datetime import date, datetime
import os
import pandas as pd
import streamlit as st
import requests
import json
import time

import plotly.express as px
import plotly.graph_objects as go

API_KEY = os.getenv("API_KEY")


def create_query(sql_query, ttl_minutes=15):
    r = requests.post(
        "https://node-api.flipsidecrypto.com/queries",
        data=json.dumps({"sql": sql_query, "ttlMinutes": ttl_minutes}),
        headers={
            "Accept": "application/json",
            "Content-Type": "application/json",
            "x-api-key": API_KEY,
        },
    )
    if r.status_code != 200:
        raise Exception(
            "Error creating query, got response: "
            + r.text
            + "with status code: "
            + str(r.status_code)
        )

    return json.loads(r.text)


def get_query_results(token):
    r = requests.get(
        "https://node-api.flipsidecrypto.com/queries/" + token,
        headers={
            "Accept": "application/json",
            "Content-Type": "application/json",
            "x-api-key": API_KEY,
        },
    )
    if r.status_code != 200:
        raise Exception(
            "Error getting query results, got response: "
            + r.text
            + "with status code: "
            + str(r.status_code)
        )

    data = json.loads(r.text)
    if data["status"] == "running":
        time.sleep(10)
        return get_query_results(token)

    return pd.DataFrame(data["results"], columns=data["columnLabels"])


st.set_page_config(
    page_title="ShroomDK",
    page_icon=":mushroom:",
    layout="wide",
    menu_items=dict(About="it's a work of joker#2418"),
)
st.title(":mushroom: ShroomDK :mushroom:")

hide_st_style = """
            <style>
            #MainMenu {visibility: hidden;}
            footer {visibility: hidden;}
            header {visibility: hidden;}
            </style>
            """
st.markdown(hide_st_style, unsafe_allow_html=True)


# @st.cache(allow_output_mutation=True, show_spinner=False, ttl=600)
def get_data(sql_query):
    query = create_query(sql_query)
    token = query.get("token")
    return get_query_results(token)


nft_query = """
    select block_timestamp, tokenid, nft_from_address, nft_to_address, event_type from ethereum.core.ez_nft_transfers 
    where nft_address='0xdfb57b6e16ddb97aeb8847386989f4dca7202146'
"""

god_mode = """
select block_timestamp, event_type, nft_from_address, nft_to_address, tokenid from ethereum.core.ez_nft_transfers 
  where nft_address='0x903e2f5d42ee23156d548dd46bb84b7873789e44'
"""

bounty_rewarders = """
select count(distinct event_inputs:to) as bounty_hunters from ethereum.core.fact_event_logs
  where origin_from_address='0xc2f41b3a1ff28fd2a6eee76ee12e51482fcfd11f'
  and event_inputs:to in (select nft_to_address from ethereum.core.ez_nft_transfers
  where nft_address='0xdfb57b6e16ddb97aeb8847386989f4dca7202146')
"""

tx_fails = """
select block_timestamp, from_address, to_address, 'Ethereum' as chain, tx_fee
from ethereum.core.fact_transactions
where to_address='0xdfb57b6e16ddb97aeb8847386989f4dca7202146'
  and status = 'FAIL'
union all
select block_timestamp, from_address, to_address, 'Arbitrum' as chain, tx_fee
from arbitrum.core.fact_transactions
where to_address='0xdfb57b6e16ddb97aeb8847386989f4dca7202146'
union all
select block_timestamp, from_address, to_address, 'Binance' as chain, tx_fee
from bsc.core.fact_transactions
where to_address='0xdfb57b6e16ddb97aeb8847386989f4dca7202146'
union all
select block_timestamp, from_address, to_address, 'Polygon' as chain, tx_fee
from polygon.core.fact_transactions
where to_address='0xdfb57b6e16ddb97aeb8847386989f4dca7202146'
"""

with st.spinner("Hang on... Loading Shrooms from ShroomDK...."):
    nft_df = get_data(nft_query)
    nft_raw_god_df = get_data(god_mode)
    bouty_hunter_df = get_data(bounty_rewarders)
    tx_fail_df = get_data(tx_fails)

nft_mint_df = nft_df[nft_df.EVENT_TYPE == "mint"]
nft_mint_df.BLOCK_TIMESTAMP = pd.to_datetime(nft_mint_df.BLOCK_TIMESTAMP)
nft_mint_df = nft_mint_df.sort_values(by="BLOCK_TIMESTAMP")

nft_trans_df = nft_df[nft_df.EVENT_TYPE == "other"]
nft_trans_df.BLOCK_TIMESTAMP = pd.to_datetime(nft_trans_df.BLOCK_TIMESTAMP)
nft_trans_df = nft_trans_df.sort_values(by="BLOCK_TIMESTAMP")

tx_fail_df.BLOCK_TIMESTAMP = pd.to_datetime(tx_fail_df.BLOCK_TIMESTAMP)
tx_fail_df = tx_fail_df.sort_values(by="BLOCK_TIMESTAMP")

shroom_hodl_cols = ["BLOCK_TIMESTAMP", "NFT_TO_ADDRESS", "TOKENID"]
shroom_hdlers_df = pd.concat(
    [nft_mint_df[shroom_hodl_cols], nft_trans_df[shroom_hodl_cols]]
)
shroom_hdlers_df.BLOCK_TIMESTAMP = pd.to_datetime(shroom_hdlers_df.BLOCK_TIMESTAMP)
shroom_hdlers_df = shroom_hdlers_df.sort_values(by="BLOCK_TIMESTAMP")

nft_raw_god_df.BLOCK_TIMESTAMP = pd.to_datetime(nft_raw_god_df.BLOCK_TIMESTAMP)
nft_raw_god_df = nft_raw_god_df.sort_values(by="BLOCK_TIMESTAMP")
nft_god_df = nft_raw_god_df.drop_duplicates("TOKENID", keep="last").reset_index(
    drop=True
)
nft_god_df = shroom_hdlers_df[
    shroom_hdlers_df.NFT_TO_ADDRESS.isin(nft_god_df.NFT_TO_ADDRESS)
]

nft_mints_by_the_hour = (
    nft_mint_df.groupby(nft_mint_df.BLOCK_TIMESTAMP.dt.hour)
    .count()
    .reset_index(drop=True)
)

nft_mints_by_hour = (
    nft_mint_df.groupby(nft_mint_df.BLOCK_TIMESTAMP.dt.floor("h"))
    .count()["TOKENID"]
    .reset_index()
)

col1, col2, col3, col4, col5 = st.columns(5)

nft_mint_df = nft_mint_df.drop_duplicates("TOKENID")
col1.metric(
    label="Number of ShroomDKs minted",
    value=len(nft_mint_df.TOKENID),
    delta=f"{(int(len(nft_mint_df[nft_mint_df.BLOCK_TIMESTAMP.dt.date == date.today()])))} today",
)
col3.metric(
    label="Number of transfers",
    value=len(nft_trans_df),
    delta=f"{(int(len(nft_trans_df[nft_trans_df.BLOCK_TIMESTAMP.dt.date == date.today()])))} today",
)
col2.metric(
    label="Number of ShroomDK Minters",
    value=int(nft_mint_df.NFT_TO_ADDRESS.nunique()),
    delta=f"{(int(nft_mint_df[nft_mint_df.BLOCK_TIMESTAMP.dt.date == date.today()].NFT_TO_ADDRESS.nunique()))} today",
)
shroom_hodl_proc = shroom_hdlers_df.drop_duplicates("TOKENID", keep="last")
col4.metric(
    label="Number of Shroom HODLers",
    value=(shroom_hodl_proc.NFT_TO_ADDRESS.nunique()),
    delta=f"{(shroom_hodl_proc[shroom_hodl_proc.BLOCK_TIMESTAMP.dt.date == date.today()].NFT_TO_ADDRESS.nunique())} today",
)
col5.metric(
    label="GOD mode and Shroom HODLers",
    value=len(nft_god_df.drop_duplicates("NFT_TO_ADDRESS")),
    delta=f"{round(len(nft_god_df.drop_duplicates('NFT_TO_ADDRESS'))*100 / int(shroom_hodl_proc.NFT_TO_ADDRESS.nunique()), 2)}% of all Shroom HODLers",
    delta_color="off",
)
st.write("")

col_chart1, col_chart2 = st.columns(2)
tx_fails = tx_fail_df.groupby("CHAIN").count()["TO_ADDRESS"].reset_index()
fig_tx_fails = px.pie(
    values=tx_fails.TO_ADDRESS,
    names=tx_fails.CHAIN,
    title="Failed mints and mints on wrong chains",
    color_discrete_sequence=px.colors.sequential.Purples_r,
    labels=dict(values="Failures", names="Chain"),
)
fig_tx_fails.update_traces(textposition="inside", textinfo="percent+value+label")
col_chart1.plotly_chart(
    fig_tx_fails,
    use_container_width=True,
)
col_chart2.plotly_chart(
    px.pie(
        values=[
            bouty_hunter_df["BOUNTY_HUNTERS"][0],
            shroom_hodl_proc.NFT_TO_ADDRESS.nunique()
            - bouty_hunter_df["BOUNTY_HUNTERS"][0],
        ],
        names=["Bounty hunters", "Shroom hunters"],
        title="How many HODLers have received any bounty payments from flipside",
        color_discrete_sequence=px.colors.sequential.Jet_r,
        labels=dict(values=" ", names=""),
    ),
    use_container_width=True,
)
nft_minter_df = (
    nft_mint_df.drop_duplicates("NFT_TO_ADDRESS")
    .groupby(nft_mint_df["BLOCK_TIMESTAMP"].dt.floor("h"))
    .count()["TOKENID"]
    .reset_index()
)

fig = go.Figure()
fig = px.bar(
    nft_mints_by_hour,
    x="BLOCK_TIMESTAMP",
    y="TOKENID",
    template="plotly_dark",
    labels=dict(
        BLOCK_TIMESTAMP="DateTime",
        TOKENID="Mints",
    ),
    title="Number of Mints and New minters overtime",
)
fig.add_trace(
    go.Scatter(
        x=nft_minter_df.BLOCK_TIMESTAMP,
        y=nft_minter_df.TOKENID,
        name="Number of new minters",
    )
)
fig.update_xaxes(title="Time")
fig.update_yaxes(title="Number of mints")
st.plotly_chart(fig, use_container_width=True)

col1_ch2, col2_ch2 = st.columns(2)

fig = go.Figure()
fig = px.area(
    nft_mints_by_the_hour,
    x=nft_mints_by_the_hour.index,
    y="TOKENID",
    template="plotly_dark",
    labels=dict(index="Hour of the day", TOKENID="Mints"),
    title="Most popular hour of the day for minting (UTC time)",
    color_discrete_sequence=px.colors.sequential.Agsunset_r,
)
fig.update_xaxes(title="Hour of the day")
fig.update_yaxes(title="Number of mints")
col1_ch2.plotly_chart(fig, use_container_width=True)

fig = go.Figure()
fig = px.line(
    nft_god_df.drop_duplicates("NFT_TO_ADDRESS")
    .groupby(nft_god_df["BLOCK_TIMESTAMP"].dt.floor("h"))
    .count()["TOKENID"]
    .reset_index(),
    x="BLOCK_TIMESTAMP",
    y="TOKENID",
    template="plotly_dark",
    labels=dict(
        BLOCK_TIMESTAMP="DateTime",
        TOKENID="Mints",
    ),
    title="Number of New minters and minters HODLing God Mode",
)
fig.add_trace(
    go.Bar(
        x=nft_minter_df.BLOCK_TIMESTAMP,
        y=nft_minter_df.TOKENID,
        name="Number of new minters",
    )
)
fig.update_xaxes(title="Time")
fig.update_yaxes(title="Number of mints")
col2_ch2.plotly_chart(fig, use_container_width=True)

tx_fees_df = (
    tx_fail_df.groupby([tx_fail_df.BLOCK_TIMESTAMP.dt.floor("h"), "CHAIN"])
    .count()["TO_ADDRESS"]
    .reset_index()
)

fig_fees = go.Figure()
fig_fees = px.bar(
    tx_fees_df,
    x="BLOCK_TIMESTAMP",
    y="TO_ADDRESS",
    color="CHAIN",
    title="Number of failed transactions overtime",
    labels=dict(BLOCK_TIMESTAMP="Time", TO_ADDRESS="Failed txs"),
)
fig.update_xaxes(title="Time")
fig.update_yaxes(title="Number of failed txs", selector=False)
st.plotly_chart(fig_fees, use_container_width=True)
