import streamlit as st
import pandas as pd
import plotly.express as px

# 1. Konfigurasi Utama Halaman Dashboard
st.set_page_config(page_title="Dashboard UBSP PIKUL NTT", layout="wide")
st.title("📊 Dashboard Monitoring Live UBSP Yayasan PIKUL")
st.markdown("Analisis data inklusi sosial, gender, dan permodalan sinkron otomatis langsung dari Google Sheets.")

# Fungsi pembersihan teks mata uang (Rp50.000 -> 50000) agar tidak error matematika
def clean_currency(val):
    if pd.isna(val):
        return 0
    if isinstance(val, (int, float)):
        return val
    val_str = str(val).replace('Rp', '').replace('.', '').replace(',', '').strip()
    try:
        return float(val_str) if val_str else 0
    except ValueError:
        return 0

# Fungsi membaca data online dengan batas cache waktu 30 detik
@st.cache_data(ttl=30)
def load_data_online(url):
    xl = pd.ExcelFile(url)
    df_kelompok = pd.read_excel(xl, sheet_name='Kelompok_UBSP')
    df_anggota = pd.read_excel(xl, sheet_name='Anggota_UBSP')
    df_progres = pd.read_excel(xl, sheet_name='Progres_UBSP')
    
    df_kelompok = df_kelompok.dropna(subset=['Nama UBSP'])
    df_kelompok['Desa'] = df_kelompok['Desa'].fillna('Belum Terdata')
    
    kolom_angka = ['Jumlah Anggota', 'Perempuan', 'Laki-Laki', 'Difabel', 'Lansia', 'Kepala Keluarga Perempuan']
    for col in kolom_angka:
        if col in df_kelompok.columns:
            df_kelompok[col] = pd.to_numeric(df_kelompok[col], errors='coerce').fillna(0).astype(int)
            
    kolom_keuangan = ['Simpanan Pokok', 'Simpanan Wajib', 'Modal Tambahan PIKUL', 'Modal Tambahan Usaha', 'Total Estimasi Modal per Nov 2025']
    for col in kolom_keuangan:
        if col in df_kelompok.columns:
            df_kelompok[col] = df_kelompok[col].apply(clean_currency)
            
    return df_kelompok, df_anggota, df_progres

# Tautan Google Sheets Publik Anda
GOOGLE_SHEET_ID = "1aHcQbLKFezNRz8c_1-zCmnP07s_j-D9xhCyFvxDUDzA"
URL_LIVE = f"https://google.com{GOOGLE_SHEET_ID}/export?format=xlsx"

try:
    df_kelompok, df_anggota, df_progres = load_data_online(URL_LIVE)
    
    # Filter Wilayah di Sidebar
    st.sidebar.header("⚙️ Filter Wilayah")
    pilihan_desa = df_kelompok['Desa'].unique().tolist()
    desa_terpilih = st.sidebar.multiselect("Pilih Desa Pendampingan PIKUL:", options=pilihan_desa, default=pilihan_desa)
    
    df_kelompok_filtered = df_kelompok[df_kelompok['Desa'].isin(desa_terpilih)]
    
    st.markdown("---")
    
    # Ringkasan Indikator Utama (Metric Cards)
    col1, col2, col3, col4 = st.columns(4)
    with col1:
        st.metric("Total Kelompok UBSP", len(df_kelompok_filtered))
    with col2:
        st.metric("Total Anggota Dampingan", int(df_kelompok_filtered['Jumlah Anggota'].sum()))
    with col3:
        total_modal = df_kelompok_filtered['Total Estimasi Modal per Nov 2025'].sum()
        st.metric("Total Estimasi Modal", f"Rp {total_modal:,.0f}")
    with col4:
        total_difabel = df_kelompok_filtered['Difabel'].sum()
        st.metric("Total Anggota Difabel", int(total_difabel))
        
    st.markdown("---")
    
    # Visualisasi Grafik Aspek Inklusi & Gender
    st.subheader("👥 Analisis Inklusi Sosial & Perspektif Gender")
    left_chart, right_chart = st.columns(2)
    
    with left_chart:
        total_p = df_kelompok_filtered['Perempuan'].sum()
        total_l = df_kelompok_filtered['Laki-Laki'].sum()
        df_gender = pd.DataFrame({'Gender': ['Perempuan', 'Laki-Laki'], 'Jumlah': [total_p, total_l]})
        fig_gender = px.pie(df_gender, values='Jumlah', names='Gender', title="Komposisi Gender Anggota UBSP", hole=0.4)
        st.plotly_chart(fig_gender, use_container_width=True)
        
    with right_chart:
        total_lansia = df_kelompok_filtered['Lansia'].sum()
        total_pekka = df_kelompok_filtered['Kepala Keluarga Perempuan'].sum()
        total_dif = df_kelompok_filtered['Difabel'].sum()
        df_rentan = pd.DataFrame({
            'Kelompok Rentan': ['Lansia', 'PEKKA', 'Difabel'],
            'Jumlah Jiwa': [total_lansia, total_pekka, total_dif]
        })
        fig_rentan = px.bar(df_rentan, x='Kelompok Rentan', y='Jumlah Jiwa', color='Kelompok Rentan', title="Penerima Manfaat Kelompok Rentan")
        st.plotly_chart(fig_rentan, use_container_width=True)
        
    st.markdown("---")
    st.subheader("💰 Ringkasan Data Finansial Kelompok Terfilter")
    st.dataframe(df_kelompok_filtered[['Nama UBSP', 'Desa', 'Kecamatan', 'Jumlah Anggota', 'Total Estimasi Modal per Nov 2025']], use_container_width=True)

except Exception as e:
    st.error(f"Gagal memuat visualisasi live. Error Teknis: {e}")
