import streamlit as st
import pandas as pd

# --- CONFIG ---
st.set_page_config(page_title="GEIMS Estimate Tool", layout="wide", page_icon="🏥")

# --- 1. THE LINK (Make sure this name matches the one in the function below) ---
GOOGLE_SHEET_CSV_URL = "https://docs.google.com/spreadsheets/d/e/2PACX-1vQG6vTU99xSFQEnORPp-5Mhp4hZ-fMIT_yb-daMsmff8t-K-1ggynkxHZi1UsbYE7o9bfo08ybKbd0X/pub?output=csv"

@st.cache_data(ttl=600)
def load_live_data(url):
    try:
        df = pd.read_csv(url, skiprows=1)
        df.columns = [str(c).replace('\n', ' ').strip() for c in df.columns]
        return df
    except Exception as e:
        st.error(f"Error connecting to Google Sheets: {e}")
        return None

# --- 2. LOADING THE DATA ---
df_surgery = load_live_data(GOOGLE_SHEET_CSV_URL)

# GEIMS Room Rates (Hardcoded from your General Information Sheet)
ROOM_DATA = {
    "Economy": {"Rent": 2500, "Consult": 700, "Nursing": 500, "RMO": 700},
    "Double": {"Rent": 4500, "Consult": 900, "Nursing": 600, "RMO": 800},
    "Single/ ICU": {"Rent": 7500, "Consult": 1200, "Nursing": 600, "RMO": 800},
    "Classic Deluxe": {"Rent": 10000, "Consult": 1500, "Nursing": 600, "RMO": 800},
    "Suite": {"Rent": 33000, "Consult": 2000, "Nursing": 2800, "RMO": 3000},
}

st.title("🏥 GEIMS Hospital Estimate Generator")

if df_surgery is not None:
    with st.sidebar:
        st.header("Patient Setup")
        pat_name = st.text_input("Patient Name", "Anuj Gill")
        room_cat = st.selectbox("Select Bed Category", list(ROOM_DATA.keys()))
        stay_days = st.number_input("Estimated Days of Stay", min_value=1, value=1)
        st.info("**Billing Rule:** 11 AM - 11 AM Cycle.")

    # Selection Logic
    if 'Department' in df_surgery.columns:
        dept_list = sorted(df_surgery['Department'].unique())
        selected_dept = st.selectbox("Search Department", dept_list)
        
        filtered_df = df_surgery[df_surgery['Department'] == selected_dept]
        selected_proc = st.selectbox("Select Surgery/Procedure", filtered_df['Service Name'])

        # Price Logic
        surgery_fee = filtered_df[filtered_df['Service Name'] == selected_proc][room_cat].values[0]
        r = ROOM_DATA[room_cat]
        
        breakdown = {
            f"Surgeon Fee ({selected_proc})": float(surgery_fee),
            "Room Rent": r['Rent'] * stay_days,
            "Consultation (Min. 2 visits/day)": (r['Consult'] * 2) * stay_days,
            "Nursing & RMO Charges": (r['Nursing'] + r['RMO']) * stay_days,
            "MRD Charges (Fixed)": 450.0,
            "Diet & Dietician": 100.0 * stay_days
        }
        
        st.subheader(f"Detailed Estimate for: {pat_name}")
        st.table(pd.DataFrame(list(breakdown.items()), columns=["Description", "Amount (₹)"]))
        
        st.metric("Estimated Grand Total", f"₹ {sum(breakdown.values()):,.2f}")
    else:
        st.error("Column 'Department' not found. Check your Google Sheet headers.")
