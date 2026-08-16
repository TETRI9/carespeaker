import streamlit as st
import ollama
import whisper
import os
from gtts import gTTS
client_ollama = ollama.Client(host="http://ollama-core:11434")
# Configuración visual de la Startup
st.set_page_config(page_title="CareSpeaker AI", page_icon="👵", layout="centered")

# Memoria para poder borrar la pantalla y key dinámico del micrófono
if "paso_completado" not in st.session_state:
    st.session_state.paso_completado = False
if "texto_espanol" not in st.session_state:
    st.session_state.texto_espanol = ""
if "traduccion_final" not in st.session_state:
    st.session_state.traduccion_final = ""
if "audio_key" not in st.session_state:
    st.session_state.audio_key = 0

st.title("👵 CareSpeaker AI")
st.subheader("Traducción médica por Voz (100% Privada)")

# Idiomas configurados
idiomas_nombres = {
    "Inglés 🇬🇧": "English",
    "Alemán 🇩🇪": "German",
    "Noruego 🇳🇴": "Norwegian",
    "Francés 🇫🇷": "French",
    "Ruso 🇷🇺": "Russian",
    "Neerlandés / Belga 🇧🇪": "Dutch"
}
idiomas_codigos = {
    "Inglés 🇬🇧": "en",
    "Alemán 🇩🇪": "de",
    "Noruego 🇳🇴": "no",
    "Francés 🇫🇷": "fr",
    "Ruso 🇷🇺": "ru",
    "Neerlandés / Belga 🇧🇪": "nl"
}

idioma_seleccionado = st.selectbox("Selecciona el idioma del residente senior:", list(idiomas_nombres.keys()))

# --- 🗑️ BOTÓN DE ELIMINAR / BORRAR TODO ---
if st.button("🗑️ ELIMINAR TEXTOS Y AUDIO (NUEVA ORDEN)", type="primary"):
    st.session_state.paso_completado = False
    st.session_state.texto_espanol = ""
    st.session_state.traduccion_final = ""
    st.session_state.audio_key += 1
    if os.path.exists("output.mp3"):
        os.remove("output.mp3")
    st.rerun()

st.write("---")

@st.cache_resource
def cargar_modelo_whisper():
    return whisper.load_model("base")

model_whisper = cargar_modelo_whisper()

# Micrófono en pantalla con key dinámico para vaciar el widget al reiniciar
audio_recibido = st.audio_input("Presiona el micrófono para dictar la indicación en Español", key=f"audio_{st.session_state.audio_key}")

if audio_recibido and not st.session_state.paso_completado:
    with st.spinner("Procesando tu voz..."):
        try:
            nombre_archivo = "audio_cuidador.wav"
            with open(nombre_archivo, "wb") as f:
                f.write(audio_recibido.getbuffer())
            
            # 1. Transcribir
            resultado_transcripcion = model_whisper.transcribe(nombre_archivo, fp16=False)
            st.session_state.texto_espanol = resultado_transcripcion["text"].strip()
            
            # 2. Traducir con Ollama
            prompt_sistema = (
                f"You are a computer translation API. Translate the user input into {idiomas_nombres[idioma_seleccionado]}. "
                "Output ONLY the raw translated words. Never reply in Spanish. Do not add notes."
            )
            response = client_ollama.chat(
                model='llama3.1',
                messages=[
                    {'role': 'system', 'content': prompt_sistema},
                    {'role': 'user', 'content': "No te olvides de tomar la pastilla."},
                    {'role': 'assistant', 'content': "Do not forget to take your pill."},
                    {'role': 'user', 'content': st.session_state.texto_espanol}
                ]
            )
            st.session_state.traduccion_final = response['message']['content'].strip().replace('"', '')
            
            # 3. Crear Audio Voces
            archivo_voz = "output.mp3"
            if os.path.exists(archivo_voz):
                os.remove(archivo_voz)
            tts = gTTS(text=st.session_state.traduccion_final, lang=idiomas_codigos[idioma_seleccionado])
            tts.save(archivo_voz)
            
            st.session_state.paso_completado = True
            
            if os.path.exists(nombre_archivo):
                os.remove(nombre_archivo)
        except Exception as e:
            st.error(f"Error: {e}")

# Mostrar resultados persistentes en pantalla
if st.session_state.texto_espanol:
    st.info(f"📝 **Texto escuchado (español):** {st.session_state.texto_espanol}")

if st.session_state.traduccion_final:
    st.success("✅ **Traducción Médica para el Senior:**")
    st.markdown(f"<h2 style='color: #4CAF50;'>{st.session_state.traduccion_final}</h2>", unsafe_allow_html=True)
    st.audio("output.mp3", autoplay=True)
