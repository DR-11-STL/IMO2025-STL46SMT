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
    BG_APP = "#0B0F19"
    BG_SIDEBAR = "#111827"
    BG_CARD = "#151C2C"
    BORDER_CARD = "#1E293B"
    TEXT_PRIMARY = "#F8FAFC"
    TEXT_SECONDARY = "#94A3B8"
    INPUT_BG = "#0F172A"
else:
    BG_APP = "#F4F6FA"
    BG_SIDEBAR = "#FFFFFF"
    BG_CARD = "#FFFFFF"
    BORDER_CARD = "#E2E8F0"
    TEXT_PRIMARY = "#0F172A"
    TEXT_SECONDARY = "#64748B"
    INPUT_BG = "#F8FAFC"

KAI_BLUE = "#282562"
KAI_BLUE_LIGHT = "#3B378C"
KAI_ORANGE = "#ec6923"

# --- CUSTOM CSS: TEMA BENTO GRID KAI MODERN (LIGHT & DARK) ---
st.markdown(f"""
<style>
@import url('https://fonts.googleapis.com/css2?family=Plus+Jakarta+Sans:wght@400;500;600;700;800;900&display=swap');

#MainMenu, header, footer {{visibility: hidden;}}
html, body, [class*="css"] {{
    font-family: 'Plus Jakarta Sans', sans-serif !important;
}}
.stApp {{
    background-color: {BG_APP};
    color: {TEXT_PRIMARY};
    transition: background-color 0.3s ease;
}}
section[data-testid="stSidebar"] {{
    background-color: {BG_SIDEBAR} !important;
    border-right: 1px solid {BORDER_CARD};
}}
.stMarkdown p, label, span {{
    color: {TEXT_PRIMARY} !important;
}}

/* Judul Utama dengan Biru KAI + Garis Tepi Putih */
.title-kai {{
    font-size: 2.3rem;
    font-weight: 900;
    margin: 0;
    padding: 0;
    color: {KAI_BLUE};
    -webkit-text-stroke: 1.2px #FFFFFF;
    text-shadow: 2px 2px 6px rgba(0, 0, 0, 0.7);
}}

/* Split-Screen Login Left Panel */
.login-brand-panel {{
    background: linear-gradient(145deg, {KAI_BLUE} 0%, #17153B 65%, {KAI_ORANGE} 140%);
    border-radius: 20px;
    padding: 45px 35px;
    color: #FFFFFF !important;
    box-shadow: 0 20px 40px rgba(0, 0, 0, 0.35);
    border: 1px solid rgba(255,255,255,0.12);
    height: 100%;
}}
.login-brand-panel h1 {{
    font-size: 3.3rem;
    font-weight: 900;
    color: {KAI_BLUE};
    -webkit-text-stroke: 1.5px #FFFFFF;
    text-shadow: 2px 2px 6px rgba(0, 0, 0, 0.8);
    margin-bottom: 12px;
}}
.login-brand-panel p {{
    color: #E2E8F0 !important;
    font-size: 0.95rem;
    line-height: 1.6;
}}
.feature-pill {{
    display: inline-block;
    background: rgba(255, 255, 255, 0.12);
    border: 1px solid rgba(255, 255, 255, 0.2);
    padding: 7px 13px;
    border-radius: 12px;
    font-size: 0.8rem;
    font-weight: 600;
    color: #FFFFFF !important;
    margin-right: 6px;
    margin-top: 10px;
}}

/* Bento Cards */
.bento-card {{
    background-color: {BG_CARD};
    border: 1px solid {BORDER_CARD};
    border-radius: 16px;
    padding: 20px 22px;
    box-shadow: 0 4px 20px rgba(0, 0, 0, 0.08);
    margin-bottom: 16px;
}}
.bento-hero {{
    background: linear-gradient(135deg, {KAI_BLUE} 0%, {KAI_BLUE_LIGHT} 60%, {KAI_ORANGE} 135%);
    border-radius: 16px;
    padding: 20px 22px;
    color: #FFFFFF !important;
    box-shadow: 0 10px 25px rgba(40, 37, 98, 0.35);
    margin-bottom: 16px;
}}
.bento-hero * {{
    color: #FFFFFF !important;
}}
.kpi-title {{
    font-size: 0.78rem;
    font-weight: 600;
    color: {TEXT_SECONDARY} !important;
    text-transform: uppercase;
    letter-spacing: 0.5px;
}}
.kpi-value {{
    font-size: 1.95rem;
    font-weight: 800;
    color: {TEXT_PRIMARY} !important;
    margin: 4px 0;
}}
.kpi-badge-orange {{
    background-color: rgba(236, 105, 35, 0.18);
    color: {KAI_ORANGE} !important;
    padding: 3px 10px;
    border-radius: 999px;
    font-size: 0.74rem;
    font-weight: 700;
}}

/* AI Assistant Orb */
.ai-orb-box {{
    background-color: {BG_CARD};
    border: 1px solid {BORDER_CARD};
    border-radius: 16px;
    padding: 20px;
    text-align: center;
}}
.ai-orb {{
    width: 80px;
    height: 80px;
    margin: 10px auto 14px auto;
    border-radius: 50%;
    background: radial-gradient(circle at 30% 30%, {KAI_ORANGE}, {KAI_BLUE} 70%, #090D16 100%);
    box-shadow: 0 0 28px rgba(236, 105, 35, 0.55), inset 0 0 15px rgba(255,255,255,0.35);
    animation: pulseOrb 3s infinite ease-in-out;
}}
@keyframes pulseOrb {{
    0% {{ transform: scale(0.96); box-shadow: 0 0 20px rgba(236, 105, 35, 0.45); }}
    50% {{ transform: scale(1.04); box-shadow: 0 0 36px rgba(40, 37, 98, 0.85); }}
    100% {{ transform: scale(0.96); box-shadow: 0 0 20px rgba(236, 105, 35, 0.45); }}
}}

/* Kustomisasi Tombol Utama */
.
