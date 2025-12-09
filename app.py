import streamlit as st
import pandas as pd
import os
from datetime import datetime

# ==============================================================================
# 1. KONFIGURASI TAMPILAN (CLEAN & PROFESSIONAL)
# ==============================================================================
st.set_page_config(page_title="UMKM POS Pro", layout="wide")

# CSS Kustom untuk Tampilan Modern
st.markdown("""
<style>
    /* Mengatur Tab agar terlihat seperti Menu Navigasi Atas */
    div[data-testid="stTabs"] button {
        flex-grow: 1; /* Agar menu rata memenuhi lebar */
        font-size: 16px;
        font-weight: 600;
        padding: 15px;
    }
    
    /* Hilangkan padding default yang berlebihan */
    .block-container {
        padding-top: 2rem;
    }
    
    /* Styling Card/Kotak Konten */
    .css-card {
        background-color: #FFFFFF;
        border-radius: 10px;
        padding: 20px;
        box-shadow: 0 4px 6px rgba(0,0,0,0.1);
        margin-bottom: 20px;
        border: 1px solid #f0f0f0;
    }
    
    /* Tombol Utama (Primary) */
    div.stButton > button:first-child {
        border-radius: 8px;
        font-weight: 600;
        width: 100%;
    }
</style>
""", unsafe_allow_html=True)

# ==============================================================================
# 2. SISTEM DATABASE
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
# 3. NAVIGASI UTAMA (MENGGUNAKAN NATIVE TABS)
# ==============================================================================
# Ini pengganti menu sebelumnya. Tidak perlu install library tambahan!
tab_kasir, tab_dashboard, tab_produk, tab_pelanggan = st.tabs([
    "🛒 KASIR (POS)", 
    "📊 DASHBOARD", 
    "📦 PRODUK", 
    "👥 PELANGGAN"
])

# ==============================================================================
# TAB 1: KASIR / POS (Default View)
# ==============================================================================
with tab_kasir:
    # Load Data
    df_produk = load_data(FILE_PRODUK, ['Nama Produk', 'Kategori', 'HPP (Modal)', 'Harga Jual', 'Stok'])
    df_pelanggan = load_data(FILE_PELANGGAN, ['No HP', 'Nama Pelanggan', 'Total Belanja'])

    # Layout: Kiri (Input) 60% - Kanan (Struk) 40%
    col_input, col_struk = st.columns([1.5, 1], gap="medium")

    # --- KOLOM KIRI: INPUT ORDER ---
    with col_input:
        st.subheader("🛍️ Input Pesanan")
        
        with st.container(border=True):
            # Baris 1: Pelanggan & Tanggal
            c1, c2 = st.columns([2,1])
            with c1:
                opsi_pel = ["UMUM (Guest)"] + df_pelanggan['Nama Pelanggan'].tolist()
                nama_pelanggan = st.selectbox("Pilih Pelanggan", opsi_pel)
            with c2:
                tgl = st.date_input("Tanggal", datetime.now(), label_visibility="collapsed")

            st.markdown("---")
            
            # Baris 2: Pilih Produk
            produk_aktif = df_produk[df_produk['Stok'] > 0]
            pilih_produk = st.selectbox("🔍 Cari Produk (Ketik Nama)", [""] + produk_aktif['Nama Produk'].tolist())
            
            if pilih_produk:
                item = df_produk[df_produk['Nama Produk'] == pilih_produk].iloc[0]
                stok_sisa = int(item['Stok'])
                harga = int(item['Harga Jual'])
                
                # Info Produk & Input Qty
                info_col, qty_col = st.columns([2, 1])
                with info_col:
                    st.info(f"Stok: {stok_sisa} | Harga: {format_rupiah(harga)}")
                with qty_col:
                    qty = st.number_input("Qty", min_value=1, max_value=stok_sisa, value=1)
                
                # Tombol Tambah
                if st.button("➕ Masukkan Keranjang", type="primary"):
                    subtotal = harga * qty
                    modal_total = int(item['HPP (Modal)']) * qty
                    
                    st.session_state['keranjang'].append({
                        "Produk": pilih_produk,
                        "Harga": harga,
                        "Qty": qty,
                        "Subtotal": subtotal,
                        "Modal": modal_total
                    })
                    st.rerun()

    # --- KOLOM KANAN: KERANJANG / STRUK ---
    with col_struk:
        st.subheader("🧾 Ringkasan Belanja")
        
        with st.container(border=True):
            if len(st.session_state['keranjang']) > 0:
                df_cart = pd.DataFrame(st.session_state['keranjang'])
                
                st.dataframe(
                    df_cart[['Produk', 'Qty', 'Subtotal']], 
                    hide_index=True, 
                    use_container_width=True,
                    column_config={"Subtotal": st.column_config.NumberColumn(format="Rp %d")}
                )
                
                total_bayar = df_cart['Subtotal'].sum()
                st.markdown("---")
                c_tot1, c_tot2 = st.columns([1,1])
                c_tot1.markdown("#### Total:")
                c_tot2.markdown(f"<h3 style='text-align: right; color: #2563EB;'>{format_rupiah(total_bayar)}</h3>", unsafe_allow_html=True)
                
                col_batal, col_bayar = st.columns(2)
                with col_batal:
                    if st.button("🗑️ Hapus"):
                        st.session_state['keranjang'] = []
                        st.rerun()
                
                with col_bayar:
                    if st.button("✅ BAYAR", type="primary"):
                        # Simpan ke Database
                        df_log = load_data(FILE_TRANSAKSI, ['Tanggal', 'Pelanggan', 'Produk', 'Qty', 'Total', 'Modal', 'Laba'])
                        new_entries = []
                        
                        for i in st.session_state['keranjang']:
                            idx = df_produk[df_produk['Nama Produk'] == i['Produk']].index[0]
                            df_produk.at[idx, 'Stok'] -= i['Qty']
                            
                            new_entries.append({
                                'Tanggal': tgl,
                                'Pelanggan': nama_pelanggan,
                                'Produk': i['Produk'],
                                'Qty': i['Qty'],
                                'Total': i['Subtotal'],
                                'Modal': i['Modal'],
                                'Laba': i['Subtotal'] - i['Modal']
                            })
                        
                        save_data(FILE_TRANSAKSI, pd.concat([df_log, pd.DataFrame(new_entries)], ignore_index=True))
                        save_data(FILE_PRODUK, df_produk)
                        
                        if nama_pelanggan != "UMUM (Guest)":
                            idx_p = df_pelanggan[df_pelanggan['Nama Pelanggan'] == nama_pelanggan].index[0]
                            df_pelanggan.at[idx_p, 'Total Belanja'] += total_bayar
                            save_data(FILE_PELANGGAN, df_pelanggan)
                        
                        st.session_state['keranjang'] = []
                        st.balloons()
                        st.success("Transaksi Berhasil!")
                        st.rerun()
            else:
                st.info("Keranjang kosong.")

# ==============================================================================
# TAB 2: DASHBOARD
# ==============================================================================
with tab_dashboard:
    st.header("📊 Dashboard Performa")
    df_trx = load_data(FILE_TRANSAKSI, ['Tanggal', 'Total', 'Laba', 'Produk', 'Qty'])
    
    if not df_trx.empty:
        col1, col2, col3, col4 = st.columns(4)
        omzet = df_trx['Total'].sum()
        laba = df_trx['Laba'].sum()
        qty_sold = df_trx['Qty'].sum()
        trx_count = len(df_trx)
        
        col1.metric("Total Omzet", format_rupiah(omzet))
        col2.metric("Total Profit", format_rupiah(laba))
        col3.metric("Produk Terjual", f"{qty_sold} Unit")
        col4.metric("Total Transaksi", f"{trx_count} Kali")
        
        st.markdown("---")
        
        c1, c2 = st.columns(2)
        with c1:
            st.subheader("Tren Penjualan")
            daily = df_trx.groupby('Tanggal')['Total'].sum().reset_index()
            st.area_chart(daily, x='Tanggal', y='Total')
        with c2:
            st.subheader("Produk Terlaris")
            top = df_trx.groupby('Produk')['Qty'].sum().sort_values(ascending=False).head(5)
            st.bar_chart(top)
    else:
        st.info("Belum ada data transaksi.")

# ==============================================================================
# TAB 3: MANAJEMEN PRODUK
# ==============================================================================
with tab_produk:
    st.header("📦 Manajemen Produk")
    df = load_data(FILE_PRODUK, ['Nama Produk', 'Kategori', 'HPP (Modal)', 'Harga Jual', 'Stok'])
    
    c_edit, c_tambah = st.columns([2, 1])
    
    with c_edit:
        st.subheader("Daftar & Edit Produk")
        st.caption("Klik angka di tabel untuk mengedit langsung.")
        edited_df = st.data_editor(df, num_rows="dynamic", use_container_width=True, height=400)
        
        if st.button("💾 Simpan Perubahan"):
            save_data(FILE_PRODUK, edited_df)
            st.success("Database berhasil diperbarui!")
            st.rerun()
            
    with c_tambah:
        st.subheader("Tambah Baru")
        with st.container(border=True):
            nama = st.text_input("Nama Produk")
            kat = st.selectbox("Kategori", ["Makanan", "Minuman", "Jasa", "Barang"])
            stok = st.number_input("Stok Awal", value=10)
            hpp = st.number_input("Modal (HPP)", step=100)
            jual = st.number_input("Harga Jual", step=100)
            
            if st.button("Simpan Produk Baru"):
                if nama and nama not in df['Nama Produk'].values:
                    new_item = pd.DataFrame([{'Nama Produk': nama, 'Kategori': kat, 'HPP (Modal)': hpp, 'Harga Jual': jual, 'Stok': stok}])
                    save_data(FILE_PRODUK, pd.concat([df, new_item], ignore_index=True))
                    st.success("Produk tersimpan!")
                    st.rerun()
                else:
                    st.error("Nama produk kosong atau sudah ada.")

# ==============================================================================
# TAB 4: PELANGGAN
# ==============================================================================
with tab_pelanggan:
    st.header("👥 Database Pelanggan")
    df_pel = load_data(FILE_PELANGGAN, ['No HP', 'Nama Pelanggan', 'Total Belanja'])
    
    col_kiri, col_kanan = st.columns([1, 2], gap="large")
    
    with col_kiri:
        with st.container(border=True):
            st.subheader("Tambah Pelanggan")
            nama = st.text_input("Nama Lengkap")
            hp = st.text_input("No HP / WhatsApp")
            if st.button("Simpan Data Pelanggan"):
                if nama and hp:
                    if hp in df_pel['No HP'].astype(str).values:
                        st.error("No HP sudah terdaftar!")
                    else:
                        new_p = pd.DataFrame([{'No HP': hp, 'Nama Pelanggan': nama, 'Total Belanja': 0}])
                        save_data(FILE_PELANGGAN, pd.concat([df_pel, new_p], ignore_index=True))
                        st.success("Berhasil!")
                        st.rerun()
    
    with col_kanan:
        st.subheader("Daftar Pelanggan")
        st.dataframe(df_pel, use_container_width=True)
