import streamlit as st
import fitz  # PyMuPDF
from PIL import Image, ImageDraw, ImageFont
import io
import zipfile  # Modul baru untuk membungkus banyak file jadi ZIP

# --- KONFIGURASI USERNAME & PASSWORD ---
USER_VALID = "Sintel46"
PASS_VALID = "IMO2025"

# --- SISTEM LOGIN ---
st.set_page_config(page_title="Generator Lampiran Progres", page_icon="📑", layout="wide")
# --- TRIK MENYEMBUNYIKAN MENU & IKON GITHUB ---
sembunyikan_elemen = """
<style>
#MainMenu {visibility: hidden;}
header {visibility: hidden;}
footer {visibility: hidden;}
</style>
"""
st.markdown(sembunyikan_elemen, unsafe_allow_html=True)

if "login_sukses" not in st.session_state:
    st.session_state.login_sukses = False

if not st.session_state.login_sukses:
    st.title("IMO2025 📑 dR")
    st.write("Silakan masukkan Username dan Password untuk masuk ke ruang kerja.")
    
    username = st.text_input("Username")
    password = st.text_input("Password", type="password")
    
    if st.button("Masuk Ruang Kerja", use_container_width=True):
        if username == USER_VALID and password == PASS_VALID:
            st.session_state.login_sukses = True
            st.rerun() 
        else:
            st.error("❌ Username atau Password salah!")
            
    st.stop() 

# ==========================================
# KODE DI BAWAH INI HANYA JALAN JIKA LOGIN BERHASIL
# ==========================================

def crop_center_square(image):
    width, height = image.size
    # Mengambil dimensi terbesar sebagai patokan agar kualitas gambar tetap tajam
    max_dim = max(width, height)
    
    # Memaksa (resize) gambar menjadi persegi 1:1 secara utuh
    # Tanpa memotong (crop) dan tanpa menambah latar belakang warna
    new_image = image.resize((max_dim, max_dim))
    
    return new_image

def proses_dokumen(pdf_file, data_rangkaian):
    doc = fitz.open(stream=pdf_file.read(), filetype="pdf")
    
    # 1. Hapus SEMUA jenis anotasi (KECUALI foto/Stamp) dengan metode "Looping Purge"
    for halaman in doc:
        while True:
            ada_yang_dihapus = False
            for anotasi in halaman.annots():
                # Jika bukan gambar (Stamp), langsung basmi
                if anotasi.type[1] != "Stamp":
                    halaman.delete_annot(anotasi)
                    ada_yang_dihapus = True
                    break # Hentikan sejenak, lalu ulangi pencarian dari awal agar pop-up anak ikut terhapus
            
            # Jika sudah bersih tidak ada anotasi tersisa, hentikan putaran
            if not ada_yang_dihapus:
                break
                
        # Mengepel bersih sisa-sisa aliran data (cache) di halaman tersebut
        halaman.clean_contents()
                
    # 2. Menjahit lampiran foto progres (hanya jika ada data foto)
    if len(data_rangkaian) > 0:
        lebar_halaman, tinggi_halaman = 595, 842
        lebar_gambar = 150
        tinggi_gambar = 150
        spasi = 30
        mulai_x = (lebar_halaman - (3 * lebar_gambar + 2 * spasi)) / 2 
        
        y_pos_awal = 60
        y_pos = y_pos_awal
        items_per_page = 0
        
        halaman_baru = doc.new_page(width=lebar_halaman, height=tinggi_halaman)
        
        for data in data_rangkaian:
            if items_per_page >= 3:
                halaman_baru = doc.new_page(width=lebar_halaman, height=tinggi_halaman)
                y_pos = y_pos_awal
                items_per_page = 0
                
            halaman_baru.insert_text(fitz.Point(mulai_x, y_pos), f"Nama Aset: {data['nama_aset']}", fontsize=14, color=(0, 0, 0))
            
            y_gambar = y_pos + 15
            koleksi = [
                {"file": data["img_0"], "label": "0%"},
                {"file": data["img_50"], "label": "50%"},
                {"file": data["img_100"], "label": "100%"}
            ]
            
            for i, item in enumerate(koleksi):
                img = Image.open(item["file"])
                img_square = crop_center_square(img)
                
                img_byte_arr = io.BytesIO()
                img_square.save(img_byte_arr, format='JPEG')
                img_bytes = img_byte_arr.getvalue()
                
                x0 = mulai_x + i * (lebar_gambar + spasi)
                y0 = y_gambar
                x1 = x0 + lebar_gambar
                y1 = y0 + tinggi_gambar
                rect = fitz.Rect(x0, y0, x1, y1)
                
                halaman_baru.insert_image(rect, stream=img_bytes)
                
                titik_teks = fitz.Point(x0 + 60, y1 + 20)
                halaman_baru.insert_text(titik_teks, item["label"], fontsize=14, color=(0, 0, 0))
                
            y_pos += 210  
            items_per_page += 1
        
    output_pdf = io.BytesIO()
    # garbage=4 (level tertinggi) untuk menghancurkan seluruh sampah objek yang sudah yatim piatu
    doc.save(output_pdf, garbage=4, deflate=True)
    doc.close()
    
    return output_pdf.getvalue()
                
    # 2. Menjahit lampiran foto progres (hanya jika ada data foto)
    if len(data_rangkaian) > 0:
        lebar_halaman, tinggi_halaman = 595, 842
        lebar_gambar = 150
        tinggi_gambar = 150
        spasi = 30
        mulai_x = (lebar_halaman - (3 * lebar_gambar + 2 * spasi)) / 2 
        
        y_pos_awal = 60
        y_pos = y_pos_awal
        items_per_page = 0
        
        halaman_baru = doc.new_page(width=lebar_halaman, height=tinggi_halaman)
        
        for data in data_rangkaian:
            if items_per_page >= 3:
                halaman_baru = doc.new_page(width=lebar_halaman, height=tinggi_halaman)
                y_pos = y_pos_awal
                items_per_page = 0
                
            halaman_baru.insert_text(fitz.Point(mulai_x, y_pos), f"Nama Aset: {data['nama_aset']}", fontsize=14, color=(0, 0, 0))
            
            y_gambar = y_pos + 15
            koleksi = [
                {"file": data["img_0"], "label": "0%"},
                {"file": data["img_50"], "label": "50%"},
                {"file": data["img_100"], "label": "100%"}
            ]
            
            for i, item in enumerate(koleksi):
                img = Image.open(item["file"])
                img_square = crop_center_square(img)
                
                img_byte_arr = io.BytesIO()
                img_square.save(img_byte_arr, format='JPEG')
                img_bytes = img_byte_arr.getvalue()
                
                x0 = mulai_x + i * (lebar_gambar + spasi)
                y0 = y_gambar
                x1 = x0 + lebar_gambar
                y1 = y0 + tinggi_gambar
                rect = fitz.Rect(x0, y0, x1, y1)
                
                halaman_baru.insert_image(rect, stream=img_bytes)
                
                titik_teks = fitz.Point(x0 + 60, y1 + 20)
                halaman_baru.insert_text(titik_teks, item["label"], fontsize=14, color=(0, 0, 0))
                
            y_pos += 210  
            items_per_page += 1
        
    output_pdf = io.BytesIO()
    
    # --- PERINTAH SAPU BERSIH MEMORI (GARBAGE COLLECTION) ---
    # garbage=4 memastikan seluruh data objek anotasi pink yang tersembunyi
    # ikut terhapus permanen dari struktur file PDF.
    doc.save(output_pdf, garbage=4, deflate=True)
    doc.close()
    
    return output_pdf.getvalue()
                
    # 2. Menjahit lampiran foto progres (hanya jika ada data foto)
    # --- (Biarkan kode bagian bawah ini tetap sama) ---
            
    # 2. Menjahit lampiran foto progres (hanya jika ada data foto)
    if len(data_rangkaian) > 0:
        lebar_halaman, tinggi_halaman = 595, 842
        lebar_gambar = 150
        tinggi_gambar = 150
        spasi = 30
        mulai_x = (lebar_halaman - (3 * lebar_gambar + 2 * spasi)) / 2 
        
        y_pos_awal = 60
        y_pos = y_pos_awal
        items_per_page = 0
        
        halaman_baru = doc.new_page(width=lebar_halaman, height=tinggi_halaman)
        
        for data in data_rangkaian:
            if items_per_page >= 3:
                halaman_baru = doc.new_page(width=lebar_halaman, height=tinggi_halaman)
                y_pos = y_pos_awal
                items_per_page = 0
                
            halaman_baru.insert_text(fitz.Point(mulai_x, y_pos), f"Nama Aset: {data['nama_aset']}", fontsize=14, color=(0, 0, 0))
            
            y_gambar = y_pos + 15
            koleksi = [
                {"file": data["img_0"], "label": "0%"},
                {"file": data["img_50"], "label": "50%"},
                {"file": data["img_100"], "label": "100%"}
            ]
            
            for i, item in enumerate(koleksi):
                img = Image.open(item["file"])
                img_square = crop_center_square(img)
                
                img_byte_arr = io.BytesIO()
                img_square.save(img_byte_arr, format='JPEG')
                img_bytes = img_byte_arr.getvalue()
                
                x0 = mulai_x + i * (lebar_gambar + spasi)
                y0 = y_gambar
                x1 = x0 + lebar_gambar
                y1 = y0 + tinggi_gambar
                rect = fitz.Rect(x0, y0, x1, y1)
                
                halaman_baru.insert_image(rect, stream=img_bytes)
                
                titik_teks = fitz.Point(x0 + 60, y1 + 20)
                halaman_baru.insert_text(titik_teks, item["label"], fontsize=14, color=(0, 0, 0))
                
            y_pos += 210  
            items_per_page += 1
        
    output_pdf = io.BytesIO()
    doc.save(output_pdf)
    doc.close()
    return output_pdf.getvalue()

# --- Antarmuka Web Utama ---
st.title("IMO2025 📑 dR ")

col_kiri, col_kanan = st.columns([4, 1])
with col_kanan:
    if st.button("🚪 Keluar", use_container_width=True):
        st.session_state.login_sukses = False
        st.rerun()

# --- PILIHAN MODE KERJA ---
st.write("Pilih jenis pekerjaan yang ingin dilakukan hari ini:")
mode_kerja = st.radio(
    "Mode Aplikasi",
    ["🧹 Hanya Bersihkan Kotak Pink Anotasi", "🚀 Bersihkan Anotasi & Jahit Foto Progres", "📸 Generator Foto Watermark Laporan"],
    label_visibility="collapsed",
    horizontal=True
)
st.divider()

# ==========================================
# LOGIKA MENU 1 & 2 (PEMROSESAN PDF)
# ==========================================
if mode_kerja in ["🧹 Hanya Bersihkan Kotak Pink Anotasi", "🚀 Bersihkan Anotasi & Jahit Foto Progres"]:
    pdf_inputs = st.file_uploader("📥 Unggah PDF Checklist Dasar (Bisa blok banyak file sekaligus)", type=["pdf"], accept_multiple_files=True)
    data_siap_proses = []

    if mode_kerja == "🚀 Bersihkan Anotasi & Jahit Foto Progres":
        st.subheader("📸 Form Rangkaian Foto Progres")
        st.write("*Isi maksimal 5 aset. Yang dikosongkan akan dilewati otomatis.*")

        for i in range(1, 6):
            st.markdown(f"**Rangkaian Aset ke-{i}**")
            nama_aset = st.text_input(f"Nama Aset {i}", key=f"nama_{i}", placeholder="Contoh: Peraga Sinyal")
            
            col1, col2, col3 = st.columns(3)
            with col1:
                img_0 = st.file_uploader("Foto 0%", key=f"img0_{i}", type=["jpg", "jpeg", "png"])
                if img_0: st.image(img_0, use_container_width=True) 
            with col2:
                img_50 = st.file_uploader("Foto 50%", key=f"img50_{i}", type=["jpg", "jpeg", "png"])
                if img_50: st.image(img_50, use_container_width=True) 
            with col3:
                img_100 = st.file_uploader("Foto 100%", key=f"img100_{i}", type=["jpg", "jpeg", "png"])
                if img_100: st.image(img_100, use_container_width=True) 
            
            if nama_aset and img_0 and img_50 and img_100:
                data_siap_proses.append({
                    "nama_aset": nama_aset,
                    "img_0": img_0,
                    "img_50": img_50,
                    "img_100": img_100
                })
            st.divider()

    # --- EKSEKUSI TOMBOL PROSES PDF ---
    if pdf_inputs:
        if mode_kerja == "🧹 Hanya Bersihkan Kotak Pink Anotasi":
            if st.button(f"🧹 Bersihkan {len(pdf_inputs)} File Anotasi Sekarang", use_container_width=True):
                with st.spinner("Sedang membersihkan kotak pink pada file PDF..."):
                    if len(pdf_inputs) == 1:
                        pdf_file = pdf_inputs[0]
                        hasil_pdf_bytes = proses_dokumen(pdf_file, [])
                        nama_file_unduh = pdf_file.name[:-4] + " revisi.pdf" if pdf_file.name.lower().endswith(".pdf") else pdf_file.name + " revisi.pdf"
                        
                        st.success("Selesai! Kotak pink berhasil dihapus dan foto laporan tetap utuh.")
                        st.download_button("⬇️ Unduh File Bersih", data=hasil_pdf_bytes, file_name=nama_file_unduh, mime="application/pdf", use_container_width=True)
                    else:
                        zip_buffer = io.BytesIO()
                        with zipfile.ZipFile(zip_buffer, "w", zipfile.ZIP_DEFLATED) as zip_file:
                            for pdf_file in pdf_inputs:
                                hasil_pdf_bytes = proses_dokumen(pdf_file, [])
                                nama_file_unduh = pdf_file.name[:-4] + " revisi.pdf" if pdf_file.name.lower().endswith(".pdf") else pdf_file.name + " revisi.pdf"
                                zip_file.writestr(nama_file_unduh, hasil_pdf_bytes)
                        
                        st.success(f"Selesai! {len(pdf_inputs)} file berhasil dibersihkan dari anotasi.")
                        st.download_button("⬇️ Unduh Semua File (ZIP)", data=zip_buffer.getvalue(), file_name="Laporan_Sintel_Bersih.zip", mime="application/zip", use_container_width=True)
                        
        elif mode_kerja == "🚀 Bersihkan Anotasi & Jahit Foto Progres":
            if len(pdf_inputs) > 1:
                st.info("ℹ️ Perhatian: Pada mode jahit foto, sistem hanya akan memproses file PDF yang letaknya paling pertama.")
                
            if len(data_siap_proses) > 0:
                st.success(f"Ada {len(data_siap_proses)} rangkaian foto yang siap dijahit.")
                if st.button("🚀 Menjahit Dokumen Sekarang!", use_container_width=True):
                    with st.spinner("Sedang membersihkan PDF dan menjahit lampiran foto..."):
                        pdf_file = pdf_inputs[0] 
                        hasil_pdf_bytes = proses_dokumen(pdf_file, data_siap_proses)
                        
                        nama_file_unduh = pdf_file.name[:-4] + " revisi.pdf" if pdf_file.name.lower().endswith(".pdf") else pdf_file.name + " revisi.pdf"
                        
                        st.balloons() 
                        st.download_button("⬇️ Unduh File: " + nama_file_unduh, data=hasil_pdf_bytes, file_name=nama_file_unduh, mime="application/pdf", use_container_width=True)
            else:
                st.warning("⚠️ Mohon lengkapi minimal satu rangkaian aset untuk dijahit.")

# ==========================================
# LOGIKA MENU 3 (GENERATOR WATERMARK FOTO)
# ==========================================
elif mode_kerja == "📸 Generator Foto Watermark Laporan":
    st.subheader("📸 Generator Foto Watermark Laporan")
    
    uploaded_image = st.file_uploader("Pilih foto lapangan yang masih polos...", type=['jpg', 'jpeg', 'png'])

    if uploaded_image is not None:
        st.info("✍️ Silakan isi data manual di bawah ini untuk dijahit ke foto:")
        
        col1, col2 = st.columns(2)
        with col1:
            waktu = st.text_input("Waktu (Timemark)", "Rabu, 05 Maret 2025 11:22")
            koordinat = st.text_input("Koordinat", "-6.957726, 110.432890")
        with col2:
            kegiatan = st.text_input("Kegiatan", "Perawatan Penggerak Wesel Elektrik W45B SMT")
            lokasi = st.text_area("Lokasi", "Kecamatan Semarang Utara, Kota Semarang\nJawa Tengah\nIndonesia")

        if st.button("Jahit Watermark ke Foto", use_container_width=True):
            image_wm = Image.open(uploaded_image)
            draw = ImageDraw.Draw(image_wm)
            
            import urllib.request
            import textwrap # Modul wajib untuk melipat teks otomatis
            
            # 1. Atur Ulang Ukuran Font (Diturunkan skalanya agar lebih rapi)
            dimensi_dasar = min(image_wm.width, image_wm.height)
            ukuran_font = int(dimensi_dasar * 0.028)
            if ukuran_font < 20: 
                ukuran_font = 20
                
            # 2. Fitur Pelipat Teks Otomatis (Auto-Wrap)
            # Menghitung batas jumlah huruf per baris (maksimal 80% dari lebar foto)
            batas_karakter = int((image_wm.width * 0.80) / (ukuran_font * 0.55))
            
            lokasi_lipat = "\n".join(textwrap.wrap(lokasi, width=batas_karakter))
            kegiatan_lipat = "\n".join(textwrap.wrap(kegiatan, width=batas_karakter))
            
            # Teks siap cetak dengan komponen yang sudah bisa melipat ke bawah
            teks_watermark = f"{waktu}\n\n{lokasi_lipat}\n\n{koordinat}\n\n{kegiatan_lipat}"
            
            # 3. Eksekusi Unduh Font
            try:
                url_font = "https://github.com/googlefonts/roboto/raw/main/src/hinted/Roboto-Medium.ttf"
                req = urllib.request.Request(url_font, headers={'User-Agent': 'Mozilla/5.0'})
                respon = urllib.request.urlopen(req, timeout=5)
                font_bytes = io.BytesIO(respon.read())
                font = ImageFont.truetype(font_bytes, ukuran_font)
            except Exception:
                try:
                    font = ImageFont.truetype("arial.ttf", ukuran_font)
                except:
                    font = ImageFont.load_default()
            
            # Margin posisi kiri atas
            margin_x = int(image_wm.width * 0.05)
            margin_y = int(image_wm.height * 0.05)
            spacing_teks = int(ukuran_font * 0.3)
            
            # Menghitung tinggi akhir teks yang sudah dilipat
            try:
                bbox = draw.multiline_textbbox((0, 0), teks_watermark, font=font, spacing=spacing_teks)
                tinggi_teks_total = bbox[3] - bbox[1]
            except AttributeError:
                if font != ImageFont.load_default():
                    tinggi_teks_total = (teks_watermark.count('\n') + 1) * int(ukuran_font * 1.3)
                else:
                    tinggi_teks_total = (teks_watermark.count('\n') + 1) * 15 
            
            # Gambar garis vertikal biru penanda
            lebar_garis = int(ukuran_font * 0.25)
            if lebar_garis < 5: lebar_garis = 5
            
            draw.rectangle(
                [margin_x, margin_y, margin_x + lebar_garis, margin_y + tinggi_teks_total],
                fill="blue"
            )
            
            # Geser teks ke kanan sedikit agar tidak menabrak garis biru
            text_x = margin_x + lebar_garis + int(ukuran_font * 0.6)
            text_y = margin_y
            
            # Outline bayangan hitam
            for adj_x in [-2, -1, 0, 1, 2]:
                for adj_y in [-2, -1, 0, 1, 2]:
                    draw.multiline_text((text_x + adj_x, text_y + adj_y), teks_watermark, font=font, fill="black", spacing=spacing_teks)
                    
            # Cetak teks putih utama
            draw.multiline_text((text_x, text_y), teks_watermark, font=font, fill="white", spacing=spacing_teks)
            
            st.image(image_wm, caption="Hasil Jahitan Watermark", use_container_width=True)

            buf_img = io.BytesIO()
            image_wm.save(buf_img, format="JPEG")
            byte_im = buf_img.getvalue()
            
            st.download_button(
                label="⬇️ Unduh Foto Laporan",
                data=byte_im,
                file_name="Laporan_Watermark_Sintel.jpg",
                mime="image/jpeg",
                use_container_width=True
            )
