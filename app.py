import streamlit as st
import pandas as pd
from datetime import datetime
import pytz
import plotly.express as px

# 1. Konfigurasi Tampilan Dashboard
st.set_page_config(page_title="Dashboard Transaksi Withdraw Minerapay", layout="wide")

# --- CUSTOM CSS UNTUK TAMPILAN ---
st.markdown("""
    <style>
    /* Mengubah warna tombol 'Browse files' menjadi Hijau */
    div[data-testid="stFileUploader"] section button {
        background-color: #28a745 !important;
        color: white !important;
        border-radius: 5px;
        border: none;
    }
    /* Efek hover tombol */
    div[data-testid="stFileUploader"] section button:hover {
        background-color: #218838 !important;
        box-shadow: 0 4px 8px rgba(0,0,0,0.2);
    }
    /* Style Kotak Jam & Tanggal Biru Modern */
    .time-container {
        background: linear-gradient(135deg, #0054A6 0%, #002D5A 100%);
        color: white;
        padding: 20px;
        border-radius: 15px;
        text-align: center;
        font-family: 'Segoe UI', Tahoma, Geneva, Verdana, sans-serif;
        box-shadow: 0 4px 15px rgba(0,0,0,0.3);
        border-bottom: 5px solid #E1261C;
    }
    </style>
""", unsafe_allow_html=True)

# --- BAGIAN ATAS: LOGO, JUDUL & JAM (WIB) ---
col_head, col_time = st.columns([2, 1])

with col_head:
    # Logo QRIS Custom Warna
    st.markdown("""
        <div style='text-align: left; font-family: sans-serif; font-weight: 900; font-size: 50px; letter-spacing: -2px; margin-bottom: -10px;'>
            <span style='color: #E1261C;'>Q</span><span style='color: #414042;'>R</span><span style='color: #0054A6;'>IS</span>
        </div>
    """, unsafe_allow_html=True)
    st.title("Dashboard Cek Transaksi Qris Minerapay")
    st.markdown("Silakan upload file Excel hasil export untuk memulai analisis data.")

with col_time:
    # Mengatur Zona Waktu ke Jakarta (WIB)
    tz_jakarta = pytz.timezone('Asia/Jakarta')
    now = datetime.now(tz_jakarta)
    waktu_skrg = now.strftime("%H:%M:%S")
    tgl_skrg = now.strftime("%d %B %Y")
    
    st.markdown(f"""
        <div class="time-container">
            <div style="font-size: 14px; font-weight: 600; letter-spacing: 2px; opacity: 0.9;">WAKTU INDONESIA BARAT</div>
            <div style="font-size: 35px; font-weight: 800; margin: 5px 0;">{waktu_skrg}</div>
            <div style="font-size: 16px; font-weight: 400;">{tgl_skrg}</div>
        </div>
    """, unsafe_allow_html=True)

st.divider()

# 2. Fitur Upload File
uploaded_file = st.file_uploader("Upload File Excel (.xlsx)", type=["xlsx"])

if uploaded_file:
    # Notifikasi Berhasil
    st.success("✅ File berhasil diupload! Memproses data...")
    
    try:
        # Membaca data dari Excel
        df = pd.read_excel(uploaded_file)

        # Daftar kolom yang dibutuhkan
        kolom_utama = [
            'id', 'reference_no', 'amount', 'fee', 'revenue', 
            'status', 'account_number', 'account_holder_name', 'remark'
        ]

        # Filter kolom yang benar-benar ada di file
        df = df[[c for c in kolom_utama if c in df.columns]].copy()
        
        # Memastikan kolom angka terbaca sebagai numerik
        for col in ['amount', 'fee', 'revenue']:
            if col in df.columns:
                df[col] = pd.to_numeric(df[col], errors='coerce').fillna(0)

        # 3. Logika Membersihkan Remark
        if 'remark' in df.columns:
            def proses_remark(val):
                txt = str(val).strip()
                if not txt or txt.lower() == 'nan' or '||' not in txt:
                    return None
                return txt.split('||')[0].strip()

            df['remark_clean'] = df['remark'].apply(proses_remark)
            df = df.dropna(subset=['remark_clean'])
            df = df[df['remark_clean'] != ""]

        # --- BAGIAN FILTER (SIDEBAR) ---
        st.sidebar.header("🔍 Filter Data")
        
        all_status = df['status'].unique().tolist() if 'status' in df.columns else []
        selected_status = st.sidebar.multiselect("Pilih Status", all_status, default=all_status)

        all_remarks = sorted(df['remark_clean'].unique().tolist()) if 'remark_clean' in df.columns else []
        selected_remark = st.sidebar.multiselect("Pilih Remark (Prefix)", all_remarks, default=all_remarks)

        # Eksekusi Filter
        df_filtered = df[
            (df['status'].isin(selected_status)) & 
            (df['remark_clean'].isin(selected_remark))
        ]

        # --- BAGIAN VISUALISASI DASHBOARD (METRICS) ---
        col1, col2, col3, col4 = st.columns(4)
        with col1:
            st.metric("Total Transaksi", f"{len(df_filtered)}")
        with col2:
            st.metric("Total Amount", f"Rp {df_filtered['amount'].sum():,.0f}")
        with col3:
            st.metric("Total Fee", f"Rp {df_filtered['fee'].sum():,.0f}")
        with col4:
            st.metric("Total Revenue", f"Rp {df_filtered['revenue'].sum():,.0f}")

        st.divider()

        # --- BAGIAN DIAGRAM KEREN (PLOTLY) ---
        st.subheader("📊 Analisis Visual Transaksi")
        c1, c2 = st.columns(2)

        with c1:
            # Diagram Donut Status
            if not df_filtered.empty:
                fig_status = px.pie(df_filtered, names='status', hole=0.5, 
                                   title="<b>Proporsi Status Transaksi</b>",
                                   color_discrete_sequence=px.colors.qualitative.Set3)
                fig_status.update_layout(margin=dict(t=50, b=20, l=20, r=20))
                st.plotly_chart(fig_status, use_container_width=True)
            else:
                st.warning("Data tidak tersedia untuk diagram status.")

        with c2:
            # Diagram Batang Revenue per Remark
            if not df_filtered.empty:
                rev_per_remark = df_filtered.groupby('remark_clean')['revenue'].sum().reset_index()
                fig_rev = px.bar(rev_per_remark, x='remark_clean', y='revenue', 
                                title="<b>Revenue berdasarkan Merchant/Remark</b>",
                                color='revenue',
                                text_auto='.2s',
                                color_continuous_scale='GnBu')
                fig_rev.update_layout(xaxis_title="Remark", yaxis_title="Total Revenue (Rp)")
                st.plotly_chart(fig_rev, use_container_width=True)
            else:
                st.warning("Data tidak tersedia untuk diagram revenue.")

        st.divider()

        # --- TABEL DATA LENGKAP ---
        st.subheader("📋 Detail Data Terfilter")
        
        kolom_tampilan = [
            'id', 'reference_no', 'amount', 'fee', 'revenue', 
            'status', 'account_number', 'account_holder_name', 'remark_clean'
        ]
        
        final_cols = [c for c in kolom_tampilan if c in df_filtered.columns]
        
        st.dataframe(
            df_filtered[final_cols], 
            use_container_width=True, 
            hide_index=True
        )

        # Tombol Download
        csv = df_filtered.to_csv(index=False).encode('utf-8')
        st.download_button(
            label="📥 Download Data Hasil Filter (CSV)", 
            data=csv, 
            file_name='hasil_filter_dashboard.csv', 
            mime='text/csv'
        )

    except Exception as e:
        st.error(f"Terjadi kesalahan saat memproses data: {e}")
else:
    st.info("💡 Menunggu file diupload untuk menampilkan dashboard...")
