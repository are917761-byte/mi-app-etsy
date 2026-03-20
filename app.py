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
# 1. CONFIGURACIÓN INICIAL Y ESTILO
# =================================================================
st.set_page_config(page_title="Etsy AI Listing Generator PRO", layout="wide", page_icon="🛍️")

st.markdown("""
    <style>
    .main { background-color: #f5f7f9; }
    .stButton>button { width: 100%; border-radius: 8px; height: 3.5em; background-color: #ff5a1f; color: white; border: none; font-weight: bold; font-size: 16px; transition: 0.3s; }
    .stButton>button:hover { background-color: #e04e1a; transform: scale(1.02); }
    .stTabs [data-baseweb="tab-list"] { gap: 10px; }
    .stTabs [data-baseweb="tab"] { height: 50px; background-color: #f0f2f6; border-radius: 5px 5px 0px 0px; padding: 10px 20px; }
    .stTabs [aria-selected="true"] { background-color: #ff5a1f !important; color: white !important; }
    </style>
    """, unsafe_allow_html=True)

st.title("🛍️ Etsy AI Listing Generator (Modo Estratega POD)")

# =================================================================
# 2. SESSION STATE (MEMORIA DE LA APP)
# =================================================================
if "product" not in st.session_state: st.session_state["product"] = "Bella+Canvas 3001"
if "niche" not in st.session_state: st.session_state["niche"] = "General"
if "detected_text" not in st.session_state: st.session_state["detected_text"] = ""
if "live_tags" not in st.session_state: st.session_state["live_tags"] = []

@st.cache_resource
def load_reader():
    return easyocr.Reader(["en", "es"], gpu=False)

reader = load_reader()

# =================================================================
# 3. FUNCIONES LÓGICAS DE SEO Y SCRAPING LIVE
# =================================================================

def obtener_keywords_live_etsy(keyword):
    """Extrae las sugerencias en tiempo real de la barra de búsqueda de Etsy."""
    if not keyword: return []
    kw_url = keyword.replace(" ", "+")
    url = f"https://www.etsy.com/ws/search/suggest?search_query={kw_url}&limit=12"
    headers = {'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/91.0.4472.124 Safari/537.36'}
    try:
        r = requests.get(url, headers=headers, timeout=5)
        if r.status_code == 200:
            return [item.get('query', '') for item in r.json().get('results', [])]
    except:
        return []
    return []

def obtener_detalles_printify(producto):
    """Diccionario técnico de productos para la descripción."""
    p = str(producto).lower()
    if "3001" in p or "t-shirt" in p:
        return "👕 ITEM SPECS (Bella+Canvas 3001):\n- 100% Airlume combed and ringspun cotton\n- Light fabric (4.2 oz/yd²)\n- Retail fit & Tear away label\n- Runs true to size"
    elif "18000" in p or "sweatshirt" in p or "hoodie" in p:
        return "🧥 ITEM SPECS (Gildan 18000/18500):\n- 50% cotton, 50% polyester\n- Medium-heavy fabric for cozy warmth\n- Classic fit & Tear-away label"
    elif "mug" in p or "taza" in p:
        return "☕ ITEM SPECS (Ceramic Mug):\n- High-quality white ceramic\n- Lead and BPA-free\n- Microwave and dishwasher safe\n- Vibrant, fade-resistant wrap-around print"
    elif "bandana" in p:
        return "🐾 ITEM SPECS (Pet Bandana):\n- 100% soft spun polyester\n- Breathable, durable, and lightweight\n- One-sided vibrant print"
    elif "plaque" in p or "placa" in p:
        return "✨ ITEM SPECS (Acrylic Plaque):\n- Premium, crystal-clear acrylic (3mm)\n- Vibrant, fade-resistant UV printing\n- Sleek wooden base (if selected)"
    elif "blanket" in p or "manta" in p:
        return "🛌 ITEM SPECS (Velveteen Plush):\n- 100% Polyester for extreme softness\n- Double needle topstitch on all seams\n- Machine washable (cold)"
    elif "bowl" in p or "plato" in p:
        return "🥣 ITEM SPECS (Pet Bowl):\n- Double-wall stainless steel / Ceramic\n- Anti-slip rubber base\n- Dishwasher safe (top rack)"
    return "✨ ITEM SPECS:\n- Premium quality materials\n- Vibrant and durable printing\n- Carefully crafted to order just for you"

def extraer_keywords_limpias(texto):
    limpio = re.sub(r"[^a-zA-Z0-9\s-]", " ", str(texto).lower())
    tokens = [t for t in re.split(r"\s+", limpio) if len(t) > 2]
    stopwords = {"the","and","for","with","this","that","your","gift","para","con","una"}
    return [t for t in tokens if t not in stopwords][:10]

# =================================================================
# 4. UI POR PESTAÑAS (FLUJO ESTRATÉGICO)
# =================================================================

t1, t2, t3, t4, t5 = st.tabs(["🎨 1. Diseño y Nicho", "🚀 2. SEO Live & Listado", "💰 3. Rentabilidad", "🛡️ 4. Radar Legal", "🔮 5. Ideas"])

# --- TAB 1: DISEÑO ---
with t1:
    st.header("1️⃣ Preparación del Producto")
    col_u1, col_u2 = st.columns([1, 2])
    
    with col_u1:
        st.subheader("Subir Arte")
        up = st.file_uploader("Sube tu diseño transparente (PNG/JPG)", type=["png", "jpg", "jpeg"])
        if up:
            img = Image.open(up)
            # Procesar para OCR (fondo oscuro para ver letras blancas)
            if img.mode in ('RGBA', 'LA'):
                bg = Image.new("RGB", img.size, (40, 40, 40))
                bg.paste(img, mask=img.split()[-1])
                img_show = bg
            else:
                img_show = img.convert("RGB")
            
            st.image(img_show, use_container_width=True, caption="Vista de análisis")
            
            if st.button("👁️ Detectar Texto del Diseño"):
                with st.spinner("Escaneando diseño..."):
                    res = reader.readtext(np.array(img_show))
                    st.session_state["detected_text"] = " ".join([r[1] for r in res])
                st.rerun()

    with col_u2:
        st.subheader("Configuración de Nicho")
        st.session_state["detected_text"] = st.text_input("Concepto / Frase del Diseño:", value=st.session_state["detected_text"])
        
        tienda = st.radio("Tienda:", ["🐾 Mascotas (POD)", "💌 Digital / Invitaciones"], horizontal=True)
        
        if tienda == "🐾 Mascotas (POD)":
            st.session_state["niche"] = st.selectbox("Micro-Nicho:", ["Memorial / Fallecidos", "Servicio / Apoyo", "Cumpleaños Mascota", "Gotcha Day / Rescate", "Humor Mascotas"])
            prods = ["Bella+Canvas 3001 T-Shirt", "Gildan 18000 Sweatshirt", "White Ceramic Mug", "Pet Bandana", "Acrylic Plaque", "Pet Bowl", "Plush Blanket", "Pet Bed", "ID Tag"]
        else:
            st.session_state["niche"] = st.selectbox("Micro-Nicho Digital:", ["Fiesta de Divorcio", "Paw-ty (Cumpleaños Perro)", "Bachelorette (Despedida)", "Conmemorativo"])
            prods = ["Digital Invitation (Canva)", "Mobile Evite (Smartphone)", "Printable Sign", "Digital Portrait"]
        
        st.session_state["product"] = st.selectbox("Producto POD:", prods)

# --- TAB 2: SEO LIVE ---
with t2:
    if st.session_state["product"] and st.session_state["detected_text"]:
        st.header("🔍 Motor SEO en Tiempo Real (Etsy Suggest API)")
        st.markdown("Extrae lo que los compradores reales están escribiendo en Etsy **ahora mismo**.")
        
        col_api1, col_api2 = st.columns([3, 1])
        with col_api1:
            semilla = st.text_input("Investigar Keyword (ej: 'dog memorial'):", value=st.session_state["detected_text"])
        with col_api2:
            st.write("") # Espaciador
            if st.button("🕵️‍♂️ Extraer Tags Live"):
                st.session_state["live_tags"] = obtener_keywords_live_etsy(semilla)
        
        if st.session_state["live_tags"]:
            st.success("🔥 Tendencias detectadas en la barra de búsqueda de Etsy:")
            st.code(", ".join(st.session_state["live_tags"]))

        st.markdown("---")
        
        if st.button("🚀 GENERAR LISTADO MAESTRO"):
            with st.spinner("Aplicando fórmula ModPawsUS..."):
                p = st.session_state["product"]
                n = st.session_state["niche"]
                kw = st.session_state["detected_text"]
                specs = obtener_detalles_printify(p)
                
                t_en, t_es, t_help = st.tabs(["🇺🇸 Listado Inglés", "🇪🇸 Referencia", "💬 Guía de Venta"])
                
                with t_en:
                    # Títulos Pirámide
                    st.subheader("📌 Títulos Optimizados (140 Caracteres)")
                    st.success(f"Custom {kw} {p} for {n}, Personalized {n} Gift, Unique {kw} Keepsake Present")
                    st.info(f"{n} {p} Personalized, Custom {kw} Design, Unique Gift for {n} Lovers")
                    
                    # Tags
                    st.subheader("🏷️ 13 Etiquetas (Mezcla Live + Estratégica)")
                    tags_base = extraer_keywords_limpias(kw) + [n.lower(), "gift", "personalized"]
                    tags_mix = list(dict.fromkeys(st.session_state["live_tags"] + tags_base))
                    tags_finales = [t[:20] for t in tags_mix][:13]
                    st.code(", ".join(tags_finales))
                    
                    # Descripción
                    st.subheader("📝 Descripción con Inyección de Specs")
                    desc = f"""✨ {p.upper()} PERSONALIZED FOR {n.upper()} ✨\n\nGive a gift that speaks to the heart with this custom "{kw}" {p}. Designed specifically for {n} lovers, this piece is a beautiful way to celebrate your furry friend.\n\n{specs}\n\n🎨 HOW TO PERSONALIZE:\n1. Enter details in the personalization box.\n2. Checkout.\n3. Send your photo via Etsy Messages!\n\n📦 PRODUCTION: 2-5 business days.\n🚚 SHIPPING: Tracked delivery included."""
                    st.code(desc)

                with t_es:
                    st.write(f"**Nicho:** {n} | **Producto:** {p}")
                    st.text_area("Descripción en Español:", f"🔥 ¡Regalo perfecto para {n}! {p} personalizado con diseño '{kw}'. \n\n{specs}", height=300)

                with t_help:
                    st.subheader("💬 Mensajes para Clientes")
                    st.code(f"Hi! I've attached the proof for your {p}. Please approve it within 24h!")
                    st.markdown("---")
                    with st.expander("🖼️ ESTRATEGIA DE MOCKUPS"):
                        st.write("1. Foto 1: El producto con el nombre claramente visible.")
                        st.write("2. Foto 2: Alguien usando el producto (Lifestyle).")
                        st.write("3. Foto 3: Gráfico de 'Cómo ordenar'.")
    else:
        st.warning("⚠️ Completa los datos en la Pestaña 1 para activar el SEO.")

# --- TAB 3: DINERO ---
with tab3:
    st.header("💰 Calculadora de Ganancia Neta")
    c1, c2 = st.columns(2)
    with c1:
        costo_p = st.number_input("Costo Printify (Producción) $", value=12.50)
        envio_p = st.number_input("Costo Envío Printify $", value=4.75)
    with c2:
        precio_v = st.number_input("Precio de Venta Etsy $", value=29.99)
        envio_v = st.number_input("Envío cobrado al cliente $", value=0.0)
    
    if st.button("📊 Calcular Rentabilidad"):
        total_ingreso = precio_v + envio_v
        fee_etsy = 0.45 + (total_ingreso * 0.095)
        neta = total_ingreso - (costo_p + envio_p + fee_etsy)
        margen = (neta / total_ingreso) * 100
        
        st.metric("Ganancia Neta", f"${neta:.2f}", f"{margen:.1f}% Margen")
        if margen > 30: st.success("🔥 ¡Excelente! Producto apto para Etsy Ads.")
        elif margen > 15: st.warning("⚠️ Margen ajustado. Evita descuentos agresivos.")
        else: st.error("🚨 Alerta: Sube el precio o cambia de producto.")

# --- TAB 4: LEGAL ---
with tab4:
    st.header("🛡️ Radar de Infracciones (Trademark)")
    t_scan = st.text_area("Pega tu título o etiquetas aquí para escanear:")
    if st.button("🛡️ Escanear Listado"):
        prohibidos = ["disney", "marvel", "star wars", "nike", "barbie", "onesie", "velcro", "jeep", "stanley"]
        hallados = [p for p in prohibidos if p in t_scan.lower()]
        if hallados:
            st.error(f"❌ ¡PELIGRO! Marcas registradas detectadas: {hallados}")
        else:
            st.success("✅ ¡Listado Limpio! No se detectaron marcas comunes.")

# --- TAB 5: IDEAS ---
with tab5:
    st.header("🔮 Máquina de Ideas POD")
    if st.button("🎲 Generar Idea Ganadora"):
        mascotas = ["Perro de Tres Patas", "Gato Senior", "Hámster Veloz", "Dueño de Rescate"]
        estilos = ["Acuarela", "Line Art", "Caricatura Retro", "Estilo Óleo"]
        prods_random = ["Taza", "Bandana", "Placa Acrílica", "Sudadera"]
        st.info(f"Nicho: {random.choice(mascotas)} | Estilo: {random.choice(estilos)} | Producto: {random.choice(prods_random)}")
    
    st.markdown("---")
    st.subheader("📅 Calendario de Temporada")
    st.write(f"Estamos en: {datetime.datetime.now().strftime('%B')}. Deberías estar subiendo diseños para: **{ (datetime.datetime.now() + datetime.timedelta(days=60)).strftime('%B') }**.")

st.markdown("---")
st.caption("Etsy AI Generator v4.0 | Samurai Live Edition | Printify Specs Injected")
