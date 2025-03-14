import os
import requests
from flask import Flask, request, jsonify
from youtube_transcript_api import YouTubeTranscriptApi

app = Flask(__name__)

# Clave de API de DeepSeek para resumir el texto
DEEPSEEK_API_KEY = os.getenv("DEEPSEEK_API_KEY")


def obtener_transcripcion(video_id):
    """Obtiene la transcripción automática de un video de YouTube sin usar OAuth."""
    try:
        transcript = YouTubeTranscriptApi.get_transcript(video_id, languages=['es'])
        texto_completo = "\n".join([t["text"] for t in transcript])
        return texto_completo
    except Exception as e:
        print("Error al obtener la transcripción:", str(e))
        return None


def obtener_resumen(subtitulos):
    """Envía la transcripción a DeepSeek AI para generar un resumen."""
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

    response = requests.post("https://api.deepseek.com/chat/completions", headers=headers, json=data)

    if response.status_code == 200:
        return response.json()["choices"][0]["message"]["content"]
    else:
        print("Error al generar resumen:", response.text)
        return None


@app.route("/procesar-video", methods=["POST"])
def procesar_video():
    """Recibe un video ID, obtiene transcripción y genera un resumen."""
    data = request.get_json()
    video_id = data.get("video_id")

    if not video_id:
        return jsonify({"error": "No se proporcionó un video_id"}), 400

    transcripcion = obtener_transcripcion(video_id)
    if not transcripcion:
        return jsonify({"error": "No se pudo obtener la transcripción"}), 500

    resumen = obtener_resumen(transcripcion)
    if not resumen:
        return jsonify({"error": "Error al generar el resumen"}), 500

    return jsonify({"resumen": resumen})


if __name__ == "__main__":
    app.run(host="0.0.0.0", port=8080)
