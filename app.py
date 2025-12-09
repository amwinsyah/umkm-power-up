import streamlit as st
import pandas as pd
import os
from datetime import datetime

# --- KONFIGURASI HALAMAN ---
st.set_page_config(page_title="UMKM Pro System", layout="wide")

# --- INITIALISASI STATE ---
if 'keranjang' not in st.session_state:
    st.session_state['keranjang'] = []

# --- DATABASE FILES ---
FILE_PRODUK = 'master_produk.csv'
FILE_TRANSAKSI = 'data_transaksi.csv'
FILE_PELANGGAN = 'data_pelanggan.csv'

# --- FUNGSI LOAD & SAVE DATA ---
def load_data(filename, columns):
    if not os.path.exists(filename):
        df = pd.DataFrame(columns=columns)
        df.to_csv(filename, index=False)
    return pd.read_csv(filename)

def save_data(filename, df):
    df.to_csv(filename, index=False)

# --- SIDEBAR MENU ---
st.sidebar.title("🏪 UMKM Digital")
menu = st.sidebar.radio("Navigasi", ["Kasir (POS)", "Master Produk", "Data Pelanggan", "Laporan Transaksi"])

# ==============================================================================
# MENU 1: KASIR (POINT OF SALE)
# ==============================================================================
if menu == "Kasir (POS)":
    st.header("🛒 Kasir Penjualan")
    
    # Load Data
    df_produk = load_data(FILE_PRODUK, ['Nama Produk', 'Kategori', 'HPP (Modal)', 'Margin (%)', 'Harga Jual', 'Stok'])
    df_pelanggan = load_data(FILE_PELANGGAN, ['Nama Pelanggan', 'No HP', 'Total Belanja'])
    
    # -- BAGIAN 1: PILIH PELANGGAN --
    col_pel, col_tgl = st.columns(2)
    with col_pel:
        list_pelanggan = ["Umum (Guest)"] + df_pelanggan['Nama Pelanggan'].tolist()
        nama_pembeli = st.selectbox("Pilih Pelanggan", list_pelanggan)
    with col_tgl:
        tanggal = st.date_input("Tanggal Transaksi", datetime.now())

    st.markdown("---")

    # -- BAGIAN 2: PILIH PRODUK --
    col1, col2, col3, col4 = st.columns([3, 2, 2, 2])
    
    with col1:
        produk_tersedia = df_produk[df_produk['Stok'] > 0]['Nama Produk'].tolist()
        pilih_produk = st.selectbox("Pilih Produk", ["-- Pilih --"] + produk_tersedia)
    
    with col2:
        harga_saat_ini = 0
        stok_saat_ini = 0
        modal_saat_ini = 0
        
        if pilih_produk != "-- Pilih --":
            data_prod = df_produk[df_produk['Nama Produk'] == pilih_produk].iloc[0]
            harga_saat_ini = int(data_prod['Harga Jual'])
            stok_saat_ini = int(data_prod['Stok'])
            modal_saat_ini = int(data_prod['HPP (Modal)'])
            
        st.metric("Harga Satuan", f"Rp {harga_saat_ini:,}")
    
    with col3:
        qty = st.number_input("Jumlah (Qty)", min_value=1, max_value=stok_saat_ini if stok_saat_ini > 0 else 1, value=1)
    
    with col4:
        if st.button("Tambah Item", type="primary"):
            if pilih_produk != "-- Pilih --":
                total_harga = harga_saat_ini * qty
                total_modal = modal_saat_ini * qty
                
                st.session_state['keranjang'].append({
                    'Nama Produk': pilih_produk,
                    'Harga Satuan': harga_saat_ini,
                    'Qty': qty,
                    'Subtotal': total_harga,
                    'Total Modal': total_modal
                })
                st.rerun() # <--- INI YANG DIPERBAIKI
            else:
                st.warning("Pilih produk dulu!")

    # -- BAGIAN 3: KERANJANG BELANJA & CHECKOUT --
    st.write("### 🛍️ Keranjang Belanja")
    
    if len(st.session_state['keranjang']) > 0:
        df_keranjang = pd.DataFrame(st.session_state['keranjang'])
        st.dataframe(df_keranjang, use_container_width=True)
        
        grand_total = df_keranjang['Subtotal'].sum()
        total_modal_transaksi = df_keranjang['Total Modal'].sum()
        
        st.subheader(f"Total Tagihan: Rp {grand_total:,.0f}")
        
        c_bayar, c_batal = st.columns([1,4])
        
        with c_bayar:
            if st.button("💰 BAYAR SEKARANG"):
                # 1. Simpan ke File Transaksi
                df_transaksi = load_data(FILE_TRANSAKSI, ['Tanggal', 'Pelanggan', 'Produk', 'Qty', 'Total', 'Modal', 'Laba'])
                
                new_transactions = []
                for item in st.session_state['keranjang']:
                    new_transactions.append({
                        'Tanggal': tanggal,
                        'Pelanggan': nama_pembeli,
                        'Produk': item['Nama Produk'],
                        'Qty': item['Qty'],
                        'Total': item['Subtotal'],
                        'Modal': item['Total Modal'],
                        'Laba': item['Subtotal'] - item['Total Modal']
                    })
                    
                    # 2. Kurangi Stok
                    idx = df_produk[df_produk['Nama Produk'] == item['Nama Produk']].index[0]
                    df_produk.at[idx, 'Stok'] = df_produk.at[idx, 'Stok'] - item['Qty']
                
                # Simpan File
                df_transaksi = pd.concat([df_transaksi, pd.DataFrame(new_transactions)], ignore_index=True)
                save_data(FILE_TRANSAKSI, df_transaksi)
                save_data(FILE_PRODUK, df_produk)
                
                # 3. Update Loyalty
                if nama_pembeli != "Umum (Guest)":
                    idx_pel = df_pelanggan[df_pelanggan['Nama Pelanggan'] == nama_pembeli].index[0]
                    df_pelanggan.at[idx_pel, 'Total Belanja'] += grand_total
                    save_data(FILE_PELANGGAN, df_pelanggan)
                
                # Reset
                st.session_state['keranjang'] = []
                st.success("Transaksi Sukses!")
                st.rerun() # <--- INI YANG DIPERBAIKI
        
        with c_batal:
            if st.button("Hapus Keranjang"):
                st.session_state['keranjang'] = []
                st.rerun() # <--- INI YANG DIPERBAIKI
    else:
        st.info("Keranjang kosong.")

# ==============================================================================
# MENU 2: MASTER PRODUK
# ==============================================================================
elif menu == "Master Produk":
    st.header("📦 Gudang & Produk")
    
    with st.expander("Tambah Produk Baru / Update Stok"):
        col1, col2 = st.columns(2)
        with col1:
            nama = st.text_input("Nama Produk")
            kategori = st.selectbox("Kategori", ["Makanan", "Minuman", "Jasa", "Retail", "Lainnya"])
            stok = st.number_input("Stok Tambahan", min_value=1, value=10)
        with col2:
            hpp = st.number_input("HPP (Modal)", min_value=0)
            jual = st.number_input("Harga Jual", min_value=0)
            
        if st.button("Simpan Produk"):
            df = load_data(FILE_PRODUK, ['Nama Produk', 'Kategori', 'HPP (Modal)', 'Margin (%)', 'Harga Jual', 'Stok'])
            
            if nama in df['Nama Produk'].values:
                idx = df[df['Nama Produk'] == nama].index[0]
                df.at[idx, 'Stok'] += stok
                if jual > 0: df.at[idx, 'Harga Jual'] = jual
                st.success(f"Stok {nama} berhasil ditambahkan!")
            else:
                margin = ((jual - hpp)/jual * 100) if jual > 0 else 0
                new_data = pd.DataFrame({'Nama Produk': [nama], 'Kategori': [kategori], 'HPP (Modal)': [hpp], 'Margin (%)': [margin], 'Harga Jual': [jual], 'Stok': [stok]})
                df = pd.concat([df, new_data], ignore_index=True)
                st.success(f"Produk {nama} berhasil dibuat!")
            
            save_data(FILE_PRODUK, df)

    st.subheader("Stok Saat Ini")
    df = load_data(FILE_PRODUK, ['Nama Produk', 'Kategori', 'HPP (Modal)', 'Margin (%)', 'Harga Jual', 'Stok'])
    st.dataframe(df, use_container_width=True)

# ==============================================================================
# MENU 3: DATA PELANGGAN
# ==============================================================================
elif menu == "Data Pelanggan":
    st.header("👥 Data Pelanggan")
    
    with st.form("input_pelanggan"):
        c1, c2 = st.columns(2)
        nama_pel = c1.text_input("Nama Pelanggan")
        hp_pel = c2.text_input("No WhatsApp")
        submit = st.form_submit_button("Simpan Pelanggan")
        
        if submit and nama_pel:
            df = load_data(FILE_PELANGGAN, ['Nama Pelanggan', 'No HP', 'Total Belanja'])
            if nama_pel not in df['Nama Pelanggan'].values:
                new_pel = pd.DataFrame({'Nama Pelanggan': [nama_pel], 'No HP': [hp_pel], 'Total Belanja': [0]})
                df = pd.concat([df, new_pel], ignore_index=True)
                save_data(FILE_PELANGGAN, df)
                st.success("Pelanggan Disimpan!")
                st.rerun() # <--- INI JUGA DIPERBAIKI
            else:
                st.warning("Nama sudah ada.")
    
    st.subheader("🏆 Top Pelanggan")
    df = load_data(FILE_PELANGGAN, ['Nama Pelanggan', 'No HP', 'Total Belanja'])
    st.dataframe(df.sort_values(by='Total Belanja', ascending=False), use_container_width=True)

# ==============================================================================
# MENU 4: LAPORAN TRANSAKSI
# ==============================================================================
elif menu == "Laporan Transaksi":
    st.header("📜 Riwayat Transaksi")
    df = load_data(FILE_TRANSAKSI, ['Tanggal', 'Pelanggan', 'Produk', 'Qty', 'Total', 'Modal', 'Laba'])
    st.dataframe(df.sort_index(ascending=False), use_container_width=True)
