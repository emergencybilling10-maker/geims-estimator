import streamlit as st
import pandas as pd
import os
from datetime import datetime

# --- PAGE CONFIG ---
st.set_page_config(page_title="GEIMS Billing Portal", layout="wide", page_icon="🏥")

# --- HYBRID DATA LOADER ---
@st.cache_data(ttl=60)
def load_hospital_data(category_name):
    target_file = f"{category_name.lower()}.csv"
    if not os.path.exists(target_file):
        return None
    try:
        # Load the CSV with Latin1 for Indian Rupee symbols
        df = pd.read_csv(target_file, encoding='latin1')
        
        # Standardize headers for the search engine
        new_cols = [str(c).strip().replace('\n', ' ') for c in df.columns]
        # Force column 1 to be the name source
        if len(new_cols) > 1:
            new_cols[1] = "Service Name"
        df.columns = new_cols
        
        return df.dropna(subset=["Service Name"])
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

# --- HEADER (Professional Format) ---
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

# --- SEARCH ---
category = st.selectbox("CHOOSE DATA SOURCE:", ["Investigation", "Procedure", "Surgery", "Gyane"])
df_active = load_hospital_data(category)

if df_active is not None:
    search_q = st.text_input(f"Search inside {category.lower()}.csv:")
    if search_q:
        filtered = df_active[df_active["Service Name"].astype(str).str.contains(search_q, case=False, na=False)]
        if not filtered.empty:
            sel_item = st.selectbox("Select Result:", filtered["Service Name"].unique())
            
            if st.button("➕ ADD ITEM"):
                row = filtered[filtered["Service Name"] == sel_item].iloc[0]
                
                # PRICE LOGIC: OPD vs Bed Category
                try:
                    if category == "Investigation":
                        # For Investigations, just take the first numeric column found
                        price_val = row.iloc[3] if len(row) > 3 else row.iloc[2]
                    else:
                        # For Packages, search for the room category in the header
                        price_col = [c for c in df_active.columns if room_cat.lower() in str(c).lower()][0]
                        price_val = row[price_col]
                    
                    price = float(str(price_val).replace(',', '').replace('₹', '').strip())
                except:
                    price = 0.0
                
                st.session_state.bill_items.append({"name": sel_item, "price": price})
                st.success(f"Added {sel_item} @ Rs. {price}")
else:
    st.warning(f"File '{category.lower()}.csv' not found on GitHub.")

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
    st.info("Note: Provisional estimate. Actuals may vary. Implants/Pharmacy extra.")

with st.sidebar:
    if st.button("🗑️ RESET"):
        st.session_state.bill_items = []
        st.rerun()
