import streamlit as st
import pandas as pd
import os

# --- PAGE CONFIG ---
st.set_page_config(page_title="GEIMS Official Billing Tool", layout="wide", page_icon="🏥")

# --- SMART DATA LOADING (Finds any GEIMS file) ---
@st.cache_data(ttl=60)
def load_geims_data():
    # This looks at every file in your GitHub folder
    files = [f for f in os.listdir('.') if f.lower().startswith('geims')]
    
    if not files:
        return None, "No file starting with 'Geims' found in GitHub."

    target_file = files[0] # Takes the first GEIMS file it finds
    
    try:
        # Try modern Excel engine
        df = pd.read_excel(target_file, engine='openpyxl')
        return df, None
    except:
        try:
            # Try legacy Excel engine
            df = pd.read_excel(target_file, engine='xlrd')
            return df, None
        except Exception as e:
            return None, f"Found {target_file} but couldn't read it. Error: {e}"

df_surgery, error_msg = load_geims_data()

# GEIMS 2025 Policy: Rates for EXTRA days (From your Billing Policy)
ROOM_POLICY = {
    "Economy": {"Rent": 2500, "Consult": 700, "Nursing": 500, "Diet": 100, "RMO": 700},
    "Double": {"Rent": 4500, "Consult": 900, "Nursing": 600, "Diet": 100, "RMO": 800},
    "Single/ ICU": {"Rent": 7500, "Consult": 1200, "Nursing": 600, "Diet": 100, "RMO": 800},
    "Classic Deluxe": {"Rent": 10000, "Consult": 1500, "Nursing": 600, "Diet": 100, "RMO": 800},
    "Suite": {"Rent": 33000, "Consult": 2000, "Nursing": 2800, "Diet": 100, "RMO": 3000},
}

st.title("🏥 GEIMS Hospital Official Billing Estimator")
st.subheader("Graphic Era Institute of Medical Sciences | 2026 Ready")

if df_surgery is not None:
    # Clean the column names for accuracy
    df_surgery.columns = [str(c).strip().replace('\n', ' ') for c in df_surgery.columns]
    
    with st.sidebar:
        st.header("Patient Setup")
        pat_name = st.text_input("Patient Name", value="Anuj Gill") 
        room_cat = st.selectbox("Bed Category", list(ROOM_POLICY.keys()))
        total_stay = st.number_input("Total Days of Stay", min_value=1, value=1)
        st.divider()
        st.info("Policy: Package inclusive of Room, Diet, Nursing, and RMO for Pkg Days.")

    try:
        col1, col2 = st.columns(2)
        with col1:
            # Auto-detects 'Department' or 'DEPT'
            dept_col = [c for c in df_surgery.columns if 'dept' in c.lower()][0]
            sel_dept = st.selectbox("Search Department", sorted(df_surgery[dept_col].dropna().unique()))
        with col2:
            # Auto-detects 'Service' or 'Procedure'
            serv_col = [c for c in df_surgery.columns if 'service' in c.lower() or 'procedure' in c.lower()][0]
            procs = sorted(df_surgery[df_surgery[dept_col] == sel_dept][serv_col].dropna().unique())
            sel_proc = st.selectbox("Select Procedure / Package", procs)

        # Logic: Packages include standard charges
        row = df_surgery[df_surgery[serv_col] == sel_proc]
        pkg_rate = float(row[room_cat].values[0])
        
        # Finds Package Days column automatically
        pkg_day_col = [c for c in df_surgery.columns if 'day' in c.lower() and 'pkg' in c.lower() or 'package' in c.lower()]
        pkg_days = int(row[pkg_day_col[0]].values[0]) if pkg_day_col else 1
        
        extra_days = max(0, total_stay - pkg_days)
        r = ROOM_POLICY[room_cat]

        breakdown = {
            f"Package Rate ({sel_proc})": pkg_rate,
            f"Package Coverage": f"Inclusive of Room, Diet, and Nursing for {pkg_days} days",
            "Admission / MRD Fee": 450.0  # Per GEIMS Policy
        }

        if extra_days > 0:
            breakdown[f"Extra Room & Nursing ({extra_days} days)"] = float((r['Rent'] + r['Nursing'] + r['RMO']) * extra_days)
            breakdown[f"Extra Consultation (2 visits/day)"] = float((r['Consult'] * 2) * extra_days)
            breakdown[f"Extra Diet Charges"] = float(r['Diet'] * extra_days)

        st.markdown("---")
        st.subheader(f"Formal Estimate for: {pat_name}")
        st.table(pd.DataFrame(list(breakdown.items()), columns=["Description", "Amount (₹)"]))
        
        total_cost = sum([v for v in breakdown.values() if isinstance(v, (float, int))])
        st.metric("Total Estimated Bill", f"₹ {total_cost:,.2f}")
    except Exception as e:
        st.error(f"Mapping Error: Please check Excel columns. Detail: {e}")
else:
    st.warning(f"🔄 {error_msg}")
