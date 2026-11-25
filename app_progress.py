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
        {"waktu": "Hari ini", "modul": "Sistem Siap", "detail": "Menunggu dokumen checklist"}
    ]

# --- PALET WARNA PRESISI RGB(40, 37, 98) & RGB(236, 105, 35) ---
NAVY_RGB = "rgb(40, 37, 98)"
NAVY_HEX = "#282562"
ORANGE_RGB = "rgb(236, 105, 35)"
ORANGE_HEX = "#ec6923"

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

def patch_watermark_gambar(img_pil, teks_hari_tanggal_baru, rasio_x0=0.0, rasio_y0=0.722, rasio_x1=0.845, rasio_y1=0.985):
    from PIL import ImageFilter
    import re

    img = img_pil.convert("RGBA")
    w, h = img.size

    bx0, by0 = 0, int(h * 0.722)
    bx1, by1 = int(w * 0.845), int(h * 0.985)
    box_w, box_h = bx1 - bx0, by1 - by0

    jam_asli = "09:00"
    koordinat_asli = "-6.9721328,110.416271"
    try:
        import pytesseract
        crop_ocr = img.crop((bx0, by0, bx1, by1)).convert("L")
        crop_ocr = crop_ocr.resize((crop_ocr.width * 2, crop_ocr.height * 2), Image.Resampling.LANCZOS)
        teks_ocr = pytesseract.image_to_string(crop_ocr, config="--psm 6")

        cari_jam = re.findall(r"\b([0-2]?\d:[0-5]\d)\b", teks_ocr)
        if cari_jam:
            jam_asli = cari_jam[0]

        cari_koord = re.findall(r"(-?\d+\.\d+\s*,\s*\d+\.\d+)", teks_ocr)
        if cari_koord:
            koordinat_asli = cari_koord[0].replace(" ", "")
    except Exception:
        pass

    strip_atas = img.crop((bx0, max(0, by0 - 5), bx1, max(1, by0 - 1))).resize((box_w, box_h), Image.Resampling.BICUBIC)
    strip_kanan = img.crop((min(w - 5, bx1 + 1), by0, min(w, bx1 + 5), by1)).resize((box_w, box_h), Image.Resampling.BICUBIC)

    tambalan_alami = Image.blend(strip_atas, strip_kanan, alpha=0.5)
    tambalan_alami = tambalan_alami.filter(ImageFilter.GaussianBlur(radius=max(3, int(box_h * 0.04))))

    mask = Image.new("L", (box_w, box_h), 255)
    draw_mask = ImageDraw.Draw(mask)
    pad = max(4, int(box_h * 0.05))
    draw_mask.rectangle([pad, pad, box_w - pad, box_h - pad], fill=255)
    mask = mask.filter(ImageFilter.GaussianBlur(radius=pad))
    img.paste(tambalan_alami, (bx0, by0), mask)

    overlay = Image.new("RGBA", img.size, (0, 0, 0, 0))
    draw = ImageDraw.Draw(overlay)
    draw.rectangle([bx0, by0, bx1, by1], fill=(12, 12, 12, 132))

    ukuran_font = max(11, int(w * 0.0365))
    try:
        font = ImageFont.truetype("DejaVuSans.ttf", ukuran_font)
    except Exception:
        font = ImageFont.load_default()

    baris_teks = [
        f"{teks_hari_tanggal_baru} {jam_asli}",
        koordinat_asli,
        "Kecamatan Semarang Utara, Kota Semarang",
        "Jawa Tengah",
        "Indonesia"
    ]

    margin_kiri = int(w * 0.016)
    y_teks = by0 + int(box_h * 0.045)
    spasi_baris = int(ukuran_font * 1.30)

    for baris in baris_teks:
        draw.text((margin_kiri + 1, y_teks + 1), baris, font=font, fill=(0, 0, 0, 150))
        draw.text((margin_kiri, y_teks), baris, font=font, fill=(242, 242, 242, 252))
        y_teks += spasi_baris

    return Image.alpha_composite(img, overlay).convert("RGB")

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

def proses_multi_tanggal_pdf(pdf_file, daftar_ganti, edit_gambar=True, teks_watermark_baru="Jumat, 03 Januari 2025"):
    doc = fitz.open(stream=pdf_file.read(), filetype="pdf")
    total_teks, total_gbr, xref_done = 0, 0, set()
    for halaman in doc:
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
        if edit_gambar:
            for img_info in halaman.get_images(full=True):
                xref = img_info[0]
                if xref in xref_done:
                    continue
                xref_done.add(xref)
                base_image = doc.extract_image(xref)
                if base_image["width"] < 180 or base_image["height"] < 180:
                    continue
                img_hasil = patch_watermark_gambar(Image.open(io.BytesIO(base_image["image"])), teks_watermark_baru)
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
    _, col_left, col_right, _ = st.columns([0.45, 2.35, 2.05, 0.45], gap="large")
    
    with col_left:
        st.markdown("""
        <style>
        /* Animasi Masuk Panel (Framer Motion Spring) */
        @keyframes framerEntrance {
            0% { opacity: 0; transform: translateY(28px) scale(0.97); }
            100% { opacity: 1; transform: translateY(0) scale(1); }
        }
        
        /* Animasi Aliran Garis Kecepatan Terus-menerus */
        @keyframes speedFlow {
            0% { stroke-dashoffset: 160; }
            100% { stroke-dashoffset: -160; }
        }
        
        /* Animasi Hembusan Partikel Debu Cahaya */
        @keyframes particleBlow {
            0% { transform: translateX(180px) scaleX(1); opacity: 0; }
            30% { opacity: 0.8; }
            70% { opacity: 0.8; }
            100% { transform: translateX(-120px) scaleX(0.5); opacity: 0; }
        }

        /* ----------------- ANIMASI GERAKAN LARI HALUS (PHYSICS-BASED) ----------------- */
        /* Pelari 1 (Paling Depan - Sangat Cepat & Lincah) */
        @keyframes strideLead {
            0%, 100% { transform: translateY(0px) skewX(0deg); }
            25% { transform: translateY(-4px) skewX(-2deg); }
            50% { transform: translateY(-1px) skewX(1deg); }
            75% { transform: translateY(-5px) skewX(-1deg); }
        }
        @keyframes limbLead {
            0%, 100% { d: path("M26 18 L18 37 L4 52 M18 37 L31 49 L26 64 M25 21 L38 28 L46 20 M23 21 L11 28 L3 36"); }
            50% { d: path("M26 18 L15 37 L10 50 M15 37 L23 48 L40 60 M25 21 L34 26 L26 16 M23 21 L16 29 L28 36"); }
        }

        /* Pelari 2 (Tengah - Tempo Konsisten) */
        @keyframes strideMid {
            0%, 100% { transform: translateY(-1px) skewX(-1deg); }
            33% { transform: translateY(-5px) skewX(-3deg); }
            66% { transform: translateY(0px) skewX(0deg); }
        }
        @keyframes limbMid {
            0%, 100% { d: path("M25 18 L17 36 L3 48 M17 36 L28 47 L21 61 M24 21 L36 28 L43 21 M22 21 L11 27 L3 34"); }
            50% { d: path("M25 18 L14 36 L9 46 M14 36 L21 47 L34 58 M24 21 L32 26 L24 15 M22 21 L14 28 L23 34"); }
        }

        /* Pelari 3 (Belakang - Tenang Namun Bertenaga) */
        @keyframes strideBack {
            0%, 100% { transform: translateY(-2px) skewX(0deg); }
            40% { transform: translateY(0px) skewX(-2deg); }
            80% { transform: translateY(-4px) skewX(1deg); }
        }
        @keyframes limbBack {
            0%, 100% { d: path("M24 18 L16 35 L2 46 M16 35 L27 46 L18 59 M23 21 L35 28 L41 21 M21 21 L10 27 L2 33"); }
            50% { d: path("M24 18 L13 35 L8 44 M13 35 L19 46 L30 56 M23 21 L31 26 L23 14 M21 21 L12 28 L20 33"); }
        }

        /* Kelas Pengendali Jalur Animasi */
        .framer-panel {
            animation: framerEntrance 0.85s cubic-bezier(0.22, 1, 0.36, 1) forwards;
        }
        .peloton-stage {
            margin: 18px 0 14px 0;
            padding: 16px 20px 10px 20px;
            background: rgba(11, 14, 23, 0.42);
            border: 1px solid rgba(255, 255, 255, 0.15);
            border-radius: 16px;
            backdrop-filter: blur(10px);
            overflow: hidden;
            position: relative;
        }
        
        /* Penerapan Gerakan Elastis Pada Pelari */
        .run-body-1 { animation: strideLead 0.58s cubic-bezier(0.45, 0.05, 0.55, 0.95) infinite; }
        .run-body-2 { animation: strideMid 0.64s cubic-bezier(0.45, 0.05, 0.55, 0.95) infinite; }
        .run-body-3 { animation: strideBack 0.70s cubic-bezier(0.45, 0.05, 0.55, 0.95) infinite; }

        .run-limbs-1 { animation: limbLead 0.58s steps(15, end) infinite; }
        .run-limbs-2 { animation: limbMid 0.64s steps(15, end) infinite; }
        .run-limbs-3 { animation: limbBack 0.70s steps(15, end) infinite; }

        /* Penerapan Aliran Kecepatan Lintasan & Udara */
        .track-fast { stroke-dasharray: 80, 50; animation: speedFlow 0.8s linear infinite; }
        .track-slow { stroke-dasharray: 100, 80; animation: speedFlow 1.6s linear infinite; }
        
        .wind-line-1 { stroke-dasharray: 40, 90; animation: speedFlow 0.5s linear infinite; }
        .wind-line-2 { stroke-dasharray: 55, 120; animation: speedFlow 0.7s linear infinite; }
        .wind-line-3 { stroke-dasharray: 30, 80; animation: speedFlow 0.4s linear infinite; }

        .particle-1 { animation: particleBlow 1.1s linear infinite; }
        .particle-2 { animation: particleBlow 1.4s linear 0.4s infinite; }
        .particle-3 { animation: particleBlow 0.9s linear 0.7s infinite; }
        </style>

        <div class='login-brand-panel framer-panel'>
            <h1>IMO2025 📑 dR</h1>
            <p>Ruang kerja digital otomasi dokumen perawatan prasarana, pembersihan anotasi, dan sinkronisasi laporan.</p>
            
            <div class='peloton-stage'>
                <svg viewBox="0 0 360 92" width="100%" height="84" xmlns="http://www.w3.org/2000/svg">
                    <defs>
                        <!-- Gradasi Mewah untuk Jejak Jalur Larinya -->
                        <linearGradient id="trackGrad" x1="0%" y1="0%" x2="100%" y2="0%">
                            <stop offset="0%" stop-color="rgba(236,105,35,0)" />
                            <stop offset="45%" stop-color="#ec6923" />
                            <stop offset="90%" stop-color="#3B378C" />
                            <stop offset="100%" stop-color="rgba(255,255,255,0.4)" />
                        </linearGradient>
                        <filter id="glowOrange" x="-30%" y="-30%" width="160%" height="160%">
                            <feGaussianBlur stdDeviation="2.5" result="blur" />
                            <feComposite in="SourceGraphic" in2="blur" operator="over" />
                        </filter>
                        <filter id="glowBlue" x="-30%" y="-30%" width="160%" height="160%">
                            <feGaussianBlur stdDeviation="1.8" result="blur" />
                            <feComposite in="SourceGraphic" in2="blur" operator="over" />
                        </filter>
                    </defs>

                    <!-- Garis Aliran Udara Terusan (Wind Speed) -->
                    <line class="wind-line-1" x1="-10" y1="12" x2="370" y2="12" stroke="rgba(255,255,255,0.08)" stroke-width="1" />
                    <line class="wind-line-2" x1="-10" y1="28" x2="370" y2="28" stroke="rgba(236,105,35,0.12)" stroke-width="1.5" />
                    <line class="wind-line-3" x1="-10" y1="46" x2="370" y2="46" stroke="rgba(59,55,140,0.18)" stroke-width="1.2" />

                    <!-- Partikel Debu Kecepatan Berseliweran -->
                    <circle class="particle-1" cx="0" cy="18" r="1.5" fill="#ec6923" />
                    <circle class="particle-2" cx="0" cy="36" r="2" fill="#FFFFFF" />
                    <circle class="particle-3" cx="0" cy="50" r="1.2" fill="#3B378C" />

                    <!-- Lintasan Neon Bawah -->
                    <line class="track-slow" x1="10" y1="78" x2="350" y2="78" stroke="url(#trackGrad)" stroke-width="2.5" stroke-linecap="round" />
                    <line class="track-fast" x1="20" y1="81" x2="340" y2="81" stroke="#FFFFFF" opacity="0.6" stroke-width="1" stroke-linecap="round" />

                    <!-- Pelari 3 (Belakang - Siluet Biru Lembut) -->
                    <g class="run-body-3" transform="translate(68, 11)" opacity="0.48" filter="url(#glowBlue)">
                        <circle cx="26" cy="10" r="5.2" fill="#94A3B8" />
                        <path class="run-limbs-3" d="M24 18 L16 35 L2 46 M16 35 L27 46 L18 59 M23 21 L35 28 L41 21 M21 21 L10 27 L2 33" stroke="#94A3B8" stroke-width="4" stroke-linecap="round" stroke-linejoin="round" fill="none"/>
                    </g>

                    <!-- Pelari 2 (Tengah - Siluet Transparan Ringan) -->
                    <g class="run-body-2" transform="translate(138, 8)" opacity="0.75">
                        <circle cx="27" cy="10" r="5.6" fill="#CBD5E1" />
                        <path class="run-limbs-2" d="M25 18 L17 36 L3 48 M17 36 L28 47 L21 61 M24 21 L36 28 L43 21 M22 21 L11 27 L3 34" stroke="#E2E8F0" stroke-width="4.3" stroke-linecap="round" stroke-linejoin="round" fill="none"/>
                    </g>

                    <!-- Pelari 1 (Paling Depan - Putih Mengkilap Dengan Glow Oranye) -->
                    <g class="run-body-1" transform="translate(208, 5)" filter="url(#glowOrange)">
                        <!-- Kepala -->
                        <circle cx="29" cy="10" r="6" fill="#FFFFFF" stroke="#ec6923" stroke-width="1.8" />
                        <!-- Badan, Tangan, dan Kaki (Bisa Mengayun Lewat Keyframes d:) -->
                        <path class="run-limbs-1" d="M26 18 L18 37 L4 52 M18 37 L31 49 L26 64 M25 21 L38 28 L46 20 M23 21 L11 28 L3 36" stroke="#FFFFFF" stroke-width="4.8" stroke-linecap="round" stroke-linejoin="round" fill="none"/>
                        <!-- Detail Pinggul/Punggung Ekstra Kontras -->
                        <path d="M25 21 L36 27" stroke="#ec6923" stroke-width="2.2" stroke-linecap="round" />
                    </g>
                </svg>
            </div>

            <div>
                <span class='feature-pill'>📅 Auto-Tanggal PDF</span>
                <span class='feature-pill'>🧹 Hapus Kotak Pink</span>
                <span class='feature-pill'>🚀 Jahit Foto 0-50-100%</span>
                <span class='feature-pill'>📸 Watermark</span>
            </div>
        </div>
        """, unsafe_allow_html=True)

    with col_right:
        st.write("")
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
        st.markdown("#### 📅 Auto-Ubah Tanggal PDF & Foto (100% Sinkron Otomatis)")
        st.caption("Tanggal dan nama hari di dalam foto dokumentasi otomatis mengikuti tanggal baru yang kamu masukkan di bawah.")
        pdf_tanggal = st.file_uploader("📥 Unggah File PDF Laporan Perawatan", type=["pdf"])
        c1, c2 = st.columns(2)
        with c1:
            lama_1 = st.text_input("Jenis 1 (Format ISO)", value="2026-09-20")
            lama_2 = st.text_input("Jenis 2 (Format Header & Foto)", value="20 September 2026")
            lama_3 = st.text_input("Jenis 3 (Opsional)", value="")
        with c2:
            baru_1 = st.text_input("Ubah Jenis 1 Menjadi", value="2025-02-12")
            baru_2 = st.text_input("Ubah Jenis 2 Menjadi", value="12 Februari 2025")
            baru_3 = st.text_input("Ubah Jenis 3 Menjadi (Opsional)", value="")

        # Otomatis hitung nama hari Indonesia dari tanggal baru (misal 12 Februari 2025 -> Rabu, 12 Februari 2025)
        def buat_hari_tanggal_indo(teks_tgl, teks_iso=""):
            import datetime
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

        if pdf_tanggal and st.button("🔄 Eksekusi Perubahan Otomatis Sekarang", use_container_width=True):
            with st.spinner("Mendeteksi jenis font asli & menyinkronkan seluruh halaman serta foto..."):
                hasil_pdf_tgl, jml_teks, jml_gbr = proses_multi_tanggal_pdf(
                    pdf_tanggal, [(lama_1, baru_1), (lama_2, baru_2), (lama_3, baru_3)],
                    edit_foto_pdf, otomatis_wm
                )
                st.session_state.riwayat_proses.insert(0, {"waktu": "Baru saja", "modul": "Auto-Tanggal", "detail": f"{pdf_tanggal.name[:22]}... ({jml_teks} teks, {jml_gbr} foto)"})
                st.success(f"✅ Berhasil! **{jml_teks} teks PDF** dan **{jml_gbr} foto dokumentasi** diperbarui menjadi **{otomatis_wm}**.")
                st.download_button("⬇️ Unduh PDF Hasil Revisi", hasil_pdf_tgl, f"Revisi_{pdf_tanggal.name.replace('20-09-2026', baru_1)}", "application/pdf", use_container_width=True)
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
