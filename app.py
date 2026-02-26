import streamlit as st
import pandas as pd
import os
from datetime import datetime

# --- PAGE CONFIG ---
st.set_page_config(page_title="GEIMS Billing Portal", layout="wide", page_icon="🏥")

# --- BULLETPROOF FILE LOADER ---
@st.cache_data(ttl=60)
def load_hospital_data(category_name):
    # This force-checks for the small-letter version of the file
    target_file = f"{category_name.lower()}.csv"
            
    if not os.path.exists(target_file):
        return None
        
    try:
        # Using 'latin1' to handle special symbols in Indian Hospital Tariffs
        df = pd.read_csv(target_file, encoding='latin1')
        
        # 1. Clean column names (Remove spaces and newlines)
        df.columns = [str(c).strip().replace('\n', ' ') for c in df.columns]
        
        # 2. Force-mapping: Ensure the code finds the service name and prices
        name_map = {
            'Item Name': 'Service Name', 
            'Procedure Name': 'Service Name', 
            'Service': 'Service Name',
            'Single/ ICU': 'Single/ ICU',
            'Classic  Deluxe': 'Classic Deluxe'
        }
        df.columns = [name_map.get(c, c) for c in df.columns]
        
        # 3. Clean duplicate column names to prevent Streamlit crash
        cols = pd.Series(df.columns)
        for dup in cols[cols.duplicated()].unique():
            cols[cols == dup] = [f"{dup}_{i}" if i != 0 else dup for i in range(sum(cols == dup))]
        df.columns = cols
        
        return df.dropna(subset=['Service Name'])
    except Exception as e:
        st.error(f"Error reading {target_file}: {e}")
        return None

# --- GEIMS 2025 FIXED POLICY RATES ---
ROOM_POLICY = {
    "Economy": {"Rent": 2500, "Consult": 700, "Nursing": 500, "Diet": 100, "RMO": 700},
    "Double": {"Rent": 4500, "Consult": 900, "Nursing": 600, "Diet": 100, "RMO": 800},
    "Single/ ICU": {"Rent": 7500, "Consult": 1200, "Nursing": 600, "Diet": 100, "RMO": 800},
    "Classic Deluxe": {"Rent": 10000, "Consult": 1500, "Nursing": 600, "Diet": 100, "RMO": 800},
    "Suite": {"Rent": 33000, "Consult": 2000, "Nursing": 2800, "Diet": 100, "RMO": 3000},
}

if 'bill_items' not in st.session_state:
    st.session_state.bill_items = []

# --- HOSPITAL HEADER (Matches your "ESTIMATE CASH" Reference) ---
st.markdown("<h1 style='text-align: center;'>GRAPHIC ERA INSTITUTE OF MEDICAL SCIENCES</h1>", unsafe_allow_html=True)
st.markdown("<p style='text-align: center;'>DHAULAS, DEHRADUN, UTTARAKHAND - 248007</p>", unsafe_allow_html=True)
st.markdown("---")
st.markdown("### PROVISIONAL ESTIMATE GENERATOR")

# --- PATIENT INFO SECTION ---
with st.container():
    c1, c2, c3 = st.columns(3)
    with c1:
        pat_name = st.text_input("PATIENT NAME", value="Anuj Gill") 
        age_sex = st.text_input("AGE / SEX", value="26 / M")
    with c2:
        room_cat = st.selectbox("BED CATEGORY", list(ROOM_POLICY.keys()))
        total_stay = st.number_input("ESTIMATED STAY (DAYS)", min_value=1, value=1)
    with c3:
        date_now = datetime.now().strftime("%d-%b-%Y")
        st.text_input("DATE", value=date_now, disabled=True)
        uhid = st.text_input("UHID NO.", value="NEW")

st.divider()

# --- CATEGORY SELECTOR (Small-Letter Map) ---
category = st.selectbox("CHOOSE DATA SOURCE:", ["Investigation", "Procedure", "Surgery", "Gyane"])
df_active = load_hospital_data(category)

if df_active is not None:
    search_q = st.text_input(f"Search inside {category.lower()}.csv:")
    if search_q:
        # Deep search across all items in the selected file
        filtered = df_active[df_active['Service Name'].str.contains(search_q, case=False, na=False)]
        if not filtered.empty:
            sel_item = st.selectbox("Select Result:", filtered['Service Name'].unique())
            
            # Package logic for multi-day stay
            is_pkg = "PKG" in sel_item.upper() or "PACKAGE" in sel_item.upper() or category in ["Surgery", "Gyane"]
            
            if st.button("➕ ADD TO ESTIMATE"):
                row = filtered[filtered['Service Name'] == sel_item].iloc[0]
                try:
                    # Finds price based on selected room category
                    price_col = [c for c in df_active.columns if room_cat.lower() in c.lower()][0]
                    price = float(str(row[price_col]).replace(',', '').replace('₹', '').strip())
                except:
                    price = 0.0
                
                # Detect package days or default
                pkg_days = 0
                if is_pkg:
                    pkg_col = [c for c in df_active.columns if 'day' in c.lower()]
                    pkg_days = int(row[pkg_col[0]]) if pkg_col and str(row[pkg_col[0]]).isdigit() else 7 if "CABG" in sel_item.upper() else 1
                
                st.session_state.bill_items.append({"name": sel_item, "price": price, "is_pkg": is_pkg, "days": pkg_days})
                st.success(f"Added: {sel_item}")
        else:
            st.error(f"No matches found in {category.lower()}.csv.")
else:
    st.warning(f"⚠️ File '{category.lower()}.csv' not found. Please verify it is on GitHub.")

# --- ESTIMATE TABLE ---
if st.session_state.bill_items:
    st.markdown("---")
    estimate_data = []
    max_pkg_days = 0
    
    for i, item in enumerate(st.session_state.bill_items):
        estimate_data.append({"S.NO": i+1, "PARTICULARS": item['name'], "AMOUNT (Rs.)": item['price']})
        if item['is_pkg']:
            max_pkg_days = max(max_pkg_days, item['days'])

    # Fixed GEIMS MRD Charge
    estimate_data.append({"S.NO": len(estimate_data)+1, "PARTICULARS": "ADMISSION / MRD CHARGES", "AMOUNT (Rs.)": 450.0})
    
    # Stay calculation
    extra_days = max(0, total_stay - max_pkg_days)
    r = ROOM_POLICY[room_cat]
    if extra_days > 0:
        stay_cost = (r['Rent'] + r['Nursing'] + r['RMO'] + (r['Consult']*2) + r['Diet']) * extra_days
        estimate_data.append({"S.NO": len(estimate_data)+1, "PARTICULARS": f"EXTRA STAY CHARGES ({extra_days} DAYS)", "AMOUNT (Rs.)": stay_cost})

    st.table(pd.DataFrame(estimate_data))
    
    total = sum([x['AMOUNT (Rs.)'] for x in estimate_data if isinstance(x['AMOUNT (Rs.)'], (int, float))])
    st.markdown(f"<h3 style='text-align: right;'>ESTIMATED TOTAL: Rs. {total:,.2f}</h3>", unsafe_allow_html=True)

    # FOOTER NOTES
    st.info("Note: Provisional estimate. Implants, Pharmacy, and Consumables are extra.")

with st.sidebar:
    if st.button("🗑️ RESET ESTIMATE"):
        st.session_state.bill_items = []
        st.rerun()
