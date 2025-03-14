import os
import logging
import requests
from flask import Flask, request, jsonify
from youtube_transcript_api import YouTubeTranscriptApi

app = Flask(__name__)

logging.basicConfig(level=logging.INFO)

# API Key de DeepSeek desde variables de entorno
DEEPSEEK_API_KEY = os.getenv("DEEPSEEK_API_KEY")

# Configurar ScraperAPI como Proxy
SCRAPERAPI_KEY = os.getenv("SCRAPERAPI_KEY")
SCRAPERAPI_PROXY = f"http://scraperapi:{SCRAPERAPI_KEY}@proxy-server.scraperapi.com:8001" if SCRAPERAPI_KEY else None

proxies = {"http": SCRAPERAPI_PROXY, "https": SCRAPERAPI_PROXY} if SCRAPERAPI_PROXY else None


def obtener_transcripcion(video_id):
    """
    Obtiene la transcripción del video de YouTube usando ScraperAPI como proxy.
    """
    if not SCRAPERAPI_KEY:
        logging.error("🚨 No se encontró la API Key de ScraperAPI. Configura la variable de entorno.")
        return None

    try:
        logging.info(f"🔎 Buscando transcripción en español para el video: {video_id}")
        transcript = YouTubeTranscriptApi.get_transcript(video_id, languages=['es'], proxies=proxies)
    except:
        try:
            logging.info(f"⚠️ No se encontró en español. Buscando en cualquier idioma...")
            transcript = YouTubeTranscriptApi.get_transcript(video_id, proxies=proxies)
        except Exception as e:
            logging.error(f"🚨 Error al obtener la transcripción a través de ScraperAPI: {str(e)}")
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
        return jsonify({"error": "❌ No se proporcionó un video_id"}), 400

    logging.info(f"📥 Procesando video: {video_id}")

    transcripcion = obtener_transcripcion(video_id)
    if not transcripcion:
        return jsonify({"error": "❌ No se pudo obtener la transcripción"}), 500

    resumen = obtener_resumen(transcripcion)
    if not resumen:
        return jsonify({"error": "❌ Error al generar el resumen"}), 500

    return jsonify({"video_id": video_id, "resumen": resumen})


if __name__ == "__main__":
    app.run(host="0.0.0.0", port=8080)
