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
# CONFIGURACIÓN INICIAL
# =========================
st.set_page_config(page_title="Etsy AI Listing Generator", layout="wide", page_icon="🛍️")

st.title("🛍️ Etsy AI Listing Generator (Modo Estratega POD)")

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
    if any(w in niche for w in ["mom", "grandma", "dad", "family", "fallecida", "memorial"]):
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
# UI DE LA APLICACIÓN
# =========================

# -----------------------------
# 1. SUBIR DISEÑO
# -----------------------------
st.header("1️⃣ Subir diseño")
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
        "Edita el texto si el OCR cometió un error (Esto será la base de tu SEO):",
        st.session_state["detected_text"],
        height=80
    )
    st.success("Texto listo para análisis.")

st.markdown("---")

# -----------------------------
# 2. PERFIL DE TIENDA
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

st.markdown("---")

# -----------------------------
# 3. SELECCIÓN DE PRODUCTO
# -----------------------------
st.header("3️⃣ Selección de Producto")

if tienda_seleccionada == "🐾 Tienda POD Mascotas":
    st.write("**Catálogo Estratégico Printify:**")
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
            if st.button(producto): st.session_state["product"] = producto
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
            if st.button(producto): st.session_state["product"] = producto

if st.session_state.get("product"):
    st.success(f"📦 Producto seleccionado: {st.session_state['product']}")

st.markdown("---")

# -----------------------------
# 4. GENERADOR SEO ETSY
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

            st.session_state["tags_generados"] = generar_tags_etsy(base_keywords, product, niche, "en")

            tab_en, tab_es = st.tabs(["🇺🇸 Inglés (Copia esto en Etsy EUA)", "🇪🇸 Español (Para tu Referencia)"])

            with tab_en:
                st.info("⚠️ COPIA ESTOS DATOS EN ETSY. El mercado de EUA busca exclusivamente en inglés.")
                st.subheader("📌 Títulos Optimizados")
                titulos_en = generar_titulos_venta(base_keywords, product, niche, keyword_text, "en")
                for t, score in titulos_en:
                    if score >= 95: st.success(f"⭐ **{score}% MATCH (Mejor Opción):**\n\n{t}")
                    else: st.info(f"🔥 **{score}% MATCH:**\n\n{t}")

                st.subheader("🏷️ 13 Etiquetas (Tags en Inglés)")
                tags_en = st.session_state["tags_generados"]
                for tag in tags_en: st.markdown(f"✅ `{tag}`")
                st.code(", ".join(tags_en), language="text")
                
                st.subheader("📝 Descripción de Alta Conversión")
                st.code(generar_descripcion_vendedora(product, niche, keyword_text, "en"), language="text")

            with tab_es:
                st.info("💡 Usa esto solo para entender la estrategia.")
                st.subheader("📌 Títulos Optimizados")
                titulos_es = generar_titulos_venta(base_keywords, product, niche, keyword_text, "es")
                for t, score in titulos_es: st.write(f"**{score}% MATCH:** {t}")
                st.subheader("🏷️ 13 Etiquetas (Tags en Español)")
                tags_es = generar_tags_etsy(base_keywords, product, niche, "es")
                st.code(", ".join(tags_es), language="text")
                st.subheader("📝 Descripción")
                st.text_area("Descripción (ES):", generar_descripcion_vendedora(product, niche, keyword_text, "es"), height=300)
else:
    st.warning("⚠️ Necesitas detectar el texto de una imagen y seleccionar un producto primero.")

st.markdown("---")

# -----------------------------
# 4.5. FLUJO DE MUESTRAS Y ADD-ON
# -----------------------------
st.header("💬 4.5 Flujo de Muestras y Add-On (Monetización)")
tab_proof1, tab_proof2, tab_addon = st.tabs(["💬 Envío de Muestra", "⏰ Recordatorio 24h", "💰 Generador Add-On"])

with tab_proof1:
    st.code("""Hi [Nombre del Cliente],\nThank you so much for your order! 💛 \nI have attached the proof (preview) to this message so you can see exactly how it will look.\nPlease review the spelling and the design. If everything looks perfect, just reply with "APPROVED"!\nBest regards,\n[Tu Nombre]""", language="text")

with tab_proof2:
    st.code("""Hi [Nombre del Cliente],\nJust checking in! I sent your design proof yesterday. \nTo ensure your order arrives on time, please let me know if the design is approved by [Hora/Fecha]. If I don't hear back by then, I will proceed with printing as shown in the proof to avoid any shipping delays.\nThank you!""", language="text")

with tab_addon:
    st.info("💡 Crea un ÚNICO listado en tu tienda. Ponle un precio de $2.99 a $4.99 USD como 'Producto Digital'.")
    st.subheader("📌 Título del Listado")
    st.code("Digital Proof Add-On for Custom Orders, Artwork Preview, See Design Before Printing, Optional Digital Proof", language="text")
    st.subheader("🏷️ Tags")
    st.code("digital proof, artwork preview, add on listing, see before printing, custom order proof, design preview, optional add on", language="text")
    st.subheader("📝 Descripción")
    st.code("""⚠️ PLEASE READ: THIS IS AN ADD-ON SERVICE, NOT A PHYSICAL PRODUCT.\nPurchase this listing IN ADDITION to your custom physical product if you wish to see a digital preview (proof) of the artwork before it is sent to production...""", language="text")

st.markdown("---")

# -----------------------------
# 5. RECURSOS EXTRA (MOCKUPS)
# -----------------------------
st.header("5️⃣ Recursos Rápidos (Placeit Mockups)")
col_m1, col_m2 = st.columns(2)
with col_m1:
    st.markdown("[👕 T-shirt / Camiseta](https://placeit.net/c/mockups/stages/t-shirt-mockup)")
    st.markdown("[🧥 Hoodie / Sudadera](https://placeit.net/c/mockups/stages/hoodie-mockup)")
    st.markdown("[☕ Mug / Taza Cerámica](https://placeit.net/c/mockups/stages/mug-mockup)")
    st.markdown("[🥤 Tumbler / Vaso Térmico](https://placeit.net/c/mockups/stages/tumbler-mockup)")
with col_m2:
    st.markdown("[🖼️ Canvas / Lienzo](https://placeit.net/c/mockups/stages/canvas-mockup)")
    st.markdown("[🛌 Blanket / Cobija](https://placeit.net/c/mockups/stages/blanket-mockup)")
    st.markdown("[🎄 Ornament / Adorno](https://placeit.net/c/mockups/stages/ornament-mockup)")
    st.markdown("[👜 Tote Bag / Bolsa](https://placeit.net/c/mockups/stages/tote-bag-mockup)")

st.markdown("---")

# -----------------------------
# 6. CALCULADORA DE RENTABILIDAD POD
# -----------------------------
st.header("💰 6. Calculadora de Rentabilidad (Estrategia de Envío)")
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
    col_res1.metric("Ingreso Bruto (Cliente)", f"${ingreso_total:.2f}")
    col_res2.metric("Tarifas Etsy", f"${etsy_fees:.2f}")
    col_res3.metric("Costo Printify", f"${(costo_printify + envio_printify):.2f}")
    
    col_res4, col_res5 = st.columns(2)
    if margen_porcentaje >= 30:
        col_res4.metric("Ganancia Neta", f"${ganancia_neta:.2f}", "Excelente")
        col_res5.metric("Margen", f"{margen_porcentaje:.1f}%", "OK para Ads")
        st.success("🔥 ¡Estrategia sólida! Tienes espacio para pagar Etsy Ads.")
    elif 15 <= margen_porcentaje < 30:
        col_res4.metric("Ganancia Neta", f"${ganancia_neta:.2f}")
        col_res5.metric("Margen", f"{margen_porcentaje:.1f}%", delta_color="off")
        st.warning("⚠️ Margen ajustado. NO uses Ads con este producto.")
    else:
        col_res4.metric("Ganancia Neta", f"${ganancia_neta:.2f}", "-Riesgo")
        col_res5.metric("Margen", f"{margen_porcentaje:.1f}%", "-Sube el precio")
        st.error("🚨 ¡Alerta roja! Estás ganando muy poco.")

st.markdown("---")

# -----------------------------
# 7. RADAR LEGAL
# -----------------------------
st.header("🚨 7. Radar Legal y Protección de Tienda")
texto_automatico = st.session_state.get("detected_text", "")
if "tags_generados" in st.session_state: texto_automatico += " " + " ".join(st.session_state["tags_generados"])

texto_a_revisar = st.text_area("Texto a revisar:", value=texto_automatico, height=80)

TRADEMARK_BLACKLIST = ["disney", "marvel", "star wars", "nike", "harry potter", "velcro", "onesie", "jeep", "taylor swift", "stanley", "snoopy", "mickey", "nfl", "nba", "barbie", "lego", "tupperware", "taser", "chapstick", "super bowl", "peanuts", "pokemon", "hello kitty", "bluey", "shrek"]

if st.button("🛡️ Escanear Listado"):
    if texto_a_revisar:
        texto_limpio = texto_a_revisar.lower()
        alertas = [marca for marca in TRADEMARK_BLACKLIST if marca in texto_limpio]
        if alertas: st.error(f"⚠️ ¡PELIGRO! Marcas registradas detectadas: **{', '.join(alertas).title()}**")
        else: st.success("✅ ¡Listado Limpio!")
    else: st.warning("No hay texto para revisar aún.")

st.markdown("---")

# -----------------------------
# 8. CALENDARIO Y CUPONES
# -----------------------------
st.header("📅 8. Calendario POD y Retención")
tab_cal, tab_cup = st.tabs(["⏰ Calendario de Subidas", "💌 Estrategia de Cupones"])

with tab_cal:
    col_q1, col_q2 = st.columns(2)
    with col_q1:
        st.markdown("**Q1:** Valentine's, St. Patrick's, Easter, Mother's Day prep.")
        st.markdown("**Q2:** Father's Day, Graduaciones, Teacher Appreciation.")
    with col_q2:
        st.markdown("**Q3:** Back to School, Halloween Prep, Thanksgiving.")
        st.markdown("**Q4:** Christmas, Ugly Sweaters, Black Friday, New Year.")

with tab_cup:
    st.markdown("Ve a **Marketing > Sales and Discounts** en Etsy:")
    st.info("**1. Carrito Abandonado** - 15% OFF (VUELVE15)")
    st.success("**2. Post-Compra** - 20% OFF (GRACIAS20)")
    st.warning("**3. Favoritos** - 10% OFF (TUYO10)")

st.markdown("---")

# -----------------------------
# 9. AUDITORÍA DE TIENDA
# -----------------------------
st.header("📈 9. Auditoría de Tienda (CSV)")
uploaded_csv = st.file_uploader("Sube tu archivo EtsySoldOrders.csv", type=["csv"])

if uploaded_csv:
    try:
        df = pd.read_csv(uploaded_csv)
        item_col = [col for col in df.columns if 'Item Name' in col or 'Artículo' in col or 'Title' in col]
        qty_col = [col for col in df.columns if 'Quantity' in col or 'Cantidad' in col]
        
        if item_col and qty_col:
            ventas = df.groupby(item_col[0])[qty_col[0]].sum().reset_index().sort_values(by=qty_col[0], ascending=False)
            st.subheader("🏆 Tus Top 5 Productos")
            st.dataframe(ventas.head(5), use_container_width=True)
            st.subheader("💀 Productos Muertos")
            st.dataframe(ventas.tail(5), use_container_width=True)
        else: st.error("No se encontraron columnas de Item y Quantity.")
    except Exception as e: st.error(f"Error al leer el archivo: {e}")

st.markdown("---")

# -----------------------------
# 10. RADAR DINÁMICO
# -----------------------------
st.header("🔮 10. Radar Dinámico de Tendencias")
mes_actual = datetime.datetime.now().month
mes_objetivo = (mes_actual + 2) % 12
if mes_objetivo == 0: mes_objetivo = 12
meses = {1: "Enero", 2: "Febrero", 3: "Marzo", 4: "Abril", 5: "Mayo", 6: "Junio", 7: "Julio", 8: "Agosto", 9: "Septiembre", 10: "Octubre", 11: "Noviembre", 12: "Diciembre"}

st.markdown(f"Estamos en **{meses[mes_actual]}**. Deberías estar subiendo diseños para **{meses[mes_objetivo]}**.")

tendencias_futuras = {
    1: ["St. Patrick's Day (Marzo)", "Easter (Marzo/Abril)"], 2: ["Mother's Day (Mayo)"],
    3: ["Teacher Appreciation (Mayo)", "Father's Day (Junio)"], 4: ["Father's Day (Junio)", "Pride Month (Junio)"],
    5: ["Julio 4th", "Camping (Julio)"], 6: ["Back to School", "Halloween (Agosto)"],
    7: ["Halloween (Octubre)", "Thanksgiving (Noviembre)"], 8: ["Christmas (Diciembre)", "Navidad Mascotas"],
    9: ["Black Friday Prep", "Winter"], 10: ["New Year's Eve (Enero)", "Valentine's Day Prep"],
    11: ["Valentine's Day", "Super Bowl"], 12: ["Valentine's Day", "100 Days of School"]
}

col_t1, col_t2 = st.columns(2)
with col_t1:
    st.success("**NICHOS EN AUGE HOY:**")
    for t in tendencias_futuras.get(mes_actual, ["Temporada general"]): st.write(f"✅ {t}")
with col_t2:
    st.warning("**ESTILO EN TENDENCIA:**")
    st.write("🎨 Retro Wavy Text, Minimalist Line Art, Bootleg Rap 90s")

st.markdown("---")

# -----------------------------
# 11. MÁQUINA DE IDEAS
# -----------------------------
st.header("💡 11. Máquina de Ideas")
col_idea1, col_idea2 = st.columns(2)

with col_idea1:
    if st.button("🎲 Generar Idea para POD Mascotas"):
        mascotas = ["Perro de Tres Patas", "Gato Ciego", "Perro de Terapia", "Mascota Rescatada", "Hurón Apoyo", "Golden Senior"]
        angulos = ["Memorial Acuarela", "Gotcha Day", "Line Art Minimalista", "Empleado del Mes"]
        productos = ["Taza Interior Negro", "Manta Suave", "Adorno Acrílico", "Vaso Térmico"]
        st.success(f"**Nicho:** {random.choice(mascotas)}\n\n**Ángulo:** {random.choice(angulos)}\n\n**Producto:** {random.choice(productos)}")

with col_idea2:
    if st.button("🎲 Generar Idea para Invitaciones"):
        eventos = ["Fiesta de Divorcio", "Cumpleaños 15 Perro", "Adopción Padrastro", "Celebración de Vida", "Fiesta Vasectomía"]
        estilos = ["Acuarela Floral Oscura", "Retro 70s", "Minimalista B/N", "Periódico Vintage", "Boleto Falso"]
