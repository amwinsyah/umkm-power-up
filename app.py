import streamlit as st
import pandas as pd
import os
from datetime import datetime
from streamlit_option_menu import option_menu

# ==============================================================================
# 1. KONFIGURASI TAMPILAN (CLEAN & PROFESSIONAL)
# ==============================================================================
st.set_page_config(page_title="UMKM POS Pro", layout="wide")

# CSS Kustom untuk Tampilan Modern
st.markdown("""
<style>
    /* Hilangkan padding default yang berlebihan */
    .block-container {
        padding-top: 1rem;
        padding-bottom: 2rem;
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
        height: auto;
        padding: 0.5rem 1rem;
    }
    
    /* Metric Card Styling */
    div[data-testid="stMetric"] {
        background-color: #F8F9FA;
        padding: 15px;
        border-radius: 10px;
        border: 1px solid #E9ECEF;
    }
    
    /* Tabel Dataframe lebih bersih */
    div[data-testid="stDataFrame"] {
        background-color: white;
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
# 3. TOP NAVIGATION BAR (MENU ATAS)
# ==============================================================================
# Menu navigasi horizontal yang modern
selected = option_menu(
    menu_title=None,
    options=["Dashboard", "Kasir (POS)", "Produk", "Pelanggan"],
    icons=["speedometer2", "cart4", "box-seam", "people-fill"],
    menu_icon="cast",
    default_index=1, # Default buka Kasir
    orientation="horizontal",
    styles={
        "container": {"padding": "0!important", "background-color": "#ffffff"},
        "icon": {"color": "#2563EB", "font-size": "18px"}, 
        "nav-link": {"font-size": "15px", "text-align": "center", "margin":"0px", "--hover-color": "#f1f5f9"},
        "nav-link-selected": {"background-color": "#2563EB", "color": "white"},
    }
)

st.markdown("---")

# ==============================================================================
# MENU 1: DASHBOARD (Ringkasan Bisnis)
# ==============================================================================
if selected == "Dashboard":
    st.header("📊 Dashboard Performa")
    
    df_trx = load_data(FILE_TRANSAKSI, ['Tanggal', 'Total', 'Laba', 'Produk', 'Qty'])
    
    if not df_trx.empty:
        # 1. KPI Cards (Kartu Indikator Utama)
        col1, col2, col3, col4 = st.columns(4)
        omzet = df_trx['Total'].sum()
        laba = df_trx['Laba'].sum()
        qty_sold = df_trx['Qty'].sum()
        trx_count = len(df_trx)
        
        col1.metric("Total Omzet", format_rupiah(omzet), help="Total pendapatan kotor")
        col2.metric("Total Profit", format_rupiah(laba), delta="Net Profit", delta_color="normal")
        col3.metric("Produk Terjual", f"{qty_sold} Unit")
        col4.metric("Total Transaksi", f"{trx_count} Kali")
        
        # 2. Grafik Analisa
        c1, c2 = st.columns(2)
        with c1:
            st.subheader("Tren Penjualan Harian")
            daily = df_trx.groupby('Tanggal')['Total'].sum().reset_index()
            st.area_chart(daily, x='Tanggal', y='Total', color="#2563EB")
            
        with c2:
            st.subheader("Top 5 Produk Terlaris")
            top = df_trx.groupby('Produk')['Qty'].sum().sort_values(ascending=False).head(5)
            st.bar_chart(top, color="#ffaa00")
            
        # 3. Tabel Transaksi Terakhir
        st.write("#### 📜 Riwayat Transaksi Terbaru")
        st.dataframe(
            df_trx.sort_index(ascending=False).head(10), 
            use_container_width=True, 
            hide_index=True,
            column_config={
                "Total": st.column_config.NumberColumn(format="Rp %d"),
                "Laba": st.column_config.NumberColumn(format="Rp %d")
            }
        )
        
    else:
        st.info("Belum ada data transaksi. Silakan lakukan penjualan di menu Kasir.")

# ==============================================================================
# MENU 2: KASIR / POS (Layout Split Screen Modern)
# ==============================================================================
elif selected == "Kasir (POS)":
    # Load Data
    df_produk = load_data(FILE_PRODUK, ['Nama Produk', 'Kategori', 'HPP (Modal)', 'Harga Jual', 'Stok'])
    df_pelanggan = load_data(FILE_PELANGGAN, ['No HP', 'Nama Pelanggan', 'Total Belanja'])

    # Layout: Kiri (Input) 60% - Kanan (Struk) 40%
    col_input, col_struk = st.columns([1.5, 1], gap="medium")

    # --- KOLOM KIRI: INPUT ORDER ---
    with col_input:
        st.subheader("🛍️ Input Pesanan")
        
        # Container Putih untuk Form
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
                if st.button("➕ Masukkan Keranjang", use_container_width=True, type="secondary"):
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
        
        # Container Putih untuk Keranjang
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
                
                # Total Harga
                total_bayar = df_cart['Subtotal'].sum()
                st.markdown("---")
                c_tot1, c_tot2 = st.columns([1,1])
                c_tot1.markdown("#### Total Tagihan:")
                c_tot2.markdown(f"<h3 style='text-align: right; color: #2563EB;'>{format_rupiah(total_bayar)}</h3>", unsafe_allow_html=True)
                
                # Tombol Aksi
                col_batal, col_bayar = st.columns(2)
                with col_batal:
                    if st.button("🗑️ Hapus", use_container_width=True):
                        st.session_state['keranjang'] = []
                        st.rerun()
                
                with col_bayar:
                    if st.button("✅ BAYAR", type="primary", use_container_width=True):
                        # Simpan ke Database
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
                        
                        save_data(FILE_TRANSAKSI, pd.concat([df_log, pd.DataFrame(new_entries)], ignore_index=True))
                        save_data(FILE_PRODUK, df_produk)
                        
                        # Update Loyalty Pelanggan
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
                st.info("Keranjang kosong.")
                st.caption("Silakan pilih produk di sebelah kiri.")

# ==============================================================================
# MENU 3: MANAJEMEN PRODUK (BISA EDIT LANGSUNG)
# ==============================================================================
elif selected == "Produk":
    st.header("📦 Manajemen Produk")
    
    df = load_data(FILE_PRODUK, ['Nama Produk', 'Kategori', 'HPP (Modal)', 'Harga Jual', 'Stok'])
    
    tab1, tab2 = st.tabs(["✏️ Daftar & Edit Produk", "➕ Tambah Produk Baru"])
    
    with tab1:
        st.write("💡 *Klik dua kali pada angka di tabel untuk mengedit langsung.*")
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
        
        if st.button("💾 Simpan Perubahan"):
            save_data(FILE_PRODUK, edited_df)
            st.success("Database produk berhasil diperbarui!")
            st.rerun()
            
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
# MENU 4: DATABASE PELANGGAN
# ==============================================================================
elif selected == "Pelanggan":
    st.header("👥 Database Pelanggan")
    
    df_pel = load_data(FILE_PELANGGAN, ['No HP', 'Nama Pelanggan', 'Total Belanja'])
    
    col_kiri, col_kanan = st.columns([1, 2], gap="large")
    
    with col_kiri:
        with st.container(border=True):
            st.subheader("Tambah Pelanggan")
            with st.form("add_pel"):
                nama = st.text_input("Nama Lengkap")
                hp = st.text_input("No HP / WhatsApp")
                if st.form_submit_button("Simpan Data"):
                    if nama and hp:
                        # Cek duplikasi
                        if hp in df_pel['No HP'].astype(str).values:
                             st.error("No HP sudah terdaftar!")
                        else:
                            new_p = pd.DataFrame([{'No HP': hp, 'Nama Pelanggan': nama, 'Total Belanja': 0}])
                            save_data(FILE_PELANGGAN, pd.concat([df_pel, new_p], ignore_index=True))
                            st.success("Berhasil!")
                            st.rerun()
    
    with col_kanan:
        st.subheader("Daftar Pelanggan Setia")
        st.dataframe(
            df_pel, 
            use_container_width=True,
            column_config={"Total Belanja": st.column_config.NumberColumn(format="Rp %d")}
        )
