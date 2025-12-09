import streamlit as st
import pandas as pd
import os
from datetime import datetime

# ==============================================================================
# 1. KONFIGURASI & GAYA TAMPILAN (CSS)
# ==============================================================================
st.set_page_config(page_title="UMKM Super App", layout="wide", initial_sidebar_state="expanded")

# Custom CSS untuk tampilan yang lebih modern (Tidak Burik)
st.markdown("""
<style>
    /* Mengubah font dan warna background */
    .stApp {
        background-color: #f8f9fa;
    }
    
    /* Style untuk Metric Card */
    div[data-testid="stMetric"] {
        background-color: #ffffff;
        border: 1px solid #e0e0e0;
        padding: 15px;
        border-radius: 10px;
        box-shadow: 0 2px 5px rgba(0,0,0,0.05);
    }
    
    /* Tombol Utama lebih keren */
    .stButton>button {
        border-radius: 20px;
        font-weight: bold;
        transition: all 0.3s;
    }
    
    /* Tabel lebih rapi */
    div[data-testid="stDataFrame"] {
        background-color: white;
        padding: 10px;
        border-radius: 10px;
    }
</style>
""", unsafe_allow_html=True)

# ==============================================================================
# 2. SISTEM DATABASE & STATE
# ==============================================================================
FILE_PRODUK = 'master_produk.csv'
FILE_TRANSAKSI = 'data_transaksi.csv'
FILE_PELANGGAN = 'data_pelanggan.csv'

if 'keranjang' not in st.session_state:
    st.session_state['keranjang'] = []

def load_data(filename, columns):
    if not os.path.exists(filename):
        df = pd.DataFrame(columns=columns)
        df.to_csv(filename, index=False)
    return pd.read_csv(filename)

def save_data(filename, df):
    df.to_csv(filename, index=False)

def format_rupiah(angka):
    return f"Rp {angka:,.0f}"

# ==============================================================================
# 3. SIDEBAR NAVIGASI (URUTAN BARU)
# ==============================================================================
st.sidebar.image("https://cdn-icons-png.flaticon.com/512/3135/3135715.png", width=100)
st.sidebar.title("UMKM Manager")
st.sidebar.write("Sistem Manajemen Toko Digital")
st.sidebar.markdown("---")

# Urutan Navigasi Sesuai Permintaan
menu = st.sidebar.radio("Menu Utama", [
    "👥 Data Pelanggan", 
    "🛒 Kasir (POS)", 
    "📦 Master Produk", 
    "📊 Laporan Transaksi"
])

# ==============================================================================
# MENU 1: DATA PELANGGAN (Ditaruh Pertama)
# ==============================================================================
if menu == "👥 Data Pelanggan":
    st.title("👥 Manajemen Pelanggan")
    st.caption("Kelola data pelanggan untuk strategi CRM dan promosi.")

    col1, col2 = st.columns([1, 2])

    with col1:
        with st.container(border=True):
            st.subheader("➕ Tambah Baru")
            with st.form("form_pelanggan"):
                nama_pel = st.text_input("Nama Lengkap")
                hp_pel = st.text_input("Nomor WhatsApp (Wajib Unik)", placeholder="0812...")
                alamat = st.text_area("Alamat (Opsional)")
                submit = st.form_submit_button("Simpan Data", type="primary")
                
                if submit and hp_pel and nama_pel:
                    df = load_data(FILE_PELANGGAN, ['No HP', 'Nama Pelanggan', 'Alamat', 'Total Belanja'])
                    
                    # Cek duplikasi berdasarkan No HP
                    if str(hp_pel) in df['No HP'].astype(str).values:
                        st.error("Nomor WhatsApp ini sudah terdaftar!")
                    else:
                        new_pel = pd.DataFrame({
                            'No HP': [hp_pel], 
                            'Nama Pelanggan': [nama_pel], 
                            'Alamat': [alamat], 
                            'Total Belanja': [0]
                        })
                        df = pd.concat([df, new_pel], ignore_index=True)
                        save_data(FILE_PELANGGAN, df)
                        st.success("Pelanggan berhasil disimpan!")
                        st.rerun()

    with col2:
        st.subheader("📂 Direktori Pelanggan")
        df_pel = load_data(FILE_PELANGGAN, ['No HP', 'Nama Pelanggan', 'Alamat', 'Total Belanja'])
        
        # Fitur Search Tabel
        search = st.text_input("🔍 Cari Nama / No HP", placeholder="Ketik untuk memfilter...")
        if search:
            mask = df_pel.astype(str).apply(lambda x: x.str.contains(search, case=False)).any(axis=1)
            df_pel = df_pel[mask]
            
        # Tampilkan Data Editor (Bisa diedit dikit)
        st.dataframe(
            df_pel, 
            column_config={
                "Total Belanja": st.column_config.NumberColumn(format="Rp %d")
            },
            use_container_width=True,
            hide_index=True
        )

# ==============================================================================
# MENU 2: KASIR / POS (POINT OF SALE)
# ==============================================================================
elif menu == "🛒 Kasir (POS)":
    st.title("🛒 Kasir Pintar")
    
    # Load Data Terkini
    df_produk = load_data(FILE_PRODUK, ['Nama Produk', 'Kategori', 'HPP (Modal)', 'Harga Jual', 'Stok'])
    df_pelanggan = load_data(FILE_PELANGGAN, ['No HP', 'Nama Pelanggan', 'Alamat', 'Total Belanja'])

    # --- LAYOUT KASIR (Kiri: Input, Kanan: Keranjang) ---
    col_kiri, col_kanan = st.columns([1.5, 1])

    with col_kiri:
        with st.container(border=True):
            st.subheader("1. Informasi Transaksi")
            
            # --- FITUR SEARCH PELANGGAN BY WA ---
            # Kita gabungkan No HP dan Nama jadi satu string biar bisa disearch
            # Format: "0812345 - Budi"
            opsi_pelanggan = ["0 - Umum (Guest)"] + [f"{row['No HP']} - {row['Nama Pelanggan']}" for index, row in df_pelanggan.iterrows()]
            
            pilih_pelanggan_str = st.selectbox(
                "👤 Cari Pelanggan (Ketik No WA)", 
                opsi_pelanggan, 
                help="Ketik nomor HP untuk mencari pelanggan"
            )
            
            # Parsing data pelanggan yang dipilih
            if " - " in pilih_pelanggan_str:
                no_hp_pembeli = pilih_pelanggan_str.split(" - ")[0]
                nama_pembeli = pilih_pelanggan_str.split(" - ")[1]
            else:
                no_hp_pembeli = "0"
                nama_pembeli = "Umum"

            tgl_transaksi = st.date_input("Tanggal", datetime.now())

        with st.container(border=True):
            st.subheader("2. Pilih Produk")
            
            # Filter produk yang stoknya ada
            produk_tersedia = df_produk[df_produk['Stok'] > 0]
            nama_produk_list = ["-- Pilih Produk --"] + produk_tersedia['Nama Produk'].tolist()
            
            pilih_produk = st.selectbox("📦 Cari Nama Produk", nama_produk_list)
            
            # Logic harga otomatis
            c1, c2, c3 = st.columns(3)
            harga_satuan = 0
            stok_tersedia = 0
            
            if pilih_produk != "-- Pilih Produk --":
                item_data = df_produk[df_produk['Nama Produk'] == pilih_produk].iloc[0]
                harga_satuan = int(item_data['Harga Jual'])
                modal_satuan = int(item_data['HPP (Modal)'])
                stok_tersedia = int(item_data['Stok'])
                
            with c1:
                st.metric("Stok Tersedia", f"{stok_tersedia} Pcs")
            with c2:
                st.metric("Harga", format_rupiah(harga_satuan))
            with c3:
                qty = st.number_input("Qty", min_value=1, max_value=stok_tersedia if stok_tersedia > 0 else 1, value=1)

            if st.button("Masuk Keranjang ⬇️", type="secondary", use_container_width=True):
                if pilih_produk != "-- Pilih Produk --":
                    subtotal = harga_satuan * qty
                    st.session_state['keranjang'].append({
                        'Nama Produk': pilih_produk,
                        'Harga': harga_satuan,
                        'Qty': qty,
                        'Subtotal': subtotal,
                        'Modal': modal_satuan * qty
                    })
                    st.success("Item ditambahkan")
                    st.rerun()
                else:
                    st.toast("Pilih produk dulu woi!", icon="⚠️")

    with col_kanan:
        st.subheader("🧾 Ringkasan Pesanan")
        
        if len(st.session_state['keranjang']) > 0:
            df_cart = pd.DataFrame(st.session_state['keranjang'])
            
            # Tampilan Keranjang Bersih
            st.dataframe(
                df_cart[['Nama Produk', 'Qty', 'Subtotal']], 
                hide_index=True, 
                use_container_width=True
            )
            
            total_belanja = df_cart['Subtotal'].sum()
            total_modal = df_cart['Modal'].sum()
            
            st.divider()
            st.markdown(f"<h2 style='text-align: right; color: #2e86de;'>Total: {format_rupiah(total_belanja)}</h2>", unsafe_allow_html=True)
            
            col_bayar_1, col_bayar_2 = st.columns(2)
            with col_bayar_1:
                if st.button("❌ Batal", use_container_width=True):
                    st.session_state['keranjang'] = []
                    st.rerun()
            
            with col_bayar_2:
                if st.button("✅ Bayar & Cetak", type="primary", use_container_width=True):
                    # 1. Simpan Transaksi
                    df_transaksi = load_data(FILE_TRANSAKSI, ['Tanggal', 'No HP', 'Pelanggan', 'Produk', 'Qty', 'Total', 'Laba'])
                    
                    new_logs = []
                    for item in st.session_state['keranjang']:
                        new_logs.append({
                            'Tanggal': tgl_transaksi,
                            'No HP': no_hp_pembeli,
                            'Pelanggan': nama_pembeli,
                            'Produk': item['Nama Produk'],
                            'Qty': item['Qty'],
                            'Total': item['Subtotal'],
                            'Laba': item['Subtotal'] - item['Modal']
                        })
                        
                        # 2. Update Stok
                        idx_prod = df_produk[df_produk['Nama Produk'] == item['Nama Produk']].index[0]
                        df_produk.at[idx_prod, 'Stok'] -= item['Qty']

                    # Simpan semua
                    save_data(FILE_TRANSAKSI, pd.concat([df_transaksi, pd.DataFrame(new_logs)], ignore_index=True))
                    save_data(FILE_PRODUK, df_produk)
                    
                    # 3. Update Loyalty Points Pelanggan
                    if no_hp_pembeli != "0":
                        # Cari berdasarkan No HP karena nama bisa sama
                        if no_hp_pembeli in df_pelanggan['No HP'].astype(str).values:
                            idx_pel = df_pelanggan[df_pelanggan['No HP'].astype(str) == str(no_hp_pembeli)].index[0]
                            df_pelanggan.at[idx_pel, 'Total Belanja'] += total_belanja
                            save_data(FILE_PELANGGAN, df_pelanggan)

                    st.session_state['keranjang'] = []
                    st.balloons()
                    st.success("Transaksi Berhasil Disimpan!")
                    st.rerun()
        else:
            st.info("Keranjang masih kosong.")
            st.markdown("---")
            st.caption("Pilih produk di sebelah kiri untuk memulai transaksi.")

# ==============================================================================
# MENU 3: MASTER PRODUK (BISA EDIT LANGSUNG)
# ==============================================================================
elif menu == "📦 Master Produk":
    st.title("📦 Gudang & Harga")
    
    tab1, tab2 = st.tabs(["Daftar Produk (Edit)", "Tambah Produk Baru"])
    
    df = load_data(FILE_PRODUK, ['Nama Produk', 'Kategori', 'HPP (Modal)', 'Harga Jual', 'Stok'])
    
    with tab1:
        st.write("Klik dua kali pada sel tabel untuk mengedit data (Excel Style).")
        # Fitur Data Editor (Modern)
        edited_df = st.data_editor(
            df,
            num_rows="dynamic",
            column_config={
                "HPP (Modal)": st.column_config.NumberColumn(format="Rp %d"),
                "Harga Jual": st.column_config.NumberColumn(format="Rp %d"),
                "Stok": st.column_config.NumberColumn(help="Stok saat ini")
            },
            use_container_width=True,
            key="editor_produk"
        )
        
        # Tombol Simpan Perubahan dari Editor
        if st.button("Simpan Perubahan Tabel"):
            save_data(FILE_PRODUK, edited_df)
            st.success("Database produk diperbarui!")
            
    with tab2:
        with st.form("tambah_produk"):
            c1, c2 = st.columns(2)
            nama = c1.text_input("Nama Produk")
            kat = c2.selectbox("Kategori", ["Makanan", "Minuman", "Elektronik", "Jasa", "Lainnya"])
            
            c3, c4, c5 = st.columns(3)
            hpp = c3.number_input("Modal (HPP)", step=1000)
            jual = c4.number_input("Harga Jual", step=1000)
            stok = c5.number_input("Stok Awal", value=10)
            
            if st.form_submit_button("Tambah Produk"):
                if nama not in df['Nama Produk'].values:
                    new_item = pd.DataFrame({'Nama Produk': [nama], 'Kategori': [kat], 'HPP (Modal)': [hpp], 'Harga Jual': [jual], 'Stok': [stok]})
                    save_data(FILE_PRODUK, pd.concat([df, new_item], ignore_index=True))
                    st.success("Produk baru ditambahkan")
                    st.rerun()
                else:
                    st.error("Nama produk sudah ada!")

# ==============================================================================
# MENU 4: LAPORAN & DASHBOARD
# ==============================================================================
elif menu == "📊 Laporan Transaksi":
    st.title("📊 Laporan & Evaluasi")
    
    df = load_data(FILE_TRANSAKSI, ['Tanggal', 'No HP', 'Pelanggan', 'Produk', 'Qty', 'Total', 'Laba'])
    
    if not df.empty:
        # Konversi kolom tanggal biar aman
        df['Tanggal'] = pd.to_datetime(df['Tanggal'])
        
        # --- SCORECARD (KPI) ---
        total_omzet = df['Total'].sum()
        total_laba = df['Laba'].sum()
        total_transaksi = len(df)
        
        m1, m2, m3 = st.columns(3)
        m1.metric("Total Omzet", format_rupiah(total_omzet), help="Total uang masuk")
        m2.metric("Total Profit", format_rupiah(total_laba), delta="Margin Bersih", delta_color="normal")
        m3.metric("Jumlah Transaksi", f"{total_transaksi} Trx")
        
        st.markdown("---")
        
        # --- GRAFIK CHART ---
        col_chart1, col_chart2 = st.columns(2)
        
        with col_chart1:
            st.subheader("Tren Penjualan Harian")
            daily_sales = df.groupby('Tanggal')['Total'].sum().reset_index()
            st.bar_chart(daily_sales, x='Tanggal', y='Total')
            
        with col_chart2:
            st.subheader("Produk Terlaris")
            top_products = df.groupby('Produk')['Qty'].sum().sort_values(ascending=False).head(5)
            st.bar_chart(top_products, horizontal=True)
            
        # --- TABEL DETAIL ---
        st.subheader("Rincian Transaksi")
        st.dataframe(
            df.sort_values(by='Tanggal', ascending=False),
            column_config={
                "Tanggal": st.column_config.DateColumn("Tanggal"),
                "Total": st.column_config.NumberColumn(format="Rp %d"),
                "Laba": st.column_config.NumberColumn(format="Rp %d"),
            },
            use_container_width=True
        )
    else:
        st.info("Belum ada data transaksi untuk ditampilkan.")
