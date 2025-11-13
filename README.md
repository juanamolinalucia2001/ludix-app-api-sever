# 🎮 Ludix API Server

Backend para la plataforma educativa Ludix — Gamificación del aprendizaje.

Deploy público (producción)
- https://ludix-app-api-sever.onrender.com/

## 🌟 Características

- 🔐 Autenticación JWT con roles (estudiante / profesor)
- 📊 Base de datos en la nube con Supabase (soporta suscripciones en tiempo real)
- 🎯 Gamificación: quizzes, puntos y seguimiento de progreso
- 🏗️ Uso de patrones de diseño (Factory, Observer, Decorator, Singleton)
- 🚀 API REST documentada con FastAPI

## 🚀 Cómo empezar (rápido)

A continuación tienes las dos opciones principales: con Supabase (recomendado) o con SQLite local.

### Opción A — Con Supabase (Recomendado)

1. Ejecutar script de configuración (si está disponible)
```bash
./setup_supabase.sh
```

2. Crear proyecto en Supabase
- Ir a https://supabase.com y crear un nuevo proyecto
- Copiar las credenciales desde Settings > API

3. Configurar variables de entorno (archivo .env)
```bash
# .env
SUPABASE_URL=https://tu-proyecto.supabase.co
SUPABASE_KEY=tu-anon-key
SUPABASE_SERVICE_KEY=tu-service-key
SECRET_KEY=una-clave-secreta-para-jwt
```

4. Crear esquema de base de datos
- Abrir SQL Editor en Supabase y ejecutar el schema (si lo provee el repositorio)
- En este repo puede revisarse el cliente en `core/supabase_client.py` para referencias

5. Ejecutar servidor (desarrollo)
```bash
# Activar entorno virtual si corresponde
source .venv/bin/activate

# Instalar dependencias
pip install -r requirements.txt

# Ejecutar
python main.py
# o con uvicorn para recarga automática:
uvicorn main:app --reload --host 0.0.0.0 --port 8000
```

### Opción B — SQLite (Local, para pruebas)

```bash
# Activar entorno virtual
source .venv/bin/activate

# Instalar dependencias
pip install -r requirements.txt

# Inicializar base de datos local (si existe script)
python init_db.py

# Ejecutar servidor
python main.py
# o
uvicorn main:app --reload --host 127.0.0.1 --port 8000
```

## Probar la API

- Endpoint base local (por defecto): http://127.0.0.1:8000/
- Documentación automática (si FastAPI está configurado): http://127.0.0.1:8000/docs

Probar el deploy en producción:
```bash
curl https://ludix-app-api-sever.onrender.com/
```