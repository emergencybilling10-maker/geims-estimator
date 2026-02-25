import streamlit as st
import pandas as pd

st.set_page_config(page_title="GEIMS Official Estimator", layout="wide", page_icon="🏥")

# --- GEIMS TARIFF DATA (INTERNAL) ---
# Hardcoded to prevent any file or connection errors
data = [
    {"Dept": "CARDIAC", "Service": "CABG (Bypass Surgery)", "Economy": 225000, "Double": 260000, "Single/ ICU": 310000, "Deluxe": 375000, "Suite": 450000},
    {"Dept": "CARDIAC", "Service": "ASD/VSD Closure", "Economy": 185000, "Double": 210000, "Single/ ICU": 245000, "Deluxe": 290000, "Suite": 350000},
    {"Dept": "CARDIAC", "Service": "Valve Replacement (Single)", "Economy": 210000, "Double": 245000, "Single/ ICU": 290000, "Deluxe": 350000, "Suite": 425000},
    {"Dept": "NEURO", "Service": "Craniotomy (Tumor/Clot)", "Economy": 145000, "Double": 170000, "Single/ ICU": 210000, "Deluxe": 260000, "Suite": 320000},
    {"Dept": "NEURO", "Service": "Spine Surgery (Discectomy)", "Economy": 95000, "Double": 115000, "Single/ ICU": 145000, "Deluxe": 185000, "Suite": 235000},
    {"Dept": "ORTHO", "Service": "Total Knee Replacement (TKR)", "Economy": 185000, "Double": 215000, "Single/ ICU": 260000, "Deluxe": 320000, "Suite": 400000},
    {"Dept": "ORTHO", "Service": "Total Hip Replacement (THR)", "Economy": 195000, "Double": 225000, "Single/ ICU": 275000, "Deluxe": 340000, "Suite": 425000},
    {"Dept": "GYNAE", "Service": "LSCS (Caesarean Section)", "Economy": 45000, "Double": 55000, "Single/ ICU": 75000, "Deluxe": 95000, "Suite": 125000},
    {"Dept": "GYNAE", "Service": "Hysterectomy (Lap/Open)", "Economy": 65000, "Double": 80000, "Single/ ICU": 105000, "Deluxe": 135000, "Suite": 180000},
    {"Dept": "GEN SURG", "Service": "Cholecystectomy (Lap)", "Economy": 48000, "Double": 58000, "Single/ ICU": 78000, "Deluxe": 98000, "Suite": 135000},
    {"Dept": "GEN SURG", "Service": "Hernia Repair (Lap/Open)", "Economy": 42000, "Double": 52000, "Single/ ICU": 72000, "Deluxe": 92000, "Suite": 125000},
]
df = pd.DataFrame(data)

# --- GEIMS BILLING RULES (MANUAL 2025) ---
RULES = {
    "Economy": {"Rent": 2500, "Consult": 700, "Nursing": 500, "RMO": 700},
    "Double": {"Rent": 4500, "Consult": 900, "Nursing": 600, "RMO": 800},
    "Single/ ICU": {"Rent": 7500, "Consult": 1200, "Nursing": 600, "RMO": 800},
    "Deluxe": {"Rent": 10000, "Consult": 1500, "Nursing": 600, "RMO": 800},
    "Suite": {"Rent": 33000, "Consult": 2000, "Nursing": 2800, "RMO": 3000},
}

st.title("🏥 GEIMS Hospital Official Estimate Tool")
st.subheader("Graphic Era Institute of Medical Sciences | 2025 Policy Compliance")

with st.sidebar:
    st.header("Patient Setup")
    pat_name = st.text_input("Patient Name", value="Anuj Gill")
    room_cat = st.selectbox("Bed Category", list(RULES.keys()))
    stay_days = st.number_input("Days of Stay", min_value=1, value=1)
    st.divider()
    st.info("Policy: 11 AM - 11 AM Cycle | Stay > 8 hrs = Full Day")

# --- UI LOGIC ---
c1, c2 = st.columns(2)
with c1:
    sel_dept = st.selectbox("Department", df['Dept'].unique())
with c2:
    procs = df[df['Dept'] == sel_dept]['Service'].unique()
    sel_proc = st.selectbox("Procedure", procs)

# --- CALCULATION ---
row = df[df['Service'] == sel_proc]
surgery_fee = row[room_cat].values[0]
r = RULES[room_cat]

# Apply Mandatory Manual Charges
breakdown = {
    f"Surgeon Fee ({sel_proc})": float(surgery_fee),
    "Room Rent": r['Rent'] * stay_days,
    "Nursing & RMO": (r['Nursing'] + r['RMO']) * stay_days,
    "Consultation (2/Day Rule)": (r['Consult'] * 2) * stay_days,
    "Admission / MRD Fee": 450.0,
    "Diet Charges": 100.0 * stay_days
}

st.markdown("---")
st.subheader(f"Formal Estimate: {pat_name}")
st.table(pd.DataFrame(list(breakdown.items()), columns=["Description", "Amount (₹)"]))

total = sum(breakdown.values())
st.metric("Estimated Grand Total", f"₹ {total:,.2f}")
st.warning("Note: Pharmacy, Consumables, and Implants extra as per actual consumption.")
