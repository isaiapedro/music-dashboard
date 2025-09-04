
# Dashboard for 1001 Albums by Pedro
from narwhals import col
import streamlit as st
import streamlit.components.v1 as components
import pandas as pd
import plotly.express as px
import plotly.graph_objects as go
from collections import Counter
import math
from PIL import Image

# Page config
st.set_page_config(page_title="1001 Albums by Pedro", layout="wide")
# --- Custom CSS Styling ---
st.markdown("""
    <style>
        body {
            background-color: #f4f4f4;
        }
        .main-title {
            background-color: #636EFA;
            padding: 20px;
            border-radius: 8px;
            color: white;
            text-align: center;
            font-size: 32px;
            font-weight: bold;
            margin-bottom: 20px;
        }
        footer {visibility: hidden;}

    background-color: #f4f4f4;

    </style>
""", unsafe_allow_html=True)