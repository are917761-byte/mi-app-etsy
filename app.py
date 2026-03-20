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
if "product" not in st.session_state:
    st.session_state["product"] = None
if "detected_text" not in st.session_state:
    st.session_state["detected_text"] = ""
if "niche" not in st.session_state:
    st.session_state["niche"] = ""
if "tienda" not in st.session_state:
    st.session_state["tienda"] = ""
if "tags_generados" not in st.session_state:
    st.session_state["tags_generados"] = []

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
    texto, niche = texto.lower(), niche.lower()
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
st.sidebar.caption("POD Master v3.0 - San Luis Potosí, MX 🇲🇽")


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
    
    # Llave única para el uploader
    uploaded_file = st.file_uploader("Sube tu diseño aquí:", type=["png", "jpg", "jpeg"], key="img_uploader")
    
    # 1. Guardar la imagen en la memoria profunda
    if uploaded_file:
        image = Image.open(uploaded_file)
        if image.mode in ('RGBA', 'LA') or (image.mode == 'P' and 'transparency' in image.info):
            fondo_blanco = Image.new("RGB", image.size, (255, 255, 255))
            fondo_blanco.paste(image, mask=image.split()[-1])
            st.session_state["imagen_memoria"] = fondo_blanco
        else:
            st.session_state["imagen_memoria"] = image.convert("RGB")

    # 2. Mostrar la imagen SIEMPRE que esté en memoria
    if "imagen_memoria" in st.session_state:
        st.image(st.session_state["imagen_memoria"], caption="Imagen en memoria lista para analizar", width=300)

        # 3. Botón con llave única anti-errores
        if st.button("👁️ Leer Texto del Diseño", key="btn_leer_ocr_unico"):
            with st.spinner("Analizando pixeles..."):
                texto = extraer_texto_ocr(reader, st.session_state["imagen_memoria"])
                st.session_state["detected_text"] = texto

    # 4. Mostrar y editar el texto detectado
    if st.session_state.get("detected_text"):
        st.subheader("Texto detectado (Edítalo para que quede perfecto):")
        nuevo_texto = st.text_input("Concepto Central:", st.session_state["detected_text"], key="input_txt_unico")
        
        if nuevo_texto != st.session_state["detected_text"]:
            st.session_state["detected_text"] = nuevo_texto
            
        st.success("✅ ¡Texto guardado! Ya no desaparecerá tu imagen. Ve al menú '2. Catálogo y Tiendas'.")

elif menu == "🛒 2. Catálogo y Tiendas":
    st.title("Perfil de Tienda y Catálogo")
    
    tienda = st.radio("Selecciona la Tienda a trabajar:", ["🐾 Tienda POD Mascotas", "💌 Tienda Digital (Invitaciones)"], key="radio_tienda")
    st.session_state["tienda"] = tienda
    
    col_n, col_e = st.columns(2)
    with col_n:
        if tienda == "🐾 Tienda POD Mascotas":
            subnicho = st.selectbox("Sub-Nicho:", ["Mascotas Fallecidas", "Apoyo Emocional / Servicio", "Cumpleaños Mascota Viva", "Rescate / Adopción"])
            estilo = st.selectbox("Estilo de Arte:", ["Acuarela Digital", "Line Art Minimalista", "Caricatura", "Óleo Digital"])
        else:
            subnicho = st.selectbox("Sub-Nicho:", ["Fiesta de Divorcio", "Cumpleaños de Mascotas", "Conmemorativos", "Despedida Anti-Tradicional"])
            estilo = st.selectbox("Estilo Visual:", ["Acuarela Elegante", "Sarcástico (Bold)", "Minimalista", "Boho"])
            
    st.session_state["niche"] = f"{subnicho} ({estilo})"
    st.info(f"🎯 Nicho configurado: **{st.session_state['niche']}**")
    
    st.markdown("---")
    st.subheader("Selección de Producto Rentable")
    
    if st.session_state["detected_text"]:
        st.success("🤖 **Sugerencia de la IA basada en tu diseño:**")
        sugs = recomendar_producto_ganador(st.session_state["detected_text"], st.session_state["niche"])
        for s in sugs: st.write(f"🔥 {s}")

    if tienda == "🐾 Tienda POD Mascotas":
        prods = ["Velveteen Plush Blanket", "White Ceramic Mug 15oz", "Square Canvas", "Pet Bandana", "Acrylic Plaque", "Gildan 18500 Hoodie", "Bella+Canvas 3001 T-Shirt"]
    else:
        prods = ["Digital Invitation (Canva)", "Mobile Evite (Smartphone Size)", "Printable Memorial Sign", "Digital Portrait File"]
        
    cols = st.columns(3)
    for idx, p in enumerate(prods):
        with cols[idx % 3]:
            if st.button(p, key=f"btn_prod_{idx}"):
                st.session_state["product"] = p
                
    if st.session_state["product"]:
        st.success(f"📦 Producto en memoria: **{st.session_state['product']}**. ¡Ve al paso 3!")

elif menu == "🚀 3. Generador SEO":
    st.title("Generador SEO Experto")
    
    if not st.session_state["detected_text"] or not st.session_state["product"]:
        st.warning("⚠️ Faltan datos. Sube un diseño (Paso 1) y selecciona un producto (Paso 2) primero.")
    else:
        if st.button("🚀 Generar Listado Optimizado", key="btn_generar_seo"):
            with st.spinner("Creando SEO..."):
                texto = st.session_state["detected_text"]
                prod = st.session_state["product"]
                nicho = st.session_state["niche"]
                kws = extraer_keywords_texto(texto)
                if not kws: kws = [nicho, prod]
                
                st.session_state["tags_generados"] = generar_tags_etsy(kws, prod, nicho, "en")
                
                tab_en, tab_es = st.tabs(["🇺🇸 Inglés (Etsy EUA)", "🇪🇸 Español (Referencia)"])
                with tab_en:
                    st.info("Copia el título con mayor porcentaje de Match:")
                    for t, score in generar_titulos_venta(kws, prod, nicho, "en"):
                        if score > 95: st.success(f"⭐ **{score}% MATCH:** {t}")
                        else: st.write(f"🔥 **{score}% MATCH:** {t}")
                    
                    st.subheader("🏷️ 13 Etiquetas (Separadas por coma)")
                    st.code(", ".join(st.session_state["tags_generados"]), language="text")
                    
                    st.subheader("📝 Descripción de Alta Conversión")
                    st.code(generar_descripcion_vendedora(prod, nicho, texto, "en"), language="text")
                    
                with tab_es:
                    st.write("Versión en español para tu organización interna.")
                    for t, score in generar_titulos_venta(kws, prod, nicho, "es"):
                        st.write(f"- {t}")

elif menu == "💬 4. Flujo de Muestras (Add-On)":
    st.title("Monetización de Revisiones (Add-On)")
    tab1, tab2, tab3 = st.tabs(["💰 Listado 'Digital Proof Add-On'", "💬 Mensaje: Enviar Muestra", "⏰ Mensaje: Alerta 24h"])
    
    with tab1:
        st.info("Crea un producto digital en tu tienda con estos datos a $3.99 USD.")
        st.subheader("Título")
        st.code("Digital Proof Add-On for Custom Orders, Artwork Preview, See Design Before Printing", language="text")
        st.subheader("Tags")
        st.code("digital proof, artwork preview, add on listing, see before printing, custom order proof", language="text")
        st.subheader("Descripción")
        st.code("Purchase this listing IN ADDITION to your custom physical product if you wish to see a digital preview (proof) of the artwork before it is sent to production...", language="text")
    with tab2:
        st.code("Hi [Nombre],\n\nI have attached the proof (preview) for your custom piece. Please reply with 'APPROVED' if it looks perfect!\n\nBest, [Tu Nombre]", language="text")
    with tab3:
        st.code("Hi [Nombre],\n\nJust checking in! If I don't hear back by [Hora], I will proceed with printing to avoid shipping delays.\n\nThank you!", language="text")

elif menu == "💰 5. Calculadora Financiera":
    st.title("Calculadora de Rentabilidad Híbrida")
    c1, c2 = st.columns(2)
    with c1:
        st.subheader("Costos (Printify)")
        costo_prod = st.number_input("Costo de Producción $", value=12.50, key="calc_prod")
        costo_env = st.number_input("Costo Envío Printify $", value=4.79, key="calc_env")
    with c2:
        st.subheader("Estrategia Etsy")
        precio_venta = st.number_input("Precio del Producto $", value=24.99, key="calc_precio")
        estrategia = st.radio("Estrategia de Envío:", ["Cobrar Envío Aparte", "Envío Gratis (Absorbido)"], key="calc_estrategia")
        cobro_cliente = st.number_input("Cobro de envío al cliente $", value=5.99, key="calc_cobro") if estrategia == "Cobrar Envío Aparte" else 0.0
        
    if st.button("📊 Calcular", key="btn_calcular"):
        ingreso = precio_venta + cobro_cliente
        etsy_fees = 0.45 + (ingreso * 0.095)
        costo_total = costo_prod + costo_env + etsy_fees
        ganancia = ingreso - costo_total
        margen = (ganancia / ingreso) * 100 if ingreso > 0 else 0
        
        st.markdown("---")
        r1, r2, r3 = st.columns(3)
        r1.metric("Ingreso Bruto", f"${ingreso:.2f}")
        r2.metric("Tarifas Etsy", f"${etsy_fees:.2f}")
        r3.metric("Ganancia Neta", f"${ganancia:.2f}")
        if margen >= 30: st.success(f"🔥 Margen del {margen:.1f}%. ¡Excelente para usar Ads!")
        elif 15 <= margen < 30: st.warning(f"⚠️ Margen del {margen:.1f}%. Bueno, pero no uses Ads.")
        else: st.error(f"🚨 Margen del {margen:.1f}%. Estás perdiendo dinero.")

elif menu == "⚖️ 6. Radar Legal":
    st.title("Protección de Propiedad Intelectual")
    texto_auto = st.session_state["detected_text"] + " " + " ".join(st.session_state["tags_generados"])
    texto_revisar = st.text_area("Texto a revisar (Autocompletado):", value=texto_auto, key="radar_txt")
    
    blacklist = ["disney", "marvel", "star wars", "nike", "harry potter", "velcro", "onesie", "jeep", "taylor swift", "stanley", "snoopy", "pokemon", "bluey"]
    if st.button("🛡️ Escanear", key="btn_escanear"):
        alertas = [m for m in blacklist if m in texto_revisar.lower()]
        if alertas: st.error(f"⚠️ ¡PELIGRO TRADEMARK! Borra esto de tu listado: {', '.join(alertas).title()}")
        else: st.success("✅ Listado Limpio de la Lista Negra.")

elif menu == "💡 7. Máquina de Ideas":
    st.title("Generador de Ideas (Océanos Azules)")
    c1, c2 = st.columns(2)
    with c1:
        if st.button("🎲 Idea para Mascotas", key="btn_idea_masc"):
            mascota = random.choice(["Perro 3 Patas", "Gato Ciego", "Perro de Terapia", "Mascota Rescatada", "Golden Senior"])
            angulo = random.choice(["Memorial Acuarela", "Gotcha Day", "Line Art Minimalista", "Óleo Renacentista"])
            prod = random.choice(["Manta", "Adorno Acrílico", "Vaso Térmico", "Lienzo"])
            st.success(f"**Vende un(a)** {prod} **estilo** {angulo} **para dueños de** {mascota}.")
    with c2:
