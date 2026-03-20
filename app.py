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
st.set_page_config(page_title="Etsy POD Master VIP", page_icon="🛍️", layout="wide")

st.markdown("""
    <style>
    /* Estilo General Watercolor */
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

    /* Navegación Superior Estilizada (Tabs) */
    .stTabs [data-baseweb="tab-list"] {
        gap: 15px;
        background-color: rgba(255, 255, 255, 0.9);
        padding: 10px 20px;
        border-radius: 50px;
        box-shadow: 0 4px 15px rgba(0,0,0,0.05);
    }
    .stTabs [data-baseweb="tab"] {
        height: 45px;
        font-weight: 600;
        font-size: 15px;
        color: #888;
        border-radius: 25px;
        border: none;
    }
    .stTabs [aria-selected="true"] {
        background-color: #ffb6c1 !important;
        color: white !important;
    }

    /* Burbuja de Radar Discreta y Flotante */
    .radar-container {
        position: fixed;
        bottom: 20px;
        right: 20px;
        z-index: 1000;
    }
    .radar-box {
        background: #2d3436;
        color: white;
        padding: 15px;
        border-radius: 15px;
        border-left: 5px solid #ffb6c1;
        font-size: 13px;
        box-shadow: 0 10px 20px rgba(0,0,0,0.2);
    }
    </style>
    """, unsafe_allow_html=True)

# =========================
# INICIALIZACIÓN DE MEMORIA
# =========================
if "product" not in st.session_state: st.session_state["product"] = None
if "detected_text" not in st.session_state: st.session_state["detected_text"] = ""
if "niche" not in st.session_state: st.session_state["niche"] = ""
if "tienda" not in st.session_state: st.session_state["tienda"] = "🐾 Tienda POD Mascotas"
if "tags_generados" not in st.session_state: st.session_state["tags_generados"] = []

@st.cache_resource
def load_reader():
    return easyocr.Reader(["en", "es"], gpu=False)
reader = load_reader()

# =========================
# MOTOR ESTRATÉGICO (FUNCIONES)
# =========================
def extraer_texto_ocr(reader, image):
    image_np = np.array(image)
    try:
        resultados = reader.readtext(image_np)
        return " ".join([r[1] for r in resultados if len(r) >= 2])
    except: return ""

def extraer_keywords_texto(texto, max_keywords=12):
    limpio = re.sub(r"[^a-zA-Z0-9\s-]", " ", texto.lower())
    tokens = [t for t in re.split(r"\s+", limpio) if len(t) > 2]
    stopwords = {"the","and","for","with","this","that","your","you","are","from","gift","para","con","una","uno","tus","tu","las","los","del","por","que","esta","este","como","muy","pero","solo","mas"}
    return [t for t in tokens if t not in stopwords][:max_keywords]

def recomendar_producto_ganador(texto, niche):
    t, n = texto.lower(), niche.lower()
    if any(w in t or w in n for w in ["memorial", "fallecida", "rainbow"]):
        return ["Velveteen Plush Blanket", "Acrylic Plaque"]
    if any(w in n for w in ["dog", "cat", "pet"]):
        return ["Pet Bandana", "White Ceramic Mug 15oz"]
    return ["Bella+Canvas 3001", "Gildan 18500 Hoodie"]

def generar_titulos_venta(keywords, product, niche, lang="en"):
    base = " ".join(keywords[:3]).title() if keywords else "Custom"
    prod = product if product else "Item"
    nch = niche if niche else "Lover"
    if lang == "en":
        return [
            (f"Personalized {prod} for {nch}, {base} Gift for {nch}, Custom Name {prod}, Unique {nch} Present", 98),
            (f"{nch} Gift, Custom {prod} with {base}, Personalized {nch} Appreciation Gift, Trendy POD Design", 92),
            (f"Custom {base} {prod}, Best {nch} Gift Idea, Personalized {prod} with Name, Trending Etsy Item", 85)
        ]
    return [(f"{prod} Personalizado para {nch}, Regalo de {base}", 98)]

def generar_tags_etsy(keywords, product, niche):
    kw = keywords[0] if keywords else "gift"
    return [f"custom {product}"[:20], f"{niche} gift"[:20], "personalized"[:20], f"gift for {niche}"[:20], f"{kw} gift"[:20], "unique present"[:20]][:13]

def generar_descripcion_vendedora(product, niche, texto_detectado):
    return f"""🔥 Give the perfect gift with this Custom {product} designed exclusively for {niche}s! 
Whether you're looking for a unique present or treating yourself, this "{texto_detectado}" design is guaranteed to bring a smile. 

✨ HOW TO PERSONALIZE ✨
1. Enter the name/text in the personalization box.
2. Double-check spelling! We print exactly what you provide.
3. Add to cart!

🎨 DIGITAL PROOF ADD-ON (OPTIONAL)
To keep our production times fast and our prices low, proofs are NOT automatically included. 
If you are ordering a PHYSICAL product and would like to see the artwork before it goes to print, please purchase our "Digital Proof Add-On" listing alongside this item.

👕 PRODUCT DETAILS 
- Premium quality {product}. Vibrant, durable POD printing.
📦 SHIPPING: Processed in 2-5 business days. Tracking included!"""

# =========================
# INTERFAZ SUPERIOR
# =========================
col_title, col_logo = st.columns([4, 1])
with col_title:
    st.markdown("<h1>🌸 Etsy Master <span style='color:#ffb6c1;'>Watercolor Pro</span></h1>", unsafe_allow_html=True)
with col_logo:
    st.image("https://upload.wikimedia.org/wikipedia/commons/thumb/a/aa/Etsy_logo.svg/1200px-Etsy_logo.svg.png", width=80)

# BURBUJA RADAR ELIMINABLE
with st.container():
    st.markdown('<div class="radar-container">', unsafe_allow_html=True)
    with st.expander("🔔 Radar de Tendencias", expanded=True):
        st.markdown("""
        <div class="radar-box">
            <b>Q2: Mother's Day & Graduations</b><br>
            Sube diseños de acuarela y lienzos.<br>
            <i>Trend: Retro Wavy Text.</i>
        </div>
        """, unsafe_allow_html=True)
    st.markdown('</div>', unsafe_allow_html=True)

# TABS DE NAVEGACIÓN (TU MOTOR COMPLETO)
tabs = st.tabs(["🏠 Inicio", "🔍 1. OCR", "🛒 2. Catálogo", "🚀 3. SEO", "💬 4. Muestras", "💰 5. Dinero", "⚖️ 6. Legal", "💡 7. Ideas"])

# --- TAB 1: DASHBOARD ---
with tabs[0]:
    st.subheader("Hola, Estratega 👋")
    c1, c2 = st.columns(2)
    with c1:
        st.info(f"🛒 **Tienda:** {st.session_state['tienda']}\n\n🎯 **Nicho:** {st.session_state['niche']}")
    with c2:
        st.success(f"📦 **Producto:** {st.session_state['product']}\n\n📝 **Texto:** {st.session_state['detected_text']}")
    st.markdown("---")
    st.subheader("🎫 Estrategia de Lealtad")
    st.write("• **VUELVE15**: 15% OFF Carrito Abandonado.")
    st.write("• **THANKS20**: Cupón físico para Re-compra.")

# --- TAB 2: OCR ---
with tabs[1]:
    st.header("Análisis de Imagen")
    up = st.file_uploader("Sube tu diseño (PNG Transparente)", type=["png", "jpg", "jpeg"])
    if up:
        img = Image.open(up)
        st.image(img, width=300)
        if st.button("👁️ Leer Texto"):
            st.session_state["detected_text"] = extraer_texto_ocr(reader, img)
            st.rerun()
    if st.session_state["detected_text"]:
        st.session_state["detected_text"] = st.text_input("Confirmar Concepto:", st.session_state["detected_text"])

# --- TAB 3: CATÁLOGO ---
with tabs[2]:
    st.header("Perfil y Productos")
    st.session_state["tienda"] = st.radio("Tienda:", ["🐾 Tienda POD Mascotas", "💌 Tienda Digital"], horizontal=True)
    if st.session_state["detected_text"]:
        st.success("🤖 **Sugerencia IA:**")
        for s in recomendar_producto_ganador(st.session_state["detected_text"], st.session_state["niche"]): st.write(f"🔥 {s}")
    
    prods = ["Bella+Canvas 3001", "Gildan 18500", "Velveteen Blanket", "Acrylic Plaque", "Pet Bandana"] if st.session_state["tienda"] == "🐾 Tienda POD Mascotas" else ["Digital Invitation", "Mobile Evite", "Memorial Sign"]
    st.session_state["product"] = st.selectbox("Selecciona Producto:", prods)

# --- TAB 4: SEO ---
with tabs[3]:
    st.header("Generador SEO (Porcentajes + Tags)")
    if st.session_state["product"] and st.session_state["detected_text"]:
        kws = extraer_keywords_texto(st.session_state["detected_text"])
        titulos = generar_titulos_venta(kws, st.session_state["product"], st.session_state["niche"])
        for t, s in titulos:
            st.success(f"⭐ **{s}% MATCH Score**")
            st.code(t)
        st.subheader("🏷️ Tags (13 Etiquetas)")
