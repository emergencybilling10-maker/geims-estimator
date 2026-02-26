import streamlit as st
import pandas as pd
from datetime import datetime

# --- PAGE CONFIG ---
st.set_page_config(page_title="GEIMS Billing System", layout="wide", page_icon="🏥")

# --- DATA LOADING (Comprehensive Scraper) ---
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

if 'bill_items' not in st.session_state:
    st.session_state.bill_items = []

# --- HEADER SECTION (Matches your CSV Reference) ---
st.title("GRAPHIC ERA INSTITUTE OF MEDICAL SCIENCES")
st.caption("DHAULAS, DEHRADUN, UTTARAKHAND - 248007")
st.markdown("### PROVISIONAL ESTIMATE FORM")

if df_master is not None:
    # --- PATIENT INFO TABLE ---
    with st.container():
        c1, c2, c3 = st.columns(3)
        with c1:
            pat_name = st.text_input("PATIENT NAME", value="Anuj Gill")
            age_sex = st.text_input("AGE / SEX", value="26 / M")
        with c2:
            room_cat = st.selectbox("BED CATEGORY", list(ROOM_POLICY.keys()))
            total_stay = st.number_input("ESTIMATED STAY (DAYS)", min_value=1, value=1)
        with c3:
            date_str = datetime.now().strftime("%d-%b-%Y")
            st.text_input("DATE", value=date_str, disabled=True)
            uhid = st.text_input("UHID NO.", value="NEW")

    st.divider()

    # --- ITEM SELECTION ---
    st.markdown("#### ADD SERVICES / PROCEDURES")
    col_a, col_b, col_c = st.columns([1, 2, 1])
    with col_a:
        sel_dept = st.selectbox("DEPARTMENT", sorted(df_master['Department'].unique()))
    with col_b:
        procs = sorted(df_master[df_master['Department'] == sel_dept]['Service Name'].unique())
        sel_proc = st.selectbox("SELECT PROCEDURE", procs)
    with col_c:
        is_pkg = st.checkbox("MARK AS PACKAGE", value=("CABG" in sel_proc or "TKR" in sel_proc))
        pkg_days = st.number_input("PKG COVERAGE DAYS", min_value=0, value=7 if is_pkg else 0)
        if st.button("➕ ADD ITEM"):
            row = df_master[df_master['Service Name'] == sel_proc].iloc[0]
            price_col = [c for c in df_master.columns if room_cat.lower() in c.lower().replace('  ', ' ')][0]
            price = float(str(row[price_col]).replace(',', '').replace('₹', '').strip() or 0)
            st.session_state.bill_items.append({"name": sel_proc, "price": price, "is_pkg": is_pkg, "days": pkg_days})

    # --- THE ESTIMATE TABLE (EXACT FORMAT) ---
    if st.session_state.bill_items:
        st.markdown("---")
        st.markdown(f"**PROVISIONAL ESTIMATE FOR {sel_proc.upper()}**")
        
        final_bill = []
        max_pkg_days = 0
        
        for item in st.session_state.bill_items:
            final_bill.append({"S.NO": len(final_bill)+1, "PARTICULARS": item['name'], "AMOUNT (Rs.)": item['price']})
            if item['is_pkg']:
                max_pkg_days = max(max_pkg_days, item['days'])

        # Add Policy Charges
        final_bill.append({"S.NO": len(final_bill)+1, "PARTICULARS": "ADMISSION / MRD CHARGES", "Amount (Rs.)": 450.0})
        
        extra_days = max(0, total_stay - max_pkg_days)
        r = ROOM_POLICY[room_cat]
        if extra_days > 0:
            final_bill.append({"S.NO": len(final_bill)+1, "PARTICULARS": f"EXTRA STAY CHARGES ({extra_days} DAYS)", "Amount (Rs.)": (r['Rent'] + r['Nursing'] + r['RMO'] + (r['Consult']*2) + r['Diet']) * extra_days})

        bill_df = pd.DataFrame(final_bill)
        st.table(bill_df)
        
        total_amt = sum([v for v in bill_df.iloc[:, -1] if isinstance(v, (float, int))])
        st.markdown(f"### **ESTIMATED TOTAL: Rs. {total_amt:,.2f}**")

        # --- FOOTER NOTES (Exactly as per your Sheet) ---
        st.markdown("""
        **Note:**
        1. This is only a provisional estimate; actual billing may vary based on clinical condition.
        2. Implants, Pharmacy, Blood Bank, and Consumables are extra as per actuals.
        3. Emergency visit / Special Consultant visit will be charged extra.
        4. Package is valid only for defined days; extra stay is chargeable.
        """)
        
        # PRINT BUTTON
        if st.button("🖨️ PRINT TO PDF"):
            st.success("Estimate Layout Ready. Press Ctrl+P to save as PDF.")

    with st.sidebar:
        if st.button("🗑️ RESET ESTIMATE"):
            st.session_state.bill_items = []
            st.rerun()
