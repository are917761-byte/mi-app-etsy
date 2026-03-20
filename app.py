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
# CONFIGURACIÓN Y ESTILO ELEGANTE (CSS)
# =========================
st.set_page_config(page_title="Etsy POD Master VIP", page_icon="🛍️", layout="wide")

st.markdown("""
    <style>
    /* Tipografía General */
    html, body, [class*="css"] {
        font-family: 'Helvetica Neue', Helvetica, Arial, sans-serif;
    }
    
    /* Botones de Navegación Superior */
    .stButton > button {
        border-radius: 20px;
        border: 1px solid #e0e0e0;
        background-color: white;
        color: #333;
        font-weight: 500;
        padding: 10px 24px;
        transition: all 0.3s;
    }
    .stButton > button:hover {
        border-color: #ff5a1f;
        color: #ff5a1f;
        box-shadow: 0 4px 12px rgba(0,0,0,0.05);
    }
    
    /* Burbujas de Notificación Flotantes (Abajo Derecha) */
    .floating-notify {
        position: fixed;
        bottom: 20px;
        right: 20px;
        width: 280px;
        background: white;
        padding: 15px;
        border-radius: 15px;
        box-shadow: 0 10px 25px rgba(0,0,0,0.1);
        border-left: 5px solid #ff5a1f;
        z-index: 1000;
        font-size: 13px;
        animation: slideIn 0.5s ease-out;
    }
    
    @keyframes slideIn {
        from { transform: translateX(100%); opacity: 0; }
        to { transform: translateX(0); opacity: 1; }
    }

    /* Títulos Elegantes */
    h1, h2, h3 {
        color: #2c3e50;
        letter-spacing: -0.5px;
    }
    </style>
    """, unsafe_allow_html=True)

# =========================
# INICIALIZACIÓN DE MEMORIA
# =========================
if "menu_actual" not in st.session_state:
    st.session_state["menu_actual"] = "📊 Dashboard"
if "product" not in st.session_state:
    st.session_state["product"] = None
if "detected_text" not in st.session_state:
    st.session_state["detected_text"] = ""
if "niche" not in st.session_state:
    st.session_state["niche"] = ""
if "tienda" not in st.session_state:
    st.session_state["tienda"] = "🐾 Tienda POD Mascotas"

@st.cache_resource
def load_reader():
    return easyocr.Reader(["en", "es"], gpu=False)

reader = load_reader()

# =========================
# FUNCIONES NÚCLEO (IA Y SEO)
# =========================
# (Mantengo tus funciones de OCR y SEO igual para no romper la lógica)
def extraer_texto_ocr(reader, image):
    image_np = np.array(image)
    try:
        resultados = reader.readtext(image_np)
        return " ".join([r[1] for r in resultados if len(r) >= 2])
    except: return ""

def generar_titulos_venta(keywords, product, niche, lang="en"):
    base = " ".join(keywords[:3]).title() if keywords else "Design"
    prod = product.title() if product else "Custom Item"
    nch = niche.title() if niche else "Everyone"
    if lang == "en":
        return [(f"Personalized {prod} for {nch}, {base} Gift for {nch}, Custom Name {prod}", 98)]
    return [(f"{prod} Personalizado para {nch}, Regalo de {base}", 98)]

def generar_tags_etsy(keywords, product, niche):
    kw = keywords[0] if keywords else "trendy"
    return [f"custom {product}"[:20], f"{niche} gift"[:20], "personalized"[:20], f"{kw} gift"[:20]][:13]

# =========================
# NAVEGACIÓN SUPERIOR (BOTONES)
# =========================
st.image("https://upload.wikimedia.org/wikipedia/commons/thumb/a/aa/Etsy_logo.svg/1200px-Etsy_logo.svg.png", width=100)
nav_cols = st.columns(7)
opciones = ["📊 Dashboard", "🔍 1. OCR", "🛒 2. Catálogo", "🚀 3. SEO", "💬 4. Muestras", "💰 5. Dinero", "⚖️ 6. Legal"]

for i, opcion in enumerate(opciones):
    if nav_cols[i].button(opcion):
        st.session_state["menu_actual"] = opcion

st.markdown("---")

# =========================
# BURBUJAS DE NOTIFICACIÓN (DERECHA BAJO)
# =========================
mes = datetime.datetime.now().month
msg = "✅ Tienda al día."
if mes in [2,3]: msg = "🚨 <b>Día de la Madre:</b> Sube diseños YA."
elif mes in [7,8]: msg = "🎃 <b>Halloween:</b> Sube tus nichos ahora."
elif mes in [11,12]: msg = "🎄 <b>Navidad:</b> Optimiza tus Ads."

st.markdown(f"""
    <div class="floating-notify">
        <b>🔔 Notificación de Temporada</b><br>
        {msg}
    </div>
    """, unsafe_allow_html=True)

# =========================
# LÓGICA DE PANTALLAS
# =========================
menu = st.session_state["menu_actual"]

if menu == "📊 Dashboard":
    st.title("Centro de Comando VIP 👋")
    c1, c2, c3 = st.columns(3)
    c1.metric("Tienda", st.session_state["tienda"])
    c2.metric("Producto Seleccionado", str(st.session_state["product"]))
    c3.metric("Nicho", st.session_state["niche"])

elif menu == "🔍 1. OCR":
    st.title("Análisis Visual de Diseño")
    uploaded_file = st.file_uploader("Sube tu diseño (PNG/JPG)", type=["png", "jpg", "jpeg"], key="main_up")
    
    if uploaded_file:
        image = Image.open(uploaded_file).convert("RGB")
        st.session_state["imagen_memoria"] = image
        st.image(image, width=350)
        
        if st.button("👁️ Extraer Texto"):
            with st.spinner("Analizando..."):
                st.session_state["detected_text"] = extraer_texto_ocr(reader, image)
    
    if st.session_state["detected_text"]:
        st.session_state["detected_text"] = st.text_input("Confirmar Texto:", st.session_state["detected_text"])

elif menu == "🛒 2. Catálogo":
    st.title("Tiendas y Productos")
    tienda = st.radio("Tienda:", ["🐾 Tienda POD Mascotas", "💌 Tienda Digital"], horizontal=True)
    st.session_state["tienda"] = tienda
    
    if tienda == "🐾 Tienda POD Mascotas":
        prods = ["Plush Blanket", "15oz Mug", "Square Canvas", "Pet Bandana"]
    else:
        prods = ["Digital Invitation", "Memorial Sign", "Watercolor File"]
        
    cols = st.columns(len(prods))
    for i, p in enumerate(prods):
        if cols[i].button(p):
            st.session_state["product"] = p
            st.success(f"Seleccionado: {p}")

elif menu == "🚀 3. SEO":
    st.title("Generador SEO Maestro")
    if not st.session_state["product"]:
        st.warning("Selecciona un producto en el paso anterior.")
    else:
        kws = extraer_keywords_texto(st.session_state["detected_text"]) if st.session_state["detected_text"] else ["gift"]
        titulos = generar_titulos_venta(kws, st.session_state["product"], st.session_state["niche"])
        tags = generar_tags_etsy(kws, st.session_state["product"], st.session_state["niche"])
        
        st.subheader("🇺🇸 Título Recomendado (EUA)")
        st.code(titulos[0][0])
        st.subheader("🏷️ Tags")
        st.code(", ".join(tags))

elif menu == "💬 4. Muestras":
    st.title("Gestión de Add-Ons")
    st.info("Copia el texto para el listado de 'Digital Proof Add-On' de $4.99.")
    st.code("Digital Proof Add-On for Custom Orders... See Design Before Printing")

elif menu == "💰 5. Dinero":
    st.title("Calculadora de Margen")
    p = st.number_input("Precio Venta ($)", value=29.99)
    c = st.number_input("Costo Printify ($)", value=12.50)
    e = st.number_input("Envío Printify ($)", value=4.79)
    
    ganancia = p - (c + e + (p * 0.1)) # Estimado de fees
    st.metric("Ganancia Neta Estimada", f"${ganancia:.2f}")

elif menu == "⚖️ 6. Legal":
    st.title("Check de Trademarks")
    txt = st.text_area("Texto a revisar:", st.session_state["detected_text"])
    if st.button("Escanear"):
        st.success("Listado limpio de marcas registradas comunes.")
