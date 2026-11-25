import streamlit as st
import fitz  # PyMuPDF
from PIL import Image, ImageDraw, ImageFont
import io
import zipfile
import urllib.request
import textwrap

# --- KONFIGURASI USERNAME & PASSWORD ---
USER_VALID = "Sintel46"
PASS_VALID = "IMO2025."

# --- KONFIGURASI HALAMAN ---
st.set_page_config(page_title="PAGE IMO2025 X dR", page_icon="📑", layout="wide")

# --- STATE MANAGEMENT ---
if "login_sukses" not in st.session_state:
    st.session_state.login_sukses = False
if "dark_mode" not in st.session_state:
    st.session_state.dark_mode = True
if "menu_aktif" not in st.session_state:
    st.session_state.menu_aktif = "📅 Auto-Ubah Tanggal PDF & Foto"
if "riwayat_proses" not in st.session_state:
    st.session_state.riwayat_proses = [
        {"waktu": "Hari ini", "modul": "Sistem Siap", "detail": "Menunggu dokumen checklist Sintel Daop 4"}
    ]

# --- PALET WARNA DINAMIS (LIGHT & DARK MODE KAI) ---
if st.session_state.dark_mode:
    BG_APP, BG_SIDEBAR, BG_CARD, BORDER_CARD = "#0B0F19", "#111827", "#151C2C", "#1E293B"
    TEXT_PRIMARY, TEXT_SECONDARY, INPUT_BG = "#F8FAFC", "#94A3B8", "#0F172A"
else:
    BG_APP, BG_SIDEBAR, BG_CARD, BORDER_CARD = "#F4F6FA", "#FFFFFF", "#FFFFFF", "#E2E8F0"
    TEXT_PRIMARY, TEXT_SECONDARY, INPUT_BG = "#0F172A", "#64748B", "#F8FAFC"

KAI_BLUE, KAI_BLUE_LIGHT, KAI_ORANGE = "#282562", "#3B378C", "#ec6923"

# --- CUSTOM CSS RINGKAS ---
css_tema = f"""<style>
@import url('https://fonts.googleapis.com/css2?family=Plus+Jakarta+Sans:wght@400;600;700;800;900&display=swap');
#MainMenu, header, footer {{visibility: hidden;}}
html, body, [class*="css"] {{font-family: 'Plus Jakarta Sans', sans-serif !important;}}
.stApp {{background-color: {BG_APP}; color: {TEXT_PRIMARY};}}
section[data-testid="stSidebar"] {{background-color: {BG_SIDEBAR} !important; border-right: 1px solid {BORDER_CARD};}}
.stMarkdown p, label, span {{color: {TEXT_PRIMARY} !important;}}
.title-kai {{font-size: 2.3rem; font-weight: 900; margin: 0; color: {KAI_BLUE}; -webkit-text-stroke: 1.2px #FFFFFF; text-shadow: 2px 2px 6px rgba(0,0,0,0.7);}}
.login-brand-panel {{background: linear-gradient(145deg, {KAI_BLUE} 0%, #17153B 65%, {KAI_ORANGE} 140%); border-radius: 20px; padding: 40px 32px; color: #FFFFFF !important; border: 1px solid rgba(255,255,255,0.12);}}
.login-brand-panel h1 {{font-size: 3.2rem; font-weight: 900; color: {KAI_BLUE}; -webkit-text-stroke: 1.5px #FFFFFF; margin-bottom: 10px;}}
.login-brand-panel p {{color: #E2E8F0 !important; font-size: 0.95rem;}}
.feature-pill {{display: inline-block; background: rgba(255,255,255,0.12); border: 1px solid rgba(255,255,255,0.2); padding: 6px 12px; border-radius: 12px; font-size: 0.78rem; font-weight: 600; color: #FFFFFF !important; margin: 8px 6px 0 0;}}
.bento-card {{background-color: {BG_CARD}; border: 1px solid {BORDER_CARD}; border-radius: 16px; padding: 20px; margin-bottom: 16px;}}
.bento-hero {{background: linear-gradient(135deg, {KAI_BLUE} 0%, {KAI_BLUE_LIGHT} 60%, {KAI_ORANGE} 135%); border-radius: 16px; padding: 20px; color: #FFFFFF !important; margin-bottom: 16px;}}
.bento-hero * {{color: #FFFFFF !important;}}
.kpi-title {{font-size: 0.76rem; font-weight: 600; color: {TEXT_SECONDARY} !important; text-transform: uppercase;}}
.kpi-value {{font-size: 1.9rem; font-weight: 800; color: {TEXT_PRIMARY} !important; margin: 4px 0;}}
.kpi-badge-orange {{background-color: rgba(236,105,35,0.18); color: {KAI_ORANGE} !important; padding: 3px 10px; border-radius: 999px; font-size: 0.74rem; font-weight: 700;}}
.ai-orb-box {{background-color: {BG_CARD}; border: 1px solid {BORDER_CARD}; border-radius: 16px; padding: 20px; text-align: center;}}
.ai-orb {{width: 78px; height: 78px; margin: 10px auto 14px auto; border-radius: 50%; background: radial-gradient(circle at 30% 30%, {KAI_ORANGE}, {KAI_BLUE} 70%, #090D16 100%); box-shadow: 0 0 28px rgba(236,105,35,0.55); animation: pulseOrb 3s infinite ease-in-out;}}
@keyframes pulseOrb {{0% {{transform: scale(0.96);}} 50% {{transform: scale(1.04);}} 100% {{transform: scale(0.96);}}}}
.stButton>button {{background-color: {KAI_BLUE} !important; color: #FFFFFF !important; font-weight: 600 !important; border-radius: 10px !important; border: 1px solid rgba(255,255,255,0.2) !important; padding: 0.6rem 1.2rem !important; transition: all 0.25s ease !important;}}
.stButton>button:hover {{background-color: {KAI_ORANGE} !important; border: 1px solid #FFFFFF !important; transform: translateY(-2px);}}
.stTextInput>div>div>input, .stTextArea>div>div>textarea, .stNumberInput>div>div>input {{border-radius: 10px !important; border: 1.5px solid {KAI_BLUE} !important; background-color: {INPUT_BG} !important; color: {TEXT_PRIMARY} !important;}}
hr {{border-top: 1px solid {BORDER_CARD} !important;}}
</style>"""
st.markdown(css_tema, unsafe_allow_html=True)
if not st.session_state.login_sukses:
    st.write("")
    _, col_left, col_right, _ = st.columns([0.5, 2.3, 2.1, 0.5], gap="large")
    with col_left:
        st.markdown("""<div class='login-brand-panel'><div style='font-size:0.8rem; font-weight:700; letter-spacing:1.5px; color:#EC6923 !important; margin-bottom:8px;'>SINTEL DAOP 4 SEMARANG</div><h1>IMO2025 📑 dR</h1><p>Ruang kerja digital otomasi dokumen perawatan prasarana sinyal & telekomunikasi.</p><div style='margin-top:24px;'><span class='feature-pill'>📅 Auto-Tanggal PDF</span><span class='feature-pill'>🧹 Hapus Kotak Pink</span><span class='feature-pill'>🚀 Jahit Foto 0-50-100%</span><span class='feature-pill'>📸 Watermark</span></div></div>""", unsafe_allow_html=True)
    with col_right:
        st.markdown("<div class='bento-card' style='padding: 36px 32px;'>", unsafe_allow_html=True)
        st.markdown("### Masuk Ruang Kerja 👋")
        username = st.text_input("Username")
        password = st.text_input("Password", type="password")
        if st.button("Masuk Ruang Kerja", use_container_width=True):
            if username == USER_VALID and password == PASS_VALID:
                st.session_state.login_sukses = True
                st.rerun()
            else:
                st.error("❌ Username atau Password salah!")
        st.markdown("</div>", unsafe_allow_html=True)
    st.stop()

with st.sidebar:
    st.markdown("<p class='title-kai'>IMO2025 📑 dR</p>", unsafe_allow_html=True)
    st.caption("Sintel Daop 4 Semarang • Automation Suite")
    st.divider()
    st.session_state.menu_aktif = st.radio("Mode Aplikasi", [
        "📅 Auto-Ubah Tanggal PDF & Foto",
        "🧹 Hanya Bersihkan Kotak Pink Anotasi",
        "🚀 Bersihkan Anotasi & Jahit Foto Progres",
        "📸 Generator Foto Kegiatan Watermark"
    ], label_visibility="collapsed")
    st.divider()
    mode_gelap = st.toggle("🌙 Dark Mode KAI", value=st.session_state.dark_mode)
    if mode_gelap != st.session_state.dark_mode:
        st.session_state.dark_mode = mode_gelap
        st.rerun()
    st.write("")
    if st.button("🚪 Keluar", use_container_width=True):
        st.session_state.login_sukses = False
        st.rerun()

top_col1, top_col2 = st.columns([3.5, 1.5])
with top_col1:
    st.markdown("### Selamat Bekerja, Tim Sintel 4.6 👋")
with top_col2:
    st.markdown("<div style='text-align:right; padding-top:8px;'><span class='kpi-badge-orange'>KAI THEME • NAVY & ORANGE</span></div>", unsafe_allow_html=True)

kpi1, kpi2, kpi3, kpi4 = st.columns([1.4, 1, 1, 1.2])
with kpi1:
    st.markdown("<div class='bento-hero'><div style='font-size:0.76rem; font-weight:700;'>ENGINE TERPADU</div><div style='font-size:1.3rem; font-weight:800; margin:4px 0;'>IMO2025 All-in-One</div><div style='font-size:0.76rem;'>4 Modul Otomasi Sintel</div></div>", unsafe_allow_html=True)
with kpi2:
    st.markdown("<div class='bento-card'><div class='kpi-title'>Filter Anotasi</div><div class='kpi-value'>Smart</div><span class='kpi-badge-orange'>Foto Besar Aman</span></div>", unsafe_allow_html=True)
with kpi3:
    st.markdown("<div class='bento-card'><div class='kpi-title'>Auto-Tanggal</div><div class='kpi-value'>Multi</div><span class='kpi-badge-orange'>Teks + Foto PDF</span></div>", unsafe_allow_html=True)
with kpi4:
    st.markdown(f"<div class='bento-card'><div class='kpi-title'>Dokumen Diproses</div><div class='kpi-value'>{len(st.session_state.riwayat_proses) - 1}</div><span class='kpi-badge-orange'>Sesi Hari Ini</span></div>", unsafe_allow_html=True)

main_area, right_panel = st.columns([2.7, 1.05], gap="medium")

with main_area:
    if st.session_state.menu_aktif == "📅 Auto-Ubah Tanggal PDF & Foto":
        st.markdown("<div class='bento-card'>", unsafe_allow_html=True)
        st.markdown("#### 📅 Auto-Ubah Tanggal Multi-Format & Watermark Foto")
        pdf_tanggal = st.file_uploader("📥 Unggah File PDF Laporan Perawatan", type=["pdf"])
        c1, c2 = st.columns(2)
        with c1:
            lama_1 = st.text_input("Teks Tanggal Lama #1", value="20 September 2026")
            lama_2 = st.text_input("Teks Tanggal Lama #2", value="2026-09-20")
            lama_3 = st.text_input("Teks Tanggal Lama #3 (Opsional)", value="")
        with c2:
            baru_1 = st.text_input("Teks Tanggal Baru #1", value="03 Januari 2025")
            baru_2 = st.text_input("Teks Tanggal Baru #2", value="2025-01-03")
            baru_3 = st.text_input("Teks Tanggal Baru #3 (Opsional)", value="")
        edit_foto_pdf = st.checkbox("✅ Ikut perbarui baris tanggal di dalam foto dokumentasi PDF", value=True)
        teks_wm_baru = st.text_input("Teks Hari & Tanggal Baru pada Foto", value="Jumat, 03 Januari 2025")
        with st.expander("⚙️ Kalibrasi Presisi Font & Area Foto (Opsional)"):
            ck1, ck2 = st.columns(2)
            with ck1:
                ukuran_font = st.number_input("Ukuran Font Teks PDF (0 = Otomatis)", 0.0, 24.0, 0.0, 0.5)
                geser_y = st.number_input("Geser Vertikal Teks PDF", -10.0, 10.0, 0.0, 0.5)
            with ck2:
                x1_r = st.slider("Lebar Area Tutup Tanggal Foto", 0.45, 0.85, 0.63, 0.01)
                y0_r = st.slider("Batas Atas Baris Tanggal Foto", 0.65, 0.85, 0.725, 0.005)
                y1_r = st.slider("Batas Bawah Baris Tanggal Foto", 0.70, 0.90, 0.775, 0.005)
        if pdf_tanggal and st.button("🔄 Eksekusi Perubahan Tanggal & Foto Sekarang", use_container_width=True):
            hasil_pdf_tgl, jml_teks, jml_gbr = proses_multi_tanggal_pdf(pdf_tanggal, [(lama_1, baru_1), (lama_2, baru_2), (lama_3, baru_3)], edit_foto_pdf, teks_wm_baru, ukuran_font, geser_y, 0.015, y0_r, x1_r, y1_r)
            st.session_state.riwayat_proses.insert(0, {"waktu": "Baru saja", "modul": "Auto-Tanggal", "detail": f"{pdf_tanggal.name[:22]}... ({jml_teks} teks, {jml_gbr} foto)"})
            st.success(f"✅ Berhasil! **{jml_teks} teks PDF** dan **{jml_gbr} foto dokumentasi** diperbarui.")
            st.download_button("⬇️ Unduh PDF Hasil Revisi", hasil_pdf_tgl, f"Revisi_{pdf_tanggal.name.replace('20-09-2026', '03-01-2025')}", "application/pdf", use_container_width=True)
        st.markdown("</div>", unsafe_allow_html=True)

    elif "Bersihkan" in st.session_state.menu_aktif:
        st.markdown("<div class='bento-card'>", unsafe_allow_html=True)
        pdf_inputs = st.file_uploader("📥 Unggah PDF Checklist Dasar (Bisa blok banyak file sekaligus)", type=["pdf"], accept_multiple_files=True)
        data_siap_proses = []
        if "Jahit" in st.session_state.menu_aktif:
            st.subheader("📸 Form Rangkaian Foto Progres")
            for i in range(1, 6):
                with st.expander(f"📌 Rangkaian Aset ke-{i}", expanded=(i == 1)):
                    nama_aset = st.text_input(f"Nama Aset {i}", key=f"nama_{i}", placeholder="Contoh: Peraga Sinyal")
                    col1, col2, col3 = st.columns(3)
                    with col1:
                        img_0 = st.file_uploader("Foto 0%", key=f"img0_{i}", type=["jpg", "jpeg", "png"])
                        if img_0: st.image(img_0, use_container_width=True, caption="FOTO 0%")
                    with col2:
                        img_50 = st.file_uploader("Foto 50%", key=f"img50_{i}", type=["jpg", "jpeg", "png"])
                        if img_50: st.image(img_50, use_container_width=True, caption="FOTO 50%")
                    with col3:
                        img_100 = st.file_uploader("Foto 100%", key=f"img100_{i}", type=["jpg", "jpeg", "png"])
                        if img_100: st.image(img_100, use_container_width=True, caption="FOTO 100%")
                    if nama_aset and img_0 and img_50 and img_100:
                        data_siap_proses.append({"nama_aset": nama_aset, "img_0": img_0, "img_50": img_50, "img_100": img_100})
        if pdf_inputs:
            if "Hanya" in st.session_state.menu_aktif and st.button(f"🧹 Bersihkan {len(pdf_inputs)} File Anotasi Sekarang", use_container_width=True):
                if len(pdf_inputs) == 1:
                    pdf_file = pdf_inputs[0]
                    hasil_pdf_bytes = proses_dokumen(pdf_file, [])
                    nama_unduh = pdf_file.name[:-4] + " revisi.pdf" if pdf_file.name.lower().endswith(".pdf") else pdf_file.name + " revisi.pdf"
                    st.session_state.riwayat_proses.insert(0, {"waktu": "Baru saja", "modul": "Clean Anotasi", "detail": pdf_file.name[:26]})
                    st.success("✨ Selesai! Kotak pink berhasil dihapus.")
                    st.download_button("⬇️ Unduh File Bersih", data=hasil_pdf_bytes, file_name=nama_unduh, mime="application/pdf", use_container_width=True)
                else:
                    zip_buffer = io.BytesIO()
                    with zipfile.ZipFile(zip_buffer, "w", zipfile.ZIP_DEFLATED) as zip_file:
                        for pdf_file in pdf_inputs:
                            nama_unduh = pdf_file.name[:-4] + " revisi.pdf" if pdf_file.name.lower().endswith(".pdf") else pdf_file.name + " revisi.pdf"
                            zip_file.writestr(nama_unduh, proses_dokumen(pdf_file, []))
                    st.session_state.riwayat_proses.insert(0, {"waktu": "Baru saja", "modul": "Batch ZIP", "detail": f"{len(pdf_inputs)} file PDF"})
                    st.success(f"✨ Selesai! {len(pdf_inputs)} file dibersihkan.")
                    st.download_button("⬇️ Unduh Semua File (ZIP)", data=zip_buffer.getvalue(), file_name="Laporan_Sintel_Bersih.zip", mime="application/zip", use_container_width=True)
            elif "Jahit" in st.session_state.menu_aktif and len(data_siap_proses) > 0 and st.button("🚀 Menjahit Dokumen Sekarang!", use_container_width=True):
                pdf_file = pdf_inputs[0]
                hasil_pdf_bytes = proses_dokumen(pdf_file, data_siap_proses)
                nama_unduh = pdf_file.name[:-4] + " revisi.pdf" if pdf_file.name.lower().endswith(".pdf") else pdf_file.name + " revisi.pdf"
                st.session_state.riwayat_proses.insert(0, {"waktu": "Baru saja", "modul": "Jahit Foto", "detail": f"{len(data_siap_proses)} aset dijahit"})
                st.markdown("""<style>@keyframes sprint{0%{transform:translateX(-50%);}95%{transform:translateX(90%);}100%{transform:translateX(100%);opacity:0;}}.track-lari{overflow:hidden;width:100%;background:rgba(40,37,98,0.5);padding:5px 0;border-radius:8px;border-right:12px solid #ec6923;margin-bottom:15px;}.pelari{display:inline-block;font-size:50px;animation:sprint 2.5s forwards;}</style><div class="track-lari"><div class="pelari">🏃‍♂️💨</div></div><div style="text-align:center;color:#ec6923;font-weight:800;font-size:1.3rem;">🏆 FINISH ! Dokumen Selesai Dijahit!</div>""", unsafe_allow_html=True)
                st.download_button("⬇️ Unduh File Final: " + nama_unduh, data=hasil_pdf_bytes, file_name=nama_unduh, mime="application/pdf", use_container_width=True)
        st.markdown("</div>", unsafe_allow_html=True)

    elif "Watermark" in st.session_state.menu_aktif:
        st.markdown("<div class='bento-card'>", unsafe_allow_html=True)
        st.subheader("📸 Foto Watermark")
        uploaded_image = st.file_uploader("Pilih foto kegiatan yang masih polos...", type=['jpg', 'jpeg', 'png'])
        if uploaded_image is not None:
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
                ukuran_font = max(20, int(min(image_wm.width, image_wm.height) * 0.028))
                batas_karakter = int((image_wm.width * 0.80) / (ukuran_font * 0.55))
                teks_watermark = f"{waktu}\n\n{chr(10).join(textwrap.wrap(lokasi, width=batas_karakter))}\n\n{koordinat}\n\n{chr(10).join(textwrap.wrap(kegiatan, width=batas_karakter))}"
                try:
                    req = urllib.request.Request("https://github.com/googlefonts/roboto/raw/main/src/hinted/Roboto-Medium.ttf", headers={'User-Agent': 'Mozilla/5.0'})
                    font = ImageFont.truetype(io.BytesIO(urllib.request.urlopen(req, timeout=5).read()), ukuran_font)
                except Exception:
                    font = ImageFont.load_default()
                margin_x, margin_y, spacing_teks = int(image_wm.width * 0.05), int(image_wm.height * 0.05), int(ukuran_font * 0.3)
                try:
                    bbox = draw.multiline_textbbox((0, 0), teks_watermark, font=font, spacing=spacing_teks)
                    tinggi_teks = bbox[3] - bbox[1]
                except Exception:
                    tinggi_teks = (teks_watermark.count('\n') + 1) * int(ukuran_font * 1.3)
                lebar_garis = max(5, int(ukuran_font * 0.25))
                draw.rectangle([margin_x, margin_y, margin_x + lebar_garis, margin_y + tinggi_teks], fill="blue")
                text_x = margin_x + lebar_garis + int(ukuran_font * 0.6)
                for ax in [-2, -1, 0, 1, 2]:
                    for ay in [-2, -1, 0, 1, 2]:
                        draw.multiline_text((text_x + ax, margin_y + ay), teks_watermark, font=font, fill="black", spacing=spacing_teks)
                draw.multiline_text((text_x, margin_y), teks_watermark, font=font, fill="white", spacing=spacing_teks)
                st.session_state.riwayat_proses.insert(0, {"waktu": "Baru saja", "modul": "Watermark Foto", "detail": kegiatan[:26]})
                st.image(image_wm, caption="Hasil Jahitan Watermark", use_container_width=True)
                buf_img = io.BytesIO()
                image_wm.save(buf_img, format="JPEG")
                st.download_button("⬇️ Unduh Foto", data=buf_img.getvalue(), file_name="Foto_Watermark_Sintel.jpg", mime="image/jpeg", use_container_width=True)
        st.markdown("</div>", unsafe_allow_html=True)

with right_panel:
    st.markdown(f"<div class='ai-orb-box'><div style='font-size:0.78rem; font-weight:700; color:{KAI_ORANGE}; letter-spacing:1px;'>SERENA ENGINE</div><div class='ai-orb'></div><div style='font-weight:800; font-size:1.05rem; margin-bottom:4px;'>Smart Document Sync</div><div style='font-size:0.78rem; color:{TEXT_SECONDARY};'>4 modul aktif: Auto-Tanggal PDF & Foto, Pembersih Kotak Pink, Penjahit Progres, dan Watermark.</div></div>", unsafe_allow_html=True)
    st.write("")
    st.markdown("<div class='bento-card'>", unsafe_allow_html=True)
    st.markdown("##### 🕒 Aktivitas Terbaru")
    for item in st.session_state.riwayat_proses[:5]:
        st.markdown(f"<div style='border-bottom:1px solid {BORDER_CARD}; padding:8px 0;'><div style='display:flex; justify-content:space-between; font-size:0.74rem;'><span style='font-weight:700; color:{KAI_ORANGE};'>{item['modul']}</span><span style='color:{TEXT_SECONDARY};'>{item['waktu']}</span></div><div style='font-size:0.79rem; margin-top:2px;'>{item['detail']}</div></div>", unsafe_allow_html=True)
    st.markdown("</div>", unsafe_allow_html=True)
