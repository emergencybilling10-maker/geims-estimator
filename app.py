import streamlit as st
import pandas as pd

# --- PAGE CONFIG ---
st.set_page_config(page_title="GEIMS Official Billing Tool", layout="wide", page_icon="🏥")

# --- UNIVERSAL DATA LOADING ---
@st.cache_data(ttl=600)
def load_geims_data():
    # List of possible names your file might have on GitHub
    possible_names = ["Geims Hospital...xlsx", "Geims Hospital...xlsx.xls"]
    
    for name in possible_names:
        try:
            # Try loading as modern Excel (.xlsx)
            return pd.read_excel(name, engine='openpyxl')
        except:
            try:
                # Try loading as old Excel (.xls)
                return pd.read_excel(name, engine='xlrd')
            except:
                continue
    return None

df_surgery = load_geims_data()

# GEIMS 2025 Policy: Rates for EXTRA days only
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
    # Clean the column names once loaded
    df_surgery.columns = [str(c).strip().replace('\n', ' ') for c in df_surgery.columns]
    
    with st.sidebar:
        st.header("Patient Setup")
        pat_name = st.text_input("Patient Name", value="Anuj Gill") 
        room_cat = st.selectbox("Bed Category", list(ROOM_POLICY.keys()))
        total_stay = st.number_input("Total Days of Stay", min_value=1, value=1)
        st.divider()
        st.info("Policy: Package includes Room, Diet, and Nursing for Pkg Days.")

    # Dynamic Search across ALL Excel data
    try:
        col1, col2 = st.columns(2)
        with col1:
            sel_dept = st.selectbox("Search Department", sorted(df_surgery['Department'].dropna().unique()))
        with col2:
            procs = sorted(df_surgery[df_surgery['Department'] == sel_dept]['Service Name'].dropna().unique())
            sel_proc = st.selectbox("Select Procedure / Package", procs)

        # Match Price
        row = df_surgery[df_surgery['Service Name'] == sel_proc]
        pkg_rate = float(row[room_cat].values[0])
        pkg_days = int(row['Package Days'].values[0]) if 'Package Days' in df_surgery.columns else 1
        
        extra_days = max(0, total_stay - pkg_days)
        r = ROOM_POLICY[room_cat]

        # Billing Breakdown based on GEIMS Manual
        breakdown = {
            f"Package Base Rate ({sel_proc})": pkg_rate,
            f"Package Coverage": f"Inclusive of Room, Diet, and Nursing for {pkg_days} days",
            "Admission / MRD Fee": 450.0  
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
        st.error(f"Data Error: Ensure Excel columns are 'Department' and 'Service Name'. Detail: {e}")
else:
    st.warning("🔄 Waiting for Excel file... Please ensure the file is named 'Geims Hospital...xlsx' on GitHub.")
