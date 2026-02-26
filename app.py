import streamlit as st
import pandas as pd
from datetime import datetime

# --- PAGE CONFIG ---
st.set_page_config(page_title="GEIMS Billing Tool", layout="wide", page_icon="🏥")

# --- DATA LOADING WITH DUPLICATE COLUMN FIX ---
@st.cache_data(ttl=60)
def load_geims_data():
    try:
        # Load raw data
        df_raw = pd.read_csv("database.csv", encoding='latin1', header=None)
        
        # Identify the header row (usually Row 1)
        header_idx = 1
        headers = [str(h).strip().replace('\n', ' ') for h in df_raw.iloc[header_idx]]
        
        # FIX: Make duplicate column names unique
        unique_headers = []
        counts = {}
        for h in headers:
            if h in counts:
                counts[h] += 1
                unique_headers.append(f"{h}_{counts[h]}")
            else:
                counts[h] = 0
                unique_headers.append(h)
        
        df_raw.columns = unique_headers
        df = df_raw.iloc[header_idx + 1:].reset_index(drop=True)
        
        # Map Service Name column
        if 'Item Name' in df.columns:
            df = df.rename(columns={'Item Name': 'Service Name'})
        
        # Clean up text to ensure search works
        df['Service Name'] = df['Service Name'].astype(str).str.strip()
        return df
    except Exception as e:
        st.error(f"Database Error: {e}")
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

    # --- SEARCH ENGINE (SEARCHES ALL COLUMNS) ---
    st.markdown("#### SEARCH TARIFF (Type 'CAG', 'Angiography', or 'Package')")
    search_query = st.text_input("Search Item:")

    if search_query:
        # Search across all columns for maximum coverage
        mask = df_master.apply(lambda row: row.astype(str).str.contains(search_query, case=False).any(), axis=1)
        filtered_df = df_master[mask]
        
        if not filtered_df.empty:
            # Display found items in a dropdown
            sel_proc = st.selectbox("Select exact item:", filtered_df['Service Name'].unique())
            
            if st.button("➕ ADD ITEM"):
                row = filtered_df[filtered_df['Service Name'] == sel_proc].iloc[0]
                
                # Dynamic price detection
                try:
                    # Find column containing room category name (e.g., 'Economy')
                    price_col = [c for c in df_master.columns if room_cat.lower() in str(c).lower()][0]
                    price = float(str(row[price_col]).replace(',', '').replace('₹', '').strip())
                except:
                    price = 0.0
                
                is_pkg = "PKG" in str(sel_proc).upper() or "PACKAGE" in str(sel_proc).upper()
                st.session_state.bill_items.append({"name": sel_proc, "price": price, "is_pkg": is_pkg})
                st.success(f"Added: {sel_proc}")
        else:
            st.error("Item not found. Please try a different keyword.")

    # --- THE ESTIMATE TABLE ---
    if st.session_state.bill_items:
        st.markdown("---")
        bill_data = []
        for i, item in enumerate(st.session_state.bill_items):
            bill_data.append({"S.NO": i+1, "PARTICULARS": item['name'], "AMOUNT (Rs.)": item['price']})
        
        # Admission Fee
        bill_data.append({"S.NO": len(bill_data)+1, "PARTICULARS": "ADMISSION / MRD CHARGES", "AMOUNT (Rs.)": 450.0})
        
        st.table(pd.DataFrame(bill_data))
        
        total = sum([item['AMOUNT (Rs.)'] for item in bill_data])
        st.markdown(f"<h3 style='text-align: right;'>TOTAL: Rs. {total:,.2f}</h3>", unsafe_allow_html=True)
        
        # FOOTER NOTES
        st.info("Note: Provisional estimate. Implants/Pharmacy extra.")
        st.button("🖨️ PRINT (Ctrl+P)")

    with st.sidebar:
        if st.button("🗑️ RESET"):
            st.session_state.bill_items = []
            st.rerun()
