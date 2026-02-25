import streamlit as st
import pandas as pd
from reportlab.lib.pagesizes import A4
from reportlab.pdfgen import canvas
from io import BytesIO

# --- PAGE CONFIG ---
st.set_page_config(page_title="GEIMS Estimate Tool", layout="wide", page_icon="🏥")

# --- LIVE LINK ---
GOOGLE_SHEET_CSV_URL = "https://docs.google.com/spreadsheets/d/e/2PACX-1vQG6vTU99xSFQEnORPp-5Mhp4hZ-fMIT_yb-daMsmff8t-K-1ggynkxHZi1UsbYE7o9bfo08ybKbd0X/pub?output=csv"

@st.cache_data(ttl=60)
def load_live_data(url):
    try:
        # 1. Load the sheet without any headers first
        raw = pd.read_csv(url, header=None)
        
        # 2. Find the row index where 'Department' exists
        header_idx = None
        for i, row in raw.iterrows():
            if "Department" in row.values:
                header_idx = i
                break
        
        if header_idx is None:
            return "ERROR: Could not find 'Department' in your sheet."

        # 3. Reload starting from that row
        df = pd.read_csv(url, skiprows=header_idx)
        
        # 4. Clean column names (Remove newlines and extra spaces)
        df.columns = [str(c).strip().replace('\n', ' ') for c in df.columns]
        
        # 5. Remove any completely empty rows
        df = df.dropna(subset=['Department', 'Service Name'], how='all')
        return df
    except Exception as e:
        return f"ERROR: {str(e)}"

df_surgery = load_live_data(GOOGLE_SHEET_CSV_URL)

# GEIMS 2025 Fixed Policy Rates
ROOM_DATA = {
    "Economy": {"Rent": 2500, "Consult": 700, "Nursing": 500, "RMO": 700},
    "Double": {"Rent": 4500, "Consult": 900, "Nursing": 600, "RMO": 800},
    "Single/ ICU": {"Rent": 7500, "Consult": 1200, "Nursing": 600, "RMO": 800},
    "Classic Deluxe": {"Rent": 10000, "Consult": 1500, "Nursing": 600, "RMO": 800},
    "Suite": {"Rent": 33000, "Consult": 2000, "Nursing": 2800, "RMO": 3000},
}

# --- MAIN UI ---
st.title("🏥 GEIMS Hospital Estimate Generator")

# Check if data loaded correctly or returned an error string
if isinstance(df_surgery, str):
    st.error(df_surgery)
    st.info("💡 Make sure your Google Sheet has a column named 'Department' and 'Service Name' in the same row.")
else:
    with st.sidebar:
        st.header("Patient Setup")
        pat_name = st.text_input("Patient Name", "Anuj Gill")
        room_cat = st.selectbox("Bed Category", list(ROOM_DATA.keys()))
        stay_days = st.number_input("Days of Stay", min_value=1, value=1)
        st.divider()
        st.info("Policy: MRD Charge (450) and Diet (100/day) applied.")

    # Filter Logic
    try:
        depts = sorted(df_surgery['Department'].dropna().unique())
        sel_dept = st.selectbox("Select Department", depts)
        
        procs = df_surgery[df_surgery['Department'] == sel_dept]['Service Name'].dropna().unique()
        sel_proc = st.selectbox("Select Surgery", procs)

        # Match Rate
        row_data = df_surgery[df_surgery['Service Name'] == sel_proc]
        s_fee = row_data[room_cat].values[0]
        
        r = ROOM_DATA[room_cat]
        
        breakdown = {
            f"Surgery: {sel_proc}": float(s_fee),
            "Room Rent": r['Rent'] * stay_days,
            "Consultation (2/day)": (r['Consult'] * 2) * stay_days,
            "Nursing & RMO": (r['Nursing'] + r['RMO']) * stay_days,
            "MRD Fee": 450.0,
            "Diet Charges": 100.0 * stay_days
        }
        
        st.subheader(f"Summary for {pat_name}")
        st.table(pd.DataFrame(list(breakdown.items()), columns=["Description", "Amount"]))
        
        total = sum(breakdown.values())
        st.metric("Grand Total", f"₹ {total:,.2f}")
        
    except Exception as e:
        st.warning("Please select a valid procedure to calculate.")
