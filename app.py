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
# 1. CONFIGURACIÓN INICIAL Y ESTILO DE INTERFAZ
# =================================================================
st.set_page_config(page_title="Etsy AI Listing Generator PRO", layout="wide", page_icon="🛍️")

# Estilo CSS para una experiencia de usuario premium (Modo Estratega)
st.markdown("""
    <style>
    .main { background-color: #f5f7f9; }
    .stButton>button { 
        width: 100%; 
        border-radius: 8px; 
        height: 3.5em; 
        background-color: #ff5a1f; 
        color: white; 
        border: none; 
        font-weight: bold; 
        font-size: 16px;
        transition: 0.3s;
    }
    .stButton>button:hover { background-color: #e04e1a; transform: scale(1.01); }
    .stTabs [data-baseweb="tab-list"] { gap: 10px; }
    .stTabs [data-baseweb="tab"] { 
        height: 50px; 
        background-color: #f0f2f6; 
        border-radius: 5px 5px 0px 0px; 
        padding: 10px 20px; 
    }
    .stTabs [aria-selected="true"] { background-color: #ff5a1f !important; color: white !important; }
    div[data-testid="stMetricValue"] { font-size: 24px; color: #ff5a1f; }
    </style>
    """, unsafe_allow_html=True)

st.title("🛍️ Etsy AI Listing Generator (Modo Estratega POD)")

# =================================================================
# 2. SESSION STATE (MEMORIA OPERATIVA)
# =================================================================
if "product" not in st.session_state: st.session_state["product"] = None
if "niche" not in st.session_state: st.session_state["niche"] = "General"
if "detected_text" not in st.session_state: st.session_state["detected_text"] = ""
if "live_tags" not in st.session_state: st.session_state["live_tags"] = []
if "final_tags" not in st.session_state: st.session_state["final_tags"] = []

@st.cache_resource
def load_reader():
    return easyocr.Reader(["en", "es"], gpu=False)

reader = load_reader()

# =================================================================
# 3. FUNCIONES DE PROCESAMIENTO (OCR Y KEYWORDS)
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
# 4. LIMPIADORES SEO (ESTRATEGIA MERCADO USA)
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
    if "sticker" in p: return "Die-Cut Sticker"
    if "tote" in p: return "Tote Bag"
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
# 5. BASE DE DATOS PRINTIFY (DETALLES TÉCNICOS COMPLETOS)
# =================================================================
def obtener_detalles_printify(producto):
    p = str(producto).lower().strip()
    
    if "3001" in p or "t-shirt" in p or "camiseta" in p:
        return "👕 ITEM SPECS (Bella+Canvas 3001):\n- 100% Airlume combed and ringspun cotton (ultra-soft!)\n- Light fabric (4.2 oz/yd²)\n- Retail fit & Tear away label\n- Runs true to size"
    elif "18000" in p or "18500" in p or "hoodie" in p or "sweatshirt" in p or "sudadera" in p:
        return "🧥 ITEM SPECS (Premium Blend):\n- 50% cotton, 50% polyester\n- Medium-heavy fabric for cozy warmth\n- Classic fit & Tear-away label\n- High-quality DTG printing"
    elif "1717" in p or "comfort colors" in p:
        return "👕 ITEM SPECS (Comfort Colors 1717):\n- 100% ring-spun cotton (Heavyweight)\n- Relaxed fit, garment-dyed fabric\n- Double-needle armhole, sleeve and bottom hems"
    elif "mug" in p or "taza" in p:
        return "☕ ITEM SPECS (Ceramic Mug):\n- High-quality white ceramic\n- Lead and BPA-free\n- Microwave and dishwasher safe\n- Vibrant, fade-resistant wrap-around print"
    elif "bandana" in p:
        return "🐾 ITEM SPECS (Pet Bandana):\n- 100% soft spun polyester\n- Breathable, durable, and lightweight\n- One-sided vibrant print\n- Hemmed edges for extra durability"
    elif "plaque" in p or "placa" in p:
        return "✨ ITEM SPECS (Acrylic Plaque):\n- Premium, crystal-clear acrylic (3mm thickness)\n- Vibrant, fade-resistant UV printing\n- Sleek wooden base (if selected)\n- Perfect for memorial or desk display"
    elif "bowl" in p or "plato" in p:
        return "🥣 ITEM SPECS (Pet Bowl):\n- Double-wall stainless steel (Steel) or Heavy Ceramic\n- Anti-slip rubber base (Steel version)\n- Dishwasher safe (top rack)\n- Large capacity for food or water"
    elif "blanket" in p or "cobija" in p or "manta" in p:
        return "🛌 ITEM SPECS (Velveteen Plush):\n- 100% Polyester for extreme, cozy softness\n- Double needle topstitch on all seams\n- Vibrant, high-detail one-sided print\n- Machine washable (cold)"
    elif "tag" in p:
        return "🏷️ ITEM SPECS (Pet ID Tag):\n- Solid metal with white coating\n- Includes metal ring for easy collar attachment\n- Double-sided custom printing\n- Durable and scratch resistant"
    elif "bed" in p:
        return "🛏️ ITEM SPECS (Pet Bed):\n- 100% polyester print area\n- Dark brown fleece back\n- Polyester filling for maximum comfort\n- Concealed zipper for easy cleaning"
    elif "sticker" in p:
        return "✨ ITEM SPECS (Die-Cut Stickers):\n- Premium vinyl with glossy finish\n- Water-resistant and durable\n- Easy-peel backing"
    elif "tote" in p:
        return "👜 ITEM SPECS (Tote Bag):\n- 100% Cotton canvas\n- Reinforced stitching on handles\n- Large printable area for vibrant designs"
    return "✨ ITEM SPECS:\n- Premium quality materials\n- Vibrant and durable printing\n- Carefully crafted to order just for you"

# =================================================================
# 6. MOTOR SEO (LIVE API Y GENERACIÓN ESTRATÉGICA)
# =================================================================
def obtener_keywords_live_etsy(keyword):
    """Investiga tendencias reales en la barra de búsqueda de Etsy."""
    if not keyword: return []
    kw_url = keyword.replace(" ", "+")
    url = f"https://www.etsy.com/ws/search/suggest?search_query={kw_url}&limit=12"
    headers = {'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36'}
    try:
        r = requests.get(url, headers=headers, timeout=5)
        if r.status_code == 200:
            datos = r.json()
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
            (f"Personalized {nicho_seo} {prod_seo}, {kw_oro} Gift Idea, Unique {prod_seo} for {nicho_seo}", 95),
            (f"{kw_oro} Style {prod_seo} Custom Name, {nicho_seo} Keepsake Present, {kw_extra} Artwork", 90)
        ]
    else:
        return [(f"{prod_seo} Personalizado {kw_oro} para {nicho_seo}, Regalo Único", 100)]

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
        raw_tags = [f"{prod_seo} custom", f"regalo {nicho_base}", f"{kw_oro} personal", "regalo unico"]

    for t in raw_tags:
        clean_t = str(t).lower().strip()
        if len(clean_t) <= 20 and clean_t not in tags: tags.append(clean_t)
        if len(tags) == 13: break
    
    fillers = ["gift for her", "personalized gift", "custom order", "unique present"]
    for f in fillers:
        if len(tags) < 13 and f not in tags: tags.append(f)
    return tags[:13]

def generar_descripcion_vendedora(product, niche, texto_detectado, lang="en"):
    specs = obtener_detalles_printify(product)
    prod_en = limpiar_producto_en(product)
    nicho_en = limpiar_nicho_en(niche)
    kw = texto_detectado if texto_detectado else "Custom Art"
    
    if lang == "en":
        return f"""✨ {prod_en.upper()} PERSONALIZED FOR {nicho_en.upper()} ✨

Capture a special moment with our custom "{kw}" {prod_en}. This isn't just a product; it's a personalized keepsake designed specifically for {nicho_en} lovers!

{specs}

🎨 HOW TO ORDER:
1. Choose your options and add your personalization details in the box.
2. For photo-based designs, please send your high-resolution image via Etsy Message after checkout.
3. Our artists will handle the rest!

📦 PRODUCTION & SHIPPING:
- Production time: 2-5 business days.
- Shipping: Tracked delivery straight to your door.
- Tracking number provided for every physical order.

Note: Since this is a custom item, we only accept returns for damaged products. Thanks for supporting our small business!

🤍 Explore more custom designs in our shop: [Insert Your Shop Link Here]"""
    else:
        return f"""✨ {product.upper()} PERSONALIZADO ✨

{specs}

✅ CÓMO ORDENAR:
1. Añade los detalles en la caja de personalización.
2. Envía tu foto por mensaje de Etsy (si aplica).
3. ¡Nosotros diseñamos y enviamos!"""

# =================================================================
# 7. INTERFAZ DE USUARIO (EL WORKFLOW MAESTRO)
# =================================================================
tab1, tab2, tab3, tab4, tab5 = st.tabs([
    "🎨 1. Diseño y Nicho", "🚀 2. SEO Live & Listado", "💰 3. Rentabilidad", "🚨 4. Legal & Radar", "📈 5. Ideas y Auditoría"
])

# --- TAB 1: PREPARACIÓN ---
with tab1:
    st.header("1️⃣ Preparación del Producto")
    col_u1, col_u2 = st.columns([1, 2])
    
    with col_u1:
        st.subheader("Subir Diseño")
        uploaded_file = st.file_uploader("Sube tu PNG transparente", type=["png", "jpg", "jpeg"])
        if uploaded_file:
            image = Image.open(uploaded_file)
            # Fix para OCR con fondos transparentes
            if image.mode in ('RGBA', 'LA'):
                bg = Image.new("RGB", image.size, (40, 40, 40))
                bg.paste(image, mask=image.split()[-1])
                image_show = bg
            else:
                image_show = image.convert("RGB")
            
            st.image(image_show, caption="Vista previa de análisis", width=300)
            if st.button("👁️ Detectar Texto del Diseño"):
                with st.spinner("Escaneando diseño..."):
                    st.session_state["detected_text"] = extraer_texto_ocr(reader, image_show)
                st.rerun()

    with col_u2:
        st.subheader("Configuración del Listado")
        st.session_state["detected_text"] = st.text_input("Concepto / Frase del Diseño (Keyword de Oro):", value=st.session_state["detected_text"])
        
        col_st1, col_st2 = st.columns(2)
        with col_st1:
            tienda = st.radio("Perfil de Tienda:", ["🐾 Mascotas (POD)", "💌 Digital / Regalos"])
        with col_st2:
            st.session_state["niche"] = st.selectbox("Sub-Nicho Estratégico:", [
                "Memorial (Mascotas Fallecidas)", "Mascotas de Servicio", "Cumpleaños", "Rescate / Adopción", "Profesiones / Trabajo", "Boda / Aniversario"
            ])

        st.subheader("Catálogo de Productos Printify")
        if tienda == "🐾 Mascotas (POD)":
            catalog = [
                "Bella+Canvas 3001 (T-Shirt)", "Gildan 18000 (Crewneck)", "Gildan 18500 (Hoodie)", "Comfort Colors 1717",
                "White Ceramic Mug 11oz", "White Ceramic Mug 15oz", "Pet Bandana", "Pet Bowl", "Pet Bed", "Pet ID Tag",
                "Acrylic Plaque", "Velveteen Plush Blanket", "Canvas Gallery Wrap", "Tote Bag", "Die-Cut Stickers"
            ]
        else:
            catalog = ["Digital Invitation", "Mobile Evite", "Printable Sign", "Digital Portrait", "Printable Planner"]
        
        # Grid de botones de producto
        cols_p = st.columns(3)
        for i, p in enumerate(catalog):
            with cols_p[i % 3]:
                if st.button(p, key=f"btn_{p}"): 
                    st.session_state["product"] = p
        
        if st.session_state["product"]:
            st.success(f"📦 Producto Activo: {st.session_state['product']}")

# --- TAB 2: SEO Y GENERACIÓN ---
with tab2:
    if st.session_state["product"] and st.session_state["detected_text"]:
        st.header("🔍 Motor SEO Live (Estilo eRank / Everbee)")
        st.markdown("Investiga lo que los compradores reales están tecleando en Etsy en este momento.")
        
        col_api1, col_api2 = st.columns([3, 1])
        with col_api1:
            semilla = st.text_input("Investigar tendencia (ej: 'dog memorial'):", value=st.session_state["detected_text"])
        with col_api2:
            st.write("")
            st.write("")
            if st.button("🕵️‍♂️ Extraer Tags Live"):
                with st.spinner("Consultando Etsy..."):
                    st.session_state["live_tags"] = obtener_keywords_live_etsy(semilla)
        
        if st.session_state["live_tags"]:
            st.success("🔥 Keywords en tendencia hoy:")
            st.code(", ".join(st.session_state["live_tags"]))

        st.markdown("---")
        
        if st.button("🚀 GENERAR LISTADO OPTIMIZADO"):
            with st.spinner("Aplicando ingeniería inversa de tiendas TOP..."):
                base_kw = extraer_keywords_texto(st.session_state["detected_text"])
                
                t_en, t_es, t_help = st.tabs(["🇺🇸 Listado Inglés (Etsy USA)", "🇪🇸 Referencia Español", "💬 Guía de Comunicación"])
                
                with t_en:
                    st.subheader("📌 Títulos Pirámide (Copia el mejor)")
                    titulos = generar_titulos_venta(base_kw, st.session_state["product"], st.session_state["niche"], st.session_state["detected_text"], "en")
                    for t, s in titulos: st.success(f"Score {s}%: {t}")

                    st.subheader("🏷️ 13 Etiquetas (Mezcla Live + Estratégica)")
                    tags_base = generar_tags_etsy(base_kw, st.session_state["product"], st.session_state["niche"], "en")
                    tags_finales = list(dict.fromkeys(st.session_state["live_tags"][:6] + tags_base))[:13]
                    st.code(", ".join([t[:20] for t in tags_finales]))

                    st.subheader("📝 Descripción con Inyección Printify")
                    full_desc = generar_descripcion_vendedora(st.session_state["product"], st.session_state["niche"], st.session_state["detected_text"], "en")
                    st.code(full_desc, language="text")

                with t_es:
                    st.write(generar_descripcion_vendedora(st.session_state["product"], st.session_state["niche"], st.session_state["detected_text"], "es"))

                with t_help:
                    st.subheader("💬 Mensajes para el Cliente")
                    st.info("Mensaje de Envío de Muestra (Proof):")
                    st.code(f"Hi! Attached is the proof for your custom {st.session_state['product']}. Please approve!")
                    st.info("Mensaje de Recordatorio:")
                    st.code("Friendly reminder! Please confirm the design so we can ship on time.")
    else:
        st.warning("⚠️ Completa los pasos en la Pestaña 1 (Diseño + Producto).")

# --- TAB 3: RENTABILIDAD ---
with tab3:
    st.header("💰 Calculadora de Rentabilidad POD")
    col_c1, col_c2 = st.columns(2)
    with col_c1:
        st.subheader("📦 Costos Printify")
        costo_p = st.number_input("Costo Producción $", value=12.50, step=0.5)
        envio_p = st.number_input("Costo Envío $", value=4.75, step=0.5)
    with col_c2:
        st.subheader("🛍️ Ingresos Etsy")
        precio_v = st.number_input("Precio de Venta $", value=29.99, step=0.5)
        envio_v = st.number_input("Envío Cobrado $", value=0.0, step=0.5)
    
    if st.button("📊 Calcular Ganancia"):
        ingreso = precio_v + envio_v
        fee_etsy = 0.45 + (ingreso * 0.09)
        neta = ingreso - (costo_p + envio_p + fee_etsy)
        margen = (neta / ingreso) * 100
        
        st.metric("Ganancia Neta", f"${neta:.2f}", f"{margen:.1f}% Margen")
        if margen > 30: st.success("🔥 ¡Margen excelente! Apto para Etsy Ads.")
        elif margen > 15: st.warning("⚠️ Margen moderado. Evita cupones agresivos.")
        else: st.error("🚨 Margen crítico. Sube el precio o cambia de proveedor.")

# --- TAB 4: LEGAL ---
with tab4:
    st.header("🚨 Radar de Trademarks y Protección")
    texto_scan = st.text_area("Pega tu título o etiquetas para escanear infracciones:")
    
    TRADEMARKS = ["disney", "marvel", "nike", "star wars", "barbie", "onesie", "velcro", "jeep", "stanley", "harry potter"]
    if st.button("🛡️ Escanear Listado"):
        alertas = [m.upper() for m in TRADEMARKS if m in texto_scan.lower()]
        if alertas:
            st.error(f"❌ PELIGRO: Marcas registradas detectadas: {alertas}")
        else:
            st.success("✅ Listado seguro de infracciones comunes.")

# --- TAB 5: AUDITORÍA ---
with tab5:
    st.header("🔮 Máquina de Ideas y Tendencias")
    col_i1, col_i2 = st.columns(2)
    with col_i1:
        st.subheader("🎲 Idea Aleatoria")
        if st.button("Generar Concepto Ganador"):
            nichos_p = ["Perro Ciego", "Gato Senior", "Enfermera Nocturna", "Abuela Primeriza"]
            estilos_p = ["Acuarela", "Line Art", "Retro 90s", "Bootleg"]
            st.info(f"Nicho: {random.choice(nichos_p)} | Estilo: {random.choice(estilos_p)}")
            
    with col_i2:
        st.subheader("📅 Calendario Estratégico")
        mes = datetime.datetime.now().month
        mes_f = (mes + 2) % 12 or 12
        st.write(f"📅 Estamos en el mes {mes}. Sube diseños para **Mes {mes_f}**.")

st.markdown("---")
st.caption("Etsy AI Listing Generator v4.0 | Samurai Live Edition | Printify Specs Injected")
