from datetime import date, datetime
import os
import pandas as pd
import streamlit as st
import requests
import json
import time

import plotly.express as px
import plotly.graph_objects as go

df = pd.read_parquet('data/pool_txs_proc.parquet')