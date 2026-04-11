import streamlit as st
import pandas as pd
from datetime import datetime
import plotly.express as px

# 1. Konfigurasi Tampilan Dashboard
st.set_page_config(page_title="Dashboard Transaksi Minerapay & Orion", layout="wide")

# --- CUSTOM CSS ---
st.markdown("""
    <style>
    /* Mengubah warna tombol 'Browse files' menjadi Hijau */
    div[data-testid="stFileUploader"] section button {
        background-color: #28a745 !important;
        color: white !important;
        border-radius: 5px;
        border: none;
    }
    /* Efek hover saat mouse di atas tombol */
    div[data-testid="stFileUploader"] section button:hover {
        background-color: #218838 !important;
        box-shadow: 0 4px 8px rgba(0,0,0,0.2);
    }
    /* Style Kotak Jam & Tanggal Biru */
    .time-container {
        background-color: #0054A6;
        color: white;
        padding: 15px;
        border-radius: 10px;
        text-align: center;
        font-family: 'Courier New', Courier, monospace;
        margin-bottom: 20px;
        border-left: 10px solid #002D5A;
    }
    </style>
""", unsafe_allow_html=True)

# --- BAGIAN ATAS: HEADER & JAM ---
col_head, col_time = st.columns([2, 1])

with col_head:
    st.markdown("""
        <div style='text-align: left; font-family: sans-serif; font-weight: 900; font-size: 50px; letter-spacing: -2px; margin-bottom: -10px;'>
            <span style='color: #E1261C;'>Q</span><span style='color: #414042;'>R</span><span style='color: #0054A6;'>IS</span>
        </div>
    """, unsafe_allow_html=True)
    st.title("Dashboard Cek Transaksi Qris Minerapay & Orion")

with col_time:
    now = datetime.now()
    waktu_skrg = now.strftime("%H:%M:%S")
    tgl_skrg = now.strftime("%d %B %Y")
    st.markdown(f"""
        <div class="time-container">
            <div style="font-size: 14px; opacity: 0.8;">WAKTU SISTEM</div>
            <div style="font-size: 28px; font-weight: bold;">{waktu_skrg}</div>
            <div style="font-size: 16px;">{tgl_skrg}</div>
        </div>
    """, unsafe_allow_html=True)

st.markdown("Silakan upload file Excel hasil export untuk memulai.")

# 2. Fitur Upload File
uploaded_file = st.file_uploader("Upload File Excel (.xlsx)", type=["xlsx"])

if uploaded_file:
    st.markdown("<h3 style='color: #28a745; text-align: left;'>✅ FILE BERHASIL DIUPLOAD</h3>", unsafe_allow_html=True)
    
    try:
        # Membaca data dari Excel
        df = pd.read_excel(uploaded_file)

        # Daftar kolom yang dibutuhkan
        kolom_utama = [
            'id', 'reference_no', 'amount', 'fee', 'revenue', 
            'status', 'account_number', 'account_holder_name', 'remark'
        ]

        # Memastikan hanya mengambil kolom yang ada di file
        df = df[[c for c in kolom_utama if c in df.columns]].copy()
        
        # Konversi kolom numerik
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

        # --- BAGIAN DIAGRAM (NEW) ---
        st.subheader("📊 Analisis Visual")
        c1, c2 = st.columns(2)

        with c1:
            # Diagram Donut Status
            if not df_filtered.empty:
                fig_status = px.pie(df_filtered, names='status', hole=0.4, 
                                   title="Distribusi Status Transaksi",
                                   color_discrete_sequence=px.colors.qualitative.Pastel)
                fig_status.update_layout(margin=dict(t=40, b=0, l=0, r=0))
                st.plotly_chart(fig_status, use_container_width=True)

        with c2:
            # Diagram Batang Revenue per Remark
            if not df_filtered.empty:
                rev_per_remark = df_filtered.groupby('remark_clean')['revenue'].sum().reset_index()
                fig_rev = px.bar(rev_per_remark, x='remark_clean', y='revenue', 
                                title="Total Revenue per Remark",
                                color='revenue',
                                color_continuous_scale='Viridis')
                fig_rev.update_layout(margin=dict(t=40, b=0, l=0, r=0))
                st.plotly_chart(fig_rev, use_container_width=True)

        st.divider()

        # Row 2: Tabel Data Lengkap
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
        st.download_button(label="📥 Download Data Hasil Filter (CSV)", data=csv, file_name='hasil_filter_dashboard.csv', mime='text/csv')

    except Exception as e:
        st.error(f"Terjadi kesalahan saat memproses data: {e}")
else:
    st.info("💡 Menunggu file diupload...")
