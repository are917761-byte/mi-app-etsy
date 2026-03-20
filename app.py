import streamlit as st
import easyocr
import numpy as np
import pandas as pd
from PIL import Image, ImageEnhance, ImageOps
import os
import re
import requests
import json
from bs4 import BeautifulSoup
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

# =================================================================
# 3. TRADUCTORES Y LIMPIADORES SEO (ESTRATEGIA USA)
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
    if "sweatshirt" in p or "18000" in p: return "Custom Sweatshirt"
    if "bowl" in p or "plato" in p: return "Pet Bowl"
    if "tag" in p: return "Pet ID Tag"
    if "collar" in p: return "Pet Collar"
    if "bed" in p: return "Pet Bed"
    return "Custom Gift"

def limpiar_nicho_en(nicho):
    n = str(nicho).lower()
    if "fallecid" in n or "memorial" in n: return "Pet Memorial"
    if "servicio" in n or "apoyo" in n: return "Service Dog"
    if "rescate" in n or "adopci" in n: return "Pet Rescue"
    if "divorcio" in n: return "Divorce Party"
    if "cumplea" in n: return "Pet Birthday"
    if "despedida" in n: return "Bachelorette"
    if "maestra" in n or "teacher" in n: return "Teacher"
    if "enfermera" in n or "nurse" in n: return "Nurse"
    return "Pet Lover"

# =================================================================
# 4. INYECCIÓN DE DETALLES TÉCNICOS PRINTIFY (SOLUCIÓN DEFINITIVA)
# =================================================================
def obtener_detalles_printify(producto):
    p = str(producto).lower().strip()
    
    if "3001" in p or "t-shirt" in p or "shirt" in p:
        return "👕 ITEM SPECS (Bella+Canvas 3001):\n- 100% Airlume combed and ringspun cotton (ultra-soft!)\n- Light fabric (4.2 oz/yd²)\n- Retail fit & Tear away label\n- Runs true to size"
    elif "18000" in p or "18500" in p or "hoodie" in p or "sweatshirt" in p:
        return "🧥 ITEM SPECS (Premium Blend):\n- 50% cotton, 50% polyester\n- Medium-heavy fabric for cozy warmth\n- Classic fit & Tear-away label"
    elif "1717" in p or "comfort colors" in p:
        return "👕 ITEM SPECS (Comfort Colors 1717):\n- 100% ring-spun cotton\n- Heavy fabric (6.1 oz/yd²)\n- Relaxed fit, garment-dyed fabric"
    elif "mug" in p or "taza" in p:
        return "☕ ITEM SPECS (Ceramic Mug):\n- High-quality white ceramic\n- Lead and BPA-free\n- Microwave and dishwasher safe\n- Vibrant, fade-resistant wrap-around print"
    elif "bandana" in p:
        return "🐾 ITEM SPECS (Pet Bandana):\n- 100% soft spun polyester\n- Breathable, durable, and lightweight\n- One-sided vibrant print"
    elif "plaque" in p or "placa" in p:
        return "✨ ITEM SPECS (Acrylic Plaque):\n- Premium, crystal-clear acrylic (3mm thickness)\n- Vibrant, fade-resistant UV printing"
    elif "bowl" in p or "plato" in p:
        return "🥣 ITEM SPECS (Pet Bowl):\n- Double-wall stainless steel or ceramic options\n- Anti-slip rubber base\n- Dishwasher safe (top rack)"
    elif "blanket" in p or "cobija" in p or "manta" in p:
        return "🛌 ITEM SPECS (Velveteen Plush):\n- 100% Polyester for extreme, cozy softness\n- Machine washable (cold)"
    elif "tag" in p:
        return "🏷️ ITEM SPECS (Pet Tag):\n- Solid metal with white coating\n- Includes metal ring for easy collar attachment"
    elif "bed" in p:
        return "🛏️ ITEM SPECS (Pet Bed):\n- 100% polyester print area\n- Polyester filling for maximum comfort"
    else:
        return f"✨ ITEM SPECS PARA {str(producto).upper()}:\n- Premium quality materials\n- Vibrant and durable printing\n- Carefully crafted to order"

# =================================================================
# 5. MOTOR DE GENERACIÓN SEO (TÍTULOS, TAGS Y API EN TIEMPO REAL)
# =================================================================
def obtener_keywords_tiempo_real_etsy(keyword_semilla):
    kw_formateada = keyword_semilla.replace(" ", "+")
    url = f"https://www.etsy.com/ws/search/suggest?search_query={kw_formateada}&limit=11"
    headers = {
        'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36',
        'Accept': 'application/json'
    }
    try:
        response = requests.get(url, headers=headers, timeout=5)
        if response.status_code == 200:
            datos = response.json()
            sugerencias = [item.get('query', '') for item in datos.get('results', []) if 'query' in item]
            return [s for s in sugerencias if s]
        else:
            return []
    except Exception as e:
        return []

def generar_titulos_venta(keywords, product, niche, texto_detectado, lang="en"):
    prod_seo = limpiar_producto_en(product)
    nicho_seo = limpiar_nicho_en(niche)
    kw_oro = texto_detectado.title() if texto_detectado else "Custom Art"
    kw_extra = keywords[1].title() if len(keywords) > 1 else "Unique"

    if lang == "en":
        return [
            (f"Custom {kw_oro} {prod_seo} for {nicho_seo}, Personalized {nicho_seo} Gift, {kw_extra} Decor", 100),
            (f"Personalized {nicho_seo} {prod_seo}, {kw_oro} Gift Idea, Unique {prod_seo} for {nicho_seo}", 95),
            (f"{kw_oro} Style {prod_seo} Custom Name, {nicho_seo} Keepsake Present, {kw_extra} Artwork", 90)
        ]
    else:
        return [
            (f"{prod_seo} Personalizado {kw_oro} para {nicho_seo}, Regalo Único", 100),
            (f"Detalle Especial de {nicho_seo}, {prod_seo} con Diseño {kw_oro}", 92)
        ]

def generar_tags_etsy(keywords, product, niche, lang="en"):
    tags = []
    prod_seo = limpiar_producto_en(product).replace("Custom ", "").strip()
    nicho_base = limpiar_nicho_en(niche).replace("Pet ", "").strip()
    kw_oro = keywords[0][:15] if keywords else "Personalized"
    
    if lang == "en":
        raw_tags = [
            f"custom {prod_seo}", f"{nicho_base} gift", f"personalized {kw_oro}",
            "birthday present", "memorial keepsake", f"{nicho_base} lover",
            "made to order gift", f"unique {prod_seo}", "hand designed art",
            f"customized {nicho_base}", "pet loss sympathy", f"{kw_oro} artwork"
        ]
    else:
        raw_tags = [f"{prod_seo} custom", f"regalo {nicho_base}", f"{kw_oro} personal", "regalo unico", "hecho a medida"]

    for t in raw_tags:
        clean_t = " ".join(t.split()).lower()
        if len(clean_t) <= 20 and clean_t not in tags: tags.append(clean_t)
        if len(tags) == 13: break
    
    fillers = ["gift for her", "personalized gift", "custom order", "unique present"]
    for f in fillers:
        if len(tags) < 13 and f not in tags: tags.append(f)
    return tags[:13]

def generar_descripcion_vendedora(product, niche, texto_detectado, lang="en"):
    specs_reales = obtener_detalles_printify(product)
    prod_en = limpiar_producto_en(product)
    nicho_en = limpiar_nicho_en(niche)
    kw = texto_detectado if texto_detectado else "Custom Art"
    
    if lang == "en":
        desc = "✨ " + prod_en.upper() + " PERSONALIZED FOR " + nicho_en.upper() + " ✨\n\n"
        desc += 'Capture a special moment with our custom "' + kw + '" ' + prod_en + '. This is a personalized keepsake designed specifically for ' + nicho_en + ' lovers!\n\n'
        desc += "👇 PRODUCT DETAILS 👇\n"
        desc += specs_reales + "\n\n"
        desc += "🎨 HOW TO ORDER:\n1. Choose your options.\n2. Add details in the personalization box.\n3. Send your photo via Etsy Message!\n\n"
        desc += "📦 PRODUCTION & SHIPPING:\n- 2-5 business days production.\n- Tracked delivery."
        return desc
    else:
        desc = "🔥 ¡Da el regalo perfecto con este " + str(product).upper() + " Personalizado!\n\n"
        desc += "👇 DETALLES DEL PRODUCTO 👇\n"
        desc += specs_reales + "\n\n"
        desc += "📦 ENVÍO: 2-5 días hábiles con rastreo."
        return desc

# =================================================================
# 6. INTERFAZ DE USUARIO (TABS ESTRATÉGICAS)
# =================================================================
tab1, tab2, tab3, tab4, tab5 = st.tabs([
    "🎨 Diseño y Nicho", "🚀 SEO & Listado", "💰 Rentabilidad", "🚨 Legal & Radar", "📈 Auditoría & Ideas"
])

# --- TAB 1: PREPARACIÓN ---
with tab1:
    st.header("1️⃣ Subir diseño (OCR o Manual)")
    uploaded_file = st.file_uploader("Sube tu diseño transparente (PNG)", type=["png", "jpg", "jpeg"])

    if uploaded_file:
        image = Image.open(uploaded_file)
        if image.mode in ('RGBA', 'LA'):
            fondo_seguro = Image.new("RGB", image.size, (40, 40, 40))
            fondo_seguro.paste(image, mask=image.split()[-1])
            image_to_show = fondo_seguro
        else:
            image_to_show = image.convert("RGB")
        st.image(image_to_show, caption="Vista previa para análisis", width=300)

        st.subheader("📝 Definición del Concepto SEO")
        st.markdown("¿Qué dice el diseño? (Ej: 'Dog Mom', 'Retrato Acuarela'). Esto define tus keywords principales.")
        
        col_ocr1, col_ocr2 = st.columns(2)
        with col_ocr1:
            if st.button("👁️ Detectar texto (OCR)"):
                with st.spinner("Leyendo diseño..."):
                    st.session_state["detected_text"] = extraer_texto_ocr(reader, image_to_show)
                st.rerun()
        with col_ocr2:
            st.session_state["detected_text"] = st.text_input("Concepto Visual / Texto Manual:", value=st.session_state["detected_text"])

    st.header("2️⃣ Perfil de Tienda y Micro-Nicho")
    col_t1, col_t2 = st.columns(2)
    with col_t1:
        tienda = st.radio("Tienda:", ["🐾 Tienda POD Mascotas", "💌 Tienda Digital"])
    with col_t2:
        st.session_state["niche"] = st.selectbox("Sub-Nicho Estratégico:", [
            "Memorial (Mascotas Fallecidas)", "Mascotas de Servicio / Apoyo", "Cumpleaños Mascota (Paw-ty)", 
            "Rescate / Adopción (Gotcha Day)", "Divorcio / Soltería", "Boda / Aniversario", "Maestra / Profesiones"
        ])

    st.header("3️⃣ Selección de Producto Printify (Bestsellers)")
    productos_mascotas = [
        "Bella+Canvas 3001 (T-Shirt)", "Gildan 18000 (Crewneck)", "Gildan 18500 (Hoodie)", "Comfort Colors 1717",
        "White Ceramic Mug 11oz", "White Ceramic Mug 15oz", "Enamel Campfire Mug", "Pet Bandana", "Pet Bowl", 
        "Pet Bed", "Pet ID Tag", "Acrylic Plaque", "Velveteen Plush Blanket", "Canvas Gallery Wrap", "Tote Bag"
    ]
    cols_p = st.columns(3)
    for i, p in enumerate(productos_mascotas):
        with cols_p[i % 3]:
            if st.button(p): st.session_state["product"] = p
    
    if st.session_state["product"]: 
        st.success(f"📦 Producto Seleccionado: {st.session_state['product']}")

# --- TAB 2: SEO Y LISTADO ---
with tab2:
    if st.session_state["product"] and st.session_state["detected_text"]:
        
        # --- NUEVA SECCIÓN: API EN TIEMPO REAL ---
        st.markdown("### 🔍 Motor SEO en Tiempo Real (Estilo eRank)")
        st.markdown("Conéctate a la barra de búsqueda de Etsy para ver qué están tecleando los compradores HOY.")
        
        col_api1, col_api2 = st.columns([3, 1])
        with col_api1:
            kw_semilla = st.text_input("Semilla SEO (Keyword corta para investigar):", value=limpiar_producto_en(st.session_state["product"]))
        with col_api2:
            st.write("") # Espaciador
            st.write("")
            if st.button("🕵️‍♂️ Extraer Tags (Live)"):
                with st.spinner("Scrapeando Etsy..."):
                    st.session_state["live_tags"] = obtener_keywords_tiempo_real_etsy(kw_semilla)
        
        if st.session_state["live_tags"]:
            st.success("🔥 Keywords calientes extraídas directamente de Etsy:")
            st.code(", ".join(st.session_state["live_tags"][:13]))
        
        st.markdown("---")
        
        # --- GENERACIÓN TRADICIONAL / ESTRATÉGICA ---
        if st.button("🚀 GENERAR LISTADO COMPLETO (Títulos + Descripción)"):
            with st.spinner("Inyectando estrategia POD..."):
                base_kw = extraer_keywords_texto(st.session_state["detected_text"])
                
                t_en, t_es, t_msgs = st.tabs(["🇺🇸 Listado Inglés (Etsy USA)", "🇪🇸 Referencia Español", "💬 Mensajes Post-Venta"])
                
                with t_en:
                    st.subheader("📌 Títulos Dinámicos (Pirámide SEO)")
                    titulos = generar_titulos_venta(base_kw, st.session_state["product"], st.session_state["niche"], st.session_state["detected_text"], "en")
                    for t, s in titulos: st.success(f"Score {s}%: {t}")

                    st.subheader("🏷️ 13 Etiquetas Híbridas (Tus Reglas + Live API)")
                    tags_base = generar_tags_etsy(base_kw, st.session_state["product"], st.session_state["niche"], "en")
                    # Mezclamos tags programados con los de la API en tiempo real si existen
                    tags_finales = st.session_state["live_tags"][:6] + tags_base
                    # Limpiamos duplicados y cortamos a 13
                    tags_finales = list(dict.fromkeys([t for t in tags_finales if len(t) <= 20]))[:13]
                    
                    st.code(", ".join(tags_finales))

                    st.subheader("📝 Descripción con Inyección Printify")
                    st.code(generar_descripcion_vendedora(st.session_state["product"], st.session_state["niche"], st.session_state["detected_text"], "en"))

                with t_es:
                    st.write(generar_descripcion_vendedora(st.session_state["product"], st.session_state["niche"], st.session_state["detected_text"], "es"))

                with t_msgs:
                    st.subheader("💬 Comunicación con el Cliente")
                    st.info("Envío de Muestra (Proof):")
                    st.code(f"Hi! Attached is the proof for your custom {st.session_state['product']}. Please approve!")
                    st.info("Recordatorio de Aprobación:")
                    st.code("Friendly reminder! We need your approval to send your order to production.")

        st.markdown("---")
        with st.expander("🖼️ RECURSOS DE MOCKUPS Y PLACEIT"):
            col_m1, col_m2 = st.columns(2)
            with col_m1:
                st.write("[👕 Mockups de Camisetas](https://placeit.net/c/mockups/stages/t-shirt-mockup)")
                st.write("[☕ Mockups de Tazas](https://placeit.net/c/mockups/stages/mug-mockup)")
            with col_m2:
                st.write("[🐾 Mockups de Mascotas](https://placeit.net/c/mockups/stages/pet-bandana-mockup)")
                st.write("[🛌 Mockups de Cobijas](https://placeit.net/c/mockups/stages/blanket-mockup)")

    else:
        st.warning("⚠️ Primero detecta el texto del diseño y selecciona un producto en la Pestaña 1.")

# --- TAB 3: RENTABILIDAD ---
with tab3:
    st.header("💰 Calculadora de Rentabilidad Real")
    col_c1, col_c2 = st.columns(2)
    with col_c1:
        st.subheader("📦 Costos Printify")
        costo_p = st.number_input("Costo Producción $", value=12.50)
        envio_p = st.number_input("Costo Envío $", value=4.75)
    with col_c2:
        st.subheader("🛍️ Ingresos Etsy")
        precio_v = st.number_input("Precio de Venta $", value=29.99)
        envio_v = st.number_input("Envío Cobrado al Cliente $", value=0.0)
    
    if st.button("📊 Calcular Margen Neto"):
        ingreso_t = precio_v + envio_v
        fee_etsy = 0.45 + (ingreso_t * 0.095)
        total_costos = costo_p + envio_p + fee_etsy
        ganancia = ingreso_t - total_costos
        margen = (ganancia / ingreso_t) * 100
        
        col_res1, col_res2 = st.columns(2)
        col_res1.metric("Ganancia Neta", f"${ganancia:.2f}")
        col_res2.metric("Margen de Beneficio", f"{margen:.1f}%")
        
        if margen > 30: st.success("🔥 ¡Excelente margen! Producto apto para Etsy Ads.")
        elif margen > 15: st.warning("⚠️ Margen moderado. Ten cuidado con los descuentos.")
        else: st.error("🚨 Margen muy bajo. Sube el precio o cambia de proveedor.")

# --- TAB 4: LEGAL Y RADAR ---
with tab4:
    st.header("🚨 Radar de Trademarks y Protección")
    texto_para_escanear = st.text_area("Pega aquí tu título o etiquetas para buscar infracciones:")
    
    BLACKLIST = ["disney", "marvel", "nike", "star wars", "harry potter", "velcro", "onesie", "jeep", "taylor swift", "stanley", "snoopy", "mickey", "nfl", "nba", "barbie", "lego"]
    
    if st.button("🛡️ Escanear Listado"):
        hallazgos = [m.upper() for m in BLACKLIST if m in texto_para_escanear.lower()]
        if hallazgos:
            st.error(f"❌ PELIGRO: Se detectaron términos con Trademark: {', '.join(hallazgos)}")
        else:
            st.success("✅ ¡Listado Limpio! No se detectaron marcas registradas comunes.")

# --- TAB 5: AUDITORÍA E IDEAS ---
with tab5:
    st.header("🔮 Máquina de Ideas y Tendencias")
    
    col_i1, col_i2 = st.columns(2)
    with col_i1:
        st.subheader("📅 Calendario Estratégico")
        mes_actual = datetime.datetime.now().month
        mes_meta = (mes_actual + 2) % 12 or 12
        st.info(f"Estamos en el mes {mes_actual}. Tu enfoque actual debe ser: **Diseños para el mes {mes_meta}.**")
        
        if st.button("🎲 Generar Idea Ganadora"):
            conceptos = ["Acuarela", "Line Art", "Caricatura", "90s Bootleg"]
            nichos = ["Gato Ciego", "Perro de Tres Patas", "Maestra de Preescolar", "Novia en Despedida", "Abuela primeriza"]
            st.success(f"Prueba este nicho: **{random.choice(nichos)}** con un estilo **{random.choice(conceptos)}**.")

    with col_i2:
        st.subheader("📈 Auditoría CSV")
        up_csv = st.file_uploader("Sube tu archivo EtsySoldOrders.csv para ver qué se vende más:", type=["csv"])
        if up_csv:
            df_ventas = pd.read_csv(up_csv)
            st.write("Resumen de tus Top Ventas:")
            st.dataframe(df_ventas.head())

st.markdown("---")
st.caption("Etsy AI Listing Generator v3.0 | Módulo 'Live Search' Activado")
