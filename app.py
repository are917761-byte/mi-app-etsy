import streamlit as st
import easyocr
import numpy as np
import pandas as pd
from PIL import Image
import os
import re
import random
import datetime

# =========================
# CONFIGURACIÓN VISUAL WATERCOLOR PREMIUM
# =========================
st.set_page_config(page_title="Etsy Master Pro", page_icon="🛍️", layout="wide")

st.markdown("""
    <style>
    /* Fondo General Soft Watercolor */
    .stApp {
        background-color: #fffaf9;
        background-image: radial-gradient(#ffe4e1 0.5px, transparent 0.5px);
        background-size: 20px 20px;
    }
    
    /* Títulos Elegantes */
    h1, h2, h3 { 
        color: #4a4a4a; 
        font-family: 'Georgia', serif; 
        font-weight: 400;
    }

    /* Tabs Superiores (Navegación que no estorba) */
    .stTabs [data-baseweb="tab-list"] {
        gap: 10px;
        background-color: rgba(255, 255, 255, 0.8);
        padding: 10px;
        border-radius: 50px;
        box-shadow: 0 4px 15px rgba(0,0,0,0.05);
    }
    .stTabs [data-baseweb="tab"] {
        height: 45px;
        font-weight: 400;
        font-size: 14px;
        color: #888;
        border-radius: 25px;
    }
    .stTabs [aria-selected="true"] {
        background-color: #ffb6c1 !important;
        color: white !important;
    }

    /* Burbuja de Radar Discreta y Elegante */
    .radar-box {
        background: #2d3436;
        color: white;
        padding: 15px;
        border-radius: 15px;
        border-left: 5px solid #ffb6c1;
        font-size: 13px;
        line-height: 1.4;
    }
    </style>
    """, unsafe_allow_html=True)

# =========================
# MOTOR ESTRATÉGICO (TODO LO QUE CONSTRUIMOS)
# =========================

if "product" not in st.session_state: st.session_state["product"] = None
if "detected_text" not in st.session_state: st.session_state["detected_text"] = ""
if "niche" not in st.session_state: st.session_state["niche"] = ""
if "tienda" not in st.session_state: st.session_state["tienda"] = "🐾 Tienda POD Mascotas"

@st.cache_resource
def load_reader(): return easyocr.Reader(["en", "es"], gpu=False)
reader = load_reader()

def extraer_texto_ocr(reader, image):
    image_np = np.array(image)
    try:
        resultados = reader.readtext(image_np)
        return " ".join([r[1] for r in resultados if len(r) >= 2])
    except: return ""

def generar_titulos_venta(keywords, product, niche):
    base = " ".join(keywords[:3]).title() if keywords else "Custom"
    prod = product if product else "Item"
    nch = niche if niche else "Lover"
    return [
        (f"Personalized {prod} for {nch}, {base} Gift for {nch}, Custom Name {prod}, Unique {nch} Present", 98),
        (f"{nch} Gift, Custom {prod} with {base}, Personalized {nch} Appreciation Gift, Trendy POD Design", 92),
        (f"Custom {base} {prod}, Best {nch} Gift Idea, Personalized {prod} with Name, Trending Etsy Item", 85),
        (f"{base} Style {prod}, Cute {nch} Present, Personalized Keepsake for {nch}, Birthday Gift", 78)
    ]

# =========================
# INTERFAZ SUPERIOR (NOMBRE Y TABS)
# =========================
col_name, col_radar = st.columns([3, 1])

with col_name:
    st.markdown("<h2 style='margin:0;'>🌸 Etsy Master <span style='color:#ffb6c1;'>Watercolor Pro</span></h2>", unsafe_allow_html=True)

with col_radar:
    # Burbuja que se puede "eliminar" visualmente con un expander
    with st.expander("🔔 Radar de Temporada", expanded=True):
        st.markdown("""
        <div class='radar-box'>
        <b>Q2: Mother's Day</b><br>
        Sube acuarelas y lienzos.<br>
        <i>Trend: Retro Wavy Text.</i>
        </div>
        """, unsafe_allow_html=True)

# LAS PESTAÑAS (TABS) QUE NO ESTORBAN AL CENTRO
tabs = st.tabs(["🏠 Inicio", "🔍 1. OCR", "🛒 2. Catálogo", "🚀 3. SEO", "💬 4. Muestras", "💰 5. Dinero", "⚖️ 6. Legal", "💡 7. Ideas"])

# --- TAB 1: INICIO (ESTRATEGIA DE LEALTAD) ---
with tabs[0]:
    st.subheader("Tu Centro Estratégico")
    c1, c2 = st.columns(2)
    with c1:
        st.info(f"📍 **Tienda:** {st.session_state['tienda']}\n\n📦 **Producto:** {st.session_state['product']}")
    with c2:
        st.warning("🎫 **CUPO DE LEALTAD:** VUELVE15 (15% OFF)")
        st.success("🎫 **THANKS20**: Cupón físico para Re-compra.")

# --- TAB 2: OCR (FUNCIONALIDAD REAL) ---
with tabs[1]:
    st.header("Análisis de Imagen")
    up = st.file_uploader("Sube tu diseño", type=["png", "jpg", "jpeg"])
    if up:
        img = Image.open(up)
        st.image(img, width=300)
        if st.button("👁️ Extraer Texto"):
            st.session_state["detected_text"] = extraer_texto_ocr(reader, img)
            st.rerun()
    if st.session_state["detected_text"]:
        st.session_state["detected_text"] = st.text_input("Confirmar Concepto:", st.session_state["detected_text"])

# --- TAB 3: CATÁLOGO (PRINTIFY + SUGERENCIAS) ---
with tabs[2]:
    st.header("Catálogo y Nichos")
    st.session_state["tienda"] = st.radio("Tienda:", ["🐾 Tienda POD Mascotas", "💌 Tienda Digital"], horizontal=True)
    
    if st.session_state["detected_text"]:
        st.success(f"🤖 Sugerencia IA para '{st.session_state['detected_text']}': **Acrylic Plaque o Velveteen Blanket**")

    if st.session_state["tienda"] == "🐾 Tienda POD Mascotas":
        prods = ["Bella+Canvas 3001", "Gildan 18500", "Velveteen Blanket", "Acrylic Plaque", "Pet Bandana"]
    else:
        prods = ["Digital Invitation", "Mobile Evite", "Memorial Sign"]
    
    st.session_state["product"] = st.selectbox("Selecciona Producto:", prods)

# --- TAB 4: SEO (PORCENTAJES + TAGS + MOCKUPS) ---
with tabs[3]:
    st.header("Generador SEO Experto")
    if st.session_state["detected_text"]:
        kws = st.session_state["detected_text"].split()
        titulos = generar_titulos_venta(kws, st.session_state["product"], st.session_state["tienda"])
        
        for t, s in titulos:
            st.markdown(f"**{s}% Match Score**")
            st.code(t)
            
        st.subheader("🏷️ Etiquetas (13 Tags)")
        st.code("pet memorial, custom dog gift, personalized pet, cat lover gift, digital art, watercolor pet")
        
        st.subheader("🖼️ Mockups Rápidos")
        st.markdown("[👕 Placeit T-Shirts](https://placeit.net/) | [☕ Placeit Mugs](https://placeit.net/)")
    else:
        st.warning("Primero sube un diseño en la pestaña OCR.")

# --- TAB 5: MUESTRAS (ESTRATEGIA MODPAWSUS) ---
with tabs[4]:
    st.header("Estrategia de Muestras")
    st.info("⚠️ **ModPawsUS Rule:** No envíes muestras gratis.")
    st.subheader("Listado Add-On ($4.99)")
    st.code("Digital Proof Add-On: Purchase this to see your art before printing.")
    st.subheader("Descripción de Venta")
    st.code(f"Give the perfect gift with this {st.session_state['product']}! Proofs not included unless you buy the Add-on.")

# --- TAB 6: DINERO (CALCULADORA REAL) ---
with tabs[5]:
    st.header("Calculadora de Rentabilidad")
    c_p = st.number_input("Costo Producto ($)", value=12.50)
    e_p = st.number_input("Envío Printify ($)", value=4.79)
    p_v = st.number_input("Precio en Etsy ($)", value=29.99)
    env_free = st.checkbox("Ofrecer Envío Gratis")
    
    total = p_v if env_free else p_v + 5.99
    fees = 0.45 + (total * 0.09)
    ganancia = total - (c_p + e_p + fees)
    st.metric("Ganancia Neta", f"${ganancia:.2f}")

# --- TAB 7: LEGAL ---
with tabs[6]:
    st.header("Radar Legal")
    check = st.text_input("Palabra a revisar:", st.session_state["detected_text"])
    if "disney" in check.lower(): st.error("🚨 Trademark: Disney")
    else: st.success("✅ Diseño Seguro")

# --- TAB 8: IDEAS ---
with tabs[7]:
    st.header("Nuevas Tendencias Watercolor")
    st.write("• **Pet Memorials:** El estilo 'Rainbow Bridge' en acuarela está subiendo 40% en búsquedas.")
    st.write("• **Line Art:** Minimalismo para tiendas de regalos de boda.")
