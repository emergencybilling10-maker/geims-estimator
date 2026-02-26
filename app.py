import streamlit as st
import pandas as pd
import os
from datetime import datetime

# --- PAGE CONFIG ---
st.set_page_config(page_title="GEIMS Master Billing", layout="wide", page_icon="🏥")

# --- MASTER DATA LOADER ---
@st.cache_data(ttl=60)
def load_master_data():
    file_path = "database.csv"
    if not os.path.exists(file_path):
        return None
    try:
        # Loading with latin1 to handle special characters
        df_raw = pd.read_csv(file_path, encoding='latin1', header=None)
        
        # SEARCH FOR HEADERS: Finding the row that defines the room categories
        header_idx = 1
        for i in range(5):
            row_str = str(df_raw.iloc[i].values).lower()
            if 'economy' in row_str or 'item name' in row_str:
                header_idx = i
                break
        
        headers = [str(h).strip().replace('\n', ' ') for h in df_raw.iloc[header_idx]]
        df_raw.columns = headers
        df = df_raw.iloc[header_idx + 1:].reset_index(drop=True)
        
        # Standardizing the Name column
        name_col = next((c for c in df.columns if any(k in c.lower() for k in ['name', 'item', 'particulars'])), df.columns[1])
        df = df.rename(columns={name_col: "Service Name"})
        
        return df.dropna(subset=["Service Name"])
    except Exception as e:
        st.error(f"Error reading master database: {e}")
        return None

# --- GEIMS 2025 POLICY RATES ---
ROOM_POLICY = {
    "Economy": {"Rent": 2500, "Consult": 700, "Nursing": 500, "Diet": 100, "RMO": 700},
    "Double": {"Rent": 4500, "Consult": 900, "Nursing": 600, "Diet": 100, "RMO": 800},
    "Single/ ICU": {"Rent": 7500, "Consult": 1200, "Nursing": 600, "Diet": 100, "RMO": 800},
    "Classic Deluxe": {"Rent": 10000, "Consult": 1500, "Nursing": 600, "Diet": 100, "RMO": 800},
    "Suite": {"Rent": 33000, "Consult": 2000, "Nursing": 2800, "Diet": 100, "RMO": 3000},
}

if 'bill_items' not in st.session_state:
    st.session_state.bill_items = []

# --- HEADER ---
st.markdown("<h1 style='text-align: center;'>GRAPHIC ERA INSTITUTE OF MEDICAL SCIENCES</h1>", unsafe_allow_html=True)
st.markdown("<p style='text-align: center;'>DHAULAS, DEHRADUN, UTTARAKHAND - 248007</p>", unsafe_allow_html=True)
st.markdown("---")
st.markdown("### PROVISIONAL ESTIMATE GENERATOR")

# --- PATIENT INFO ---
with st.container():
    c1, c2, c3 = st.columns(3)
    with c1:
        pat_name = st.text_input("PATIENT NAME", value="Anuj Gill") #
    with c2:
        room_cat = st.selectbox("BED CATEGORY", list(ROOM_POLICY.keys()))
        total_stay = st.number_input("ESTIMATED STAY (DAYS)", min_value=1, value=1)
    with c3:
        uhid = st.text_input("UHID NO.", value="NEW")

st.divider()

# --- MASTER SEARCH ---
df_master = load_master_data()

if df_master is not None:
    st.markdown("#### SEARCH ENTIRE TARIFF (Investigations & Surgeries)")
    search_q = st.text_input("Type Item Name (e.g. 'CAG', 'Blood', 'CABG'):")
    
    if search_q:
        # Search every row for the keyword
        mask = df_master["Service Name"].astype(str).str.contains(search_q, case=False, na=False)
        filtered = df_master[mask]
        
        if not filtered.empty:
            sel_item = st.selectbox("Select Result:", filtered["Service Name"].unique())
            
            if st.button("➕ ADD ITEM TO ESTIMATE"):
                row = filtered[filtered["Service Name"] == sel_item].iloc[0]
                
                # SMART PRICE DETECTION
                try:
                    # Look for the bed category in headers. If not found, use the first price column (OPD rate)
                    price_cols = [c for c in df_master.columns if room_cat.lower() in str(c).lower()]
                    price_col = price_cols[0] if price_cols else df_master.columns[3]
                    
                    price_raw = str(row[price_col]).replace(',', '').replace('₹', '').strip()
                    price = float(price_raw) if price_raw.replace('.','').isdigit() else 0.0
                except:
                    price = 0.0
                
                st.session_state.bill_items.append({"name": sel_item, "price": price})
                st.success(f"Added {sel_item}")
        else:
            st.error("No matches found in the database.")
else:
    st.warning("⚠️ Master file 'database.csv' not found on GitHub.")

# --- ESTIMATE TABLE ---
if st.session_state.bill_items:
    st.markdown("---")
    bill_df = pd.DataFrame(st.session_state.bill_items)
    bill_df.index += 1
    st.table(bill_df.rename(columns={"name": "PARTICULARS", "price": "AMOUNT (Rs.)"}))
    
    total = sum([x['price'] for x in st.session_state.bill_items]) + 450.0 #
    st.markdown(f"**MRD Charges: Rs. 450.00**")
    st.markdown(f"### TOTAL ESTIMATE: Rs. {total:,.2f}")
    
    # FOOTER NOTES
    st.info("Note: Provisional estimate. Actuals may vary based on clinical condition.")
    st.button("🖨️ PRINT (Ctrl+P)")

with st.sidebar:
    if st.button("🗑️ RESET"):
        st.session_state.bill_items = []
        st.rerun()
