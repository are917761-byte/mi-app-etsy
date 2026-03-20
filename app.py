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
# CONFIGURACIÓN DE PÁGINA (ESTILO APP)
# =========================
st.set_page_config(page_title="Etsy POD Master", page_icon="🛍️", layout="wide")

# =========================
# INICIALIZACIÓN DE MEMORIA (SESSION STATE)
# =========================
if "product" not in st.session_state: st.session_state["product"] = None
if "detected_text" not in st.session_state: st.session_state["detected_text"] = ""
if "niche" not in st.session_state: st.session_state["niche"] = ""
if "tienda" not in st.session_state: st.session_state["tienda"] = ""
if "tags_generados" not in st.session_state: st.session_state["tags_generados"] = []
if "imagen_memoria" not in st.session_state: st.session_state["imagen_memoria"] = None
if "subnicho_memoria" not in st.session_state: st.session_state["subnicho_memoria"] = ""
if "estilo_memoria" not in st.session_state: st.session_state["estilo_memoria"] = ""

@st.cache_resource
def load_reader():
    return easyocr.Reader(["en", "es"], gpu=False)

reader = load_reader()

# =========================
# FUNCIONES NÚCLEO (IA Y SEO)
# =========================
def extraer_texto_ocr(reader, image):
    image_np = np.array(image)
    try:
        resultados = reader.readtext(image_np)
        return " ".join([r[1] for r in resultados if len(r) >= 2])
    except Exception as e:
        st.error(f"Error leyendo la imagen: {e}")
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
    texto, niche = (texto or "").lower(), (nicho or "").lower()
    recomendaciones = []
    if any(w in texto or w in niche for w in ["navidad", "christmas", "xmas", "catmas", "ornament"]):
        recomendaciones.extend(["Ceramic Ornament (Adorno Navideño)", "Gildan 18000 (Ugly Sweater Style)"])
    if any(w in niche for w in ["nurse", "teacher", "doctor", "lawyer"]):
        recomendaciones.extend(["Tote Bag (Para llevar al trabajo)", "Tumbler 20oz (Vasos para turnos largos)"])
    if any(w in niche for w in ["dog", "cat", "pet", "paw", "mascota"]):
        recomendaciones.extend(["Pet Bandana (Para el perrito)", "White Ceramic Mug 15oz (Para el dueño)"])
    if any(w in niche for w in ["mom", "grandma", "dad", "family", "fallecida", "memorial"]):
        recomendaciones.extend(["Velveteen Plush Blanket (Regalo acogedor)", "Acrylic Plaque (Recuerdo sentimental)", "Square Canvas"])
    if not recomendaciones:
        recomendaciones = ["Bella+Canvas 3001 (Camiseta Bestseller)", "White Ceramic Mug 11oz (Regalo Seguro)"]
    return list(set(recomendaciones))[:2]

def generar_titulos_venta(keywords, product, niche, lang="en"):
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
        tags = [f"custom {product}"[:20], f"{niche} gift"[:20], f"personalized {product}"[:20], f"gift for {niche}"[:20], "custom name gift"[:20], f"{kw} {product}"[:20], "unique present"[:20], f"funny {niche} gift"[:20], f"{niche} appreciation"[:20], "birthday gift"[:20], "customized present"[:20], f"best {niche} idea"[:20], "etsy trendy design"[:20]]
    else:
        tags = [f"{product} custom"[:20], f"regalo {niche}"[:20], f"{product} personal"[:20], f"regalo para {niche}"[:20], "regalo con nombre"[:20], f"{kw} {product}"[:20], "regalo unico"[:20], f"regalo gracioso"[:20], f"aprecio {niche}"[:20], "regalo cumpleanos"[:20], "detalle personalizado"[:20], f"idea {niche}"[:20], "etsy diseno"[:20]]
    return list(dict.fromkeys(tags))[:13]

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
If you are ordering a PHYSICAL product and would like to see the artwork before it goes to print, please purchase our "Digital Proof Add-On" listing alongside this item.

👕 PRODUCT DETAILS 
- Premium quality {product}. Vibrant, durable POD printing.
📦 SHIPPING: Processed in 2-5 business days. Tracking included!"""
    else:
        return f"🔥 ¡Da el regalo perfecto con este {product} Personalizado diseñado exclusivamente para {niche}s!\n..."

def mostrar_notificaciones_urgentes():
    mes_actual = datetime.datetime.now().month
    st.markdown("### 🔔 Alertas de Temporada (EUA)")
    if mes_actual in [2, 3]: st.error("🚨 **URGENTE:** Diseña para el **Día de la Madre**. ¡Sube tus lienzos y tazas HOY!")
    elif mes_actual in [4, 5]: st.warning("⏳ **ALERTA:** Prepara diseños para **Día del Padre** y **Graduaciones**.")
    elif mes_actual in [7, 8]: st.error("🎃 **URGENTE:** Sube tus diseños de **Halloween** AHORA (Etsy tarda en indexar).")
    elif mes_actual in [9, 10]: st.error("🎄 **Q4 ESTÁ AQUÍ:** Optimiza listados navideños y activa Etsy Ads. No subas cosas nuevas.")
    else: st.info("✅ Estás al día. Revisa la 'Máquina de Ideas' para planear tu próximo mes.")
    st.markdown("---")


# =========================
# MENÚ LATERAL (ESTILO APP)
# =========================
st.sidebar.image("https://upload.wikimedia.org/wikipedia/commons/thumb/a/aa/Etsy_logo.svg/1200px-Etsy_logo.svg.png", width=120)
st.sidebar.title("Navegación POD")

menu = st.sidebar.radio("Ir a:", [
    "📊 Dashboard y Alertas",
    "🔍 1. Subir Diseño (OCR)",
    "🛒 2. Catálogo y Tiendas",
    "🚀 3. Generador SEO",
    "💬 4. Flujo de Muestras (Add-On)",
    "💰 5. Calculadora Financiera",
    "⚖️ 6. Radar Legal",
    "💡 7. Máquina de Ideas"
])

st.sidebar.markdown("---")
st.sidebar.caption("POD Master v3.0 - SLP, MX 🇲🇽")


# =========================
# RUTEO DE PANTALLAS
# =========================

if menu == "📊 Dashboard y Alertas":
    st.title("Hola, Estratega 👋")
    mostrar_notificaciones_urgentes()
    
    col1, col2 = st.columns(2)
    with col1:
        st.info("🛒 **Tu Tienda Actual:** " + (st.session_state['tienda'] if st.session_state['tienda'] else "No seleccionada"))
        st.info("🎯 **Nicho de Trabajo:** " + (st.session_state['niche'] if st.session_state['niche'] else "No seleccionado"))
    with col2:
        st.success("📦 **Producto Activo:** " + (st.session_state['product'] if st.session_state['product'] else "No seleccionado"))
        st.warning("📝 **Texto en Memoria:** " + (st.session_state['detected_text'] if st.session_state['detected_text'] else "Vacío"))

elif menu == "🔍 1. Subir Diseño (OCR)":
    st.title("Visión Artificial (Extraer Texto)")
    st.markdown("Sube tu PNG transparente o Mockup. La IA leerá las letras para construir tu SEO.")
    
    # 1. Subidor de archivos con llave única cerrada correctamente
    uploaded_file = st.file_uploader("Sube tu diseño aquí:", type=["png", "jpg", "jpeg"], key="uploader_final")
    
    # 2. Guardar la imagen en la memoria si hay un archivo nuevo
    if uploaded_file is not None:
        image = Image.open(uploaded_file)
        if image.mode in ('RGBA', 'LA') or (image.mode == 'P' and 'transparency' in image.info):
            fondo_blanco = Image.new("RGB", image.size, (255, 255, 255))
            fondo_blanco.paste(image, mask=image.split()[-1])
            st.session_state["imagen_memoria"] = fondo_blanco
        else:
            st.session_state["imagen_memoria"] = image.convert("RGB")

    # 3. Mostrar la imagen SIEMPRE que esté guardada
    if "imagen_memoria" in st.session_state:
        st.image(st.session_state["imagen_memoria"], caption="Imagen lista para analizar", width=300)

        # 4. Botón para leer el texto con comillas bien cerradas
        if st.button("👁️ Leer Texto del Diseño", key="btn_ocr_final"):
            with st.spinner("Analizando pixeles..."):
                texto = extraer_texto_ocr(reader, st.session_state["imagen_memoria"])
                st.session_state["detected_text"] = texto

    # 5. Mostrar y editar el texto detectado
    if st.session_state.get("detected_text"):
        st.subheader("Texto detectado (Edítalo si es necesario):")
        # Campo de texto con llave cerrada correctamente
        nuevo_texto = st.text_input("Concepto Central:", st.session_state["detected_text"], key="input_text_final")
        
        if nuevo_texto != st.session_state["detected_text"]:
            st.session_state["detected_text"] = nuevo_texto
            
        st.success("✅ ¡Texto guardado! Ya puedes ir al menú '2. Catálogo y Tiendas'.")
