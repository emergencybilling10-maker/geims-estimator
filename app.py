import streamlit as st
import pandas as pd

# --- PAGE CONFIG ---
st.set_page_config(page_title="GEIMS Estimate Tool", layout="wide", page_icon="🏥")

# --- YOUR LIVE LINK ---
GOOGLE_SHEET_CSV_URL = "https://docs.google.com/spreadsheets/d/e/2PACX-1vQG6vTU99xSFQEnORPp-5Mhp4hZ-fMIT_yb-daMsmff8t-K-1ggynkxHZi1UsbYE7o9bfo08ybKbd0X/pub?output=csv"

@st.cache_data(ttl=60)
def load_live_data(url):
    try:
        # Direct load since Row 1 is now the header
        df = pd.read_csv(url)
        
        # Clean column names (Remove spaces/newlines)
        df.columns = [str(c).strip().replace('\n', ' ') for c in df.columns]
        
        # Remove empty rows at the bottom
        df = df.dropna(subset=['Department', 'Service Name'], how='all')
        return df
    except Exception as e:
        st.error(f"⚠️ Connection Error: {e}")
        return None

df_surgery = load_live_data(GOOGLE_SHEET_CSV_URL)

# GEIMS 2025 Fixed Policy Rates (Based on your role at Indus Healthcare Group)
ROOM_DATA = {
    "Economy": {"Rent": 2500, "Consult": 700, "Nursing": 500, "RMO": 700},
    "Double": {"Rent": 4500, "Consult": 900, "Nursing": 600, "RMO": 800},
    "Single/ ICU": {"Rent": 7500, "Consult": 1200, "Nursing": 600, "RMO": 800},
    "Classic Deluxe": {"Rent": 10000, "Consult": 1500, "Nursing": 600, "RMO": 800},
    "Suite": {"Rent": 33000, "Consult": 2000, "Nursing": 2800, "RMO": 3000},
}

st.title("🏥 GEIMS Hospital Estimate Generator")

if df_surgery is not None:
    # Diagnostic: Check if 'Department' is actually a column
    if 'Department' not in df_surgery.columns:
        st.error(f"❌ Column 'Department' not found. Available columns: {list(df_surgery.columns)}")
        st.stop()

    with st.sidebar:
        st.header("Patient Setup")
        pat_name = st.text_input("Patient Name", "Anuj Gill")
        room_cat = st.selectbox("Bed Category", list(ROOM_DATA.keys()))
        stay_days = st.number_input("Days of Stay", min_value=1, value=1)
        st.divider()
        st.info("Policy: MRD Charge (450) and Diet (100/day) applied.")

    try:
        # Selection Logic
        depts = sorted(df_surgery['Department'].dropna().unique())
        selected_dept = st.selectbox("Select Department", depts)
        
        procs = df_surgery[df_surgery['Department'] == selected_dept]['Service Name'].dropna().unique()
        selected_proc = st.selectbox("Select Surgery", procs)

        # Match Price
        row_match = df_surgery[df_surgery['Service Name'] == selected_proc]
        surgery_fee = row_match[room_cat].values[0]
        
        r = ROOM_DATA[room_cat]
        
        # Billing Logic (Applying GEIMS 11AM Discharge Policy)
        breakdown = {
            f"Surgery: {selected_proc}": float(surgery_fee),
            "Room Rent": r['Rent'] * stay_days,
            "Consultation (2/day)": (r['Consult'] * 2) * stay_days,
            "Nursing & RMO": (r['Nursing'] + r['RMO']) * stay_days,
            "MRD Fee (Fixed)": 450.0,
            "Diet Charges": 100.0 * stay_days
        }
        
        st.subheader(f"Summary for {pat_name}")
        st.table(pd.DataFrame(list(breakdown.items()), columns=["Description", "Amount (₹)"]))
        st.metric("Estimated Total", f"₹ {sum(breakdown.values()):,.2f}")
        
    except Exception as e:
        st.warning("Please select a valid procedure to calculate.")
