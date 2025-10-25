# 🎮 Ludix API Server

Backend para la plataforma educativa Ludix - Gamificación del aprendizaje

## 🌟 Características

- 🔐 **Autenticación JWT** con roles (estudiante/profesor)
- 📊 **Base de datos en la nube** con Supabase
- 🎯 **Gamificación** con quizzes y seguimiento de progreso
- 🏗️ **Patrones de diseño** (Factory, Observer, Decorator, Singleton)
- 🚀 **API REST** documentada con FastAPI
- 🔄 **Real-time** con Supabase subscriptions

## 🚀 Configuración Rápida

### Opción A: Con Supabase (Recomendado)

1. **Ejecutar script de configuración**
```bash
./setup_supabase.sh
```

2. **Crear proyecto en Supabase**
   - Ve a [supabase.com](https://supabase.com) 
   - Crea un nuevo proyecto
   - Copia las credenciales desde Settings > API

3. **Configurar variables de entorno**
```bash
# Editar .env
SUPABASE_URL=https://tu-proyecto.supabase.co
SUPABASE_KEY=tu-anon-key
SUPABASE_SERVICE_KEY=tu-service-key
```

4. **Crear esquema de base de datos**
   - Ve al SQL Editor en Supabase
   - Copia y ejecuta el schema desde `core/supabase_client.py`

5. **Ejecutar servidor**
```bash
python main.py
```

### Opción B: Con SQLite Local

```bash
# Activar entorno virtual
source .venv/bin/activate

# Instalar dependencias
pip install -r requirements.txt

# Inicializar base de datos
python init_db.py

# Ejecutar servidor
python main.py
```