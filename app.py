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

# =========================
# TRADUCTOR Y LIMPIADOR INTERNO PARA SEO PURO (INGLÉS)
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
# FUNCIONES PRINCIPALES DE SEO (REGLAS ETSY 2024+)
# =========================

def generar_titulos_venta(keywords, product, niche, texto_detectado, lang="en"):
    kw1 = keywords[0].title() if len(keywords) > 0 else "Custom"
    kw2 = keywords[1].title() if len(keywords) > 1 else "Design"

    if lang == "en":
        prod_en = limpiar_producto_en(product)
        niche_en = limpiar_nicho_en(niche)
        titulos = [
            (f"Custom {prod_en} for {niche_en}, Personalized {kw1} Gift, {kw2} Keepsake Present", 98),
            (f"{niche_en} Gift Idea, Personalized {kw1} {prod_en}, Custom Name Design", 92),
            (f"Personalized {kw1} {prod_en}, Unique Gift for {niche_en}, Custom Art Item", 85)
        ]
    else:
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
        # Limpiamos y quitamos la palabra "Custom" si venía pegada al producto
        prod_en = limpiar_producto_en(product).replace("Custom ", "").replace("Custom", "").strip()
        niche_en = limpiar_nicho_en(niche)
        kw = keywords[0] if keywords else "art"
        
        # Arsenal de sinónimos: No repetimos para abarcar más mercado
        raw_tags = [
            f"custom {prod_en}", 
            f"{niche_en} gift", 
            f"personalized {kw}",
            f"unique {prod_en}", 
            f"bespoke {niche_en}", 
            "made to order",
            f"gift for {niche_en}", 
            "keepsake present", 
            f"customized {kw}",
            "special occasion", 
            f"{kw} artwork", 
            f"trendy {prod_en}", 
            "thoughtful gift"
        ]
    else:
        prod_es = product.split(" (")[0].strip().lower()
        nicho_es = niche.split(" (")[0].strip().lower()
        kw = keywords[0] if keywords else "arte"
        
        raw_tags = [
            f"{prod_es} custom", f"regalo {nicho_es}", f"{kw} personal",
            f"regalo unico", "hecho a medida", f"para {nicho_es}",
            "recuerdo especial", "arte personalizado", f"detalle {nicho_es}",
            "regalo original", "tendencia", "regalo especial", f"{kw} a medida"
        ]
        
    # Limpiar y asegurar que ninguna etiqueta pase de 20 caracteres (Regla Etsy)
    for t in raw_tags:
        clean_t = t.replace("  ", " ").strip()
        if len(clean_t) <= 20 and clean_t not in tags: 
            tags.append(clean_t)
        if len(tags) == 13: break
        
    # Relleno de seguridad con más sinónimos si alguna etiqueta fue descartada por ser muy larga
    fillers = ["bespoke gift", "personalized item", "unique present", "custom design"]
    for f in fillers:
        if len(tags) < 13 and f not in tags: tags.append(f)
            
    return tags[:13]

def obtener_detalles_printify(producto):
    p = producto.lower()
    if "3001" in p or "t-shirt" in p:
        return "👕 ITEM SPECS (Bella+Canvas 3001):\n- 100% Airlume combed and ringspun cotton (ultra-soft!)\n- Light fabric (4.2 oz/yd²)\n- Retail fit & Tear away label\n- Runs true to size"
    elif "18000" in p or "18500" in p or "hoodie" in p or "sweatshirt" in p:
        return "🧥 ITEM SPECS (Premium Blend):\n- 50% cotton, 50% polyester\n- Medium-heavy fabric for cozy warmth\n- Classic fit & Tear-away label\n- Runs true to size"
    elif "mug" in p:
        return "☕ ITEM SPECS (Ceramic Mug):\n- High-quality white ceramic\n- Lead and BPA-free\n- Microwave and dishwasher safe\n- Vibrant, fade-resistant wrap-around print"
    elif "blanket" in p:
        return "🛌 ITEM SPECS (Velveteen Plush):\n- 100% Polyester for extreme, cozy softness\n- Double needle topstitch on all seams\n- Vibrant, high-detail one-sided print\n- Machine washable (cold)"
    elif "plaque" in p:
        return "✨ ITEM SPECS (Acrylic Plaque):\n- Premium, crystal-clear acrylic\n- Vibrant, fade-resistant printed design\n- Sleek and modern aesthetic, perfect for display"
    elif "bandana" in p:
        return "🐾 ITEM SPECS (Pet Bandana):\n- 100% soft spun polyester\n- Breathable, durable, and lightweight\n- One-sided vibrant print\n- Perfect fit for your furry friend"
    elif "digital" in p or "evite" in p or "sign" in p:
        return "📱 ITEM SPECS (Digital File):\n- High-resolution digital download (JPEG/PDF)\n- NO physical item will be shipped\n- Ready to print at home, local print shop, or send via text/email"
    else:
        return "✨ ITEM SPECS:\n- Premium quality materials\n- Vibrant and durable printing\n- Carefully crafted to order"

def generar_descripcion_vendedora(product, niche, texto_detectado, lang="en"):
    # Limpiar palabras para SEO
    prod_en = limpiar_producto_en(product)
    niche_en = limpiar_nicho_en(niche)
    detalles_printify = obtener_detalles_printify(product)
    kw = texto_detectado if texto_detectado else "Custom Art"
    
    if lang == "en":
        return f"""{prod_en} for {niche_en} | Personalized {kw} Gift | Custom {prod_en}

Give the perfect meaningful gift with this custom {prod_en} designed exclusively for {niche_en}s! 
Whether you're looking for a unique present or treating yourself, this gorgeous "{kw}" design is guaranteed to bring a smile. 

✨ HOW TO PERSONALIZE ✨
1. Enter your specific details in the personalization box.
2. Double-check your spelling! We print exactly what you provide.
3. Add to cart and checkout!

{detalles_printify}

🎨 DIGITAL PROOF ADD-ON (OPTIONAL)
To keep our production times fast and prices low, proofs are NOT automatically included. 
Want to see the artwork before it prints? Purchase our "Digital Proof Add-On" listing alongside this item! Otherwise, our expert artists will ensure your design looks amazing.

📦 SHIPPING & PRODUCTION 
- Carefully made to order just for you.
- Production: 2-5 business days.
- Tracking number included with every physical order!

🤍 Thank you for supporting our small business! 
Explore more custom designs in our shop: [Insert Your Shop Link Here]"""
    else:
        prod_es = product.split(" (")[0].strip()
        nicho_es = niche.split(" (")[0].strip()
        
        return f"""🔥 ¡Da el regalo perfecto con este {prod_es} Personalizado diseñado exclusivamente para {nicho_es}! 
Ya sea para un regalo único o para ti mismo, este diseño de "{kw}" garantiza una sonrisa. 

✨ CÓMO PERSONALIZAR ✨
1. Ingresa los detalles en la caja de personalización.
2. ¡Revisa la ortografía! Imprimimos exactamente lo que escribes.

{detalles_printify}

🎨 MUESTRA DIGITAL (OPCIONAL - COSTO EXTRA)
Para mantener nuestros tiempos de envío rápidos, las muestras NO están incluidas automáticamente. 
Si deseas ver el arte antes de imprimir, por favor compra nuestro listado "Digital Proof Add-On" junto con este artículo. 

📦 DETALLES Y ENVÍO
- Procesado en 2-5 días hábiles. ¡Rastreo incluido!"""

# =========================
# UI DE LA APLICACIÓN
# =========================

# -----------------------------
# 1. SUBIR DISEÑO
# -----------------------------
with tab1:
    st.header("1️⃣ Subir diseño (OCR o Manual)")
    uploaded_file = st.file_uploader("Sube tu diseño transparente (PNG)", type=["png", "jpg", "jpeg"])

    if uploaded_file:
        image = Image.open(uploaded_file)
        
        # --- MAGIA PARA FONDOS TRANSPARENTES (EL ARREGLO) ---
        if image.mode in ('RGBA', 'LA') or (image.mode == 'P' and 'transparency' in image.info):
            # Usamos un fondo GRIS OSCURO (40, 40, 40) en lugar de blanco.
            # Esto asegura que los diseños con letras blancas o negras sean visibles para el OCR.
            fondo_seguro = Image.new("RGB", image.size, (40, 40, 40))
            fondo_seguro.paste(image, mask=image.split()[-1])
            image = fondo_seguro
        else:
            image = image.convert("RGB")

st.image(image, caption="Vista previa (Fondo ajustado para lectura)", width=300)

    # --- NUEVA LÓGICA ESTRATÉGICA ---
    st.subheader("📝 ¿Cómo definimos el SEO de tu diseño?")
    st.markdown("Si tu diseño tiene texto (ej: una frase), usa el OCR. Si es **SOLO GRÁFICO** (ej: retrato de perro acuarela), escribe el concepto tú misma.")

    col_ocr1, col_ocr2 = st.columns(2)

    with col_ocr1:
        # Tu botón OCR original
        if st.button("👁️ Detectar texto (OCR)"):
            with st.spinner("Analizando imagen..."):
                texto = extraer_texto_ocr(reader, image)
                st.session_state["detected_text"] = texto
                if not texto.strip():
                    st.info("OCR no detectó texto. Introduce el concepto manualmente a la derecha.")
                else:
                    st.rerun()

    with col_ocr2:
        # Entrada manual para diseños puramente gráficos
        st.markdown("**Entrada Manual (Para diseños gráficos):**")
        concepto_manual = st.text_input(
            "Describe lo que se ve en la imagen (ej: Retrato acuarela Golden Retriever):",
            value=st.session_state["detected_text"], # Se pre-llena con OCR si hubo, o vacío si no
            key="final_concept_input"
        )
        
        # Actualizamos la variable central del SEO con lo que tú escribas
        if concepto_manual != st.session_state["detected_text"]:
             st.session_state["detected_text"] = concepto_manual

# --- Esta condición es la que desbloquea el SEO ---
if st.session_state["detected_text"]:
    st.success(f"✅ Concepto '{st.session_state['detected_text']}' guardado en memoria. ¡Procede al SEO!")
elif uploaded_file:
    st.warning("⚠️ Ejecuta el OCR o escribe el concepto manual arriba para activar el SEO.")

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
    st.write("**Catálogo Estratégico Printify (Bestsellers + Mascotas):**")
    
    productos_mascotas = [
        # --- BESTSELLERS GLOBALES (Para los dueños) ---
        "Bella+Canvas 3001 (T-Shirt Bestseller)",
        "Gildan 18000 (Crewneck Sweatshirt)",
        "Gildan 18500 (Hoodie Clásica)",
        "Comfort Colors 1717 (Camiseta Premium)",
        "Gildan 5000 (Camiseta Económica)",
        "White Ceramic Mug 11oz & 15oz (Taza clásica)",
        "Enamel Campfire Mug (Taza de campamento)",
        "Tote Bag (Bolsa de tela)",
        "Die-Cut Stickers (Pegatinas)",
        "Velveteen Plush Blanket (Cobija Suave)",
        "Canvas Gallery Wraps (Lienzo Premium)",
        "Acrylic Plaque (Placa Acrílica Memorial)",
        
        # --- PRODUCTOS EXCLUSIVOS PARA MASCOTAS ---
        "Pet Bandana (Bandana para Cuello)",
        "Pet Bowl (Plato de Cerámica/Acero)",
        "Pet Feeding Mat (Tapete para Platos)",
        "Pet Bed (Cama Suave para Mascotas)",
        "Pet Tank Top (Camiseta para Perros)",
        "Pet Tag (Placa de Identificación Hueso/Círculo)",
        "Pet Collar (Collar Ajustable)"
    ]
    
    # Lo dividimos en 3 columnas para que se vea ordenado
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
st.subheader("🖼️ Mockups Populares (Placeit)")
    
    col_m1, col_m2 = st.columns(2)
    
    with col_m1:
        st.markdown("**Ropa y Básicos**")
        st.markdown("[👕 T-shirt / Camisetas (B+C 3001, Gildan)](https://placeit.net/c/mockups/stages/t-shirt-mockup)")
        st.markdown("[🧥 Hoodies / Sudaderas](https://placeit.net/c/mockups/stages/hoodie-mockup)")
        st.markdown("[👜 Tote Bags / Bolsas](https://placeit.net/c/mockups/stages/tote-bag-mockup)")
        st.markdown("[✨ Stickers / Pegatinas](https://placeit.net/c/mockups/stages/sticker-mockup)")
        
        st.markdown("<br>**Hogar y Regalos (Memoriales)**", unsafe_allow_html=True)
        st.markdown("[☕ Mugs / Tazas (11oz & 15oz)](https://placeit.net/c/mockups/stages/mug-mockup)")
        st.markdown("[🥤 Tumblers / Vasos Térmicos](https://placeit.net/c/mockups/stages/tumbler-mockup)")
        st.markdown("[🖼️ Canvas / Lienzos](https://placeit.net/c/mockups/stages/canvas-mockup)")
        st.markdown("[🛌 Blankets / Cobijas](https://placeit.net/c/mockups/stages/blanket-mockup)")
        st.markdown("[🎄 Ornaments / Adornos](https://placeit.net/c/mockups/stages/ornament-mockup)")

    with col_m2:
        st.markdown("**Exclusivos para Mascotas**")
        st.markdown("[🐾 Pet Bandanas / Paliacates](https://placeit.net/c/mockups/stages/pet-bandana-mockup)")
        st.markdown("[🥣 Pet Bowls / Platos](https://placeit.net/c/mockups/stages/pet-bowl-mockup)")
        st.markdown("[🛏️ Pet Beds / Camas](https://placeit.net/c/mockups/stages/pet-bed-mockup)")
        st.markdown("[🐕 Pet Tank Tops / Ropita](https://placeit.net/c/mockups/stages/dog-t-shirt-mockup)")
        st.markdown("[🏷️ Pet Collars / Collares](https://placeit.net/c/mockups/stages/pet-collar-mockup)")
        
        st.markdown("<br>**Digitales e Invitaciones**", unsafe_allow_html=True)
        st.markdown("[💌 Invitations / Tarjetas Impresas](https://placeit.net/c/mockups/stages/invitation-mockup)")
        st.markdown("[📱 Mobile Evites / Smartphones](https://placeit.net/c/mockups/stages/iphone-mockup)")

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
        st.success(f"**Evento:** {random.choice(eventos)}\n\n**Estilo:** {random.choice(estilos)}")
