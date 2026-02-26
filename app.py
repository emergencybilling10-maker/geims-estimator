import streamlit as st
import pandas as pd

# --- PAGE CONFIG ---
st.set_page_config(page_title="GEIMS Official Billing Tool", layout="wide", page_icon="🏥")

# --- SMART DATA LOADING WITH ENCODING FIX ---
@st.cache_data(ttl=60)
def load_geims_data():
    # List of encodings to try to fix the 'utf-8' error
    encodings = ['utf-8', 'iso-8859-1', 'cp1252']
    for encoding in encodings:
        try:
            df = pd.read_csv("database.csv", encoding=encoding)
            # Standardize duplicate column names to prevent reindexing errors
            cols = []
            count = {}
            for col in df.columns:
                col_name = str(col).strip()
                if col_name in count:
                    count[col_name] += 1
                    cols.append(f"{col_name}_{count[col_name]}")
                else:
                    count[col_name] = 0
                    cols.append(col_name)
            df.columns = cols
            return df
        except Exception:
            continue
    st.error("Error: Could not decode 'database.csv'. Please try saving it as a plain CSV again.")
    return None

df_master = load_geims_data()

# GEIMS 2025 Policy: Fixed Rates for EXTRA days beyond package
# Source: GEIMS Billing Policy 2025
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
        st.header("Patient Setup")
        pat_name = st.text_input("Patient Name", value="Anuj Gill") 
        room_cat = st.selectbox("Selected Bed Category", list(ROOM_POLICY.keys()))
        total_stay = st.number_input("Total Days of Stay", min_value=1, value=1)
        st.divider()
        st.info("Policy: Packages include Room, Diet, Nursing, and RMO for Pkg Days.")

    try:
        # Smart Column Finder (keyword-based)
        dept_col = [c for c in df_master.columns if 'dept' in c.lower()][0]
        serv_col = [c for c in df_master.columns if 'service' in c.lower() or 'procedure' in c.lower()][0]
        
        col1, col2 = st.columns(2)
        with col1:
            sel_dept = st.selectbox("Search Department", sorted(df_master[dept_col].dropna().unique()))
        with col2:
            procs = sorted(df_master[df_master[dept_col] == sel_dept][serv_col].dropna().unique())
            sel_proc = st.selectbox("Select Procedure / Investigation", procs)

        # Extraction and Pricing Logic
        row = df_master[df_master[serv_col] == sel_proc]
        price_col = [c for c in df_master.columns if room_cat.lower() in c.lower()][0]
        price_val = str(row[price_col].values[0]).replace(',', '').replace('₹', '').strip()
        base_rate = float(price_val) if price_val.replace('.','').isdigit() else 0.0
        
        # Package Days detection (defaults to 1 if missing)
        pkg_day_col = [c for c in df_master.columns if 'day' in c.lower() and ('pkg' in c.lower() or 'package' in c.lower())]
        pkg_days = int(row[pkg_day_col[0]].values[0]) if pkg_day_col else 1
        
        # Extra Day Calculation (GEIMS 11 AM - 11 AM Policy)
        extra_days = max(0, total_stay - pkg_days)
        r = ROOM_POLICY[room_cat]

        breakdown = {
            f"Package Rate ({sel_proc})": base_rate,
            "Package Inclusions": f"Includes Room, Diet, Nursing & RMO for {pkg_days} days",
            "Admission / MRD Fee": 450.0  # Fixed one-time fee
        }

        if extra_days > 0:
            breakdown[f"Extra Room & Nursing ({extra_days} days)"] = float((r['Rent'] + r['Nursing'] + r['RMO']) * extra_days)
            breakdown[f"Extra Consultation (2 visits/day)"] = float((r['Consult'] * 2) * extra_days)
            breakdown[f"Extra Diet Charges"] = float(r['Diet'] * extra_days)

        st.markdown("---")
        st.subheader(f"Formal Estimate Summary: {pat_name}")
        st.table(pd.DataFrame(list(breakdown.items()), columns=["Description", "Amount (₹)"]))
        
        total_cost = sum([v for v in breakdown.values() if isinstance(v, (float, int))])
        st.metric("Total Estimated Bill", f"₹ {total_cost:,.2f}")
        st.caption("Note: Pharmacy, Implants, and Consumables are extra as per actual consumption.")

    except Exception as e:
        st.error(f"Data Mapping Error: Please check CSV headers. Detail: {e}")
else:
    st.warning("🔄 System is ready. Refresh the app to retry loading 'database.csv'.")
