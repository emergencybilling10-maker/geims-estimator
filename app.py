import streamlit as st
import pandas as pd
import os
from datetime import datetime

# --- PAGE CONFIG ---
st.set_page_config(page_title="GEIMS HIS-Estimate Tool", layout="wide", page_icon="🏥")

# --- HIS-GRADE DATA LOADER ---
@st.cache_data(ttl=60)
def load_his_database():
    if not os.path.exists("database.csv"):
        return None
    try:
        # Load everything as strings to prevent "NaN" or "Empty" row crashes
        df = pd.read_csv("database.csv", encoding='latin1', header=None).astype(str)
        
        # CLEANING: Remove rows that are just empty headers from the PDF conversion
        df = df[df.apply(lambda x: len(''.join(x)) > 10, axis=1)]
        
        return df
    except Exception as e:
        st.error(f"System Error: {e}")
        return None

# --- GEIMS POLICY ---
ROOM_POLICY = {
    "Economy": {"Rent": 2500, "Consult": 700, "Nursing": 500, "Diet": 100, "RMO": 700},
    "Double": {"Rent": 4500, "Consult": 900, "Nursing": 600, "Diet": 100, "RMO": 800},
    "Single/ ICU": {"Rent": 7500, "Consult": 1200, "Nursing": 600, "Diet": 100, "RMO": 800},
    "Classic Deluxe": {"Rent": 10000, "Consult": 1500, "Nursing": 600, "Diet": 100, "RMO": 800},
    "Suite": {"Rent": 33000, "Consult": 2000, "Nursing": 2800, "Diet": 100, "RMO": 3000},
}

if 'bill_items' not in st.session_state:
    st.session_state.bill_items = []

# --- H.I.S. INTERFACE HEADER ---
st.markdown("<h1 style='text-align: center; color: #cc0000;'>GEIMS HOSPITAL INFORMATION SYSTEM</h1>", unsafe_allow_html=True)
st.markdown("<p style='text-align: center;'><b>Provisional Estimate & Billing Module | 2026</b></p>", unsafe_allow_html=True)

df_master = load_his_database()

if df_master is not None:
    # --- PATIENT REGISTRATION ---
    with st.expander("📝 Patient Registration Details", expanded=True):
        col1, col2, col3 = st.columns(3)
        with col1:
            pat_name = st.text_input("Patient Name", value="Anuj Gill")
            uhid = st.text_input("UHID / Reg No.", value="NEW")
        with col2:
            room_cat = st.selectbox("Bed Category Selection", list(ROOM_POLICY.keys()))
            stay_days = st.number_input("Expected Days of Stay", min_value=1, value=1)
        with col3:
            st.write(f"**Date:** {datetime.now().strftime('%d-%m-%Y')}")
            st.write(f"**Location:** Dehradun Unit")

    st.divider()

    # --- H.I.S. SEARCH BAR ---
    st.subheader("🔍 Master Tariff Search")
    search_query = st.text_input("Search for Package, Surgery, or Investigation (e.g. 'CAG', 'MRI', 'Blood')")

    if search_query:
        # SEARCH EVERYWHERE: This scans all 5000+ cells for your word
        mask = df_master.apply(lambda row: row.str.contains(search_query, case=False).any(), axis=1)
        results = df_master[mask]
        
        if not results.empty:
            # We show you exactly what was found so you can pick the right one
            # Column 1 is usually the name, Column 3 is usually Economy price
            st.write("### Matching Items Found:")
            for i in range(len(results)):
                row = results.iloc[i]
                item_name = row.iloc[1] # Item Name
                item_price = row.iloc[3] # Economy Rate
                
                c1, c2 = st.columns([4, 1])
                with c1:
                    st.write(f"**{item_name}**")
                with c2:
                    if st.button(f"Add Rs. {item_price}", key=f"btn_{i}"):
                        price_clean = str(item_price).replace(',', '').replace('₹', '').strip()
                        st.session_state.bill_items.append({
                            "name": item_name,
                            "price": float(price_clean) if price_clean.replace('.','').isdigit() else 0.0
                        })
                        st.success(f"Added to Estimate")
        else:
            st.error("No matches found in the Master Tariff.")

    # --- FINAL BILL GENERATION ---
    if st.session_state.bill_items:
        st.markdown("---")
        st.subheader("PROVISIONAL ESTIMATE SUMMARY")
        
        bill_df = pd.DataFrame(st.session_state.bill_items)
        bill_df.index += 1
        st.table(bill_df.rename(columns={"name": "Service Particulars", "price": "Amount (Rs.)"}))
        
        # GEIMS Fixed Fees
        subtotal = sum([x['price'] for x in st.session_state.bill_items])
        mrd_fee = 450.0
        
        st.markdown(f"**Admission / MRD Fee:** Rs. {mrd_fee}")
        st.markdown(f"## **GRAND TOTAL: Rs. {subtotal + mrd_fee:,.2f}**")
        
        # FOOTER NOTES
        st.info("Note: This is a provisional estimate. Actual billing may vary based on clinical condition.")
        
        if st.button("🗑️ Reset Tool"):
            st.session_state.bill_items = []
            st.rerun()
else:
    st.warning("⚠️ Database connection lost. Ensure 'database.csv' is in the main folder.")
