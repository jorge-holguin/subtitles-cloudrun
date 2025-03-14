import os
import logging
import requests
from flask import Flask, request, jsonify
from youtube_transcript_api import YouTubeTranscriptApi

# Configurar logging para Cloud Run
logging.basicConfig(level=logging.INFO)

app = Flask(__name__)

# API Key de DeepSeek desde variables de entorno
DEEPSEEK_API_KEY = os.getenv("DEEPSEEK_API_KEY")


def obtener_transcripcion(video_id):
    """
    Obtiene la transcripción automática de un video de YouTube sin usar OAuth.
    Si no hay subtítulos en español, intenta obtenerlos en cualquier idioma.
    """
    try:
        logging.info(f"Intentando obtener transcripción en español para el video: {video_id}")
        transcript = YouTubeTranscriptApi.get_transcript(video_id, languages=['es'])
    except:
        try:
            logging.info(f"No se encontró transcripción en español. Intentando en cualquier idioma...")
            transcript = YouTubeTranscriptApi.get_transcript(video_id)
        except Exception as e:
            logging.error(f"Error al obtener la transcripción del video {video_id}: {str(e)}")
            return None

    texto_completo = "\n".join([t["text"] for t in transcript])
    logging.info("✅ Transcripción obtenida correctamente.")
    return texto_completo


def obtener_resumen(subtitulos):
    """
    Envía la transcripción a DeepSeek AI para generar un resumen.
    """
    if not DEEPSEEK_API_KEY:
        logging.error("🚨 No se encontró la API Key de DeepSeek. Configura la variable de entorno.")
        return None

    headers = {
        "Content-Type": "application/json",
        "Authorization": f"Bearer {DEEPSEEK_API_KEY}"
    }

    data = {
        "model": "deepseek-chat",
        "messages": [
            {"role": "system", "content": "Eres un asistente que resume textos."},
            {"role": "user", "content": f"Resume el siguiente texto en español:\n\n{subtitulos}"}
        ],
        "stream": False
    }

    try:
        response = requests.post("https://api.deepseek.com/chat/completions", headers=headers, json=data)
        response.raise_for_status()
        resumen = response.json()["choices"][0]["message"]["content"]
        logging.info("✅ Resumen generado correctamente.")
        return resumen
    except Exception as e:
        logging.error(f"🚨 Error al generar resumen con DeepSeek: {str(e)}")
        return None


@app.route("/procesar-video", methods=["POST"])
def procesar_video():
    """
    Recibe un video ID, obtiene la transcripción y genera un resumen con IA.
    """
    data = request.get_json()
    video_id = data.get("video_id")

    if not video_id:
        return jsonify({"error": "No se proporcionó un video_id"}), 400

    logging.info(f"📥 Procesando video: {video_id}")

    transcripcion = obtener_transcripcion(video_id)
    if not transcripcion:
        return jsonify({"error": "No se pudo obtener la transcripción"}), 500

    resumen = obtener_resumen(transcripcion)
    if not resumen:
        return jsonify({"error": "Error al generar el resumen"}), 500

    return jsonify({"resumen": resumen})


if __name__ == "__main__":
    app.run(host="0.0.0.0", port=8080)
