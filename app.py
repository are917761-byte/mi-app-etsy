import streamlit as st
import easyocr
import numpy as np
import pandas as pd
from PIL import Image, ImageEnhance, ImageOps
import os
import re
import requests
import json
import datetime
import random

# =================================================================
# 1. CONFIGURACIÓN INICIAL Y ESTADO DE SESIÓN
# =================================================================
st.set_page_config(page_title="Etsy AI Listing Generator PRO", layout="wide", page_icon="🛍️")

# Estilo CSS para mejorar la interfaz
st.markdown("""
    <style>
    .main { background-color: #f5f7f9; }
    .stButton>button { width: 100%; border-radius: 5px; height: 3em; background-color: #ff5a1f; color: white; border: none; font-weight: bold;}
    .stTabs [data-baseweb="tab-list"] { gap: 24px; }
    .stTabs [data-baseweb="tab"] { height: 50px; white-space: pre-wrap; background-color: #f0f2f6; border-radius: 5px 5px 0px 0px; gap: 1px; }
    .stTabs [aria-selected="true"] { background-color: #ff5a1f !important; color: white !important; }
    </style>
    """, unsafe_allow_html=True)

st.title("🛍️ Etsy AI Listing Generator (Modo Estratega POD)")

# Inicialización de variables de estado
if "product" not in st.session_state: st.session_state["product"] = None
if "niche" not in st.session_state: st.session_state["niche"] = "General"
if "detected_text" not in st.session_state: st.session_state["detected_text"] = ""
if "tags_generados" not in st.session_state: st.session_state["tags_generados"] = []
if "live_tags" not in st.session_state: st.session_state["live_tags"] = []

@st.cache_resource
def load_reader():
    return easyocr.Reader(["en", "es"], gpu=False)

reader = load_reader()

# =================================================================
# 2. FUNCIONES DE PROCESAMIENTO (OCR Y KEYWORDS)
# =================================================================
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
    limpio = re.sub(r"[^a-zA-Z0-9\s-]", " ", str(texto).lower())
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

# =================================================================
# 3. TRADUCTORES Y LIMPIADORES SEO
# =================================================================
def limpiar_producto_en(producto):
    p = str(producto).lower()
    if "blanket" in p or "cobija" in p: return "Plush Blanket"
    if "mug" in p or "taza" in p: return "Coffee Mug"
    if "canvas" in p or "lienzo" in p: return "Canvas Art"
    if "bandana" in p: return "Pet Bandana"
    if "plaque" in p or "placa" in p: return "Acrylic Plaque"
    if "hoodie" in p: return "Custom Hoodie"
    if "3001" in p or "t-shirt" in p: return "Custom Shirt"
    if "18000" in p or "sweatshirt" in p: return "Custom Sweatshirt"
    if "bowl" in p or "plato" in p: return "Pet Bowl"
    if "tag" in p: return "Pet ID Tag"
    return "Custom Gift"

def limpiar_nicho_en(nicho):
    n = str(nicho).lower()
    if "fallecid" in n or "memorial" in n: return "Pet Memorial"
    if "servicio" in n or "apoyo" in n: return "Service Dog"
    if "rescate" in n or "adopci" in n: return "Pet Rescue"
    if "divorcio" in n: return "Divorce Party"
    if "cumplea" in n: return "Pet Birthday"
    return "Pet Lover"

# =================================================================
# 4. INYECCIÓN DE DETALLES TÉCNICOS PRINTIFY (VERSION BLINDADA)
# =================================================================
def obtener_detalles_printify(producto):
    p = str(producto).lower().strip()
    if "3001" in p or "t-shirt" in p:
        return "👕 ITEM SPECS (Bella+Canvas 3001):\n- 100% Airlume combed and ringspun cotton\n- Light fabric (4.2 oz/yd²)\n- Retail fit & Tear away label"
    elif "18000" in p or "18500" in p or "hoodie" in p or "sweatshirt" in p:
        return "🧥 ITEM SPECS (Premium Blend):\n- 50% cotton, 50% polyester\n- Medium-heavy fabric for cozy warmth\n- Classic fit & Tear-away label"
    elif "mug" in p or "taza" in p:
        return "☕ ITEM SPECS (Ceramic Mug):\n- High-quality white ceramic\n- Lead and BPA-free\n- Microwave and dishwasher safe"
    elif "bandana" in p:
        return "🐾 ITEM SPECS (Pet Bandana):\n- 100% soft spun polyester\n- Breathable, durable, and lightweight\n- One-sided vibrant print"
    elif "plaque" in p or "placa" in p:
        return "✨ ITEM SPECS (Acrylic Plaque):\n- Premium, crystal-clear acrylic (3mm)\n- Vibrant, fade-resistant UV printing"
    elif "blanket" in p or "cobija" in p:
        return "🛌 ITEM SPECS (Velveteen Plush):\n- 100% Polyester for extreme softness\n- Machine washable (cold)"
    elif "bowl" in p or "plato" in p:
        return "🥣 ITEM SPECS (Pet Bowl):\n- Double-wall stainless steel or ceramic\n- Anti-slip rubber base\n- Dishwasher safe"
    return "✨ ITEM SPECS:\n- Premium quality materials\n- Vibrant and durable printing\n- Carefully crafted to order"

# =================================================================
# 5. MOTOR SEO (LIVE API Y GENERACIÓN)
# =================================================================
def obtener_keywords_tiempo_real_etsy(keyword_semilla):
    kw_formateada = keyword_semilla.replace(" ", "+")
    url = f"https://www.etsy.com/ws/search/suggest?search_query={kw_formateada}&limit=11"
    headers = {'User-Agent': 'Mozilla/5.0'}
    try:
        response = requests.get(url, headers=headers, timeout=5)
        if response.status_code == 200:
            datos = response.json()
            return [item.get('query', '') for item in datos.get('results', [])]
        return []
    except:
        return []

def generar_titulos_venta(keywords, product, niche, texto_detectado, lang="en"):
    prod_seo = limpiar_producto_en(product)
    nicho_seo = limpiar_nicho_en(niche)
    kw_oro = texto_detectado.title() if texto_detectado else "Custom Art"
    kw_extra = keywords[1].title() if len(keywords) > 1 else "Unique"
    if lang == "en":
        return [
            (f"Custom {kw_oro} {prod_seo} for {nicho_seo}, Personalized {nicho_seo} Gift, {kw_extra} Decor", 100),
            (f"Personalized {nicho_seo} {prod_seo}, {kw_oro} Gift Idea, Unique {prod_seo} for {nicho_seo}", 95)
        ]
    return [(f"{prod_seo} Personalizado {kw_oro} para {nicho_seo}", 100)]

def generar_tags_etsy(keywords, product, niche, lang="en"):
    tags = []
    prod_seo = limpiar_producto_en(product).replace("Custom ", "").strip()
    nicho_base = limpiar_nicho_en(niche).replace("Pet ", "").strip()
    kw_oro = keywords[0][:15] if keywords else "Personalized"
    if lang == "en":
        raw_tags = [f"custom {prod_seo}", f"{nicho_base} gift", f"personalized {kw_oro}", "memorial keepsake", f"{nicho_base} lover"]
    else:
        raw_tags = [f"{prod_seo} custom", f"regalo {nicho_base}"]
    for t in raw_tags:
        clean_t = t.lower()
        if len(clean_t) <= 20 and clean_t not in tags: tags.append(clean_t)
    return tags

def generar_descripcion_vendedora(product, niche, texto_detectado, lang="en"):
    specs = obtener_detalles_printify(product)
    prod_en = limpiar_producto_en(product)
    nicho_en = limpiar_nicho_en(niche)
    kw = texto_detectado if texto_detectado else "Custom Art"
    if lang == "en":
        desc = f"✨ {prod_en.upper()} PERSONALIZED FOR {nicho_en.upper()} ✨\n\n"
        desc += f'Capture a special moment with our custom "{kw}" {prod_en}.\n\n'
        desc += f"👇 PRODUCT DETAILS 👇\n{specs}\n\n"
        desc += "📦 SHIPPING: 2-5 days production time."
        return desc
    return f"🔥 {product.upper()} PERSONALIZADO\n\n{specs}"

# =================================================================
# 6. INTERFAZ (TABS)
# =================================================================
tab1, tab2, tab3, tab4, tab5 = st.tabs(["🎨 Diseño", "🚀 SEO", "💰 Dinero", "🚨 Legal", "📈 Ideas"])

with tab1:
    st.header("1️⃣ Subir diseño")
    uploaded_file = st.file_uploader("Sube tu PNG", type=["png", "jpg"])
    if uploaded_file:
        img = Image.open(uploaded_file)
        st.image(img, width=300)
        if st.button("👁️ Leer texto"):
            st.session_state["detected_text"] = extraer_texto_ocr(reader, img)
            st.rerun()
        st.session_state["detected_text"] = st.text_input("Concepto:", value=st.session_state["detected_text"])
    
    st.header("2️⃣ Tienda y Producto")
    tienda = st.radio("Tienda:", ["🐾 Mascotas", "💌 Digital"])
    st.session_state["niche"] = st.selectbox("Nicho:", ["Memorial", "Cumpleaños", "Servicio", "Rescate"])
    
    productos = ["Bella+Canvas 3001", "Gildan 18000", "Pet Bandana", "Coffee Mug", "Acrylic Plaque", "Pet Bowl", "Plush Blanket"]
    cols_p = st.columns(3)
    for i, p in enumerate(productos):
        with cols_p[i % 3]:
            if st.button(p): st.session_state["product"] = p
    if st.session_state["product"]: st.success(f"Producto: {st.session_state['product']}")

with tab2:
    if st.session_state["product"] and st.session_state["detected_text"]:
        st.header("🔍 Live SEO")
        kw_semilla = st.text_input("Keyword semilla:", value=st.session_state["detected_text"])
        if st.button("🕵️‍♂️ Live Etsy Search"):
            st.session_state["live_tags"] = obtener_keywords_tiempo_real_etsy(kw_semilla)
        
        if st.session_state["live_tags"]:
            st.code(", ".join(st.session_state["live_tags"]))

        if st.button("🚀 GENERAR LISTADO COMPLETO"):
            kw_list = extraer_keywords_texto(st.session_state["detected_text"])
            t1, t2 = st.tabs(["🇺🇸 Inglés", "🇪🇸 Español"])
            with t1:
                titulos = generar_titulos_venta(kw_list, st.session_state["product"], st.session_state["niche"], st.session_state["detected_text"], "en")
                for t, s in titulos: st.success(t)
                st.code(generar_descripcion_vendedora(st.session_state["product"], st.session_state["niche"], st.session_state["detected_text"], "en"))
            with t2:
                st.write(generar_descripcion_vendedora(st.session_state["product"], st.session_state["niche"], st.session_state["detected_text"], "es"))
    else:
        st.warning("Faltan datos en la Pestaña 1")

with tab3:
    st.header("💰 Calculadora")
    cp = st.number_input("Costo Printify", value=12.0)
    pv = st.number_input("Precio Etsy", value=25.0)
    if st.button("Calcular"):
        ganancia = pv - cp - (pv * 0.15)
        st.metric("Ganancia", f"${ganancia:.2f}")

with tab4:
    st.header("🚨 Radar Legal")
    t_scan = st.text_area("Texto a escanear:")
    if st.button("Escanear"):
        if "disney" in t_scan.lower(): st.error("Marca detectada: Disney")
        else: st.success("Seguro")

with tab5:
    st.header("📈 Tendencias")
    st.write(f"Sube diseños para: {datetime.datetime.now().month + 2}")
    if st.button("Idea aleatoria"):
        st.info(f"Nicho: {random.choice(['Perro Ciego', 'Gato Senior'])} | Producto: {random.choice(['Taza', 'Manta'])}")
