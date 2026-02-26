import streamlit as st
import pandas as pd
from datetime import datetime

# --- PAGE CONFIG ---
st.set_page_config(page_title="GEIMS Billing Tool", layout="wide", page_icon="🏥")

# --- POWER SEARCH DATA LOADING ---
@st.cache_data(ttl=60)
def load_geims_data():
    try:
        # Load the CSV using 'latin1' to handle special Indian Rupee symbols
        df_raw = pd.read_csv("database.csv", encoding='latin1', header=None)
        
        # Headers are in Row 1
        headers = df_raw.iloc[1].tolist()
        headers = [str(h).strip().replace('\n', ' ') for h in headers]
        df_raw.columns = headers
        
        # Keep every single row from Row 2 to the end
        df = df_raw.iloc[2:].reset_index(drop=True)
        
        # Standardize 'Service Name' for searching
        if 'Item Name' in df.columns:
            df = df.rename(columns={'Item Name': 'Service Name'})
        
        # CLEANING: Remove hidden characters and ensure every row is searchable
        df['Service Name'] = df['Service Name'].astype(str).str.strip()
        df = df[df['Service Name'] != 'nan']
        
        return df
    except Exception as e:
        st.error(f"Database Sync Error: {e}")
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

# --- HOSPITAL HEADER (Exact Format) ---
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

    # --- POWER SEARCH INTERFACE ---
    st.markdown("#### SEARCH ALL TARIFF ITEMS (Packages & Investigations)")
    
    # This search box now hits every single row in the database
    search_query = st.text_input("Type Surgery or Investigation Name (e.g., 'Angiography', 'CAG', 'TKR')")
    
    if search_query:
        # Filter the master list based on your typing
        filtered_df = df_master[df_master['Service Name'].str.contains(search_query, case=False, na=False)]
        
        if not filtered_df.empty:
            sel_proc = st.selectbox("Select from results:", filtered_df['Service Name'].unique())
            
            col_pkg1, col_pkg2 = st.columns([1, 1])
            with col_pkg1:
                is_pkg = st.checkbox("MARK AS PACKAGE", value=("PKG" in sel_proc.upper() or "PACKAGE" in sel_proc.upper()))
            with col_pkg2:
                pkg_days = st.number_input("PKG COVERAGE DAYS", min_value=0, value=7 if "CABG" in sel_proc.upper() else 1 if is_pkg else 0)
            
            if st.button("➕ ADD SELECTED ITEM TO ESTIMATE"):
                row = filtered_df[filtered_df['Service Name'] == sel_proc].iloc[0]
                # Dynamic column mapping to find the price for your room category
                price_col = [c for c in filtered_df.columns if room_cat.lower() in c.lower().replace('  ', ' ')][0]
                price_raw = str(row[price_col]).replace(',', '').replace('₹', '').strip()
                price = float(price_raw) if price_raw.replace('.','').isdigit() else 0.0
                st.session_state.bill_items.append({"name": sel_proc, "price": price, "is_pkg": is_pkg, "days": pkg_days})
                st.success(f"Added {sel_proc}")
        else:
            st.error("No matches found. Try a different keyword.")

    # --- ESTIMATE TABLE (Exact Format) ---
    if st.session_state.bill_items:
        st.markdown("---")
        display_data = []
        max_pkg_days = 0
        
        for i, item in enumerate(st.session_state.bill_items):
            display_data.append({"S.NO": i+1, "PARTICULARS": item['name'], "AMOUNT (Rs.)": item['price']})
            if item['is_pkg']:
                max_pkg_days = max(max_pkg_days, item['days'])

        # Mandatory Fees
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

        # --- FOOTER NOTES (Exactly as per your reference) ---
        st.info("""
        **Note:**
        1. This is only a provisional estimate; actual billing may vary based on clinical condition.
        2. Implants, Pharmacy, Blood Bank, and Consumables are extra as per actuals.
        3. Emergency visit / Special Consultant visit will be charged extra.
        4. Package is valid only for defined days; extra stay is chargeable.
        """)
        
        st.button("🖨️ PRINT ESTIMATE (Ctrl+P)")

    with st.sidebar:
        if st.button("🗑️ CLEAR ESTIMATE"):
            st.session_state.bill_items = []
            st.rerun()

else:
    st.warning("🔄 System is waiting for 'database.csv'. Please refresh after upload.")
