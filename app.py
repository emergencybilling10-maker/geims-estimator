import streamlit as st
import pandas as pd
from datetime import datetime
import os

# --- PAGE CONFIG ---
st.set_page_config(page_title="GEIMS Billing Tool", layout="wide", page_icon="🏥")

# --- MULTI-FILE LOADING LOGIC ---
@st.cache_data(ttl=60)
def load_all_geims_data():
    # The four files you are uploading
    files = ["investigation.csv", "procedure_charges.csv", "surgery.csv", "gyane_package.csv"]
    all_dfs = []
    
    for f in files:
        if os.path.exists(f):
            try:
                # Using latin1 to handle special characters from Excel
                df = pd.read_csv(f, encoding='latin1')
                df.columns = [str(c).strip() for c in df.columns]
                # Ensure Service Name column exists for searching
                if 'Service Name' in df.columns or 'Item Name' in df.columns:
                    df = df.rename(columns={'Item Name': 'Service Name'})
                    all_dfs.append(df)
            except:
                continue
    
    if all_dfs:
        return pd.concat(all_dfs, ignore_index=True)
    return None

df_master = load_all_geims_data()

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

# --- HOSPITAL HEADER ---
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

    # --- SEARCH & ADD SECTION ---
    st.markdown("#### SEARCH SERVICES (Scans All 4 CSV Files)")
    search_query = st.text_input("Type Surgery, Package, or Investigation Name:")
    
    if search_query:
        # Search every row for the keyword
        mask = df_master['Service Name'].str.contains(search_query, case=False, na=False)
        filtered_df = df_master[mask]
        
        if not filtered_df.empty:
            sel_proc = st.selectbox("Select from results:", filtered_df['Service Name'].unique())
            
            cp1, cp2 = st.columns(2)
            with cp1:
                # Auto-check if it's a package from Gyne or Surgery files
                is_pkg = st.checkbox("MARK AS PACKAGE", value=("PKG" in sel_proc.upper() or "PACKAGE" in sel_proc.upper()))
            with cp2:
                pkg_days = st.number_input("PKG COVERAGE DAYS", min_value=0, value=7 if "SURGERY" in sel_proc.upper() else 1 if is_pkg else 0)
            
            if st.button("➕ ADD TO ESTIMATE"):
                row = filtered_df[filtered_df['Service Name'] == sel_proc].iloc[0]
                # Dynamic price detection
                price_col = [c for c in df_master.columns if room_cat.lower() in c.lower()][0]
                price = float(str(row[price_col]).replace(',', '').replace('₹', '').strip() or 0)
                st.session_state.bill_items.append({"name": sel_proc, "price": price, "is_pkg": is_pkg, "days": pkg_days})
                st.success(f"Added: {sel_proc}")

    # --- ESTIMATE TABLE ---
    if st.session_state.bill_items:
        st.markdown("---")
        display_data = []
        max_pkg_days = 0
        
        for i, item in enumerate(st.session_state.bill_items):
            display_data.append({"S.NO": i+1, "PARTICULARS": item['name'], "AMOUNT (Rs.)": item['price']})
            if item['is_pkg']:
                max_pkg_days = max(max_pkg_days, item['days'])

        # Official Fees
        display_data.append({"S.NO": len(display_data)+1, "PARTICULARS": "ADMISSION / MRD CHARGES", "AMOUNT (Rs.)": 450.0})
        
        # Policy Stay Calculation
        extra_days = max(0, total_stay - max_pkg_days)
        r = ROOM_POLICY[room_cat]
        if extra_days > 0:
            stay_total = (r['Rent'] + r['Nursing'] + r['RMO'] + (r['Consult']*2) + r['Diet']) * extra_days
            display_data.append({"S.NO": len(display_data)+1, "PARTICULARS": f"EXTRA STAY ({extra_days} DAYS)", "AMOUNT (Rs.)": stay_total})

        st.table(pd.DataFrame(display_data))
        
        total_val = sum([item['AMOUNT (Rs.)'] for item in display_data])
        st.markdown(f"<h3 style='text-align: right;'>ESTIMATED TOTAL: Rs. {total_val:,.2f}</h3>", unsafe_allow_html=True)

        # FOOTER NOTES
        st.info("Note: Provisional estimate. Implants/Pharmacy extra.")
        st.button("🖨️ PRINT (Ctrl+P)")

    with st.sidebar:
        if st.button("🗑️ RESET"):
            st.session_state.bill_items = []
            st.rerun()
else:
    st.warning("Waiting for the 4 CSV files (investigation.csv, procedure_charges.csv, etc.) on GitHub.")
