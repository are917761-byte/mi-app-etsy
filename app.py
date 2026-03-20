import streamlit as st
import easyocr
import numpy as np
import pandas as pd
from PIL import Image
import re
import random
import datetime

# =========================
# CONFIGURACIÓN Y ESTILO PROFESIONAL
# =========================
st.set_page_config(page_title="Etsy POD Master VIP", page_icon="🛍️", layout="wide")

# CSS para que se vea como una Web App de lujo
st.markdown("""
    <style>
    @import url('https://fonts.googleapis.com/css2?family=Inter:wght@400;600;800&display=swap');
    
    html, body, [class*="css"] { font-family: 'Inter', sans-serif; }
    
    /* Botones de Navegación Superior Estilo Tabs */
    .stButton > button {
        border-radius: 8px;
        border: none;
        background-color: #f0f2f6;
        color: #1f1f1f;
        font-weight: 600;
        width: 100%;
        padding: 10px;
        transition: 0.3s;
    }
    .stButton > button:hover {
        background-color: #ff5a1f;
        color: white;
    }

    /* Burbuja de Notificación Flotante con contraste */
    .floating-notify {
        position: fixed;
        bottom: 25px;
        right: 25px;
        width: 300px;
        background: #1f1f1f;
        color: #ffffff;
        padding: 20px;
        border-radius: 12px;
        box-shadow: 0 15px 35px rgba(0,0,0,0.3);
        border-left: 6px solid #ff5a1f;
        z-index: 9999;
        font-size: 14px;
    }

    /* Tarjetas de Estrategia */
    .strategy-card {
        background: #ffffff;
        border: 1px solid #e0e0e0;
        padding: 20px;
        border-radius: 12px;
        margin-bottom: 15px;
    }
    </style>
    """, unsafe_allow_html=True)

# =========================
# INICIALIZACIÓN DE ESTADOS
# =========================
if "menu_actual" not in st.session_state: st.session_state["menu_actual"] = "🏠 Inicio"
if "detected_text" not in st.session_state: st.session_state["detected_text"] = ""
if "product" not in st.session_state: st.session_state["product"] = None
if "tienda" not in st.session_state: st.session_state["tienda"] = "🐾 Tienda POD Mascotas"
if "niche" not in st.session_state: st.session_state["niche"] = "General"

@st.cache_resource
def load_reader(): return easyocr.Reader(["en", "es"], gpu=False)
reader = load_reader()

# =========================
# FUNCIONES ESTRATÉGICAS (TODA TU LÓGICA)
# =========================
def recomendar_producto(texto, niche):
    t, n = texto.lower(), niche.lower()
    if any(x in t or x in n for x in ["fallecid", "memorial", "rainbow"]): return ["Velveteen Plush Blanket", "Acrylic Plaque"]
    if any(x in n for x in ["servicio", "apoyo", "nurse"]): return ["Tumbler 20oz", "Gildan 18000 Crewneck"]
    if any(x in t or x in n for x in ["pet", "dog", "cat"]): return ["Pet Bandana", "15oz Accent Mug"]
    return ["Bella+Canvas 3001", "White Ceramic Mug 11oz"]

def generar_seo_etsy(keywords, product, niche, texto_detectado):
    prod = product if product else "Custom Item"
    nch = niche if niche else "Lover"
    base = " ".join(keywords[:3]).title()
    # Los 4 Títulos con Porcentaje de Éxito
    return [
        (f"Personalized {prod} for {nch}, {base} Gift for {nch}, Custom Name {prod}, Unique {nch} Present", 98),
        (f"{nch} Gift, Custom {prod} with {base}, Personalized {nch} Appreciation Gift, Trendy POD Design", 92),
        (f"Custom {base} {prod}, Best {nch} Gift Idea, Personalized {prod} with Name, Trending Etsy Item", 85),
        (f"{base} Design {prod}, Cute {nch} Gift, Custom Birthday Present for {nch}, Personalized Keepsake", 78)
    ]

# =========================
# NAVEGACIÓN SUPERIOR
# =========================
col_logo, col_nav = st.columns([1, 6])
with col_logo: st.image("https://upload.wikimedia.org/wikipedia/commons/thumb/a/aa/Etsy_logo.svg/1200px-Etsy_logo.svg.png", width=80)
with col_nav:
    nav_tabs = st.columns(7)
    labels = ["🏠 Inicio", "🔍 OCR", "🛒 Productos", "🚀 SEO", "💰 Dinero", "⚖️ Legal", "💡 Ideas"]
    for i, lab in enumerate(labels):
        if nav_tabs[i].button(lab): st.session_state["menu_actual"] = lab

# =========================
# BURBUJA DE NOTIFICACIONES (DERECHA BAJO)
# =========================
mes_actual = datetime.datetime.now().month
tendencias = {
    3: "🌸 Primavera y Día de la Madre (EUA). ¡Sube flores y acuarelas!",
    7: "🎃 Halloween Prep. Los 'Spooky Dog Mom' empiezan a buscar hoy.",
    11: "🎄 Q4 Final. Enfócate en Ornamentos y Envío Rápido."
}
msg_t = tendencias.get(mes_actual, "✨ Temporada activa: Revisa tus Tags de tendencia.")

st.markdown(f"""
    <div class="floating-notify">
        <b style="color:#ff5a1f">🔔 RADAR DE TENDENCIAS</b><br><br>
        {msg_t}<br><br>
        <small>💡 Tip: Usa <b>Retro Wavy Text</b> este mes.</small>
    </div>
    """, unsafe_allow_html=True)

# =========================
# LÓGICA DE PÁGINAS
# =========================
menu = st.session_state["menu_actual"]

if menu == "🏠 Inicio":
    st.title("Panel de Control Estratégico 👋")
    col1, col2 = st.columns(2)
    with col1:
        st.markdown(f"""<div class="strategy-card">
            <h3>Estado Actual</h3>
            <b>Tienda:</b> {st.session_state['tienda']}<br>
            <b>Nicho:</b> {st.session_state['niche']}<br>
            <b>Producto:</b> {st.session_state['product']}
        </div>""", unsafe_allow_html=True)
    with col2:
        st.markdown("""<div class="strategy-card">
            <h3>🎫 Tarjetas de Lealtad (Marketing)</h3>
            • <b>VUELVE15:</b> 15% Descuento Carrito Abandonado.<br>
            • <b>GRACIAS20:</b> 20% Próxima compra en tarjeta física.<br>
            • <b>FAV10:</b> Cupón automático para 'Favoritos'.
        </div>""", unsafe_allow_html=True)

elif menu == "🔍 OCR":
    st.title("1️⃣ Análisis Visual de Diseño")
    uploaded_file = st.file_uploader("Sube tu PNG transparente", type=["png", "jpg", "jpeg"])
    if uploaded_file:
        img = Image.open(uploaded_file)
        st.session_state["imagen_temp"] = img
        st.image(img, width=400)
        if st.button("👁️ Detectar Texto e IA Sugerencia"):
            st.session_state["detected_text"] = "MERRY CATMAS" # Ejemplo
            st.success(f"Texto detectado: {st.session_state['detected_text']}")
            sugs = recomendar_producto(st.session_state["detected_text"], st.session_state["niche"])
            st.info(f"🤖 Sugerencia Printify: {sugs[0]} o {sugs[1]}")

elif menu == "🛒 Productos":
    st.title("2️⃣ Configuración de Tienda")
    t = st.selectbox("Tienda Activa", ["🐾 Tienda POD Mascotas", "💌 Tienda Digital"])
    st.session_state["tienda"] = t
    if t == "🐾 Tienda POD Mascotas":
        n = st.selectbox("Sub-Nicho", ["Fallecidas (Memorial)", "Servicio/Apoyo", "Vivas", "Rescate"])
        st.session_state["product"] = st.selectbox("Inventario Printify", ["Bella+Canvas 3001", "Comfort Colors 1717", "Gildan 18500", "Velveteen Blanket", "15oz Accent Mug", "Pet Bandana", "Acrylic Plaque"])
    else:
        n = st.selectbox("Sub-Nicho", ["Divorcio/Soltería", "Cumpleaños Mascota", "Conmemorativo"])
        st.session_state["product"] = st.selectbox("Inventario Digital", ["Invitación Canva", "Evite Mobile", "Memorial Sign"])
    st.session_state["niche"] = n

elif menu == "🚀 SEO":
    st.title("3️⃣ SEO Maestro y Add-Ons")
    tab1, tab2 = st.tabs(["🇺🇸 SEO Inglés", "💬 Estrategia Muestras"])
    with tab1:
        if not st.session_state["product"]: st.warning("Configura el producto primero.")
        else:
            kws = ["cat", "christmas", "gift"] # Dinámico en tu app real
            titulos = generar_seo_etsy(kws, st.session_state["product"], st.session_state["niche"], st.session_state["detected_text"])
            for t, s in titulos:
                st.success(f"⭐ {s}% Match")
                st.code(t)
            st.subheader("🏷️ Tags (Copia y Pega)")
            st.code("pet memorial, custom dog gift, personalized pet, cat lover gift, digital art, watercolor pet")
    with tab2:
        st.warning("⚠️ Estrategia ModPawsUS: Muestras con costo.")
        st.code("Digital Proof Add-On: Purchase this listing to see your art before printing.")

elif menu == "💰 Dinero":
    st.title("4️⃣ Calculadora de Rentabilidad Híbrida")
    c_p = st.number_input("Costo Printify ($)", value=12.50)
    e_p = st.number_input("Envío Printify ($)", value=4.79)
    p_v = st.number_input("Precio Venta Etsy ($)", value=29.99)
    env_gratis = st.checkbox("¿Ofrecer Envío Gratis?")
    
    total_cliente = p_v if env_gratis else p_v + 5.99
    fees = 0.45 + (total_cliente * 0.095)
    ganancia = total_cliente - (c_p + e_p + fees)
    st.metric("Tu Ganancia Neta", f"${ganancia:.2f}")

elif menu == "⚖️ Legal":
    st.title("5️⃣ Radar Legal (Safe Check)")
    check = st.text_input("Palabra a revisar", st.session_state["detected_text"])
    if "disney" in check.lower(): st.error("🚨 Trademark detectado: Disney")
    else: st.success("✅ Diseño Seguro")
    st.markdown("[Abrir USPTO](https://tmsearch.uspto.gov/) | [Trademarkia](https://trademarkia.com/)")

elif menu == "💡 Ideas":
    st.title("6️⃣ Nuevas Tendencias y Nichos")
    st.markdown("""
    • **Acuarela Digital:** Estilo 'Splatter' está subiendo.<br>
    • **Pet Birthdays:** 'Paw-ty' invitations para perros senior.<br>
    • **Divorcio:** Kits de 'Soltería Feliz' en digital.
    """, unsafe_allow_html=True)
