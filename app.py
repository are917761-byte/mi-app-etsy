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

# =========================
# CONFIGURACIÓN VISUAL WATERCOLOR PREMIUM
# =========================
st.set_page_config(page_title="Etsy Master Pro", page_icon="🌸", layout="wide")

st.markdown("""
    <style>
    /* Fondo General Soft Watercolor */
    .stApp {
        background-color: #fffaf9;
        background-image: radial-gradient(#ffe4e1 0.8px, transparent 0.8px);
        background-size: 24px 24px;
    }
    
    /* Tipografía y Títulos Elegantes */
    h1, h2, h3 { 
        color: #4a4a4a; 
        font-family: 'Georgia', serif; 
        font-weight: 400;
        letter-spacing: 0.5px;
    }
    
    p, li, span, div {
        font-family: 'Helvetica Neue', sans-serif;
    }

    /* Tabs Superiores (Navegación que no estorba) */
    .stTabs [data-baseweb="tab-list"] {
        gap: 8px;
        background-color: rgba(255, 255, 255, 0.9);
        padding: 10px 15px;
        border-radius: 50px;
        box-shadow: 0 4px 15px rgba(0,0,0,0.03);
        margin-bottom: 20px;
    }
    .stTabs [data-baseweb="tab"] {
        height: 42px;
        font-weight: 500;
        font-size: 14px;
        color: #888;
        border-radius: 25px;
        padding: 0 20px;
        transition: all 0.3s ease;
    }
    .stTabs [aria-selected="true"] {
        background-color: #ffb6c1 !important;
        color: white !important;
        box-shadow: 0 2px 8px rgba(255, 182, 193, 0.4);
    }

    /* Burbuja de Radar Discreta y Elegante */
    .radar-box {
        background: #2d3436;
        color: white;
        padding: 15px;
        border-radius: 15px;
        border-left: 5px solid #ffb6c1;
        font-size: 13px;
        line-height: 1.5;
        box-shadow: 0 10px 20px rgba(0,0,0,0.1);
    }
    
    /* Ajuste para tarjetas y métricas */
    div[data-testid="metric-container"] {
        background-color: rgba(255,255,255,0.8);
        border: 1px solid #ffe4e1;
        padding: 15px;
        border-radius: 10px;
    }
    </style>
    """, unsafe_allow_html=True)

# =========================
# SESSION STATE INIT
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
# FUNCIONES PRINCIPALES (TU MOTOR INTACTO)
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
        if token in stopwords or token in vistos: continue
        vistos.add(token)
        resultado.append(token)
        if len(resultado) >= max_keywords: break
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
    if any(w in niche for w in ["mom", "grandma", "dad", "family"]):
        recomendaciones.extend(["Velveteen Plush Blanket (Regalo acogedor)", "Acrylic Plaque (Recuerdo sentimental)"])
    if any(w in niche for w in ["gym", "workout", "camping", "fishing"]):
        recomendaciones.extend(["Enamel Campfire Mug", "Tumbler 20oz"])
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
# INTERFAZ SUPERIOR: NOMBRE Y BURBUJA (WATERCOLOR)
# =========================
col_name, col_radar = st.columns([3, 1])

with col_name:
    st.markdown("<h2 style='margin:0;'>🌸 Etsy Master <span style='color:#ffb6c1;'>Watercolor Pro</span></h2>", unsafe_allow_html=True)
    st.caption("Estratega POD y Gestor de Flujos")

with col_radar:
    # Burbuja de Radar que puedes colapsar (cerrar) para que no estorbe
    with st.expander("🔔 Radar de Temporada", expanded=True):
        mes_actual = datetime.datetime.now().month
        if mes_actual in [2, 3]: msg = "Q2: Mother's Day & Spring.<br><i>Trend: Watercolor & Floral.</i>"
        elif mes_actual in [4, 5]: msg = "Q2: Father's Day & Grads.<br><i>Trend: Retro Wavy.</i>"
        elif mes_actual in [7, 8]: msg = "Q3: Halloween Prep.<br><i>Trend: Spooky Cute.</i>"
        else: msg = "Q4 Prep: Christmas & Q4.<br><i>Trend: Ugly Sweaters.</i>"
        
        st.markdown(f"""
        <div class='radar-box'>
        <b>Temporada Activa:</b><br>
        {msg}
        </div>
        """, unsafe_allow_html=True)

# =========================
# NAVEGACIÓN SUPERIOR (TABS)
# =========================
tab_ocr, tab_cat, tab_seo, tab_muestras, tab_dinero, tab_legal, tab_auditoria, tab_ideas = st.tabs([
    "🔍 1. Subir Diseño", 
    "🛒 2. Catálogo", 
    "🚀 3. SEO", 
    "💬 4. Muestras", 
    "💰 5. Dinero", 
    "⚖️ 6. Legal",
    "📈 7. Auditoría",
    "💡 8. Ideas"
])

# -----------------------------
# TAB 1: SUBIR DISEÑO (OCR)
# -----------------------------
with tab_ocr:
    st.header("1️⃣ Subir diseño para Análisis Visual")
    uploaded_file = st.file_uploader("Sube tu diseño transparente (PNG)", type=["png", "jpg", "jpeg"])

    if uploaded_file:
        image = Image.open(uploaded_file)
        if image.mode in ('RGBA', 'LA') or (image.mode == 'P' and 'transparency' in image.info):
            fondo_blanco = Image.new("RGB", image.size, (255, 255, 255))
            fondo_blanco.paste(image, mask=image.split()[-1])
            image = fondo_blanco
        else:
            image = image.convert("RGB")

        st.image(image, caption="Vista previa", width=300)

        if st.button("👁️ Detectar texto (OCR)"):
            with st.spinner("Analizando imagen..."):
                st.session_state["detected_text"] = extraer_texto_ocr(reader, image)
                st.rerun()

    if st.session_state["detected_text"]:
        st.subheader("Texto detectado")
        st.session_state["detected_text"] = st.text_area(
            "Edita el texto si el OCR cometió un error (Base de tu SEO):",
            st.session_state["detected_text"],
            height=80
        )
        st.
