from datetime import datetime
import streamlit as st

import pandas as pd

import plotly.express as px
import plotly.graph_objects as go

st.set_page_config(
    page_title="Osmosis Stablecoins",
    page_icon=":microscope:",
    layout="wide",
    menu_items=dict(About="it's a work of joker#2418"),
)
st.title("Osmosis Stablecoin dominance")

hide_st_style = """
            <style>
            #MainMenu {visibility: hidden;}
            footer {visibility: hidden;}
            header {visibility: hidden;}
            </style>
            """
st.markdown(hide_st_style, unsafe_allow_html=True)


@st.cache(show_spinner=True)
def load_and_process_data():
    tfx = pd.read_json(
        "https://node-api.flipsidecrypto.com/api/v2/queries/d16b470b-9e22-492e-aa13-51b9047e7a61/data/latest"
    )
    to_stbl_swaps = pd.read_json(
        "https://node-api.flipsidecrypto.com/api/v2/queries/c97dc80b-cf50-497b-857f-4529bef247d2/data/latest"
    )
    from_stbl_swaps = pd.read_json(
        "https://node-api.flipsidecrypto.com/api/v2/queries/d26867a8-93a0-428b-9549-7ec6d5d7af40/data/latest"
    )
    ust_price = pd.read_json(
        "https://api.coingecko.com/api/v3/coins/terrausd/market_chart?vs_currency=usd&days=200&interval=daily"
    )
    ust_price["date"] = ust_price["prices"].apply(lambda x: x[0])
    ust_price["price"] = ust_price["prices"].apply(lambda x: x[1])
    ust_price["date"] = pd.to_datetime(ust_price["date"], unit="ms").dt.date
    ust_price = ust_price[:-1][["date", "price"]]
    ust_price["symbol"] = "USTC"
    ust_price["date"] = pd.to_datetime(ust_price["date"])

    tfx.DATE = pd.to_datetime(tfx.DATE)
    to_stbl_swaps.DATE = pd.to_datetime(to_stbl_swaps.DATE)
    from_stbl_swaps.DATE = pd.to_datetime(from_stbl_swaps.DATE)

    tfx = tfx.fillna(0)
    to_stbl_swaps = to_stbl_swaps.fillna(0)
    from_stbl_swaps = from_stbl_swaps.fillna(0)

    tfx = tfx.merge(
        ust_price, left_on=["DATE", "TOKEN"], right_on=["date", "symbol"], how="left"
    )
    tfx.price = tfx.price.fillna(1)
    tfx["usd_amount"] = tfx.Amount * tfx.price
    tfx["usd_ibc_amount"] = tfx["IBC-Out amount"] * tfx.price

    to_stbl_swaps = to_stbl_swaps.merge(
        ust_price, left_on=["DATE", "TO_TOKEN"], right_on=["date", "symbol"], how="left"
    )
    to_stbl_swaps.price = to_stbl_swaps.price.fillna(1)
    to_stbl_swaps["usd_amount"] = to_stbl_swaps.TO_AMOUNT * to_stbl_swaps.price

    from_stbl_swaps = from_stbl_swaps.merge(
        ust_price,
        left_on=["DATE", "FROM_TOKEN"],
        right_on=["date", "symbol"],
        how="left",
    )
    from_stbl_swaps.price = from_stbl_swaps.price.fillna(1)
    from_stbl_swaps["usd_amount"] = from_stbl_swaps.FROM_AMOUNT * from_stbl_swaps.price

    return tfx, to_stbl_swaps, from_stbl_swaps


tfx, to_stbl_swaps, from_stbl_swaps = load_and_process_data()

selected_token = st.sidebar.multiselect(
    "What stablecoins you want to see",
    (tfx.TOKEN.unique()),
    (tfx.TOKEN.unique()),
)
st.sidebar.text("Please pick a date range: (YY/MM/DD)")
slider_start = st.sidebar.slider(
    "Start date:",
    min_value=min(tfx.DATE).to_pydatetime(),
    max_value=max(tfx.DATE).to_pydatetime(),
    value=min(tfx.DATE).to_pydatetime(),
    format="YY/MM/DD",
)

slider_end = st.sidebar.slider(
    "End Date:",
    min_value=slider_start,
    max_value=max(tfx.DATE).to_pydatetime(),
    value=max(tfx.DATE).to_pydatetime(),
    format="YY/MM/DD",
)

fig_all_tfx = go.Figure()

tfx_vis = tfx[tfx.TOKEN.isin(list(selected_token))]

tfx_vis = tfx_vis[tfx_vis.DATE >= slider_start]
tfx_vis = tfx_vis[tfx_vis.DATE <= slider_end]

to_swap_vis = to_stbl_swaps[to_stbl_swaps.TO_TOKEN.isin(list(selected_token))]
# to_swap_vis = to_swap_vis[to_swap_vis.FROM_TOKEN.isin(list(selected_token))]

to_swap_vis = to_swap_vis[to_swap_vis.DATE >= slider_start]
to_swap_vis = to_swap_vis[to_swap_vis.DATE <= slider_end]

# from_swap_vis = from_stbl_swaps[from_stbl_swaps.TO_TOKEN.isin(list(selected_token))]
from_swap_vis = from_stbl_swaps[from_stbl_swaps.FROM_TOKEN.isin(list(selected_token))]

from_swap_vis = from_swap_vis[from_swap_vis.DATE >= slider_start]
from_swap_vis = from_swap_vis[from_swap_vis.DATE <= slider_end]


fig_all_tfx = px.bar(
    tfx_vis[["DATE", "TOKEN", "usd_amount"]],
    x="DATE",
    y="usd_amount",
    color="TOKEN",
    labels={"DATE": "Date", "TOKEN": "Coin name", "usd_amount": "Dollar value"},
    title="All Stablecoins transfers",
    template="plotly_dark",
)


st.plotly_chart(fig_all_tfx, use_container_width=True)

st.text(
    f"Dominant stablecoin in transfers during {slider_start.date().strftime('%Y-%B-%d')} to {slider_end.date().strftime('%Y-%B-%d')}"
)
fig_all_tfx_pie = px.pie(
    tfx_vis[["TOKEN", "usd_amount"]].groupby("TOKEN").sum().reset_index(),
    names="TOKEN",
    values="usd_amount",
    color="TOKEN",
    labels={"DATE": "Date", "TOKEN": "Coin name", "usd_amount": "Dollar value"},
    template="plotly_dark",
    color_discrete_sequence=px.colors.sequential.solar_r,
)


st.plotly_chart(fig_all_tfx_pie, use_container_width=True)


fig_ibc_tfx = go.Figure()

fig_ibc_tfx = px.bar(
    tfx_vis[["DATE", "TOKEN", "usd_ibc_amount"]],
    x="DATE",
    y="usd_ibc_amount",
    color="TOKEN",
    labels={
        "DATE": "Date",
        "TOKEN": "Coin name",
        "usd_ibc_amount": "Dollar value",
    },
    title="Stablecoins transferred out of IBC",
    template="plotly_dark",
)


st.plotly_chart(fig_ibc_tfx, use_container_width=True)

st.text(
    f"Dominant stablecoin in IBC transfer(out) during {slider_start.date().strftime('%Y-%B-%d')} to {slider_end.date().strftime('%Y-%B-%d')}"
)
fig_all_tfx_pie = px.pie(
    tfx_vis[["TOKEN", "usd_ibc_amount"]].groupby("TOKEN").sum().reset_index(),
    names="TOKEN",
    values="usd_ibc_amount",
    color="TOKEN",
    labels={"DATE": "Date", "TOKEN": "Coin name", "usd_ibc_amount": "Dollar value"},
    template="plotly_dark",
    color_discrete_sequence=px.colors.sequential.Inferno_r,
)


st.plotly_chart(fig_all_tfx_pie, use_container_width=True)


fig_from_swaps = go.Figure()

fig_from_swaps = px.bar(
    from_swap_vis[["DATE", "FROM_TOKEN", "usd_amount"]],
    x="DATE",
    y="usd_amount",
    color="FROM_TOKEN",
    labels={"DATE": "Date"},
    title="Swaps FROM stablecoins to other coins",
    template="plotly_dark",
)


st.plotly_chart(fig_from_swaps, use_container_width=True)


fig_to_swaps = go.Figure()

fig_to_swaps = px.bar(
    to_swap_vis[["DATE", "TO_TOKEN", "usd_amount"]],
    x="DATE",
    y="usd_amount",
    color="TO_TOKEN",
    labels={"DATE": "Date"},
    title="Swaps TO stablecoins from other coins",
    template="plotly_dark",
)


st.plotly_chart(fig_to_swaps, use_container_width=True)
