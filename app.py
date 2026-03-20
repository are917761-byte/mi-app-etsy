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
# CONFIGURACIÓN VISUAL (ESTILO APP OSCURA / TARJETAS BLANCAS)
# =========================
st.set_page_config(page_title="Etsy AI Listing Generator", layout="wide", page_icon="📱")

st.markdown("""
    <style>
    /* Fondo oscuro de la App (Igual a la imagen de referencia) */
    .stApp {
        background-color: #161622;
        color: #FFFFFF;
        font-family: 'Inter', sans-serif;
    }
    
    /* Headers principales en blanco */
    h1, h2, h3 { color: #FFFFFF !important; font-weight: 800; }
    
    /* Textos generales en blanco/gris claro */
    p, span, label { color: #E2E8F0 !important; }

    /* TARJETAS BLANCAS REDONDEADAS (Estilo de la imagen) */
    .white-card {
        background-color: #FFFFFF;
        color: #1A1A1A;
        border-radius: 35px;
        padding: 30px;
        margin-bottom: 25px;
        box-shadow: 0 10px 30px rgba(0,0,0,0.3);
    }
    .white-card h1, .white-card h2, .white-card h3, .white-card h4, .white-card p, .white-card li, .white-card strong {
        color: #1A1A1A !important;
    }

    /* Estilizar Inputs, Text Areas y Selects para que parezcan de App */
    .stTextInput>div>div>input, .stSelectbox>div>div>select, .stTextArea>div>div>textarea, .stNumberInput>div>div>input {
        background-color: #FFFFFF;
        border-radius: 20px;
        color: #1A1A1A !important;
        border: 2px solid #E2E8F0;
        padding: 10px 15px;
    }
    
    /* BOTONES NARANJAS (Igual a la imagen) */
    .stButton > button {
        background-color: #FF9B70;
        color: #FFFFFF !important;
        border-radius: 25px;
        border: none;
        padding: 10px 24px;
        font-weight: 700;
        font-size: 16px;
        box-shadow: 0 4px 15px rgba(255, 155, 112, 0.4);
        transition: all 0.3s;
        width: 100%;
    }
    .stButton > button:hover {
        background-color: #FF804D;
        box-shadow: 0 6px 20px rgba(255, 155, 112, 0.6);
    }

    /* Menú Lateral (Navegación tipo App) */
    .stSidebar { background-color: #1E1E2D; }
    .stSidebar [data-testid="stSidebarNav"] { padding-top: 20px; }
    .stSidebar [data-testid="stMarkdownContainer"] p, .stSidebar h3 { color: #FFFFFF !important; }
    
    /* CALENDARIO VISUAL DE LA APP */
    .cal-container {
        background-color: #FFFFFF;
        border-radius: 30px;
        padding: 20px;
        color: #1A1A1A;
        width: 100%;
        max-width: 350px;
        margin: 0 auto;
    }
    .cal-header {
        text-align: center; font-weight: bold; font-size: 18px; margin-bottom: 15px; color: #1A1A1A;
    }
    .cal-grid {
        display: grid; grid-template-columns: repeat(7, 1fr); gap: 5px; text-align: center;
    }
    .cal-day-name { font-size: 12px; color: #888; font-weight: bold; }
    .cal-day {
        height: 35px; width: 35px; line-height: 35px; margin: auto; border-radius: 50%; font-size: 14px; color: #1A1A1A;
    }
    .cal-event {
        background-color: #FF9B70; color: #FFFFFF; font-weight: bold; box-shadow: 0 2px 8px rgba(255,155,112,0.5);
    }
    </style>
    """, unsafe_allow_html=True)

# Ilustración de Perro Minimalista (Reemplazando al gato de la imagen)
DOG_IMG_URL = "https://cdn-icons-png.flaticon.com/512/1900/1900137.png"

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
# TRADUCTOR Y LIMPIADOR INTERNO PARA SEO PURO (NUEVO)
# =========================
def limpiar_producto_en(producto):
    p = producto.lower()
    if "blanket" in p: return "Plush Blanket"
    if "mug" in p: return "Coffee Mug"
    if "canvas" in p: return "Canvas Art"
    if "bandana" in p: return "Pet Bandana"
    if "plaque" in p: return "Acrylic Plaque"
    if "hoodie" in p: return "Custom Hoodie"
    if "t-shirt" in p or "3001" in p: return "Custom Shirt"
    if "invitation" in p: return "Digital Invite"
    if "evite" in p: return "Mobile Evite"
    if "sign" in p: return "Printable Sign"
    if "portrait" in p: return "Custom Portrait"
    if "bowl" in p: return "Pet Bowl"
    if "collar" in p: return "Pet Collar"
    if "bed" in p: return "Pet Bed"
    return "Custom Gift"

def limpiar_nicho_en(nicho):
    n = nicho.lower()
    if "fallecid" in n or "memorial" in n: return "Pet Memorial"
    if "servicio" in n or "apoyo" in n: return "Service Dog"
    if "rescate" in n or "adopci" in n: return "Pet Rescue"
    if "divorcio" in n: return "Divorce Party"
    if "cumplea" in n: return "Pet Birthday"
    if "despedida" in n: return "Bachelorette"
    if "conmemorativo" in n: return "Memorial Gift"
    return "Pet Lover"

# =========================
# FUNCIONES PRINCIPALES DE SEO (OPTIMIZADAS REGLAS 2024)
# =========================

def extraer_texto_ocr(reader, image):
    image_np = np.array(image)
    try:
        resultados = reader.readtext(image_np)
    except Exception as e:
        return ""
    textos = [r[1] for r in resultados if len(r) >= 2]
    return " ".join(textos)

def extraer_keywords_texto(texto, max_keywords=12):
    limpio = re.sub(r"[^a-zA-Z0-9\s-]", " ", texto.lower())
    tokens = [t for t in re.split(r"\s+", limpio) if len(t) > 2]
    stopwords = {"the","and","for","with","this","that","your","you","are","from","gift","para","con","una","uno","tus","tu","las","los","del","por","que","esta","este","como","muy","pero","solo","mas", "estilo", "retrato", "acuarela"}
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
        recomendaciones.extend(["Ceramic Ornament (Adorno Navideño)", "Gildan 18000 (Ugly Sweater Style)"])
    if any(w in niche for w in ["nurse", "teacher", "doctor", "lawyer"]):
        recomendaciones.extend(["Tote Bag (Para llevar al trabajo)", "Tumbler 20oz (Vasos para turnos largos)"])
    if any(w in niche for w in ["dog", "cat", "pet", "paw"]):
        recomendaciones.extend(["Pet Bandana (Para el perrito)", "White Ceramic Mug 15oz (Para el dueño)"])
    if any(w in niche for w in ["mom", "grandma", "dad", "family", "fallecida", "memorial"]):
        recomendaciones.extend(["Velveteen Plush Blanket (Regalo acogedor)", "Acrylic Plaque (Recuerdo sentimental)"])
    if any(w in niche for w in ["gym", "workout", "camping", "fishing"]):
        recomendaciones.extend(["Enamel Campfire Mug", "Tumbler 20oz"])
    if not recomendaciones:
        recomendaciones = ["Bella+Canvas 3001 (T-Shirt Bestseller)", "White Ceramic Mug 11oz & 15oz (Taza clásica)"]
    return list(set(recomendaciones))[:2]

def generar_titulos_venta(keywords, product, niche, texto_detectado, lang="en"):
    # Limpiamos el texto principal detectado/escrito para usarlo como Keyword 1
    kw1 = keywords[0].title() if len(keywords) > 0 else "Custom"
    kw2 = keywords[1].title() if len(keywords) > 1 else "Design"

    if lang == "en":
        prod_en = limpiar_producto_en(product)
        niche_en = limpiar_nicho_en(niche)
        
        # Etsy SEO 2024: Frases legibles, separadas por coma, sin keyword stuffing excesivo.
        titulos = [
            (f"Custom {prod_en} for {niche_en}, Personalized {kw1} Gift, {kw2} Keepsake Present", 98),
            (f"{niche_en} Gift Idea, Personalized {kw1} {prod_en}, Custom Name Design", 92),
            (f"Personalized {kw1} {prod_en}, Unique Gift for {niche_en}, Custom Art Item", 85)
        ]
    else:
        # Español solo de referencia interna
        prod_es = product.split(" (")[0].strip()
        nicho_es = niche.split(" (")[0].strip()
        titulos = [
            (f"{prod_es} Personalizado para {nicho_es}, Regalo de {kw1}", 98),
            (f"Regalo para {nicho_es}, {prod_es} con {kw1} Personalizado", 92),
            (f"{prod_es} Único para {nicho_es}, Detalle de {kw1}", 85)
        ]
    return [(t[:140].strip(', '), score) for t, score in titulos]

def generar_tags_etsy(keywords, product, niche, lang="en"):
    tags = []
    
    if lang == "en":
        prod_en = limpiar_producto_en(product)
        niche_en = limpiar_nicho_en(niche)
        kw = keywords[0] if keywords else "custom"
        
        raw_tags = [
            f"custom {prod_en}", f"{niche_en} gift", f"personalized {kw}",
            f"{kw} {prod_en}", f"custom {niche_en}", "personalized gift",
            f"gift for {niche_en}", f"custom name {kw}", "custom portrait",
            "unique present", "custom artwork", f"{niche_en} present", "trendy gift"
        ]
    else:
        prod_es = product.split(" (")[0].strip().lower()
        nicho_es = niche.split(" (")[0].strip().lower()
        kw = keywords[0] if keywords else "regalo"
        
        raw_tags = [
            f"{prod_es} custom", f"regalo {nicho_es}", f"{kw} personal",
            f"regalo {kw}", "regalo personalizado", f"para {nicho_es}",
            "regalo con nombre", "retrato custom", "arte personalizado",
            "detalle unico", f"{nicho_es} detalle", "regalo original", "tendencia"
        ]
        
    # Validar que ningún tag pase de 20 caracteres (Regla estricta de Etsy)
    for t in raw_tags:
        clean_t = t.replace("  ", " ").strip()
        if len(clean_t) <= 20 and clean_t not in tags:
            tags.append(clean_t)
        if len(tags) == 13: break
        
    # Si faltan tags para llegar a 13, agregar relleno seguro
    fillers = ["custom gift", "personalized item", "special present", "unique design"]
    for f in fillers:
        if len(tags) < 13 and f not in tags:
            tags.append(f)
            
    return tags[:13]

def generar_descripcion_vendedora(product, niche, texto_detectado, lang="en"):
    if lang == "en":
        prod_en = limpiar_producto_en(product)
        niche_en = limpiar_nicho_en(niche)
        
        return f"""Give the perfect gift with this custom {prod_en} designed exclusively for {niche_en}s! 

Whether you're looking for a unique present or treating yourself, this "{texto_detectado}" design is guaranteed to bring a smile. Our items are made with premium materials to ensure vibrant and long-lasting quality.

✨ HOW TO PERSONALIZE ✨
1. Enter your specific details in the personalization box.
2. Double-check your spelling! We print exactly what you provide.
3. Add to cart and checkout!

🎨 DIGITAL PROOF ADD-ON (OPTIONAL)
To keep our production times fast and our prices low, proofs are NOT automatically included. 
If you are ordering a PHYSICAL product and would like to see the artwork before it goes to print, please purchase our "Digital Proof Add-On" listing alongside this item. Otherwise, our artists will use their expert judgment to make your design look amazing!

👕 PRODUCT DETAILS 
- Premium quality {prod_en}. 
- Vibrant, durable POD printing.
📦 SHIPPING: Processed in 2-5 business days. Tracking included!"""
    else:
        prod_es = product.split(" (")[0].strip()
        nicho_es = niche.split(" (")[0].strip()
        
        return f"""🔥 ¡Da el regalo perfecto con este {prod_es} Personalizado diseñado exclusivamente para {nicho_es}! 
Ya sea para un regalo único o para ti mismo, este diseño de "{texto_detectado}" garantiza una sonrisa. 

✨ CÓMO PERSONALIZAR ✨
1. Ingresa los detalles en la caja de personalización.
2. ¡Revisa la ortografía! Imprimimos exactamente lo que escribes.

🎨 MUESTRA DIGITAL (OPCIONAL - COSTO EXTRA)
Para mantener nuestros tiempos de envío rápidos, las muestras NO están incluidas automáticamente. 
Si deseas ver el arte antes de imprimir, por favor compra nuestro listado "Digital Proof Add-On" junto con este artículo. 

👕 DETALLES Y ENVÍO
- {prod_es} de calidad premium.
📦 Procesado en 2-5 días hábiles. ¡Rastreo incluido!"""

# =========================
# MENÚ DE NAVEGACIÓN LATERAL (ESTILO APP)
# =========================
st.sidebar.markdown(f"<div style='text-align: center;'><img src='{DOG_IMG_URL}' width='80' style='filter: invert(1); margin-bottom: 20px;'></div>", unsafe_allow_html=True)
st.sidebar.markdown("<h2 style='text-align: center;'>Etsy App</h2>", unsafe_allow_html=True)

menu = st.sidebar.radio("Navegación:", [
    "🏠 Dashboard & Calendario",
    "1️⃣ Subir Diseño / Concepto",
    "2️⃣ Perfil de Tienda",
    "3️⃣ Selección de Producto",
    "4️⃣ Generador SEO Etsy",
    "💬 Flujo de Muestras",
    "📦 Recursos Rápidos",
    "💰 Calculadora POD",
    "🚨 Radar Legal",
    "📅 Calendario POD",
    "📈 Auditoría de Tienda",
    "🔮 Radar Dinámico",
    "💡 Máquina de Ideas"
])

# =========================
# RUTEO DE PÁGINAS (CONTENIENDO TUS 650+ LÍNEAS EXACTAS)
# =========================

if menu == "🏠 Dashboard & Calendario":
    st.markdown("<h1>Hola, Estratega 👋</h1>", unsafe_allow_html=True)
    col_dash1, col_dash2 = st.columns([1, 1.5])
    
    with col_dash1:
        st.markdown(f"""
        <div class="white-card" style="text-align: center;">
            <img src="{DOG_IMG_URL}" width="120" style="margin-bottom: 15px;">
            <h2>Tu Mascota POD</h2>
            <p style="color:#1A1A1A !important;">Lista para analizar diseños y buscar tendencias.</p>
        </div>
        """, unsafe_allow_html=True)
        
    with col_dash2:
        mes_actual_nombre = datetime.datetime.now().strftime("%B")
        st.markdown(f"""
        <div class="cal-container">
            <div class="cal-header">🗓️ {mes_actual_nombre.capitalize()} (Fechas Clave)</div>
            <div class="cal-grid">
                <div class="cal-day-name">L</div><div class="cal-day-name">M</div><div class="cal-day-name">X</div><div class="cal-day-name">J</div><div class="cal-day-name">V</div><div class="cal-day-name">S</div><div class="cal-day-name">D</div>
                <div></div><div></div><div></div><div class="cal-day">1</div><div class="cal-day">2</div><div class="cal-day">3</div><div class="cal-day">4</div>
                <div class="cal-day">5</div><div class="cal-day">6</div><div class="cal-day">7</div><div class="cal-day cal-event">8</div><div class="cal-day">9</div><div class="cal-day">10</div><div class="cal-day">11</div>
                <div class="cal-day">12</div><div class="cal-day">13</div><div class="cal-day cal-event">14</div><div class="cal-day">15</div><div class="cal-day">16</div><div class="cal-day">17</div><div class="cal-day">18</div>
                <div class="cal-day">19</div><div class="cal-day">20</div><div class="cal-day">21</div><div class="cal-day cal-event">22</div><div class="cal-day">23</div><div class="cal-day">24</div><div class="cal-day">25</div>
                <div class="cal-day">26</div><div class="cal-day">27</div><div class="cal-day">28</div><div class="cal-day cal-event">29</div><div class="cal-day">30</div><div class="cal-day">31</div><div></div>
            </div>
            <p style="text-align:center; font-size:12px; margin-top:15px; color:#888;">Naranja: Días límite de subida para el algoritmo.</p>
        </div>
        """, unsafe_allow_html=True)

elif menu == "1️⃣ Subir Diseño / Concepto":
    st.markdown("<h1>1️⃣ Definir Concepto del Diseño</h1>", unsafe_allow_html=True)
    st.markdown("<div class='white-card'>", unsafe_allow_html=True)
    uploaded_file = st.file_uploader("Sube tu diseño para analizarlo", type=["png", "jpg", "jpeg"])

    if uploaded_file:
        image = Image.open(uploaded_file)
        if image.mode in ('RGBA', 'LA') or (image.mode == 'P' and 'transparency' in image.info):
            fondo_blanco = Image.new("RGB", image.size, (255, 255, 255))
            fondo_blanco.paste(image, mask=image.split()[-1])
            image = fondo_blanco
        else:
            image = image.convert("RGB")

        st.image(image, caption="Vista previa", width=300)

        st.markdown("---")
        st.subheader("📝 ¿Cómo definimos el SEO de tu diseño?")
        st.markdown("<p style='color:#1A1A1A !important;'>Si tu diseño tiene texto, usa el OCR. Si es **SOLO GRÁFICO** (ej: retrato de perro acuarela), escribe el concepto tú misma.</p>", unsafe_allow_html=True)

        col_ocr1, col_ocr2 = st.columns(2)

        with col_ocr1:
            if st.button("👁️ Detectar texto (OCR)"):
                with st.spinner("Analizando imagen..."):
                    texto = extraer_texto_ocr(reader, image)
                    st.session_state["detected_text"] = texto
                    if not texto.strip():
                        st.info("OCR no detectó texto. Introduce el concepto manualmente a la derecha.")
                    else:
                        st.rerun()

        with col_ocr2:
            st.markdown("**Entrada Manual:**")
            concepto_manual = st.text_input(
                "Describe la imagen (ej: Watercolor Golden Retriever):",
                value=st.session_state["detected_text"], 
                key="final_concept_input"
            )
            
            if concepto_manual != st.session_state["detected_text"]:
                 st.session_state["detected_text"] = concepto_manual

    if st.session_state.get("detected_text"):
        st.success(f"✅ Concepto '{st.session_state['detected_text']}' guardado. ¡Ve al Catálogo!")
    elif uploaded_file:
        st.warning("⚠️ Ejecuta el OCR o escribe el concepto manual arriba para activar el SEO.")
        
    st.markdown("</div>", unsafe_allow_html=True)

elif menu == "2️⃣ Perfil de Tienda":
    st.markdown("<h1>2️⃣ Perfil de Tienda y Micro-Nicho</h1>", unsafe_allow_html=True)
    st.markdown("<div class='white-card'>", unsafe_allow_html=True)
    col_tienda1, col_tienda2 = st.columns(2)

    with col_tienda1:
        tienda_seleccionada = st.radio("Selecciona la Tienda a trabajar:", ["🐾 Tienda POD Mascotas", "💌 Tienda Digital (Invitaciones)"])

    with col_tienda2:
        if tienda_seleccionada == "🐾 Tienda POD Mascotas":
            subnicho = st.selectbox("Selecciona el Sub-Nicho:", [
                "Mascotas Fallecidas (Memorial / Rainbow Bridge)",
                "Mascotas de Servicio Médico / Apoyo Emocional",
                "Mascotas Vivas (Cumpleaños / Uso Diario)",
                "Rescate / Adopción (Gotcha Day)"
            ])
            estilo_arte = st.selectbox("Estilo de Personalización:", [
                "Acuarela Digital (Watercolor Portrait)",
                "Line Art Minimalista",
                "Caricatura / Cartoon",
                "Pintura al Óleo Digital"
            ])
            st.session_state["niche"] = f"{subnicho} estilo {estilo_arte}"
        else:
            subnicho = st.selectbox("Selecciona el Sub-Nicho:", [
                "Fiesta de Divorcio / Inicio de Soltería",
                "Cumpleaños de Mascotas (Paw-ty)",
                "Conmemorativos / Celebración de Vida",
                "Despedida de Soltera Anti-Tradicional"
            ])
            estilo_arte = st.selectbox("Estilo Visual:", [
                "Acuarela Digital Elegante",
                "Sarcástico / Divertido (Texto Bold)",
                "Minimalista / Estético",
                "Boho / Floral"
            ])
            st.session_state["niche"] = f"{subnicho} estilo {estilo_arte}"

    st.info(f"🎯 **Enfoque actual:** {tienda_seleccionada} ➔ {st.session_state['niche']}")
    st.session_state["tienda_seleccionada"] = tienda_seleccionada 
    st.markdown("</div>", unsafe_allow_html=True)

elif menu == "3️⃣ Selección de Producto":
    st.markdown("<h1>3️⃣ Selección de Producto</h1>", unsafe_allow_html=True)
    st.markdown("<div class='white-card'>", unsafe_allow_html=True)
    
    tienda_seleccionada = st.session_state.get("tienda_seleccionada", "🐾 Tienda POD Mascotas")

    if tienda_seleccionada == "🐾 Tienda POD Mascotas":
        st.write("**Catálogo Estratégico Printify (Bestsellers + Mascotas):**")
        productos_mascotas = [
            "Bella+Canvas 3001 (T-Shirt Bestseller)",
            "Gildan 18000 (Crewneck Sweatshirt)",
            "Gildan 18500 (Hoodie Clásica)",
            "Comfort Colors 1717 (Camiseta Premium)",
            "Gildan 5000 (Camiseta Económica)",
            "White Ceramic Mug 11oz & 15oz (Taza clásica)",
            "Enamel Campfire Mug (Taza campamento)",
            "Tote Bag (Bolsa de tela)",
            "Die-Cut Stickers (Pegatinas)",
            "Velveteen Plush Blanket (Cobija Suave)",
            "Canvas Gallery Wraps (Lienzo Premium)",
            "Acrylic Plaque (Placa Acrílica Memorial)",
            "Pet Bandana (Bandana para Cuello)",
            "Pet Bowl (Plato de Cerámica/Acero)",
            "Pet Feeding Mat (Tapete Platos)",
            "Pet Bed (Cama Mascota)",
            "Pet Tank Top (Camiseta Perros)",
            "Pet Tag (Placa Identificación)",
            "Pet Collar (Collar Ajustable)"
        ]
        cols_prod = st.columns(3)
        for idx, producto in enumerate(productos_mascotas):
            with cols_prod[idx % 3]:
                if st.button(producto):
                    st.session_state["product"] = producto
    else:
        st.write("**Catálogo Digital:**")
        productos_digitales = [
            "Digital Invitation (Canva Template)",
            "Evite / Mobile Invitation (Smartphone Size)",
            "Printable Memorial Sign",
            "Digital Watercolor Portrait File"
        ]
        cols_dig = st.columns(2)
        for idx, producto in enumerate(productos_digitales):
            with cols_dig[idx % 2]:
                if st.button(producto):
                    st.session_state["product"] = producto

    if st.session_state.get("product"):
        st.success(f"📦 Producto seleccionado: {st.session_state['product']}")
    st.markdown("</div>", unsafe_allow_html=True)

elif menu == "4️⃣ Generador SEO Etsy":
    st.markdown("<h1>4️⃣ Generador SEO Experto para Etsy</h1>", unsafe_allow_html=True)
    if st.session_state["detected_text"] and st.session_state.get("product"):
        if st.button("🚀 Generar Listado Optimizado"):
            st.session_state["generar_seo_ahora"] = True
            
        if st.session_state.get("generar_seo_ahora"):
            st.markdown("<div class='white-card'>", unsafe_allow_html=True)
            with st.spinner("Creando SEO con intención de regalo..."):
                product = st.session_state["product"]
                niche = st.session_state.get("niche", "General")
                keyword_text = st.session_state["detected_text"].strip()
                base_keywords = extraer_keywords_texto(keyword_text)
                if not base_keywords: base_keywords = [niche, product, "gift"]

                st.session_state["tags_generados"] = generar_tags_etsy(base_keywords, product, niche, "en")

                tab_en, tab_es = st.tabs(["🇺🇸 Inglés (Copia esto en Etsy EUA)", "🇪🇸 Español (Para tu Referencia)"])

                with tab_en:
                    st.info("⚠️ COPIA ESTOS DATOS EN ETSY. Están limpios en inglés puro sin Spanglish.")
                    st.subheader("📌 Títulos Optimizados (Best Practice 2024)")
                    titulos_en = generar_titulos_venta(base_keywords, product, niche, keyword_text, "en")
                    for t, score in titulos_en:
                        if score >= 95:
                            st.success(f"⭐ **{score}% MATCH:**\n\n{t}")
                        else:
                            st.info(f"🔥 **{score}% MATCH:**\n\n{t}")

                    st.subheader("🏷️ 13 Etiquetas Exactas (Menos de 20 chars)")
                    tags_en = st.session_state["tags_generados"]
                    for tag in tags_en:
                        st.markdown(f"✅ `{tag}`")
                    st.caption("Copia y pega:")
                    st.code(", ".join(tags_en), language="text")
                    
                    st.subheader("📝 Descripción Estructurada")
                    st.code(generar_descripcion_vendedora(product, niche, keyword_text, "en"), language="text")

                with tab_es:
                    st.info("💡 Traducción de referencia (No usar en la tienda de EUA).")
                    st.subheader("📌 Títulos")
                    titulos_es = generar_titulos_venta(base_keywords, product, niche, keyword_text, "es")
                    for t, score in titulos_es:
                        st.write(f"**{score}% MATCH:** {t}")
                    st.subheader("🏷️ Etiquetas")
                    tags_es = generar_tags_etsy(base_keywords, product, niche, "es")
                    st.code(", ".join(tags_es), language="text")
                    st.subheader("📝 Descripción")
                    st.text_area("Descripción (ES):", generar_descripcion_vendedora(product, niche, keyword_text, "es"), height=300)
            st.markdown("</div>", unsafe_allow_html=True)
    else:
        st.warning("⚠️ Necesitas detectar el texto de una imagen o escribir el concepto y seleccionar un producto primero.")

elif menu == "💬 Flujo de Muestras":
    st.markdown("<h1>💬 Flujo de Muestras y Add-On (Monetización)</h1>", unsafe_allow_html=True)
    st.markdown("Automatiza tu atención al cliente y monetiza las revisiones.")

    tab_proof1, tab_proof2, tab_addon = st.tabs([
        "💬 Mensaje: Envío de Muestra", 
        "⏰ Mensaje: Recordatorio 24h", 
        "💰 Generador: Listado Add-On"
    ])

    with tab_proof1:
        st.markdown("<div class='white-card'>", unsafe_allow_html=True)
        st.markdown("**Usa esto cuando el cliente PAGA por la muestra.**")
        st.code("""Hi [Nombre del Cliente],\n\nThank you so much for your order! 💛 \n\nI have finished the digital design for your custom piece. I have attached the proof (preview) to this message so you can see exactly how it will look.\n\nPlease review the spelling and the design. If everything looks perfect, just reply with "APPROVED" and I will send it straight to production! If you need any minor tweaks, let me know.\n\nBest regards,\n[Tu Nombre]""", language="text")
        st.markdown("</div>", unsafe_allow_html=True)

    with tab_proof2:
        st.markdown("<div class='white-card'>", unsafe_allow_html=True)
        st.markdown("**Usa esto si el cliente no responde en 24 horas.**")
        st.code("""Hi [Nombre del Cliente],\n\nJust checking in! I sent your design proof yesterday. \n\nTo ensure your order arrives on time, please let me know if the design is approved by [Hora/Fecha]. If I don't hear back by then, I will proceed with printing as shown in the proof to avoid any shipping delays.\n\nThank you!""", language="text")
        st.markdown("</div>", unsafe_allow_html=True)

    with tab_addon:
        st.markdown("<div class='white-card'>", unsafe_allow_html=True)
        st.info("💡 **ESTRATEGIA:** Crea un ÚNICO listado en tu tienda con esta información. Ponle un precio de $2.99 a $4.99 USD y configúralo como 'Producto Digital'.")
        st.subheader("📸 Sugerencia de Imagen (Mockup)")
        st.markdown("Crea una imagen sencilla y estética en Canva. Fondo de color pastel, y letras grandes y legibles que digan:\n\n**'DIGITAL PROOF ADD-ON. See your artwork before it prints!'**")
        st.subheader("📌 Título del Listado en Inglés")
        st.code("Digital Proof Add-On for Custom Orders, Artwork Preview, See Design Before Printing, Optional Digital Proof, Pet Portrait Proof Add On", language="text")
        st.subheader("🏷️ Etiquetas (Tags)")
        st.code("digital proof, artwork preview, add on listing, see before printing, custom order proof, design preview, optional add on, pet portrait proof, custom gift proof, digital download, rush proof, approval required, order upgrade", language="text")
        st.subheader("📝 Descripción del Listado")
        st.code("""⚠️ PLEASE READ: THIS IS AN ADD-ON SERVICE, NOT A PHYSICAL PRODUCT.\n\nPurchase this listing IN ADDITION to your custom physical product if you wish to see a digital preview (proof) of the artwork before it is sent to production. \n\nTo keep our prices low and production times incredibly fast, proofs are not automatically included with our standard physical items. Our expert artists use their best judgment to create stunning pieces based on your photos and notes. However, if you prefer to review and approve the design first to request minor tweaks, this add-on is for you!\n\n✨ HOW IT WORKS ✨\n1. Add your physical custom item (mug, canvas, blanket, etc.) to your cart.\n2. Add this "Digital Proof Add-On" listing to your cart as well.\n3. Complete your checkout.\n4. Within 24-48 hours, we will send you a digital preview of your design via Etsy Messages.\n5. You can approve it or request one (1) minor revision. \n\n*Note: Purchasing a proof may extend your final delivery date slightly, as we will wait for your approval before printing.*""", language="text")
        st.markdown("</div>", unsafe_allow_html=True)

elif menu == "📦 Recursos Rápidos":
    st.markdown("<h1>📦 Recursos Rápidos</h1>", unsafe_allow_html=True)
    st.markdown("<div class='white-card'>", unsafe_allow_html=True)
    col1, col2 = st.columns(2)
    with col1:
        st.subheader("🖼️ Mockups Populares (Placeit)")
        mockups = {
            "👕 T-shirt / Camiseta": "https://placeit.net/c/mockups/stages/t-shirt-mockup",
            "🧥 Hoodie / Sudadera": "https://placeit.net/c/mockups/stages/hoodie-mockup",
            "☕ Mug / Taza Cerámica": "https://placeit.net/c/mockups/stages/mug-mockup",
            "🥤 Tumbler / Vaso Térmico": "https://placeit.net/c/mockups/stages/tumbler-mockup",
            "🖼️ Canvas / Lienzo": "https://placeit.net/c/mockups/stages/canvas-mockup",
            "🛌 Blanket / Cobija": "https://placeit.net/c/mockups/stages/blanket-mockup",
            "🎄 Ornament / Adorno": "https://placeit.net/c/mockups/stages/ornament-mockup",
            "👜 Tote Bag / Bolsa": "https://placeit.net/c/mockups/stages/tote-bag-mockup"
        }
        for name, url in mockups.items():
            st.markdown(f"[{name}]({url})")
    st.markdown("</div>", unsafe_allow_html=True)

elif menu == "💰 Calculadora POD":
    st.markdown("<h1>💰 Calculadora de Rentabilidad (Estrategia de Envío)</h1>", unsafe_allow_html=True)
    st.markdown("<div class='white-card'>", unsafe_allow_html=True)
    col_calc1, col_calc2 = st.columns(2)

    with col_calc1:
        st.subheader("📦 Costos (Printify)")
        costo_printify = st.number_input("Costo de Producción $", min_value=0.0, value=12.50, step=0.5)
        envio_printify = st.number_input("Costo de Envío Printify $", min_value=0.0, value=4.79, step=0.5)

    with col_calc2:
        st.subheader("🛍️ Ingresos (Etsy)")
        precio_venta = st.number_input("Precio del Producto $", min_value=0.0, value=24.99, step=0.5)
        estrategia_envio = st.radio("Estrategia de Envío al Cliente:", ["Cobrar Envío Aparte", "Envío Gratis (Absorbido)"])
        cobro_envio_etsy = st.number_input("¿Cuánto cobrarás de envío? $", min_value=0.0, value=5.99, step=0.5) if estrategia_envio == "Cobrar Envío Aparte" else 0.0

    if st.button("📊 Calcular Ganancia Real"):
        ingreso_total = precio_venta + cobro_envio_etsy
        etsy_fees = 0.45 + (ingreso_total * 0.095)
        costo_total = costo_printify + envio_printify + etsy_fees
        ganancia_neta = ingreso_total - costo_total
        margen_porcentaje = (ganancia_neta / ingreso_total) * 100 if ingreso_total > 0 else 0

        st.markdown("---")
        col_res1, col_res2, col_res3 = st.columns(3)
        col_res1.metric("Ingreso Bruto (Paga el Cliente)", f"${ingreso_total:.2f}")
        col_res2.metric("Tarifas Retenidas por Etsy", f"${etsy_fees:.2f}")
        col_res3.metric("Costo Printify (Prod + Envío)", f"${(costo_printify + envio_printify):.2f}")
        
        st.write("") 
        
        col_res4, col_res5 = st.columns(2)
        if margen_porcentaje >= 30:
            col_res4.metric("Ganancia Neta (Directo a tu bolsa)", f"${ganancia_neta:.2f}", "Margen Excelente")
            col_res5.metric("Margen de Beneficio", f"{margen_porcentaje:.1f}%", "Aprobado para Escalar")
            st.success("🔥 ¡Estrategia sólida! Tienes un margen mayor al 30%. Tienes espacio para pagar Etsy Ads ($3 al día) y seguir ganando dinero.")
        elif 15 <= margen_porcentaje < 30:
            col_res4.metric("Ganancia Neta", f"${ganancia_neta:.2f}")
            col_res5.metric("Margen de Beneficio", f"{margen_porcentaje:.1f}%", delta_color="off")
            st.warning("⚠️ Margen ajustado. Está bien para conseguir tus primeras ventas y reseñas, pero NO uses Ads con este producto porque terminarás perdiendo dinero.")
        else:
            col_res4.metric("Ganancia Neta", f"${ganancia_neta:.2f}", "-Riesgo de Pérdida")
            col_res5.metric("Margen de Beneficio", f"{margen_porcentaje:.1f}%", "-Cambia tu estrategia")
            st.error("🚨 ¡Alerta roja! Estás ganando muy poco o directamente trabajando gratis. Sube el precio del producto o cobra el envío.")
    st.markdown("</div>", unsafe_allow_html=True)

elif menu == "🚨 Radar Legal":
    st.markdown("<h1>🚨 Radar Legal y Protección de Tienda</h1>", unsafe_allow_html=True)
    st.markdown("<div class='white-card'>", unsafe_allow_html=True)

    texto_automatico = st.session_state.get("detected_text", "")
    if "tags_generados" in st.session_state:
        texto_automatico += " " + " ".join(st.session_state["tags_generados"])

    texto_a_revisar = st.text_area("Texto a revisar (Autocompletado automáticamente):", value=texto_automatico, height=100)

    TRADEMARK_BLACKLIST = [
        "disney", "marvel", "star wars", "nike", "harry potter", "velcro", 
        "onesie", "jeep", "taylor swift", "stanley", "snoopy", "mickey", 
        "nfl", "nba", "barbie", "lego", "tupperware", "taser", "chapstick", 
        "super bowl", "peanuts", "pokemon", "hello kitty", "bluey", "shrek"
    ]

    col_legal1, col_legal2 = st.columns([2, 1])

    with col_legal1:
        if st.button("🛡️ Escanear Listado Completo"):
            if texto_a_revisar:
                texto_limpio = texto_a_revisar.lower()
                alertas = [marca for marca in TRADEMARK_BLACKLIST if marca in texto_limpio]
                
                if alertas:
                    st.error(f"⚠️ ¡PELIGRO DE TRADEMARK! Hemos detectado marcas registradas: **{', '.join(alertas).title()}**")
                    st.write("❌ **Acción:** Borra estas palabras inmediatamente de tus tags o título. Etsy cerrará tu tienda.")
                else:
                    st.success("✅ ¡Listado Limpio! Tu texto y tags pasaron la prueba de la Lista Negra común.")
            else:
                st.warning("No hay texto para revisar aún.")

    with col_legal2:
        st.subheader("Base Oficial (EUA)")
        st.markdown("[🔍 Buscar en USPTO (TESS)](https://tmsearch.uspto.gov/)")
        st.markdown("[📝 Buscar en Trademarkia](https://trademarkia.com/)")
    st.markdown("</div>", unsafe_allow_html=True)

elif menu == "📅 Calendario POD":
    st.markdown("<h1>📅 Calendario POD y Retención (Estrategia EUA)</h1>", unsafe_allow_html=True)
    st.markdown("En Print on Demand, **diseñamos con 2 a 3 meses de anticipación**.")

    tab_cal, tab_cup = st.tabs(["⏰ Calendario de Subidas", "💌 Estrategia de Cupones"])

    with tab_cal:
        st.markdown("<div class='white-card'>", unsafe_allow_html=True)
        st.subheader("El Ciclo de Vida del Regalo en EUA")
        col_q1, col_q2 = st.columns(2)
        with col_q1:
            st.markdown("""
            **Q1 (Ene - Mar)**
            * **Enero:** Diseña para *Valentine's Day* y *St. Patrick's Day*.
            * **Febrero:** Sube diseños de *Easter* y *Spring*.
            * **Marzo:** ¡URGENTE! Diseña para *Mother's Day*.
            
            **Q2 (Abr - Jun)**
            * **Abril:** Sube diseños de *Father's Day* y *Gradu
