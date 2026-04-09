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
if 'admin_logged_in' not in st.session_state:
    st.session_state.admin_logged_in = False
if 'last_active' not in st.session_state:
    st.session_state.last_active = time.time()

if 'dl_logged_in' not in st.session_state:
    st.session_state.dl_logged_in = False
if 'dl_last_active' not in st.session_state:
    st.session_state.dl_last_active = time.time()

# ==========================================
# 1. KONFIGURASI HALAMAN & HIDE GITHUB LOGO
# ==========================================
st.set_page_config(page_title="Web Say Bread", layout="wide")

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

st.title("🍞 Monitoring Say Bread")

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
    "RP POTENSI RUSAK": "{:,.0f}",
    "SPD": "{:.2f}",
    "DSI": "{:.2f}"
}

# ==========================================
# 4. MENU UTAMA MENGGUNAKAN TABS
# ==========================================
tab_resume, tab_monitoring, tab_dsi, tab_rekomendasi, tab_download, tab_admin = st.tabs([
    "📊 Resume Rusak", 
    "📈 Monitoring Say Bread", 
    "🍞 Cek DSI FD Say Bread", 
    "💡 Rekomendasi Produksi",
    "📥 Download Master", 
    "🔐 Admin"
])

periode_dict = get_periode_data()
cloud_name = st.secrets["CLOUDINARY_CLOUD_NAME"]
base_url = f"https://res.cloudinary.com/{cloud_name}/raw/upload/{PUBLIC_FILE_ID}?t={int(time.time())}"


# ------------------------------------------
# ISI TAB 1: RESUME RUSAK PER TOKO
# ------------------------------------------
with tab_resume:
    st.subheader("Resume Rusak")
    st.markdown(f"#### 📅 Periode Data: `{periode_dict.get('Resume_Rusak', 'Belum diatur')}`")
    st.write("")

    input_toko_res = st.text_input("🔍 Filter Kode Toko / Nama AM / Nama AS:", placeholder="Contoh: F08C atau SNI", key="input_res").upper()
    btn_enter_res = st.button("Enter ↵", key="btn_res", type="primary")

    with st.spinner("Memuat data..."):
        try:
            resp_res = requests.get(base_url)
            if resp_res.status_code == 200:
                df_res = pd.read_excel(BytesIO(resp_res.content), sheet_name='Resume_Rusak')
                df_res['TOKO'] = df_res['TOKO'].astype(str).str.strip().str.upper()
                df_res['AM'] = df_res['AM'].fillna("").astype(str).str.strip().str.upper()
                df_res['AS'] = df_res['AS'].fillna("").astype(str).str.strip().str.upper()

                if input_toko_res or btn_enter_res:
                    mask = (df_res['TOKO'] == input_toko_res) | (df_res['AM'].str.contains(input_toko_res)) | (df_res['AS'].str.contains(input_toko_res))
                    filtered_res = df_res[mask].copy()
                    
                    if filtered_res.empty:
                        st.warning(f"⚠️ Data untuk kata kunci '{input_toko_res}' tidak ditemukan.")
                    else:
                        st.success(f"✅ Menampilkan detail data untuk: {input_toko_res} ({len(filtered_res)} Toko ditemukan)")
                        filtered_res.insert(0, 'NO', range(1, len(filtered_res) + 1))
                        st.dataframe(filtered_res.style.format(format_ribuan), hide_index=True, use_container_width=True)
                else:
                    st.info("📌 Menampilkan Ringkasan (Resume) Data Kerusakan by Presentase (%).")
                    
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
                    df_toko = df_res.sort_values(by='%', ascending=False).head(10).copy()
                    df_toko = df_toko[['TOKO', 'NAMA', 'AM', 'AS', 'PENJ.BERSIH', 'RUSAK', '%']]
                    df_toko.insert(0, 'NO', range(1, len(df_toko) + 1))
                    st.dataframe(df_toko.style.format(format_ribuan), hide_index=True, use_container_width=True)
            else:
                st.info("ℹ️ Belum ada data sumber yang diunggah oleh Admin.")
        except Exception as e:
            st.error(f"Terjadi kesalahan sistem: {e}")


# ------------------------------------------
# ISI TAB 2: MONITORING SAY BREAD
# ------------------------------------------
with tab_monitoring:
    st.subheader("Monitoring Produksi, Sales, Rusak Per Toko")
    st.markdown(f"#### 📅 Periode Data: `{periode_dict.get('Monitoring', 'Belum diatur')}`")
    st.write("")

    input_toko_mon = st.text_input("🔍 Masukkan 4 Digit Kode Toko:", max_chars=4, placeholder="Contoh: F08C", key="input_mon").upper()
    btn_enter_mon = st.button("Enter ↵", key="btn_mon", type="primary")

    if input_toko_mon or btn_enter_mon:
        if len(input_toko_mon) < 4:
            st.error("⚠️ Error: Kode toko harus terdiri dari 4 digit alfanumerik!")
        elif len(input_toko_mon) == 4:
            with st.spinner("Memuat data..."):
                try:
                    resp_mon = requests.get(base_url)
                    if resp_mon.status_code == 200:
                        df_mon = pd.read_excel(BytesIO(resp_mon.content), sheet_name='Monitoring')
                        df_mon['Toko'] = df_mon['Toko'].astype(str).str.strip().str.upper()
                        filtered_mon = df_mon[df_mon['Toko'] == input_toko_mon]

                        if filtered_mon.empty:
                            st.warning(f"⚠️ Data tidak ditemukan.")
                        else:
                            st.markdown("---")
                            col1, col2, col3 = st.columns(3)
                            with col1: st.success(f"**🏷️ Nama Toko:**\n\n{filtered_mon.iloc[0]['Nama']}")
                            with col2: st.info(f"**👤 AM:**\n\n{filtered_mon.iloc[0]['AM']}")
                            with col3: st.warning(f"**👥 AS:**\n\n{filtered_mon.iloc[0]['AS']}")
                            
                            st.write("")
                            kolom_tampil = ['PLU Jual', 'Deskripsi', 'Qty Produksi', 'Qty Sales', 'QTY Total Rusak', '% Rusak By Qty', 'Avg Produksi', 'Avg Sales', 'Avg Rusak']
                            display_df = filtered_mon[[col for col in kolom_tampil if col in filtered_mon.columns]]

                            st.dataframe(display_df, hide_index=True, use_container_width=True, column_config={
                                "% Rusak By Qty": st.column_config.NumberColumn(format="%.2f"),
                                "Avg Produksi": st.column_config.NumberColumn(format="%.2f"),
                                "Avg Sales": st.column_config.NumberColumn(format="%.2f"),
                                "Avg Rusak": st.column_config.NumberColumn(format="%.2f")
                            })
                            
                            output = BytesIO()
                            with pd.ExcelWriter(output, engine='openpyxl') as writer:
                                filtered_mon.to_excel(writer, index=False, sheet_name='Monitoring')
                            st.download_button("📥 Download Data Lengkap (Excel)", data=output.getvalue(), file_name=f"Monitoring_{input_toko_mon}.xlsx")
                except Exception as e:
                    st.error(f"Terjadi kesalahan sistem: {e}")


# ------------------------------------------
# ISI TAB 3: CEK DSI FD SAY BREAD
# ------------------------------------------
with tab_dsi:
    st.subheader("Cek DSI FD Say Bread")
    st.markdown(f"#### 📅 Periode Data: `{periode_dict.get('DSI_FD', 'Belum diatur')}`")
    st.write("")

    input_toko_dsi = st.text_input("🔍 Masukkan 4 Digit Kode Toko:", max_chars=4, placeholder="Contoh: F08C", key="input_dsi").upper()
    btn_enter_dsi = st.button("Enter ↵", key="btn_dsi", type="primary")

    with st.spinner("Memuat data..."):
        try:
            resp_dsi = requests.get(base_url)
            if resp_dsi.status_code == 200:
                df_dsi = pd.read_excel(BytesIO(resp_dsi.content), sheet_name='DSI_FD')
                df_dsi['KODE_TOKO'] = df_dsi['KODE_TOKO'].astype(str).str.strip().str.upper()

                if input_toko_dsi or btn_enter_dsi:
                    if len(input_toko_dsi) < 4:
                        st.error("⚠️ Error: Kode toko harus terdiri dari 4 digit alfanumerik!")
                    else:
                        filtered_dsi = df_dsi[df_dsi['KODE_TOKO'] == input_toko_dsi].copy()
                        if filtered_dsi.empty:
                            st.warning(f"⚠️ Data tidak ditemukan.")
                        else:
                            st.markdown("---")
                            col1, col2, col3 = st.columns(3)
                            with col1: st.success(f"**🏷️ Nama Toko:**\n\n{filtered_dsi.iloc[0]['NAMA']}")
                            with col2: st.info(f"**👤 AM:**\n\n{filtered_dsi.iloc[0]['AM']}")
                            with col3: st.warning(f"**👥 AS:**\n\n{filtered_dsi.iloc[0]['AS']}")
                            
                            st.write("")
                            filtered_dsi = filtered_dsi.sort_values(by="RP POTENSI RUSAK", ascending=False)
                            kolom_tampil_dsi = ['PLU FD', 'DESC FD', 'Umur Produk', 'SPD', 'DSI', 'POTENSI RUSAK', 'RP POTENSI RUSAK', 'CEK DSI']
                            display_df_dsi = filtered_dsi[[col for col in kolom_tampil_dsi if col in filtered_dsi.columns]]

                            st.dataframe(display_df_dsi.style.format(format_ribuan), hide_index=True, use_container_width=True)
                            
                            output_dsi = BytesIO()
                            with pd.ExcelWriter(output_dsi, engine='openpyxl') as writer:
                                filtered_dsi.to_excel(writer, index=False, sheet_name='DSI')
                            st.download_button("📥 Download Data Lengkap (Excel)", data=output_dsi.getvalue(), file_name=f"DSI_{input_toko_dsi}.xlsx")
                else:
                    st.info("📌 Menampilkan Ringkasan (Resume) DSI by Rp Potensi Rusak tertinggi.")
                    st.write("### 👥 Resume DSI Per AM")
                    df_am_dsi = df_dsi.groupby('AM', as_index=False)[['POTENSI RUSAK', 'RP POTENSI RUSAK']].sum().sort_values(by="RP POTENSI RUSAK", ascending=False).copy()
                    df_am_dsi.insert(0, 'NO', range(1, len(df_am_dsi) + 1))
                    st.dataframe(df_am_dsi.style.format(format_ribuan), hide_index=True, use_container_width=True)

                    st.write("### 👤 Top 10 Resume DSI Per AS")
                    df_as_dsi = df_dsi.groupby('AS', as_index=False)[['POTENSI RUSAK', 'RP POTENSI RUSAK']].sum().sort_values(by="RP POTENSI RUSAK", ascending=False).head(10).copy()
                    df_as_dsi.insert(0, 'NO', range(1, len(df_as_dsi) + 1))
                    st.dataframe(df_as_dsi.style.format(format_ribuan), hide_index=True, use_container_width=True)

                    st.write("### 🏪 Top 10 Resume DSI Per Toko")
                    agg_dsi = df_dsi.groupby(['KODE_TOKO', 'NAMA', 'AM', 'AS'], as_index=False)[['POTENSI RUSAK', 'RP POTENSI RUSAK']].sum().sort_values(by="RP POTENSI RUSAK", ascending=False).head(10).copy()
                    agg_dsi.insert(0, 'NO', range(1, len(agg_dsi) + 1))
                    st.dataframe(agg_dsi.style.format(format_ribuan), hide_index=True, use_container_width=True)
        except Exception as e:
            st.error(f"Terjadi kesalahan sistem: {e}")


# ------------------------------------------
# ISI TAB 4: REKOMENDASI PRODUKSI (DENGAN INTERAKSI OTOMATIS)
# ------------------------------------------
with tab_rekomendasi:
    st.subheader("💡 Rekomendasi Produksi (Interaktif)")
    st.markdown(f"#### 📅 Periode Data: `{periode_dict.get('Rekomendasi', 'Belum diatur')}`")
    st.write("")

    input_toko_rek = st.text_input("🔍 Masukkan 4 Digit Kode Toko:", max_chars=4, placeholder="Contoh: F08C", key="input_rek").upper()
    btn_enter_rek = st.button("Enter ↵", key="btn_rek", type="primary")

    if input_toko_rek or btn_enter_rek:
        if len(input_toko_rek) < 4:
            st.error("⚠️ Error: Kode toko harus terdiri dari 4 digit alfanumerik!")
        elif len(input_toko_rek) == 4:
            with st.spinner("Memuat data..."):
                try:
                    resp_rek = requests.get(base_url)
                    if resp_rek.status_code == 200:
                        df_rek = pd.read_excel(BytesIO(resp_rek.content), sheet_name='Monitoring')
                        df_rek['Toko'] = df_rek['Toko'].astype(str).str.strip().str.upper()
                        filtered_rek = df_rek[df_rek['Toko'] == input_toko_rek].copy()

                        if filtered_rek.empty:
                            st.warning(f"⚠️ Data untuk kode toko '{input_toko_rek}' tidak ditemukan.")
                        else:
                            st.markdown("---")
                            col1, col2, col3 = st.columns(3)
                            with col1: st.success(f"**🏷️ Nama Toko:**\n\n{filtered_rek.iloc[0]['Nama']}")
                            with col2: st.info(f"**👤 AM:**\n\n{filtered_rek.iloc[0]['AM']}")
                            with col3: st.warning(f"**👥 AS:**\n\n{filtered_rek.iloc[0]['AS']}")
                            
                            st.write("")
                            st.info("👇 **PANDUAN:** Silakan klik dua kali pada kolom **[ ✍️ Input Sisa Fisik ]** di tabel bawah ini untuk mengubah angka. Kolom **[ 🎯 Rekomendasi Produksi ]** akan otomatis menghitung hasilnya.")

                            # Siapkan Data Dasar
                            base_df = filtered_rek[['PLU Jual', 'Deskripsi', 'Avg Sales']].copy()
                            base_df['Avg Sales'] = base_df['Avg Sales'].fillna(0)
                            
                            # Buat kolom baru untuk diinput user (Default = 0)
                            base_df['✍️ Input Sisa Fisik'] = 0

                            # Render Tabel Interaktif (Data Editor)
                            edited_df = st.data_editor(
                                base_df,
                                column_config={
                                    "✍️ Input Sisa Fisik": st.column_config.NumberColumn(
                                        min_value=0, 
                                        step=1, 
                                        format="%d"
                                    ),
                                    "Avg Sales": st.column_config.NumberColumn(format="%.2f")
                                },
                                disabled=['PLU Jual', 'Deskripsi', 'Avg Sales'], # Kolom ini dikunci agar tidak bisa diedit
                                hide_index=True,
                                use_container_width=True
                            )

                            # LOGIKA PERHITUNGAN RUMUS OTOMATIS
                            def hitung_rekomendasi(row):
                                avg_sales = row['Avg Sales']
                                sisa_fisik = row['✍️ Input Sisa Fisik']
                                # Rumus = MAX(2, ROUNDUP(Avg Sales * 1.05 - Sisa Fisik))
                                kalkulasi = (avg_sales * 0.05) - sisa_fisik
                                rekomendasi = max(2, math.ceil(kalkulasi))
                                return rekomendasi

                            # Menambahkan hasil perhitungan ke DataFrame
                            edited_df['🎯 Rekomendasi Produksi'] = edited_df.apply(hitung_rekomendasi, axis=1)

                            st.markdown("---")
                            st.write("### 📈 Hasil Akhir Rekomendasi")
                            st.dataframe(
                                edited_df[['PLU Jual', 'Deskripsi', 'Avg Sales', '✍️ Input Sisa Fisik', '🎯 Rekomendasi Produksi']], 
                                hide_index=True, 
                                use_container_width=True
                            )

                            # Download Hasil Kalkulasi
                            output_rek = BytesIO()
                            with pd.ExcelWriter(output_rek, engine='openpyxl') as writer:
                                edited_df.to_excel(writer, index=False, sheet_name='Rekomendasi')
                            excel_data_rek = output_rek.getvalue()

                            st.download_button(
                                label="📥 Download Hasil Rekomendasi (Excel)",
                                data=excel_data_rek,
                                file_name=f"Rekomendasi_Produksi_{input_toko_rek}.xlsx",
                                mime="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet",
                                type="primary"
                            )
                except Exception as e:
                    st.error(f"Terjadi kesalahan sistem: {e}")


# ------------------------------------------
# ISI TAB 5: DOWNLOAD MASTER (DIKUNCI & TIMEOUT)
# ------------------------------------------
with tab_download:
    if st.session_state.dl_logged_in:
        time_elapsed_dl = time.time() - st.session_state.dl_last_active
        if time_elapsed_dl > 300: 
            st.session_state.dl_logged_in = False
            st.warning("⏱️ Sesi Download telah berakhir (Timeout 5 Menit). Silakan login kembali.")
            time.sleep(2)
            st.rerun()

    if not st.session_state.dl_logged_in:
        st.subheader("🔐 Login Download Master")
        pass_master = st.text_input("Password Download:", type="password", key="pass_master")
        if st.button("Login", key="btn_login_dl", type="primary"):
            if pass_master == "321":
                st.session_state.dl_logged_in = True
                st.session_state.dl_last_active = time.time()
                st.rerun()
            else:
                st.error("❌ Password Salah!")
                
    else:
        st.session_state.dl_last_active = time.time() 
        col_dl_title, col_dl_logout = st.columns([4, 1])
        with col_dl_title:
            st.subheader("📥 Download File Excel Master")
            st.success("🔓 Akses Diberikan!")
        with col_dl_logout:
            st.write("")
            if st.button("🚪 Logout", key="btn_logout_dl", type="primary"):
                st.session_state.dl_logged_in = False
                st.rerun()

        st.markdown("---")
        st.write("Klik tombol di bawah untuk mengunduh seluruh database master Excel.")
        
        try:
            resp_raw = requests.get(base_url)
            if resp_raw.status_code == 200:
                st.download_button("📥 DOWNLOAD FILE MASTER (.xlsx)", data=resp_raw.content, file_name="Master_Database_SayBread.xlsx", type="primary")
            else:
                st.info("File master belum diunggah oleh Admin.")
        except Exception as e:
            st.error("Gagal mengambil file.")


# ------------------------------------------
# ISI TAB 6: ADMIN AREA
# ------------------------------------------
with tab_admin:
    if st.session_state.admin_logged_in:
        time_elapsed = time.time() - st.session_state.last_active
        if time_elapsed > 300: 
            st.session_state.admin_logged_in = False
            st.warning("⏱️ Sesi Admin telah berakhir (Timeout 5 Menit). Silakan login kembali.")
            time.sleep(2) 
            st.rerun()

    if not st.session_state.admin_logged_in:
        st.subheader("🔐 Login Admin")
        password_input = st.text_input("Masukkan Password Admin:", type="password", key="login_pass")
        if st.button("Login", key="btn_login_admin", type="primary"):
            if password_input == "icnbr034":
                st.session_state.admin_logged_in = True
                st.session_state.last_active = time.time() 
                st.rerun() 
            else:
                st.error("❌ Password Salah!")
    else:
        st.session_state.last_active = time.time() 
        col_title, col_logout = st.columns([4, 1])
        with col_title:
            st.subheader("⚙️ Dashboard Admin")
            st.success("🔓 Login Berhasil! Selamat datang Admin.")
        with col_logout:
            st.write("") 
            if st.button("🚪 Logout", key="btn_logout_admin", type="primary"):
                st.session_state.admin_logged_in = False
                st.rerun()

        st.markdown("---")
        st.write("### 1. Pengaturan Periode Data")
        
        col_p1, col_p2 = st.columns(2)
        with col_p1:
            p_res = st.date_input("Periode [Resume Rusak]:", [])
            p_mon = st.date_input("Periode [Monitoring]:", [])
        with col_p2:
            p_dsi = st.date_input("Periode [DSI FD]:", [])
            p_rek = st.date_input("Periode [Rekomendasi]:", [])

        def format_date(d_input):
            if len(d_input) == 2: return f"{d_input[0].strftime('%d %B %Y')} - {d_input[1].strftime('%d %B %Y')}"
            elif len(d_input) == 1: return f"{d_input[0].strftime('%d %B %Y')}"
            return "Belum diatur"

        dict_periode_baru = {"Resume_Rusak": format_date(p_res), "Monitoring": format_date(p_mon), "DSI_FD": format_date(p_dsi), "Rekomendasi": format_date(p_rek)}

        if st.button("🔄 Simpan & Perbarui Tanggal Saja", type="secondary"):
            with st.spinner("Memperbarui tanggal..."):
                json_periode = json.dumps(dict_periode_baru)
                cloudinary.uploader.upload(BytesIO(json_periode.encode('utf-8')), resource_type="raw", public_id=PUBLIC_PERIODE_ID, overwrite=True, invalidate=True)
                st.success("✅ Tanggal berhasil diperbarui!")

        st.markdown("---")
        st.write("### 2. Upload File Excel Master")
        uploaded_file = st.file_uploader("Pilih file Excel", type=["xlsx", "xls"], key="uploader")
        
        if uploaded_file is not None:
            if st.button("📤 Upload Excel & Perbarui Semua", type="primary"):
                with st.spinner("Mengunggah..."):
                    cloudinary.uploader.upload(uploaded_file, resource_type="raw", public_id=PUBLIC_FILE_ID, overwrite=True, invalidate=True)
                    json_periode = json.dumps(dict_periode_baru)
                    cloudinary.uploader.upload(BytesIO(json_periode.encode('utf-8')), resource_type="raw", public_id=PUBLIC_PERIODE_ID, overwrite=True, invalidate=True)
                    st.success("✅ File Master Excel dan Periode berhasil diperbarui!")
