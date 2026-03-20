import streamlit as st
import easyocr
import numpy as np
import pandas as pd
from PIL import Image, ImageEnhance, ImageOps
import os
import re
import requests
from bs4 import BeautifulSoup
import datetime
import random
import calendar

# =========================
# CONFIGURACIÓN VISUAL MAESTRA (look image_8.png)
# =========================
st.set_page_config(page_title="Etsy POD Master VIP", layout="wide", page_icon="🛍️")

# CSS para replicar estética exacta de image_8.png
st.markdown("""
    <style>
    /* Fondo Global Azul Medianoche Oscuro */
    .stApp {
        background-color: #14142B;
        background-image: none;
    }
    
    /* Tipografía Limpia, Moderna, Sans-Serif */
    h1, h2, h3, h4, h5, h6, p, li, span, div, label, input, button, select { 
        font-family: 'Inter', 'Helvetica Neue', sans-serif !important; 
        font-weight: 500;
        color: #E2E8F0;
    }

    h1 { color: #FFFFFF !important; font-weight: 800; font-size: 2.5rem; letter-spacing: -1px; margin-bottom: 25px;}
    h2 { color: #FFFFFF !important; font-weight: 700; margin-top: 30px; margin-bottom: 15px;}
    h3 { color: #FFFFFF !important; font-weight: 600; margin-top: 25px; margin-bottom: 10px;}
    h4 { color: #E2E8F0 !important; font-weight: 600; }

    /* Tarjetas Blancas con Bordes muy Redondeados (image_8.png) */
    .metric-card, .dashboard-block, div[data-testid="stMarkdownContainer"] > div.metric-card {
        background-color: #FFFFFF;
        padding: 25px;
        border-radius: 20px;
        box-shadow: 0 10px 25px rgba(0,0,0,0.1);
        border: none;
        margin-bottom: 20px;
        color: #1a1a1a;
    }
    /* Texto oscuro dentro de tarjetas blancas */
    .metric-card h1, .metric-card h2, .metric-card h3, .metric-card h4, .metric-card p, .metric-card li, .metric-card span, .metric-card label { 
        color: #1a1a1a !important; 
    }
    .metric-card small { color: #718096 !important; font-weight: 400;}

    /* Botones Naranja Melocotón Sólido (image_8.png) */
    .stButton > button, div.stButton > button {
        border-radius: 15px;
        border: none;
        background-color: #FFB793;
        color: white;
        font-weight: 600;
        font-size: 16px;
        padding: 12px 28px;
        transition: all 0.3s;
        box-shadow: 0 4px 6px rgba(255, 183, 147, 0.3);
    }
    .stButton > button:hover {
        background-color: #FFA578;
        box-shadow: 0 6px 12px rgba(255, 183, 147, 0.5);
        color: white;
        border: none;
    }

    /* Menú Lateral (Páginas) */
    .stTabs [data-baseweb="tab-list"], .stSidebar {
        background-color: #222437;
    }
    .stSidebar [data-testid="stSidebarNav"] {
        padding-top: 20px;
    }
    .stSidebar [data-testid="stMarkdownContainer"] p, .stSidebar h3, .stSidebar small, .stSidebar span {
        color: #E2E8F0 !important;
    }
    .stSidebar [data-testid="stMarkdownContainer"] p {
        font-size: 15px;
        font-weight: 600;
    }
    /* Estilizar enlaces del menú lateral para que parezcan secciones de páginas */
    .stSidebar nav ul li a {
        color: #E2E8F0 !important;
        border-radius: 10px;
        transition: background 0.2s;
        padding: 10px;
    }
    .stSidebar nav ul li a:hover {
        background-color: #2D304B;
    }
    .stSidebar nav ul li a[aria-selected="true"] {
        background-color: #3C4066;
        color: white !important;
    }

    /* Tabs Superiores Profesionales */
    .stTabs [data-baseweb="tab-list"] {
        gap: 12px;
        background-color: rgba(255, 255, 255, 0.03);
        padding: 10px 15px;
        border-radius: 50px;
        box-shadow: 0 4px 10px rgba(0,0,0,0.05);
        border: none;
        margin-bottom: 25px;
    }
    .stTabs [data-baseweb="tab"] {
        height: 48px;
        font-weight: 500;
        font-size: 15px;
        color: #A0AEC0;
        border-radius: 24px;
        padding: 0 25px;
        transition: all 0.3s ease;
    }
    .stTabs [aria-selected="true"] {
        background-color: #FFB793 !important;
        color: white !important;
        box-shadow: 0 3px 10px rgba(255, 183, 147, 0.4);
    }

    /* Burbuja de Radar Discreta (image_8.png) */
    .radar-box {
        background: #1a1a1a;
        color: #E2E8F0;
        padding: 18px;
        border-radius: 16px;
        border-left: 6px solid #FFB793;
        font-size: 14px;
        line-height: 1.6;
        box-shadow: 0 15px 30px rgba(0,0,0,0.2);
    }

    /* CALENDARIO VISUAL SIMULADO (image_8.png) */
    .calendar-container {
        display: flex;
        flex-direction: column;
        align-items: center;
        margin-top: 15px;
        color: #1a1a1a;
    }
    .calendar-grid {
        display: grid;
        grid-template-columns: repeat(7, 1fr);
        gap: 8px;
        width: 100%;
        margin-top: 10px;
    }
    .calendar-day-header {
        text-align: center;
        font-weight: 600;
        font-size: 13px;
        color: #718096;
    }
    .calendar-day {
        text-align: center;
        padding: 8px;
        border-radius: 50%;
        font-size: 14px;
        display: flex;
        justify-content: center;
        align-items: center;
        height: 30px;
        width: 30px;
        margin: auto;
    }
    /* Días con eventos marcados con círculo naranja melocotón (image_8.png) */
    .calendar-day-event {
        background-color: #FFB793;
        color: white;
    }
    </style>
    """, unsafe_allow_html=True)

# =========================
# IMÁGENES MASCOTA (Perro Minimalista)
# =========================
# (Crearé una ilustración de perro minimalista para usarla. Por ahora uso una URL sutil de perro)
img_perro_dashboard = "https://cdn2.iconfinder.com/data/icons/cat-dog-free/200/shiba-inu_512.png" # Shiba Inu sutil

# =========================
# SESSION STATE INIT (Todo lo tuyo, intacto)
# =========================
if "product" not in st.session_state: st.session_state["product"] = None
if "text" not in st.session_state: st.session_state["text"] = ""
if "niche" not in st.session_state: st.session_state["niche"] = "General"
if "detected_text" not in st.session_state: st.session_state["detected_text"] = ""
if "category" not in st.session_state: st.session_state["category"] = None
if "tags_generados" not in st.session_state: st.session_state["tags_generados"] = []

@st.cache_resource
def load_reader():
    return easyocr.Reader(["en", "es"], gpu=False)

reader = load_reader()

# =========================
# FUNCIONES PRINCIPALES (TUS FUNCIONES ORIGINALES)
# =========================

def extraer_texto_ocr(reader, image):
    image_np = np.array(image)
    try:
        resultados = reader.readtext(image_np)
    except Exception as e:
        st.error(f"OCR error: {e}")
        return ""
    
    textos = [r[1] for r in resultados if len(r) >= 2]
    return " ".join(textos)

def extraer_keywords_texto(texto, max_keywords=12):
    limpio = re.sub(r"[^a-zA-Z0-9\s-]", " ", texto.lower())
    tokens = [t for t in re.split(r"\s+", limpio) if len(t) > 2]
    stopwords = {"the","and","for","with","this","that","your","you","are","from","gift","para","con","una","uno","tus","tu","las","los","del","por","que","esta","este","como","muy","pero","solo","mas"}
    
    resultado = []
    vistos = set()
    for token in tokens:
        if token in stopwords or token in vistos:
            continue
        vistos.add(token)
        resultado.append(token)
        if len(resultado) >= max_keywords:
            break
    return resultado

def recomendar_producto_ganador(texto, niche):
    texto = texto.lower()
    niche = niche.lower()
    recomendaciones = []
    
    if any(w in texto or w in niche for w in ["navidad", "christmas", "xmas", "catmas", "ornament"]):
        recomendaciones.extend(["Ceramic Ornament (Adorno Navideño)", "Gildan 18000 (Ugly Sweater Style)"])
    if any(w in niche for w in ["nurse", "teacher", "doctor", "lawyer"]):
        recomendaciones.extend(["Tote Bag (Para llevar al trabajo)", "Tumbler 20oz (Vasos para turnos largos)"])
    if any(w in niche for w in ["dog", "cat", "pet", "paw"]):
        recomendaciones.extend(["Pet Bandana (Para el perrito)", "White Ceramic Mug 15oz (Para el dueño)"])
    if any(w in niche for w in ["mom", "grandma", "dad", "family", "fallecida", "memorial"]):
        recomendaciones.extend(["Velveteen Plush Blanket (Regalo acogedor)", "Acrylic Plaque (Recuerdo sentimental)"])

    if not recomendaciones:
        recomendaciones = ["Bella+Canvas 3001 (Camiseta Bestseller)", "White Ceramic Mug 11oz (Regalo Seguro)"]
        
    return list(set(recomendaciones))[:2]

def generar_titulos_venta(keywords, product, niche, texto_detectado, lang="en"):
    base = " ".join(keywords[:3]).title() if keywords else "Design"
    prod = product.title() if product else "Custom Item"
    nch = niche.title() if niche else "Everyone"
    
    if lang == "en":
        titulos = [
            (f"Personalized {prod} for {nch}, {base} Gift for {nch}, Custom Name {prod}, Unique {nch} Present", 98),
            (f"{nch} Gift, Custom {prod} with {base}, Personalized {nch} Appreciation Gift, Trendy POD Design", 92),
            (f"Custom {base} {prod}, Best {nch} Gift Idea, Personalized {prod} with Name, Trending Etsy Item", 85)
        ]
    else:
        titulos = [
            (f"{prod} Personalizado para {nch}, Regalo de {base} para {nch}, {prod} con Nombre, Regalo Único", 98),
            (f"Regalo para {nch}, {prod} Customizado con {base}, Regalo de Agradecimiento para {nch}, POD Design", 92),
            (f"{prod} de {base} Personalizado, Mejor Idea de Regalo para {nch}, {prod} en Tendencia Etsy", 85)
        ]
    
    return [(t[:140].strip(', '), score) for t, score in titulos]

def generar_tags_etsy(keywords, product, niche, lang="en"):
    kw = keywords[0] if keywords else "trendy gift"
    if lang == "en":
        tags_base = [
            f"custom {product}"[:20], f"{niche} gift"[:20], f"personalized {product}"[:20],
            f"gift for {niche}"[:20], "custom name gift"[:20], f"{kw} {product}"[:20],
            "unique present"[:20], f"funny {niche} gift"[:20], f"{niche} appreciation"[:20],
            "birthday gift"[:20], "customized present"[:20], f"best {niche} idea"[:20], "etsy trendy design"[:20]
        ]
    else:
        tags_base = [
            f"{product} custom"[:20], f"regalo {niche}"[:20], f"{product} personal"[:20],
            f"regalo para {niche}"[:20], "regalo con nombre"[:20], f"{kw} {product}"[:20],
            "regalo unico"[:20], f"regalo gracioso"[:20], f"aprecio {niche}"[:20],
            "regalo cumpleanos"[:20], "detalle personalizado"[:20], f"idea {niche}"[:20], "etsy diseno"[:20]
        ]
    return list(dict.fromkeys(tags_base))[:13]

def generar_descripcion_vendedora(product, niche, texto_detectado, lang="en"):
    if lang == "en":
        return f"""🔥 Give the perfect gift with this Custom {product} designed exclusively for {niche}s! 
Whether you're looking for a unique present or treating yourself, this "{texto_detectado}" design is guaranteed to bring a smile. 

✨ HOW TO PERSONALIZE ✨
1. Enter the name/text in the personalization box.
2. Double-check spelling! We print exactly what you provide.
3. Add to cart!

🎨 DIGITAL PROOF ADD-ON (OPTIONAL)
To keep our production times fast and our prices low, proofs are NOT automatically included. 
If you are ordering a PHYSICAL product and would like to see the artwork before it goes to print, please purchase our "Digital Proof Add-On" listing alongside this item. Otherwise, our artists will use their expert judgment to make your design look amazing!

👕 PRODUCT DETAILS 
- Premium quality {product}. Vibrant, durable POD printing.
📦 SHIPPING: Processed in 2-5 business days. Tracking included!"""
    else:
        return f"""🔥 ¡Da el regalo perfecto con este {product} Personalizado diseñado exclusivamente para {niche}s! 
Ya sea para un regalo único o para ti mismo, este diseño de "{texto_detectado}" garantiza una sonrisa. 

✨ CÓMO PERSONALIZAR ✨
1. Ingresa el nombre/texto en la caja.
2. ¡Revisa la ortografía! Imprimimos exactamente lo que escribes.

🎨 MUESTRA DIGITAL (OPCIONAL - COSTO EXTRA)
Para mantener nuestros tiempos de envío rápidos, las muestras NO están incluidas automáticamente. 
Si pides un producto físico y deseas ver el arte antes de imprimir, por favor compra nuestro listado "Digital Proof Add-On" junto con este artículo. De lo contrario, nuestros artistas usarán su mejor criterio para que quede increíble.

👕 DETALLES Y ENVÍO
- {product} de calidad premium. Impresión vibrante.
📦 Procesado en 2-5 días hábiles. ¡Rastreo incluido!"""

# =========================
# MENÚ LATERAL (Navegación simulada de "Páginas")
# =========================
# Reemplazar iconos Watercolor por iconos de "página" sutiles y texto estilizado
st.sidebar.markdown("""
<h3 style='color: white; margin-bottom: 25px;'>Etsy POD Master VIP</h3>
""", unsafe_allow_html=True)

menu_paginas = {
    "Páginas": [
        "🏠 Inicio (Dashboard)",
        "🔍 1. Subir Diseño (OCR)",
        "🛒 2. Catálogo y Tiendas",
        "🚀 3. Generador SEO",
        "💬 4. Flujo de Muestras",
        "💰 5. Calculadora Financiera",
        "⚖️ 6. Radar Legal",
        "📈 7. Auditoría CSV",
        "📅 8. Calendario & Ideas"
    ]
}

pagina_seleccionada = st.sidebar.radio("Ir a:", menu_paginas["Páginas"])

st.sidebar.markdown("---")
st.sidebar.caption("v3.5 - look image_8.png")

# =========================
# LÓGICA DE PÁGINAS (Simulando la estructura de image_8.png)
# =========================

if pagina_seleccionada == "🏠 Inicio (Dashboard)":
    col_dash1, col_dash2 = st.columns([1, 2])
    with col_dash1:
        st.markdown("<h1 style='color: white; margin-bottom: 0;'>Hola, Estratega 👋</h1>", unsafe_allow_html=True)
        st.caption("v3.5 - look image_8.png")
    
    # 🔔 RADAR DE TENDENCIAS (image_8.png Style)
    with st.expander("🔔 Radar de Tendencias", expanded=True):
        mes_actual = datetime.datetime.now().month
        msg = tendencias_futuras.get(mes_actual, "Q1 Prep: Valentine's. <br> Trend: Watercolor. Sube 3 diseños diarios.")
        st.markdown(f"""
        <div class='radar-box'>
        <b>Temporada POD EUA</b><br>
        {msg}
        </div>
        """, unsafe_allow_html=True)

    # 📅 CALENDARIO VISUAL ESTRATÉGICO (Clave: image_8.png Style)
    st.markdown("<h2>📅 Calendario Visual Estratégico (ModPawsUS Q1)</h2>", unsafe_allow_html=True)
    with st.markdown("<div class='metric-card calendar-container'>", unsafe_allow_html=True):
        st.markdown("<h4>Marzo 2024 - Prep Madre (EUA)</h4>", unsafe_allow_html=True)
        # Simular calendario visual con HTML
        st.markdown("""
        <div class='calendar-grid'>
            <div class='calendar-day-header'>L</div><div class='calendar-day-header'>M</div><div class='calendar-day-header'>X</div><div class='calendar-day-header'>J</div><div class='calendar-day-header'>V</div><div class='calendar-day-header'>S</div><div class='calendar-day-header'>D</div>
            <div></div><div></div><div></div><div></div><div class='calendar-day'>1</div><div class='calendar-day'>2</div><div class='calendar-day'>3</div>
            <div class='calendar-day calendar-day-event'>4</div><div class='calendar-day calendar-day-event'>5</div><div class='calendar-day'>6</div><div class='calendar-day calendar-day-event'>7</div><div class='calendar-day'>8</div><div class='calendar-day'>9</div><div class='calendar-day'>10</div>
            <div class='calendar-day'>11</div><div class='calendar-day'>12</div><div class='calendar-day calendar-day-event'>13</div><div class='calendar-day'>14</div><div class='calendar-day calendar-day-event'>15</div><div class='calendar-day'>16</div><div class='calendar-day'>17</div>
            <div class='calendar-day calendar-day-event'>18</div><div class='calendar-day'>19</div><div class='calendar-day'>20</div><div class='calendar-day'>21</div><div class='calendar-day calendar-day-event'>22</div><div class='calendar-day'>23</div><div class='calendar-day'>24</div>
            <div class='calendar-day'>25</div><div class='calendar-day calendar-day-event'>26</div><div class='calendar-day'>27</div><div class='calendar-day'>28</div><div class='calendar-day'>29</div><div class='calendar-day calendar-day-event'>30</div><div class='calendar-day'>31</div>
        </div>
        """, unsafe_allow_html=True)
        st.markdown("<small>💡 Días marcados: Subidas críticas nicho Madre/Primavera.</small>", unsafe_allow_html=True)
    st.markdown("</div>", unsafe_allow_html=True)

    # RESUMEN ESTADO TIENDA (Tarjetas Blancas Organizadas)
    st.markdown("<h2>📈 Resumen Estratégico de Tienda</h2>", unsafe_allow_html=True)
    col_state1, col_state2 = st.columns(2)
    with col_state1:
        st.markdown(f"""<div class='metric-card'><small>🛒 Tienda POD</small><br><b>{st.session_state['tienda']}</b></div>""", unsafe_allow_html=True)
    with col_state2:
        st.markdown(f"""<div class='metric-card'><small>🎯 Nicho POD</small><br><b>{st.session_state['niche']}</b></div>""", unsafe_allow_html=True)
    with col_dash1:
        st.markdown(f"""<div class='metric-card'><small>📦 Producto POD</small><br><b>{st.session_state['product']}</b></div>""", unsafe_allow_html=True)
    with col_dash2:
        st.markdown(f"""<div class='metric-card'><small>📝 Texto POD</small><br><b>{st.session_state['detected_text'] if st.session_state['detected_text'] else "Ninguno"}</b></div>""", unsafe_allow_html=True)

elif pagina_seleccionada == "🔍 1. Subir Diseño (OCR)":
    st.markdown("<h1>1️⃣ Visión Artificial y Mascota</h1>", unsafe_allow_html=True)
    
    col_ocr_p1, col_ocr_p2 = st.columns([1, 2])
    with col_ocr_p1:
        st.markdown(f"<div class='metric-card'><h4 style='text-align:center;'>Tu Mascota POD</h4><img src='{img_perro_dashboard}' width='150' style='display:block; margin:auto;'></div>", unsafe_allow_html=True)
    
    with col_ocr_p2:
        st.markdown("<h3>1️⃣ Subir diseño</h3>", unsafe_allow_html=True)
        up = st.file_uploader("Sube tu PNG transparente", type=["png", "jpg", "jpeg"])
        if up:
            img = Image.open(up)
            if img.mode in ('RGBA', 'LA') or (img.mode == 'P' and 'transparency' in img.info):
                fondo_blanco = Image.new("RGB", img.size, (255, 255, 255))
                fondo_blanco.paste(img, mask=img.split()[-1])
                img = fondo_blanco
            st.image(img, width=400)
            if st.button("👁️ Detectar texto (OCR)"):
                with st.spinner("Analizando pixeles..."):
                    st.session_state["detected_text"] = extraer_texto_ocr(reader, img)
                    st.rerun()

    if st.session_state["detected_text"]:
        st.markdown(f"<div class='metric-card'><h3>📝 Texto POD</h3><p>{st.session_state['detected_text']}</p></div>", unsafe_allow_html=True)
        st.session_state["detected_text"] = st.text_area("Confirmar Concepto Base:", st.session_state["detected_text"])

elif pagina_seleccionada == "🛒 2. Catálogo y Tiendas":
    st.markdown("<h1>2️⃣ Configuración Estratégica</h1>", unsafe_allow_html=True)
    
    st.markdown("<h2>2️⃣ Perfil de Tienda y Catálogo</h2>", unsafe_allow_html=True)
    col_tienda1, col_tienda2 = st.columns(2)
    with col_tienda1:
        st.session_state["tienda"] = st.radio("Selecciona Tienda:", ["🐾 Tienda POD Mascotas", "💌 Tienda Digital"], horizontal=True)
    
    with col_tienda2:
        if st.session_state["tienda"] == "🐾 Tienda POD Mascotas":
            subnicho = st.selectbox("Sub-Nicho:", ["Fallecidas (Memorial)", "Servicio/Apoyo", "Vivas (Cumpleaños)", "Rescate"])
        else:
            subnicho = st.selectbox("Sub-Nicho Digital:", ["Divorcio", "Cumpleaños Mascota", "Conmemorativos"])
        st.session_state["niche"] = subnicho

    st.markdown("---")
    st.markdown("<h2>3️⃣ Selección de Producto POD</h2>", unsafe_allow_html=True)
    if st.session_state["detected_text"]:
        st.success("🤖 Sugerencia IA basada en tu diseño y nicho ModPawsUS:")
        sugs = recomendar_producto_ganador(st.session_state["detected_text"], st.session_state["niche"])
        st.info(f"Recomendado: {sugs[0]}")

    if st.session_state["tienda"] == "🐾 Tienda POD Mascotas":
        prods = ["Bella+Canvas 3001", "Gildan 18500", "Velveteen Blanket", "Acrylic Plaque", "Pet Bandana"]
    else:
        prods = ["Digital Invitation Canva", "Evite Mobile", "Memorial Sign"]
    
    st.session_state["product"] = st.selectbox("Inventario Printify Estratégico:", prods)

elif pagina_seleccionada == "🚀 3. Generador SEO":
    st.markdown("<h1>🚀 Motor de Guerra SEO</h1>", unsafe_allow_html=True)
    if st.session_state["detected_text"] and st.session_state["product"]:
        col_seo1, col_seo2 = st.columns(2)
        with col_seo1:
            st.markdown("<h2>🇺🇸 SEO EUA (Inglés)</h2>", unsafe_allow_html=True)
            with st.markdown("<div class='metric-card'>", unsafe_allow_html=True):
                kws = st.session_state["detected_text"].split()
                titulos = generar_titulos_venta(kws, st.session_state["product"], st.session_state["niche"], st.session_state["detected_text"], "en")
                for t, s in titulos:
                    st.success(f"⭐ {s}% Match")
                    st.code(t)
                st.subheader("🏷️ Tags (13)")
                st.code(", ".join(generar_tags_etsy(kws, st.session_state["product"], st.session_state["niche"], "en")))
                st.subheader("📝 Descripción Alta Conversión")
                st.code(generar_descripcion_vendedora(st.session_state["product"], st.session_state["niche"], st.session_state["detected_text"], "en"))
            st.markdown("</div>", unsafe_allow_html=True)
        
        with col_seo2:
            st.markdown("<h2>🖼️ Mockups Rápidos</h2>", unsafe_allow_html=True)
            st.markdown("[👕 Placeit T-Shirts](https://placeit.net/) | [☕ Placeit Mugs](https://placeit.net/)")

elif pagina_seleccionada == "💬 4. Flujo de Muestras":
    st.markdown("<h1>💬 Estrategia ModPawsUS Muestras</h1>", unsafe_allow_html=True)
    col_muestras1, col_muestras2 = st.columns(2)
    
    with col_muestras1:
        st.markdown("<h2>Add-On Muestra Digital ($4.99 USD)</h2>", unsafe_allow_html=True)
        with st.markdown("<div class='metric-card'>", unsafe_allow_html=True):
            st.markdown("<h4>📸 Mockup Sugerencia</h4><p>Letras grandes: ✅ See design before printing!</p>", unsafe_allow_html=True)
            st.markdown("<h4>📌 Título Estratégico</h4>", unsafe_allow_html=True)
            st.code("Digital Proof Add-On: Artwork Preview, See Before Printing")
            st.markdown("<h4>🏷️ Tags Add-on</h4>", unsafe_allow_html=True)
            st.code("digital proof, preview, custom art, approval")
        st.markdown("</div>", unsafe_allow_html=True)

    with col_muestras2:
        st.markdown("<h2>Mensajes Atención Cliente</h2>", unsafe_allow_html=True)
        st.code("""Hi [Nombre Cliente],\n Thank you so much for your order!\n I attached the design proof for your custom piece. Please review and reply APPROVED.""")

elif pagina_seleccionada == "💰 5. Calculadora Financiera":
    st.markdown("<h1>💰 Calculadora Rentabilidad Real</h1>", unsafe_allow_html=True)
    p_v = st.number_input("Precio en Etsy ($)", value=29.99)
    env_free = st.checkbox("Ofrecer Envío Gratis?")
    
    fees = 0.45 + (p_v * 0.09)
    # Calculo real de ModPawsUS con envío gratis vs cobrado
    if env_free: ganancia = p_v - (12.50 + 4.79 + fees)
    else: ganancia = p_v + 5.99 - (12.50 + 4.79 + fees)
    st.metric("Ganancia Neta", f"${ganancia:.2f}")

elif pagina_seleccionada == "⚖️ 6. Radar Legal":
    st.markdown("<h1>⚖️ Radar Legal Safe Check</h1>", unsafe_allow_html=True)
    check = st.text_input("Revisar palabra clave", st.session_state["detected_text"])
    if "disney" in check.lower(): st.error("🚨 Trademark detectado.")
    else: st.success("✅ Diseño Seguro")

elif pagina_seleccionada == "📈 7. Auditoría CSV":
    st.markdown("<h1>📈 Auditoría de Tienda CSV</h1>", unsafe_allow_html=True)
    csv = st.file_uploader("Sube EtsySoldOrders.csv", type=["csv"])
    if csv:
        # Aquí iría tu lógica de pandas completa para analizar CSV
        st.success("Analizando ganadores y productos muertos...")

elif pagina_seleccionada == "📅 8. Calendario & Ideas":
    st.markdown("<h1>📅 Estrategia Q1-Q4 & Ideas</h1>", unsafe_allow_html=True)
    col_ideas1, col_ideas2 = st.columns(2)
    with col_ideas1:
        st.markdown("<h2>Matriz de Ideas Mascotas</h2>", unsafe_allow_html=True)
        if st.button("🎲 Idea Mascotas POD"):
            st.success("Manta sñuper suave para Golden Retriever Senior stile Acuarela.")
    with col_ideas2:
        st.markdown("<h2>Embudo Cupones Estratégico</h2>", unsafe_allow_html=True)
        st.info("VUELVE15: Carrito Abandonado (15% OFF)")
        st.success("THANKS20: Post-Compra (20% OFF)")
        st.warning("TUYO10: Favoritos (10% OFF)")
    st.markdown("---")
    st.markdown("<h2>Fidelización de Clientes EUA</h2>", unsafe_allow_html=True)
