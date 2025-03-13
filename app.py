import os
import requests
import json
from flask import Flask, request, jsonify

# Cargar claves de API desde variables de entorno
YOUTUBE_API_KEY = os.getenv("YOUTUBE_API_KEY")
DEEPSEEK_API_KEY = os.getenv("DEEPSEEK_API_KEY")

app = Flask(__name__)

def obtener_id_subtitulos(video_id):
    """Obtiene el ID del subtítulo (ASR si está disponible, sino standard)."""
    url = f"https://www.googleapis.com/youtube/v3/captions?part=snippet&videoId={video_id}&key={YOUTUBE_API_KEY}"
    response = requests.get(url)
    data = response.json()

    if "items" in data:
        for item in data["items"]:
            track_kind = item["snippet"]["trackKind"]
            language = item["snippet"]["language"]
            caption_id = item["id"]

            # Prioriza subtítulos ASR en español
            if track_kind == "asr" and language == "es":
                return caption_id

        # Si no hay ASR, devuelve el primero disponible
        return data["items"][0]["id"]

    return None


def descargar_subtitulos(caption_id):
    """Descarga los subtítulos usando el ID obtenido"""
    url = f"https://www.googleapis.com/youtube/v3/captions/{caption_id}?tfmt=srt&key={YOUTUBE_API_KEY}"
    response = requests.get(url)

    if response.status_code == 200:
        return response.text
    return None

def obtener_resumen(subtitulos):
    """Envía los subtítulos a DeepSeek AI para generar un resumen"""
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
    return None

@app.route("/procesar-video", methods=["POST"])
def procesar_video():
    """Recibe un video ID, obtiene subtítulos y genera un resumen"""
    data = request.get_json()
    video_id = data.get("video_id")

    if not video_id:
        return jsonify({"error": "No se proporcionó un video_id"}), 400

    caption_id = obtener_id_subtitulos(video_id)
    if not caption_id:
        return jsonify({"error": "No se encontraron subtítulos"}), 404

    subtitulos = descargar_subtitulos(caption_id)
    if not subtitulos:
        return jsonify({"error": "Error al descargar los subtítulos"}), 500

    resumen = obtener_resumen(subtitulos)
    if not resumen:
        return jsonify({"error": "Error al generar el resumen"}), 500

    return jsonify({"resumen": resumen})

if __name__ == "__main__":
    app.run(host="0.0.0.0", port=8080)
