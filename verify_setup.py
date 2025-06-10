#!/usr/bin/env python3
"""
Script de verificación para Hostify Broadcast Message System
Verifica que todo esté configurado correctamente antes del primer uso.
"""

import os
import sys
import importlib.util

def check_python_version():
    """Verifica la versión de Python"""
    if sys.version_info < (3, 7):
        print("❌ Se requiere Python 3.7 o superior")
        return False
    print(f"✅ Python {sys.version.split()[0]} - OK")
    return True

def check_dependencies():
    """Verifica que las dependencias estén instaladas"""
    required_packages = ['requests', 'python-dotenv']
    missing = []
    
    for package in required_packages:
        try:
            if package == 'python-dotenv':
                import dotenv
            else:
                __import__(package)
            print(f"✅ {package} - Instalado")
        except ImportError:
            print(f"❌ {package} - NO instalado")
            missing.append(package)
    
    return len(missing) == 0

def check_env_file():
    """Verifica la configuración del archivo .env"""
    if not os.path.exists('.env'):
        print("❌ Archivo .env no encontrado")
        print("   Ejecuta: cp .env.example .env")
        return False
    
    print("✅ Archivo .env encontrado")
    
    # Verificar que tenga la API key
    with open('.env', 'r') as f:
        content = f.read()
        if 'tu_api_key' in content or not content.strip():
            print("⚠️  Archivo .env necesita configuración")
            print("   Edita .env con tu API key de Hostify")
            return False
    
    print("✅ Archivo .env configurado")
    return True

def check_main_script():
    """Verifica que el script principal exista y sea ejecutable"""
    if not os.path.exists('hostify_broadcast_final.py'):
        print("❌ Script principal no encontrado")
        return False
    
    print("✅ Script principal encontrado")
    
    # Verificar permisos de ejecución
    if os.access('hostify_broadcast_final.py', os.X_OK):
        print("✅ Permisos de ejecución - OK")
    else:
        print("⚠️  Añadiendo permisos de ejecución...")
        os.chmod('hostify_broadcast_final.py', 0o755)
    
    return True

def test_import():
    """Intenta importar el módulo principal"""
    try:
        from hostify_broadcast_final import MessageProcessor
        print("✅ Importación del módulo principal - OK")
        return True
    except Exception as e:
        print(f"❌ Error al importar módulo principal: {e}")
        return False

def main():
    """Función principal de verificación"""
    print("🔍 VERIFICACIÓN DEL SISTEMA")
    print("=" * 50)
    
    checks = [
        ("Versión de Python", check_python_version),
        ("Dependencias", check_dependencies),
        ("Archivo de configuración", check_env_file),
        ("Script principal", check_main_script),
        ("Importación de módulos", test_import)
    ]
    
    passed = 0
    total = len(checks)
    
    for name, check_func in checks:
        print(f"\n🔄 Verificando {name}...")
        if check_func():
            passed += 1
        else:
            print(f"   ❌ {name} falló")
    
    print("\n" + "=" * 50)
    print(f"📊 RESULTADO: {passed}/{total} verificaciones pasadas")
    
    if passed == total:
        print("🎉 ¡Sistema listo para usar!")
        print("\nPuedes ejecutar:")
        print("  python3 hostify_broadcast_final.py")
    else:
        print("⚠️  Sistema requiere configuración adicional")
        print("\nPasos recomendados:")
        if passed < total - 1:
            print("1. Ejecuta: ./setup.sh")
        print("2. Edita .env con tu API key de Hostify")
        print("3. Ejecuta este script nuevamente")

if __name__ == "__main__":
    main()
