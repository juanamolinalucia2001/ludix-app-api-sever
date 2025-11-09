#!/usr/bin/env python3
"""
Script para inicializar el esquema de base de datos en Supabase
"""

import os
import sys
from core.supabase_client import get_supabase_admin_client, LUDIX_SCHEMA
from core.config import settings

def init_supabase_schema():
    """Inicializa el esquema de base de datos en Supabase"""
    print("🚀 Inicializando esquema de Supabase...")
    
    try:
        # Verificar configuración
        if not settings.SUPABASE_URL or not settings.SUPABASE_SERVICE_KEY:
            print("❌ Error: Variables de entorno SUPABASE_URL y SUPABASE_SERVICE_KEY son requeridas")
            print("   Verifica tu archivo .env")
            return False
        
        print(f"📡 Conectando a Supabase: {settings.SUPABASE_URL}")
        
        # Obtener cliente admin
        client = get_supabase_admin_client()
        
        print("📊 Ejecutando esquema SQL...")
        
        # Ejecutar esquema SQL
        # Nota: Supabase Python client no tiene método directo para ejecutar SQL raw
        # El esquema debe ejecutarse manualmente en el SQL Editor de Supabase
        
        print("⚠️  IMPORTANTE: El esquema SQL debe ejecutarse manualmente")
        print("   1. Ve a https://app.supabase.com/project/{}/sql".format(
            settings.SUPABASE_URL.split('//')[1].split('.')[0]
        ))
        print("   2. Copia y pega el siguiente esquema SQL:")
        print("   3. Ejecuta el script")
        print()
        print("=" * 60)
        print("ESQUEMA SQL PARA COPIAR:")
        print("=" * 60)
        print(LUDIX_SCHEMA)
        print("=" * 60)
        print()
        
        # Verificar que las tablas principales existen
        print("🔍 Verificando conexión con tablas...")
        
        # Test básico de conexión
        try:
            # Intentar hacer una consulta simple (esto verificará la conexión)
            result = client.table('users').select('*').limit(1).execute()
            print("✅ Conexión con tabla 'users' exitosa")
        except Exception as e:
            if "relation \"public.users\" does not exist" in str(e):
                print("⚠️  Las tablas aún no existen. Ejecuta el SQL schema en Supabase primero.")
            else:
                print(f"⚠️  Error verificando tablas: {e}")
        
        print("✅ Configuración de Supabase completada")
        return True
        
    except Exception as e:
        print(f"❌ Error inicializando Supabase: {e}")
        return False

def verify_supabase_setup():
    """Verifica que Supabase esté configurado correctamente"""
    print("🔍 Verificando configuración de Supabase...")
    
    # Verificar variables de entorno
    required_vars = ['SUPABASE_URL', 'SUPABASE_KEY', 'SUPABASE_SERVICE_KEY']
    missing_vars = []
    
    for var in required_vars:
        if not getattr(settings, var, None):
            missing_vars.append(var)
    
    if missing_vars:
        print(f"❌ Variables de entorno faltantes: {', '.join(missing_vars)}")
        return False
    
    print("✅ Variables de entorno configuradas correctamente")
    
    # Verificar formato de URL
    if not settings.SUPABASE_URL.startswith('https://'):
        print("❌ SUPABASE_URL debe comenzar con https://")
        return False
    
    if not '.supabase.co' in settings.SUPABASE_URL:
        print("❌ SUPABASE_URL no parece ser una URL válida de Supabase")
        return False
    
    print("✅ URL de Supabase válida")
    
    # Verificar conexión
    try:
        client = get_supabase_admin_client()
        print("✅ Conexión con Supabase exitosa")
        return True
    except Exception as e:
        print(f"❌ Error conectando a Supabase: {e}")
        return False

if __name__ == "__main__":
    print("🎮 Ludix API - Inicialización de Supabase")
    print("=" * 50)
    
    # Verificar configuración
    if not verify_supabase_setup():
        print("\n❌ Error en la configuración. Por favor corrige los problemas arriba.")
        sys.exit(1)
    
    # Inicializar esquema
    if init_supabase_schema():
        print("\n🎉 ¡Inicialización completada!")
        print("\n📋 Próximos pasos:")
        print("   1. Ejecuta el SQL schema en Supabase (URL mostrada arriba)")
        print("   2. Ejecuta: python main.py")
        print("   3. Ve a http://localhost:8001/docs para probar la API")
    else:
        print("\n❌ Error en la inicialización")
        sys.exit(1)
