import os
import requests
from flask import Flask, request, jsonify

app = Flask(__name__)

# Claves de API desde variables de entorno
YOUTUBE_API_KEY = os.getenv("YOUTUBE_API_KEY")
YOUTUBE_OAUTH_TOKEN = os.getenv("YOUTUBE_OAUTH_TOKEN")  # Token OAuth
DEEPSEEK_API_KEY = os.getenv("DEEPSEEK_API_KEY")


def obtener_id_subtitulos(video_id):
    """Obtiene el ID de los subtítulos estándar (o ASR si no hay estándar)."""
    url = f"https://www.googleapis.com/youtube/v3/captions?part=snippet&videoId={video_id}&key={YOUTUBE_API_KEY}"
    response = requests.get(url)
    data = response.json()

    if "items" in data:
        standard_id = None
        asr_id = None

        for item in data["items"]:
            track_kind = item["snippet"]["trackKind"]
            language = item["snippet"]["language"]
            caption_id = item["id"]

            print(f"Subtítulo encontrado: {caption_id} - Tipo: {track_kind} - Idioma: {language}")

            if track_kind == "standard" and language.startswith("es"):
                standard_id = caption_id  # Guarda el ID del subtítulo estándar en español
            elif track_kind == "asr" and language.startswith("es"):
                asr_id = caption_id  # Guarda el ID del subtítulo automático en español

        # Priorizar subtítulos estándar
        if standard_id:
            print(f"Usando subtítulo estándar: {standard_id}")
            return standard_id
        elif asr_id:
            print(f"Usando subtítulo ASR: {asr_id}")
            return asr_id

    print("No se encontraron subtítulos.")
    return None


def descargar_subtitulos(caption_id):
    """Descarga los subtítulos usando OAuth."""
    url = f"https://www.googleapis.com/youtube/v3/captions/{caption_id}?tfmt=srt"
    headers = {
        "Authorization": f"Bearer {YOUTUBE_OAUTH_TOKEN}"
    }

    response = requests.get(url, headers=headers)

    if response.status_code == 200:
        return response.text  # Retorna los subtítulos en formato SRT
    else:
        print("Error al descargar subtítulos:", response.text)
        return None


def obtener_resumen(subtitulos):
    """Envía los subtítulos a DeepSeek AI para generar un resumen."""
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
    """Recibe un video ID, obtiene subtítulos y genera un resumen."""
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
