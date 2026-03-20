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
# CONFIGURACIÓN VISUAL (REPLICA EXACTA DE LA IMAGEN)
# =========================
st.set_page_config(page_title="Etsy App Master", layout="wide", page_icon="📱")

st.markdown("""
    <style>
    /* Fondo principal Azul Noche Profundo (De tu imagen) */
    .stApp {
        background-color: #1a1a24;
        color: #ffffff;
        font-family: 'Inter', sans-serif;
    }
    
    /* Headers en Blanco */
    h1, h2, h3, h4 { color: #ffffff !important; font-weight: 800; }
    p, span, label { color: #f0f0f5 !important; font-weight: 500;}

    /* Simulación de Pantallas de App (Tarjetas Blancas) */
    .app-screen {
        background-color: #ffffff;
        border-radius: 40px;
        padding: 35px;
        box-shadow: 0 15px 35px rgba(0,0,0,0.4);
        margin-bottom: 25px;
        color: #1a1a24;
    }
    /* El texto dentro de las tarjetas blancas debe ser oscuro */
    .app-screen h1, .app-screen h2, .app-screen h3, .app-screen h4, .app-screen p, .app-screen li, .app-screen b {
        color: #1a1a24 !important;
    }
    
    /* Botones Color Durazno (De tu imagen) */
    .stButton > button {
        background-color: #ffb185 !important;
        color: #ffffff !important;
        border-radius: 30px !important;
        border: none !important;
        padding: 12px 28px !important;
        font-weight: 700 !important;
        font-size: 16px !important;
        box-shadow: 0 8px 20px rgba(255, 177, 133, 0.4) !important;
        transition: all 0.3s ease !important;
        width: 100%;
    }
    .stButton > button:hover {
        background-color: #ff9a60 !important;
        transform: translateY(-2px);
    }

    /* Inputs y Selects */
    .stTextInput>div>div>input, .stSelectbox>div>div>select, .stTextArea>div>div>textarea, .stNumberInput>div>div>input {
        background-color: #f4f4f8;
        border-radius: 20px;
        color: #1a1a24 !important;
        border: 2px solid #e0e0e0;
        padding: 10px 15px;
    }

    /* Menú Lateral */
    .stSidebar { background-color: #232332; }
    .stSidebar [data-testid="stSidebarNav"] { padding-top: 20px; }
    .stSidebar [data-testid="stMarkdownContainer"] p { color: #ffffff !important; font-size: 16px; font-weight: bold;}
    
    /* Calendario Visual CSS */
    .cal-box {
        background-color: #ffffff; border-radius: 35px; padding: 25px; color: #1a1a24; margin: auto; max-width: 350px;
    }
    .cal-header {
        text-align: center; font-weight: bold; font-size: 18px; margin-bottom: 20px; color: #1a1a24;
    }
    .cal-grid { display: grid; grid-template-columns: repeat(7, 1fr); gap: 8px; text-align: center; }
    .cal-day-header { font-size: 12px; color: #888; font-weight: bold; }
    .cal-day {
        height: 35px; width: 35px; line-height: 35px; margin: auto; border-radius: 50%; font-size: 14px; color: #1a1a24; font-weight: 500;
    }
    .cal-event {
        background-color: #1a1a24; color: #ffffff;
    }
    .cal-event-orange {
        background-color: #ffb185; color: #ffffff; box-shadow: 0 4px 10px rgba(255, 177, 133, 0.5);
    }
    </style>
    """, unsafe_allow_html=True)

# =========================
# PERRO MINIMALISTA (Reemplazo del Gato dibujado en SVG puro)
# =========================
PERRO_SVG = """
<div style="display: flex; justify-content: center; margin-bottom: 10px;">
    <svg width="180" height="180" viewBox="0 0 100 100">
        <path d="M 25 45 Q 10 20 30 15 Z" fill="#1a1a24"/>
        <path d="M 75 45 Q 90 20 70 15 Z" fill="#1a1a24"/>
        <path d="M 20 45 C 15 20, 35 15, 50 18 C 65 15, 85 20, 80 45 C 95 65, 85 90, 50 90 C 15 90, 5 65, 20 45 Z" fill="#1a1a24"/>
        <ellipse cx="35" cy="45" rx="9" ry="13" fill="white"/>
        <ellipse cx="65" cy="45" rx="9" ry="13" fill="white"/>
        <circle cx="35" cy="45" r="4" fill="#1a1a24"/>
        <circle cx="65" cy="45" r="4" fill="#1a1a24"/>
        <path d="M 45 65 Q 50 60 55 65 Q 58 75 50 78 Q 42 75 45 65 Z" fill="white"/>
        <circle cx="50" cy="65" r="2.5" fill="#1a1a24"/>
        <circle cx="20" cy="70" r="1.5" fill="white"/>
        <circle cx="80" cy="70" r="1.5" fill="white"/>
    </svg>
</div>
"""

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
# FUNCIONES PRINCIPALES (TU CÓDIGO INTACTO)
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
    base = " ".join(keywords[:3]).title()
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
    if lang == "en":
        tags_base = [f"custom {product}"[:20], f"{niche} gift"[:20], f"personalized {product}"[:20], f"gift for {niche}"[:20], "custom name gift"[:20], f"{keywords[0]} {product}"[:20] if keywords else "trendy gift", "unique present"[:20], f"funny {niche} gift"[:20], f"{niche} appreciation"[:20], "birthday gift"[:20], "customized present"[:20], f"best {niche} idea"[:20], "etsy trendy design"[:20]]
    else:
        tags_base = [f"{product} custom"[:20], f"regalo {niche}"[:20], f"{product} personal"[:20], f"regalo para {niche}"[:20], "regalo con nombre"[:20], f"{keywords[0]} {product}"[:20] if keywords else "regalo tendencia", "regalo unico"[:20], f"regalo gracioso"[:20], f"aprecio {niche}"[:20], "regalo cumpleanos"[:20], "detalle personalizado"[:20], f"idea {niche}"[:20], "etsy diseno"[:20]]
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
# MENÚ DE NAVEGACIÓN
# =========================
st.sidebar.markdown(PERRO_SVG, unsafe_allow_html=True)
st.sidebar.markdown("<h2 style='text-align:center;'>Etsy App</h2>", unsafe_allow_html=True)

menu = st.sidebar.radio("Navegación", [
    "🏠 Inicio & Calendario",
    "🔍 1. Subir Diseño (OCR)",
    "🛒 2. Catálogo y Nichos",
    "🚀 3. Generador SEO",
    "💬 4. Muestras Add-On",
    "💰 5. Calculadora Real",
    "⚖️ 6. Radar Legal",
    "📈 7. Auditoría de Tienda",
    "💡 8. Ideas y Tendencias"
])

# =========================
# PANTALLAS DE LA APP
# =========================

if menu == "🏠 Inicio & Calendario":
    st.markdown("<h1>Inicio</h1>", unsafe_allow_html=True)
    
    col1, col2 = st.columns([1, 1.2])
    
    with col1:
        st.markdown(f"""
        <div class="app-screen" style="text-align: center;">
            {PERRO_SVG}
            <h2>¡Hola de nuevo!</h2>
            <p style="color:#1a1a24 !important;">Estamos felices de verte. Tu mascota POD está lista para analizar tendencias.</p>
        </div>
        """, unsafe_allow_html=True)
        
    with col2:
        mes_actual = datetime.datetime.now().strftime("%B")
        st.markdown(f"""
        <div class="cal-box">
            <div class="cal-header">🗓️ {mes_actual.capitalize()} (Fechas Clave)</div>
            <div class="cal-grid">
                <div class="cal-day-header">L</div><div class="cal-day-header">M</div><div class="cal-day-header">X</div><div class="cal-day-header">J</div><div class="cal-day-header">V</div><div class="cal-day-header">S</div><div class="cal-day-header">D</div>
                <div></div><div></div><div></div><div class="cal-day">1</div><div class="cal-day">2</div><div class="cal-day">3</div><div class="cal-day">4</div>
                <div class="cal-day">5</div><div class="cal-day cal-event">6</div><div class="cal-day">7</div><div class="cal-day cal-event-orange">8</div><div class="cal-day">9</div><div class="cal-day">10</div><div class="cal-day">11</div>
                <div class="cal-day">12</div><div class="cal-day">13</div><div class="cal-day">14</div><div class="cal-day">15</div><div class="cal-day cal-event">16</div><div class="cal-day">17</div><div class="cal-day">18</div>
                <div class="cal-day">19</div><div class="cal-day">20</div><div class="cal-day">21</div><div class="cal-day">22</div><div class="cal-day">23</div><div class="cal-day cal-event-orange">24</div><div class="cal-day">25</div>
                <div class="cal-day">26</div><div class="cal-day">27</div><div class="cal-day">28</div><div class="cal-day">29</div><div class="cal-day">30</div><div class="cal-day">31</div><div></div>
            </div>
            <p style="text-align:center; font-size:11px; margin-top:10px; color:#888;">Naranja: Subida urgente. Negro: Fin de revisión.</p>
        </div>
        """, unsafe_allow_html=True)

elif menu == "🔍 1. Subir Diseño (OCR)":
    st.markdown("<h1>1️⃣ Analizar Diseño</h1>", unsafe_allow_html=True)
    st.markdown("<div class='app-screen'>", unsafe_allow_html=True)
    
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

        if st.button("Detectar texto (OCR)"):
            with st.spinner("Analizando imagen..."):
                texto = extraer_texto_ocr(reader, image)
                st.session_state["detected_text"] = texto

    if st.session_state["detected_text"]:
        st.subheader("Texto detectado")
        st.session_state["detected_text"] = st.text_area(
            "Edita el texto si el OCR cometió un error:",
            st.session_state["detected_text"],
            height=80
        )
        st.success("Texto guardado en memoria.")
    st.markdown("</div>", unsafe_allow_html=True)

elif menu == "🛒 2. Catálogo y Nichos":
    st.markdown("<h1>2️⃣ Perfil de Tienda</h1>", unsafe_allow_html=True)
    st.markdown("<div class='app-screen'>", unsafe_allow_html=True)
    
    col_tienda1, col_tienda2 = st.columns(2)
    with col_tienda1:
        tienda_seleccionada = st.radio("Selecciona la Tienda a trabajar:", ["🐾 Tienda POD Mascotas", "💌 Tienda Digital (Invitaciones)"])
    with col_tienda2:
        if tienda_seleccionada == "🐾 Tienda POD Mascotas":
            subnicho = st.selectbox("Selecciona el Sub-Nicho:", [
                "Mascotas Fallecidas (Memorial / Rainbow Bridge)", "Mascotas de Servicio Médico / Apoyo Emocional", "Mascotas Vivas (Cumpleaños / Uso Diario)", "Rescate / Adopción (Gotcha Day)"
            ])
            estilo_arte = st.selectbox("Estilo de Personalización:", [
                "Acuarela Digital (Watercolor Portrait)", "Line Art Minimalista", "Caricatura / Cartoon", "Pintura al Óleo Digital"
            ])
            st.session_state["niche"] = f"{subnicho} estilo {estilo_arte}"
        else:
            subnicho = st.selectbox("Selecciona el Sub-Nicho:", [
                "Fiesta de Divorcio / Inicio de Soltería", "Cumpleaños de Mascotas (Paw-ty)", "Conmemorativos / Celebración de Vida", "Despedida de Soltera Anti-Tradicional"
            ])
            estilo_arte = st.selectbox("Estilo Visual:", [
                "Acuarela Digital Elegante", "Sarcástico / Divertido (Texto Bold)", "Minimalista / Estético", "Boho / Floral"
            ])
            st.session_state["niche"] = f"{subnicho} estilo {estilo_arte}"

    st.markdown("---")
    st.subheader("3️⃣ Selección de Producto")
    if tienda_seleccionada == "🐾 Tienda POD Mascotas":
        productos_mascotas = ["Velveteen Plush Blanket", "White Ceramic Mug 15oz", "Square Canvas", "Pet Bandana", "Acrylic Plaque", "Gildan 18500 Hoodie"]
        cols_prod = st.columns(3)
        for idx, producto in enumerate(productos_mascotas):
            with cols_prod[idx % 3]:
                if st.button(producto): st.session_state["product"] = producto
    else:
        productos_digitales = ["Digital Invitation Canva", "Evite Mobile", "Printable Memorial Sign", "Digital Portrait File"]
        cols_dig = st.columns(2)
        for idx, producto in enumerate(productos_digitales):
            with cols_dig[idx % 2]:
                if st.button(producto): st.session_state["product"] = producto

    if st.session_state.get("product"):
        st.success(f"📦 Producto seleccionado: {st.session_state['product']}")
    st.markdown("</div>", unsafe_allow_html=True)

elif menu == "🚀 3. Generador SEO":
    st.markdown("<h1>🚀 Generador SEO</h1>", unsafe_allow_html=True)
    
    if st.session_state["detected_text"] and st.session_state.get("product"):
        if st.button("Generar Listado Optimizado"):
            st.session_state["generar_seo_ahora"] = True
            
        if st.session_state.get("generar_seo_ahora"):
            st.markdown("<div class='app-screen'>", unsafe_allow_html=True)
            product = st.session_state["product"]
            niche = st.session_state.get("niche", "General")
            keyword_text = st.session_state["detected_text"].strip()
            base_keywords = extraer_keywords_texto(keyword_text)
            if not base_keywords: base_keywords = [niche, product, "gift"]

            st.session_state["tags_generados"] = generar_tags_etsy(base_keywords, product, niche, "en")

            st.markdown("<h2>🇺🇸 SEO en Inglés (EUA)</h2>", unsafe_allow_html=True)
            titulos_en = generar_titulos_venta(base_keywords, product, niche, keyword_text, "en")
            for t, score in titulos_en:
                if score >= 95: st.success(f"⭐ **{score}% MATCH:**\n{t}")
                else: st.info(f"🔥 **{score}% MATCH:**\n{t}")

            st.subheader("🏷️ Etiquetas (Copia separadas por coma)")
            st.code(", ".join(st.session_state["tags_generados"]), language="text")
            
            st.subheader("📝 Descripción")
            st.code(generar_descripcion_vendedora(product, niche, keyword_text, "en"), language="text")
            st.markdown("</div>", unsafe_allow_html=True)
    else:
        st.warning("⚠️ Necesitas detectar texto y seleccionar un producto primero.")

elif menu == "💬 4. Muestras Add-On":
    st.markdown("<h1>💬 Flujo de Muestras</h1>", unsafe_allow_html=True)
    st.markdown("<div class='app-screen'>", unsafe_allow_html=True)
    st.markdown("<h4>Mensaje: Envío de Muestra (Cliente Pagó)</h4>", unsafe_allow_html=True)
    st.code("Hi [Nombre],\nThank you for your order! 💛\nI attached the proof (preview) for your custom piece. Please review the spelling and design. Reply 'APPROVED'.\nBest, [Tu Nombre]", language="text")
    
    st.markdown("---")
    st.markdown("<h4>💰 Listado Add-On ($4.99 USD)</h4>", unsafe_allow_html=True)
    st.markdown("**Título:**")
    st.code("Digital Proof Add-On for Custom Orders, Artwork Preview, Optional Digital Proof", language="text")
    st.markdown("**Tags:**")
    st.code("digital proof, artwork preview, add on listing, custom order proof", language="text")
    st.markdown("**Descripción:**")
    st.code("⚠️ THIS IS AN ADD-ON SERVICE, NOT A PHYSICAL PRODUCT.\nPurchase this listing IN ADDITION to your custom item to see a digital preview...", language="text")
    st.markdown("</div>", unsafe_allow_html=True)

elif menu == "💰 5. Calculadora Real":
    st.markdown("<h1>💰 Calculadora de Rentabilidad</h1>", unsafe_allow_html=True)
    st.markdown("<div class='app-screen'>", unsafe_allow_html=True)
    col_calc1, col_calc2 = st.columns(2)

    with col_calc1:
        costo_printify = st.number_input("Costo de Producción $", min_value=0.0, value=12.50, step=0.5)
        envio_printify = st.number_input("Costo de Envío Printify $", min_value=0.0, value=4.79, step=0.5)

    with col_calc2:
        precio_venta = st.number_input("Precio del Producto $", min_value=0.0, value=24.99, step=0.5)
        estrategia_envio = st.radio("Estrategia de Envío al Cliente:", ["Cobrar Envío Aparte", "Envío Gratis (Absorbido)"])
        cobro_envio_etsy = st.number_input("¿Cuánto cobrarás de envío? $", value=5.99) if estrategia_envio == "Cobrar Envío Aparte" else 0.0

    if st.button("Calcular Ganancia Real"):
        ingreso_total = precio_venta + cobro_envio_etsy
        etsy_fees = 0.45 + (ingreso_total * 0.095)
        costo_total = costo_printify + envio_printify + etsy_fees
        ganancia_neta = ingreso_total - costo_total
        margen_porcentaje = (ganancia_neta / ingreso_total) * 100 if ingreso_total > 0 else 0

        st.markdown("---")
        st.write(f"**Ingreso Bruto:** ${ingreso_total:.2f}")
        st.write(f"**Tarifas Etsy:** ${etsy_fees:.2f}")
        
        if margen_porcentaje >= 30:
            st.success(f"🔥 Ganancia Neta: **${ganancia_neta:.2f}** ({margen_porcentaje:.1f}%). Aprobado para Ads.")
        elif 15 <= margen_porcentaje < 30:
            st.warning(f"⚠️ Ganancia Neta: **${ganancia_neta:.2f}** ({margen_porcentaje:.1f}%). No uses Ads.")
        else:
            st.error(f"🚨 Ganancia Neta: **${ganancia_neta:.2f}** ({margen_porcentaje:.1f}%). Sube el precio.")
    st.markdown("</div>", unsafe_allow_html=True)

elif menu == "⚖️ 6. Radar Legal":
    st.markdown("<h1>⚖️ Radar Legal (Trademarks)</h1>", unsafe_allow_html=True)
    st.markdown("<div class='app-screen'>", unsafe_allow_html=True)
    
    texto_automatico = st.session_state.get("detected_text", "")
    if "tags_generados" in st.session_state: texto_automatico += " " + " ".join(st.session_state["tags_generados"])

    texto_a_revisar = st.text_area("Texto a revisar:", value=texto_automatico, height=100)

    TRADEMARK_BLACKLIST = ["disney", "marvel", "star wars", "nike", "harry potter", "velcro", "onesie", "jeep", "taylor swift", "stanley", "snoopy", "mickey", "nfl", "nba", "barbie", "lego", "tupperware", "taser", "chapstick", "super bowl", "peanuts", "pokemon", "hello kitty", "bluey", "shrek"]

    if st.button("Escanear Listado"):
        if texto_a_revisar:
            alertas = [marca for marca in TRADEMARK_BLACKLIST if marca in texto_a_revisar.lower()]
            if alertas: st.error(f"⚠️ ¡PELIGRO! Marcas registradas: **{', '.join(alertas).title()}**")
            else: st.success("✅ ¡Listado Limpio!")
        else: st.warning("No hay texto para revisar aún.")
    st.markdown("</div>", unsafe_allow_html=True)

elif menu == "📈 7. Auditoría de Tienda":
    st.markdown("<h1>📈 Auditoría de CSV</h1>", unsafe_allow_html=True)
    st.markdown("<div class='app-screen'>", unsafe_allow_html=True)
    uploaded_csv = st.file_uploader("Sube EtsySoldOrders.csv", type=["csv"])

    if uploaded_csv:
        try:
            df = pd.read_csv(uploaded_csv)
            item_col = [col for col in df.columns if 'Item Name' in col or 'Artículo' in col or 'Title' in col]
            qty_col = [col for col in df.columns if 'Quantity' in col or 'Cantidad' in col]
            if item_col and qty_col:
                ventas_por_producto = df.groupby(item_col[0])[qty_col[0]].sum().reset_index().sort_values(by=qty_col[0], ascending=False)
                st.subheader("🏆 Top 5 Productos (¡Escala estos!)")
                st.dataframe(ventas_por_producto.head(5), use_container_width=True)
                st.subheader("💀 Productos Muertos")
                st.dataframe(ventas_por_producto.tail(5), use_container_width=True)
            else: st.error("No se encontraron las columnas correctas.")
        except Exception as e: st.error(f"Error: {e}")
    st.markdown("</div>", unsafe_allow_html=True)

elif menu == "💡 8. Ideas y Tendencias":
    st.markdown("<h1>💡 Ideas, Tendencias y Cupones</h1>", unsafe_allow_html=True)
    st.markdown("<div class='app-screen'>", unsafe_allow_html=True)
    
    st.subheader("💌 Embudo de Retención (Top Sellers)")
    st.markdown("Ve a Marketing en Etsy y configura:")
    st.info("**1. Carrito Abandonado:** 15% OFF (VUELVE15)")
    st.success("**2. Post-Compra:** 20% OFF (GRACIAS20)")
    st.warning("**3. Favoritos:** 10% OFF (TUYO10)")
    st.markdown("---")
    
    col_idea1, col_idea2 = st.columns(2)
    with col_idea1:
        if st.button("Idea Mascotas POD"):
            mascotas = ["Perro 3 Patas", "Gato Ciego", "Perro Terapia", "Mascota Rescatada"]
            angulos = ["Memorial Acuarela", "Gotcha Day", "Arte Minimalista"]
            productos = ["Taza Interior Negro", "Manta Suave", "Adorno Acrílico"]
            st.success(f"**Nicho:** {random.choice(mascotas)}\n\n**Ángulo:** {random.choice(angulos)}\n\n**Producto:** {random.choice(productos)}")

    with col_idea2:
        if st.button("Idea Invitaciones"):
            eventos = ["Fiesta Divorcio", "Cumpleaños 15 Perro", "Adopción Padrastro", "Celebración de Vida"]
            estilos = ["Acuarela Floral", "Retro 70s", "Minimalista Blanco/Negro", "Periódico Vintage"]
            st.success(f"**Evento:** {random.choice(eventos)}\n\n**Estilo:** {random.choice(estilos)}")
    st.markdown("</div>", unsafe_allow_html=True)
