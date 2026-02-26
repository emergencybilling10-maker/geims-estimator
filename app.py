import streamlit as st
import pandas as pd

# --- PAGE CONFIG ---
st.set_page_config(page_title="GEIMS Billing System", layout="wide", page_icon="🏥")

# --- DATA LOADING (Enhanced) ---
@st.cache_data(ttl=60)
def load_geims_data():
    try:
        df_raw = pd.read_csv("database.csv", encoding='latin1', header=None)
        headers = df_raw.iloc[1].tolist()
        headers = [str(h).strip().replace('\n', ' ') for h in headers]
        df_raw.columns = headers
        df = df_raw.iloc[2:].reset_index(drop=True)
        
        rename_map = {'Item Name': 'Service Name', 'Classic  Deluxe': 'Classic Deluxe'}
        df.columns = [rename_map.get(c, c) for c in df.columns]

        df['Department'] = None
        current_dept = "General"
        cleaned_rows = []

        for _, row in df.iterrows():
            item_id = str(row['Item ID']).strip().lower()
            if (pd.isna(row['Item ID']) or item_id in ['nan', '']) and str(row['Economy']).strip() == 'Economy':
                current_dept = str(row['Service Name']).strip().replace(' PROCEDURE CHARGES', '').title()
            elif not (pd.isna(row['Item ID']) or item_id in ['nan', '']):
                r_dict = row.to_dict()
                r_dict['Department'] = current_dept
                cleaned_rows.append(r_dict)
        return pd.DataFrame(cleaned_rows)
    except Exception as e:
        st.error(f"Database Error: {e}")
        return None

df_master = load_geims_data()

# GEIMS 2025 FIXED POLICY
ROOM_POLICY = {
    "Economy": {"Rent": 2500, "Consult": 700, "Nursing": 500, "Diet": 100, "RMO": 700},
    "Double": {"Rent": 4500, "Consult": 900, "Nursing": 600, "Diet": 100, "RMO": 800},
    "Single/ ICU": {"Rent": 7500, "Consult": 1200, "Nursing": 600, "Diet": 100, "RMO": 800},
    "Classic Deluxe": {"Rent": 10000, "Consult": 1500, "Nursing": 600, "Diet": 100, "RMO": 800},
    "Suite": {"Rent": 33000, "Consult": 2000, "Nursing": 2800, "Diet": 100, "RMO": 3000},
}

# --- SESSION STATE FOR MULTI-SURGERY ---
if 'bill_items' not in st.session_state:
    st.session_state.bill_items = []

st.title("🏥 GEIMS Official Billing Estimator")
st.subheader("Graphic Era Institute of Medical Sciences | 2026 Ready")

if df_master is not None:
    # --- SIDEBAR: PATIENT & ROOM ---
    with st.sidebar:
        st.header("1. Patient Info")
        pat_name = st.text_input("Patient Name", value="Anuj Gill") 
        room_cat = st.selectbox("Room Category", list(ROOM_POLICY.keys()))
        total_stay = st.number_input("Total Days of Stay", min_value=1, value=1)
        st.divider()
        if st.button("🗑️ Clear All Items"):
            st.session_state.bill_items = []
            st.rerun()

    # --- MAIN UI: ADDING ITEMS ---
    st.markdown("### 2. Add Surgeries, Procedures, or Investigations")
    c1, c2, c3 = st.columns([1, 1.5, 0.5])
    
    with c1:
        sel_dept = st.selectbox("Department", sorted(df_master['Department'].unique()))
    with c2:
        procs = sorted(df_master[df_master['Department'] == sel_dept]['Service Name'].unique())
        sel_proc = st.selectbox("Select Item", procs)
    with c3:
        is_pkg = st.checkbox("Is this a Package?")
        pkg_days = st.number_input("Pkg Days", min_value=0, value=7 if "CABG" in sel_proc else 0) if is_pkg else 0
        if st.button("➕ Add to Bill"):
            row = df_master[df_master['Service Name'] == sel_proc].iloc[0]
            price_col = [c for c in df_master.columns if room_cat.lower() in c.lower().replace('  ', ' ')][0]
            price = float(str(row[price_col]).replace(',', '').replace('₹', '').strip() or 0)
            st.session_state.bill_items.append({"name": sel_proc, "price": price, "is_pkg": is_pkg, "days": pkg_days})

    # --- BILL CALCULATION ---
    if st.session_state.bill_items:
        st.markdown("---")
        st.subheader(f"Estimate for: {pat_name}")
        
        final_table = []
        total_pkg_days = max([item['days'] for item in st.session_state.bill_items])
        
        # 1. Add selected items
        for item in st.session_state.bill_items:
            final_table.append({"Description": item['name'], "Amount": item['price']})
        
        # 2. Add Admission Fee (Fixed)
        final_table.append({"Description": "Admission / MRD Fee", "Amount": 450.0})
        
        # 3. Extra Day Policy Math
        extra_days = max(0, total_stay - total_pkg_days)
        r = ROOM_POLICY[room_cat]
        
        if extra_days > 0:
            final_table.append({"Description": f"Extra Room & Nursing ({extra_days} days)", "Amount": (r['Rent'] + r['Nursing'] + r['RMO']) * extra_days})
            final_table.append({"Description": f"Extra Consultation (2 visits/day)", "Amount": (r['Consult'] * 2) * extra_days})
            final_table.append({"Description": "Extra Diet Charges", "Amount": r['Diet'] * extra_days})

        # Display Table
        bill_df = pd.DataFrame(final_table)
        st.table(bill_df)
        
        total_val = bill_df['Amount'].sum()
        st.metric("Grand Total Estimated", f"₹ {total_val:,.2f}")
        
        st.caption("Policy: Package includes standard care for defined days. Pharmacy/Implants extra.")
