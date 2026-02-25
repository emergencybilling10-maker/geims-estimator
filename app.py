import streamlit as st
import pandas as pd
import os

st.set_page_config(page_title="GEIMS Estimate Tool", layout="wide")

# --- AUTO-DETECTION LOGIC ---
def find_file(name_to_find):
    files = os.listdir(".")
    for f in files:
        if name_to_find in f.lower(): # Finds 'surgery.csv' or 'surgery.csv.xls'
            return f
    return None

surgery_path = find_file("surgery")

@st.cache_data
def load_data(path):
    if path:
        try:
            # GEIMS surgery files usually have 1 header row to skip
            df = pd.read_csv(path, skiprows=1)
            df.columns = [c.strip() for c in df.columns]
            return df
        except Exception as e:
            st.error(f"Error reading {path}: {e}")
    return None

df_surgery = load_data(surgery_path)

# --- GEIMS TARIFF RULES ---
ROOM_RATES = {
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
        room_cat = st.selectbox("Bed Category", list(ROOM_RATES.keys()))
        stay_days = st.number_input("Days of Stay", min_value=1, value=1)

    # Department and Surgery Selection
    if 'Department' in df_surgery.columns:
        dept = st.selectbox("Select Department", df_surgery['Department'].unique())
        surgeries = df_surgery[df_surgery['Department'] == dept]['Service Name']
        proc = st.selectbox("Select Procedure", surgeries)

        # Pricing Logic
        surgery_fee = df_surgery[df_surgery['Service Name'] == proc][room_cat].values[0]
        r_vals = ROOM_RATES[room_cat]
        
        breakdown = {
            "Surgery/Procedure Fee": surgery_fee,
            "Room Rent": r_vals['Rent'] * stay_days,
            "Daily Consultations (2 visits)": (r_vals['Consult'] * 2) * stay_days,
            "Nursing & RMO": (r_vals['Nursing'] + r_vals['RMO']) * stay_days,
            "MRD Charges": 450,
            "Diet Charges": 100 * stay_days
        }
        
        st.table(pd.DataFrame(list(breakdown.items()), columns=["Description", "Amount"]))
        st.metric("Total Estimate", f"₹ {sum(breakdown.values()):,.2f}")
    else:
        st.error("The CSV format is incorrect. Please check the 'Department' column.")
else:
    st.warning("⚠️ Still looking for 'surgery.csv'. Please rename your file on GitHub to exactly 'surgery.csv'.")
