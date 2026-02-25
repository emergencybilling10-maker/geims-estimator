import streamlit as st
import pandas as pd
import os

st.set_page_config(page_title="GEIMS Estimate Tool", layout="wide")

# --- FILE DETECTION ---
def get_file_path(keyword):
    """Finds a file in the repo that contains a specific word."""
    for f in os.listdir("."):
        if keyword.lower() in f.lower():
            return f
    return None

surgery_file = get_file_path("surgery")

@st.cache_data
def load_geims_data(path):
    if path:
        try:
            # We skip the first row because your Excel exports have a title row
            df = pd.read_csv(path, skiprows=1)
            df.columns = [c.strip().replace('\n', ' ') for c in df.columns]
            return df
        except Exception as e:
            st.error(f"Error reading {path}: {e}")
    return None

df_surgery = load_geims_data(surgery_file)

# GEIMS Room Rates (Manual 2024-2025)
ROOM_DATA = {
    "Economy": {"Rent": 2500, "Consult": 700, "Nursing": 500, "RMO": 700},
    "Double": {"Rent": 4500, "Consult": 900, "Nursing": 600, "RMO": 800},
    "Single/ ICU": {"Rent": 7500, "Consult": 1200, "Nursing": 600, "RMO": 800},
    "Classic Deluxe": {"Rent": 10000, "Consult": 1500, "Nursing": 600, "RMO": 800},
    "Suite": {"Rent": 33000, "Consult": 2000, "Nursing": 2800, "RMO": 3000},
}

st.title("🏥 GEIMS Hospital Estimate System")

if df_surgery is not None:
    with st.sidebar:
        st.header("Patient Setup")
        pat_name = st.text_input("Patient Name", "Anuj Gill")
        room_cat = st.selectbox("Bed Category", list(ROOM_DATA.keys()))
        stay_days = st.number_input("Estimated Days", min_value=1, value=1)
        st.info("Policy: Billing Cycle 11 AM - 11 AM")

    # Selection Logic
    if 'Department' in df_surgery.columns:
        dept = st.selectbox("Select Department", df_surgery['Department'].unique())
        filtered = df_surgery[df_surgery['Department'] == dept]
        proc = st.selectbox("Select Procedure", filtered['Service Name'])

        # Get Price based on Room Category
        # Note: We match the column name in your CSV
        csv_col = room_cat if room_cat != "Single/ ICU" else "Single/ ICU"
        try:
            surgery_fee = filtered[filtered['Service Name'] == proc][csv_col].values[0]
        except:
            surgery_fee = 0
            st.warning("Rate not found for this category.")

        r_vals = ROOM_DATA[room_cat]
        
        # Policy Calculations
        breakdown = {
            f"Surgery Fee ({proc})": surgery_fee,
            "Room Rent": r_vals['Rent'] * stay_days,
            "Consultation (2 visits/day)": (r_vals['Consult'] * 2) * stay_days,
            "Nursing & RMO Charges": (r_vals['Nursing'] + r_vals['RMO']) * stay_days,
            "MRD Charges (One-time)": 450,
            "Diet & Dietician Charges": 100 * stay_days
        }
        
        st.subheader(f"Detailed Estimate for {pat_name}")
        st.table(pd.DataFrame(list(breakdown.items()), columns=["Description", "Amount (₹)"]))
        
        total = sum(breakdown.values())
        st.metric("Total Estimated Cost", f"₹ {total:,.2f}")
    else:
        st.error("Format Error: Ensure the 'Department' column exists in your CSV.")
else:
    st.warning("⚠️ Files not detected. Please ensure you have uploaded 'surgery.csv' to GitHub.")
