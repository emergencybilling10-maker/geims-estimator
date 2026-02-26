import streamlit as st
import pandas as pd

# --- PAGE CONFIG ---
st.set_page_config(page_title="GEIMS Official Billing Tool", layout="wide", page_icon="🏥")

# --- ADVANCED DATA CLEANING ---
@st.cache_data(ttl=60)
def load_geims_data():
    try:
        # 1. Load CSV with no header first to find the real column names
        df_raw = pd.read_csv("database.csv", encoding='latin1', header=None)
        
        # 2. Set headers from Row 1 (where Item Name, Economy, etc. are)
        headers = df_raw.iloc[1].tolist()
        headers = [str(h).strip().replace('\n', ' ') for h in headers]
        df_raw.columns = headers
        
        # 3. Remove metadata rows and reset
        df = df_raw.iloc[2:].reset_index(drop=True)
        
        # 4. Standardize Column Names
        rename_map = {
            'Item Name': 'Service Name',
            'Single/ ICU': 'Single/ ICU',
            'Classic  Deluxe': 'Classic Deluxe' # Handles the double space in your CSV
        }
        df.columns = [rename_map.get(c, c) for c in df.columns]

        # 5. Extract Departments (rows with no Item ID but "Economy" header)
        df['Department'] = None
        current_dept = "General Procedures"
        cleaned_rows = []

        for _, row in df.iterrows():
            item_id = str(row['Item ID']).strip().lower()
            service_name = str(row['Service Name']).strip()
            economy_val = str(row['Economy']).strip()
            
            # Check if this is a Department Header row
            if (pd.isna(row['Item ID']) or item_id == 'nan' or item_id == '') and economy_val == 'Economy':
                current_dept = service_name.replace(' PROCEDURE CHARGES', '').replace(' CHARGES', '').title()
            elif not (pd.isna(row['Item ID']) or item_id == 'nan' or item_id == ''):
                # This is a procedure row
                row_dict = row.to_dict()
                row_dict['Department'] = current_dept
                cleaned_rows.append(row_dict)

        return pd.DataFrame(cleaned_rows)
    except Exception as e:
        st.error(f"Error Processing CSV: {e}")
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
        st.header("1. Patient Setup")
        pat_name = st.text_input("Patient Name", value="Anuj Gill") 
        room_cat = st.selectbox("Selected Bed Category", list(ROOM_POLICY.keys()))
        
        # Package Days Handling (As per your request for CABG packages)
        st.divider()
        st.header("2. Stay Details")
        total_stay = st.number_input("Total Days of Stay", min_value=1, value=1)
        pkg_days = st.number_input("Package Days (e.g., 7 for CABG)", min_value=0, value=0, help="Package price covers Room/Diet/Nursing/RMO for these days.")
        st.info("Note: If Package Days > 0, extra charges apply only after the package period ends.")

    try:
        col1, col2 = st.columns(2)
        with col1:
            sel_dept = st.selectbox("Search Department", sorted(df_master['Department'].dropna().unique()))
        with col2:
            procs = sorted(df_master[df_master['Department'] == sel_dept]['Service Name'].dropna().unique())
            sel_proc = st.selectbox("Select Procedure / Investigation", procs)

        # Get the pricing row
        row = df_master[df_master['Service Name'] == sel_proc].iloc[0]
        
        # Find the correct price column (handling space/formatting issues)
        price_col = [c for c in df_master.columns if room_cat.lower() in c.lower().replace('  ', ' ')][0]
        
        # Clean price (Remove commas like '21, 600' or '₹')
        raw_price = str(row[price_col]).replace(',', '').replace('₹', '').strip()
        base_rate = float(raw_price) if raw_price.replace('.', '').isdigit() else 0.0

        # Billing Math
        extra_days = max(0, total_stay - pkg_days)
        r = ROOM_POLICY[room_cat]

        breakdown = {
            f"Base Rate ({sel_proc})": base_rate,
            "Admission / MRD Fee": 450.0 
        }

        if pkg_days > 0:
            breakdown["Package Coverage"] = f"Inclusive of Room, Diet, & Nursing for {pkg_days} days"

        if extra_days > 0:
            breakdown[f"Extra Room & Nursing ({extra_days} days)"] = float((r['Rent'] + r['Nursing'] + r['RMO']) * extra_days)
            breakdown[f"Extra Consultation (2 visits/day)"] = float((r['Consult'] * 2) * extra_days)
            breakdown[f"Extra Diet Charges"] = float(r['Diet'] * extra_days)

        st.markdown("---")
        st.subheader(f"Formal Estimate Summary: {pat_name}")
        st.table(pd.DataFrame(list(breakdown.items()), columns=["Description", "Amount (₹)"]))
        
        total_cost = sum([v for v in breakdown.values() if isinstance(v, (float, int))])
        st.metric("Total Estimated Bill", f"₹ {total_cost:,.2f}")
        st.caption("Policy Note: Implants, Pharmacy, and Consumables are extra as per actual consumption.")

    except Exception as e:
        st.error(f"Selection Error: Ensure columns match in CSV. Detail: {e}")
else:
    st.warning("🔄 System is ready. Refresh the app to retry loading 'database.csv'.")
