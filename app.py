import streamlit as st
import pandas as pd
from datetime import datetime

# --- PAGE CONFIG ---
st.set_page_config(page_title="GEIMS Billing Tool", layout="wide", page_icon="🏥")

# --- DATA LOADING WITH RECOVERY LOGIC ---
@st.cache_data(ttl=60)
def load_geims_data():
    try:
        # Load the CSV with 'latin1' to avoid encoding crashes
        df_raw = pd.read_csv("database.csv", encoding='latin1', header=None)
        
        # We search Row 0 to Row 5 for the header that contains 'Item Name' or 'Economy'
        header_row = 1 
        for i in range(5):
            if 'Economy' in str(df_raw.iloc[i].values):
                header_row = i
                break
        
        headers = df_raw.iloc[header_row].tolist()
        headers = [str(h).strip().replace('\n', ' ') for h in headers]
        df_raw.columns = headers
        
        # Keep ALL rows to ensure no packages are missed
        df = df_raw.iloc[header_row + 1:].reset_index(drop=True)
        
        # Force column names to be standard
        if 'Item Name' in df.columns:
            df = df.rename(columns={'Item Name': 'Service Name'})
        elif 'PROCEDURE CHARGES SPECIALITY WISE' in df.columns:
             df = df.rename(columns={'PROCEDURE CHARGES SPECIALITY WISE': 'Service Name'})
        
        # CLEANING: Remove completely empty rows but KEEP everything else
        df['Service Name'] = df['Service Name'].astype(str).str.strip()
        return df
    except Exception as e:
        st.error(f"Critical Sync Error: {e}")
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

# --- GEIMS HEADER ---
st.markdown("<h1 style='text-align: center;'>GRAPHIC ERA INSTITUTE OF MEDICAL SCIENCES</h1>", unsafe_allow_html=True)
st.markdown("<p style='text-align: center;'>DHAULAS, DEHRADUN, UTTARAKHAND - 248007</p>", unsafe_allow_html=True)
st.markdown("---")

# --- DIAGNOSTIC TOOL (Remove this after fix) ---
with st.expander("🔍 DIAGNOSTIC MODE: View Raw CSV Data"):
    if df_master is not None:
        st.write("First 20 rows of your CSV. Check if 'Item Name' or 'Economy' columns look right:")
        st.dataframe(df_master.head(20))

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

# --- THE SEARCH ENGINE ---
st.markdown("#### SEARCH TARIFF (Type 'CAG', 'Angiography', or 'Package')")
search_query = st.text_input("Search Item Name:")

if search_query and df_master is not None:
    # We search in multiple possible columns just in case
    filtered_df = df_master[df_master.apply(lambda row: search_query.lower() in str(row.values).lower(), axis=1)]
    
    if not filtered_df.empty:
        # Use the first column that looks like a name
        name_col = 'Service Name' if 'Service Name' in filtered_df.columns else filtered_df.columns[1]
        sel_proc = st.selectbox("Select exact item:", filtered_df[name_col].unique())
        
        if st.button("➕ ADD TO ESTIMATE"):
            row = filtered_df[filtered_df[name_col] == sel_proc].iloc[0]
            # Try to find price column
            try:
                price_col = [c for c in filtered_df.columns if room_cat.lower() in str(c).lower()][0]
                price = float(str(row[price_col]).replace(',', '').replace('₹', '').strip())
            except:
                price = 0.0
            
            is_pkg = "PKG" in str(sel_proc).upper() or "PACKAGE" in str(sel_proc).upper()
            st.session_state.bill_items.append({"name": sel_proc, "price": price, "is_pkg": is_pkg})
            st.rerun()

# --- ESTIMATE TABLE ---
if st.session_state.bill_items:
    st.markdown("---")
    bill_data = []
    for i, item in enumerate(st.session_state.bill_items):
        bill_data.append({"S.NO": i+1, "PARTICULARS": item['name'], "AMOUNT (Rs.)": item['price']})
    
    bill_data.append({"S.NO": len(bill_data)+1, "PARTICULARS": "ADMISSION / MRD CHARGES", "AMOUNT (Rs.)": 450.0})
    
    st.table(pd.DataFrame(bill_data))
    
    # FOOTER NOTES
    st.info("Note: Provisional estimate. Implants/Pharmacy extra.")
    st.button("🖨️ PRINT (Ctrl+P)")

with st.sidebar:
    if st.button("🗑️ RESET"):
        st.session_state.bill_items = []
        st.rerun()
