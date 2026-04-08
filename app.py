import streamlit as st
import pandas as pd

# 1. Konfigurasi Tampilan Dashboard
st.set_page_config(page_title="Dashboard Transaksi Excel", layout="wide")

st.title("📊 Dashboard Analisis Transaksi")
st.markdown("Silakan upload file Excel hasil export untuk memulai.")

# 2. Fitur Upload File
uploaded_file = st.file_uploader("Upload File Excel (.xlsx)", type=["xlsx"])

if uploaded_file:
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

        # 3. Logika Membersihkan Remark & Filter Baris Kosong
        if 'remark' in df.columns:
            # Bersihkan data awal
            df['remark'] = df['remark'].astype(str).str.strip()
            
            # Ambil bagian sebelum || saja
            df['remark_clean'] = df['remark'].apply(
                lambda x: x.split('||')[0].strip() if '||' in x and x.lower() != 'nan' and x != '' else None
            )

            # Buang baris yang remark_clean nya kosong (Data tidak valid)
            df = df.dropna(subset=['remark_clean'])
            df = df[df['remark_clean'] != ""]

        # --- BAGIAN FILTER (SIDEBAR) ---
        st.sidebar.header("🔍 Filter Data")
        
        # Filter Status
        all_status = df['status'].unique().tolist() if 'status' in df.columns else []
        selected_status = st.sidebar.multiselect("Pilih Status", all_status, default=all_status)

        # Filter Remark (Hasil yang sudah dipotong dan dibersihkan)
        all_remarks = sorted(df['remark_clean'].unique().tolist()) if 'remark_clean' in df.columns else []
        selected_remark = st.sidebar.multiselect("Pilih Remark (Prefix)", all_remarks, default=all_remarks)

        # Menjalankan filter pada data
        df_filtered = df[
            (df['status'].isin(selected_status)) & 
            (df['remark_clean'].isin(selected_remark))
        ]

        # --- BAGIAN VISUALISASI DASHBOARD ---
        col1, col2, col3, col4 = st.columns(4)
        with col1:
            st.metric("Total Transaksi", f"{len(df_filtered)}")
        with col2:
            total_amt = df_filtered['amount'].sum() if 'amount' in df_filtered.columns else 0
            st.metric("Total Amount", f"Rp {total_amt:,.0f}")
        with col3:
            total_fee = df_filtered['fee'].sum() if 'fee' in df_filtered.columns else 0
            st.metric("Total Fee", f"Rp {total_fee:,.0f}")
        with col4:
            total_rev = df_filtered['revenue'].sum() if 'revenue' in df_filtered.columns else 0
            st.metric("Total Revenue", f"Rp {total_rev:,.0f}")

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
        st.error(f"Error: {e}")
else:
    st.info("💡 Menunggu file diupload...")