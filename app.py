import streamlit as st
import pandas as pd
import os
from datetime import datetime

# --- PAGE CONFIG ---
st.set_page_config(page_title="GEIMS Billing Tool", layout="wide", page_icon="🏥")

# --- SMART MULTI-FILE LOADER ---
@st.cache_data(ttl=60)
def load_all_geims_data():
    files = ["investigations.csv", "procedure_charges.csv", "surgical_procedures.csv", "gyane_packages.csv"]
    all_dfs = []
    
    for f in files:
        if os.path.exists(f):
            try:
                # Try different encodings to prevent the 'utf-8' error
                temp_df = pd.read_csv(f, encoding='latin1')
                temp_df.columns = [str(c).strip() for c in temp_df.columns]
                all_dfs.append(temp_df)
            except:
                continue
                
    if not all_dfs:
        return None
    
    # Combine everything into one searchable database
    master_df = pd.concat(all_dfs, ignore_index=True)
    return master_df

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
    # --- PATIENT INFO ---
    with st.container():
        c1, c2, c3 = st.columns(3)
        with c1:
            pat_name = st.text_input("PATIENT NAME", value="Anuj Gill") #
            age_sex = st.text_input("AGE / SEX", value="26 / M")
        with c2:
            room_cat = st.selectbox("BED CATEGORY", list(ROOM_POLICY.keys()))
            total_stay = st.number_input("ESTIMATED STAY (DAYS)", min_value=1, value=1)
        with c3:
            uhid = st.text_input("UHID NO.", value="NEW")

    st.divider()

    # --- UNIVERSAL SEARCH BOX ---
    st.markdown("#### SEARCH ANY ITEM (Investigations, Surgeries, or Gyane Packages)")
    search_query = st.text_input("Type here to search (e.g. LSCS, Blood Test, TKR)...")
    
    if search_query:
        # Searches through all four files at once
        mask = df_master.apply(lambda row: row.astype(str).str.contains(search_query, case=False).any(), axis=1)
        filtered_df = df_master[mask]
        
        if not filtered_df.empty:
            # Use Service Name column or fallback to first column
            name_col = 'Service Name' if 'Service Name' in filtered_df.columns else filtered_df.columns[0]
            sel_proc = st.selectbox("Found matches:", filtered_df[name_col].unique())
            
            col_a, col_b = st.columns(2)
            with col_a:
                is_pkg = st.checkbox("MARK AS PACKAGE", value=("PKG" in sel_proc.upper() or "PACKAGE" in sel_proc.upper()))
            with col_b:
                pkg_days = st.number_input("PKG COVERAGE DAYS", min_value=0, value=1 if is_pkg else 0)
                
            if st.button("➕ ADD TO ESTIMATE"):
                row = filtered_df[filtered_df[name_col] == sel_proc].iloc[0]
                price_col = [c for c in df_master.columns if room_cat.lower() in str(c).lower()][0]
                price = float(str(row[price_col]).replace(',', '').replace('₹', '').strip())
                st.session_state.bill_items.append({"name": sel_proc, "price": price, "is_pkg": is_pkg, "days": pkg_days})
                st.rerun()

    # --- ESTIMATE DISPLAY ---
    if st.session_state.bill_items:
        st.markdown("---")
        bill_data = []
        max_pkg_days = 0
        for i, item in enumerate(st.session_state.bill_items):
            bill_data.append({"S.NO": i+1, "PARTICULARS": item['name'], "AMOUNT (Rs.)": item['price']})
            if item['is_pkg']: max_pkg_days = max(max_pkg_days, item['days'])

        bill_data.append({"S.NO": len(bill_data)+1, "PARTICULARS": "ADMISSION / MRD CHARGES", "AMOUNT (Rs.)": 450.0})
        
        # Stay Math
        extra_days = max(0, total_stay - max_pkg_days)
        r = ROOM_POLICY[room_cat]
        if extra_days > 0:
            stay_charge = (r['Rent'] + r['Nursing'] + r['RMO'] + (r['Consult']*2) + r['Diet']) * extra_days
            bill_data.append({"S.NO": len(bill_data)+1, "PARTICULARS": f"EXTRA STAY ({extra_days} DAYS)", "AMOUNT (Rs.)": stay_charge})

        st.table(pd.DataFrame(bill_data))
        total = sum([row['AMOUNT (Rs.)'] for row in bill_data])
        st.markdown(f"<h3 style='text-align: right;'>TOTAL: Rs. {total:,.2f}</h3>", unsafe_allow_html=True)
        
        st.info("Note: Provisional estimate. Implants/Pharmacy extra.")

else:
    st.warning("🔄 Please upload the four CSV files to GitHub to activate the system.")
