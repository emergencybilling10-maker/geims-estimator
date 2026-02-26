import streamlit as st
import pandas as pd
import os
from datetime import datetime

# --- PAGE CONFIG ---
st.set_page_config(page_title="GEIMS Billing Portal", layout="wide", page_icon="🏥")

# --- SMART FILE LOADER (Case-Insensitive) ---
@st.cache_data(ttl=60)
def load_hospital_data(category_name):
    # Search for the file on GitHub regardless of capitalization
    all_files = os.listdir('.')
    target_file = None
    for f in all_files:
        if f.lower() == f"{category_name.lower()}.csv":
            target_file = f
            break
            
    if not target_file:
        return None
        
    try:
        # Load the CSV and clean standard GEIMS headers
        df = pd.read_csv(target_file, encoding='latin1')
        df.columns = [str(c).strip() for c in df.columns]
        
        # Mapping possible header variations to 'Service Name'
        name_map = {'Item Name': 'Service Name', 'Procedure Name': 'Service Name', 'Service': 'Service Name'}
        df.columns = [name_map.get(c, c) for c in df.columns]
        
        return df.dropna(subset=['Service Name'])
    except Exception as e:
        st.error(f"Error reading {target_file}: {e}")
        return None

# --- GEIMS 2025 FIXED POLICY ---
ROOM_POLICY = {
    "Economy": {"Rent": 2500, "Consult": 700, "Nursing": 500, "Diet": 100, "RMO": 700},
    "Double": {"Rent": 4500, "Consult": 900, "Nursing": 600, "Diet": 100, "RMO": 800},
    "Single/ ICU": {"Rent": 7500, "Consult": 1200, "Nursing": 600, "Diet": 100, "RMO": 800},
    "Classic Deluxe": {"Rent": 10000, "Consult": 1500, "Nursing": 600, "Diet": 100, "RMO": 800},
    "Suite": {"Rent": 33000, "Consult": 2000, "Nursing": 2800, "Diet": 100, "RMO": 3000},
}

if 'bill_items' not in st.session_state:
    st.session_state.bill_items = []

# --- HOSPITAL HEADER (Exact Reference Format) ---
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

# --- CATEGORY SELECTOR (Matched to your files) ---
category = st.selectbox("CHOOSE DATA SOURCE:", ["Investigation", "Procedure", "Surgery", "Gyane"])
df_active = load_hospital_data(category)

if df_active is not None:
    search_q = st.text_input(f"Search inside {category}:")
    if search_q:
        # Direct searchable list of all items in that specific CSV
        filtered = df_active[df_active['Service Name'].str.contains(search_q, case=False, na=False)]
        if not filtered.empty:
            sel_item = st.selectbox("Select Result:", filtered['Service Name'].unique())
            
            # Package detection for multi-day stay logic
            is_pkg = "PKG" in sel_item.upper() or "PACKAGE" in sel_item.upper() or category in ["Surgery", "Gyane"]
            
            if st.button("➕ ADD TO ESTIMATE"):
                row = filtered[filtered['Service Name'] == sel_item].iloc[0]
                try:
                    # Finds price based on selected room type
                    price_col = [c for c in df_active.columns if room_cat.lower() in c.lower()][0]
                    price = float(str(
