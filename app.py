import streamlit as st
import pandas as pd
import cloudinary
import cloudinary.uploader
import requests
from io import BytesIO
import time

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

st.title("🍞 Portal Say Bread")

# ==========================================
# 3. MENU UTAMA MENGGUNAKAN TABS
# ==========================================
tab_monitoring, tab_admin = st.tabs(["📊 Monitoring Say Bread", "🔐 Admin"])

# ------------------------------------------
# ISI TAB 1: MONITORING SAY BREAD
# ------------------------------------------
with tab_monitoring:
    st.subheader("Pencarian Data Toko")
    
    cloud_name = st.secrets["CLOUDINARY_CLOUD_NAME"]
    base_url = f"https://res.cloudinary.com/{cloud_name}/raw/upload/{PUBLIC_FILE_ID}"
    fetch_url = f"{base_url}?t={int(time.time())}"

    # Menggunakan try-except untuk mengambil data dari cloud
    try:
        response = requests.get(fetch_url)
        
        if response.status_code == 200:
            # Membaca data
            df = pd.read_excel(BytesIO(response.content))
            
            # Membersihkan spasi pada kolom Toko untuk memastikan pencarian akurat
            # dan mengubah tipe data menjadi string huruf besar (Uppercase)
            df['Toko'] = df['Toko'].astype(str).str.strip().str.upper()

            # 1. Kolom Input Kode Toko
            input_toko = st.text_input("🔍 Masukkan 4 Digit Kode Toko:", max_chars=4, placeholder="Contoh: F08C").upper()

            if input_toko:
                # Jika input kurang dari 4 digit
                if len(input_toko) < 4:
                    st.error("⚠️ Error: Kode toko harus terdiri dari 4 digit alfanumerik!")
                
                # Jika input pas 4 digit
                elif len(input_toko) == 4:
                    # Filter data berdasarkan kode toko
                    filtered_df = df[df['Toko'] == input_toko]

                    if filtered_df.empty:
                        st.warning(f"⚠️ Data untuk kode toko '{input_toko}' tidak ditemukan.")
                    else:
                        st.markdown("---")
                        # 2. Menampilkan Label Nama, AM, dan AS
                        nama_toko = filtered_df.iloc[0]['Nama']
                        am_toko = filtered_df.iloc[0]['AM']
                        as_toko = filtered_df.iloc[0]['AS']

                        col1, col2, col3 = st.columns(3)
                        with col1:
                            st.success(f"**🏷️ Nama Toko:**\n\n{nama_toko}")
                        with col2:
                            st.info(f"**👤 AM:**\n\n{am_toko}")
                        with col3:
                            st.warning(f"**👥 AS:**\n\n{as_toko}")
                        
                        st.write("") # Spasi kosong

                        # 3. Tampilan Data Terbatas di Layar
                        # Daftar kolom yang ingin ditampilkan di Web
                        kolom_tampil = [
                            'PLU Jual', 'Deskripsi', 'Qty Produksi', 'Qty Sales', 
                            'QTY Total Rusak', '% Rusak By Qty', 'Avg Produksi', 
                            'Avg Sales', 'Avg Rusak'
                        ]
                        
                        # Memastikan hanya mengambil kolom yang ada di excel agar tidak error
                        kolom_tersedia = [col for col in kolom_tampil if col in filtered_df.columns]
                        display_df = filtered_df[kolom_tersedia]

                        st.write(f"**Tabel Data Item - {nama_toko}**")
                        # Menampilkan dataframe tanpa index angka di awal
                        st.dataframe(display_df, hide_index=True, use_container_width=True)

                        st.markdown("<br>", unsafe_allow_html=True)

                        # 4. Tombol Download Data Lengkap
                        # Membuat file excel di dalam memori (menggunakan semua kolom dari filtered_df)
                        output = BytesIO()
                        with pd.ExcelWriter(output, engine='openpyxl') as writer:
                            filtered_df.to_excel(writer, index=False, sheet_name='Data_Toko')
                        excel_data = output.getvalue()

                        st.download_button(
                            label=f"📥 Download Data Lengkap {input_toko} (Excel)",
                            data=excel_data,
                            file_name=f"Data_SayBread_{input_toko}.xlsx",
                            mime="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet",
                            type="primary"
                        )
        else:
            st.info("ℹ️ Belum ada data sumber yang diunggah oleh Admin.")
            
    except Exception as e:
        st.error(f"Terjadi kesalahan sistem: {e}")


# ------------------------------------------
# ISI TAB 2: ADMIN AREA
# ------------------------------------------
with tab_admin:
    st.subheader("Halaman Admin")
    
    password_input = st.text_input("Masukkan Password Admin:", type="password", key="admin_pass")
    
    if password_input == "icnbr034":
        st.success("🔓 Login Berhasil! Selamat datang Admin.")
        st.markdown("---")
        st.write("Upload File Excel master (.xlsx) untuk memperbarui database.")
        
        uploaded_file = st.file_uploader("Pilih file Excel", type=["xlsx", "xls"], key="uploader")
        
        if uploaded_file is not None:
            if st.button("📤 Upload & Perbarui Data"):
                with st.spinner("Mengunggah data ke Cloudinary..."):
                    try:
                        cloudinary.uploader.upload(
                            uploaded_file,
                            resource_type="raw",
                            public_id=PUBLIC_FILE_ID,
                            overwrite=True,
                            invalidate=True
                        )
                        st.success("✅ File berhasil diunggah! Data Monitoring sudah diperbarui.")
                    except Exception as e:
                        st.error(f"❌ Gagal mengunggah file: {e}")
                        
    elif password_input != "":
        st.error("❌ Password Salah! Anda tidak memiliki akses.")