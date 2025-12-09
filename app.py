import streamlit as st
import pandas as pd
import os
from datetime import datetime

# ==============================================================================
# 1. KONFIGURASI HALAMAN
# ==============================================================================
st.set_page_config(page_title="UMKM Super App", layout="wide", initial_sidebar_state="expanded")

# ==============================================================================
# 2. SISTEM TEMA (DARK/LIGHT MODE SWITCH)
# ==============================================================================
# Fungsi untuk menyuntikkan CSS dinamis berdasarkan pilihan user
def inject_custom_css(is_dark_mode):
    if is_dark_mode:
        # --- CSS MODE GELAP (DARK MODE) ---
        bg_color = "#121212"
        text_color = "#ffffff"
        card_bg = "#1E1E1E"
        border_color = "#333333"
        input_bg = "#2D2D2D"
    else:
        # --- CSS MODE TERANG (LIGHT MODE) ---
        bg_color = "#f8f9fa"
        text_color = "#212529"
        card_bg = "#ffffff"
        border_color = "#e0e0e0"
        input_bg = "#ffffff"

    st.markdown(f"""
    <style>
        /* Mengatur Background Utama & Warna Teks Global */
        .stApp {{
            background-color: {bg_color};
            color: {text_color};
        }}
        
        /* Mengatur Container/Card agar terlihat rapi */
        div[data-testid="stContainer"] {{
            background-color: transparent;
        }}
        
        /* Container border (kotak-kotak fitur) */
        div[data-testid="stVerticalBlockBorderWrapper"] > div > div {{
            background-color: {card_bg};
            border: 1px solid {border_color};
            border-radius: 10px;
            padding: 15px;
        }}
        
        /* Memperbaiki Warna Input (Agar tidak invisible) */
        input, select, textarea {{
            color: {text_color} !important;
            background-color: {input_bg} !important;
        }}
        
        /* Memperbaiki Warna Pilihan Dropdown */
        div[data-baseweb="select"] > div {{
            background-color: {input_bg} !important;
            color: {text_color} !important;
        }}
        
        /* Metric Card Style */
        div[data-testid="stMetric"] {{
            background-color: {card_bg};
            padding: 10px;
            border-radius: 8px;
            border: 1px solid {border_color};
        }}

        /* Tabel Dataframe */
        div[data-testid="stDataFrame"] {{
            background-color: {card_bg};
        }}
        
        h1, h2, h3, h4, p, label, span {{
            color: {text_color} !important;
        }}
    </style>
    """, unsafe_allow_html=True)

# ==============================================================================
# 3. DATABASE & LOGIKA DASAR
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
# 4. SIDEBAR & NAVIGASI
# ==============================================================================
st.sidebar.title("UMKM Manager")

# --- TOGGLE NIGHT MODE ---
st.sidebar.markdown("### 🎨 Tampilan")
is_dark = st.sidebar.toggle("🌙 Mode Gelap (Night Mode)", value=False)
inject_custom_css(is_dark) # Panggil fungsi CSS di sini

st.sidebar.markdown("---")
st.sidebar.markdown("### 🧭 Menu")
menu = st.sidebar.radio("Navigasi", [
    "👥 Data Pelanggan", 
    "🛒 Kasir (POS)", 
    "📦 Master Produk", 
    "📊 Laporan Transaksi"
])

# ==============================================================================
# MENU 1: DATA PELANGGAN
# ==============================================================================
if menu == "👥 Data Pelanggan":
    st.title("👥 Manajemen Pelanggan")
    
    col1, col2 = st.columns([1, 2])

    with col1:
        with st.container(border=True):
            st.subheader("➕ Tambah Pelanggan")
            with st.form("form_pelanggan"):
                nama_pel = st.text_input("Nama Lengkap")
                hp_pel = st.text_input("Nomor WhatsApp", placeholder="0812...")
                alamat = st.text_area("Alamat")
                submit = st.form_submit_button("Simpan Data", type="primary")
                
                if submit and hp_pel and nama_pel:
                    df = load_data(FILE_PELANGGAN, ['No HP', 'Nama Pelanggan', 'Alamat', 'Total Belanja'])
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
                        st.success("Berhasil disimpan!")
                        st.rerun()

    with col2:
        with st.container(border=True):
            st.subheader("📂 Direktori Pelanggan")
            df_pel = load_data(FILE_PELANGGAN, ['No HP', 'Nama Pelanggan', 'Alamat', 'Total Belanja'])
            
            search = st.text_input("🔍 Cari Nama / No HP", placeholder="Ketik filter...")
            if search:
                mask = df_pel.astype(str).apply(lambda x: x.str.contains(search, case=False)).any(axis=1)
                df_pel = df_pel[mask]
                
            st.dataframe(
                df_pel, 
                column_config={"Total Belanja": st.column_config.NumberColumn(format="Rp %d")},
                use_container_width=True,
                hide_index=True
            )

# ==============================================================================
# MENU 2: KASIR / POS
# ==============================================================================
elif menu == "🛒 Kasir (POS)":
    st.title("🛒 Kasir Pintar")
    
    df_produk = load_data(FILE_PRODUK, ['Nama Produk', 'Kategori', 'HPP (Modal)', 'Harga Jual', 'Stok'])
    df_pelanggan = load_data(FILE_PELANGGAN, ['No HP', 'Nama Pelanggan', 'Alamat', 'Total Belanja'])

    col_kiri, col_kanan = st.columns([1.5, 1])

    with col_kiri:
        with st.container(border=True):
            st.subheader("1. Data Pembeli")
            opsi_pelanggan = ["0 - Umum (Guest)"] + [f"{row['No HP']} - {row['Nama Pelanggan']}" for index, row in df_pelanggan.iterrows()]
            pilih_pelanggan_str = st.selectbox("👤 Pilih Pelanggan", opsi_pelanggan)
            
            if " - " in pilih_pelanggan_str:
                no_hp_pembeli = pilih_pelanggan_str.split(" - ")[0]
                nama_pembeli = pilih_pelanggan_str.split(" - ")[1]
            else:
                no_hp_pembeli = "0"
                nama_pembeli = "Umum"

            tgl_transaksi = st.date_input("Tanggal", datetime.now())

        with st.container(border=True):
            st.subheader("2. Input Produk")
            produk_tersedia = df_produk[df_produk['Stok'] > 0]
            nama_produk_list = ["-- Pilih Produk --"] + produk_tersedia['Nama Produk'].tolist()
            pilih_produk = st.selectbox("📦 Cari Produk", nama_produk_list)
            
            c1, c2, c3 = st.columns(3)
            harga_satuan, stok_tersedia = 0, 0
            
            if pilih_produk != "-- Pilih Produk --":
                item_data = df_produk[df_produk['Nama Produk'] == pilih_produk].iloc[0]
                harga_satuan = int(item_data['Harga Jual'])
                modal_satuan = int(item_data['HPP (Modal)'])
                stok_tersedia = int(item_data['Stok'])
                
            with c1: st.metric("Stok", f"{stok_tersedia}")
            with c2: st.metric("Harga", format_rupiah(harga_satuan))
            with c3: qty = st.number_input("Qty", 1, max_value=stok_tersedia if stok_tersedia > 0 else 1, value=1)

            if st.button("Masuk Keranjang ⬇️", type="primary", use_container_width=True):
                if pilih_produk != "-- Pilih Produk --":
                    st.session_state['keranjang'].append({
                        'Nama Produk': pilih_produk,
                        'Harga': harga_satuan,
                        'Qty': qty,
                        'Subtotal': harga_satuan * qty,
                        'Modal': modal_satuan * qty
                    })
                    st.rerun()

    with col_kanan:
        with st.container(border=True):
            st.subheader("🧾 Invoice")
            if len(st.session_state['keranjang']) > 0:
                df_cart = pd.DataFrame(st.session_state['keranjang'])
                st.dataframe(df_cart[['Nama Produk', 'Qty', 'Subtotal']], hide_index=True, use_container_width=True)
                
                total_belanja = df_cart['Subtotal'].sum()
                st.divider()
                st.subheader(f"Total: {format_rupiah(total_belanja)}")
                
                c_btn1, c_btn2 = st.columns(2)
                if c_btn1.button("❌ Batal"):
                    st.session_state['keranjang'] = []
                    st.rerun()
                if c_btn2.button("✅ Bayar"):
                    # Simpan Log
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
                        idx_prod = df_produk[df_produk['Nama Produk'] == item['Nama Produk']].index[0]
                        df_produk.at[idx_prod, 'Stok'] -= item['Qty']

                    save_data(FILE_TRANSAKSI, pd.concat([df_transaksi, pd.DataFrame(new_logs)], ignore_index=True))
                    save_data(FILE_PRODUK, df_produk)
                    
                    if no_hp_pembeli != "0" and no_hp_pembeli in df_pelanggan['No HP'].astype(str).values:
                        idx_pel = df_pelanggan[df_pelanggan['No HP'].astype(str) == str(no_hp_pembeli)].index[0]
                        df_pelanggan.at[idx_pel, 'Total Belanja'] += total_belanja
                        save_data(FILE_PELANGGAN, df_pelanggan)

                    st.session_state['keranjang'] = []
                    st.success("Transaksi Sukses!")
                    st.balloons()
                    st.rerun()
            else:
                st.caption("Keranjang kosong.")

# ==============================================================================
# MENU 3: MASTER PRODUK
# ==============================================================================
elif menu == "📦 Master Produk":
    st.title("📦 Gudang & Harga")
    
    df = load_data(FILE_PRODUK, ['Nama Produk', 'Kategori', 'HPP (Modal)', 'Harga Jual', 'Stok'])
    tab1, tab2 = st.tabs(["Daftar Produk", "Tambah Baru"])
    
    with tab1:
        with st.container(border=True):
            st.info("💡 Edit langsung di tabel lalu klik Simpan.")
            edited_df = st.data_editor(
                df, num_rows="dynamic", use_container_width=True,
                column_config={"HPP (Modal)": st.column_config.NumberColumn(format="Rp %d"), "Harga Jual": st.column_config.NumberColumn(format="Rp %d")}
            )
            if st.button("Simpan Perubahan Tabel"):
                save_data(FILE_PRODUK, edited_df)
                st.success("Update berhasil!")
                st.rerun()
            
    with tab2:
        with st.form("tambah_produk"):
            c1, c2 = st.columns(2)
            nama = c1.text_input("Nama Produk")
            kat = c2.selectbox("Kategori", ["Makanan", "Minuman", "Elektronik", "Jasa", "Lainnya"])
            c3, c4, c5 = st.columns(3)
            hpp = c3.number_input("Modal", step=1000)
            jual = c4.number_input("Harga Jual", step=1000)
            stok = c5.number_input("Stok", value=10)
            
            if st.form_submit_button("Tambah Produk"):
                if nama not in df['Nama Produk'].values:
                    new_item = pd.DataFrame({'Nama Produk': [nama], 'Kategori': [kat], 'HPP (Modal)': [hpp], 'Harga Jual': [jual], 'Stok': [stok]})
                    save_data(FILE_PRODUK, pd.concat([df, new_item], ignore_index=True))
                    st.success("Produk ditambahkan")
                    st.rerun()
                else:
                    st.error("Produk sudah ada!")

# ==============================================================================
# MENU 4: LAPORAN
# ==============================================================================
elif menu == "📊 Laporan Transaksi":
    st.title("📊 Laporan Keuangan")
    df = load_data(FILE_TRANSAKSI, ['Tanggal', 'No HP', 'Pelanggan', 'Produk', 'Qty', 'Total', 'Laba'])
    
    if not df.empty:
        total_omzet = df['Total'].sum()
        total_laba = df['Laba'].sum()
        
        c1, c2, c3 = st.columns(3)
        c1.metric("Omzet", format_rupiah(total_omzet))
        c2.metric("Profit", format_rupiah(total_laba))
        c3.metric("Transaksi", f"{len(df)}")
        
        with st.container(border=True):
            st.subheader("Detail Transaksi")
            st.dataframe(df, use_container_width=True)
    else:
        st.info("Belum ada data.")
