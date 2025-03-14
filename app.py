import os
import logging
import random
import requests
from flask import Flask, request, jsonify
from youtube_transcript_api import YouTubeTranscriptApi

app = Flask(__name__)

logging.basicConfig(level=logging.INFO)

# API Key de DeepSeek desde variables de entorno
DEEPSEEK_API_KEY = os.getenv("DEEPSEEK_API_KEY")

# Lista de proxies de Webshare.io (Pega aquí tus proxies)
PROXIES_LIST = [
    "http://bzdgdeyv:y4ggqycpywv5@38.154.227.167:5868",
    "http://bzdgdeyv:y4ggqycpywv5@38.153.152.244:9594",
    "http://bzdgdeyv:y4ggqycpywv5@86.38.234.176:6630",
    "http://bzdgdeyv:y4ggqycpywv5@173.211.0.148:6641",
    "http://bzdgdeyv:y4ggqycpywv5@161.123.152.115:6360",
    "http://bzdgdeyv:y4ggqycpywv5@216.10.27.159:6837",
    "http://bzdgdeyv:y4ggqycpywv5@64.64.118.149:6732",
    "http://bzdgdeyv:y4ggqycpywv5@104.239.105.125:6655",
    "http://bzdgdeyv:y4ggqycpywv5@166.88.58.10:5735",
    "http://bzdgdeyv:y4ggqycpywv5@45.151.162.198:6600",
]

def obtener_proxy():
    """Selecciona un proxy aleatorio de la lista."""
    proxy_url = random.choice(PROXIES_LIST)
    return {"http": proxy_url, "https": proxy_url}

def obtener_transcripcion(video_id):
    """
    Obtiene la transcripción del video de YouTube usando Webshare.io.
    """
    for _ in range(3):  # Intentar hasta 3 veces con diferentes proxies
        proxy = obtener_proxy()
        try:
            logging.info(f"🔎 Intentando obtener transcripción con proxy: {proxy}")
            transcript = YouTubeTranscriptApi.get_transcript(video_id, languages=['es'], proxies=proxy)
            texto_completo = "\n".join([t["text"] for t in transcript])
            logging.info("✅ Transcripción obtenida correctamente.")
            return texto_completo
        except Exception as e:
            logging.warning(f"⚠️ Fallo al obtener transcripción con este proxy: {str(e)}")
    
    logging.error("🚨 No se pudo obtener la transcripción después de múltiples intentos.")
    return None

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
