#!/bin/bash

# Script de configuración para Ludix con Supabase
echo "🚀 Configurando Ludix con Supabase..."

# Activar entorno virtual
echo "📦 Activando entorno virtual..."
source .venv/bin/activate

# Instalar dependencias actualizadas
echo "📥 Instalando dependencias..."
pip install -r requirements.txt

# Verificar instalación de Supabase
echo "🔍 Verificando instalación de Supabase..."
python -c "import supabase; print('✅ Supabase instalado correctamente')" || {
    echo "❌ Error al importar Supabase"
    echo "🔄 Intentando instalación manual..."
    pip install supabase==2.0.0
}

# Crear archivo .env si no existe
if [ ! -f .env ]; then
    echo "📝 Creando archivo .env..."
    cp .env.example .env
    echo "⚠️  IMPORTANTE: Edita el archivo .env con tus credenciales de Supabase"
else
    echo "✅ Archivo .env ya existe"
fi

echo ""
echo "📋 PASOS PARA COMPLETAR LA CONFIGURACIÓN:"
echo ""
echo "1. 🌐 Ve a https://supabase.com y crea un nuevo proyecto"
echo "2. 📊 Copia la URL y las API Keys desde Settings > API"
echo "3. ✏️  Edita el archivo .env con tus credenciales:"
echo "   - SUPABASE_URL=https://tu-proyecto.supabase.co"
echo "   - SUPABASE_KEY=tu-anon-key"
echo "   - SUPABASE_SERVICE_KEY=tu-service-key"
echo ""
echo "4. 🗄️  Ejecuta el SQL schema en el SQL Editor de Supabase:"
echo "   (Copia el contenido de core/supabase_client.py - LUDIX_SCHEMA)"
echo ""
echo "5. 🚀 Ejecuta el servidor:"
echo "   python main.py"
echo ""
echo "💡 Alternativa: Si prefieres usar SQLite local, simplemente:"
echo "   python init_db.py  # Inicializar base de datos local"
echo "   python main.py     # Ejecutar servidor"
echo ""
