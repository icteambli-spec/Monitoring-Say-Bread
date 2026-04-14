import streamlit as st
import pandas as pd
import cloudinary
import cloudinary.uploader
import requests
from io import BytesIO
import time
import json
import math
from datetime import datetime

# ==========================================
# 0. INISIALISASI SESSION STATE
# ==========================================
if 'current_page' not in st.session_state:
    st.session_state.current_page = "Home"

if 'admin_logged_in' not in st.session_state:
    st.session_state.admin_logged_in = False
if 'last_active' not in st.session_state:
    st.session_state.last_active = time.time()

def go_home():
    st.session_state.current_page = "Home"

# ==========================================
# 1. KONFIGURASI HALAMAN & HIDE GITHUB LOGO
# ==========================================
st.set_page_config(page_title="Monitoring Produk Khusus", layout="wide", initial_sidebar_state="collapsed")

hide_st_style = """
            <style>
            #MainMenu {visibility: hidden;}
            header {visibility: hidden;}
            footer {visibility: hidden;}
            .block-container {
                padding-top: 2rem;
                padding-bottom: 0rem;
            }
            </style>
            """
st.markdown(hide_st_style, unsafe_allow_html=True)

# ==========================================
# 2. KONFIGURASI CLOUDINARY
# ==========================================
cloudinary.config(
    cloud_name = st.secrets["CLOUDINARY_CLOUD_NAME"],
    api_key = st.secrets["CLOUDINARY_API_KEY"],
    api_secret = st.secrets["CLOUDINARY_API_SECRET"],
    secure = True
)

PUBLIC_FILE_ID = "data_saybread.xlsx"
PUBLIC_PERIODE_ID = "periode_saybread.json"

# ==========================================
# 3. FUNGSI BANTU
# ==========================================
@st.cache_data(ttl=60)
def get_periode_data():
    cloud_name = st.secrets["CLOUDINARY_CLOUD_NAME"]
    periode_url = f"https://res.cloudinary.com/{cloud_name}/raw/upload/{PUBLIC_PERIODE_ID}?t={int(time.time())}"
    try:
        resp = requests.get(periode_url)
        if resp.status_code == 200:
            return resp.json()
    except:
        pass
    return {}

format_ribuan = {
    "PENJ.BERSIH": "{:,.0f}",
    "RUSAK": "{:,.0f}",
    "%": "{:.2f}",
    "POTENSI RUSAK": "{:,.0f}",
    "QTY POTENSI RUSAK": "{:,.0f}",
    "RP POTENSI RUSAK": "{:,.0f}",
    "SPD": "{:.2f}",
    "DSI": "{:.2f}"
}

periode_dict = get_periode_data()
cloud_name = st.secrets["CLOUDINARY_CLOUD_NAME"]
base_url = f"https://res.cloudinary.com/{cloud_name}/raw/upload/{PUBLIC_FILE_ID}?t={int(time.time())}"


# ==========================================
# HALAMAN 1: HOME (MENU UTAMA)
# ==========================================
if st.session_state.current_page == "Home":
    st.markdown("<h1 style='text-align: center;'>🍞🍗 Monitoring Web Produk Khusus</h1>", unsafe_allow_html=True)
    st.markdown("<h4 style='text-align: center; color: gray;'>Silakan pilih layanan di bawah ini:</h4><br><br>", unsafe_allow_html=True)

    col1, col2, col3 = st.columns(3)
    
    with col1:
        st.info("📊 **Divisi Roti & Pastry**")
        if st.button("🍞 Monitoring Say Bread", use_container_width=True, type="primary"):
            st.session_state.current_page = "Say Bread"
            st.rerun()
            
    with col2:
        st.warning("🍗 **Divisi Fast Food**")
        if st.button("🍗 Monitoring Fried Chicken", use_container_width=True, type="primary"):
            st.session_state.current_page = "Fried Chicken"
            st.rerun()
            
    with col3:
        st.error("⚙️ **Pengaturan Sistem**")
        if st.button("🔐 Halaman Admin", use_container_width=True, type="primary"):
            st.session_state.current_page = "Admin"
            st.rerun()

    st.write("<br><br><br><br>", unsafe_allow_html=True)


# ==========================================
# HALAMAN 2: SAY BREAD
# ==========================================
elif st.session_state.current_page == "Say Bread":
    col_back, col_title = st.columns([1, 10])
    with col_back:
        if st.button("⬅️ Kembali", use_container_width=True): go_home(); st.rerun()
    with col_title:
        st.title("🍞 Portal Monitoring Say Bread")

    tab_resume, tab_monitoring, tab_dsi, tab_rekomendasi = st.tabs([
        "📊 Resume Rusak", "📈 Monitoring Say Bread", "🍞 Cek DSI FD Say Bread", "💡 Rekomendasi Produksi"
    ])

    # --- TAB 1: RESUME RUSAK ---
    with tab_resume:
        st.subheader("Resume Rusak")
        st.markdown(f"#### 📅 Periode Data: `{periode_dict.get('Resume_Rusak', 'Belum diatur')}`")
        input_toko_res = st.text_input("🔍 Filter Kode Toko / Nama AM / Nama AS:", placeholder="Contoh: F08C atau SUNARI", key="sb_res").upper()
        if input_toko_res or st.button("Enter ↵", key="btn_sb_res", type="primary"):
            with st.spinner("Memuat data..."):
                try:
                    resp = requests.get(base_url)
                    if resp.status_code == 200:
                        df_res = pd.read_excel(BytesIO(resp.content), sheet_name='Resume_Rusak')
                        df_res['TOKO'] = df_res['TOKO'].astype(str).str.strip().str.upper()
                        df_res['AM'] = df_res['AM'].fillna("").astype(str).str.strip().str.upper()
                        df_res['AS'] = df_res['AS'].fillna("").astype(str).str.strip().str.upper()

                        if input_toko_res:
                            mask = (df_res['TOKO'] == input_toko_res) | (df_res['AM'].str.contains(input_toko_res)) | (df_res['AS'].str.contains(input_toko_res))
                            filtered = df_res[mask].copy()
                            if filtered.empty: st.warning("Data tidak ditemukan.")
                            else:
                                filtered.insert(0, 'NO', range(1, len(filtered) + 1))
                                st.dataframe(filtered.style.format(format_ribuan), hide_index=True, use_container_width=True)
                        else:
                            st.write("### 👥 Resume Rusak Per AM")
                            df_am = df_res.groupby('AM', as_index=False)[['PENJ.BERSIH', 'RUSAK']].sum()
                            df_am['%'] = (df_am['RUSAK'] / df_am['PENJ.BERSIH']) * 100
                            df_am['%'] = df_am['%'].fillna(0) 
                            df_am = df_am.sort_values(by='%', ascending=False).copy()
                            df_am.insert(0, 'NO', range(1, len(df_am) + 1))
                            st.dataframe(df_am.style.format(format_ribuan), hide_index=True, use_container_width=True)

                            st.write("### 👤 Top 10 Resume Rusak Per AS")
                            df_as = df_res.groupby('AS', as_index=False)[['PENJ.BERSIH', 'RUSAK']].sum()
                            df_as['%'] = (df_as['RUSAK'] / df_as['PENJ.BERSIH']) * 100
                            df_as['%'] = df_as['%'].fillna(0)
                            df_as = df_as.sort_values(by='%', ascending=False).head(10).copy() 
                            df_as.insert(0, 'NO', range(1, len(df_as) + 1))
                            st.dataframe(df_as.style.format(format_ribuan), hide_index=True, use_container_width=True)

                            st.write("### 🏪 Top 10 Resume Rusak Per Toko")
                            df_toko = df_res.sort_values(by='%', ascending=False).head(10).copy()[['TOKO', 'NAMA', 'AM', 'AS', 'PENJ.BERSIH', 'RUSAK', '%']]
                            df_toko.insert(0, 'NO', range(1, len(df_toko) + 1))
                            st.dataframe(df_toko.style.format(format_ribuan), hide_index=True, use_container_width=True)
                except Exception as e: st.error(f"Error: {e}")

    # --- TAB 2: MONITORING ---
    with tab_monitoring:
        st.subheader("Monitoring Data Toko")
        st.markdown(f"#### 📅 Periode Data: `{periode_dict.get('Monitoring', 'Belum diatur')}`")
        input_toko_mon = st.text_input("🔍 Masukkan 4 Digit Kode Toko:", max_chars=4, key="sb_mon").upper()
        if input_toko_mon or st.button("Enter ↵", key="btn_sb_mon", type="primary"):
            if len(input_toko_mon) == 4:
                try:
                    resp = requests.get(base_url)
                    df_mon = pd.read_excel(BytesIO(resp.content), sheet_name='Monitoring')
                    df_mon['Toko'] = df_mon['Toko'].astype(str).str.strip().str.upper()
                    filtered = df_mon[df_mon['Toko'] == input_toko_mon]
                    if not filtered.empty:
                        st.success(f"**Toko:** {filtered.iloc[0]['Nama']} | **AM:** {filtered.iloc[0]['AM']} | **AS:** {filtered.iloc[0]['AS']}")
                        cols = ['PLU Jual', 'Deskripsi', 'Qty Produksi', 'Qty Sales', 'QTY Total Rusak', '% Rusak By Qty', 'Avg Produksi', 'Avg Sales', 'Avg Rusak']
                        display_df = filtered[[c for c in cols if c in filtered.columns]]
                        st.dataframe(display_df, hide_index=True, use_container_width=True, column_config={
                            "% Rusak By Qty": st.column_config.NumberColumn(format="%.2f"),
                            "Avg Produksi": st.column_config.NumberColumn(format="%.2f"),
                            "Avg Sales": st.column_config.NumberColumn(format="%.2f"),
                            "Avg Rusak": st.column_config.NumberColumn(format="%.2f")
                        })
                        out = BytesIO(); filtered.to_excel(out, index=False); st.download_button("📥 Download Excel", data=out.getvalue(), file_name=f"Mon_{input_toko_mon}.xlsx")
                    else: st.warning("Data tidak ditemukan.")
                except Exception as e: st.error(f"Error: {e}")

    # --- TAB 3: DSI FD ---
    with tab_dsi:
        st.subheader("Cek DSI FD Say Bread")
        st.markdown(f"#### 📅 Periode Data: `{periode_dict.get('DSI_FD', 'Belum diatur')}`")
        input_dsi = st.text_input("🔍 Masukkan 4 Digit Kode Toko:", max_chars=4, key="sb_dsi").upper()
        if input_dsi or st.button("Enter ↵", key="btn_sb_dsi", type="primary"):
            try:
                resp = requests.get(base_url)
                df_dsi = pd.read_excel(BytesIO(resp.content), sheet_name='DSI_FD')
                df_dsi['KODE_TOKO'] = df_dsi['KODE_TOKO'].astype(str).str.strip().str.upper()
                if len(input_dsi) == 4:
                    filtered = df_dsi[df_dsi['KODE_TOKO'] == input_dsi].sort_values(by="RP POTENSI RUSAK", ascending=False)
                    if not filtered.empty:
                        st.success(f"**Toko:** {filtered.iloc[0]['NAMA']} | **AM:** {filtered.iloc[0]['AM']} | **AS:** {filtered.iloc[0]['AS']}")
                        cols = ['PLU FD', 'DESC FD', 'Umur Produk', 'SPD', 'DSI', 'POTENSI RUSAK', 'RP POTENSI RUSAK', 'CEK DSI']
                        st.dataframe(filtered[[c for c in cols if c in filtered.columns]].style.format(format_ribuan), hide_index=True, use_container_width=True)
                        out = BytesIO(); filtered.to_excel(out, index=False); st.download_button("📥 Download Excel", data=out.getvalue(), file_name=f"DSI_{input_dsi}.xlsx")
                    else: st.warning("Data tidak ditemukan.")
                else:
                    st.write("### 👥 Resume DSI Per AM")
                    df_am_dsi = df_dsi.groupby('AM', as_index=False)[['POTENSI RUSAK', 'RP POTENSI RUSAK']].sum().sort_values(by="RP POTENSI RUSAK", ascending=False)
                    st.dataframe(df_am_dsi.style.format(format_ribuan), hide_index=True, use_container_width=True)
            except Exception as e: st.error(f"Error: {e}")

    # --- TAB 4: REKOMENDASI ---
    with tab_rekomendasi:
        st.subheader("💡 Rekomendasi Produksi (Interaktif)")
        st.markdown(f"#### 📅 Periode Data: `{periode_dict.get('Rekomendasi', 'Belum diatur')}`")
        input_rek = st.text_input("🔍 Masukkan 4 Digit Kode Toko:", max_chars=4, key="sb_rek").upper()
        if input_rek or st.button("Enter ↵", key="btn_sb_rek", type="primary"):
            if len(input_rek) == 4:
                try:
                    resp = requests.get(base_url)
                    df_rek = pd.read_excel(BytesIO(resp.content), sheet_name='Monitoring')
                    df_rek['Toko'] = df_rek['Toko'].astype(str).str.strip().str.upper()
                    filtered = df_rek[df_rek['Toko'] == input_rek].copy()
                    if not filtered.empty:
                        st.success(f"**Toko:** {filtered.iloc[0]['Nama']} | **AM:** {filtered.iloc[0]['AM']} | **AS:** {filtered.iloc[0]['AS']}")
                        base_df = filtered[['PLU Jual', 'Deskripsi', 'Avg Sales']].copy()
                        base_df['Avg Sales'] = base_df['Avg Sales'].fillna(0)
                        base_df['✍️ Input Sisa Fisik'] = None
                        
                        st.info("👇 Klik ganda pada sel kosong di bawah kolom **[✍️ Input Sisa Fisik]** untuk mengetik angka.")
                        edited_df = st.data_editor(base_df, hide_index=True, use_container_width=True, disabled=['PLU Jual', 'Deskripsi', 'Avg Sales'],
                            column_config={"✍️ Input Sisa Fisik": st.column_config.NumberColumn(min_value=0, step=1), "Avg Sales": st.column_config.NumberColumn(format="%.2f")})

                        def hitung(row):
                            if pd.isna(row['✍️ Input Sisa Fisik']) or row['✍️ Input Sisa Fisik'] is None or row['✍️ Input Sisa Fisik'] == "": return None
                            return max(2, math.ceil((row['Avg Sales'] * 1.05) - float(row['✍️ Input Sisa Fisik'])))

                        edited_df['🎯 Rekomendasi Produksi'] = edited_df.apply(hitung, axis=1)
                        st.markdown("---"); st.write("### 📈 Hasil Akhir Rekomendasi")
                        st.dataframe(edited_df, hide_index=True, use_container_width=True, column_config={"🎯 Rekomendasi Produksi": st.column_config.NumberColumn(format="%d"), "✍️ Input Sisa Fisik": st.column_config.NumberColumn(format="%d")})
                        
                        out = BytesIO(); edited_df.to_excel(out, index=False); st.download_button("📥 Download", data=out.getvalue(), file_name=f"Rek_{input_rek}.xlsx", type="primary")
                    else: st.warning("Data tidak ditemukan.")
                except Exception as e: st.error(f"Error: {e}")


# ==========================================
# HALAMAN 3: FRIED CHICKEN
# ==========================================
elif st.session_state.current_page == "Fried Chicken":
    col_back, col_title = st.columns([1, 10])
    with col_back:
        if st.button("⬅️ Kembali", use_container_width=True): go_home(); st.rerun()
    with col_title:
        st.title("🍗 Portal Monitoring Fried Chicken")

    st.subheader("Cek DSI Raw Fried Chicken")
    st.markdown(f"#### 📅 Periode Data: `{periode_dict.get('DSI_FC', 'Belum diatur')}`")
    
    input_fc = st.text_input("🔍 Masukkan 4 Digit Kode Toko (Kosongkan untuk melihat Resume Default):", max_chars=4, key="fc_dsi").upper()
    if input_fc or st.button("Enter ↵", key="btn_fc_dsi", type="primary"):
        with st.spinner("Memuat data Fried Chicken..."):
            try:
                resp = requests.get(base_url)
                if resp.status_code == 200:
                    df_fc = pd.read_excel(BytesIO(resp.content), sheet_name='DSI_FC')
                    
                    # Pembersihan & Penyesuaian Nama Kolom
                    df_fc['KODE_TOKO'] = df_fc['KODE_TOKO'].astype(str).str.strip().str.upper()
                    df_fc = df_fc.rename(columns={'POTENSI RUSAK': 'QTY POTENSI RUSAK', 'NAMA': 'NAMA TOKO'})

                    if len(input_fc) == 4:
                        # TAMPILAN FILTER (DETAIL PER TOKO)
                        filtered_fc = df_fc[df_fc['KODE_TOKO'] == input_fc].copy()
                        if filtered_fc.empty:
                            st.warning(f"⚠️ Data untuk kode toko '{input_fc}' tidak ditemukan di sheet DSI_FC.")
                        else:
                            st.success(f"✅ Data ditemukan untuk toko: {input_fc}")
                            # Diurutkan berdasarkan RP POTENSI RUSAK tertinggi
                            filtered_fc = filtered_fc.sort_values(by="RP POTENSI RUSAK", ascending=False)
                            
                            kolom_tampil_fc = ['KODE_TOKO', 'NAMA TOKO', 'DSI', 'SPD', 'QTY POTENSI RUSAK', 'RP POTENSI RUSAK']
                            display_df_fc = filtered_fc[[c for c in kolom_tampil_fc if c in filtered_fc.columns]]

                            st.dataframe(display_df_fc.style.format(format_ribuan), hide_index=True, use_container_width=True)
                            
                            # Tombol Download
                            out_fc = BytesIO()
                            with pd.ExcelWriter(out_fc, engine='openpyxl') as writer:
                                filtered_fc.to_excel(writer, index=False, sheet_name='DSI_FriedChicken')
                            st.download_button("📥 Download Data Lengkap (Excel)", data=out_fc.getvalue(), file_name=f"DSI_FC_{input_fc}.xlsx", type="primary")
                    
                    else:
                        # TAMPILAN DEFAULT (RESUME)
                        st.info("📌 Menampilkan Ringkasan DSI FC by Rp Potensi Rusak tertinggi.")
                        
                        # Grouping by AM, AS, KODE_TOKO
                        agg_fc = df_fc.groupby(['AM', 'AS', 'KODE_TOKO'], as_index=False)[['QTY POTENSI RUSAK', 'RP POTENSI RUSAK']].sum()
                        agg_fc = agg_fc.sort_values(by="RP POTENSI RUSAK", ascending=False).copy()
                        
                        # Menyusun urutan kolom yang diminta: AM, AS, KODE_TOKO, QTY POTENSI RUSAK, RP POTENSI RUSAK
                        agg_fc = agg_fc[['AM', 'AS', 'KODE_TOKO', 'QTY POTENSI RUSAK', 'RP POTENSI RUSAK']]
                        agg_fc.insert(0, 'NO', range(1, len(agg_fc) + 1))
                        
                        st.dataframe(agg_fc.style.format(format_ribuan), hide_index=True, use_container_width=True)
                else:
                    st.info("File Master belum diunggah oleh Admin.")
            except ValueError:
                st.error("❌ Sheet bernama 'DSI_FC' tidak ditemukan di file Excel Master!")
            except Exception as e:
                st.error(f"Terjadi kesalahan sistem: {e}")


# ==========================================
# HALAMAN 4: ADMIN AREA
# ==========================================
elif st.session_state.current_page == "Admin":
    col_back, col_title = st.columns([1, 10])
    with col_back:
        if st.button("⬅️ Kembali", use_container_width=True): go_home(); st.rerun()
    with col_title:
        st.title("⚙️ Halaman Pengaturan Admin")

    if st.session_state.admin_logged_in:
        time_elapsed = time.time() - st.session_state.last_active
        if time_elapsed > 300: 
            st.session_state.admin_logged_in = False
            st.warning("⏱️ Sesi Admin telah berakhir (Timeout 5 Menit). Silakan login kembali.")
            time.sleep(2); st.rerun()

    if not st.session_state.admin_logged_in:
        st.subheader("🔐 Login Admin")
        password_input = st.text_input("Masukkan Password Admin:", type="password", key="login_admin_page")
        if st.button("Login", type="primary"):
            if password_input == "icnbr034":
                st.session_state.admin_logged_in = True
                st.session_state.last_active = time.time() 
                st.rerun() 
            else: st.error("❌ Password Salah!")
    else:
        st.session_state.last_active = time.time() 
        col_t, col_l = st.columns([4, 1])
        with col_t: st.success("🔓 Login Berhasil! Selamat datang Admin.")
        with col_l:
            if st.button("🚪 Logout", use_container_width=True, type="primary"):
                st.session_state.admin_logged_in = False; st.rerun()

        st.markdown("---")
        st.write("### 1. Pengaturan Periode Data")
        
        c1, c2, c3 = st.columns(3)
        with c1: p_res = st.date_input("Periode [Resume Rusak]:", []); p_mon = st.date_input("Periode [Monitoring SB]:", [])
        with c2: p_dsi = st.date_input("Periode [DSI SB]:", []); p_rek = st.date_input("Periode [Rekomendasi]:", [])
        with c3: p_fc = st.date_input("Periode [DSI FC]:", []) # Tambahan untuk Fried Chicken

        def fd(d): return f"{d[0].strftime('%d %b %Y')} - {d[1].strftime('%d %b %Y')}" if len(d)==2 else (d[0].strftime('%d %b %Y') if len(d)==1 else "Belum diatur")

        dict_periode_baru = {"Resume_Rusak": fd(p_res), "Monitoring": fd(p_mon), "DSI_FD": fd(p_dsi), "Rekomendasi": fd(p_rek), "DSI_FC": fd(p_fc)}

        if st.button("🔄 Simpan & Perbarui Tanggal Saja", type="secondary"):
            with st.spinner("Menyimpan..."):
                cloudinary.uploader.upload(BytesIO(json.dumps(dict_periode_baru).encode('utf-8')), resource_type="raw", public_id=PUBLIC_PERIODE_ID, overwrite=True, invalidate=True)
                st.success("✅ Tanggal berhasil diperbarui!")

        st.markdown("---")
        st.write("### 2. Upload File Excel Master")
        st.warning("Pastikan file Excel memiliki sheet: **Resume_Rusak**, **Monitoring**, **DSI_FD**, **Rekomendasi**, dan **DSI_FC**.")
        uploaded_file = st.file_uploader("Pilih file Excel", type=["xlsx", "xls"])
        
        if uploaded_file and st.button("📤 Upload Excel & Perbarui Semua", type="primary"):
            with st.spinner("Mengunggah..."):
                cloudinary.uploader.upload(uploaded_file, resource_type="raw", public_id=PUBLIC_FILE_ID, overwrite=True, invalidate=True)
                cloudinary.uploader.upload(BytesIO(json.dumps(dict_periode_baru).encode('utf-8')), resource_type="raw", public_id=PUBLIC_PERIODE_ID, overwrite=True, invalidate=True)
                st.success("✅ File Master Excel dan Periode berhasil diperbarui!")

        st.markdown("---")
        st.write("### 3. Download File Excel Master")
        try:
            resp_raw = requests.get(base_url)
            if resp_raw.status_code == 200:
                st.download_button("📥 DOWNLOAD FILE MASTER SEKARANG (.xlsx)", data=resp_raw.content, file_name="Master_Database_SayBread_FC.xlsx", type="primary")
        except: st.error("Gagal memuat file.")
