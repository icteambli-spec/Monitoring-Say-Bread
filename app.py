import streamlit as st
import pandas as pd
import cloudinary
import cloudinary.uploader
import requests
from io import BytesIO
import time
import json
from datetime import datetime

# ==========================================
# 0. INISIALISASI SESSION STATE (UNTUK LOGIN ADMIN & TIMEOUT)
# ==========================================
if 'admin_logged_in' not in st.session_state:
    st.session_state.admin_logged_in = False
if 'last_active' not in st.session_state:
    st.session_state.last_active = time.time()

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
    st.subheader("Resume Rusak Per Toko")
    st.markdown(f"#### 📅 Periode Data: `{periode_dict.get('Resume_Rusak', 'Belum diatur')}`")
    st.write("")

    input_toko_res = st.text_input("🔍 Filter 4 Digit Kode Toko (Kosongkan untuk melihat Top 20):", max_chars=4, placeholder="Contoh: F08C", key="input_res").upper()
    btn_enter_res = st.button("Enter ↵", key="btn_res", type="primary")

    with st.spinner("Memuat data..."):
        try:
            resp_res = requests.get(base_url)
            if resp_res.status_code == 200:
                df_res = pd.read_excel(BytesIO(resp_res.content), sheet_name='Resume_Rusak')
                df_res['TOKO'] = df_res['TOKO'].astype(str).str.strip().str.upper()

                if input_toko_res or btn_enter_res:
                    if len(input_toko_res) < 4:
                        st.error("⚠️ Error: Kode toko harus terdiri dari 4 digit alfanumerik!")
                    else:
                        filtered_res = df_res[df_res['TOKO'] == input_toko_res].copy()
                        if filtered_res.empty:
                            st.warning(f"⚠️ Data untuk kode toko '{input_toko_res}' tidak ditemukan.")
                        else:
                            st.success(f"✅ Data ditemukan untuk toko: {input_toko_res}")
                            st.dataframe(filtered_res.style.format(format_ribuan), hide_index=True, use_container_width=True)
                else:
                    st.info("📌 Menampilkan Top 20 Toko dengan nilai Rusak tertinggi (by Rupiah).")
                    top_20_df = df_res.sort_values(by="RUSAK", ascending=False).head(20).copy()
                    top_20_df.insert(0, 'NO', range(1, len(top_20_df) + 1))
                    st.dataframe(top_20_df.style.format(format_ribuan), hide_index=True, use_container_width=True)
            else:
                st.info("ℹ️ Belum ada data sumber yang diunggah oleh Admin.")
        except ValueError:
            st.error("❌ Sheet bernama 'Resume_Rusak' tidak ditemukan di file Excel Master!")
        except Exception as e:
            st.error(f"Terjadi kesalahan sistem: {e}")


# ------------------------------------------
# ISI TAB 2: MONITORING SAY BREAD
# ------------------------------------------
with tab_monitoring:
    st.subheader("Monitoring Data Toko")
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
                            st.warning(f"⚠️ Data untuk kode toko '{input_toko_mon}' tidak ditemukan di sheet Monitoring.")
                        else:
                            st.markdown("---")
                            nama_toko = filtered_mon.iloc[0]['Nama']
                            am_toko = filtered_mon.iloc[0]['AM']
                            as_toko = filtered_mon.iloc[0]['AS']

                            col1, col2, col3 = st.columns(3)
                            with col1: st.success(f"**🏷️ Nama Toko:**\n\n{nama_toko}")
                            with col2: st.info(f"**👤 AM:**\n\n{am_toko}")
                            with col3: st.warning(f"**👥 AS:**\n\n{as_toko}")
                            
                            st.write("")
                            kolom_tampil = [
                                'PLU Jual', 'Deskripsi', 'Qty Produksi', 'Qty Sales', 
                                'QTY Total Rusak', '% Rusak By Qty', 'Avg Produksi', 
                                'Avg Sales', 'Avg Rusak'
                            ]
                            
                            kolom_tersedia = [col for col in kolom_tampil if col in filtered_mon.columns]
                            display_df = filtered_mon[kolom_tersedia]

                            st.write(f"**Tabel Data Item - {nama_toko}**")
                            st.dataframe(
                                display_df, hide_index=True, use_container_width=True,
                                column_config={
                                    "% Rusak By Qty": st.column_config.NumberColumn(format="%.2f"),
                                    "Avg Produksi": st.column_config.NumberColumn(format="%.2f"),
                                    "Avg Sales": st.column_config.NumberColumn(format="%.2f"),
                                    "Avg Rusak": st.column_config.NumberColumn(format="%.2f")
                                }
                            )

                            st.markdown("<br>", unsafe_allow_html=True)
                            
                            output = BytesIO()
                            with pd.ExcelWriter(output, engine='openpyxl') as writer:
                                filtered_mon.to_excel(writer, index=False, sheet_name='Monitoring_Toko')
                            excel_data = output.getvalue()

                            st.download_button(
                                label=f"📥 Download Data Lengkap {input_toko_mon} (Excel)",
                                data=excel_data,
                                file_name=f"Monitoring_SayBread_{input_toko_mon}.xlsx",
                                mime="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet"
                            )
                    else:
                        st.info("ℹ️ Belum ada data sumber yang diunggah oleh Admin.")
                except ValueError:
                    st.error("❌ Sheet bernama 'Monitoring' tidak ditemukan di file Excel Master!")
                except Exception as e:
                    st.error(f"Terjadi kesalahan sistem: {e}")


# ------------------------------------------
# ISI TAB 3: CEK DSI FD SAY BREAD
# ------------------------------------------
with tab_dsi:
    st.subheader("Cek DSI FD Say Bread")
    st.markdown(f"#### 📅 Periode Data: `{periode_dict.get('DSI_FD', 'Belum diatur')}`")
    st.write("")

    input_toko_dsi = st.text_input("🔍 Masukkan 4 Digit Kode Toko Untuk Melihat Detail Item Per Toko (Kosongkan untuk melihat Top 10 Toko Rusak Tertinggi):", max_chars=4, placeholder="Contoh: F08C", key="input_dsi").upper()
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
                            st.warning(f"⚠️ Data untuk kode toko '{input_toko_dsi}' tidak ditemukan di sheet DSI_FD.")
                        else:
                            st.markdown("---")
                            nama_toko_dsi = filtered_dsi.iloc[0]['NAMA']
                            am_toko_dsi = filtered_dsi.iloc[0]['AM']
                            as_toko_dsi = filtered_dsi.iloc[0]['AS']

                            col1, col2, col3 = st.columns(3)
                            with col1: st.success(f"**🏷️ Nama Toko:**\n\n{nama_toko_dsi}")
                            with col2: st.info(f"**👤 AM:**\n\n{am_toko_dsi}")
                            with col3: st.warning(f"**👥 AS:**\n\n{as_toko_dsi}")
                            
                            st.write("")
                            filtered_dsi = filtered_dsi.sort_values(by="RP POTENSI RUSAK", ascending=False)
                            
                            kolom_tampil_dsi = [
                                'PLU FD', 'DESC FD', 'Umur Produk', 'SPD', 'DSI', 
                                'POTENSI RUSAK', 'RP POTENSI RUSAK', 'CEK DSI'
                            ]
                            
                            kolom_tersedia_dsi = [col for col in kolom_tampil_dsi if col in filtered_dsi.columns]
                            display_df_dsi = filtered_dsi[kolom_tersedia_dsi]

                            st.write(f"**Tabel Data DSI - {nama_toko_dsi}**")
                            st.dataframe(display_df_dsi.style.format(format_ribuan), hide_index=True, use_container_width=True)

                            st.markdown("<br>", unsafe_allow_html=True)
                            
                            output_dsi = BytesIO()
                            with pd.ExcelWriter(output_dsi, engine='openpyxl') as writer:
                                filtered_dsi.to_excel(writer, index=False, sheet_name='DSI_Toko')
                            excel_data_dsi = output_dsi.getvalue()

                            st.download_button(
                                label=f"📥 Download Data Lengkap {input_toko_dsi} (Excel)",
                                data=excel_data_dsi,
                                file_name=f"DSI_SayBread_{input_toko_dsi}.xlsx",
                                mime="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet"
                            )
                else:
                    st.info("📌 Menampilkan Top 10 Toko dengan Potensi Rusak tertinggi (by Rupiah).")
                    agg_dsi = df_dsi.groupby(['KODE_TOKO', 'NAMA', 'AM', 'AS'], as_index=False)[['POTENSI RUSAK', 'RP POTENSI RUSAK']].sum()
                    top_10_dsi = agg_dsi.sort_values(by="RP POTENSI RUSAK", ascending=False).head(10).copy()
                    top_10_dsi.insert(0, 'NO', range(1, len(top_10_dsi) + 1))
                    st.dataframe(top_10_dsi.style.format(format_ribuan), hide_index=True, use_container_width=True)
            else:
                st.info("ℹ️ Belum ada data sumber yang diunggah oleh Admin.")
        except ValueError:
            st.error("❌ Sheet bernama 'DSI_FD' tidak ditemukan di file Excel Master!")
        except Exception as e:
            st.error(f"Terjadi kesalahan sistem: {e}")


# ------------------------------------------
# ISI TAB 4: REKOMENDASI PRODUKSI
# ------------------------------------------
with tab_rekomendasi:
    st.subheader("Rekomendasi Produksi")
    st.markdown(f"#### 📅 Periode Data: `{periode_dict.get('Rekomendasi', 'Belum diatur')}`")
    st.info("🚀 **Coming Soon!**\n\nFitur ini sedang dalam tahap pengembangan.")


# ------------------------------------------
# ISI TAB 5: DOWNLOAD MASTER (PASSWORD: 321)
# ------------------------------------------
with tab_download:
    st.subheader("Download File Excel Master")
    st.write("Masukkan password untuk mengunduh database master (seluruh sheet).")
    
    pass_master = st.text_input("Password Download:", type="password", key="pass_master")
    btn_enter_dl = st.button("Enter ↵", key="btn_dl", type="primary")
    
    if pass_master == "321":
        st.success("🔓 Akses Diberikan!")
        try:
            resp_raw = requests.get(base_url)
            if resp_raw.status_code == 200:
                st.download_button(
                    label="📥 DOWNLOAD FILE MASTER (.xlsx)",
                    data=resp_raw.content,
                    file_name="Master_Database_SayBread.xlsx",
                    mime="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet",
                    type="primary"
                )
            else:
                st.info("File master belum diunggah oleh Admin.")
        except Exception as e:
            st.error("Gagal mengambil file.")
    elif pass_master != "":
        st.error("❌ Password Salah!")


# ------------------------------------------
# ISI TAB 6: ADMIN AREA (DENGAN TIMEOUT & LOGOUT)
# ------------------------------------------
with tab_admin:
    
    # 1. CEK TIMEOUT (Jika sudah login, cek apakah sudah > 5 menit / 300 detik nganggur)
    if st.session_state.admin_logged_in:
        time_elapsed = time.time() - st.session_state.last_active
        if time_elapsed > 300: # 300 detik = 5 menit
            st.session_state.admin_logged_in = False
            st.warning("⏱️ Sesi Admin telah berakhir (Timeout 5 Menit). Silakan login kembali.")
            time.sleep(2) # Jeda sebentar agar user bisa baca pesan errornya
            st.rerun() # Refresh halaman

    # 2. HALAMAN LOGIN
    if not st.session_state.admin_logged_in:
        st.subheader("🔐 Login Admin")
        password_input = st.text_input("Masukkan Password Admin:", type="password", key="login_pass")
        if st.button("Login", type="primary"):
            if password_input == "icnbr034":
                st.session_state.admin_logged_in = True
                st.session_state.last_active = time.time() # Catat waktu masuk
                st.rerun() # Refresh halaman untuk masuk ke dashboard admin
            else:
                st.error("❌ Password Salah! Anda tidak memiliki akses.")

    # 3. DASHBOARD ADMIN (JIKA LOGIN BERHASIL)
    else:
        # Perbarui waktu aktif setiap kali Admin mengklik/berinteraksi di halaman ini
        st.session_state.last_active = time.time() 

        # Header Dashboard Admin & Tombol Logout
        col_title, col_logout = st.columns([4, 1])
        with col_title:
            st.subheader("⚙️ Dashboard Admin")
            st.success("🔓 Login Berhasil! Selamat datang Admin.")
        with col_logout:
            st.write("") # Spasi
            if st.button("🚪 Logout", type="primary"):
                st.session_state.admin_logged_in = False
                st.rerun()

        st.markdown("---")
        
        # BAGIAN 1: PENGATURAN PERIODE
        st.write("### 1. Pengaturan Periode Data")
        st.info("Atur periode di bawah ini. Anda bisa langsung memperbarui tanggalnya saja tanpa harus upload Excel lagi.")
        
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

        dict_periode_baru = {
            "Resume_Rusak": format_date(p_res),
            "Monitoring": format_date(p_mon),
            "DSI_FD": format_date(p_dsi),
            "Rekomendasi": format_date(p_rek)
        }

        # TOMBOL 1: PERBARUI TANGGAL SAJA
        if st.button("🔄 Simpan & Perbarui Tanggal Saja"):
            with st.spinner("Memperbarui tanggal di server..."):
                try:
                    json_periode = json.dumps(dict_periode_baru)
                    cloudinary.uploader.upload(
                        BytesIO(json_periode.encode('utf-8')),
                        resource_type="raw",
                        public_id=PUBLIC_PERIODE_ID,
                        overwrite=True,
                        invalidate=True
                    )
                    st.success("✅ Tanggal berhasil diperbarui tanpa mengubah file Excel!")
                except Exception as e:
                    st.error(f"❌ Gagal memperbarui tanggal: {e}")

        st.markdown("---")
        
        # BAGIAN 2: UPLOAD EXCEL MASTER
        st.write("### 2. Upload File Excel Master")
        st.warning("Pastikan file Excel Anda memiliki sheet: **Resume_Rusak**, **Monitoring**, **DSI_FD**, dan **Rekomendasi**.")
        uploaded_file = st.file_uploader("Pilih file Excel", type=["xlsx", "xls"], key="uploader")
        
        # TOMBOL 2: UPLOAD EXCEL + TANGGAL
        if uploaded_file is not None:
            if st.button("📤 Upload Excel & Perbarui Semua", type="primary"):
                with st.spinner("Mengunggah Excel dan Periode ke server..."):
                    try:
                        # Upload Excel
                        cloudinary.uploader.upload(
                            uploaded_file,
                            resource_type="raw",
                            public_id=PUBLIC_FILE_ID,
                            overwrite=True,
                            invalidate=True
                        )
                        # Upload Tanggal
                        json_periode = json.dumps(dict_periode_baru)
                        cloudinary.uploader.upload(
                            BytesIO(json_periode.encode('utf-8')),
                            resource_type="raw",
                            public_id=PUBLIC_PERIODE_ID,
                            overwrite=True,
                            invalidate=True
                        )
                        st.success("✅ File Master Excel dan Periode berhasil diperbarui!")
                    except Exception as e:
                        st.error(f"❌ Gagal mengunggah file: {e}")
