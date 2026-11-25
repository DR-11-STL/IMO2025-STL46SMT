import streamlit as st
import fitz  # PyMuPDF
from PIL import Image, ImageDraw, ImageFont, ImageFilter, ImageEnhance
import io
import zipfile
import urllib.request
import textwrap
import re
import datetime

USER_VALID = "Sintel46"
PASS_VALID = "IMO2025."

st.set_page_config(page_title="PAGE IMO2025 X dR", page_icon="📑", layout="wide")

if "login_sukses" not in st.session_state:
    st.session_state.login_sukses = False
if "dark_mode" not in st.session_state:
    st.session_state.dark_mode = True
if "menu_aktif" not in st.session_state:
    st.session_state.menu_aktif = "📅 Auto-Ubah Tanggal PDF & Foto"
if "riwayat_proses" not in st.session_state:
    st.session_state.riwayat_proses = [
        {"waktu": "Hari ini", "modul": "Sistem Siap", "detail": "Menunggu dokumen checklist"}
    ]

NAVY_RGB = "rgb(40, 37, 98)"
ORANGE_RGB = "rgb(236, 105, 35)"

if st.session_state.dark_mode:
    BG_APP, BG_SIDEBAR, BG_CARD, BORDER_CARD = "#0B0E17", "#101422", "#14192B", "rgba(40, 37, 98, 0.55)"
    TEXT_PRIMARY, TEXT_SECONDARY, INPUT_BG = "#F8FAFC", "#94A3B8", "#0E1220"
else:
    BG_APP, BG_SIDEBAR, BG_CARD, BORDER_CARD = "#F4F6FA", "#FFFFFF", "#FFFFFF", "rgba(40, 37, 98, 0.2)"
    TEXT_PRIMARY, TEXT_SECONDARY, INPUT_BG = "#0F172A", "#64748B", "#F8FAFC"

css_tema = f"""<style>
@import url('https://fonts.googleapis.com/css2?family=Plus+Jakarta+Sans:wght@400;600;700;800;900&display=swap');
#MainMenu, header, footer {{visibility: hidden;}}
html, body, [class*="css"] {{font-family: 'Plus Jakarta Sans', sans-serif !important;}}
.stApp {{background-color: {BG_APP}; color: {TEXT_PRIMARY};}}
section[data-testid="stSidebar"] {{background-color: {BG_SIDEBAR} !important; border-right: 1px solid {BORDER_CARD};}}
.stMarkdown p, label, span {{color: {TEXT_PRIMARY} !important;}}
.title-kai {{font-size: 2.3rem; font-weight: 900; margin: 0; color: {NAVY_RGB}; -webkit-text-stroke: 1.2px #FFFFFF; text-shadow: 2px 2px 6px rgba(0,0,0,0.7);}}
.login-brand-panel {{background: linear-gradient(145deg, {NAVY_RGB} 0%, #191742 60%, {ORANGE_RGB} 135%); border-radius: 20px; padding: 40px 32px; color: #FFFFFF !important; border: 1px solid rgba(255,255,255,0.15);}}
.login-brand-panel h1 {{font-size: 3.2rem; font-weight: 900; color: {NAVY_RGB}; -webkit-text-stroke: 1.5px #FFFFFF; margin-bottom: 10px;}}
.login-brand-panel p {{color: #E2E8F0 !important; font-size: 0.95rem;}}
.feature-pill {{display: inline-block; background: rgba(255,255,255,0.12); border: 1px solid rgba(255,255,255,0.22); padding: 6px 12px; border-radius: 12px; font-size: 0.78rem; font-weight: 600; color: #FFFFFF !important; margin: 8px 6px 0 0;}}
.bento-card {{background-color: {BG_CARD}; border: 1px solid {BORDER_CARD}; border-radius: 16px; padding: 20px; margin-bottom: 16px;}}
.bento-hero {{background: linear-gradient(135deg, {NAVY_RGB} 0%, {ORANGE_RGB} 125%); border-radius: 16px; padding: 20px; color: #FFFFFF !important; margin-bottom: 16px;}}
.bento-hero * {{color: #FFFFFF !important;}}
.kpi-title {{font-size: 0.76rem; font-weight: 600; color: {TEXT_SECONDARY} !important; text-transform: uppercase;}}
.kpi-value {{font-size: 1.9rem; font-weight: 800; color: {TEXT_PRIMARY} !important; margin: 4px 0;}}
.kpi-badge-orange {{background-color: rgba(236, 105, 35, 0.18); color: {ORANGE_RGB} !important; padding: 3px 10px; border-radius: 999px; font-size: 0.74rem; font-weight: 700;}}
.ai-orb-box {{background-color: {BG_CARD}; border: 1px solid {BORDER_CARD}; border-radius: 16px; padding: 20px; text-align: center;}}
.ai-orb {{width: 78px; height: 78px; margin: 10px auto 14px auto; border-radius: 50%; background: radial-gradient(circle at 30% 30%, {ORANGE_RGB}, {NAVY_RGB} 70%, #090D16 100%); box-shadow: 0 0 28px rgba(236, 105, 35, 0.55); animation: pulseOrb 3s infinite ease-in-out;}}
@keyframes pulseOrb {{0% {{transform: scale(0.96);}} 50% {{transform: scale(1.04);}} 100% {{transform: scale(0.96);}}}}
.stButton>button {{background-color: {NAVY_RGB} !important; color: #FFFFFF !important; font-weight: 600 !important; border-radius: 10px !important; border: 1px solid rgba(255,255,255,0.2) !important; padding: 0.6rem 1.2rem !important; transition: all 0.25s ease !important;}}
.stButton>button:hover {{background-color: {ORANGE_RGB} !important; border: 1px solid #FFFFFF !important; transform: translateY(-2px);}}
.stTextInput>div>div>input, .stTextArea>div>div>textarea {{border-radius: 10px !important; border: 1.5px solid {NAVY_RGB} !important; background-color: {INPUT_BG} !important; color: {TEXT_PRIMARY} !important;}}
.stTextInput>div>div>input:focus, .stTextArea>div>div>textarea:focus {{border-color: {ORANGE_RGB} !important;}}
hr {{border-top: 1px solid {BORDER_CARD} !important;}}
</style>"""
st.markdown(css_tema, unsafe_allow_html=True)

def crop_center_square(image):
    max_dim = max(image.size)
    return image.resize((max_dim, max_dim))

def proses_dokumen(pdf_file, data_rangkaian):
    doc = fitz.open(stream=pdf_file.read(), filetype="pdf")
    for halaman in doc:
        while True:
            ada_yang_dihapus = False
            for anotasi in halaman.annots():
                if anotasi.type[1] != "Stamp" or anotasi.rect.height < 150:
                    halaman.delete_annot(anotasi)
                    ada_yang_dihapus = True
                    break
            if not ada_yang_dihapus:
                break
        halaman.clean_contents()

    if len(data_rangkaian) > 0:
        lebar_halaman, tinggi_halaman = 595, 842
        lebar_gambar, tinggi_gambar, spasi = 150, 150, 30
        mulai_x = (lebar_halaman - (3 * lebar_gambar + 2 * spasi)) / 2
        y_pos, items_per_page = 60, 0
        halaman_baru = doc.new_page(width=lebar_halaman, height=tinggi_halaman)

        for data in data_rangkaian:
            if items_per_page >= 3:
                halaman_baru = doc.new_page(width=lebar_halaman, height=tinggi_halaman)
                y_pos, items_per_page = 60, 0
            halaman_baru.insert_text(fitz.Point(mulai_x, y_pos), f"Nama Aset: {data['nama_aset']}", fontsize=14, color=(0, 0, 0))
            koleksi = [
                {"file": data["img_0"], "label": "Foto 0%"},
                {"file": data["img_50"], "label": "Foto 50%"},
                {"file": data["img_100"], "label": "Foto 100%"}
            ]
            for i, item in enumerate(koleksi):
                img_square = crop_center_square(Image.open(item["file"]))
                img_byte_arr = io.BytesIO()
                img_square.save(img_byte_arr, format='JPEG')
                x0 = mulai_x + i * (lebar_gambar + spasi)
                y0 = y_pos + 15
                halaman_baru.insert_image(fitz.Rect(x0, y0, x0 + lebar_gambar, y0 + tinggi_gambar), stream=img_byte_arr.getvalue())
                halaman_baru.insert_text(fitz.Point(x0 + 60, y0 + tinggi_gambar + 20), item["label"], fontsize=14, color=(0, 0, 0))
            y_pos += 210
            items_per_page += 1

    output_pdf = io.BytesIO()
    doc.save(output_pdf, garbage=2, deflate=True)
    doc.close()
    return output_pdf.getvalue()

def deteksi_tanggal_otomatis_pdf(pdf_bytes):
    doc = fitz.open(stream=pdf_bytes, filetype="pdf")
    gabungan_teks = "\n".join(hal.get_text("text") for hal in doc)
    doc.close()

    tgl_iso_ditemukan = ""
    tgl_indo_ditemukan = ""

    cari_iso = re.findall(r"\b(20\d{2}-\d{2}-\d{2})\b", gabungan_teks)
    if cari_iso:
        tgl_iso_ditemukan = cari_iso[0]

    bulan_regex = r"(?:Januari|Februari|Maret|April|Mei|Juni|Juli|Agustus|September|Oktober|November|Desember)"
    cari_indo = re.findall(rf"\b(\d{{1,2}}\s+{bulan_regex}\s+20\d{{2}})\b", gabungan_teks, flags=re.IGNORECASE)
    if cari_indo:
        tgl_indo_ditemukan = cari_indo[0]

    return tgl_iso_ditemukan, tgl_indo_ditemukan

def baca_metadata_foto_asli(img_rgba):
    """Membaca jam asli (baris 1) dan koordinat + alamat asli (baris 2-5) dari masing-masing foto."""
    w, h = img_rgba.size
    bx0, by0 = 0, int(h * 0.715)
    bx1, by1 = int(w * 0.90), int(h * 0.990)

    jam_hasil = None
    koord_hasil = None
    alamat_hasil = None

    def bersihkan_baris_asli(teks):
        t = re.sub(r"[^A-Za-z0-9,\s]", "", teks)
        t = re.sub(r"^([A-Za-z0-9]{1,2}\s+)+", "", t.strip())
        t = re.sub(r"(\s+[A-Za-z0-9]{1,2})+$", "", t.strip())
        t = re.sub(r"\s+", " ", t).strip(" ,")
        t = re.sub(r"Kota Semaran\b", "Kota Semarang", t, flags=re.IGNORECASE)
        t = re.sub(r"Kecamalan", "Kecamatan", t, flags=re.IGNORECASE)
        return t

    try:
        import pytesseract

        crop_dasar = img_rgba.crop((bx0, by0, bx1, by1)).convert("L")
        crop_besar = crop_dasar.resize((crop_dasar.width * 3, crop_dasar.height * 3), Image.Resampling.LANCZOS)

        kandidat_gambar = [
            ImageEnhance.Contrast(crop_besar).enhance(2.2),
            crop_besar.point(lambda p: 255 if p > 185 else 0),
            crop_besar.point(lambda p: 255 if p > 155 else 0),
        ]

        for gbr_uji in kandidat_gambar:
            teks_ocr = pytesseract.image_to_string(gbr_uji, config="--psm 6")

            if not jam_hasil:
                cari_jam = re.findall(r"\b([0-2]?\d:[0-5]\d)\b", teks_ocr)
                if cari_jam:
                    jam_hasil = cari_jam[0]

            if not koord_hasil:
                cari_koord = re.findall(r"(-?\d+\.\d+\s*,\s*\d+\.\d+)", teks_ocr)
                if cari_koord:
                    koord_hasil = cari_koord[0].replace(" ", "")

            if not alamat_hasil:
                semua_baris = [b.strip() for b in teks_ocr.splitlines() if b.strip()]
                idx_mulai = -1
                for i, b in enumerate(semua_baris):
                    if re.search(r"-?\d+\.\d+\s*,\s*\d+\.\d+", b):
                        idx_mulai = i + 1
                        break
                    elif any(k in b.lower() for k in ["kecamatan", "kota ", "kabupaten"]):
                        idx_mulai = i
                        break

                if idx_mulai != -1 and len(semua_baris) > idx_mulai:
                    kandidat_baris = []
                    for raw_b in semua_baris[idx_mulai : idx_mulai + 3]:
                        clean_b = bersihkan_baris_asli(raw_b)
                        if "indonesia" in clean_b.lower():
                            clean_b = "Indonesia"
                        elif "jawa tengah" in clean_b.lower():
                            clean_b = "Jawa Tengah"
                        if len(clean_b) >= 4:
                            kandidat_baris.append(clean_b)

                    if kandidat_baris and any(k in kandidat_baris[0].lower() for k in ["kecamatan", "kota", "kabupaten", "semarang", "genuk", "pedurungan", "gayamsari", "tawang", "poncol", "alastua"]):
                        if len(kandidat_baris) == 1:
                            kandidat_baris.extend(["Jawa Tengah", "Indonesia"])
                        elif len(kandidat_baris) == 2 and "indonesia" not in kandidat_baris[1].lower():
                            kandidat_baris.append("Indonesia")
                        alamat_hasil = kandidat_baris

            if jam_hasil and koord_hasil and alamat_hasil:
                break
    except Exception:
        pass

    return jam_hasil, koord_hasil, alamat_hasil

def patch_watermark_gambar(img_pil, teks_hari_tanggal_baru, fallback_meta=None):
    img = img_pil.convert("RGBA")
    w, h = img.size

    bx0, by0 = 0, int(h * 0.720)
    bx1, by1 = int(w * 0.885), int(h * 0.985)
    box_w, box_h = bx1 - bx0, by1 - by0

    jam_asli, koordinat_asli, baris_alamat = baca_metadata_foto_asli(img)

    if fallback_meta:
        if not jam_asli and fallback_meta.get("jam"):
            jam_asli = fallback_meta["jam"]
        if not koordinat_asli and fallback_meta.get("koord"):
            koordinat_asli = fallback_meta["koord"]
        if not baris_alamat and fallback_meta.get("alamat"):
            baris_alamat = fallback_meta["alamat"]

    jam_asli = jam_asli or "09:20"
    koordinat_asli = koordinat_asli or "-6.9817887,110.4731881"
    baris_alamat = baris_alamat or [
        "Kecamatan Genuk, Kota Semarang",
        "Jawa Tengah",
        "Indonesia"
    ]

    meta_terbaca = {"jam": jam_asli, "koord": koordinat_asli, "alamat": baris_alamat}

    strip_atas = img.crop((bx0, max(0, by0 - 5), bx1, max(1, by0 - 1))).resize((box_w, box_h), Image.Resampling.BICUBIC)
    strip_kanan = img.crop((min(w - 5, bx1 + 1), by0, min(w, bx1 + 5), by1)).resize((box_w, box_h), Image.Resampling.BICUBIC)
    tambalan_alami = Image.blend(strip_atas, strip_kanan, alpha=0.5).filter(ImageFilter.GaussianBlur(radius=max(3, int(box_h * 0.04))))

    mask = Image.new("L", (box_w, box_h), 255)
    pad = max(4, int(box_h * 0.05))
    ImageDraw.Draw(mask).rectangle([pad, pad, box_w - pad, box_h - pad], fill=255)
    mask = mask.filter(ImageFilter.GaussianBlur(radius=pad))
    img.paste(tambalan_alami, (bx0, by0), mask)

    overlay = Image.new("RGBA", img.size, (0, 0, 0, 0))
    draw = ImageDraw.Draw(overlay)
    draw.rectangle([bx0, by0, bx1, by1], fill=(8, 8, 8, 162))

    ukuran_font = max(11, int(w * 0.034))
    try:
        font = ImageFont.truetype("DejaVuSans.ttf", ukuran_font)
    except Exception:
        font = ImageFont.load_default()

    baris_teks = [
        f"{teks_hari_tanggal_baru} {jam_asli}",
        koordinat_asli
    ] + baris_alamat

    margin_kiri = int(w * 0.016)
    y_teks = by0 + int(box_h * 0.05)
    spasi_baris = int(ukuran_font * 1.32)

    for baris in baris_teks:
        for ox, oy in [(-1, 0), (1, 0), (0, -1), (0, 1), (1, 1)]:
            draw.text((margin_kiri + ox, y_teks + oy), baris, font=font, fill=(0, 0, 0, 210))
        draw.text((margin_kiri, y_teks), baris, font=font, fill=(255, 255, 255, 255))
        y_teks += spasi_baris

    return Image.alpha_composite(img, overlay).convert("RGB"), meta_terbaca

def deteksi_gaya_teks(halaman, teks_target):
    data_teks = halaman.get_text("dict")
    for blok in data_teks.get("blocks", []):
        for baris in blok.get("lines", []):
            gabungan = "".join(s.get("text", "") for s in baris.get("spans", ""))
            if teks_target.lower() in gabungan.lower():
                for span in baris.get("spans", []):
                    if any(kata in span.get("text", "").lower() for kata in teks_target.lower().split()):
                        nama_font = span.get("font", "").lower()
                        is_bold = ("bold" in nama_font) or bool(span.get("flags", 0) & 16)
                        return span.get("size", 9.0), is_bold, span.get("origin")
    return None, False, None

def proses_multi_tanggal_pdf(pdf_bytes, daftar_ganti, edit_gambar=True, teks_watermark_baru="Sabtu, 11 Januari 2025"):
    doc = fitz.open(stream=pdf_bytes, filetype="pdf")
    total_teks, total_gbr, xref_done = 0, 0, set()
    meta_terakhir = None

    for idx_hal, halaman in enumerate(doc):
        for teks_lama, teks_baru in daftar_ganti:
            if not teks_lama.strip():
                continue
            fs_asli, is_bold, origin_asli = deteksi_gaya_teks(halaman, teks_lama)
            for rect in halaman.search_for(teks_lama):
                fs = fs_asli if fs_asli else max(7.5, (rect.y1 - rect.y0) * 0.78)
                font_pakai = "hebo" if is_bold else "helv"
                halaman.add_redact_annot(rect, fill=(1, 1, 1))
                halaman.apply_redactions()
                y_tulis = origin_asli[1] if (origin_asli and abs(origin_asli[1] - rect.y1) < 5) else (rect.y1 - 1.5)
                halaman.insert_text(fitz.Point(rect.x0, y_tulis), teks_baru, fontsize=fs, fontname=font_pakai, color=(0, 0, 0))
                total_teks += 1

        if edit_gambar and idx_hal > 0:
            for img_info in halaman.get_images(full=True):
                xref = img_info[0]
                if xref in xref_done:
                    continue
                xref_done.add(xref)
                base_image = doc.extract_image(xref)
                w_img, h_img = base_image["width"], base_image["height"]
                if w_img < 180 or h_img < 180:
                    continue

                pil_cek = Image.open(io.BytesIO(base_image["image"])).convert("RGB")
                p_kiri_atas = pil_cek.getpixel((5, 5))
                p_kanan_atas = pil_cek.getpixel((w_img - 6, 5))
                if all(c > 245 for c in p_kiri_atas) and all(c > 245 for c in p_kanan_atas):
                    continue

                img_hasil, meta_terakhir = patch_watermark_gambar(pil_cek, teks_watermark_baru, meta_terakhir)
                buf = io.BytesIO()
                img_hasil.save(buf, format="JPEG", quality=88)
                halaman.replace_image(xref, stream=buf.getvalue())
                total_gbr += 1

        halaman.clean_contents()

    output_pdf = io.BytesIO()
    doc.save(output_pdf, garbage=3, deflate=True)
    doc.close()
    return output_pdf.getvalue(), total_teks, total_gbr

if not st.session_state.login_sukses:
    st.write("")
    st.write("")
    _, col_left, col_right, _ = st.columns([0.5, 2.3, 2.1, 0.5], gap="large")
    with col_left:
        st.markdown("""<div class='login-brand-panel'><h1>IMO2025 📑 dR</h1><p>Ruang kerja digital otomasi dokumen perawatan prasarana, pembersihan anotasi, dan sinkronisasi laporan.</p><div style='margin-top:24px;'><span class='feature-pill'>📅 Auto-Tanggal PDF</span><span class='feature-pill'>🧹 Hapus Kotak Pink</span><span class='feature-pill'>🚀 Jahit Foto 0-50-100%</span><span class='feature-pill'>📸 Watermark</span></div></div>""", unsafe_allow_html=True)
    with col_right:
        st.markdown("<div class='bento-card' style='padding: 36px 32px;'>", unsafe_allow_html=True)
        st.markdown("### Masuk Ruang Kerja 👋")
        st.caption("Silakan masukkan Username dan Password untuk melanjutkan.")
        st.write("")
        username = st.text_input("Username")
        password = st.text_input("Password", type="password")
        st.write("")
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
    st.caption("Automation Workspace Suite")
    st.divider()
    st.session_state.menu_aktif = st.radio("Mode Aplikasi", [
        "📅 Auto-Ubah Tanggal PDF & Foto",
        "🧹 Hanya Bersihkan Kotak Pink Anotasi",
        "🚀 Bersihkan Anotasi & Jahit Foto Progres",
        "📸 Generator Foto Kegiatan Watermark"
    ], label_visibility="collapsed")
    st.divider()
    mode_gelap = st.toggle("🌙 Dark Mode", value=st.session_state.dark_mode)
    if mode_gelap != st.session_state.dark_mode:
        st.session_state.dark_mode = mode_gelap
        st.rerun()
    st.write("")
    if st.button("🚪 Keluar", use_container_width=True):
        st.session_state.login_sukses = False
        st.rerun()

st.markdown("### Selamat Bekerja 👋")

kpi1, kpi2, kpi3, kpi4 = st.columns([1.4, 1, 1, 1.2])
with kpi1:
    st.markdown("<div class='bento-hero'><div style='font-size:0.76rem; font-weight:700;'>ENGINE TERPADU</div><div style='font-size:1.3rem; font-weight:800; margin:4px 0;'>IMO2025 All-in-One</div><div style='font-size:0.76rem;'>4 Modul Otomasi Dokumen</div></div>", unsafe_allow_html=True)
with kpi2:
    st.markdown("<div class='bento-card'><div class='kpi-title'>Filter Anotasi</div><div class='kpi-value'>Smart</div><span class='kpi-badge-orange'>Foto Besar Aman</span></div>", unsafe_allow_html=True)
with kpi3:
    st.markdown("<div class='bento-card'><div class='kpi-title'>Auto-Tanggal</div><div class='kpi-value'>Auto</div><span class='kpi-badge-orange'>Font & Foto PDF</span></div>", unsafe_allow_html=True)
with kpi4:
    st.markdown(f"<div class='bento-card'><div class='kpi-title'>Dokumen Diproses</div><div class='kpi-value'>{len(st.session_state.riwayat_proses) - 1}</div><span class='kpi-badge-orange'>Sesi Hari Ini</span></div>", unsafe_allow_html=True)

main_area, right_panel = st.columns([2.7, 1.05], gap="medium")

with main_area:
    if st.session_state.menu_aktif == "📅 Auto-Ubah Tanggal PDF & Foto":
        st.markdown("<div class='bento-card'>", unsafe_allow_html=True)
        st.markdown("#### 📅 Auto-Ubah Tanggal PDF & Foto (Deteksi Otomatis)")
        st.caption("Tanggal asli di dalam PDF otomatis terbaca saat file diunggah, dan seluruh teks serta foto akan sinkron ke tanggal baru.")
        pdf_tanggal = st.file_uploader("📥 Unggah File PDF Laporan Perawatan", type=["pdf"])

        default_lama_1 = "2026-10-01"
        default_lama_2 = "01 Oktober 2026"
        pdf_bytes_cache = None

        if pdf_tanggal is not None:
            pdf_bytes_cache = pdf_tanggal.getvalue()
            det_iso, det_indo = deteksi_tanggal_otomatis_pdf(pdf_bytes_cache)
            if det_iso:
                default_lama_1 = det_iso
            if det_indo:
                default_lama_2 = det_indo

        c1, c2 = st.columns(2)
        with c1:
            lama_1 = st.text_input("Jenis 1 (Terdeteksi Otomatis - ISO)", value=default_lama_1, key=f"l1_{default_lama_1}")
            lama_2 = st.text_input("Jenis 2 (Terdeteksi Otomatis - Header)", value=default_lama_2, key=f"l2_{default_lama_2}")
            lama_3 = st.text_input("Jenis 3 (Opsional)", value="")
        with c2:
            baru_1 = st.text_input("Ubah Jenis 1 Menjadi", value="2025-01-11")
            baru_2 = st.text_input("Ubah Jenis 2 Menjadi", value="11 Januari 2025")
            baru_3 = st.text_input("Ubah Jenis 3 Menjadi (Opsional)", value="")

        def buat_hari_tanggal_indo(teks_tgl, teks_iso=""):
            hari_indo = ["Senin", "Selasa", "Rabu", "Kamis", "Jumat", "Sabtu", "Minggu"]
            bulan_map = {
                "januari": 1, "februari": 2, "maret": 3, "april": 4, "mei": 5, "juni": 6,
                "juli": 7, "agustus": 8, "september": 9, "oktober": 10, "november": 11, "desember": 12
            }
            try:
                bagian = teks_tgl.strip().split()
                if len(bagian) == 3 and bagian[1].lower() in bulan_map:
                    dt = datetime.date(int(bagian[2]), bulan_map[bagian[1].lower()], int(bagian[0]))
                    return f"{hari_indo[dt.weekday()]}, {teks_tgl.strip()}"
            except Exception:
                pass
            try:
                if len(teks_iso.strip().split("-")) == 3:
                    y, m, d = map(int, teks_iso.strip().split("-"))
                    dt = datetime.date(y, m, d)
                    return f"{hari_indo[dt.weekday()]}, {teks_tgl.strip()}"
            except Exception:
                pass
            return teks_tgl.strip()

        otomatis_wm = buat_hari_tanggal_indo(baru_2, baru_1)
        edit_foto_pdf = st.checkbox(f"✅ Otomatis ubah tanggal di dalam seluruh foto menjadi: **{otomatis_wm}**", value=True)

        if pdf_bytes_cache and st.button("🔄 Eksekusi Perubahan Otomatis Sekarang", use_container_width=True):
            with st.spinner("Mendeteksi jenis font asli & menyinkronkan seluruh halaman serta foto..."):
                hasil_pdf_tgl, jml_teks, jml_gbr = proses_multi_tanggal_pdf(
                    pdf_bytes_cache, [(lama_1, baru_1), (lama_2, baru_2), (lama_3, baru_3)],
                    edit_foto_pdf, otomatis_wm
                )
                st.session_state.riwayat_proses.insert(0, {"waktu": "Baru saja", "modul": "Auto-Tanggal", "detail": f"{pdf_tanggal.name[:22]}... ({jml_teks} teks, {jml_gbr} foto)"})
                st.success(f"✅ Berhasil! **{jml_teks} teks PDF** dan **{jml_gbr} foto dokumentasi** diperbarui menjadi **{otomatis_wm}**.")
                nama_file_out = f"Revisi_{pdf_tanggal.name.replace(lama_1, baru_1)}"
                st.download_button("⬇️ Unduh PDF Hasil Revisi", hasil_pdf_tgl, nama_file_out, "application/pdf", use_container_width=True)
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
                    st.download_button("⬇️ Unduh Semua File (ZIP)", data=zip_buffer.getvalue(), file_name="Laporan_Bersih.zip", mime="application/zip", use_container_width=True)
            elif "Jahit" in st.session_state.menu_aktif and len(data_siap_proses) > 0 and st.button("🚀 Menjahit Dokumen Sekarang!", use_container_width=True):
                pdf_file = pdf_inputs[0]
                hasil_pdf_bytes = proses_dokumen(pdf_file, data_siap_proses)
                nama_unduh = pdf_file.name[:-4] + " revisi.pdf" if pdf_file.name.lower().endswith(".pdf") else pdf_file.name + " revisi.pdf"
                st.session_state.riwayat_proses.insert(0, {"waktu": "Baru saja", "modul": "Jahit Foto", "detail": f"{len(data_siap_proses)} aset dijahit"})
                st.success("🏆 Dokumen Selesai Dijahit!")
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
                st.download_button("⬇️ Unduh Foto", data=buf_img.getvalue(), file_name="Foto_Watermark.jpg", mime="image/jpeg", use_container_width=True)
        st.markdown("</div>", unsafe_allow_html=True)

with right_panel:
    st.markdown(f"<div class='ai-orb-box'><div class='ai-orb'></div><div style='font-weight:800; font-size:1.05rem; margin-bottom:4px;'>Smart Document Sync</div><div style='font-size:0.78rem; color:{TEXT_SECONDARY};'>4 modul aktif: Auto-Tanggal PDF & Foto, Pembersih Kotak Pink, Penjahit Progres, dan Watermark.</div></div>", unsafe_allow_html=True)
    st.write("")
    st.markdown("<div class='bento-card'>", unsafe_allow_html=True)
    st.markdown("##### 🕒 Aktivitas Terbaru")
    for item in st.session_state.riwayat_proses[:5]:
        st.markdown(f"<div style='border-bottom:1px solid {BORDER_CARD}; padding:8px 0;'><div style='display:flex; justify-content:space-between; font-size:0.74rem;'><span style='font-weight:700; color:{ORANGE_RGB};'>{item['modul']}</span><span style='color:{TEXT_SECONDARY};'>{item['waktu']}</span></div><div style='font-size:0.79rem; margin-top:2px;'>{item['detail']}</div></div>", unsafe_allow_html=True)
    st.markdown("</div>", unsafe_allow_html=True)
