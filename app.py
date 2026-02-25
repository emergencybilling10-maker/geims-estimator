import streamlit as st
import pandas as pd
import pdfplumber

# --- PAGE CONFIG ---
st.set_page_config(page_title="GEIMS Official Billing Tool", layout="wide", page_icon="🏥")

# --- PDF DATA EXTRACTION ---
@st.cache_data(ttl=600)
def load_data_from_pdf(file_path):
    all_rows = []
    try:
        with pdfplumber.open(file_path) as pdf:
            for page in pdf.pages:
                table = page.extract_table()
                if table:
                    # Converting PDF tables into a usable database
                    df_temp = pd.DataFrame(table[1:], columns=table[0])
                    all_rows.append(df_temp)
        
        final_df = pd.concat(all_rows, ignore_index=True)
        # Cleaning headers for match accuracy
        final_df.columns = [str(c).strip().replace('\n', ' ') for c in final_df.columns]
        return final_df
    except Exception as e:
        st.error(f"Error reading PDF: {e}")
        return None

# --- GEIMS 2025 POLICY RULES ---
# These daily rates apply ONLY for extra days beyond the package
ROOM_POLICY = {
    "Economy": {"Rent": 2500, "Consult": 700, "Nursing": 500, "Diet": 100, "RMO": 700},
    "Double": {"Rent": 4500, "Consult": 900, "Nursing": 600, "Diet": 100, "RMO": 800},
    "Single/ ICU": {"Rent": 7500, "Consult": 1200, "Nursing": 600, "Diet": 100, "RMO": 800},
    "Classic Deluxe": {"Rent": 10000, "Consult": 1500, "Nursing": 600, "Diet": 100, "RMO": 800},
    "Suite": {"Rent": 33000, "Consult": 2000, "Nursing": 2800, "Diet": 100, "RMO": 3000},
}

st.title("🏥 GEIMS Hospital Official Billing Estimator")
st.subheader("Automated Data Sync: Graphic Era Institute of Medical Sciences")

# Synchronizing with your uploaded files
df_master = load_data_from_pdf("Geims_Tariff_Dec_2025.pdf")

if df_master is not None:
    with st.sidebar:
        st.header("Patient Setup")
        pat_name = st.text_input("Patient Name", value="Anuj Gill") #
        room_cat = st.selectbox("Selected Bed Category", list(ROOM_POLICY.keys()))
        total_stay = st.number_input("Total Days of Stay", min_value=1, value=1)
        st.divider()
        st.info("System identifies Packages: Inclusive of Room, Diet, and Nursing for Pkg Days.")

    try:
        # Finding the right columns in the PDF
        dept_col = [c for c in df_master.columns if 'dept' in c.lower()][0]
        serv_col = [c for c in df_master.columns if 'service' in c.lower() or 'procedure' in c.lower()][0]
        
        col1, col2 = st.columns(2)
        with col1:
            sel_dept = st.selectbox("Search Department", sorted(df_master[dept_col].dropna().unique()))
        with col2:
            procs = sorted(df_master[df_master[dept_col] == sel_dept][serv_col].unique())
            sel_proc = st.selectbox("Select Surgery / Investigation", procs)

        # Calculation Logic
        row = df_master[df_master[serv_col] == sel_proc]
        
        # Clean price string and convert to float
        price_str = str(row[room_cat].values[0]).replace(',', '').replace('₹', '').strip()
        base_rate = float(price_str) if price_str.replace('.','').isdigit() else 0.0
        
        # Determine Package Days from PDF or default to 1
        pkg_day_col = [c for c in df_master.columns if 'day' in c.lower() and ('pkg' in c.lower() or 'package' in c.lower())]
        pkg_days = int(row[pkg_day_col[0]].values[0]) if pkg_day_col else 1
        
        extra_days = max(0, total_stay - pkg_days)
        r = ROOM_POLICY[room_cat]

        # Official GEIMS Breakdown
        breakdown = {
            f"Base Rate ({sel_proc})": base_rate,
            "Package Inclusions": f"Covers Room, Nursing, RMO & Diet for {pkg_days} days",
            "Admission / MRD Fee": 450.0 #
        }

        if extra_days > 0:
            breakdown[f"Extra Room & Nursing ({extra_days} days)"] = float((r['Rent'] + r['Nursing'] + r['RMO']) * extra_days)
            breakdown[f"Extra Consultation (2 visits/day)"] = float((r['Consult'] * 2) * extra_days)
            breakdown[f"Extra Diet Charges"] = float(r['Diet'] * extra_days)

        st.markdown("---")
        st.subheader(f"Formal Estimate Summary: {pat_name}")
        st.table(pd.DataFrame(list(breakdown.items()), columns=["Description", "Amount (₹)"]))
        
        total_val = sum([v for v in breakdown.values() if isinstance(v, (float, int))])
        st.metric("Estimated Grand Total", f"₹ {total_val:,.2f}")
        st.caption("Policy Note: Pharmacy, Consumables, and Implants extra as per actuals.")

    except Exception as e:
        st.warning("Please check your PDF structure or selection. Ensure columns 'Department' and 'Service Name' exist.")
else:
    st.error("System could not find 'Geims_Tariff_Dec_2025.pdf'. Please ensure the filename is exact on GitHub.")
