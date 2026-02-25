import streamlit as st
import pandas as pd

# --- CONFIG ---
st.set_page_config(page_title="GEIMS Estimate Tool", layout="wide", page_icon="🏥")

# --- YOUR LIVE DATA LINK ---
GOOGLE_SHEET_CSV_URL = "https://docs.google.com/spreadsheets/d/e/2PACX-1vQG6vTU99xSFQEnORPp-5Mhp4hZ-fMIT_yb-daMsmff8t-K-1ggynkxHZi1UsbYE7o9bfo08ybKbd0X/pub?output=csv"

@st.cache_data(ttl=60)
def load_live_data(url):
    try:
        # We load the data without skipping rows first to find where the headers are
        df = pd.read_csv(url)
        
        # If 'Department' isn't in the first row, we look for it in the first 5 rows
        if 'Department' not in df.columns:
            for i in range(5):
                temp_df = pd.read_csv(url, skiprows=i)
                if 'Department' in temp_df.columns:
                    df = temp_df
                    break
        
        # Clean column names
        df.columns = [str(c).replace('\n', ' ').strip() for c in df.columns]
        return df
    except Exception as e:
        st.error(f"Connection Error: {e}")
        return None

df_surgery = load_live_data(GOOGLE_SHEET_CSV_URL)

# GEIMS Room Rates (Manual 2024-25)
ROOM_DATA = {
    "Economy": {"Rent": 2500, "Consult": 700, "Nursing": 500, "RMO": 700},
    "Double": {"Rent": 4500, "Consult": 900, "Nursing": 600, "RMO": 800},
    "Single/ ICU": {"Rent": 7500, "Consult": 1200, "Nursing": 600, "RMO": 800},
    "Classic Deluxe": {"Rent": 10000, "Consult": 1500, "Nursing": 600, "RMO": 800},
    "Suite": {"Rent": 33000, "Consult": 2000, "Nursing": 2800, "RMO": 3000},
}

st.title("🏥 GEIMS Hospital Estimate Generator")

if df_surgery is not None:
    # Diagnostic: Let's see if we found the columns
    if 'Department' not in df_surgery.columns:
        st.error("❌ 'Department' column still not detected.")
        st.write("Current Columns found in your sheet:", list(df_surgery.columns))
        st.info("💡 Hint: Make sure the word 'Department' is in the very first row of your Google Sheet tab.")
    else:
        with st.sidebar:
            st.header("Patient Setup")
            pat_name = st.text_input("Patient Name", "Anuj Gill")
            room_cat = st.selectbox("Select Bed Category", list(ROOM_DATA.keys()))
            stay_days = st.number_input("Estimated Days of Stay", min_value=1, value=1)

        # Selection Logic
        dept_list = sorted(df_surgery['Department'].dropna().unique())
        selected_dept = st.selectbox("Search Department", dept_list)
        
        filtered_df = df_surgery[df_surgery['Department'] == selected_dept]
        selected_proc = st.selectbox("Select Surgery/Procedure", filtered_df['Service Name'].dropna().unique())

        # Pricing
        try:
            # Match the room category to the column
            surgery_fee = filtered_df[filtered_df['Service Name'] == selected_proc][room_cat].values[0]
            r = ROOM_DATA[room_cat]
            
            breakdown = {
                f"Surgeon Fee ({selected_proc})": float(surgery_fee),
                "Room Rent": r['Rent'] * stay_days,
                "Consultation (Min. 2 visits/day)": (r['Consult'] * 2) * stay_days,
                "Nursing & RMO": (r['Nursing'] + r['RMO']) * stay_days,
                "MRD Fee": 450.0,
                "Diet Charges": 100.0 * stay_days
            }
            
            st.subheader(f"Detailed Estimate for: {pat_name}")
            st.table(pd.DataFrame(list(breakdown.items()), columns=["Description", "Amount (₹)"]))
            st.metric("Estimated Grand Total", f"₹ {sum(breakdown.values()):,.2f}")
        except:
            st.warning("Please select a procedure to calculate the total.")
