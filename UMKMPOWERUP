import streamlit as st
import pandas as pd
import os

# --- KONFIGURASI HALAMAN ---
st.set_page_config(page_title="UMKM Master System", layout="wide")
st.title("🏭 Manajemen Produk & Harga")

# --- DATABASE (FILE PENYIMPANAN) ---
FILE_PRODUK = 'master_produk.csv'

# Fungsi Memuat Data
def load_produk():
    if not os.path.exists(FILE_PRODUK):
        # Membuat kerangka jika file belum ada
        df = pd.DataFrame(columns=['Nama Produk', 'Kategori', 'HPP (Modal)', 'Margin (%)', 'Harga Jual', 'Stok'])
        df.to_csv(FILE_PRODUK, index=False)
    return pd.read_csv(FILE_PRODUK)

# Fungsi Menyimpan Data Baru
def simpan_produk(nama, kategori, hpp, margin, harga_jual, stok):
    df = load_produk()
    # Cek apakah produk sudah ada (update stok) atau baru
    if nama in df['Nama Produk'].values:
        st.warning(f"Produk '{nama}' sudah ada di database. Hapus dulu jika ingin ubah total.")
    else:
        new_data = pd.DataFrame({
            'Nama Produk': [nama],
            'Kategori': [kategori],
            'HPP (Modal)': [hpp],
            'Margin (%)': [margin],
            'Harga Jual': [harga_jual],
            'Stok': [stok]
        })
        df = pd.concat([df, new_data], ignore_index=True)
        df.to_csv(FILE_PRODUK, index=False)
        st.success(f"Sukses! {nama} masuk ke inventory.")

# --- SIDEBAR NAVIGASI ---
menu = st.sidebar.selectbox("Menu Tahap 1", ["Kalkulator Harga & Input Produk", "Lihat Stok Gudang"])

# ==============================================================================
# FITUR 1: PRICING CALCULATOR (PENENTU HARGA)
# ==============================================================================
if menu == "Kalkulator Harga & Input Produk":
    st.header("🧮 Hitung Harga Jual Optimal")
    st.caption("Gunakan fitur ini untuk menentukan harga jual agar profit terjaga, lalu simpan ke database.")

    col1, col2 = st.columns(2)
    
    with col1:
        st.subheader("1. Input Biaya")
        nama_produk = st.text_input("Nama Produk")
        kategori = st.selectbox("Kategori", ["Makanan/Minuman", "Pakaian", "Jasa", "Elektronik", "Lainnya"])
        stok_awal = st.number_input("Stok Awal", min_value=0, value=10)
        
    with col2:
        st.subheader("2. Hitung Cuan")
        hpp = st.number_input("HPP / Modal per Unit (Rp)", min_value=0.0, step=100.0, help="Total biaya bahan + tenaga per 1 barang")
        target_margin = st.slider("Ingin Profit Margin Berapa? (%)", min_value=0, max_value=100, value=30)
        
        # --- LOGIKA MATEMATIKA PRICING ---
        # Rumus: Harga Jual = Modal + (Modal * Persen Untung)
        profit_per_unit = hpp * (target_margin / 100)
        saran_harga = hpp + profit_per_unit
        
        st.info(f"💰 Saran Harga Jual: **Rp {saran_harga:,.0f}**")
        
        # Opsi Manual Override (Kalau user ingin membulatkan harga, misal 13.500 jadi 15.000)
        harga_final = st.number_input("Tetapkan Harga Jual Final (Rp)", value=float(saran_harga), min_value=0.0)
        
        # Hitung ulang margin real jika harga dibulatkan
        if harga_final > 0:
            real_margin = ((harga_final - hpp) / harga_final) * 100
            st.write(f"*Margin Aktual: {real_margin:.1f}%*")

    # Tombol Simpan
    st.markdown("---")
    if st.button("Simpan ke Database Produk"):
        if nama_produk and harga_final > 0:
            simpan_produk(nama_produk, kategori, hpp, target_margin, harga_final, stok_awal)
        else:
            st.error("Nama produk dan harga tidak boleh kosong!")

# ==============================================================================
# FITUR 2: GUDANG / INVENTORY TRACKING
# ==============================================================================
elif menu == "Lihat Stok Gudang":
    st.header("📦 Inventory & Aset")
    
    df = load_produk()
    
    if not df.empty:
        # Metrik Ringkas
        total_items = df['Stok'].sum()
        total_aset = (df['HPP (Modal)'] * df['Stok']).sum()
        potensi_omzet = (df['Harga Jual'] * df['Stok']).sum()
        
        m1, m2, m3 = st.columns(3)
        m1.metric("Total Barang (Pcs)", f"{total_items:,}")
        m2.metric("Nilai Aset (Modal Tertanam)", f"Rp {total_aset:,.0f}")
        m3.metric("Potensi Omzet (Jika Habis)", f"Rp {potensi_omzet:,.0f}")
        
        st.markdown("---")
        # Tampilkan Tabel
        st.dataframe(df, use_container_width=True)
        
        # Fitur Hapus Data (Reset)
        if st.checkbox("Tampilkan Opsi Hapus Data"):
            if st.button("⚠️ Hapus Semua Data Produk"):
                if os.path.exists(FILE_PRODUK):
                    os.remove(FILE_PRODUK)
                    st.experimental_rerun()
    else:
        st.info("Belum ada produk. Silakan input di menu Kalkulator Harga.")
