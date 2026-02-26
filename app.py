import streamlit as st
import pandas as pd
import os
from datetime import datetime

# --- PAGE CONFIG ---
st.set_page_config(page_title="GEIMS Billing Portal", layout="wide", page_icon="🏥")

# --- SMART DATA LOADER (For 4 Individual Files) ---
@st.cache_data(ttl=60)
def load_hospital_data(file_name):
    if not os.path.exists(file_name):
        return None
    try:
        # Load and clean headers instantly
        df = pd.read_csv(file_name, encoding='latin1')
        df.columns = [str(c).strip() for c in df.columns]
        
        # Standardize 'Service Name' across all files
        name_map = {'Item Name': 'Service Name', 'Procedure Name': 'Service Name'}
        df.columns = [name_map.get(c, c) for c in df.columns]
        
        return df.dropna(subset=['Service Name'])
    except:
        return None

# --- GEIMS 2025 POLICY ---
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
st.markdown("### PROVISIONAL ESTIMATE GENERATOR")

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
        date_now = datetime.now().strftime("%d-%b-%Y")
        st.text_input("DATE", value=date_now, disabled=True)
        uhid = st.text_input("UHID NO.", value="NEW")

st.divider()

# --- CATEGORY SELECTOR ---
st.markdown("#### SELECT CATEGORY & SEARCH ITEM")
cat_col, search_col = st.columns([1, 2])

with cat_col:
    # Use your four specific files
    category = st.selectbox("Choose Data Type:", ["Investigation", "Procedure", "Surgery", "Gyane"])
    file_name = f"{category.lower()}.csv"

with search_col:
    df_active = load_hospital_data(file_name)
    if df_active is not None:
        search_q = st.text_input(f"Type to search in {category}:")
        if search_q:
            filtered = df_active[df_active['Service Name'].str.contains(search_q, case=False, na=False)]
            if not filtered.empty:
                sel_item = st.selectbox("Select Item:", filtered['Service Name'].unique())
                
                # Package Logic (Auto-detect from file or name)
                is_pkg = "PKG" in sel_item.upper() or "PACKAGE" in sel_item.upper() or category in ["Surgery", "Gyane"]
                
                if st.button("➕ ADD TO ESTIMATE"):
                    row = filtered[filtered['Service Name'] == sel_item].iloc[0]
                    # Find price column
                    try:
                        price_col = [c for c in df_active.columns if room_cat.lower() in c.lower()][0]
                        price = float(str(row[price_col]).replace(',', '').replace('₹', '').strip())
                    except:
                        price = 0.0
                    
                    # Get Package Days from CSV or default
                    pkg_days = 0
                    if is_pkg:
                        pkg_col = [c for c in df_active.columns if 'day' in c.lower()]
                        pkg_days = int(row[pkg_col[0]]) if pkg_col else 7 if "CABG" in sel_item.upper() else 1
                    
                    st.session_state.bill_items.append({"name": sel_item, "price": price, "is_pkg": is_pkg, "days": pkg_days})
                    st.success(f"Added: {sel_item}")
            else:
                st.error("No matches found.")
    else:
        st.warning(f"File '{file_name}' not found. Please upload it to GitHub.")

# --- ESTIMATE TABLE ---
if st.session_state.bill_items:
    st.markdown("---")
    estimate_data = []
    max_pkg_days = 0
    
    for i, item in enumerate(st.session_state.bill_items):
        estimate_data.append({"S.NO": i+1, "PARTICULARS": item['name'], "AMOUNT (Rs.)": item['price']})
        if item['is_pkg']:
            max_pkg_days = max(max_pkg_days, item['days'])

    # Fixed Charges
    estimate_data.append({"S.NO": len(estimate_data)+1, "PARTICULARS": "ADMISSION / MRD CHARGES", "AMOUNT (Rs.)": 450.0})
    
    # Stay Policy
    extra_days = max(0, total_stay - max_pkg_days)
    r = ROOM_POLICY[room_cat]
    if extra_days > 0:
        stay_cost = (r['Rent'] + r['Nursing'] + r['RMO'] + (r['Consult']*2) + r['Diet']) * extra_days
        estimate_data.append({"S.NO": len(estimate_data)+1, "PARTICULARS": f"EXTRA STAY CHARGES ({extra_days} DAYS)", "AMOUNT (Rs.)": stay_cost})

    st.table(pd.DataFrame(estimate_data))
    
    total = sum([x['AMOUNT (Rs.)'] for x in estimate_data])
    st.markdown(f"<h3 style='text-align: right;'>ESTIMATED TOTAL: Rs. {total:,.2f}</h3>", unsafe_allow_html=True)

    # FOOTER NOTES
    st.info("Note: Provisional estimate. Actuals may vary based on clinical condition. Implants/Pharmacy extra.")
    st.button("🖨️ PRINT (Ctrl+P)")

with st.sidebar:
    if st.button("🗑️ RESET"):
        st.session_state.bill_items = []
        st.rerun()
