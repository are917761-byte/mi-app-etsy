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
# CONFIGURACIÓN VISUAL PREMIUM (PROFESIONAL)
# =========================
st.set_page_config(page_title="Etsy Master Pro", page_icon="🛍️", layout="wide")

# CSS para diseño profesional y Burbuja de Radar
st.markdown("""
    <style>
    .stApp { background-color: #f8f9fa; }
    h1, h2, h3 { color: #1e1e1e; font-family: 'Inter', sans-serif; font-weight: 800; }
    
    /* Tarjetas del Dashboard */
    .metric-card {
        background-color: white;
        padding: 20px;
        border-radius: 12px;
        box-shadow: 0 4px 6px rgba(0,0,0,0.05);
        border: 1px solid #edf2f7;
        margin-bottom: 20px;
    }

    /* Notificación Flotante Estilo ModPaws */
    .floating-radar {
        position: fixed;
        bottom: 30px;
        right: 30px;
        width: 320px;
        background: #1a202c;
        color: white;
        padding: 20px;
        border-radius: 16px;
        box-shadow: 0 20px 25px -5px rgba(0,0,0,0.1);
        border-left: 6px solid #ff4b4b;
        z-index: 1000;
    }

    /* Tabs Profesionales arriba */
    .stTabs [data-baseweb="tab-list"] {
        gap: 24px;
        background-color: white;
        padding: 10px 20px;
        border-radius: 15px;
        box-shadow: 0 2px 4px rgba(0,0,0,0.05);
    }
    .stTabs [data-baseweb="tab"] {
        height: 50px;
        font-weight: 600;
        font-size: 16px;
        color: #718096;
    }
    .stTabs [aria-selected="true"] { color: #ff4b4b !important; border-bottom-color: #ff4b4b !important; }
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
# FUNCIONES ESTRATÉGICAS (EL MOTOR)
# =========================

def extraer_texto_ocr(reader, image):
    image_np = np.array(image)
    try:
        resultados = reader.readtext(image_np)
        return " ".join([r[1] for r in resultados if len(r) >= 2])
    except Exception as e:
        return ""

def extraer_keywords_texto(texto, max_keywords=12):
    limpio = re.sub(r"[^a-zA-Z0-9\s-]", " ", texto.lower())
    tokens = [t for t in re.split(r"\s+", limpio) if len(t) > 2]
    stopwords = {"the","and","for","with","this","that","your","you","are","from","gift","para","con","una","uno","tus","tu","las","los","del","por","que","esta","este","como","muy","pero","solo","mas"}
    resultado = []
    vistos = set()
    for token in tokens:
        if token in stopwords or token in vistos: continue
        vistos.add(token)
        resultado.append(token)
        if len(resultado) >= max_keywords: break
    return resultado

def recomendar_producto_ganador(texto, niche):
    texto, niche = texto.lower(), niche.lower()
    recomendaciones = []
    if any(w in texto or w in niche for w in ["navidad", "christmas", "xmas", "catmas", "ornament"]):
        recomendaciones.extend(["Ceramic Ornament", "Gildan 18000 Crewneck"])
    if any(w in niche for w in ["nurse", "teacher", "doctor"]):
        recomendaciones.extend(["Tote Bag", "Tumbler 20oz"])
    if any(w in niche for w in ["dog", "cat", "pet", "paw"]):
        recomendaciones.extend(["Pet Bandana", "White Ceramic Mug 15oz"])
    if any(w in niche for w in ["memorial", "fallecida", "remembrance"]):
        recomendaciones.extend(["Velveteen Plush Blanket", "Acrylic Plaque", "Square Canvas"])
    if not recomendaciones:
        recomendaciones = ["Bella+Canvas 3001", "White Ceramic Mug 11oz"]
    return list(set(recomendaciones))[:2]

def generar_titulos_venta(keywords, product, niche, lang="en"):
    base = " ".join(keywords[:3]).title() if keywords else "Custom"
    prod = product if product else "Product"
    nch = niche if niche else "Lover"
    if lang == "en":
        titulos = [
            (f"Personalized {prod} for {nch}, {base} Gift for {nch}, Custom Name {prod}, Unique {nch} Present", 98),
            (f"{nch} Gift, Custom {prod} with {base}, Personalized {nch} Appreciation Gift, Trendy POD Design", 92),
            (f"Custom {base} {prod}, Best {nch} Gift Idea, Personalized {prod} with Name, Trending Etsy Item", 85)
        ]
    else:
        titulos = [(f"{prod} Personalizado para {nch}, Regalo de {base}", 98)]
    return titulos

def generar_tags_etsy(keywords, product, niche, lang="en"):
    kw = keywords[0] if keywords else "trendy"
    if lang == "en":
        return [f"custom {product}"[:20], f"{niche} gift"[:20], "personalized"[:20], f"gift for {niche}"[:20], f"{kw} gift"[:20]][:13]
    return [f"regalo {product}"[:20], f"detalle {niche}"[:20]]

def generar_descripcion_vendedora(product, niche, texto_detectado, lang="en"):
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
# ESTRUCTURA DE NAVEGACIÓN (TABS)
# =========================
st.title("Etsy Master Pro")

tab_dash, tab_ocr, tab_cat, tab_seo, tab_muestras, tab_finanzas, tab_legal, tab_ideas = st.tabs([
    "🏠 Dashboard", "🔍 1. OCR", "🛒 2. Catálogo", "🚀 3. SEO", "💬 4. Muestras", "💰 5. Dinero", "⚖️ 6. Legal", "💡 7. Ideas"
])

# --- BURBUJA DE RADAR (SIEMPRE VISIBLE) ---
st.markdown(f"""
    <div class="floating-radar">
        <h4 style="margin:0; color:#ff4b4b;">🔔 Radar de Tendencias</h4>
        <p style="font-size:14px; margin-top:10px;">
            <b>Q1-Q2:</b> Mother's Day & Graduations.<br>
            <b>Style:</b> Watercolor & Retro Wavy.<br>
            <span style="color:#cbd5e0;">Tip: Sube 3 diseños diarios para indexar.</span>
        </p>
    </div>
    """, unsafe_allow_html=True)

# --- 1. DASHBOARD ---
with tab_dash:
    st.subheader("Estado de tu Negocio")
    c1, c2, c3 = st.columns(3)
    with c1: st.markdown(f'<div class="metric-card"><small>Tienda</small><br><b>{st.session_state["tienda"]}</b></div>', unsafe_allow_html=True)
    with c2: st.markdown(f'<div class="metric-card"><small>Producto</small><br><b>{st.session_state["product"]}</b></div>', unsafe_allow_html=True)
    with c3: st.markdown(f'<div class="metric-card"><small>Diseño</small><br><b>{st.session_state["detected_text"][:20] if st.session_state["detected_text"] else "Ninguno"}</b></div>', unsafe_allow_html=True)
    
    st.subheader("Tarjetas de Lealtad y Descuentos")
    col_l1, col_l2 = st.columns(2)
    with col_l1: st.success("🎫 **VUELVE15**: 15% OFF Carrito Abandonado\n\n🎫 **FAV10**: 10% OFF a Favoritos")
    with col_l2: st.info("🎫 **THANKS20**: Cupón físico en paquete\n\n🎫 **VIP25**: Clientes recurrentes")

# --- 2. OCR ---
with tab_ocr:
    st.header("Analizar Diseño")
    uploaded_file = st.file_uploader("Sube tu PNG transparente", type=["png", "jpg", "jpeg"], key="main_up")
    if uploaded_file:
        image = Image.open(uploaded_file)
        # Procesar transparencia
        if image.mode in ('RGBA', 'LA') or (image.mode == 'P' and 'transparency' in image.info):
            fondo_blanco = Image.new("RGB", image.size, (255, 255, 255))
            fondo_blanco.paste(image, mask=image.split()[-1])
            image = fondo_blanco
        st.session_state["imagen_memoria"] = image
        st.image(image, width=350)
        if st.button("👁️ Leer Texto del Diseño"):
            with st.spinner("Analizando..."):
                st.session_state["detected_text"] = extraer_texto_ocr(reader, image)
    
    if st.session_state["detected_text"]:
        st.session_state["detected_text"] = st.text_input("Editar texto detectado:", st.session_state["detected_text"])

# --- 3. CATÁLOGO ---
with tab_cat:
    st.header("Perfil y Productos")
    tienda = st.radio("Selecciona Tienda:", ["🐾 Tienda POD Mascotas", "💌 Tienda Digital"], horizontal=True)
    st.session_state["tienda"] = tienda
    
    col1, col2 = st.columns(2)
    with col1:
        if tienda == "🐾 Tienda POD Mascotas":
            niche = st.selectbox("Sub-Nicho:", ["Fallecidas", "Apoyo/Servicio", "Vivas", "Rescate"])
        else:
            niche = st.selectbox("Sub-Nicho:", ["Divorcio/Soltería", "Cumpleaños Mascota", "Conmemorativos"])
        st.session_state["niche"] = niche

    st.markdown("---")
    if st.session_state["detected_text"]:
        st.success("🤖 **Sugerencia IA:**")
        sugs = recomendar_producto_ganador(st.session_state["detected_text"], st.session_state["niche"])
        for s in sugs: st.write(f"🔥 {s}")

    prods = ["Bella+Canvas 3001", "Gildan 18500", "Velveteen Blanket", "Acrylic Plaque", "Pet Bandana"] if tienda == "🐾 Tienda POD Mascotas" else ["Digital Invitation", "Mobile Evite", "Memorial Sign"]
    
    cols = st.columns(len(prods))
    for i, p in enumerate(prods):
        if cols[i].button(p):
            st.session_state["product"] = p
            st.balloons()

# --- 4. SEO ---
with tab_seo:
    st.header("Generador SEO con Porcentajes")
    if st.session_state["product"] and st.session_state["detected_text"]:
        kws = extraer_keywords_texto(st.session_state["detected_text"])
        titulos = generar_titulos_venta(kws, st.session_state["product"], st.session_state["niche"], "en")
        
        for t, s in titulos:
            if s > 95: st.success(f"⭐ **{s}% MATCH (Recomendado):**\n{t}")
            else: st.info(f"🔥 **{s}% MATCH:**\n{t}")
        
        st.subheader("🏷️ 13 Etiquetas (Inglés)")
        st.code(", ".join(generar_tags_etsy(kws, st.session_state["product"], st.session_state["niche"], "en")))
        
        st.subheader("📝 Descripción de Alta Conversión")
        st.code(generar_descripcion_vendedora(st.session_state["product"], st.session_state["niche"], st.session_state["detected_text"], "en"))
    else:
        st.warning("Falta diseño o producto.")

# --- 5. MUESTRAS ---
with tab_muestras:
    st.header("Estrategia de Muestras (Add-On)")
    st.warning("⚠️ Monetiza tu tiempo como ModPawsUS: Las muestras se pagan aparte.")
    st.subheader("Configuración del Listado Add-On ($4.99)")
    st.code("Digital Proof Add-On for Custom Orders, See Design Before Printing")
    st.markdown("**Descripción sugerida:** Purchase this listing IN ADDITION to your physical product if you wish to see a digital preview...")

# --- 6. FINANZAS ---
with tab_finanzas:
    st.header("Calculadora de Rentabilidad Híbrida")
    c_p = st.number_input("Costo Printify ($)", value=12.50)
    e_p = st.number_input("Envío Printify ($)", value=4.79)
    p_v = st.number_input("Precio Venta ($)", value=29.99)
    env_free = st.checkbox("Ofrecer Envío Gratis (Súmalo al precio)")
    
    total = p_v if env_free else p_v + 5.99
    fees = 0.45 + (total * 0.095)
    ganancia = total - (c_p + e_p + fees)
    st.metric("Ganancia Neta", f"${ganancia:.2f}")

# --- 7. LEGAL ---
with tab_legal:
    st.header("Radar Legal")
    check = st.text_input("Revisar palabra:", st.session_state["detected_text"])
    if "disney" in check.lower(): st.error("🚨 Trademark detectado.")
    else: st.success("✅ Diseño Seguro")

# --- 8. IDEAS ---
with tab_ideas:
    st.header("Máquina de Ideas y Tendencias")
    if st.button("🎲 Generar Idea"):
        n = random.choice(["Gato Ciego", "Perro de Terapia", "Mascota Fallecida"])
        st.success(f"Crea una **Acuarela Digital** de un **{n}** en un **Lienzo Cuadrado**.")
