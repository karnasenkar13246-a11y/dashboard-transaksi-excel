import streamlit as st
import pandas as pd
from datetime import datetime
import pytz
import plotly.express as px

# 1. Konfigurasi Tampilan Dashboard
st.set_page_config(page_title="Dashboard Transaksi Withdraw Minerapay", layout="wide")

# --- CUSTOM CSS ---
st.markdown("""
    <style>
    div[data-testid="stFileUploader"] section button {
        background-color: #28a745 !important;
        color: white !important;
        border-radius: 5px;
        border: none;
    }
    div[data-testid="stFileUploader"] section button:hover {
        background-color: #218838 !important;
        box-shadow: 0 4px 8px rgba(0,0,0,0.2);
    }
    .time-container {
        background: linear-gradient(135deg, #0054A6 0%, #002D5A 100%);
        color: white;
        padding: 20px;
        border-radius: 15px;
        text-align: center;
        font-family: 'Segoe UI', sans-serif;
        box-shadow: 0 4px 15px rgba(0,0,0,0.3);
        border-bottom: 5px solid #E1261C;
    }
    </style>
""", unsafe_allow_html=True)

# --- BAGIAN ATAS: LOGO & JAM ---
col_head, col_time = st.columns([2, 1])

with col_head:
    st.markdown("""
        <div style='text-align: left; font-family: sans-serif; font-weight: 900; font-size: 50px; letter-spacing: -2px; margin-bottom: -10px;'>
            <span style='color: #E1261C;'>Q</span><span style='color: #414042;'>R</span><span style='color: #0054A6;'>IS</span>
        </div>
    """, unsafe_allow_html=True)
    st.title("Dashboard Transaksi Withdraw Minerapay")

with col_time:
    tz_jakarta = pytz.timezone('Asia/Jakarta')
    now = datetime.now(tz_jakarta)
    st.markdown(f"""
        <div class="time-container">
            <div style="font-size: 14px; font-weight: 600; letter-spacing: 2px; opacity: 0.9;">WAKTU INDONESIA BARAT</div>
            <div style="font-size: 35px; font-weight: 800; margin: 5px 0;">{now.strftime("%H:%M:%S")}</div>
            <div style="font-size: 16px;">{now.strftime("%d %B %Y")}</div>
        </div>
    """, unsafe_allow_html=True)

st.divider()

# --- SIDEBAR: FILTER & SEARCH ---
st.sidebar.header("🔍 Filter & Pencarian")

# Fitur Pencarian No Referensi
search_ref = st.sidebar.text_input("Cari No. Referensi", placeholder="Ketik nomor referensi...")

st.sidebar.divider()

# Kotak Warna (Setting Visual)
st.sidebar.header("🎨 Visual")
col_success = st.sidebar.color_picker("Warna SUCCESS", "#28a745")
col_pending = st.sidebar.color_picker("Warna PENDING", "#ffc107")
col_failed  = st.sidebar.color_picker("Warna EXPIRED", "#dc3545")
theme_revenue = st.sidebar.selectbox("Tema Gradient", ["Viridis", "Plasma", "Blues", "Turbo"])

# --- PROSES DATA ---
uploaded_file = st.file_uploader("Upload File Excel (.xlsx)", type=["xlsx"])

if uploaded_file:
    try:
        # Load Data
        df = pd.read_excel(uploaded_file)
        
        # 1. Bersihkan Remark (Ambil sebelum ||)
        if 'remark' in df.columns:
            df['remark_clean'] = df['remark'].apply(lambda x: str(x).split('||')[0].strip() if '||' in str(x) else None)
            df = df.dropna(subset=['remark_clean'])

        # 2. Filter Multiselect di Sidebar
        all_status = df['status'].unique().tolist() if 'status' in df.columns else []
        selected_status = st.sidebar.multiselect("Pilih Status", all_status, default=all_status)

        all_remarks = sorted(df['remark_clean'].unique().tolist()) if 'remark_clean' in df.columns else []
        selected_remark = st.sidebar.multiselect("Pilih Remark", all_remarks, default=all_remarks)

        # 3. Logika Filter Gabungan (Status + Remark + Search Ref)
        mask = (df['status'].isin(selected_status)) & (df['remark_clean'].isin(selected_remark))
        
        # Jika kolom pencarian diisi, filter berdasarkan No Referensi
        if search_ref:
            mask = mask & (df['reference_no'].astype(str).str.contains(search_ref, case=False, na=False))

        df_filtered = df[mask].copy()

        # Konversi Angka
        for c in ['amount', 'fee', 'revenue']:
            if c in df_filtered.columns:
                df_filtered[c] = pd.to_numeric(df_filtered[c], errors='coerce').fillna(0)

        # Metrics
        c1, c2, c3, c4 = st.columns(4)
        c1.metric("Total Transaksi", f"{len(df_filtered)}")
        c2.metric("Total Amount", f"Rp {df_filtered['amount'].sum():,.0f}")
        c3.metric("Total Fee", f"Rp {df_filtered['fee'].sum():,.0f}")
        c4.metric("Total Revenue", f"Rp {df_filtered['revenue'].sum():,.0f}")

        st.divider()

        # --- DIAGRAM ---
        st.subheader("📊 Analisis Visual")
        viz1, viz2 = st.columns(2)

        with viz1:
            if not df_filtered.empty:
                color_map = {"SUCCESS": col_success, "PENDING": col_pending, "EXPIRED": col_failed, "FAILED": col_failed}
                fig_status = px.pie(df_filtered, names='status', hole=0.5, title="Distribusi Status",
                                   color='status', color_discrete_map=color_map)
                st.plotly_chart(fig_status, use_container_width=True)
            else:
                st.warning("Data tidak ditemukan untuk kriteria tersebut.")

        with viz2:
            if not df_filtered.empty:
                rev_data = df_filtered.groupby('remark_clean')['revenue'].sum().reset_index()
                fig_rev = px.bar(rev_data, x='remark_clean', y='revenue', title="Revenue per Remark",
                                color='revenue', color_continuous_scale=theme_revenue)
                st.plotly_chart(fig_rev, use_container_width=True)

        st.divider()
        
        # --- TABEL DETAIL ---
        st.subheader("📋 Detail Data Terfilter")
        st.dataframe(df_filtered, use_container_width=True, hide_index=True)

        # Tombol Download
        csv = df_filtered.to_csv(index=False).encode('utf-8')
        st.download_button("📥 Download Hasil Filter (CSV)", csv, "filter_transaksi.csv", "text/csv")

    except Exception as e:
        st.error(f"Terjadi kesalahan: {e}")
else:
    st.info("💡 Silakan upload file excel transaksi Anda.")
