#!/bin/bash

# Hostify Broadcast Message System - Setup Script
# Este script configura el entorno de desarrollo

set -e

echo "🚀 Configurando Hostify Broadcast Message System..."
echo "=" * 50

# Verificar Python
if ! command -v python3 &> /dev/null; then
    echo "❌ Python 3 no está instalado. Por favor instálalo primero."
    exit 1
fi

echo "✅ Python 3 encontrado: $(python3 --version)"

# Crear entorno virtual si no existe
if [ ! -d "venv" ]; then
    echo "📦 Creando entorno virtual..."
    python3 -m venv venv
else
    echo "✅ Entorno virtual ya existe"
fi

# Activar entorno virtual
echo "🔄 Activando entorno virtual..."
source venv/bin/activate

# Instalar dependencias
echo "📚 Instalando dependencias..."
pip install -r requirements.txt

# Crear archivo .env si no existe
if [ ! -f ".env" ]; then
    echo "⚙️ Creando archivo de configuración..."
    cp .env.example .env
    echo "⚠️  IMPORTANTE: Edita el archivo .env con tu API key de Hostify"
else
    echo "✅ Archivo .env ya existe"
fi

# Dar permisos de ejecución al script principal
chmod +x hostify_broadcast_final.py

echo ""
echo "🎉 ¡Configuración completada!"
echo ""
echo "📋 Próximos pasos:"
echo "1. Edita el archivo .env con tu API key de Hostify"
echo "2. Activa el entorno virtual: source venv/bin/activate"
echo "3. Ejecuta el sistema: python3 hostify_broadcast_final.py"
echo ""
echo "📖 Para más información, consulta README.md"
