# Usa una imagen ligera de Python
FROM python:3.9

# Establecer el directorio de trabajo dentro del contenedor
WORKDIR /app

# Copiar los archivos necesarios al contenedor
COPY requirements.txt .
COPY app.py .

# Instalar las dependencias y verificar que se instalen correctamente
RUN pip install --no-cache-dir -r requirements.txt && \
    pip list  # Agregar esta línea para mostrar qué paquetes se instalaron

# Exponer el puerto 8080 (necesario para Cloud Run)
EXPOSE 8080

# Ejecutar la aplicación con Gunicorn
CMD ["gunicorn", "--bind", "0.0.0.0:8080", "app:app"]
