import streamlit as st
import fitz  # PyMuPDF
from PIL import Image, ImageDraw, ImageFont
import io
import zipfile
import urllib.request
import textwrap 

# --- KONFIGURASI USERNAME & PASSWORD ---
USER_VALID = "Sintel46"
PASS_VALID = "IMO2025"

# --- SISTEM LOGIN ---
st.set_page_config(page_title="PAGE IMO2025 X dR", page_icon="📑", layout="wide")

# --- CUSTOM CSS: TEMA DARK MODE KAI MODERN ---
tema_visual = """
<style>
/* Sembunyikan elemen bawaan Streamlit/GitHub */
#MainMenu {visibility: hidden;}
header {visibility: hidden;}
footer {visibility: hidden;}

/* Latar Belakang Hitam Elegan (Dark Mode) */
.stApp {
    background-color: #121212;
}

/* Memaksa teks bawaan menjadi terang/putih agar terbaca di latar gelap */
html, body, [class*="css"], .stMarkdown p, label {
    color: #E2E8F0 !important;
}

/* Kustomisasi Judul Utama dengan Biru KAI + Garis Tepi Putih */
.title-kai {
    text-align: center;
    font-size: 3.5rem;
    font-weight: 900;
    margin-bottom: 30px; 
    padding-bottom: 0px;
    color: #282562; /* Biru Gelap KAI */
    -webkit-text-stroke: 1.5px #FFFFFF; /* Garis tepi putih */
    text-shadow: 2px 2px 4px rgba(0, 0, 0, 0.8); /* Shadow gelap agar lebih menonjol */
}

/* Kustomisasi Tombol Utama: Warna Dasar Biru Gelap KAI */
.stButton>button {
    background-color: #282562 !important; 
    color: #FFFFFF !important;
    font-weight: 600 !important;
    border-radius: 8px !important;
    border: 1px solid #282562 !important;
    padding: 0.6rem 1.2rem !important;
    box-shadow: 0 4px 6px -1px rgba(0, 0, 0, 0.5) !important;
    transition: all 0.3s ease !important;
}

/* Efek saat tombol disentuh (Hover) berubah ke Oranye KAI */
.stButton>button:hover {
    background-color: #ec6923 !important; 
    border: 1px solid #ec6923 !important;
    transform: translateY(-3px);
    box-shadow: 0 10px 15px -3px rgba(236, 105, 35, 0.4) !important;
}

/* Kustomisasi Kotak Input */
.stTextInput>div>div>input, .stTextArea>div>div>textarea {
    border-radius: 8px !important;
    border: 1.5px solid #282562 !important;
    background-color: #1E1E1E !important;
    color: #FFFFFF !important;
}
.stTextInput>div>div>input:focus, .stTextArea>div>div>textarea:focus {
    border-color: #ec6923 !important;
    box-shadow: 0 0 0 1px #ec6923 !important;
}

/* Modifikasi Kotak Notifikasi / Info */
div[data-testid="stInfo"] {
    background-color: rgba(40, 37, 98, 0.25) !important; 
    border-left: 5px solid #282562 !important;
    color: #E2E8F0 !important;
}
div[data-testid="stSuccess"] {
    background-color: rgba(236, 105, 35, 0.15) !important; 
    border-left: 5px solid #ec6923 !important;
    color: #E2E8F0 !important;
}
div[data-testid="stWarning"] {
    background-color: rgba(236, 105, 35, 0.25) !important;
    border-left: 5px solid #ec6923 !important;
    color: #E2E8F0 !important;
}

/* Penyesuaian Garis Pembatas */
hr {
    border-top: 1px solid #2D2D2D !important;
}
</style>
"""
st.markdown(tema_visual, unsafe_allow_html=True)

if "login_sukses" not in st.session_state:
    st.session_state.login_sukses = False

if not st.session_state.login_sukses:
    st.markdown("<h1 class='title-kai'>IMO2025 📑 dR</h1>", unsafe_allow_html=True)
    
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
    max_dim = max(width, height)
    new_image = image.resize((max_dim, max_dim))
    return new_image

def proses_dokumen(pdf_file, data_rangkaian):
    doc = fitz.open(stream=pdf_file.read(), filetype="pdf")
    
    for halaman in doc:
        teks_halaman = halaman.get_text().upper()
        is_checklist = "REFER" in teks_halaman or "DIKETAHUI" in teks_halaman or "PERALATAN" in teks_halaman
        
        while True:
            ada_yang_dihapus = False
            for anotasi in halaman.annots():
                info = anotasi.info
                isi_teks = (str(info.get("content", "")) + str(info.get("subject", ""))).upper()
                
                if anotasi.type[1] != "Stamp" or "STL" in isi_teks or "SMT" in isi_teks:
                    halaman.delete_annot(anotasi)
                    ada_yang_dihapus = True
                    break
            if not ada_yang_dihapus:
                break
                
        if not is_checklist:
            kotak_tutup_presisi = fitz.Rect(430, 245, 580, 290) 
            halaman.add_redact_annot(kotak_tutup_presisi, fill=(1, 1, 1))
            halaman.apply_redactions()
        
        halaman.clean_contents()
                
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
    doc.save(output_pdf, garbage=2, deflate=True)
    doc.close()
    
    return output_pdf.getvalue()

# --- Antarmuka Web Utama ---
col_kiri, col_kanan = st.columns([4, 1])
with col_kiri:
    st.markdown("<h1 class='title-kai' style='text-align: left;'>IMO2025 📑 dR</h1>", unsafe_allow_html=True)
with col_kanan:
    st.write("")
    if st.button("🚪 Keluar", use_container_width=True):
        st.session_state.login_sukses = False
        st.rerun()

st.divider()

# --- PILIHAN MODE KERJA ---
st.write("Pilih jenis pekerjaan yang ingin dilakukan hari ini:")
mode_kerja = st.radio(
    "Mode Aplikasi",
    ["🧹 Hanya Bersihkan Kotak Pink Anotasi", "🚀 Bersihkan Anotasi & Jahit Foto Progres", "📸 Generator Foto Kegiatan Watermark"],
    label_visibility="collapsed",
    horizontal=True
)
st.divider()

# ==========================================
# LOGIKA MENU 1 & 2 (PEMROSESAN PDF)
# ==========================================
if "Bersihkan" in mode_kerja:
    pdf_inputs = st.file_uploader("📥 Unggah PDF Checklist Dasar (Bisa blok banyak file sekaligus)", type=["pdf"], accept_multiple_files=True)
    data_siap_proses = []

    if "Jahit" in mode_kerja:
        st.subheader("📸 Form Rangkaian Foto Progres")
        st.write("*Isi maksimal 5 aset. Yang dikosongkan akan dilewati otomatis.*")

        for i in range(1, 6):
            st.markdown(f"**Rangkaian Aset ke-{i}**")
            nama_aset = st.text_input(f"Nama Aset {i}", key=f"nama_{i}", placeholder="Contoh: Peraga Sinyal")
            
            col1, col2, col3 = st.columns(3)
            with col1:
                img_0 = st.file_uploader("Foto 0%", key=f"img0_{i}", type=["jpg", "jpeg", "png"])
                if img_0: st.image(img_0, use_container_width=True, caption="0%") 
            with col2:
                img_50 = st.file_uploader("Foto 50%", key=f"img50_{i}", type=["jpg", "jpeg", "png"])
                if img_50: st.image(img_50, use_container_width=True, caption="50%") 
            with col3:
                img_100 = st.file_uploader("Foto 100%", key=f"img100_{i}", type=["jpg", "jpeg", "png"])
                if img_100: st.image(img_100, use_container_width=True, caption="100%") 
            
            if nama_aset and img_0 and img_50 and img_100:
                data_siap_proses.append({
                    "nama_aset": nama_aset,
                    "img_0": img_0,
                    "img_50": img_50,
                    "img_100": img_100
                })
            st.divider()

    if pdf_inputs:
        if "Hanya" in mode_kerja:
            if st.button(f"🧹 Bersihkan {len(pdf_inputs)} File Anotasi Sekarang", use_container_width=True):
                with st.spinner("Sedang membersihkan kotak pink pada file PDF..."):
                    if len(pdf_inputs) == 1:
                        pdf_file = pdf_inputs[0]
                        hasil_pdf_bytes = proses_dokumen(pdf_file, [])
                        nama_file_unduh = pdf_file.name[:-4] + " revisi.pdf" if pdf_file.name.lower().endswith(".pdf") else pdf_file.name + " revisi.pdf"
                        
                        st.success("✨ Selesai! Kotak pink berhasil dihapus dan tabel laporan aman utuh.")
                        st.download_button("⬇️ Unduh File Bersih", data=hasil_pdf_bytes, file_name=nama_file_unduh, mime="application/pdf", use_container_width=True)
                    else:
                        zip_buffer = io.BytesIO()
                        with zipfile.ZipFile(zip_buffer, "w", zipfile.ZIP_DEFLATED) as zip_file:
                            for pdf_file in pdf_inputs:
                                hasil_pdf_bytes = proses_dokumen(pdf_file, [])
                                nama_file_unduh = pdf_file.name[:-4] + " revisi.pdf" if pdf_file.name.lower().endswith(".pdf") else pdf_file.name + " revisi.pdf"
                                zip_file.writestr(nama_file_unduh, hasil_pdf_bytes)
                        
                        st.success(f"✨ Selesai! {len(pdf_inputs)} file berhasil dibersihkan dari anotasi tanpa merusak tabel.")
                        st.download_button("⬇️ Unduh Semua File (ZIP)", data=zip_buffer.getvalue(), file_name="Laporan_Sintel_Bersih.zip", mime="application/zip", use_container_width=True)
                        
        elif "Jahit" in mode_kerja:
            if len(pdf_inputs) > 1:
                st.info("ℹ️ Perhatian: Pada mode jahit foto, sistem hanya akan memproses file PDF yang letaknya paling pertama.")
                
            if len(data_siap_proses) > 0:
                st.success(f"✅ Ada {len(data_siap_proses)} rangkaian foto yang siap dijahit.")
                if st.button("🚀 Menjahit Dokumen Sekarang!", use_container_width=True):
                    with st.spinner("Sedang membersihkan PDF dan menjahit lampiran foto..."):
                        pdf_file = pdf_inputs[0] 
                        hasil_pdf_bytes = proses_dokumen(pdf_file, data_siap_proses)
                        nama_file_unduh = pdf_file.name[:-4] + " revisi.pdf" if pdf_file.name.lower().endswith(".pdf") else pdf_file.name + " revisi.pdf"
                        
                        animasi_lari = """
                        <style>
                        @keyframes sprint {
                          0% { transform: translateX(-50%); opacity: 1; }
                          95% { transform: translateX(90%); opacity: 1; }
                          100% { transform: translateX(100%); opacity: 0; }
                        }
                        .track-lari {
                          overflow: hidden;
                          width: 100%;
                          background-color: rgba(40, 37, 98, 0.5); /* Warna trek biru gelap KAI */
                          padding: 5px 0;
                          border-radius: 8px;
                          border-right: 12px solid #ec6923; /* Pita Garis Finish Oranye KAI */
                          border-bottom: 3px dashed #64748B;
                          margin-bottom: 15px;
                        }
                        .pelari {
                          display: inline-block;
                          font-size: 50px;
                          animation: sprint 2.5s cubic-bezier(0.25, 0.1, 0.25, 1) forwards;
                        }
                        .teks-finish {
                          text-align: center;
                          color: #ec6923;
                          font-weight: 800;
                          font-size: 1.3rem;
                          margin-top: 5px;
                          text-shadow: 1px 1px 2px rgba(0,0,0,0.5);
                        }
                        </style>
                        <div class="track-lari">
                          <div class="pelari">🏃‍♂️💨</div>
                        </div>
                        <div class="teks-finish">🏆 FINISH STRONG! Dokumen Selesai Dijahit!</div>
                        """
                        st.markdown(animasi_lari, unsafe_allow_html=True)
                        st.download_button("⬇️ Unduh File Final: " + nama_file_unduh, data=hasil_pdf_bytes, file_name=nama_file_unduh, mime="application/pdf", use_container_width=True)
            else:
                st.warning("⚠️ Mohon lengkapi minimal satu rangkaian aset untuk dijahit.")

# ==========================================
# LOGIKA MENU 3 (GENERATOR WATERMARK FOTO)
# ==========================================
elif "Watermark" in mode_kerja:
    st.subheader("📸 Foto Watermark")
    
    uploaded_image = st.file_uploader("Pilih foto kegiatan yang masih polos...", type=['jpg', 'jpeg', 'png'])

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
            
            dimensi_dasar = min(image_wm.width, image_wm.height)
            ukuran_font = int(dimensi_dasar * 0.028)
            if ukuran_font < 20: 
                ukuran_font = 20
                
            batas_karakter = int((image_wm.width * 0.80) / (ukuran_font * 0.55))
            
            lokasi_lipat = "\n".join(textwrap.wrap(lokasi, width=batas_karakter))
            kegiatan_lipat = "\n".join(textwrap.wrap(kegiatan, width=batas_karakter))
            
            teks_watermark = f"{waktu}\n\n{lokasi_lipat}\n\n{koordinat}\n\n{kegiatan_lipat}"
            
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
            
            margin_x = int(image_wm.width * 0.05)
            margin_y = int(image_wm.height * 0.05)
            spacing_teks = int(ukuran_font * 0.3)
            
            try:
                bbox = draw.multiline_textbbox((0, 0), teks_watermark, font=font, spacing=spacing_teks)
                tinggi_teks_total = bbox[3] - bbox[1]
            except AttributeError:
                if font != ImageFont.load_default():
                    tinggi_teks_total = (teks_watermark.count('\n') + 1) * int(ukuran_font * 1.3)
                else:
                    tinggi_teks_total = (teks_watermark.count('\n') + 1) * 15 
            
            lebar_garis = int(ukuran_font * 0.25)
            if lebar_garis < 5: lebar_garis = 5
            
            draw.rectangle(
                [margin_x, margin_y, margin_x + lebar_garis, margin_y + tinggi_teks_total],
                fill="blue"
            )
            
            text_x = margin_x + lebar_garis + int(ukuran_font * 0.6)
            text_y = margin_y
            
            for adj_x in [-2, -1, 0, 1, 2]:
                for adj_y in [-2, -1, 0, 1, 2]:
                    draw.multiline_text((text_x + adj_x, text_y + adj_y), teks_watermark, font=font, fill="black", spacing=spacing_teks)
                    
            draw.multiline_text((text_x, text_y), teks_watermark, font=font, fill="white", spacing=spacing_teks)
            
            st.image(image_wm, caption="Hasil Jahitan Watermark", use_container_width=True)

            buf_img = io.BytesIO()
            image_wm.save(buf_img, format="JPEG")
            byte_im = buf_img.getvalue()
            
            st.download_button(
                label="⬇️ Unduh Foto",
                data=byte_im,
                file_name="Foto_Watermark_Sintel.jpg",
                mime="image/jpeg",
                use_container_width=True
            )
