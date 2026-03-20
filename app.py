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

# Configuración inicial de la página
st.set_page_config(page_title="Etsy AI Listing Generator", layout="wide")

st.title("🛍️ Etsy AI Listing Generator (Modo Estratega POD)")

# =========================
# SESSION STATE INIT
# =========================
if "product" not in st.session_state:
    st.session_state["product"] = None
if "text" not in st.session_state:
    st.session_state["text"] = ""
if "niche" not in st.session_state:
    st.session_state["niche"] = "General"
if "detected_text" not in st.session_state:
    st.session_state["detected_text"] = ""
if "category" not in st.session_state:
    st.session_state["category"] = None

@st.cache_resource
def load_reader():
    return easyocr.Reader(["en", "es"], gpu=False)

reader = load_reader()

# =========================
# FUNCIONES PRINCIPALES
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
    
    # Lógica del Estratega POD
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

    # Si el nicho es muy raro, damos los 2 bestsellers mundiales
    if not recomendaciones:
        recomendaciones = ["Bella+Canvas 3001 (Camiseta Bestseller)", "White Ceramic Mug 11oz (Regalo Seguro)"]
        
    return list(set(recomendaciones))[:2]

# --- MÓDULOS DE SEO (ESTILO EXPERTO POD) ---

def generar_titulos_venta(keywords, product, niche, texto_detectado, lang="en"):
    base = " ".join(keywords[:3]).title()
    prod = product.title() if product else "Custom Item"
    nch = niche.title() if niche else "Everyone"
    
    # Asignamos porcentajes de efectividad basados en la estructura del título
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
    
    # Cortamos a 140 caracteres manteniendo el porcentaje intacto
    return [(t[:140].strip(', '), score) for t, score in titulos]

def generar_tags_etsy(keywords, product, niche, lang="en"):
    if lang == "en":
        tags_base = [
            f"custom {product}"[:20], f"{niche} gift"[:20], f"personalized {product}"[:20],
            f"gift for {niche}"[:20], "custom name gift"[:20], f"{keywords[0]} {product}"[:20] if keywords else "trendy gift",
            "unique present"[:20], f"funny {niche} gift"[:20], f"{niche} appreciation"[:20],
            "birthday gift"[:20], "customized present"[:20], f"best {niche} idea"[:20], "etsy trendy design"[:20]
        ]
    else:
        tags_base = [
            f"{product} custom"[:20], f"regalo {niche}"[:20], f"{product} personal"[:20],
            f"regalo para {niche}"[:20], "regalo con nombre"[:20], f"{keywords[0]} {product}"[:20] if keywords else "regalo tendencia",
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
# UI DE LA APLICACIÓN
# =========================

# -----------------------------
# 1. SUBIR DISEÑO
# -----------------------------
st.header("1️⃣ Subir diseño")
uploaded_file = st.file_uploader("Sube tu diseño para analizarlo", type=["png", "jpg", "jpeg"])

if uploaded_file:
    # 1. Abrimos la imagen original tal como viene
    image = Image.open(uploaded_file)
    
    # 2. MAGIA PARA FONDOS TRANSPARENTES (PNG)
    if image.mode in ('RGBA', 'LA') or (image.mode == 'P' and 'transparency' in image.info):
        # Creamos un fondo blanco puro del mismo tamaño
        fondo_blanco = Image.new("RGB", image.size, (255, 255, 255))
        # Pegamos tu diseño transparente sobre el fondo blanco
        fondo_blanco.paste(image, mask=image.split()[-1])
        image = fondo_blanco
    else:
        # Si ya es un JPG normal, la dejamos igual
        image = image.convert("RGB")

    st.image(image, caption="Vista previa", width=300)

    if st.button("Detectar texto (OCR)"):
        with st.spinner("Analizando imagen..."):
            texto = extraer_texto_ocr(reader, image)
            st.session_state["detected_text"] = texto

if st.session_state["detected_text"]:
    st.subheader("Texto detectado")
    st.session_state["detected_text"] = st.text_area(
        "Edita el texto si el OCR cometió un error (Esto será la base de tu SEO):",
        st.session_state["detected_text"],
        height=80
    )
    st.success("Texto listo para análisis.")

# -----------------------------
# 2. TUS TIENDAS Y SUB-NICHOS ESTRELLA
# -----------------------------
st.header("2️⃣ Perfil de Tienda y Micro-Nicho")

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

st.info(f"🎯 **Enfoque actual:** {tienda_seleccionada} ➔ {subnicho} ({estilo_arte})")

# -----------------------------
# 3. SELECCIÓN DE PRODUCTO
# -----------------------------
st.header("3️⃣ Selección de Producto")

if tienda_seleccionada == "🐾 Tienda POD Mascotas":
    st.write("**Catálogo Estratégico Printify:**")
    # Productos específicos para tus nichos de mascotas
    productos_mascotas = [
        "Velveteen Plush Blanket (Ideal para Memorial)",
        "White Ceramic Mug 15oz (Dueños de Apoyo Emocional)",
        "Square Canvas (Retrato Acuarela Premium)",
        "Pet Bandana (Cumpleaños Mascota)",
        "Acrylic Plaque (Memorial Transparente)",
        "Gildan 18500 Hoodie (Ropa de Dueño)"
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

# -----------------------------
# 4. GENERADOR SEO ETSY (LA MAGIA)
# -----------------------------
st.header("4️⃣ Generador SEO Experto para Etsy")
if st.session_state["detected_text"] and st.session_state.get("product"):
    if st.button("🚀 Generar Listado Optimizado"):
        with st.spinner("Creando SEO con intención de regalo..."):
            
            product = st.session_state["product"]
            niche = st.session_state.get("niche", "General")
            keyword_text = st.session_state["detected_text"].strip()
            base_keywords = extraer_keywords_texto(keyword_text)
            if not base_keywords: base_keywords = [niche, product, "gift"]

            # Guardamos los tags en inglés en la sesión para el Radar Legal
            st.session_state["tags_generados"] = generar_tags_etsy(base_keywords, product, niche, "en")

            # Crear pestañas de idiomas
            tab_en, tab_es = st.tabs(["🇺🇸 Inglés (Copia esto en Etsy EUA)", "🇪🇸 Español (Para tu Referencia)"])

            with tab_en:
                st.info("⚠️ COPIA ESTOS DATOS EN ETSY. El mercado de EUA busca exclusivamente en inglés.")
                
                st.subheader("📌 Títulos Optimizados")
                st.markdown("Copia el título con el mayor porcentaje de coincidencia estratégica:")
                titulos_en = generar_titulos_venta(base_keywords, product, niche, keyword_text, "en")
                for t, score in titulos_en:
                    if score >= 95:
                        st.success(f"⭐ **{score}% MATCH (Mejor Opción):**\n\n{t}")
                    else:
                        st.info(f"🔥 **{score}% MATCH:**\n\n{t}")

                st.subheader("🏷️ 13 Etiquetas (Tags en Inglés)")
                tags_en = st.session_state["tags_generados"]
                for tag in tags_en:
                    st.markdown(f"✅ `{tag}`")
                st.caption("Copia todos de un solo clic para pegarlos en Etsy (separados por coma):")
                st.code(", ".join(tags_en), language="text")
                
                st.subheader("📝 Descripción de Alta Conversión")
                st.markdown("Incluye la estrategia de *Muestra Digital Opcional (Proof Add-on)* para aumentar tu margen.")
                st.code(generar_descripcion_vendedora(product, niche, keyword_text, "en"), language="text")

            with tab_es:
                st.info("💡 Usa esto solo para entender la estrategia detrás del SEO en inglés.")
                st.subheader("📌 Títulos Optimizados")
                titulos_es = generar_titulos_venta(base_keywords, product, niche, keyword_text, "es")
                for t, score in titulos_es:
                    st.write(f"**{score}% MATCH:** {t}")

                st.subheader("🏷️ 13 Etiquetas (Tags en Español)")
                tags_es = generar_tags_etsy(base_keywords, product, niche, "es")
                st.code(", ".join(tags_es), language="text")
                
                st.subheader("📝 Descripción")
                st.text_area("Descripción (ES):", generar_descripcion_vendedora(product, niche, keyword_text, "es"), height=300)
else:
    st.warning("⚠️ Necesitas detectar el texto de una imagen y seleccionar un producto primero.")

# -----------------------------
# 4.5. FLUJO DE APROBACIÓN (PROOFING WORKFLOW) Y ADD-ON
# -----------------------------
st.header("💬 Flujo de Muestras y Add-On (Monetización)")
st.markdown("Automatiza tu atención al cliente y monetiza las revisiones de diseño. Los Top Sellers no dan su tiempo de revisión gratis.")

tab_proof1, tab_proof2, tab_addon = st.tabs([
    "💬 Mensaje: Envío de Muestra", 
    "⏰ Mensaje: Recordatorio 24h", 
    "💰 Generador: Listado Add-On"
])

with tab_proof1:
    st.markdown("**Usa esto cuando el cliente PAGA por la muestra o compra un producto digital caro (como una invitación personalizada).**")
    st.code("""Hi [Nombre del Cliente],

Thank you so much for your order! 💛 

I have finished the digital design for your custom piece. I have attached the proof (preview) to this message so you can see exactly how it will look.

Please review the spelling and the design. If everything looks perfect, just reply with "APPROVED" and I will send it straight to production! If you need any minor tweaks, let me know.

Best regards,
[Tu Nombre]""", language="text")

with tab_proof2:
    st.markdown("**Usa esto si el cliente no responde en 24 horas (Para evitar que Etsy te penalice por envíos tardíos).**")
    st.code("""Hi [Nombre del Cliente],

Just checking in! I sent your design proof yesterday. 

To ensure your order arrives on time, please let me know if the design is approved by [Hora/Fecha]. If I don't hear back by then, I will proceed with printing as shown in the proof to avoid any shipping delays.

Thank you!""", language="text")

with tab_addon:
    st.info("💡 **ESTRATEGIA:** Crea un ÚNICO listado en tu tienda con esta información. Ponle un precio de $2.99 a $4.99 USD y configúralo como 'Producto Digital' (Digital Download).")
    
    st.subheader("📸 Sugerencia de Imagen (Mockup)")
    st.markdown("Crea una imagen sencilla y estética en Canva. Fondo de color pastel, y letras grandes y legibles que digan:\n\n**'DIGITAL PROOF ADD-ON. See your artwork before it prints!'**\n*(Agrega un ícono de una lupa o un checkmark ✅)*.")
    
    st.subheader("📌 Título del Listado en Inglés")
    st.code("Digital Proof Add-On for Custom Orders, Artwork Preview, See Design Before Printing, Optional Digital Proof, Pet Portrait Proof Add On", language="text")
    
    st.subheader("🏷️ 13 Etiquetas (Tags)")
    st.code("digital proof, artwork preview, add on listing, see before printing, custom order proof, design preview, optional add on, pet portrait proof, custom gift proof, digital download, rush proof, approval required, order upgrade", language="text")
    
    st.subheader("📝 Descripción del Listado (Copia y Pega)")
    st.code("""⚠️ PLEASE READ: THIS IS AN ADD-ON SERVICE, NOT A PHYSICAL PRODUCT.

Purchase this listing IN ADDITION to your custom physical product if you wish to see a digital preview (proof) of the artwork before it is sent to production. 

To keep our prices low and production times incredibly fast, proofs are not automatically included with our standard physical items. Our expert artists use their best judgment to create stunning pieces based on your photos and notes. However, if you prefer to review and approve the design first to request minor tweaks, this add-on is for you!

✨ HOW IT WORKS ✨
1. Add your physical custom item (mug, canvas, blanket, etc.) to your cart.
2. Add this "Digital Proof Add-On" listing to your cart as well.
3. Complete your checkout.
4. Within 24-48 hours, we will send you a digital preview of your design via Etsy Messages.
5. You can approve it or request one (1) minor revision. 

*Note: Purchasing a proof may extend your final delivery date slightly, as we will wait for your approval before printing.*""", language="text")
    
# -----------------------------
# 5. RECURSOS EXTRA (MOCKUPS & TENDENCIAS)
# -----------------------------
st.header("5️⃣ Recursos Rápidos")
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

# -----------------------------
# 6. CALCULADORA DE RENTABILIDAD POD AVANZADA
# -----------------------------
st.header("💰 Calculadora de Rentabilidad (Estrategia de Envío)")
st.markdown("Calcula tu ganancia real comparando la estrategia de **Envío Gratis** vs **Cobrar Envío**.")

col_calc1, col_calc2 = st.columns(2)

with col_calc1:
    st.subheader("📦 Costos (Printify)")
    costo_printify = st.number_input("Costo de Producción $", min_value=0.0, value=12.50, step=0.5)
    envio_printify = st.number_input("Costo de Envío Printify $", min_value=0.0, value=4.79, step=0.5)

with col_calc2:
    st.subheader("🛍️ Ingresos (Etsy)")
    precio_venta = st.number_input("Precio del Producto $", min_value=0.0, value=24.99, step=0.5)
    estrategia_envio = st.radio("Estrategia de Envío al Cliente:", ["Cobrar Envío Aparte", "Envío Gratis (Absorbido)"])
    
    if estrategia_envio == "Cobrar Envío Aparte":
        cobro_envio_etsy = st.number_input("¿Cuánto le cobrarás de envío al cliente? $", min_value=0.0, value=5.99, step=0.5)
    else:
        cobro_envio_etsy = 0.0
        st.info("💡 Consejo: Asegúrate de que el Precio del Producto sea lo suficientemente alto para cubrir tu costo de producción Y el envío de Printify.")

if st.button("📊 Calcular Ganancia Real"):
    # Ingreso Total (Lo que paga el cliente en total)
    ingreso_total = precio_venta + cobro_envio_etsy
    
    # Tarifas Etsy EUA (9.5% del total + $0.45 fijos por listado y proc. de pago)
    etsy_fees = 0.45 + (ingreso_total * 0.095)
    
    # Costo Total (Lo que tú pagas a Printify + Lo que se queda Etsy)
    costo_total = costo_printify + envio_printify + etsy_fees
    
    # Ganancia Neta
    ganancia_neta = ingreso_total - costo_total
    margen_porcentaje = (ganancia_neta / ingreso_total) * 100 if ingreso_total > 0 else 0

    st.markdown("---")
    col_res1, col_res2, col_res3 = st.columns(3)
    col_res1.metric("Ingreso Bruto (Paga el Cliente)", f"${ingreso_total:.2f}")
    col_res2.metric("Tarifas Retenidas por Etsy", f"${etsy_fees:.2f}")
    col_res3.metric("Costo Printify (Prod + Envío)", f"${(costo_printify + envio_printify):.2f}")
    
    st.write("") # Espaciador visual
    
    col_res4, col_res5 = st.columns(2)
    if margen_porcentaje >= 30:
        col_res4.metric("Ganancia Neta (Directo a tu bolsa)", f"${ganancia_neta:.2f}", "Margen Excelente")
        col_res5.metric("Margen de Beneficio", f"{margen_porcentaje:.1f}%", "Aprobado para Escalar")
        st.success("🔥 ¡Estrategia sólida! Tienes un margen mayor al 30%. Tienes espacio para pagar Etsy Ads ($3 al día) y seguir ganando dinero.")
    elif 15 <= margen_porcentaje < 30:
        col_res4.metric("Ganancia Neta", f"${ganancia_neta:.2f}")
        col_res5.metric("Margen de Beneficio", f"{margen_porcentaje:.1f}%", delta_color="off")
        st.warning("⚠️ Margen ajustado. Está bien para conseguir tus primeras ventas y reseñas (Reviews), pero NO uses Ads con este producto porque terminarás perdiendo dinero.")
    else:
        col_res4.metric("Ganancia Neta", f"${ganancia_neta:.2f}", "-Riesgo de Pérdida")
        col_res5.metric("Margen de Beneficio", f"{margen_porcentaje:.1f}%", "-Cambia tu estrategia")
        st.error("🚨 ¡Alerta roja! Estás ganando muy poco o directamente trabajando gratis. Sube el precio del producto o cobra el envío.")

# -----------------------------
# 7. RADAR LEGAL (TRADEMARKS & COPYRIGHT)
# -----------------------------
st.header("🚨 Radar Legal y Protección de Tienda")
st.markdown("Evita suspensiones. La IA cruzará tu texto detectado y tus tags generados con nuestra Lista Negra.")

# Autocompletar con el texto detectado y los tags si ya se generaron
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

# -----------------------------
# 8. CALENDARIO POD Y RETENCIÓN DE CLIENTES
# -----------------------------
st.header("📅 Calendario POD y Retención (Estrategia EUA)")
st.markdown("En Print on Demand, **diseñamos con 2 a 3 meses de anticipación**.")

tab_cal, tab_cup = st.tabs(["⏰ Calendario de Subidas (Cuándo Diseñar)", "💌 Estrategia de Cupones (Fidelización)"])

with tab_cal:
    st.subheader("El Ciclo de Vida del Regalo en EUA")
    col_q1, col_q2 = st.columns(2)
    
    with col_q1:
        st.markdown("""
        **Q1 (Ene - Mar)**
        * **Enero:** Diseña para *Valentine's Day* y *St. Patrick's Day*.
        * **Febrero:** Sube diseños de *Easter* y *Spring*.
        * **Marzo:** ¡URGENTE! Diseña para *Mother's Day*.
        
        **Q2 (Abr - Jun)**
        * **Abril:** Sube diseños de *Father's Day* y *Graduaciones*.
        * **Mayo:** Diseña para *Teacher Appreciation* y *Nurse Week*.
        * **Junio:** Sube nichos de verano (Camping, Julio 4th).
        """)

    with col_q2:
        st.markdown("""
        **Q3 (Jul - Sep)**
        * **Julio:** Diseña para *Back to School*.
        * **Agosto:** Sube *Halloween* (El algoritmo necesita tiempo).
        * **Septiembre:** Sube *Thanksgiving* y prepara *Navidad*.
        
        **Q4 (Oct - Dic) - ¡Temporada Alta!**
        * **Octubre:** Todo debe ser *Christmas* y *Ugly Sweaters*.
        * **Noviembre:** Black Friday / Cyber Monday.
        * **Diciembre:** Prepara diseños de *New Year*.
        """)

with tab_cup:
    st.subheader("El Embudo de Retención (Estilo Top Sellers)")
    st.markdown("Ve a **Marketing > Sales and Discounts** en Etsy y configura estas 3 campañas:")
    st.info("**1. Carrito Abandonado (Abandoned Cart)** - 15% OFF (Código: VUELVE15)")
    st.success("**2. Agradecimiento Post-Compra (Thank You)** - 20% OFF (Código: GRACIAS20)")
    st.warning("**3. Favoritos (Recently Favorited)** - 10% OFF (Código: TUYO10)")

# -----------------------------
# 9. AUDITORÍA DE TIENDA (ANÁLISIS DE CSV)
# -----------------------------
st.header("📈 Auditoría de Tienda (Identifica tus Ganadores)")
st.markdown("Ve a **Etsy > Settings > Options > Download Data > Orders** y sube ese archivo CSV aquí para descubrir qué escalar.")

uploaded_csv = st.file_uploader("Sube tu archivo CSV de Pedidos (EtsySoldOrders.csv)", type=["csv"])

if uploaded_csv:
    try:
        df = pd.read_csv(uploaded_csv)
        item_col = [col for col in df.columns if 'Item Name' in col or 'Artículo' in col or 'Title' in col]
        qty_col = [col for col in df.columns if 'Quantity' in col or 'Cantidad' in col]
        
        if item_col and qty_col:
            item_name = item_col[0]
            qty_name = qty_col[0]
            
            ventas_por_producto = df.groupby(item_name)[qty_name].sum().reset_index()
            ventas_por_producto = ventas_por_producto.sort_values(by=qty_name, ascending=False)
            
            st.subheader("🏆 Tus Top 5 Productos (¡Escala estos!)")
            st.markdown("*Estrategia: Pon estos diseños en OTROS productos (ej. de Taza a Sudadera).*")
            st.dataframe(ventas_por_producto.head(5), use_container_width=True)
            
            st.subheader("💀 Productos Muertos (Mátalos o re-optimízalos)")
            st.markdown("*Estrategia: Cambia el Mockup o el SEO. Si no venden en 2 meses más, bórralos.*")
            st.dataframe(ventas_por_producto.tail(5), use_container_width=True)
            
        else:
            st.error("No se encontraron las columnas de 'Item Name' y 'Quantity' en el CSV.")
            
    except Exception as e:
        st.error(f"Hubo un error al leer el archivo. Detalle: {e}")

# -----------------------------
# 10. RADAR DINÁMICO DE TENDENCIAS (FUTURO)
# -----------------------------
st.header("🔮 Radar Dinámico de Tendencias (¿Qué diseñar HOY?)")

mes_actual = datetime.datetime.now().month
# Sumamos 2 meses para saber qué temporada estamos preparando
mes_objetivo = (mes_actual + 2) % 12
if mes_objetivo == 0: mes_objetivo = 12

meses = {
    1: "Enero", 2: "Febrero", 3: "Marzo", 4: "Abril", 5: "Mayo", 6: "Junio",
    7: "Julio", 8: "Agosto", 9: "Septiembre", 10: "Octubre", 11: "Noviembre", 12: "Diciembre"
}

st.markdown(f"Estamos en **{meses[mes_actual]}**. El algoritmo de Etsy tarda semanas en indexar SEO. Por lo tanto, hoy deberías estar subiendo diseños para la demanda masiva de **{meses[mes_objetivo]}** y el mes siguiente.")

tendencias_futuras = {
    1: ["St. Patrick's Day (Marzo)", "Easter / Pascua (Marzo/Abril)", "Spring Break (Marzo)"],
    2: ["Mother's Day (Mayo - ¡URGENTE!)", "Cinco de Mayo", "Graduaciones Tempranas"],
    3: ["Teacher Appreciation (Mayo)", "Nurse Week (Mayo)", "Father's Day (Junio - Empieza a diseñar)"],
    4: ["Father's Day (Junio)", "Pride Month (Junio)", "Summer Vacations / Family Trips (Junio/Julio)"],
    5: ["Julio 4th (Independencia EUA)", "Camping / Lake Life (Julio)", "Bachelorette Parties (Verano)"],
    6: ["Back to School (Agosto/Septiembre)", "Fall / Otoño temprano (Hojas, Calabazas)", "Halloween (Agosto - Empieza ya)"],
    7: ["Halloween (Octubre)", "Thanksgiving / Friendsgiving (Noviembre)", "Autumn Festivals"],
    8: ["Christmas / Ugly Sweaters (Diciembre - Sube todo en Q4)", "Navidad para Mascotas"],
    9: ["Black Friday Prep", "Regalos Navideños Personalizados", "Winter / Nieve"],
    10: ["New Year's Eve (Enero)", "Fitness / Gym Goals (Para Enero)", "Valentine's Day (Febrero - Prepárate)"],
    11: ["Valentine's Day (Febrero)", "Super Bowl / Sports (Febrero)"],
    12: ["Valentine's Day (Febrero)", "100 Days of School", "Mardi Gras"]
}

col_t1, col_t2 = st.columns(2)
with col_t1:
    st.success(f"**NICHOS EN AUGE PARA SUBIR HOY:**")
    for tendencia in tendencias_futuras[mes_actual]:
        st.write(f"✅ {tendencia}")

with col_t2:
    st.warning("**ESTILO GRÁFICO EN TENDENCIA (EUA):**")
    st.write("🎨 Retro Wavy Text (Estilo años 70s)")
    st.write("🎨 Minimalist Line Art (Elegante y barato de imprimir)")
    st.write("🎨 Faux Embroidery (Efecto bordado impreso)")
    st.write("🎨 Bootleg Rap 90s (Camisetas vintage personalizadas con fotos)")

    # -----------------------------
# 11. GENERADOR DE IDEAS (LA MATRIZ DE NICHOS)
# -----------------------------
import random
st.header("💡 Máquina de Ideas (Micro-Nichos Inexplorados)")
st.markdown("Haz clic en el botón para generar combinaciones únicas basadas en las matrices de éxito de tiendas multimillonarias.")

col_idea1, col_idea2 = st.columns(2)

with col_idea1:
    if st.button("🎲 Generar Idea para POD Mascotas"):
        mascotas = ["Perro de Tres Patas", "Gato Ciego", "Perro de Terapia para Autismo", "Mascota Rescatada de Refugio", "Hurón de Apoyo Emocional", "Perro Policia Retirado", "Golden Retriever Senior", "Gato Negro (Mala Suerte Revertida)"]
        angulos = ["Memorial Acuarela", "Regalo de Gotcha Day (Adopción)", "Arte de Línea Minimalista", "Diseño Divertido de 'Empleado del Mes'", "Retrato Estilo Renacentista"]
        productos = ["Taza de Café con Interior Negro", "Manta Súper Suave", "Adorno Navideño Acrílico", "Vaso Térmico para Enfermeras", "Sudadera Premium"]
        
        st.success(f"**Idea Generada:**")
        st.write(f"**Nicho:** {random.choice(mascotas)}")
        st.write(f"**Ángulo:** {random.choice(angulos)}")
        st.write(f"**Producto:** {random.choice(productos)}")
        st.caption("Estrategia: Busca esto en Etsy. Si hay menos de 500 resultados, ¡hazlo hoy!")

with col_idea2:
    if st.button("🎲 Generar Idea para Invitaciones"):
        eventos = ["Fiesta de Divorcio", "Cumpleaños 15 de Perro Senior", "Adopción Oficial de Padrastro", "Celebración de Vida (Funeral Alegre)", "Fiesta de Quitarse los Brackets", "Fiesta de Vasectomía", "Aniversario de Supervivencia al Cáncer"]
        estilos = ["Acuarela Floral Oscura", "Tipografía Retro Años 70s", "Minimalista Blanco y Negro", "Estilo Periódico Vintage", "Boleto de Avión/Concierto Falso"]
        
        st.success(f"**Idea Generada:**")
        st.write(f"**Evento:** {random.choice(eventos)}")
        st.write(f"**Estilo Visual:** {random.choice(estilos)}")
        st.caption("Estrategia: El mercado de 'Anti-Fiestas' o celebraciones no convencionales está explotando en TikTok. Capitaliza esto.")
