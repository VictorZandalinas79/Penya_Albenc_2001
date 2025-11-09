#!/bin/bash

# Nombre del entorno
ENV_NAME="venv311"

# Verifica si Python 3.11 está instalado
if ! command -v python3.11 &> /dev/null
then
    echo "❌ Python 3.11 no está instalado. Instálalo primero (ej. con pyenv o brew)."
    exit 1
fi

# Crear entorno virtual
echo "🐍 Creando entorno virtual con Python 3.11..."
python3.11 -m venv $ENV_NAME

# Activar entorno
source $ENV_NAME/bin/activate

# Actualizar pip
echo "⬆️ Actualizando pip..."
pip install --upgrade pip

# Instalar dependencias
echo "📦 Instalando dependencias desde requirements.txt..."
pip install -r requirements.txt

# Ejecutar la app
echo "🚀 Ejecutando app.py..."
$ENV_NAME/bin/python app.py