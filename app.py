import streamlit as st
import pandas as pd

# --- CONFIG ---
st.set_page_config(page_title="GEIMS Estimate Tool", layout="wide", page_icon="🏥")

# --- THE LINK ---
GOOGLE_SHEET_CSV_URL = "https://docs.google.com/spreadsheets/d/e/2PACX-1vQG6vTU99xSFQEnORPp-5Mhp4hZ-fMIT_yb-daMsmff8t-K-1ggynkxHZi1UsbYE7o9bfo08ybKbd0X/pub?output=csv"

@st.cache_data(ttl=60)
def load_and_clean_data(url):
    try:
        # Load data (trying without skipping rows first)
        df = pd.read_csv(url)
        
        # CLEANING: If 'Department' isn't a header, find it in the first 5 rows
        if 'Department' not in df.columns:
            for i in range(1, 6):
                temp_df = pd.read_csv(url, skiprows=i)
                temp_df.columns = [str(c).strip().replace('\n', ' ') for c in temp_df.columns]
                if 'Department' in temp_df.columns:
                    df = temp_df
                    break
        else:
            df.columns = [str(c).strip().replace('\n', ' ') for c in df.columns]

        # Final Cleaning: Remove empty rows and columns
        df = df.dropna(axis=0, how='all').dropna(axis=1, how='all')
        return df
    except Exception as e:
        st.error(f"⚠️ Connection Error: {e}")
        return None

df_surgery = load_and_clean_data(GOOGLE_SHEET_CSV_URL)

# GEIMS 2025 Fixed Room Rates
ROOM_DATA = {
    "Economy": {"Rent": 2500, "Consult": 700, "Nursing": 500, "RMO": 700},
    "Double": {"Rent": 4500, "Consult": 900, "Nursing": 600, "RMO": 800},
    "Single/ ICU": {"Rent": 7500, "Consult": 1200, "Nursing": 600, "RMO": 800},
    "Classic Deluxe": {"Rent": 10000, "Consult": 1500, "Nursing": 600, "RMO": 800},
    "Suite": {"Rent": 33000, "Consult": 2000, "Nursing": 2800, "RMO": 3000},
}

st.title("🏥 GEIMS Hospital Estimate Generator")

if df_surgery is not None:
    # --- DEBUG SECTION (Visible only if error exists) ---
    if 'Department' not in df_surgery.columns:
        st.error("❌ 'Department' column not detected.")
        st.write("Headers found in your sheet:", list(df_surgery.columns))
        st.write("Preview of first 3 rows:")
        st.dataframe(df_surgery.head(3))
        st.stop()
    
    # --- UI ---
    with st.sidebar:
        st.header("Patient Setup")
        pat_name = st.text_input("Patient Name", "Anuj Gill")
        room_cat = st.selectbox("Bed Category", list(ROOM_DATA.keys()))
        stay_days = st.number_input("Days of Stay", min_value=1, value=1)

    # Search Logic
    depts = sorted(df_surgery['Department'].dropna().unique())
    sel_dept = st.selectbox("Search Department", depts)
    
    # Filter by Service Name
    services = df_surgery[df_surgery['Department'] == sel_dept]['Service Name'].dropna().unique()
    sel_proc = st.selectbox("Select Procedure", services)

    # Billing Calculation
    try:
        # Match Room Category to CSV column
        # Note: If category name is slightly different in CSV, we find it
        col_to_use = room_cat
        if room_cat not in df_surgery.columns:
            # Fallback to similar name
            for col in df_surgery.columns:
                if room_cat.lower() in col.lower():
                    col_to_use = col
                    break
        
        surgery_fee = df_surgery[df_surgery['Service Name'] == sel_proc][col_to_use].values[0]
        r = ROOM_DATA[room_cat]
        
        breakdown = {
            f"Surgery: {sel_proc}": float(surgery_fee),
            "Room Rent": r['Rent'] * stay_days,
            "Consultation (2/day)": (r['Consult'] * 2) * stay_days,
            "Nursing & RMO": (r['Nursing'] + r['RMO']) * stay_days,
            "MRD Fee (One-time)": 450.0,
            "Diet Charges": 100.0 * stay_days
        }
        
        st.subheader(f"Estimate for: {pat_name}")
        st.table(pd.DataFrame(list(breakdown.items()), columns=["Description", "Amount (₹)"]))
        st.metric("Total Estimate", f"₹ {sum(breakdown.values()):,.2f}")
    except:
        st.warning("Rate not found for this selection. Check sheet data.")

else:
    st.info("🔄 Connecting to GEIMS Google Sheet...")
