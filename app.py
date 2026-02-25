import streamlit as st
import pandas as pd

st.set_page_config(page_title="GEIMS Official Billing Tool", layout="wide", page_icon="🏥")

# --- COMPREHENSIVE GEIMS TARIFF DATABASE (DEC 2025) ---
# Each entry includes the Package Days as defined in your policy
data = [
    # CARDIAC SURGERY (CTVS)
    {"Dept": "CARDIAC SURGERY", "Service": "CABG (Bypass Surgery)", "Pkg_Days": 7, "Economy": 225000, "Double": 260000, "Single/ ICU": 310000, "Classic Deluxe": 375000, "Suite": 450000},
    {"Dept": "CARDIAC SURGERY", "Service": "ASD/VSD Closure", "Pkg_Days": 5, "Economy": 185000, "Double": 210000, "Single/ ICU": 245000, "Classic Deluxe": 290000, "Suite": 350000},
    {"Dept": "CARDIAC SURGERY", "Service": "Valve Replacement (Single)", "Pkg_Days": 7, "Economy": 210000, "Double": 245000, "Single/ ICU": 290000, "Classic Deluxe": 350000, "Suite": 425000},
    
    # NEURO SURGERY
    {"Dept": "NEURO SURGERY", "Service": "Craniotomy (Tumor/Clot)", "Pkg_Days": 7, "Economy": 145000, "Double": 170000, "Single/ ICU": 210000, "Classic Deluxe": 260000, "Suite": 320000},
    {"Dept": "NEURO SURGERY", "Service": "Spine Surgery (Discectomy)", "Pkg_Days": 4, "Economy": 95000, "Double": 115000, "Single/ ICU": 145000, "Classic Deluxe": 185000, "Suite": 235000},
    {"Dept": "NEURO SURGERY", "Service": "VP Shunt", "Pkg_Days": 4, "Economy": 75000, "Double": 90000, "Single/ ICU": 115000, "Classic Deluxe": 145000, "Suite": 190000},
    
    # ORTHOPAEDICS
    {"Dept": "ORTHOPAEDICS", "Service": "Total Knee Replacement (TKR)", "Pkg_Days": 5, "Economy": 185000, "Double": 215000, "Single/ ICU": 260000, "Classic Deluxe": 320000, "Suite": 400000},
    {"Dept": "ORTHOPAEDICS", "Service": "Total Hip Replacement (THR)", "Pkg_Days": 5, "Economy": 195000, "Double": 225000, "Single/ ICU": 275000, "Classic Deluxe": 340000, "Suite": 425000},
    {"Dept": "ORTHOPAEDICS", "Service": "Arthroscopy (Diagnostic)", "Pkg_Days": 2, "Economy": 35000, "Double": 45000, "Single/ ICU": 60000, "Classic Deluxe": 75000, "Suite": 100000},
    
    # GYNAECOLOGY
    {"Dept": "GYNAECOLOGY", "Service": "LSCS (C-Section)", "Pkg_Days": 3, "Economy": 45000, "Double": 55000, "Single/ ICU": 75000, "Classic Deluxe": 95000, "Suite": 125000},
    {"Dept": "GYNAECOLOGY", "Service": "Hysterectomy (Lap/Open)", "Pkg_Days": 3, "Economy": 65000, "Double": 80000, "Single/ ICU": 105000, "Classic Deluxe": 135000, "Suite": 180000},
    {"Dept": "GYNAECOLOGY", "Service": "Normal Delivery", "Pkg_Days": 2, "Economy": 25000, "Double": 32000, "Single/ ICU": 45000, "Classic Deluxe": 55000, "Suite": 75000},

    # UROLOGY
    {"Dept": "UROLOGY", "Service": "TURP (Prostate)", "Pkg_Days": 3, "Economy": 55000, "Double": 68000, "Single/ ICU": 88000, "Classic Deluxe": 115000, "Suite": 160000},
    {"Dept": "UROLOGY", "Service": "PCNL (Kidney Stone)", "Pkg_Days": 3, "Economy": 62000, "Double": 75000, "Single/ ICU": 98000, "Classic Deluxe": 125000, "Suite": 175000},
    {"Dept": "UROLOGY", "Service": "URSL", "Pkg_Days": 2, "Economy": 45000, "Double": 55000, "Single/ ICU": 75000, "Classic Deluxe": 95000, "Suite": 130000},

    # GENERAL SURGERY
    {"Dept": "GENERAL SURGERY", "Service": "Lap Cholecystectomy", "Pkg_Days": 2, "Economy": 48000, "Double": 58000, "Single/ ICU": 78000, "Classic Deluxe": 98000, "Suite": 135000},
    {"Dept": "GENERAL SURGERY", "Service": "Hernia Repair (Lap/Open)", "Pkg_Days": 2, "Economy": 42000, "Double": 52000, "Single/ ICU": 72000, "Classic Deluxe": 92000, "Suite": 125000},
    {"Dept": "GENERAL SURGERY", "Service": "Appendectomy", "Pkg_Days": 2, "Economy": 40000, "Double": 50000, "Single/ ICU": 70000, "Classic Deluxe": 90000, "Suite": 120000},

    # ENT / OPHTHALMOLOGY
    {"Dept": "ENT", "Service": "Tympanoplasty", "Pkg_Days": 2, "Economy": 35000, "Double": 45000, "Single/ ICU": 60000, "Classic Deluxe": 80000, "Suite": 110000},
    {"Dept": "OPHTHALMOLOGY", "Service": "Cataract (Phaco + IOL)", "Pkg_Days": 1, "Economy": 25000, "Double": 32000, "Single/ ICU": 45000, "Classic Deluxe": 60000, "Suite": 85000},
]

df = pd.DataFrame(data)

# --- DAILY POLICY RATES (FOR EXTRA DAYS ONLY) ---
ROOM_POLICY = {
    "Economy": {"Rent": 2500, "Consult": 700, "Nursing": 500, "Diet": 100, "RMO": 700},
    "Double": {"Rent": 4500, "Consult": 900, "Nursing": 600, "Diet": 100, "RMO": 800},
    "Single/ ICU": {"Rent": 7500, "Consult": 1200, "Nursing": 600, "Diet": 100, "RMO": 800},
    "Classic Deluxe": {"Rent": 10000, "Consult": 1500, "Nursing": 600, "Diet": 100, "RMO": 800},
    "Suite": {"Rent": 33000, "Consult": 2000, "Nursing": 2800, "Diet": 100, "RMO": 3000},
}

st.title("🏥 GEIMS Hospital Official Billing Estimator")
st.subheader("Graphic Era Institute of Medical Sciences | 2026 Policy Compliance")

# --- UI INTERFACE ---
with st.sidebar:
    st.header("Patient Setup")
    pat_name = st.text_input("Patient Name", value="Anuj Gill")
    room_cat = st.selectbox("Selected Bed Category", list(ROOM_POLICY.keys()))
    total_stay = st.number_input("Total Days of Stay", min_value=1, value=1)
    st.divider()
    st.info("System automatically identifies Inclusive Packages vs. Extra Days.")

# Selection logic
col1, col2 = st.columns(2)
with col1:
    sel_dept = st.selectbox("Search Department", sorted(df['Dept'].unique()))
with col2:
    procs = sorted(df[df['Dept'] == sel_dept]['Service'].unique())
    sel_proc = st.selectbox("Select Surgery / Procedure", procs)

# --- BILLING CALCULATOR ---
row = df[df['Service'] == sel_proc]
pkg_rate = float(row[room_cat].values[0])
pkg_days = int(row['Pkg_Days'].values[0])

# Logic for Extra Days
extra_days = max(0, total_stay - pkg_days)
r = ROOM_POLICY[room_cat]

# Build the breakdown table based on GEIMS Manual
breakdown = {
    f"Package Base Rate ({sel_proc})": pkg_rate,
    f"Package Coverage": f"Includes Room, Diet, Nursing, RMO, and Surgeon Fee for {pkg_days} days",
    "Admission / MRD Fee": 450.0  # Fixed
}

if extra_days > 0:
    breakdown[f"Extra Room Rent ({extra_days} days)"] = float(r['Rent'] * extra_days)
    breakdown[f"Extra Nursing & RMO"] = float((r['Nursing'] + r['RMO']) * extra_days)
    breakdown[f"Extra Consultation (2 visits/day)"] = float((r['Consult'] * 2) * extra_days)
    breakdown[f"Extra Diet Charges"] = float(r['Diet'] * extra_days)

st.markdown("---")
st.subheader(f"Detailed Estimate for: {pat_name}")
st.table(pd.DataFrame(list(breakdown.items()), columns=["Description", "Details / Charges (₹)"]))

# Calculate Numeric Total
total_cost = sum([v for v in breakdown.values() if isinstance(v, (float, int))])
st.metric("Total Estimated Bill (Package + Extras)", f"₹ {total_cost:,.2f}")
st.caption("Policy Note: Implants, Pharmacy, Blood Bank, and Consumables are billed extra as per actual consumption.")
