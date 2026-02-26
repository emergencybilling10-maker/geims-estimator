import streamlit as st
import pandas as pd

# --- PAGE CONFIG ---
st.set_page_config(page_title="GEIMS Official Billing Tool", layout="wide", page_icon="🏥")

# --- SMART DATA LOADING ---
@st.cache_data(ttl=60)
def load_geims_data():
    encodings = ['utf-8', 'iso-8859-1', 'cp1252', 'latin1']
    for encoding in encodings:
        try:
            df = pd.read_csv("database.csv", encoding=encoding)
            # Remove empty columns and rows
            df = df.dropna(how='all', axis=1).dropna(how='all', axis=0)
            df.columns = [str(c).strip() for c in df.columns]
            return df
        except Exception:
            continue
    return None

df_master = load_geims_data()

# GEIMS 2025 Policy: Fixed Rates for EXTRA days beyond package
ROOM_POLICY = {
    "Economy": {"Rent": 2500, "Consult": 700, "Nursing": 500, "Diet": 100, "RMO": 700},
    "Double": {"Rent": 4500, "Consult": 900, "Nursing": 600, "Diet": 100, "RMO": 800},
    "Single/ ICU": {"Rent": 7500, "Consult": 1200, "Nursing": 600, "Diet": 100, "RMO": 800},
    "Classic Deluxe": {"Rent": 10000, "Consult": 1500, "Nursing": 600, "Diet": 100, "RMO": 800},
    "Suite": {"Rent": 33000, "Consult": 2000, "Nursing": 2800, "Diet": 100, "RMO": 3000},
}

st.title("🏥 GEIMS Hospital Official Billing Estimator")
st.subheader("Graphic Era Institute of Medical Sciences | 2026 Ready")

if df_master is not None:
    with st.sidebar:
        st.header("1. System Setup")
        # SAFETY FALLBACK: Let user pick columns if auto-detection fails
        all_cols = list(df_master.columns)
        
        # Try to guess, otherwise user picks
        try:
            def_dept = [c for c in all_cols if 'dept' in c.lower()][0]
        except:
            def_dept = all_cols[0]
            
        try:
            def_serv = [c for c in all_cols if 'serv' in c.lower() or 'proc' in c.lower()][0]
        except:
            def_serv = all_cols[1] if len(all_cols) > 1 else all_cols[0]

        dept_col = st.selectbox("Select Department Column", all_cols, index=all_cols.index(def_dept))
        serv_col = st.selectbox("Select Service/Surgery Column", all_cols, index=all_cols.index(def_serv))
        
        st.divider()
        st.header("2. Patient Details")
        pat_name = st.text_input("Patient Name", value="Anuj Gill") 
        room_cat = st.selectbox("Bed Category", list(ROOM_POLICY.keys()))
        total_stay = st.number_input("Total Days of Stay", min_value=1, value=1)

    try:
        col1, col2 = st.columns(2)
        with col1:
            sel_dept = st.selectbox("Department", sorted(df_master[dept_col].dropna().unique()))
        with col2:
            procs = sorted(df_master[df_master[dept_col] == sel_dept][serv_col].dropna().unique())
            sel_proc = st.selectbox("Procedure / Investigation", procs)

        # Extraction
        row = df_master[df_master[serv_col] == sel_proc].iloc[0]
        
        # Price Search
        try:
            price_col = [c for c in df_master.columns if room_cat.lower() in c.lower()][0]
            price_val = str(row[price_col]).replace(',', '').replace('₹', '').strip()
            base_rate = float(price_val)
        except:
            base_rate = 0.0
            st.warning(f"Could not find price for {room_cat} in the CSV.")

        # Package Days logic
        pkg_day_cols = [c for c in df_master.columns if 'day' in c.lower() and ('pkg' in c.lower() or 'package' in c.lower())]
        pkg_days = int(row[pkg_day_cols[0]]) if pkg_day_cols and str(row[pkg_day_cols[0]]).isdigit() else 1
        
        extra_days = max(0, total_stay - pkg_days)
        r = ROOM_POLICY[room_cat]

        breakdown = {
            f"Base Rate ({sel_proc})": base_rate,
            "Package Inclusions": f"Covers Room, Nursing, RMO & Diet for {pkg_days} days",
            "Admission / MRD Fee": 450.0 # Fixed GEIMS Policy
        }

        if extra_days > 0:
            breakdown[f"Extra Room & Nursing ({extra_days} days)"] = float((r['Rent'] + r['Nursing'] + r['RMO']) * extra_days)
            breakdown[f"Extra Consultation (2 visits/day)"] = float((r['Consult'] * 2) * extra_days)
            breakdown[f"Extra Diet Charges"] = float(r['Diet'] * extra_days)

        st.markdown("---")
        st.subheader(f"Formal Estimate: {pat_name}")
        st.table(pd.DataFrame(list(breakdown.items()), columns=["Description", "Amount (₹)"]))
        
        total_cost = sum([v for v in breakdown.values() if isinstance(v, (float, int))])
        st.metric("Total Estimated Bill", f"₹ {total_cost:,.2f}")

    except Exception as e:
        st.error(f"Selection Error: Please verify columns in sidebar. Detail: {e}")
else:
    st.warning("🔄 Ensure 'database.csv' is uploaded to GitHub.")
