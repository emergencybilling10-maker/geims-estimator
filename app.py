import streamlit as st
import pandas as pd
from reportlab.lib.pagesizes import A4
from reportlab.pdfgen import canvas
from io import BytesIO

st.set_page_config(page_title="GEIMS Estimate Tool", layout="wide")

# --- DATA LOADING ---
@st.cache_data
def load_geims_data():
    try:
        df = pd.read_csv("surgery.csv", skiprows=1)
        df.columns = [c.strip() for c in df.columns]
        return df
    except:
        st.error("⚠️ Error: 'surgery.csv' not found in your GitHub repository.")
        return None

df_surgery = load_geims_data()

# GEIMS Room Rates (Manual 2025)
ROOMS = {
    "Economy": {"Rent": 2500, "Consult": 700, "Nursing": 500, "RMO": 700},
    "Double": {"Rent": 4500, "Consult": 900, "Nursing": 600, "RMO": 800},
    "Single/ ICU": {"Rent": 7500, "Consult": 1200, "Nursing": 600, "RMO": 800},
    "Classic Deluxe": {"Rent": 10000, "Consult": 1500, "Nursing": 600, "RMO": 800},
    "Suite": {"Rent": 33000, "Consult": 2000, "Nursing": 2800, "RMO": 3000},
}

# --- APP UI ---
st.title("🏥 GEIMS Hospital Estimate System")
st.markdown("---")

if df_surgery is not None:
    with st.sidebar:
        st.header("1. Patient Setup")
        pat_name = st.text_input("Patient Name", "Anuj Gill")
        room_cat = st.selectbox("Bed Category", list(ROOMS.keys()))
        stay_days = st.number_input("Estimated Days", min_value=1, value=2)

    # Surgery Search
    st.header("2. Select Procedure")
    dept = st.selectbox("Department", df_surgery['Department'].unique())
    surgeries = df_surgery[df_surgery['Department'] == dept]['Service Name']
    proc = st.selectbox("Procedure", surgeries)

    # Calculation Logic
    s_rate = df_surgery[df_surgery['Service Name'] == proc][room_cat].values[0]
    r_vals = ROOMS[room_cat]
    
    # Policy: MRD (450), Diet (100/day), 2 Consults/day
    breakdown = {
        f"Surgery: {proc}": s_rate,
        "Room Rent": r_vals['Rent'] * stay_days,
        "Consultation (2 visits/day)": (r_vals['Consult'] * 2) * stay_days,
        "Nursing & RMO": (r_vals['Nursing'] + r_vals['RMO']) * stay_days,
        "MRD Registration Fee": 450,
        "Diet Charges": 100 * stay_days
    }
    
    total = sum(breakdown.values())

    # Results
    c1, c2 = st.columns([2,1])
    with c1:
        st.table(pd.DataFrame(list(breakdown.items()), columns=["Description", "Amount (₹)"]))
    with c2:
        st.metric("Total Estimate", f"₹ {total:,.2f}")
        st.success("Policy Applied: 11AM-11AM Billing Cycle")
