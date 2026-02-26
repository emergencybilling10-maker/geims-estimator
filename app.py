import streamlit as st
import pandas as pd
from datetime import datetime

# --- PAGE CONFIG ---
st.set_page_config(page_title="GEIMS Billing System", layout="wide", page_icon="🏥")

# --- DATA LOADING (Direct from database.csv) ---
@st.cache_data(ttl=60)
def load_geims_data():
    try:
        # Load with encoding fix for Excel-based CSVs
        df_raw = pd.read_csv("database.csv", encoding='latin1', header=None)
        headers = df_raw.iloc[1].tolist()
        headers = [str(h).strip().replace('\n', ' ') for h in headers]
        df_raw.columns = headers
        df = df_raw.iloc[2:].reset_index(drop=True)
        
        # Standardizing names
        rename_map = {'Item Name': 'Service Name', 'Classic  Deluxe': 'Classic Deluxe'}
        df.columns = [rename_map.get(c, c) for c in df.columns]
        
        # Remove empty rows
        df = df.dropna(subset=['Service Name'])
        return df
    except Exception as e:
        st.error(f"Database Error: {e}")
        return None

df_master = load_geims_data()

# GEIMS 2025 FIXED POLICY RATES
ROOM_POLICY = {
    "Economy": {"Rent": 2500, "Consult": 700, "Nursing": 500, "Diet": 100, "RMO": 700},
    "Double": {"Rent": 4500, "Consult": 900, "Nursing": 600, "Diet": 100, "RMO": 800},
    "Single/ ICU": {"Rent": 7500, "Consult": 1200, "Nursing": 600, "Diet": 100, "RMO": 800},
    "Classic Deluxe": {"Rent": 10000, "Consult": 1500, "Nursing": 600, "Diet": 100, "RMO": 800},
    "Suite": {"Rent": 33000, "Consult": 2000, "Nursing": 2800, "Diet": 100, "RMO": 3000},
}

if 'bill_items' not in st.session_state:
    st.session_state.bill_items = []

# --- HEADER (Matches your Reference Sheets) ---
st.markdown("<h1 style='text-align: center;'>GRAPHIC ERA INSTITUTE OF MEDICAL SCIENCES</h1>", unsafe_allow_html=True)
st.markdown("<p style='text-align: center;'>DHAULAS, DEHRADUN, UTTARAKHAND - 248007</p>", unsafe_allow_html=True)
st.markdown("---")
st.markdown("### PROVISIONAL ESTIMATE FORM")

if df_master is not None:
    # --- PATIENT INFO SECTION ---
    with st.container():
        c1, c2, c3 = st.columns(3)
        with c1:
            pat_name = st.text_input("PATIENT NAME", value="Anuj Gill") #
            age_sex = st.text_input("AGE / SEX", value="26 / M")
        with c2:
            room_cat = st.selectbox("BED CATEGORY", list(ROOM_POLICY.keys()))
            total_stay = st.number_input("ESTIMATED STAY (DAYS)", min_value=1, value=1)
        with c3:
            date_str = datetime.now().strftime("%d-%b-%Y")
            st.text_input("DATE", value=date_str, disabled=True)
            uhid = st.text_input("UHID NO.", value="NEW")

    st.divider()

    # --- SINGLE SEARCH SELECTION ---
    st.markdown("#### ADD SERVICES / PROCEDURES")
    # All items from database.csv are now in this one searchable list
    all_services = sorted(df_master['Service Name'].unique())
    
    col_x, col_y = st.columns([3, 1])
    with col_x:
        sel_proc = st.selectbox("SEARCH & SELECT ANY ITEM (Surgery/Test/Procedure)", all_services)
    with col_y:
        is_pkg = st.checkbox("MARK AS PACKAGE", value=("CABG" in sel_proc or "TKR" in sel_proc or "PKG" in sel_proc.upper()))
        pkg_days = st.number_input("PKG COVERAGE DAYS", min_value=0, value=7 if is_pkg else 0)
        if st.button("➕ ADD TO ESTIMATE"):
            row = df_master[df_master['Service Name'] == sel_proc].iloc[0]
            # Find price for the selected room category
            price_col = [c for c in df_master.columns if room_cat.lower() in c.lower().replace('  ', ' ')][0]
            price_raw = str(row[price_col]).replace(',', '').replace('₹', '').strip()
            price = float(price_raw) if price_raw.replace('.','').isdigit() else 0.0
            st.session_state.bill_items.append({"name": sel_proc, "price": price, "is_pkg": is_pkg, "days": pkg_days})

    # --- THE ESTIMATE TABLE (EXACT FORMAT) ---
    if st.session_state.bill_items:
        st.markdown("---")
        st.markdown(f"**PROVISIONAL ESTIMATE FOR {st.session_state.bill_items[0]['name'].upper()}**")
        
        display_data = []
        max_pkg_days = 0
        
        # Adding selected items one by one
        for i, item in enumerate(st.session_state.bill_items):
            display_data.append({"S.NO": i+1, "PARTICULARS": item['name'], "AMOUNT (Rs.)": item['price']})
            if item['is_pkg']:
                max_pkg_days = max(max_pkg_days, item['days'])

        # Fixed Policy Charges
        display_data.append({"S.NO": len(display_data)+1, "PARTICULARS": "ADMISSION / MRD CHARGES", "AMOUNT (Rs.)": 450.0})
        
        # Stay Calculation
        extra_days = max(0, total_stay - max_pkg_days)
        r = ROOM_POLICY[room_cat]
        if extra_days > 0:
            stay_total = (r['Rent'] + r['Nursing'] + r['RMO'] + (r['Consult']*2) + r['Diet']) * extra_days
            display_data.append({"S.NO": len(display_data)+1, "PARTICULARS": f"EXTRA STAY CHARGES ({extra_days} DAYS)", "AMOUNT (Rs.)": stay_total})

        st.table(pd.DataFrame(display_data))
        
        total_amt = sum([row['AMOUNT (Rs.)'] for row in display_data])
        st.markdown(f"<h3 style='text-align: right;'>ESTIMATED TOTAL: Rs. {total_amt:,.2f}</h3>", unsafe_allow_html=True)

        # --- FOOTER NOTES (Matches your Reference Sheets) ---
        st.info("""
        **Note:**
        1. This is only a provisional estimate; actual billing may vary based on clinical condition.
        2. Implants, Pharmacy, Blood Bank, and Consumables are extra as per actuals.
        3. Emergency visit / Special Consultant visit will be charged extra.
        4. Package is valid only for defined days; extra stay is chargeable.
        """)
        
        if st.button("🖨️ PRINT ESTIMATE"):
            st.success("Format Ready. Use Ctrl+P to save as PDF.")

    with st.sidebar:
        if st.button("🗑️ CLEAR ESTIMATE"):
            st.session_state.bill_items = []
            st.rerun()

else:
    st.warning("🔄 Please ensure 'database.csv' is uploaded and correctly formatted.")
