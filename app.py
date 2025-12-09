import streamlit as st
import pandas as pd
import os
from datetime import datetime

# ==============================================================================
# 1. SETUP & CSS INJECTION (THE "KAFE SANS" THEME)
# ==============================================================================
st.set_page_config(page_title="Kafe Sans POS", layout="wide", initial_sidebar_state="collapsed")

st.markdown("""
<style>
    /* --- GLOBAL RESET & FONTS --- */
    @import url('https://fonts.googleapis.com/css2?family=Poppins:wght@400;600;700&display=swap');
    
    html, body, [class*="css"] {
        font-family: 'Poppins', sans-serif;
        background-color: #F5F7FB; /* Background abu muda seperti referensi */
    }
    
    /* Hilangkan padding default Streamlit yang besar */
    .block-container {
        padding-top: 1rem;
        padding-bottom: 2rem;
        padding-left: 2rem;
        padding-right: 2rem;
    }

    /* --- CUSTOM COMPONENTS --- */
    
    /* HEADER BAR STYLE */
    .top-bar {
        background-color: #FFFFFF;
        padding: 15px 25px;
        border-radius: 15px;
        box-shadow: 0 2px 10px rgba(0,0,0,0.05);
        margin-bottom: 25px;
        display: flex;
        align-items: center;
        justify-content: space-between;
    }
    .brand-logo {
        font-size: 24px;
        font-weight: 700;
        color: #2C3E50;
    }
    .brand-accent { color: #00C853; } /* Hijau Kafe Sans */

    /* PRODUCT CARD STYLE */
    div[data-testid="stVerticalBlockBorderWrapper"] {
        background-color: #FFFFFF;
        border-radius: 15px;
        box-shadow: 0 4px 15px rgba(0,0,0,0.08);
        border: none; /* Hilangkan border default */
        padding: 0px !important; /* Reset padding container */
        overflow: hidden; /* Agar gambar tidak keluar radius */
        transition: transform 0.2s;
    }
    div[data-testid="stVerticalBlockBorderWrapper"]:hover {
        transform: translateY(-5px);
    }
    
    /* Styling gambar di dalam card */
    div[data-testid="stImage"] img {
        border-radius: 15px 15px 0 0 !important;
        object-fit: cover;
        height: 150px; /* Tinggi gambar tetap */
        width: 100%;
    }
    
    /* Styling Text di dalam card produk */
    .prod-title { font-weight: 600; color: #2C3E50; margin-bottom: 5px; font-size: 1rem;}
    .prod-price { color: #00C853; font-weight: 700; font-size: 1.1rem;}

    /* BUTTON STYLES */
    /* Tombol 'Add' kecil di produk */
    div[data-testid="stVerticalBlockBorderWrapper"] button {
        width: 100%;
        border-radius: 0 0 15px 15px;
        background-color: #F5F7FB;
        color: #2C3E50;
        border: none;
        font-weight: 600;
    }
    div[data-testid="stVerticalBlockBorderWrapper"] button:hover {
        background-color: #e0e7ff;
        color: #00C853;
    }

    /* Tombol Pay Besar (Hijau) */
    .big-green-button > button {
        background-color: #00C853 !important;
        color: white !important;
        font-size: 18px !important;
        font-weight: 700 !important;
        padding: 15px !important;
        border-radius: 12px !important;
        border: none !important;
        box-shadow: 0 4px 10px rgba(0, 200, 83, 0.3);
    }
    .big-green-button > button:hover {
         background-color: #00963F !important;
    }
    
    /* --- RIGHT SIDEBAR (CART) STYLE --- */
    /* Container Order Details */
    .cart-container {
        background-color: #FFFFFF;
        border-radius: 20px;
        padding: 25px;
        height: auto;
        min-height: 600px; /* Agar terlihat penuh ke bawah */
        box-shadow: -5px 0 20px rgba(0,0,0,0.05);
    }
    .cart-header { font-size: 1.2rem; font-weight: 700; color: #2C3E50; margin-bottom: 20px;}
    .customer-info { background-color: #F5F7FB; padding: 15px; border-radius: 10px; margin-bottom: 20px; font-size: 0.9rem;}
    
    /* Cart Item row */
    .cart-item {
        display: flex; justify-content: space-between; align-items: center;
        padding: 10px 0; border-bottom: 1px solid #eee;
    }
    .qty-badge {
        background-color: #2C3E50; color: white; padding: 2px 8px; border-radius: 5px; font-size: 0.8rem; margin-right: 10px;
    }
    
    /* Summary section */
    .summary-row { display: flex; justify-content: space-between; margin-bottom: 10px; color: #7f8c8d; }
    .total-row { display: flex; justify-content: space-between; font-size: 1.3rem; font-weight: 700; color: #2C3E50; margin-top: 20px; margin-bottom: 30px;}

</style>
""", unsafe_allow_html=True)

# ==============================================================================
# 2. DATABASE FUNCTIONS & UTILS
# ==============================================================================
FILE_PRODUK = 'master_produk.csv'
FILE_TRANSAKSI = 'data_transaksi.csv'
FILE_PELANGGAN = 'data_pelanggan.csv'

if 'keranjang' not in st.session_state: st.session_state['keranjang'] = []
if 'selected_category' not in st.session_state: st.session_state['selected_category'] = "All Menu"

def load_data(filename, columns):
    if not os.path.exists(filename):
        df = pd.DataFrame(columns=columns)
        # Khusus produk, tambahkan kolom ImageURL default
        if filename == FILE_PRODUK:
             df['ImageURL'] = "https://source.unsplash.com/random/300x200/?food"
        df.to_csv(filename, index=False)
        return df
    
    df = pd.read_csv(filename)
    # Pastikan kolom ImageURL ada jika file sudah eksis tapi versi lama
    if filename == FILE_PRODUK and 'ImageURL' not in df.columns:
         df['ImageURL'] = "https://source.unsplash.com/random/300x200/?food"
    
    return df

def save_data(filename, df):
    df.to_csv(filename, index=False)

def format_rupiah(angka):
    return f"Rp {angka:,.0f}"

# Load Data Awal
df_produk = load_data(FILE_PRODUK, ['Nama Produk', 'Kategori', 'HPP (Modal)', 'Harga Jual', 'Stok', 'ImageURL'])
df_pelanggan = load_data(FILE_PELANGGAN, ['No HP', 'Nama Pelanggan', 'Total Belanja'])

# ==============================================================================
# 3. LAYOUT UTAMA (Split 70% Kiri, 30% Kanan)
# ==============================================================================

# --- FAKE TOP NAVIGATION BAR (Visual Only) ---
st.markdown("""
    <div class="top-bar">
        <div class="brand-logo">Kafe <span class="brand-accent">Sans</span></div>
        <div style="flex-grow: 1; margin-left: 50px;">
            <input type="text" placeholder="🔍 Search Menu..." style="padding: 10px 20px; border-radius: 10px; border: 1px solid #eee; width: 60%; background-color: #F5F7FB;">
        </div>
        <div style="display: flex; gap: 20px; color: #7f8c8d; font-weight: 600;">
            <span style="color: #00C853; border-bottom: 2px solid #00C853;">Menu</span>
            <span>Reservation</span>
            <span>Delivery</span>
            <span>Accounting</span>
        </div>
        <div style="margin-left: 30px; display: flex; align-items: center;">
            <img src="https://cdn-icons-png.flaticon.com/512/4140/4140048.png" width="40" style="border-radius: 50%; margin-right: 10px;">
            <div>
                <div style="font-weight: 700; color: #2C3E50;">Casey Kaspol</div>
                <div style="font-size: 0.8rem; color: #7f8c8d;">Cashier</div>
            </div>
        </div>
    </div>
""", unsafe_allow_html=True)


# MEMBAGI LAYAR JADI DUA KOLOM BESAR
main_col, cart_col = st.columns([7, 3], gap="large")

# ==============================================================================
# BAGIAN KIRI: MENU & PRODUK GRID
# ==============================================================================
with main_col:
    st.markdown("### Special menu for you")
    
    # --- CATEGORY FILTER (Simpel dulu pakai radio button horizontal) ---
    categories = ["All Menu"] + df_produk['Kategori'].unique().tolist()
    selected_cat = st.radio("Categories", categories, horizontal=True, label_visibility="collapsed")

    # Filter Data Produk
    if selected_cat == "All Menu":
        filtered_df = df_produk[df_produk['Stok'] > 0]
    else:
        filtered_df = df_produk[(df_produk['Kategori'] == selected_cat) & (df_produk['Stok'] > 0)]

    st.markdown("---")

    # --- PRODUCT GRID SYSTEM (The Tricky Part!) ---
    # Kita akan loop data dan membuat 4 kolom per baris
    
    ROWS_PER_GRID = 4
    # Bagi data menjadi chunks (kelompok) berisi 4 produk
    product_chunks = [filtered_df.iloc[i:i + ROWS_PER_GRID] for i in range(0, len(filtered_df), ROWS_PER_GRID)]

    if not filtered_df.empty:
        for chunk in product_chunks:
            cols = st.columns(ROWS_PER_GRID) # Buat 4 kolom
            for i, (_, row) in enumerate(chunk.iterrows()):
                with cols[i]:
                    # --- PRODUCT CARD ---
                    # Kita gunakan container dengan CSS khusus yang sudah dibuat di atas
                    with st.container(border=True): 
                        # Gambar
                        st.image(row['ImageURL'], use_column_width=True)
                        
                        # Teks (Judul & Harga) - Pakai markdown biar rapi
                        st.markdown(f"""
                            <div style="padding: 15px;">
                                <div class="prod-title">{row['Nama Produk']}</div>
                                <div class="prod-price">{format_rupiah(row['Harga Jual'])}</div>
                                <div style="font-size: 0.8rem; color: #7f8c8d;">Stok: {row['Stok']}</div>
                            </div>
                        """, unsafe_allow_html=True)
                        
                        # Tombol Add
                        if st.button("Add to Order ＋", key=f"add_{row['Nama Produk']}", use_container_width=True):
                            # Logika tambah ke keranjang
                            st.session_state['keranjang'].append({
                                "Produk": row['Nama Produk'],
                                "Harga": int(row['Harga Jual']),
                                "Qty": 1,
                                "Modal": int(row['HPP (Modal)'])
                            })
                            st.toast(f"✅ {row['Nama Produk']} ditambahkan!")
                            st.rerun() # Refresh agar keranjang di kanan update
    else:
        st.info("Tidak ada produk tersedia di kategori ini.")
        
    # --- DEBUG: TOMBOL UNTUK RESTOCK/MANAGE DI BAWAH ---
    with st.expander("⚙️ Manajemen Stok & Produk (Admin Only)"):
        st.caption("Gunakan area ini untuk menambah stok atau produk baru karena UI di atas khusus kasir.")
        tab1, tab2 = st.tabs(["Edit Stok/URL Gambar", "Tambah Baru"])
        with tab1:
            edited_df = st.data_editor(df_produk, num_rows="dynamic", key="editor_stok")
            if st.button("Simpan Perubahan Database"):
                save_data(FILE_PRODUK, edited_df)
                st.success("Database diupdate!")
                st.rerun()
        with tab2:
            with st.form("quick_add"):
                n = st.text_input("Nama")
                k = st.selectbox("Kategori", ["Makanan", "Minuman", "Snack"])
                h = st.number_input("Harga Jual", step=1000)
                m = st.number_input("Modal", step=1000)
                s = st.number_input("Stok", value=10)
                img = st.text_input("URL Gambar (Opsional)", placeholder="https://...")
                if st.form_submit_button("Simpan"):
                    img_url = img if img else "https://source.unsplash.com/random/300x200/?food"
                    new_p = pd.DataFrame([{'Nama Produk':n, 'Kategori':k, 'HPP (Modal)':m, 'Harga Jual':h, 'Stok':s, 'ImageURL':img_url}])
                    save_data(FILE_PRODUK, pd.concat([df_produk, new_p], ignore_index=True))
                    st.rerun()


# ==============================================================================
# BAGIAN KANAN: CART & CHECKOUT (SISI GELAP KAFE SANS)
# ==============================================================================
with cart_col:
    # Bungkus semua sisi kanan dalam container putih besar
    st.markdown('<div class="cart-container">', unsafe_allow_html=True)
    
    st.markdown('<div class="cart-header">Order Details 🧾</div>', unsafe_allow_html=True)
    
    # --- CUSTOMER INFO (Fake dulu biar mirip referensi) ---
    st.markdown("""
        <div class="customer-info">
            <div><strong>Recipient:</strong> Yolanda Tamara (Guest)</div>
            <div style="color: #7f8c8d; font-size: 0.8rem;">Mon, Oct 16, 2023, 12:00</div>
            <div style="color: #00C853; font-weight: 600;">#ORDER-00234</div>
        </div>
    """, unsafe_allow_html=True)
    
    st.markdown("---")

    # --- CART ITEMS LIST ---
    if len(st.session_state['keranjang']) > 0:
        # Grouping items (agar kalau klik 2x, qty jadi 2, bukan list panjang)
        df_cart_raw = pd.DataFrame(st.session_state['keranjang'])
        df_cart_grouped = df_cart_raw.groupby(['Produk', 'Harga', 'Modal']).size().reset_index(name='Qty')
        
        total_subtotal = 0
        
        # Loop untuk menampilkan item di keranjang
        for index, item in df_cart_grouped.iterrows():
            item_subtotal = item['Harga'] * item['Qty']
            total_subtotal += item_subtotal
            
            st.markdown(f"""
                <div class="cart-item">
                    <div style="display: flex; align-items: center;">
                        <span class="qty-badge">{item['Qty']}x</span>
                        <span style="font-weight: 600; color: #2C3E50;">{item['Produk']}</span>
                    </div>
                    <div style="font-weight: 600;">{format_rupiah(item_subtotal)}</div>
                </div>
            """, unsafe_allow_html=True)
            # Catatan: Fitur remove per item/edit qty sulit di UI ini, kita pakai tombol "Clear All" dulu.

        st.markdown("---")
        
        # --- SUMMARY SECTION ---
        tax = total_subtotal * 0.11 # PPN 11% ceritanya
        discount = 0 # Belum ada fitur diskon
        grand_total = total_subtotal + tax - discount
        
        st.markdown(f"""
            <div class="summary-row"><span>Subtotal</span> <span>{format_rupiah(total_subtotal)}</span></div>
            <div class="summary-row"><span>Tax (11%)</span> <span>{format_rupiah(tax)}</span></div>
            <div class="summary-row"><span>Discount</span> <span>- {format_rupiah(discount)}</span></div>
            <div class="total-row"><span>Total</span> <span>{format_rupiah(grand_total)}</span></div>
        """, unsafe_allow_html=True)
        
        # --- TOMBOL BAYAR (BIG GREEN BUTTON) ---
        # Kita bungkus dengan class khusus biar warnanya hijau
        st.markdown('<div class="big-green-button">', unsafe_allow_html=True)
        if st.button(f"Pay {format_rupiah(grand_total)} 💸", use_container_width=True):
            # --- PROSES PEMBAYARAN ---
            df_log = load_data(FILE_TRANSAKSI, ['Tanggal', 'Pelanggan', 'Produk', 'Qty', 'Total', 'Modal', 'Laba'])
            new_entries = []
            
            for _, item in df_cart_grouped.iterrows():
                # Kurangi Stok di DB Utama
                idx = df_produk[df_produk['Nama Produk'] == item['Produk']].index[0]
                df_produk.at[idx, 'Stok'] -= item['Qty']
                
                # Catat Log
                new_entries.append({
                    'Tanggal': datetime.now(),
                    'Pelanggan': "Yolanda Tamara (Guest)", # Hardcoded dulu sesuai UI
                    'Produk': item['Produk'],
                    'Qty': item['Qty'],
                    'Total': item['Harga'] * item['Qty'],
                    'Modal': item['Modal'] * item['Qty'],
                    'Laba': (item['Harga'] - item['Modal']) * item['Qty']
                })

            save_data(FILE_TRANSAKSI, pd.concat([df_log, pd.DataFrame(new_entries)], ignore_index=True))
            save_data(FILE_PRODUK, df_produk) # Simpan stok baru
            
            st.session_state['keranjang'] = [] # Kosongkan keranjang
            st.balloons()
            st.success("Payment Success!")
            st.rerun()
            
        st.markdown('</div>', unsafe_allow_html=True) # Tutup div big-green-button
        
        # Tombol Clear Cart kecil di bawah
        if st.button("❌ Clear Order", type="secondary", use_container_width=True):
             st.session_state['keranjang'] = []
             st.rerun()

    else:
        # Tampilan saat keranjang kosong
        st.markdown("""
            <div style="text-align: center; padding: 50px 0; color: #bdc3c7;">
                <img src="https://cdn-icons-png.flaticon.com/512/2038/2038854.png" width="80" style="margin-bottom: 20px; opacity: 0.5;">
                <p>No items selected yet.</p>
                <p style="font-size: 0.8rem;">Click "Add" on menus to start ordering.</p>
            </div>
        """, unsafe_allow_html=True)

    st.markdown('</div>', unsafe_allow_html=True) # Tutup cart-container
