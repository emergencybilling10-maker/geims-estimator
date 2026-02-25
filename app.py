import streamlit as st
import pandas as pd

# --- PAGE CONFIG ---
st.set_page_config(page_title="GEIMS Estimate Tool", layout="wide", page_icon="🏥")

# --- INTERNAL DATABASE (The "One Shot" Solution) ---
# Extracted from: Geims Hospital DDN Surgeries Procedures Tariff UPDATED DEC 2025
data = [
    {"Department": "CARDIAC SURGERY", "Service Name": "ASD/VSD CLOSURE", "Economy": 185000, "Double": 210000, "Single/ ICU": 245000, "Classic Deluxe": 290000, "Suite": 350000},
    {"Department": "CARDIAC SURGERY", "Service Name": "CABG (BYPASS SURGERY)", "Economy": 225000, "Double": 260000, "Single/ ICU": 310000, "Classic Deluxe": 375000, "Suite": 450000},
    {"Department": "CARDIAC SURGERY", "Service Name": "VALVE REPLACEMENT (SINGLE)", "Economy": 210000, "Double": 245000, "Single/ ICU": 290000, "Classic Deluxe": 350000, "Suite": 425000},
    {"Department": "NEURO SURGERY", "Service Name": "CRANIOTOMY (TUMOR/CLOT)", "Economy": 145000, "Double": 170000, "Single/ ICU": 210000, "Classic Deluxe": 260000, "Suite": 320000},
    {"Department": "NEURO SURGERY", "Service Name": "SPINE SURGERY (DISCECTOMY)", "Economy": 95000, "Double": 115000, "Single/ ICU": 145000, "Classic Deluxe": 185000, "Suite": 235000},
    {"Department": "ORTHOPAEDICS", "Service Name": "TOTAL KNEE REPLACEMENT (TKR)", "Economy": 185000, "Double": 215000, "Single/ ICU": 260000, "Classic Deluxe": 320000, "Suite": 400000},
    {"Department": "ORTHOPAEDICS", "Service Name": "TOTAL HIP REPLACEMENT (THR)", "Economy": 195000, "Double": 225000, "Single/ ICU": 275000, "Classic Deluxe": 340000, "Suite": 425000},
    {"Department": "GYNAECOLOGY", "Service Name": "LSCS (CAESAREAN SECTION)", "Economy": 45000, "Double": 55000, "Single/ ICU": 75000, "Classic Deluxe": 95000, "Suite": 125000},
    {"Department": "GYNAECOLOGY", "Service Name": "HYSTERECTOMY (LAP/OPEN)", "Economy": 65000, "Double": 80000, "Single/ ICU": 105000, "Classic Deluxe": 135000, "Suite": 180000},
    {"Department": "GENERAL SURGERY", "Service Name": "CHOLECYSTECTOMY (LAP)", "Economy": 48000, "Double": 58000, "Single/ ICU": 78000, "Classic Deluxe": 98000, "Suite": 135000},
    {"Department": "GENERAL SURGERY", "Service Name": "HERNIA REPAIR (LAP/OPEN)", "Economy": 42000, "Double": 52000, "Single/ ICU": 72000, "Classic Deluxe": 92000, "Suite": 125000},
    {"Department": "UROLOGY", "Service Name": "TURP (PROSTATE)", "Economy": 55000, "Double": 68000, "Single/ ICU": 88000, "Classic Deluxe": 115000, "Suite": 160000},
    {"Department": "UROLOGY", "Service Name": "PCNL (KIDNEY STONE)", "Economy": 62000, "Double": 75000, "Single/ ICU": 98000, "Classic Deluxe": 125000, "Suite": 175000},
]

df_surgery = pd.DataFrame(data)

# GEIMS Fixed Policy Rates (MRD, Diet, & Room Rules)
ROOM_DATA = {
    "Economy": {"Rent": 2500, "Consult": 700, "Nursing": 500, "RMO": 700},
    "Double": {"Rent": 4500, "Consult": 900, "Nursing": 600, "RMO": 800},
    "Single/ ICU": {"Rent": 7500, "Consult": 1200, "Nursing": 600, "RMO": 800},
    "Classic Deluxe": {"Rent": 10000, "Consult": 1500, "Nursing": 600, "RMO": 800},
    "Suite": {"Rent": 33000, "Consult": 2000, "Nursing": 2800, "RMO": 3000},
}

# --- UI INTERFACE ---
st.title("🏥 GEIMS Hospital Estimate Generator")
st.subheader("Graphic Era Institute of Medical Sciences | Billing Portal")

with st.sidebar:
    st.header("Patient Setup")
    pat_name = st.text_input("Patient Name", value="Anuj Gill")
    room_cat = st.selectbox("Bed Category", list(ROOM_DATA.keys()))
    stay_days = st.number_input("Estimated Days of Stay", min_value=1, value=1)
    st.divider()
    st.markdown("**User:** Coordinator / M.O.D")
    st.info("Policy: MRD Fee (450) and Diet (100) are automatically included.")

# Search Bars
c1, c2 = st.columns(2)
with c1:
    depts = sorted(df_surgery['Department'].unique())
    sel_dept = st.selectbox("Search Department", depts)
with c2:
    procs = df_surgery[df_surgery['Department'] == sel_dept]['Service Name'].unique()
    sel_proc = st.selectbox("Select Procedure", procs)

# Calculation
row = df_surgery[df_surgery['Service Name'] == sel_proc]
surgery_fee = row[room_cat].values[0]
r = ROOM_DATA[room_cat]

# Apply GEIMS Rules: MRD 450, Diet 100, 2 Consultations per day
breakdown = {
    f"Surgeon Fee ({sel_proc})": float(surgery_fee),
    "Room Rent": r['Rent'] * stay_days,
    "Daily Consultations (2 visits/day)": (r['Consult'] * 2) * stay_days,
    "Nursing & RMO Charges": (r['Nursing'] + r['RMO']) * stay_days,
    "MRD Registration Fee": 450.0,
    "Diet & Dietician Charges": 100.0 * stay_days
}

st.markdown("---")
st.subheader(f"Detailed Estimate Summary: {pat_name}")
st.table(pd.DataFrame(list(breakdown.items()), columns=["Description", "Amount (INR)"]))

total = sum(breakdown.values())
st.metric("Total Estimated Bill", f"₹ {total:,.2f}")
st.caption("Disclaimer: Pharmacy, Implants, and Consumables extra as per actuals.")
