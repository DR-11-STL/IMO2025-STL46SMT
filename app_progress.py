import streamlit as st
import streamlit.components.v1 as components
import fitz  # PyMuPDF
from PIL import Image, ImageDraw, ImageFont, ImageFilter, ImageEnhance, ImageOps
import io
import os
import base64
import zipfile
import urllib.request
import textwrap
import re
import datetime

USER_VALID = "Sintel46"
PASS_VALID = "IMO2025."
RAW_ICON_URL = "https://raw.githubusercontent.com/DR-11-STL/IMO2025-SINTEL46SMT/main/icon_imoxdr.png"

# --- KOLEKSI IKON VEKTOR SVG MODERN (LUCIDE STYLE) ---
SVG_ICONS = {
    "calendar": '<svg width="18" height="18" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round"><rect x="3" y="4" width="18" height="18" rx="2" ry="2"/><line x1="16" y1="2" x2="16" y2="6"/><line x1="8" y1="2" x2="8" y2="6"/><line x1="3" y1="10" x2="21" y2="10"/></svg>',
    "sparkles": '<svg width="18" height="18" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round"><path d="m12 3-1.912 5.813a2 2 0 0 1-1.275 1.275L3 12l5.813 1.912a2 2 0 0 1 1.275 1.275L12 21l1.912-5.813a2 2 0 0 1 1.275-1.275L21 12l-5.813-1.912a2 2 0 0 1-1.275-1.275L12 3Z"/></svg>',
    "layers": '<svg width="18" height="18" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round"><polygon points="12 2 2 7 12 12 22 7 12 2"/><polyline points="2 17 12 22 22 17"/><polyline points="2 12 12 17 22 12"/></svg>',
    "camera": '<svg width="18" height="18" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round"><path d="M14.5 4h-5L7 7H4a2 2 0 0 0-2 2v9a2 2 0 0 0 2 2h16a2 2 0 0 0 2-2V9a2 2 0 0 0-2-2h-3l-2.5-3z"/><circle cx="12" cy="13" r="3"/></svg>',
    "shield": '<svg width="18" height="18" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round"><path d="M12 22s8-4 8-10V5l-8-3-8 3v7c0 6 8 10 8 10z"/></svg>',
    "clock": '<svg width="16" height="16" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round"><circle cx="12" cy="12" r="10"/><polyline points="12 6 12 12 16 14"/></svg>',
    "eye": '<svg width="17" height="17" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round"><path d="M2 12s3-7 10-7 10 7 10 7-3 7-10 7-10-7-10-7Z"/><circle cx="12" cy="12" r="3"/></svg>',
    "cpu": '<svg width="18" height="18" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round"><rect x="4" y="4" width="16" height="16" rx="2"/><rect x="9" y="9" width="6" height="6"/><path d="M15 2v2"/><path d="M15 20v2"/><path d="M2 15h2"/><path d="M2 9h2"/><path d="M20 15h2"/><path d="M20 9h2"/><path d="M9 2v2"/><path d="M9 20v2"/></svg>'
}

def ikon_badge(nama_ikon, warna="#EC6923"):
    svg = SVG_ICONS.get(nama_ikon, "")
    return f"<span style='display:inline-flex; align-items:center; justify-content:center; width:34px; height:34px; border-radius:10px; background:rgba(236,105,35,0.14); border:1px solid rgba(236,105,35,0.35); color:{warna}; margin-right:10px; vertical-align:middle;'>{svg}</span>"

@st.cache_data(show_spinner=False)
def muat_ikon_aplikasi_base64():
    kandidat_file = ["icon_imoxdr.png", "icon_imoxdr.jpg", "icon_imoxdr.jpeg", "bc434dcc.jpeg"]
    for nama_file in kandidat_file:
        if os.path.exists(nama_file):
            try:
                img = Image.open(nama_file).convert("RGBA").resize((512, 512), Image.Resampling.LANCZOS)
                buf = io.BytesIO()
                img.save(buf, format="PNG")
                return "data:image/png;base64," + base64.b64encode(buf.getvalue()).decode("utf-8"), img
            except Exception:
                pass
    return "", None

ICON_DATA_URL, ICON_PIL = muat_ikon_aplikasi_base64()

st.set_page_config(
    page_title="IMOXdR",
    page_icon=ICON_PIL if ICON_PIL is not None else "🟧",
    layout="wide",
    initial_sidebar_state="collapsed"
)

if "login_sukses" not in st.session_state:
    st.session_state.login_sukses = False
if "dark_mode" not in st.session_state:
    st.session_state.dark_mode = True
if "riwayat_proses" not in st.session_state:
    st.session_state.riwayat_proses = [
        {"waktu": "Hari ini", "modul": "Sistem Siap", "detail": "Menunggu dokumen checklist"}
    ]

NAVY_RGB = "rgb(40, 37, 98)"
ORANGE_RGB = "rgb(236, 105, 35)"

if st.session_state.dark_mode:
    BG_APP = "radial-gradient(circle at 12% 10%, rgba(40, 37, 98, 0.45) 0%, #070A12 45%), radial-gradient(circle at 88% 85%, rgba(236, 105, 35, 0.16) 0%, #070A12 50%)"
    BG_SIDEBAR = "rgba(13, 17, 29, 0.85)"
    BG_GLASS = "rgba(20, 26, 46, 0.52)"
    BORDER_GLASS = "rgba(255, 255, 255, 0.11)"
    TEXT_PRIMARY, TEXT_SECONDARY, INPUT_BG = "#F8FAFC", "#94A3B8", "rgba(10, 14, 26, 0.72)"
else:
    BG_APP = "radial-gradient(circle at 15% 10%, rgba(40, 37, 98, 0.08) 0%, #F1F5F9 50%), radial-gradient(circle at 85% 90%, rgba(236, 105, 35, 0.08) 0%, #F1F5F9 55%)"
    BG_SIDEBAR = "rgba(255, 255, 255, 0.85)"
    BG_GLASS = "rgba(255, 255, 255, 0.72)"
    BORDER_GLASS = "rgba(40, 37, 98, 0.14)"
    TEXT_PRIMARY, TEXT_SECONDARY, INPUT_BG = "#0F172A", "#475569", "rgba(248, 250, 252, 0.9)"

css_tema = f"""<style>
@import url('https://fonts.googleapis.com/css2?family=Plus+Jakarta+Sans:wght@400;500;600;700;800;900&display=swap');

#MainMenu, footer, [data-testid="stDecoration"], .stAppDeployButton, .stToolbarActions,
[data-testid="stStatusWidget"], div[class*="viewerBadge"], div[class*="profileContainer"],
div[class*="profilePreview"], div[class*="StatusWidget"], div[class*="manageApp"],
button[kind="manageApp"], a[href*="streamlit.io/cloud"], a[href*="share.streamlit.io"] {{
    display: none !important;
    visibility: hidden !important;
    opacity: 0 !important;
    pointer-events: none !important;
    width: 0 !important;
    height: 0 !important;
}}

header[data-testid="stHeader"] {{
    background: transparent !important;
    visibility: visible !important;
    display: flex !important;
    pointer-events: none !important;
}}
[data-testid="stToolbar"] {{
    visibility: visible !important;
    display: flex !important;
    background: transparent !important;
}}

[data-testid="stExpandSidebarButton"], [data-testid="collapsedControl"] {{
    position: fixed !important;
    top: 14px !important;
    left: 14px !important;
    z-index: 999999 !important;
    visibility: visible !important;
    display: flex !important;
    align-items: center !important;
    justify-content: center !important;
    width: 42px !important;
    height: 42px !important;
    background: linear-gradient(135deg, {NAVY_RGB}, {ORANGE_RGB}) !important;
    color: #FFFFFF !important;
    border: 1px solid rgba(255,255,255,0.35) !important;
    border-radius: 12px !important;
    box-shadow: 0 8px 20px rgba(0, 0, 0, 0.45) !important;
    opacity: 1 !important;
    pointer-events: auto !important;
    cursor: pointer !important;
    transition: all 0.25s cubic-bezier(0.16, 1, 0.3, 1) !important;
}}
[data-testid="stExpandSidebarButton"]:hover, [data-testid="collapsedControl"]:hover {{
    transform: translateY(-2px) scale(1.04) !important;
    box-shadow: 0 10px 24px rgba(236, 105, 35, 0.6) !important;
}}
[data-testid="stExpandSidebarButton"] svg, [data-testid="collapsedControl"] svg {{
    fill: #FFFFFF !important;
    color: #FFFFFF !important;
    width: 22px !important;
    height: 22px !important;
}}

.block-container {{
    padding-top: 2.6rem !important;
    padding-left: 2.2rem !important;
    padding-right: 2.2rem !important;
    max-width: 1480px !important;
}}

html, body, [class*="css"] {{font-family: 'Plus Jakarta Sans', sans-serif !important;}}
.stApp {{
    background: {BG_APP} !important;
    background-attachment: fixed !important;
    color: {TEXT_PRIMARY};
}}

section[data-testid="stSidebar"] {{
    background: {BG_SIDEBAR} !important;
    backdrop-filter: blur(20px) !important;
    -webkit-backdrop-filter: blur(20px) !important;
    border-right: 1px solid {BORDER_GLASS} !important;
    z-index: 1000000 !important;
}}

.stMarkdown p, label, span {{color: {TEXT_PRIMARY} !important;}}

.title-kai {{
    font-size: 2.1rem;
    font-weight: 900;
    margin: 0;
    background: linear-gradient(90deg, #FFFFFF 0%, #CBD5E1 100%);
    -webkit-background-clip: text;
    -webkit-text-fill-color: transparent;
    letter-spacing: -0.5px;
}}

/* GLASSMORPHISM CARDS */
.glass-card {{
    background: {BG_GLASS};
    backdrop-filter: blur(18px);
    -webkit-backdrop-filter: blur(18px);
    border: 1px solid {BORDER_GLASS};
    border-radius: 20px;
    padding: 22px 24px;
    margin-bottom: 18px;
    box-shadow: 0 12px 32px rgba(0, 0, 0, 0.22);
    transition: transform 0.25s ease, border-color 0.25s ease;
}}
.glass-card:hover {{
    border-color: rgba(236, 105, 35, 0.35);
}}

.glass-hero {{
    background: linear-gradient(135deg, rgba(40, 37, 98, 0.88) 0%, rgba(236, 105, 35, 0.88) 130%);
    backdrop-filter: blur(16px);
    -webkit-backdrop-filter: blur(16px);
    border: 1px solid rgba(255, 255, 255, 0.22);
    border-radius: 20px;
    padding: 20px 22px;
    color: #FFFFFF !important;
    margin-bottom: 18px;
    box-shadow: 0 12px 30px rgba(236, 105, 35, 0.22);
}}
.glass-hero * {{color: #FFFFFF !important;}}

.login-brand-panel {{
    background: linear-gradient(145deg, rgba(40, 37, 98, 0.9) 0%, rgba(16, 20, 38, 0.95) 60%, rgba(236, 105, 35, 0.85) 140%);
    backdrop-filter: blur(20px);
    border-radius: 24px;
    padding: 42px 34px;
    color: #FFFFFF !important;
    border: 1px solid rgba(255, 255, 255, 0.18);
    box-shadow: 0 20px 45px rgba(0, 0, 0, 0.4);
}}
.login-brand-panel h1 {{
    font-size: 3.1rem;
    font-weight: 900;
    color: #FFFFFF !important;
    letter-spacing: -1px;
    margin-bottom: 10px;
}}
.login-brand-panel p {{color: #CBD5E1 !important; font-size: 0.96rem; line-height: 1.6;}}

.feature-pill {{
    display: inline-flex;
    align-items: center;
    gap: 6px;
    background: rgba(255, 255, 255, 0.1);
    backdrop-filter: blur(8px);
    border: 1px solid rgba(255, 255, 255, 0.2);
    padding: 7px 14px;
    border-radius: 999px;
    font-size: 0.78rem;
    font-weight: 600;
    color: #FFFFFF !important;
    margin: 8px 6px 0 0;
}}

.kpi-title {{font-size: 0.72rem; font-weight: 700; color: {TEXT_SECONDARY} !important; text-transform: uppercase; letter-spacing: 0.6px;}}
.kpi-value {{font-size: 1.85rem; font-weight: 800; color: {TEXT_PRIMARY} !important; margin: 4px 0;}}
.kpi-badge-orange {{
    display: inline-block;
    background: rgba(236, 105, 35, 0.16);
    border: 1px solid rgba(236, 105, 35, 0.35);
    color: #FF8A4C !important;
    padding: 3px 11px;
    border-radius: 999px;
    font-size: 0.72rem;
    font-weight: 700;
}}

.ai-orb-box {{
    background: {BG_GLASS};
    backdrop-filter: blur(18px);
    border: 1px solid {BORDER_GLASS};
    border-radius: 20px;
    padding: 22px 18px;
    text-align: center;
    box-shadow: 0 12px 32px rgba(0, 0, 0, 0.2);
}}
.ai-orb {{
    width: 74px;
    height: 74px;
    margin: 8px auto 14px auto;
    border-radius: 50%;
    background: radial-gradient(circle at 30% 30%, {ORANGE_RGB}, {NAVY_RGB} 70%, #070A12 100%);
    box-shadow: 0 0 32px rgba(236, 105, 35, 0.55);
    animation: pulseOrb 3.2s infinite ease-in-out;
}}
@keyframes pulseOrb {{0% {{transform: scale(0.95);}} 50% {{transform: scale(1.05);}} 100% {{transform: scale(0.95);}}}}

/* MODERN FILE UPLOADER DROPZONE */
[data-testid="stFileUploader"] section {{
    background: rgba(40, 37, 98, 0.14) !important;
    border: 1.5px dashed rgba(236, 105, 35, 0.55) !important;
    border-radius: 16px !important;
    padding: 18px !important;
    transition: all 0.25s ease !important;
}}
[data-testid="stFileUploader"] section:hover {{
    background: rgba(236, 105, 35, 0.08) !important;
    border-color: {ORANGE_RGB} !important;
}}

/* BUTTONS & INPUTS */
.stButton>button, .stDownloadButton>button {{
    background: linear-gradient(135deg, {NAVY_RGB} 0%, #373385 100%) !important;
    color: #FFFFFF !important;
    font-weight: 700 !important;
    border-radius: 12px !important;
    border: 1px solid rgba(255, 255, 255, 0.22) !important;
    padding: 0.65rem 1.3rem !important;
    box-shadow: 0 6px 18px rgba(0, 0, 0, 0.28) !important;
    transition: all 0.25s ease !important;
}}
.stButton>button:hover, .stDownloadButton>button:hover {{
    background: linear-gradient(135deg, {ORANGE_RGB} 0%, #FF7E38 100%) !important;
    border-color: #FFFFFF !important;
    transform: translateY(-2px);
    box-shadow: 0 8px 22px rgba(236, 105, 35, 0.45) !important;
}}

.stTextInput>div>div>input, .stTextArea>div>div>textarea {{
    border-radius: 12px !important;
    border: 1px solid {BORDER_GLASS} !important;
    background-color: {INPUT_BG} !important;
    color: {TEXT_PRIMARY} !important;
    padding: 10px 14px !important;
}}
.stTextInput>div>div>input:focus, .stTextArea>div>div>textarea:focus {{
    border-color: {ORANGE_RGB} !important;
    box-shadow: 0 0 0 2px rgba(236, 105, 35, 0.25) !important;
}}

/* RADIO PILLS DI SIDEBAR */
div[role="radiogroup"] label {{
    background: rgba(255, 255, 255, 0.04) !important;
    border: 1px solid {BORDER_GLASS} !important;
    border-radius: 12px !important;
    padding: 10px 14px !important;
    margin-bottom: 8px !important;
    transition: all 0.2s ease !important;
}}
div[role="radiogroup"] label:hover {{
    border-color: {ORANGE_RGB} !important;
    background: rgba(236, 105, 35, 0.1) !important;
}}

hr {{border-top: 1px solid {BORDER_GLASS} !important;}}
</style>"""
st.markdown(css_tema, unsafe_allow_html=True)

# Suntikkan URL Asli GitHub RAW untuk Logo "dR" & Nama "IMOXdR" agar terbaca server WebAPK Android
components.html(f"""
<script>
const setupAppBrandAndClean = () => {{
    try {{
        const doc = window.parent.document;
        const head = doc.head;

        doc.querySelectorAll('div, button, a, span').forEach(el => {{
            if (el.textContent && el.textContent.trim() === 'Manage app') {{
                let target = el.closest('div[class*="profile"], div[class*="viewer"], div[class*="Status"]') || el.parentElement;
                if (target) {{
                    target.style.setProperty('display', 'none', 'important');
                    target.style.setProperty('visibility', 'hidden', 'important');
                }}
            }}
        }});

        if (!doc.getElementById('imoxdr-manifest-injected')) {{
            const iconUrl = "{RAW_ICON_URL}";
            doc.title = 'IMOXdR';

            doc.querySelectorAll('link[rel="manifest"], link[rel="icon"], link[rel="shortcut icon"], link[rel="apple-touch-icon"]').forEach(el => el.remove());

            const addLink = (rel, href, sizes = '') => {{
                const l = doc.createElement('link');
                l.rel = rel;
                l.href = href;
                if (sizes) l.sizes = sizes;
                head.appendChild(l);
            }};
            const addMeta = (name, content) => {{
                let m = doc.querySelector(`meta[name="${{name}}"]`);
                if (!m) {{ m = doc.createElement('meta'); m.name = name; head.appendChild(m); }}
                m.content = content;
            }};

            addLink('icon', iconUrl, '512x512');
            addLink('apple-touch-icon', iconUrl, '512x512');
            addMeta('application-name', 'IMOXdR');
            addMeta('apple-mobile-web-app-title', 'IMOXdR');
            addMeta('mobile-web-app-capable', 'yes');
            addMeta('apple-mobile-web-app-capable', 'yes');
            addMeta('apple-mobile-web-app-status-bar-style', 'black-translucent');
            addMeta('theme-color', '#08080A');

            const manifestObj = {{
                name: "IMOXdR",
                short_name: "IMOXdR",
                start_url: window.parent.location.href,
                display: "standalone",
                background_color: "#08080A",
                theme_color: "#08080A",
                icons: [
                    {{ src: iconUrl, sizes: "192x192", type: "image/png", purpose: "any" }},
                    {{ src: iconUrl, sizes: "512x512", type: "image/png", purpose: "any" }}
                ]
            }};
            const manifestBase64 = btoa(unescape(encodeURIComponent(JSON.stringify(manifestObj))));
            const manifestLink = doc.createElement('link');
            manifestLink.id = 'imoxdr-manifest-injected';
            manifestLink.rel = 'manifest';
            manifestLink.href = 'data:application/manifest+json;base64,' + manifestBase64;
            head.appendChild(manifestLink);
        }}
    }} catch (e) {{}}
}};
setupAppBrandAndClean();
setInterval(setupAppBrandAndClean, 800);
</script>
""", height=0, width=0)

# --- FUNGSI RENDER PREVIEW PDF OTOMATIS ---
def render_preview_pdf(pdf_bytes, maks_halaman=3):
    doc = fitz.open(stream=pdf_bytes, filetype="pdf")
    total_hal = len(doc)
    gambar_halaman = []
    for idx in range(min(total_hal, maks_halaman)):
        pix = doc[idx].get_pixmap(dpi=130)
        img = Image.open(io.BytesIO(pix.tobytes("png")))
        gambar_halaman.append((idx + 1, img))
    doc.close()
    return gambar_halaman, total_hal

def tampilkan_panel_preview_pdf(pdf_bytes, judul="Pratinjau Dokumen PDF"):
    if not pdf_bytes:
        return
    gambar_list, total_hal = render_preview_pdf(pdf_bytes, maks_halaman=4)
    st.markdown(f"<div style='margin-top:14px; margin-bottom:8px; font-weight:700; font-size:0.92rem; display:flex; align-items:center;'>{ikon_badge('eye')} {judul} <span style='margin-left:8px; font-size:0.76rem; color:{TEXT_SECONDARY};'>(Menampilkan {len(gambar_list)} dari {total_hal} halaman)</span></div>", unsafe_allow_html=True)
    cols = st.columns(len(gambar_list))
    for col, (no_hal, img) in zip(cols, gambar_list):
        with col:
            st.image(img, caption=f"Halaman {no_hal}", use_container_width=True)

@st.cache_data(show_spinner=False)
def ambil_bytes_font_roboto():
    try:
        req = urllib.request.Request(
            "https://github.com/googlefonts/roboto/raw/main/src/hinted/Roboto-Medium.ttf",
            headers={'User-Agent': 'Mozilla/5.0'}
        )
        return urllib.request.urlopen(req, timeout=5).read()
    except Exception:
        return None

def muat_font_roboto(ukuran):
    font_bytes = ambil_bytes_font_roboto()
    if font_bytes:
        try:
            return ImageFont.truetype(io.BytesIO(font_bytes), ukuran)
        except Exception:
            pass
    try:
        return ImageFont.truetype("/usr/share/fonts/truetype/dejavu/DejaVuSans.ttf", ukuran)
    except Exception:
        return ImageFont.load_default()

def crop_center_square(image):
    img = ImageOps.exif_transpose(image).convert("RGB")
    w, h = img.size
    sisi = min(w, h)
    kiri = (w - sisi) // 2
    atas = (h - sisi) // 2
    return img.crop((kiri, atas, kiri + sisi, atas + sisi)).resize((600, 600), Image.Resampling.LANCZOS)

def proses_dokumen(pdf_file, data_rangkaian):
    pdf_file.seek(0)
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
        lebar_gambar, tinggi_gambar, spasi = 155, 155, 25
        mulai_x = (lebar_halaman - (3 * lebar_gambar + 2 * spasi)) / 2
        y_pos, items_per_page = 60, 0
        halaman_baru = doc.new_page(width=lebar_halaman, height=tinggi_halaman)

        path_font_bold = "/usr/share/fonts/truetype/dejavu/DejaVuSans-Bold.ttf"
        path_font_reg = "/usr/share/fonts/truetype/dejavu/DejaVuSans.ttf"

        for data in data_rangkaian:
            if items_per_page >= 3:
                halaman_baru = doc.new_page(width=lebar_halaman, height=tinggi_halaman)
                y_pos, items_per_page = 60, 0
            try:
                halaman_baru.insert_text(fitz.Point(mulai_x, y_pos), f"{data['nama_aset']}", fontsize=13, fontname="dejavubold", fontfile=path_font_bold, color=(0, 0, 0))
            except Exception:
                halaman_baru.insert_text(fitz.Point(mulai_x, y_pos), f"{data['nama_aset']}", fontsize=13, fontname="hebo", color=(0, 0, 0))

            koleksi = [
                {"file": data["img_0"], "label": "Foto 0%"},
                {"file": data["img_50"], "label": "Foto 50%"},
                {"file": data["img_100"], "label": "Foto 100%"}
            ]
            for i, item in enumerate(koleksi):
                item["file"].seek(0)
                img_square = crop_center_square(Image.open(item["file"]))
                img_byte_arr = io.BytesIO()
                img_square.save(img_byte_arr, format='JPEG', quality=92, subsampling=0)
                x0 = mulai_x + i * (lebar_gambar + spasi)
                y0 = y_pos + 15
                halaman_baru.insert_image(fitz.Rect(x0, y0, x0 + lebar_gambar, y0 + tinggi_gambar), stream=img_byte_arr.getvalue())
                try:
                    halaman_baru.insert_text(fitz.Point(x0 + 50, y0 + tinggi_gambar + 18), item["label"], fontsize=11, fontname="dejavureg", fontfile=path_font_reg, color=(0, 0, 0))
                except Exception:
                    halaman_baru.insert_text(fitz.Point(x0 + 52, y0 + tinggi_gambar + 18), item["label"], fontsize=11, fontname="helv", color=(0, 0, 0))
            y_pos += 225
            items_per_page += 1

    output_pdf = io.BytesIO()
    doc.save(output_pdf, garbage=2, deflate=True)
    doc.close()
    return output_pdf.getvalue()

def deteksi_tanggal_otomatis_pdf(pdf_bytes):
    doc = fitz.open(stream=pdf_bytes, filetype="pdf")
    gabungan_teks = "\n".join(hal.get_text("text") for hal in doc)
    doc.close()
    tgl_iso = re.findall(r"\b(20\d{2}-\d{2}-\d{2})\b", gabungan_teks)
    bulan_regex = r"(?:Januari|Februari|Maret|April|Mei|Juni|Juli|Agustus|September|Oktober|November|Desember)"
    tgl_indo = re.findall(rf"\b(\d{{1,2}}\s+{bulan_regex}\s+20\d{{2}})\b", gabungan_teks, flags=re.IGNORECASE)
    return (tgl_iso[0] if tgl_iso else ""), (tgl_indo[0] if tgl_indo else "")

def baca_metadata_foto_asli(img_rgba):
    w, h = img_rgba.size
    bx0, by0 = 0, int(h * 0.710)
    bx1, by1 = int(w * 0.92), int(h * 0.992)
    jam_hasil, koord_hasil, alamat_hasil = None, None, None

    def normalisasi_koordinat(raw_k):
        k = raw_k.strip()
        if "," in k:
            bagian = [p.strip() for p in k.split(",") if p.strip()]
            sep = ","
        else:
            bagian = [p.strip() for p in k.split() if p.strip()]
            sep = " "
        if len(bagian) == 2:
            lat, lon = bagian[0], bagian[1]
            if not lat.startswith("-"):
                lat = "-" + lat
            return f"{lat}{sep}{lon}"
        return k

    def bersihkan_baris_asli(teks):
        t = re.sub(r"[^A-Za-z0-9,\.\-\s]", "", teks)
        t = re.sub(r"^([A-Za-z0-9]{1,2}\s+)+", "", t.strip())
        t = re.sub(r"(\s+[A-Za-z0-9]{1,2})+$", "", t.strip())
        t = re.sub(r"\s+", " ", t).strip(" ,.")

        kamus_perbaikan = [
            (r"\bKcamatan\b|\bKecamalan\b|\bKecarnatan\b|\bKecamtan\b", "Kecamatan"),
            (r"\bKabupalen\b|\bKabupatan\b|\bKabupafen\b", "Kabupaten"),
            (r"Utaraj\b", "Utara,"),
            (r"Timurj\b", "Timur,"),
            (r"Baratj\b", "Barat,"),
            (r"Selatanj\b", "Selatan,"),
            (r"Tengahj\b", "Tengah,"),
            (r"Torohj\b", "Toroh,"),
            (r"Genukj\b", "Genuk,"),
            (r"Pedurunganj\b", "Pedurungan,"),
            (r"Gayamsarij\b", "Gayamsari,"),
            (r"Kota Semaran\b|\bSemaran\b", "Kota Semarang"),
            (r"\bGroboganj\b|\bGrobogam\b", "Grobogan"),
            (r"\bPurwodadij\b|\bPurwadadi\b", "Purwodadi"),
            (r"\bDemakj\b", "Demak"),
            (r"\bKendalj\b", "Kendal"),
            (r"\bBatangj\b", "Batang"),
            (r"\bPekalonganj\b", "Pekalongan"),
            (r"\bTegalj\b", "Tegal"),
            (r"\bKudusj\b", "Kudus"),
            (r"\bPatij\b", "Pati"),
            (r"\bJeparaj\b", "Jepara"),
            (r"\bBloraj\b", "Blora"),
            (r"\bBoyolalij\b", "Boyolali"),
            (r"\bSalatigaj\b", "Salatiga"),
        ]
        for pola, ganti in kamus_perbaikan:
            t = re.sub(pola, ganti, t, flags=re.IGNORECASE)

        t = re.sub(r"(Kecamatan\s+[A-Za-z\s]+?)\s+(Kabupaten|Kota)\b", r"\1, \2", t, flags=re.IGNORECASE)
        t = re.sub(r",\s*,", ",", t)

        if any(k in t.lower() for k in ["indonesia", "yonesi", "ndonesi", "donesia"]):
            return "Indonesia"
        if "jawa tengah" in t.lower() or "awa tengah" in t.lower():
            return "Jawa Tengah"
        return t

    try:
        import pytesseract
        crop_dasar = img_rgba.crop((bx0, by0, bx1, by1)).convert("L")
        crop_besar = crop_dasar.resize((crop_dasar.width * 3, crop_dasar.height * 3), Image.Resampling.LANCZOS)
        kandidat_gambar = [
            ImageEnhance.Contrast(crop_besar).enhance(2.3),
            crop_besar.point(lambda p: 255 if p > 185 else 0),
            crop_besar.point(lambda p: 255 if p > 155 else 0),
        ]
        for gbr_uji in kandidat_gambar:
            teks_ocr = pytesseract.image_to_string(gbr_uji, config="--psm 6")
            if not jam_hasil:
                cari_jam = re.findall(r"\b([0-2]?\d[:\.][0-5]\d)\b", teks_ocr)
                if cari_jam:
                    jam_hasil = cari_jam[0]
            if not koord_hasil:
                cari_koord = re.findall(r"(-?\d+\.\d+(?:\s*,\s*|\s+)\d+\.\d+)", teks_ocr)
                if cari_koord:
                    koord_hasil = normalisasi_koordinat(cari_koord[0])
            if not alamat_hasil:
                semua_baris = [b.strip() for b in teks_ocr.splitlines() if b.strip()]
                idx_mulai = -1
                for i, b in enumerate(semua_baris):
                    if re.search(r"-?\d+\.\d+(?:\s*,\s*|\s+)\d+\.\d+", b):
                        idx_mulai = i + 1
                        break
                    elif any(k in b.lower() for k in ["kecamatan", "kcamatan", "kota ", "kabupaten"]):
                        idx_mulai = i
                        break
                if idx_mulai != -1 and len(semua_baris) > idx_mulai:
                    kandidat_baris = []
                    for raw_b in semua_baris[idx_mulai : idx_mulai + 3]:
                        clean_b = bersihkan_baris_asli(raw_b)
                        if len(clean_b) >= 4:
                            kandidat_baris.append(clean_b)
                    if kandidat_baris and any(k in kandidat_baris[0].lower() for k in ["kecamatan", "kota", "kabupaten", "semarang", "grobogan", "toroh", "genuk", "pedurungan", "gayamsari", "tawang", "poncol", "alastua"]):
                        if re.search(r"\b\d{5}\b", kandidat_baris[0]):
                            kandidat_baris = [kandidat_baris[0], "Indonesia"]
                        elif len(kandidat_baris) == 1:
                            kandidat_baris.extend(["Jawa Tengah", "Indonesia"])
                        elif len(kandidat_baris) == 2 and kandidat_baris[1] != "Indonesia":
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

    jam_asli, koordinat_asli, baris_alamat = baca_metadata_foto_asli(img)
    if fallback_meta:
        jam_asli = jam_asli or fallback_meta.get("jam")
        koordinat_asli = koordinat_asli or fallback_meta.get("koord")
        baris_alamat = baris_alamat or fallback_meta.get("alamat")

    jam_asli = jam_asli or "09:20"
    koordinat_asli = koordinat_asli or "-6.9817887,110.4731881"
    if not koordinat_asli.startswith("-"):
        koordinat_asli = "-" + koordinat_asli
    baris_alamat = baris_alamat or ["Kecamatan Genuk, Kota Semarang", "Jawa Tengah", "Indonesia"]
    meta_terbaca = {"jam": jam_asli, "koord": koordinat_asli, "alamat": baris_alamat}

    ukuran_font = max(12, int(w * 0.033))
    font = muat_font_roboto(ukuran_font)
    baris_teks = [f"{teks_hari_tanggal_baru} {jam_asli}", koordinat_asli] + baris_alamat
    spasi_baris = int(ukuran_font * 1.28)
    pad_x = max(8, int(w * 0.015))
    pad_y = max(6, int(h * 0.010))

    dummy_draw = ImageDraw.Draw(img)
    lebar_maks_teks = 0
    for baris in baris_teks:
        try:
            bbox = dummy_draw.textbbox((0, 0), baris, font=font)
            lw = bbox[2] - bbox[0]
        except Exception:
            lw = int(len(baris) * ukuran_font * 0.54)
        if lw > lebar_maks_teks:
            lebar_maks_teks = lw

    bx0, by1 = 0, int(h * 0.992)
    tinggi_kotak = (len(baris_teks) * spasi_baris) + (pad_y * 2)
    by0 = max(int(h * 0.68), min(int(h * 0.72), by1 - tinggi_kotak))
    bx1 = min(int(w * 0.94), max(int(w * 0.86), bx0 + lebar_maks_teks + (pad_x * 2)))
    box_w, box_h = bx1 - bx0, by1 - by0

    strip_atas = img.crop((bx0, max(0, by0 - 5), bx1, max(1, by0 - 1))).resize((box_w, box_h), Image.Resampling.BICUBIC)
    strip_kanan = img.crop((min(w - 5, bx1 + 1), by0, min(w, bx1 + 5), by1)).resize((box_w, box_h), Image.Resampling.BICUBIC)
    tambalan_alami = Image.blend(strip_atas, strip_kanan, alpha=0.5).filter(ImageFilter.GaussianBlur(radius=max(3, int(box_h * 0.04))))

    mask = Image.new("L", (box_w, box_h), 255)
    pad_blur = max(3, int(box_h * 0.04))
    ImageDraw.Draw(mask).rectangle([pad_blur, pad_blur, box_w - pad_blur, box_h - pad_blur], fill=255)
    mask = mask.filter(ImageFilter.GaussianBlur(radius=pad_blur))
    img.paste(tambalan_alami, (bx0, by0), mask)

    overlay = Image.new("RGBA", img.size, (0, 0, 0, 0))
    draw = ImageDraw.Draw(overlay)
    draw.rectangle([bx0, by0, bx1, by1], fill=(12, 12, 12, 215))

    y_teks = by0 + pad_y
    for baris in baris_teks:
        draw.text((bx0 + pad_x + 1, y_teks + 1), baris, font=font, fill=(0, 0, 0, 230))
        draw.text((bx0 + pad_x, y_teks), baris, font=font, fill=(255, 255, 255, 255))
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
                        is_bold = ("bold" in nama_font) or ("black" in nama_font) or bool(span.get("flags", 0) & 16)
                        c_int = span.get("color", 0)
                        r = ((c_int >> 16) & 255) / 255.0
                        g = ((c_int >> 8) & 255) / 255.0
                        b = (c_int & 255) / 255.0
                        return span.get("size", 9.0), is_bold, span.get("origin"), (r, g, b)
    return None, False, None, (0, 0, 0)

def proses_multi_tanggal_pdf(pdf_bytes, daftar_ganti, edit_gambar=True, teks_watermark_baru="Sabtu, 11 Januari 2025"):
    doc = fitz.open(stream=pdf_bytes, filetype="pdf")
    total_teks, total_gbr, xref_done = 0, 0, set()
    meta_terakhir = None

    path_font_bold = "/usr/share/fonts/truetype/dejavu/DejaVuSans-Bold.ttf"
    path_font_reg = "/usr/share/fonts/truetype/dejavu/DejaVuSans.ttf"

    for idx_hal, halaman in enumerate(doc):
        for teks_lama, teks_baru in daftar_ganti:
            if not teks_lama.strip():
                continue
            fs_asli, is_bold, origin_asli, warna_asli = deteksi_gaya_teks(halaman, teks_lama)
            for rect in halaman.search_for(teks_lama):
                fs = fs_asli if fs_asli else max(7.5, (rect.y1 - rect.y0) * 0.78)
                halaman.add_redact_annot(rect, fill=(1, 1, 1))
                halaman.apply_redactions()
                y_tulis = origin_asli[1] if (origin_asli and abs(origin_asli[1] - rect.y1) < 5) else (rect.y1 - 1.5)
                try:
                    if is_bold:
                        halaman.insert_text(fitz.Point(rect.x0, y_tulis), teks_baru, fontsize=fs, fontname="dejavubold", fontfile=path_font_bold, color=warna_asli)
                    else:
                        halaman.insert_text(fitz.Point(rect.x0, y_tulis), teks_baru, fontsize=fs, fontname="dejavureg", fontfile=path_font_reg, color=warna_asli)
                except Exception:
                    font_pakai = "hebo" if is_bold else "helv"
                    halaman.insert_text(fitz.Point(rect.x0, y_tulis), teks_baru, fontsize=fs, fontname=font_pakai, color=warna_asli)
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
                img_hasil = ImageEnhance.Sharpness(img_hasil).enhance(1.12)
                buf = io.BytesIO()
                img_hasil.save(buf, format="JPEG", quality=95, subsampling=0)
                halaman.replace_image(xref, stream=buf.getvalue())
                total_gbr += 1

        halaman.clean_contents()

    output_pdf = io.BytesIO()
    doc.save(output_pdf, garbage=3, deflate=True)
    doc.close()
    return output_pdf.getvalue(), total_teks, total_gbr

# --- HALAMAN LOGIN ---
if not st.session_state.login_sukses:
    st.write("")
    st.write("")
    _, col_left, col_right, _ = st.columns([0.45, 2.3, 2.1, 0.45], gap="large")
    with col_left:
        logo_html = f"<img src='{ICON_DATA_URL}' style='width:72px; height:72px; border-radius:18px; border:1.5px solid rgba(255,255,255,0.28); margin-bottom:16px; box-shadow:0 8px 24px rgba(0,0,0,0.45);'/>" if ICON_DATA_URL else ""
        st.markdown(f"""
        <div class='login-brand-panel'>
            {logo_html}
            <h1>IMOXdR</h1>
            <p></p>
            <div style='margin-top:24px;'>
                <span class='feature-pill'>{SVG_ICONS['calendar']} Auto-Tanggal PDF</span>
                <span class='feature-pill'>{SVG_ICONS['sparkles']} Hapus Kotak Pink</span>
                <span class='feature-pill'>{SVG_ICONS['layers']} Jahit Foto 0-50-100%</span>
                <span class='feature-pill'>{SVG_ICONS['camera']} Watermark</span>
            </div>
        </div>
        """, unsafe_allow_html=True)
    with col_right:
        st.markdown("<div class='glass-card' style='padding: 38px 34px;'>", unsafe_allow_html=True)
        st.markdown(f"<div style='display:flex; align-items:center; margin-bottom:6px;'>{ikon_badge('shield')} <span style='font-size:1.35rem; font-weight:800;'>Masuk Ruang Kerja</span></div>", unsafe_allow_html=True)
        st.caption("Keep The Track Clear and The Workflow Sharp")
        st.write("")
        username = st.text_input("Username", placeholder="Masukkan username")
        password = st.text_input("Password", type="password", placeholder="••••••••")
        st.write("")
        if st.button("Masuk Ruang Kerja", use_container_width=True):
            if username == USER_VALID and password == PASS_VALID:
                st.session_state.login_sukses = True
                st.rerun()
            else:
                st.error("Username atau Password salah!")
        st.markdown("</div>", unsafe_allow_html=True)
    st.stop()

# --- SIDEBAR NAVIGASI ---
with st.sidebar:
    if ICON_DATA_URL:
        st.markdown(f"<div style='display:flex; align-items:center; gap:12px;'><img src='{ICON_DATA_URL}' style='width:48px; height:48px; border-radius:14px; border:1px solid rgba(255,255,255,0.25);'/><div><p class='title-kai' style='font-size:1.7rem;'>IMOXdR</p><span style='font-size:0.74rem; color:{TEXT_SECONDARY};'>Automation Workspace</span></div></div>", unsafe_allow_html=True)
    else:
        st.markdown("<p class='title-kai'>IMOXdR</p>", unsafe_allow_html=True)
        st.caption("Automation Workspace Suite")
    st.divider()
    pilihan_menu = st.radio("Mode Aplikasi", [
        "Auto-Ubah Tanggal PDF & Foto",
        "Bersihkan Kotak Pink Anotasi",
        "Foto Progres 0-50-100%",
        "Generator Foto Watermark"
    ], label_visibility="collapsed")
    st.divider()
    mode_gelap = st.toggle("Dark Mode", value=st.session_state.dark_mode)
    if mode_gelap != st.session_state.dark_mode:
        st.session_state.dark_mode = mode_gelap
        st.rerun()
    st.write("")
    if st.button("Keluar Sesi", use_container_width=True):
        st.session_state.login_sukses = False
        st.rerun()

# --- HEADER & KPI BENTO ---
st.markdown(f"<div style='display:flex; align-items:center; justify-content:space-between; margin-bottom:14px;'><div><h2 style='margin:0; font-weight:800; letter-spacing:-0.4px;'>Selamat Bekerja, dR</h2><span style='font-size:0.84rem; color:{TEXT_SECONDARY};'></span></div></div>", unsafe_allow_html=True)

kpi1, kpi2, kpi3, kpi4 = st.columns([1.45, 1, 1, 1.15])
with kpi1:
    st.markdown(f"<div class='glass-hero'><div style='font-size:0.72rem; font-weight:700; letter-spacing:0.8px; opacity:0.85;'>ENGINE TERPADU</div>Glassmorphism<div style='font-size:1.35rem; font-weight:800; margin:4px 0;'>IMOXdR Suite v2.0</div><div style='font-size:0.78rem; opacity:0.9;'></div></div>", unsafe_allow_html=True)
with kpi2:
    st.markdown("<div class='glass-card'><div class='kpi-title'>Filter Anotasi</div><div class='kpi-value'>Smart</div><span class='kpi-badge-orange'>Foto Besar Aman</span></div>", unsafe_allow_html=True)
with kpi3:
    st.markdown("<div class='glass-card'><div class='kpi-title'>Auto-Tanggal</div><div class='kpi-value'>Sync</div><span class='kpi-badge-orange'>Font & Foto PDF</span></div>", unsafe_allow_html=True)
with kpi4:
    st.markdown(f"<div class='glass-card'><div class='kpi-title'>Dokumen Diproses</div><div class='kpi-value'>{len(st.session_state.riwayat_proses) - 1}</div><span class='kpi-badge-orange'>Sesi Hari Ini</span></div>", unsafe_allow_html=True)

# --- AREA KERJA UTAMA ---
main_area, right_panel = st.columns([2.75, 1.05], gap="medium")

with main_area:
    if pilihan_menu == "Auto-Ubah Tanggal PDF & Foto":
        st.markdown("<div class='glass-card'>", unsafe_allow_html=True)
        st.markdown(f"<div style='display:flex; align-items:center; margin-bottom:4px;'>{ikon_badge('calendar')} <span style='font-size:1.18rem; font-weight:800;'>Auto-Ubah Tanggal PDF & Foto (Deteksi Otomatis)</span></div>", unsafe_allow_html=True)
        st.caption("Tanggal asli di dalam PDF otomatis terbaca saat file diunggah, lengkap dengan pratinjau halaman sebelum dan sesudah revisi.")
        pdf_tanggal = st.file_uploader("Unggah File PDF Laporan Perawatan", type=["pdf"])

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

            with st.expander("Lihat Pratinjau PDF Asli Sebelum Diubah", expanded=False):
                tampilkan_panel_preview_pdf(pdf_bytes_cache, "Pratinjau Dokumen Asli")

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
        edit_foto_pdf = st.checkbox(f"Otomatis ubah tanggal di dalam seluruh foto menjadi: **{otomatis_wm}**", value=True)

        if pdf_bytes_cache and st.button("Eksekusi Perubahan Otomatis Sekarang", use_container_width=True):
            with st.spinner("Mendeteksi jenis font asli & menyinkronkan seluruh halaman serta foto..."):
                hasil_pdf_tgl, jml_teks, jml_gbr = proses_multi_tanggal_pdf(
                    pdf_bytes_cache, [(lama_1, baru_1), (lama_2, baru_2), (lama_3, baru_3)],
                    edit_foto_pdf, otomatis_wm
                )
                st.session_state.riwayat_proses.insert(0, {"waktu": "Baru saja", "modul": "Auto-Tanggal", "detail": f"{pdf_tanggal.name[:22]}... ({jml_teks} teks, {jml_gbr} foto)"})
                st.success(f"Berhasil! **{jml_teks} teks PDF** dan **{jml_gbr} foto dokumentasi** diperbarui menjadi **{otomatis_wm}**.")
                tampilkan_panel_preview_pdf(hasil_pdf_tgl, "Pratinjau Hasil Revisi (Siap Unduh)")
                nama_file_out = f"Revisi_{pdf_tanggal.name.replace(lama_1, baru_1)}"
                st.download_button("Unduh PDF Hasil Revisi", hasil_pdf_tgl, nama_file_out, "application/pdf", use_container_width=True)
        st.markdown("</div>", unsafe_allow_html=True)

    elif pilihan_menu == "Bersihkan Kotak Pink Anotasi":
        st.markdown("<div class='glass-card'>", unsafe_allow_html=True)
        st.markdown(f"<div style='display:flex; align-items:center; margin-bottom:4px;'>{ikon_badge('sparkles')} <span style='font-size:1.18rem; font-weight:800;'>Bersihkan Kotak Pink Anotasi</span></div>", unsafe_allow_html=True)
        st.caption("Unggah satu atau banyak file PDF checklist sekaligus untuk menghapus anotasi kotak pink dan mengecek hasilnya.")
        pdf_inputs = st.file_uploader("Unggah PDF Checklist Dasar (Bisa blok banyak file sekaligus)", type=["pdf"], accept_multiple_files=True, key="up_clean")
        if pdf_inputs and st.button(f"Bersihkan {len(pdf_inputs)} File Anotasi Sekarang", use_container_width=True):
            if len(pdf_inputs) == 1:
                pdf_file = pdf_inputs[0]
                hasil_pdf_bytes = proses_dokumen(pdf_file, [])
                nama_unduh = pdf_file.name[:-4] + " revisi.pdf" if pdf_file.name.lower().endswith(".pdf") else pdf_file.name + " revisi.pdf"
                st.session_state.riwayat_proses.insert(0, {"waktu": "Baru saja", "modul": "Clean Anotasi", "detail": pdf_file.name[:26]})
                st.success("Selesai! Kotak pink berhasil dihapus.")
                tampilkan_panel_preview_pdf(hasil_pdf_bytes, "Pratinjau Dokumen Bersih")
                st.download_button("Unduh File Bersih", data=hasil_pdf_bytes, file_name=nama_unduh, mime="application/pdf", use_container_width=True)
            else:
                zip_buffer = io.BytesIO()
                preview_pertama = None
                with zipfile.ZipFile(zip_buffer, "w", zipfile.ZIP_DEFLATED) as zip_file:
                    for idx, pdf_file in enumerate(pdf_inputs):
                        nama_unduh = pdf_file.name[:-4] + " revisi.pdf" if pdf_file.name.lower().endswith(".pdf") else pdf_file.name + " revisi.pdf"
                        hasil_item = proses_dokumen(pdf_file, [])
                        if idx == 0:
                            preview_pertama = hasil_item
                        zip_file.writestr(nama_unduh, hasil_item)
                st.session_state.riwayat_proses.insert(0, {"waktu": "Baru saja", "modul": "Batch ZIP", "detail": f"{len(pdf_inputs)} file PDF"})
                st.success(f"Selesai! {len(pdf_inputs)} file dibersihkan.")
                if preview_pertama:
                    tampilkan_panel_preview_pdf(preview_pertama, f"Pratinjau Sampel File Pertama ({pdf_inputs[0].name})")
                st.download_button("Unduh Semua File (ZIP)", data=zip_buffer.getvalue(), file_name="Laporan_Bersih.zip", mime="application/zip", use_container_width=True)
        st.markdown("</div>", unsafe_allow_html=True)

    elif pilihan_menu == "Foto Progres 0-50-100%":
        st.markdown("<div class='glass-card'>", unsafe_allow_html=True)
        st.markdown(f"<div style='display:flex; align-items:center; margin-bottom:4px;'>{ikon_badge('layers')} <span style='font-size:1.18rem; font-weight:800;'>Bersihkan Anotasi & Jahit Foto Progres (0% - 50% - 100%)</span></div>", unsafe_allow_html=True)
        st.caption("Unggah PDF checklist dasar, lalu isi hingga 5 judul aset beserta 3 foto progres (0%, 50%, 100%) di masing-masing aset.")
        pdf_jahit = st.file_uploader("Unggah File PDF Checklist Dasar", type=["pdf"], key="up_jahit_single")

        st.markdown("##### Form Rangkaian Foto Progres (5 Aset × 3 Kolom)")
        data_siap_proses = []
        for i in range(1, 6):
            with st.expander(f"Rangkaian Aset ke-{i}", expanded=(i == 1)):
                nama_aset = st.text_input(f"Nama Aset {i}", key=f"nama_{i}", placeholder="Contoh: Peraga Sinyal / Penggerak Wesel")
                col1, col2, col3 = st.columns(3)
                with col1:
                    img_0 = st.file_uploader("Foto 0%", key=f"img0_{i}", type=["jpg", "jpeg", "png"])
                    if img_0:
                        st.image(img_0, use_container_width=True, caption="FOTO 0%")
                with col2:
                    img_50 = st.file_uploader("Foto 50%", key=f"img50_{i}", type=["jpg", "jpeg", "png"])
                    if img_50:
                        st.image(img_50, use_container_width=True, caption="FOTO 50%")
                with col3:
                    img_100 = st.file_uploader("Foto 100%", key=f"img100_{i}", type=["jpg", "jpeg", "png"])
                    if img_100:
                        st.image(img_100, use_container_width=True, caption="FOTO 100%")
                if nama_aset and img_0 and img_50 and img_100:
                    data_siap_proses.append({"nama_aset": nama_aset, "img_0": img_0, "img_50": img_50, "img_100": img_100})

        st.write("")
        if pdf_jahit is not None:
            if len(data_siap_proses) > 0:
                if st.button("Menjahit Dokumen Sekarang!", use_container_width=True):
                    with st.spinner("Membersihkan kotak pink & menjahit foto progres..."):
                        hasil_pdf_bytes = proses_dokumen(pdf_jahit, data_siap_proses)
                        nama_unduh = pdf_jahit.name[:-4] + " revisi.pdf" if pdf_jahit.name.lower().endswith(".pdf") else pdf_jahit.name + " revisi.pdf"
                        st.session_state.riwayat_proses.insert(0, {"waktu": "Baru saja", "modul": "Jahit Foto", "detail": f"{len(data_siap_proses)} aset dijahit"})
                        st.success("Dokumen Selesai Dijahit!")
                        tampilkan_panel_preview_pdf(hasil_pdf_bytes, "Pratinjau Halaman Final")
                        st.download_button("Unduh File Final: " + nama_unduh, data=hasil_pdf_bytes, file_name=nama_unduh, mime="application/pdf", use_container_width=True)
            else:
                st.info("Isi Nama Aset serta Foto 0%, 50%, dan 100% minimal pada 1 rangkaian untuk memunculkan tombol jahit.")
        st.markdown("</div>", unsafe_allow_html=True)

    elif pilihan_menu == "Generator Foto Watermark":
        st.markdown("<div class='glass-card'>", unsafe_allow_html=True)
        st.markdown(f"<div style='display:flex; align-items:center; margin-bottom:4px;'>{ikon_badge('camera')} <span style='font-size:1.18rem; font-weight:800;'>Generator Foto Kegiatan Watermark</span></div>", unsafe_allow_html=True)
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
                image_wm = ImageOps.exif_transpose(Image.open(uploaded_image)).convert("RGB")
                draw = ImageDraw.Draw(image_wm)
                ukuran_font = max(20, int(min(image_wm.width, image_wm.height) * 0.028))
                batas_karakter = int((image_wm.width * 0.80) / (ukuran_font * 0.55))
                teks_watermark = f"{waktu}\n\n{chr(10).join(textwrap.wrap(lokasi, width=batas_karakter))}\n\n{koordinat}\n\n{chr(10).join(textwrap.wrap(kegiatan, width=batas_karakter))}"
                font = muat_font_roboto(ukuran_font)
                margin_x, margin_y, spacing_teks = int(image_wm.width * 0.05), int(image_wm.height * 0.05), int(ukuran_font * 0.3)
                try:
                    bbox = draw.multiline_textbbox((0, 0), teks_watermark, font=font, spacing=spacing_teks)
                    tinggi_teks = bbox[3] - bbox[1]
                except Exception:
                    tinggi_teks = (teks_watermark.count('\n') + 1) * int(ukuran_font * 1.3)
                lebar_garis = max(5, int(ukuran_font * 0.25))
                draw.rectangle([margin_x, margin_y, margin_x + lebar_garis, margin_y + tinggi_teks], fill="blue")
                text_x = margin_x + lebar_garis + int(ukuran_font * 0.6)
                draw.multiline_text((text_x + 1, margin_y + 1), teks_watermark, font=font, fill="black", spacing=spacing_teks)
                draw.multiline_text((text_x, margin_y), teks_watermark, font=font, fill="white", spacing=spacing_teks)
                st.session_state.riwayat_proses.insert(0, {"waktu": "Baru saja", "modul": "Watermark Foto", "detail": kegiatan[:26]})
                st.image(image_wm, caption="Hasil Jahitan Watermark", use_container_width=True)
                buf_img = io.BytesIO()
                image_wm.save(buf_img, format="JPEG", quality=95, subsampling=0)
                st.download_button("Unduh Foto", data=buf_img.getvalue(), file_name="Foto_Watermark.jpg", mime="image/jpeg", use_container_width=True)
        st.markdown("</div>", unsafe_allow_html=True)

# --- PANEL KANAN (STATUS & LOG) ---
with right_panel:
    st.markdown(f"<div class='ai-orb-box'><div class='ai-orb'></div><div style='font-weight:800; font-size:1.05rem; margin-bottom:4px;'>Smart Document Sync</div><div style='font-size:0.78rem; color:{TEXT_SECONDARY}; line-height:1.5;'>4 modul aktif: Auto-Tanggal PDF & Foto, Pembersih Kotak Pink, Penjahit Progres, dan Watermark.</div></div>", unsafe_allow_html=True)
    st.write("")
    st.markdown("<div class='glass-card'>", unsafe_allow_html=True)
    st.markdown(f"<div style='display:flex; align-items:center; gap:8px; font-weight:800; font-size:0.95rem; margin-bottom:10px;'>{SVG_ICONS['clock']} Aktivitas Terbaru</div>", unsafe_allow_html=True)
    for item in st.session_state.riwayat_proses[:5]:
        st.markdown(f"<div style='border-bottom:1px solid {BORDER_GLASS}; padding:9px 0;'><div style='display:flex; justify-content:space-between; font-size:0.74rem;'><span style='font-weight:700; color:#FF8A4C;'>{item['modul']}</span><span style='color:{TEXT_SECONDARY};'>{item['waktu']}</span></div><div style='font-size:0.8rem; margin-top:3px;'>{item['detail']}</div></div>", unsafe_allow_html=True)
    st.markdown("</div>", unsafe_allow_html=True)
