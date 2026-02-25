import streamlit as st
import pandas as pd

st.set_page_config(page_title="GEIMS Billing Tool", layout="wide", page_icon="🏥")

# --- GEIMS TARIFF DATA (DEC 2025 UPDATED) ---
# Inclusive Packages as per Tariff
data = [
    {"Dept": "CARDIAC SURGERY", "Service": "CABG (Package)", "Pkg_Days": 7, "Economy": 225000, "Double": 260000, "Single/ ICU": 310000, "Deluxe": 375000, "Suite": 450000},
    {"Dept": "CARDIAC SURGERY", "Service": "ASD/VSD Closure (Package)", "Pkg_Days": 5, "Economy": 185000, "Double": 210000, "Single/ ICU": 245000, "Deluxe": 290000, "Suite": 350000},
    {"Dept": "NEURO SURGERY", "Service": "Craniotomy (Package)", "Pkg_Days": 7, "Economy": 145000, "Double": 170000, "Single/ ICU": 210000, "Deluxe": 260000, "Suite": 320000},
    {"Dept": "ORTHOPAEDICS", "Service": "Total Knee Replacement (TKR)", "Pkg_Days": 5, "Economy": 185000, "Double": 215000, "Single/ ICU": 260000, "Deluxe": 320000, "Suite": 400000},
    {"Dept": "GYNAECOLOGY", "Service": "LSCS (Package)", "Pkg_Days": 3, "Economy": 45000, "Double": 55000, "Single/ ICU": 75000, "Deluxe": 95000, "Suite": 125000},
    {"Dept": "GENERAL SURGERY", "Service": "Lap Cholecystectomy", "Pkg_Days": 2, "Economy": 48000, "Double": 58000, "Single/ ICU": 78000, "Deluxe": 98000, "Suite": 135000},
    {"Dept": "UROLOGY", "Service": "TURP (Package)", "Pkg_Days": 3, "Economy": 55000, "Double": 68000, "Single/ ICU": 88000, "Deluxe": 115000, "Suite": 160000},
]
df = pd.DataFrame(data)

# Daily Rates for EXTRA days only (as per 2025 Policy)
EXTRA_RATES = {
    "Economy": {"Rent": 2500, "Consult": 700, "Nursing": 500, "Diet": 100, "RMO": 700},
    "Double": {"Rent": 4500, "Consult": 900, "Nursing": 600, "Diet": 100, "RMO": 800},
    "Single/ ICU": {"Rent": 7500, "Consult": 1200, "Nursing": 600, "Diet": 100, "RMO": 800},
    "Deluxe": {"Rent": 10000, "Consult": 1500, "Nursing": 600, "Diet": 100, "RMO": 800},
    "Suite": {"Rent": 33000, "Consult": 2000, "Nursing": 2800, "Diet": 100, "RMO": 3000},
}

st.title("🏥 GEIMS Hospital Official Billing Estimator")
st.subheader("Graphic Era Institute of Medical Sciences | 2026 Ready")

with st.sidebar:
    st.header("Patient Setup")
    pat_name = st.text_input("Patient Name", value="Anuj Gill")
    room_cat = st.selectbox("Selected Bed Category", list(EXTRA_RATES.keys()))
    total_stay = st.number_input("Total Days of Stay", min_value=1, value=1)
    st.divider()
    st.info("System automatically calculates Inclusive Package days vs. Extra days.")

# Selection
col1, col2 = st.columns(2)
with col1:
    sel_dept = st.selectbox("Department", df['Dept'].unique())
with col2:
    procs = df[df['Dept'] == sel_dept]['Service'].unique()
    sel_proc = st.selectbox("Procedure/Package", procs)

# Calculation Logic
row = df[df['Service'] == sel_proc]
pkg_rate = row[room_cat].values[0]
pkg_days = int(row['Pkg_Days'].values[0])

# Determine Extra Days
extra_days = max(0, total_stay - pkg_days)
r = EXTRA_RATES[room_cat]

# Breakdown
breakdown = {
    f"Package Rate ({sel_proc})": float(pkg_rate),
    f"Inclusions": f"Covers Room, Nursing, Diet, RMO & Surgeon for {pkg_days} days",
}

if extra_days > 0:
    breakdown[f"Extra Room Rent ({extra_days} days)"] = r['Rent'] * extra_days
    breakdown[f"Extra Nursing & RMO"] = (r['Nursing'] + r['RMO']) * extra_days
    breakdown[f"Extra Consultation (2/day)"] = (r['Consult'] * 2) * extra_days
    breakdown[f"Extra Diet"] = r['Diet'] * extra_days

breakdown["Admission / MRD Fee (One-time)"] = 450.0

st.markdown("---")
st.subheader(f"Final Estimate: {pat_name}")
st.table(pd.DataFrame(list(breakdown.items()), columns=["Description", "Charges / Details"]))

total = sum([v for v in breakdown.values() if isinstance(v, float)])
st.metric("Estimated Grand Total", f"₹ {total:,.2f}")
st.caption("Policy Note: Implants, Pharmacy, and Blood Bank charges are extra as per actuals.")
