import pandas as pd
import streamlit as st
from supabase import create_client

supabase = create_client(
    st.secrets["SUPABASE_URL"],
    st.secrets["SUPABASE_KEY"]
)

def ensure_dirs():
    pass

def append_record(record: dict):
    supabase.table("records").insert(record).execute()

def load_records():
    response = supabase.table("records").select("*").execute()

    data = response.data

    if not data:
        return pd.DataFrame()

    return pd.DataFrame(data)
