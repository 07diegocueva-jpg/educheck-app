import streamlit as st
import docx2txt
import PyPDF2
from transformers import pipeline
import base64

# --- CONFIGURACIÓN DE MARCA ---
NOMBRE_APP = "EduCheck IA"
COLOR_PRIMARIO = "#003366"  # Azul institucional
COLOR_FONDO = "#f8f9fa"

st.set_page_config(page_title=NOMBRE_APP, page_icon="🎓", layout="wide")

# --- CSS PERSONALIZADO (Para quitar el look "cutre") ---
st.markdown(f"""
    <style>
    .main {{
        background-color: {COLOR_FONDO};
    }}
    .stButton>button {{
        width: 100%;
        border-radius: 5px;
        height: 3em;
        background-color: {COLOR_PRIMARIO};
        color: white;
        font-weight: bold;
        border: none;
    }}
    .stMetric {{
        background-color: white;
        padding: 15px;
        border-radius: 10px;
        box-shadow: 0 2px 4px rgba(0,0,0,0.05);
    }}
    [data-testid="stSidebar"] {{
        background-color: white;
        border-right: 1px solid #e0e0e0;
    }}
    h1 {{
        color: {COLOR_PRIMARIO};
        font-family: 'Helvetica Neue', Helvetica, Arial, sans-serif;
    }}
    </style>
    """, unsafe_allow_html=True)

# --- LÓGICA DE DETECCIÓN ---
@st.cache_resource
def load_model():
    return pipeline("text-classification", model="roberta-base-openai-detector")

detector = load_model()

def extract_text(file):
    if file.type == "application/pdf":
        return " ".join([p.extract_text() for p in PyPDF2.PdfReader(file).pages])
    elif file.type == "application/vnd.openxmlformats-officedocument.wordprocessingml.document":
        return docx2txt.process(file)
    else:
        return file.read().decode("utf-8")

# --- BARRA LATERAL (LOGO Y CONTACTO) ---
with st.sidebar:
    # Si tienes un archivo logo.png, descomenta las siguientes líneas:
    # st.image("logo.png", width=150) 
    st.title(f"🎓 {NOMBRE_APP}")
    st.markdown("---")
    st.info("**Uso Institucional:** Esta herramienta analiza patrones lingüísticos para verificar la autoría académica.")
    st.write("✉️ contacto@tuweb.com")

# --- CUERPO PRINCIPAL ---
st.title(f"Panel de Auditoría de Originalidad")
st.write("Sube el trabajo del alumno para iniciar el análisis profundo por fragmentos.")

archivo = st.file_uploader("", type=['pdf', 'docx', 'txt'])

if archivo:
    texto = extract_text(archivo)
    
    col_btn, _ = st.columns([1, 2])
    with col_btn:
        btn_analizar = st.button("🚀 INICIAR ESCANEO")

    if btn_analizar:
        # Dividir en bloques
        chunks = [texto[i:i+600] for i in range(0, len(texto), 600)][:15]
        
        with st.spinner('Ejecutando algoritmos de detección...'):
            resultados = [detector(c)[0] for c in chunks]
        
        # Cálculos
        total_ia = sum(1 for r in resultados if r['label'] == 'Fake')
        score_ia = (total_ia / len(resultados)) * 100
        score_humano = 100 - score_ia

        # Muestra visual de resultados
        st.markdown("### 📊 Resultado de la Evaluación")
        c1, c2, c3 = st.columns(3)
        
        with c1:
            st.metric("Autoría Humana", f"{score_humano:.1f}%")
        with c2:
            st.metric("Probabilidad IA", f"{score_ia:.1f}%")
        with c3:
            estado = "✅ ORIGINAL" if score_ia < 25 else "⚠️ REVISAR"
            st.metric("Estado del Documento", estado)

        # Reporte y detalles
        st.markdown("---")
        col_rep, col_det = st.columns(2)
        
        with col_rep:
            st.subheader("Reporte Oficial")
            reporte_txt = f"AUDITORÍA {NOMBRE_APP}\n"
            reporte_txt += f"Documento: {archivo.name}\n"
            reporte_txt += f"Originalidad: {score_humano:.1f}%\n"
            reporte_txt += "--------------------------\n"
            for i, r in enumerate(resultados):
                reporte_txt += f"Bloque {i+1}: {r['label']} ({r['score']:.2%})\n"
            
            st.download_button("📥 Descargar Certificado (.txt)", reporte_txt, f"Certificado_{archivo.name}.txt")

        with col_det:
            st.subheader("Análisis de Segmentos")
            for i, r in enumerate(resultados):
                color = "red" if r['label'] == 'Fake' else "green"
                st.markdown(f"Bloque {i+1}: :{color}[{r['label']}] ({r['score']:.1%})")