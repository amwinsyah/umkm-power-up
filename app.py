import streamlit as st
import pandas as pd
import os
from datetime import datetime
from streamlit_option_menu import option_menu # Wajib install ini dulu

# ==============================================================================
# 1. SETUP & CSS MAGIC (MODERN LOOK)
# ==============================================================================
st.set_page_config(page_title="UMKM POS Pro", layout="wide")

# CSS Kustom untuk Tampilan Bersih & Profesional
st.markdown("""
<style>
    /* Hilangkan padding atas yang berlebihan */
    .block-container {
        padding-top: 1rem;
        padding-bottom: 1rem;
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
    
    /* Tombol Primary lebih modern */
    div.stButton > button:first-child {
        background-color: #2563EB;
        color: white;
        border-radius: 8px;
        border: none;
        padding: 0.5rem 1rem;
        font-weight: 600;
    }
    div.stButton > button:hover {
        background-color: #1D4ED8;
        color: white;
    }
    
    /* Metric Card Styling */
    div[data-testid="stMetric"] {
        background-color: #F3F4F6;
        padding: 15px;
        border-radius: 10px;
        border: 1px solid #E5E7EB;
    }
</style>
""", unsafe_allow_html=True)

# ==============================================================================
# 2. DATABASE ENGINE
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
# 3. TOP NAVIGATION BAR (MENU ATAS)
# ==============================================================================
# Ini menggantikan Sidebar agar lebih luas
selected = option_menu(
    menu_title=None,
    options=["Dashboard", "Kasir (POS)", "Produk", "Pelanggan"],
    icons=["speedometer2", "cart4", "box-seam", "people-fill"],
    menu_icon="cast",
    default_index=1, # Default langsung buka Kasir
    orientation="horizontal",
    styles={
        "container": {"padding": "0!important", "background-color": "#fafafa"},
        "icon": {"color": "orange", "font-size": "18px"}, 
        "nav-link": {"font-size": "16px", "text-align": "center", "margin":"0px", "--hover-color": "#eee"},
        "nav-link-selected": {"background-color": "#2563EB"},
    }
)

# ==============================================================================
# MENU 1: DASHBOARD (Ringkasan)
# ==============================================================================
if selected == "Dashboard":
    st.markdown("### 📊 Performa Toko Anda")
    
    df_trx = load_data(FILE_TRANSAKSI, ['Tanggal', 'Total', 'Laba', 'Produk', 'Qty'])
    
    if not df_trx.empty:
        # KPI Cards
        col1, col2, col3, col4 = st.columns(4)
        omzet = df_trx['Total'].sum()
        laba = df_trx['Laba'].sum()
        qty_sold = df_trx['Qty'].sum()
        trx_count = len(df_trx)
        
        col1.metric("💰 Total Omzet", format_rupiah(omzet))
        col2.metric("📈 Total Profit", format_rupiah(laba))
        col3.metric("📦 Produk Terjual", f"{qty_sold} Items")
        col4.metric("🧾 Total Transaksi", f"{trx_count} Struk")
        
        st.markdown("---")
        
        # Grafik
        c1, c2 = st.columns(2)
        with c1:
            st.caption("Tren Penjualan (Omzet)")
            # Group by tanggal
            daily = df_trx.groupby('Tanggal')['Total'].sum().reset_index()
            st.line_chart(daily, x='Tanggal', y='Total')
            
        with c2:
            st.caption("Top 5 Produk Terlaris")
            top = df_trx.groupby('Produk')['Qty'].sum().sort_values(ascending=False).head(5)
            st.bar_chart(top)
            
        # Tabel Riwayat Terbaru
        st.write("#### 📜 10 Transaksi Terakhir")
        st.dataframe(df_trx.sort_index(ascending=False).head(10), use_container_width=True, hide_index=True)
        
    else:
        st.info("Belum ada data transaksi. Yuk mulai jualan di menu Kasir!")

# ==============================================================================
# MENU 2: KASIR / POS (UI BARU: Split Screen)
# ==============================================================================
elif selected == "Kasir (POS)":
    # Load Data
    df_produk = load_data(FILE_PRODUK, ['Nama Produk', 'Kategori', 'HPP (Modal)', 'Harga Jual', 'Stok'])
    df_pelanggan = load_data(FILE_PELANGGAN, ['No HP', 'Nama Pelanggan', 'Total Belanja'])

    # Layout: Kiri (Input) 60% - Kanan (Struk) 40%
    col_input, col_struk = st.columns([1.5, 1], gap="medium")

    # --- KOLOM KIRI: INPUT ORDER ---
    with col_input:
        st.markdown("#### 🛍️ Buat Pesanan Baru")
        
        # Container Pelanggan
        with st.container():
            c1, c2 = st.columns([2,1])
            with c1:
                # Searchable Dropdown Pelanggan
                opsi_pel = ["UMUM (Guest)"] + df_pelanggan['Nama Pelanggan'].tolist()
                nama_pelanggan = st.selectbox("Pilih Pelanggan", opsi_pel)
            with c2:
                tgl = st.date_input("Tanggal", datetime.now(), label_visibility="collapsed")

        st.markdown("---")
        
        # Container Produk
        # Filter Produk yg ada stoknya
        produk_aktif = df_produk[df_produk['Stok'] > 0]
        pilih_produk = st.selectbox("🔍 Cari Produk (Ketik Nama)", [""] + produk_aktif['Nama Produk'].tolist())
        
        if pilih_produk:
            # Ambil detail produk
            item = df_produk[df_produk['Nama Produk'] == pilih_produk].iloc[0]
            stok_sisa = int(item['Stok'])
            harga = int(item['Harga Jual'])
            
            # Form Input Qty
            c_info, c_qty, c_btn = st.columns([2, 1, 1])
            with c_info:
                st.info(f"Stok: {stok_sisa} | Harga: {format_rupiah(harga)}")
            with c_qty:
                qty = st.number_input("Qty", min_value=1, max_value=stok_sisa, value=1, label_visibility="collapsed")
            with c_btn:
                if st.button("➕ Tambah", use_container_width=True):
                    # Tambah ke keranjang
                    subtotal = harga * qty
                    modal_total = int(item['HPP (Modal)']) * qty
                    
                    st.session_state['keranjang'].append({
                        "Produk": pilih_produk,
                        "Harga": harga,
                        "Qty": qty,
                        "Subtotal": subtotal,
                        "Modal": modal_total
                    })
                    st.toast(f"Berhasil menambahkan {pilih_produk}")
                    st.rerun()

    # --- KOLOM KANAN: STRUK / KERANJANG ---
    with col_struk:
        st.markdown("#### 🧾 Ringkasan Belanja")
        
        # Container Keranjang (Visual Card)
        with st.container(border=True):
            if len(st.session_state['keranjang']) > 0:
                df_cart = pd.DataFrame(st.session_state['keranjang'])
                
                # Tampilkan Tabel Minimalis
                st.dataframe(
                    df_cart[['Produk', 'Qty', 'Subtotal']], 
                    hide_index=True, 
                    use_container_width=True,
                    column_config={"Subtotal": st.column_config.NumberColumn(format="Rp %d")}
                )
                
                # Kalkulasi
                total_bayar = df_cart['Subtotal'].sum()
                
                st.markdown("---")
                c_tot1, c_tot2 = st.columns([1,1])
                c_tot1.markdown("### Total:")
                c_tot2.markdown(f"<h3 style='text-align: right; color: #2563EB;'>{format_rupiah(total_bayar)}</h3>", unsafe_allow_html=True)
                
                # Action Buttons
                b1, b2 = st.columns(2)
                if b1.button("🗑️ Hapus Semua", use_container_width=True):
                    st.session_state['keranjang'] = []
                    st.rerun()
                
                if b2.button("✅ BAYAR", type="primary", use_container_width=True):
                    # Proses Simpan Transaksi
                    df_log = load_data(FILE_TRANSAKSI, ['Tanggal', 'Pelanggan', 'Produk', 'Qty', 'Total', 'Modal', 'Laba'])
                    
                    new_entries = []
                    for i in st.session_state['keranjang']:
                        # Kurangi Stok
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
                    
                    # Save All
                    save_data(FILE_TRANSAKSI, pd.concat([df_log, pd.DataFrame(new_entries)], ignore_index=True))
                    save_data(FILE_PRODUK, df_produk)
                    
                    # Update Pelanggan (Loyalty)
                    if nama_pelanggan != "UMUM (Guest)":
                        idx_p = df_pelanggan[df_pelanggan['Nama Pelanggan'] == nama_pelanggan].index[0]
                        df_pelanggan.at[idx_p, 'Total Belanja'] += total_bayar
                        save_data(FILE_PELANGGAN, df_pelanggan)
                    
                    st.session_state['keranjang'] = []
                    st.balloons()
                    st.success("Transaksi Berhasil!")
                    st.rerun()
                    
            else:
                st.empty()
                st.info("Keranjang masih kosong.")
                st.caption("Pilih produk di sebelah kiri untuk memulai.")

# ==============================================================================
# MENU 3: MANAJEMEN PRODUK
# ==============================================================================
elif selected == "Produk":
    st.markdown("### 📦 Gudang & Harga Produk")
    
    df = load_data(FILE_PRODUK, ['Nama Produk', 'Kategori', 'HPP (Modal)', 'Harga Jual', 'Stok'])
    
    tab1, tab2 = st.tabs(["✏️ Edit Data Produk", "➕ Tambah Produk Baru"])
    
    with tab1:
        st.caption("Klik dua kali pada angka di tabel untuk mengedit langsung.")
        edited_df = st.data_editor(
            df,
            num_rows="dynamic",
            use_container_width=True,
            column_config={
                "HPP (Modal)": st.column_config.NumberColumn(format="Rp %d"),
                "Harga Jual": st.column_config.NumberColumn(format="Rp %d"),
                "Stok": st.column_config.NumberColumn(help="Stok saat ini")
            },
            height=400
        )
        
        if st.button("💾 Simpan Perubahan Tabel"):
            save_data(FILE_PRODUK, edited_df)
            st.success("Database produk berhasil diperbarui!")
            
    with tab2:
        with st.form("add_prod"):
            c1, c2, c3 = st.columns(3)
            nama = c1.text_input("Nama Produk")
            kat = c2.selectbox("Kategori", ["Makanan", "Minuman", "Jasa", "Barang"])
            stok = c3.number_input("Stok Awal", value=10)
            
            c4, c5 = st.columns(2)
            hpp = c4.number_input("Modal (HPP)", step=100)
            jual = c5.number_input("Harga Jual", step=100)
            
            if st.form_submit_button("Simpan Produk Baru"):
                if nama and nama not in df['Nama Produk'].values:
                    new_item = pd.DataFrame([{
                        'Nama Produk': nama, 'Kategori': kat, 
                        'HPP (Modal)': hpp, 'Harga Jual': jual, 'Stok': stok
                    }])
                    save_data(FILE_PRODUK, pd.concat([df, new_item], ignore_index=True))
                    st.success("Produk tersimpan!")
                    st.rerun()
                else:
                    st.error("Nama produk kosong atau sudah ada.")

# ==============================================================================
# MENU 4: PELANGGAN
# ==============================================================================
elif selected == "Pelanggan":
    st.markdown("### 👥 Database Pelanggan")
    
    df_pel = load_data(FILE_PELANGGAN, ['No HP', 'Nama Pelanggan', 'Total Belanja'])
    
    c_kiri, c_kanan = st.columns([1, 2])
    
    with c_kiri:
        with st.container(border=True):
            st.write("#### Tambah Pelanggan")
            with st.form("add_pel"):
                nama = st.text_input("Nama")
                hp = st.text_input("No HP / WA")
                if st.form_submit_button("Simpan"):
                    if nama and hp:
                        new_p = pd.DataFrame([{'No HP': hp, 'Nama Pelanggan': nama, 'Total Belanja': 0}])
                        save_data(FILE_PELANGGAN, pd.concat([df_pel, new_p], ignore_index=True))
                        st.success("Disimpan!")
                        st.rerun()
    
    with c_kanan:
        st.dataframe(
            df_pel, 
            use_container_width=True,
            column_config={"Total Belanja": st.column_config.NumberColumn(format="Rp %d")}
        )
