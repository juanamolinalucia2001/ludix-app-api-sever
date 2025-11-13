#!/bin/bash

# Script para ejecutar tests de Ludix API con Supabase
echo "🧪 Ejecutando tests de Ludix API..."

# Colores para output
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
NC='\033[0m' # No Color

# Función para imprimir mensajes coloreados
print_status() {
    echo -e "${BLUE}[INFO]${NC} $1"
}

print_success() {
    echo -e "${GREEN}[SUCCESS]${NC} $1"
}

print_warning() {
    echo -e "${YELLOW}[WARNING]${NC} $1"
}

print_error() {
    echo -e "${RED}[ERROR]${NC} $1"
}

# Verificar si estamos en el directorio correcto
if [ ! -f "main.py" ] || [ ! -f "requirements.txt" ]; then
    print_error "Este script debe ejecutarse desde el directorio raíz del proyecto API"
    exit 1
fi

# Verificar si el entorno virtual está activado
if [ -z "$VIRTUAL_ENV" ]; then
    print_warning "No se detectó un entorno virtual activo"
    print_status "Intentando activar entorno virtual..."
    
    if [ -d ".venv" ]; then
        source .venv/bin/activate
        print_success "Entorno virtual activado"
    elif [ -d "venv" ]; then
        source venv/bin/activate
        print_success "Entorno virtual activado"
    else
        print_error "No se encontró entorno virtual. Crea uno con: python -m venv .venv"
        exit 1
    fi
fi

# Verificar instalación de dependencias de testing
print_status "Verificando dependencias de testing..."
python -c "import pytest, httpx" 2>/dev/null || {
    print_warning "Instalando dependencias de testing..."
    pip install pytest pytest-asyncio httpx coverage pytest-cov
}

# Crear archivo .env para testing si no existe
if [ ! -f ".env" ]; then
    print_status "Creando archivo .env para testing..."
    cat > .env << EOF
# Configuración para testing
DEBUG=True
SECRET_KEY=test-secret-key-for-ludix
DATABASE_URL=sqlite:///./test_ludix.db

# Supabase configuration (opcional para tests)
SUPABASE_URL=https://test.supabase.co
SUPABASE_KEY=test-anon-key
SUPABASE_SERVICE_KEY=test-service-key

# Test environment
ENVIRONMENT=test
EOF
    print_success "Archivo .env creado"
fi

# Función para ejecutar tests con diferentes niveles
run_tests() {
    local test_type=$1
    local test_path=$2
    local description=$3
    
    echo ""
    print_status "🧪 Ejecutando $description..."
    echo "=================================================="
    
    case $test_type in
        "basic")
            pytest $test_path -v --tb=short
            ;;
        "coverage")
            pytest $test_path --cov=. --cov-report=term-missing --cov-report=html
            ;;
        "verbose")
            pytest $test_path -v -s --tb=long
            ;;
        "markers")
            pytest $test_path -v -m "$test_path"
            ;;
        *)
            pytest $test_path -v
            ;;
    esac
    
    local exit_code=$?
    if [ $exit_code -eq 0 ]; then
        print_success "$description completados exitosamente"
    else
        print_error "$description fallaron (código: $exit_code)"
        return $exit_code
    fi
}

# Parsear argumentos
case "${1:-all}" in
    "smoke")
        print_status "🔥 Ejecutando smoke tests..."
        run_tests basic "tests/test_basic.py::TestBasicEndpoints::test_root_endpoint tests/test_basic.py::TestBasicEndpoints::test_health_check_endpoint" "Smoke Tests"
        ;;
    
    "auth")
        print_status "🔐 Ejecutando tests de autenticación..."
        run_tests basic "tests/test_auth.py" "Tests de Autenticación"
        ;;
    
    "users")
        print_status "👥 Ejecutando tests de usuarios..."
        run_tests basic "tests/test_users.py" "Tests de Usuarios"
        ;;
    
    "games")
        print_status "🎮 Ejecutando tests de juegos..."
        run_tests basic "tests/test_games.py" "Tests de Juegos"
        ;;
    
    "supabase")
        print_status "🗄️ Ejecutando tests de Supabase..."
        run_tests basic "tests/test_supabase.py" "Tests de Supabase"
        ;;
    
    "integration")
        print_status "🔗 Ejecutando tests de integración..."
        run_tests basic "tests/test_integration.py" "Tests de Integración"
        ;;
    
    "unit")
        print_status "🔬 Ejecutando tests unitarios..."
        run_tests basic "tests/test_auth.py tests/test_users.py tests/test_games.py tests/test_basic.py" "Tests Unitarios"
        ;;
    
    "coverage")
        print_status "📊 Ejecutando tests con cobertura..."
        run_tests coverage "tests/" "Tests con Cobertura"
        print_status "Reporte de cobertura generado en htmlcov/"
        ;;
    
    "verbose")
        print_status "📝 Ejecutando tests en modo verbose..."
        run_tests verbose "tests/" "Tests Verbose"
        ;;
    
    "fast")
        print_status "⚡ Ejecutando tests rápidos (sin integración)..."
        run_tests basic "tests/ -m 'not integration'" "Tests Rápidos"
        ;;
    
    "all")
        print_status "🚀 Ejecutando toda la suite de tests..."
        
        # Ejecutar tests por categoría
        run_tests basic "tests/test_basic.py" "Tests Básicos" && \
        run_tests basic "tests/test_auth.py" "Tests de Autenticación" && \
        run_tests basic "tests/test_users.py" "Tests de Usuarios" && \
        run_tests basic "tests/test_games.py" "Tests de Juegos" && \
        run_tests basic "tests/test_supabase.py" "Tests de Supabase" && \
        run_tests basic "tests/test_integration.py" "Tests de Integración"
        
        if [ $? -eq 0 ]; then
            print_success "🎉 Todos los tests pasaron exitosamente!"
        else
            print_error "❌ Algunos tests fallaron"
            exit 1
        fi
        ;;
    
    "help"|"-h"|"--help")
        echo "🧪 Script de Tests para Ludix API"
        echo ""
        echo "Uso: $0 [OPCIÓN]"
        echo ""
        echo "Opciones disponibles:"
        echo "  all         - Ejecutar toda la suite de tests (por defecto)"
        echo "  smoke       - Ejecutar solo smoke tests básicos"
        echo "  auth        - Ejecutar tests de autenticación"
        echo "  users       - Ejecutar tests de usuarios"
        echo "  games       - Ejecutar tests de juegos"
        echo "  supabase    - Ejecutar tests de Supabase"
        echo "  integration - Ejecutar tests de integración"
        echo "  unit        - Ejecutar tests unitarios"
        echo "  coverage    - Ejecutar tests con reporte de cobertura"
        echo "  verbose     - Ejecutar tests en modo verbose"
        echo "  fast        - Ejecutar tests rápidos (sin integración)"
        echo "  help        - Mostrar esta ayuda"
        echo ""
        echo "Ejemplos:"
        echo "  $0              # Ejecutar todos los tests"
        echo "  $0 smoke        # Solo smoke tests"
        echo "  $0 auth         # Solo tests de autenticación"
        echo "  $0 coverage     # Tests con cobertura"
        echo ""
        echo "Variables de entorno opcionales:"
        echo "  TEST_SUPABASE_URL     - URL de Supabase para testing"
        echo "  TEST_SUPABASE_KEY     - Key de Supabase para testing"
        echo ""
        exit 0
        ;;
    
    *)
        print_error "Opción no reconocida: $1"
        print_status "Usa '$0 help' para ver opciones disponibles"
        exit 1
        ;;
esac

# Cleanup
print_status "🧹 Limpiando archivos temporales de test..."
rm -f test_ludix.db
rm -rf .pytest_cache
rm -rf __pycache__
find tests/ -name "__pycache__" -type d -exec rm -rf {} + 2>/dev/null

print_success "✅ Tests completados!"
echo ""
echo "📋 Próximos pasos:"
echo "   • Revisa los resultados de los tests arriba"
echo "   • Para tests con cobertura: $0 coverage"
echo "   • Para tests específicos: $0 [auth|users|games|supabase]"
echo "   • Para debug: $0 verbose"
echo ""
