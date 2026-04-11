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
    /* Styling Tombol Upload */
    div[data-testid="stFileUploader"] section button {
        background-color: #28a745 !important;
        color: white !important;
        border-radius: 5px;
        border: none;
    }
    /* Kotak Jam Biru */
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
    /* Styling Kontainer Filter di Dashboard */
    .filter-box {
        background-color: #f8f9fa;
        padding: 20px;
        border-radius: 10px;
        border: 1px solid #dee2e6;
        margin-bottom: 25px;
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

# 2. Fitur Upload File
uploaded_file = st.file_uploader("Upload File Excel (.xlsx)", type=["xlsx"])

if uploaded_file:
    try:
        # Load Data
        df = pd.read_excel(uploaded_file)
        
        # Bersihkan Remark (Prefix sebelum ||)
        if 'remark' in df.columns:
            df['remark_clean'] = df['remark'].apply(lambda x: str(x).split('||')[0].strip() if '||' in str(x) else None)
            df = df.dropna(subset=['remark_clean'])

        # ---------------------------------------------------------
        # 3. PANEL KONTROL (MUNCUL DI DASHBOARD)
        # ---------------------------------------------------------
        st.markdown("### 🛠️ Panel Kontrol & Filter")
        
        # Baris Pertama: Pencarian & Filter Utama
        row1_col1, row1_col2, row1_col3 = st.columns([1.5, 1, 1])
        
        with row1_col1:
            search_ref = st.text_input("🔍 Cari No. Referensi", placeholder="Ketik nomor referensi untuk mencari spesifik...")
            
        with row1_col2:
            all_status = df['status'].unique().tolist() if 'status' in df.columns else []
            selected_status = st.multiselect("Filter Status", all_status, default=all_status)
            
        with row1_col3:
            all_remarks = sorted(df['remark_clean'].unique().tolist()) if 'remark_clean' in df.columns else []
            selected_remark = st.multiselect("Filter Remark", all_remarks, default=all_remarks)

        # Baris Kedua: Pengaturan Visual (Menggunakan Expander agar rapi)
        with st.expander("🎨 Pengaturan Warna & Tema Diagram"):
            v_col1, v_col2, v_col3, v_col4 = st.columns(4)
            with v_col1:
                col_success = st.color_picker("Warna SUCCESS", "#28a745")
            with v_col2:
                col_pending = st.color_picker("Warna PENDING", "#ffc107")
            with v_col3:
                col_failed  = st.color_picker("Warna EXPIRED", "#dc3545")
            with v_col4:
                theme_revenue = st.selectbox("Tema Gradient", ["Viridis", "Plasma", "Blues", "Turbo", "Magma"])

        # ---------------------------------------------------------
        # 4. LOGIKA FILTERING
        # ---------------------------------------------------------
        mask = (df['status'].isin(selected_status)) & (df['remark_clean'].isin(selected_remark))
        if search_ref:
            mask = mask & (df['reference_no'].astype(str).str.contains(search_ref, case=False, na=False))

        df_filtered = df[mask].copy()

        # Konversi kolom numerik
        for c in ['amount', 'fee', 'revenue']:
            if c in df_filtered.columns:
                df_filtered[c] = pd.to_numeric(df_filtered[c], errors='coerce').fillna(0)

        # ---------------------------------------------------------
        # 5. RINGKASAN METRICS
        # ---------------------------------------------------------
        st.divider()
        m1, m2, m3, m4 = st.columns(4)
        m1.metric("Total Transaksi", f"{len(df_filtered)}")
        m2.metric("Total Amount", f"Rp {df_filtered['amount'].sum():,.0f}")
        m3.metric("Total Fee", f"Rp {df_filtered['fee'].sum():,.0f}")
        m4.metric("Total Revenue", f"Rp {df_filtered['revenue'].sum():,.0f}")

        # ---------------------------------------------------------
        # 6. VISUALISASI DIAGRAM
        # ---------------------------------------------------------
        st.subheader("📊 Analisis Visual")
        viz1, viz2 = st.columns(2)

        with viz1:
            if not df_filtered.empty:
                color_map = {"SUCCESS": col_success, "PENDING": col_pending, "EXPIRED": col_failed, "FAILED": col_failed}
                fig_status = px.pie(df_filtered, names='status', hole=0.5, title="<b>Distribusi Status Transaksi</b>",
                                   color='status', color_discrete_map=color_map)
                st.plotly_chart(fig_status, use_container_width=True)
            else:
                st.warning("Data tidak ditemukan untuk filter ini.")

        with viz2:
            if not df_filtered.empty:
                rev_data = df_filtered.groupby('remark_clean')['revenue'].sum().reset_index()
                fig_rev = px.bar(rev_data, x='remark_clean', y='revenue', title="<b>Total Revenue per Merchant/Remark</b>",
                                color='revenue', color_continuous_scale=theme_revenue)
                st.plotly_chart(fig_rev, use_container_width=True)

        # ---------------------------------------------------------
        # 7. TABEL DETAIL & DOWNLOAD
        # ---------------------------------------------------------
        st.divider()
        st.subheader("📋 Detail Data Terfilter")
        st.dataframe(df_filtered, use_container_width=True, hide_index=True)

        csv = df_filtered.to_csv(index=False).encode('utf-8')
        st.download_button("📥 Download Hasil Filter (CSV)", csv, "data_transaksi_filtered.csv", "text/csv")

    except Exception as e:
        st.error(f"Terjadi kesalahan sistem: {e}")
else:
    # Tampilan saat awal buka (sebelum upload)
    st.info("👋 Selamat Datang! Silakan unggah file Excel hasil export transaksi untuk melihat dashboard interaktif.")
    st.image("https://img.freepik.com/free-vector/data-report-concept-illustration_114360-883.jpg", width=400)
