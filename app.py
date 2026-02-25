import streamlit as st
import pandas as pd
from reportlab.lib.pagesizes import A4
from reportlab.pdfgen import canvas
from io import BytesIO

# --- PAGE CONFIG ---
st.set_page_config(page_title="GEIMS Estimate Tool", layout="wide", page_icon="🏥")

# --- LIVE LINK ---
GOOGLE_SHEET_CSV_URL = "https://docs.google.com/spreadsheets/d/e/2PACX-1vQG6vTU99xSFQEnORPp-5Mhp4hZ-fMIT_yb-daMsmff8t-K-1ggynkxHZi1UsbYE7o9bfo08ybKbd0X/pub?output=csv"

@st.cache_data(ttl=60)
def load_live_data(url):
    try:
        # Load raw to find where 'Department' starts
        raw = pd.read_csv(url, header=None)
        header_idx = 0
        for i, row in raw.iterrows():
            if "Department" in row.values:
                header_idx = i
                break
        
        # Load with correct header
        df = pd.read_csv(url, skiprows=header_idx)
        df.columns = [str(c).strip().replace('\n', ' ') for c in df.columns]
        return df.dropna(subset=['Department', 'Service Name'], how='all')
    except Exception as e:
        st.error(f"Waiting for connection: {e}")
        return None

df_surgery = load_live_data(GOOGLE_SHEET_CSV_URL)

# GEIMS 2025 Hardcoded Policy Rates
ROOM_DATA = {
    "Economy": {"Rent": 2500, "Consult": 700, "Nursing": 500, "RMO": 700},
    "Double": {"Rent": 4500, "Consult": 900, "Nursing": 600, "RMO": 800},
    "Single/ ICU": {"Rent": 7500, "Consult": 1200, "Nursing": 600, "RMO": 800},
    "Classic Deluxe": {"Rent": 10000, "Consult": 1500, "Nursing": 600, "RMO": 800},
    "Suite": {"Rent": 33000, "Consult": 2000, "Nursing": 2800, "RMO": 3000},
}

# --- PDF FUNCTION ---
def create_pdf(name, breakdown, total):
    buffer = BytesIO()
    p = canvas.Canvas(buffer, pagesize=A4)
    w, h = A4
    p.setFont("Helvetica-Bold", 16)
    p.drawCentredString(w/2, h-50, "GEIMS HOSPITAL - ESTIMATE")
    p.setFont("Helvetica", 10)
    p.drawCentredString(w/2, h-65, "Dhoolkot, Chakrata Road, Dehradun")
    p.line(50, h-80, w-50, h-80)
    p.drawString(50, h-110, f"Patient Name: {name}")
    p.drawString(50, h-125, f"Date: {pd.Timestamp.now().strftime('%d-%m-%Y')}")
    y = h-160
    p.setFont("Helvetica-Bold", 11)
    p.drawString(50, y, "Description")
    p.drawRightString(w-50, y, "Amount (INR)")
    y -= 20
    p.setFont("Helvetica", 11)
    for k, v in breakdown.items():
        p.drawString(50, y, k)
        p.drawRightString(w-50, y, f"{v:,.2f}")
        y -= 20
    p.line(50, y, w-50, y)
    p.setFont("Helvetica-Bold", 12)
    p.drawString(50, y-25, "TOTAL ESTIMATED COST:")
    p.drawRightString(w-50, y-25, f"Rs. {total:,.2f}")
    p.showPage()
    p.save()
    buffer.seek(0)
    return buffer

# --- MAIN UI ---
st.title("🏥 GEIMS Hospital Estimate Generator")

if df_surgery is not None:
    with st.sidebar:
        st.header("Patient Setup")
        pat_name = st.text_input("Patient Name", "Anuj Gill")
        room_cat = st.selectbox("Bed Category", list(ROOM_DATA.keys()))
        stay_days = st.number_input("Days of Stay", min_value=1, value=1)
        st.divider()
        st.info("Policy: MRD Charge (450) and Diet (100/day) applied.")

    depts = sorted(df_surgery['Department'].dropna().unique())
    sel_dept = st.selectbox("Select Department", depts)
    procs = df_surgery[df_surgery['Department'] == sel_dept]['Service Name'].dropna().unique()
    sel_proc = st.selectbox("Select Surgery", procs)

    try:
        # Match data
        s_fee = df_surgery[df_surgery['Service Name'] == sel_proc][room_cat].values[0]
        r = ROOM_DATA[room_cat]
        
        breakdown = {
            f"Surgery: {sel_proc}": float(s_fee),
            "Room Rent": r['Rent'] * stay_days,
            "Consultation (2/day)": (r['Consult'] * 2) * stay_days,
            "Nursing & RMO": (r['Nursing'] + r['RMO']) * stay_days,
            "MRD Fee": 450.0,
            "Diet Charges": 100.0 * stay_days
        }
        
        st.subheader(f"Summary for {pat_name}")
        st.table(pd.DataFrame(list(breakdown.items()), columns=["Description", "Amount"]))
        total = sum(breakdown.values())
        st.metric("Grand Total", f"₹ {total:,.2f}")

        if st.button("Generate Professional PDF"):
            pdf = create_pdf(pat_name, breakdown, total)
            st.download_button("📥 Download Estimate PDF", pdf, f"GEIMS_{pat_name}.pdf")
            
    except:
        st.warning("Please select a valid procedure to calculate.")
