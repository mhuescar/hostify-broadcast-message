#!/usr/bin/env python3
"""
Ejemplo de uso del Hostify Broadcast Message System
Este script muestra cómo usar las funciones principales del sistema
"""

from hostify_broadcast_final import (
    MessageProcessor, 
    broadcast_message_to_specific_listing,
    broadcast_message_to_all_future_bookings,
    load_message_from_file
)

def ejemplo_mensaje_simple():
    """Ejemplo 1: Enviar mensaje simple a una propiedad específica"""
    print("📝 EJEMPLO 1: Mensaje simple a propiedad específica")
    print("=" * 60)
    
    # Mensaje con variables que se reemplazarán automáticamente
    mensaje = "Hola {{guest_name}}, tu check-in está listo: {{chekin_signup_form_link}}"
    
    # ID de propiedad de ejemplo (cambiar por uno real)
    listing_id = "196240"
    
    # Enviar mensaje
    resultado = broadcast_message_to_specific_listing(listing_id, mensaje)
    
    print(f"\n📊 Resultado:")
    print(f"   - Reservas procesadas: {resultado['total_bookings']}")
    print(f"   - Mensajes enviados: {resultado['messages_sent']}")
    print(f"   - Errores: {len(resultado['errors'])}")

def ejemplo_mensaje_desde_archivo():
    """Ejemplo 2: Cargar mensaje desde archivo y enviar masivamente"""
    print("\n📄 EJEMPLO 2: Mensaje desde archivo - Envío masivo")
    print("=" * 60)
    
    # Cargar mensaje desde archivo
    mensaje = load_message_from_file("mensaje_prueba_final")
    
    if not mensaje:
        print("❌ No se pudo cargar el mensaje del archivo")
        return
    
    print(f"✅ Mensaje cargado: {mensaje}")
    
    # ADVERTENCIA: Esto enviará a TODAS las propiedades
    # Descomenta la siguiente línea solo si estás seguro
    # resultado = broadcast_message_to_all_future_bookings(mensaje)
    
    print("⚠️  Envío masivo comentado por seguridad")
    print("   Descomenta la línea en el código para ejecutar")

def ejemplo_verificacion_sistema():
    """Ejemplo 3: Verificar que el sistema esté funcionando"""
    print("\n🔍 EJEMPLO 3: Verificación del sistema")
    print("=" * 60)
    
    try:
        # Inicializar procesador de mensajes
        processor = MessageProcessor()
        
        print(f"✅ APIs disponibles:")
        print(f"   - Hostify: ✅")
        print(f"   - Chekin: {'✅' if processor.chekin.is_available else '❌'}")
        
        # Obtener propiedades para verificar conexión
        propiedades = processor.hostify.get_active_properties()
        print(f"✅ Propiedades encontradas: {len(propiedades)}")
        
        if propiedades:
            # Mostrar ejemplos de propiedades
            print(f"\n📋 Primeras 3 propiedades:")
            for i, prop in enumerate(propiedades[:3]):
                prop_id = prop.get('id', 'N/A')
                prop_name = prop.get('name', 'Sin nombre')[:40]
                print(f"   {i+1}. ID: {prop_id} - {prop_name}...")
        
    except Exception as e:
        print(f"❌ Error: {e}")
        print("   Verifica tu configuración en .env")

def ejemplo_mensaje_personalizado():
    """Ejemplo 4: Crear mensaje con todas las variables disponibles"""
    print("\n🎨 EJEMPLO 4: Mensaje con todas las variables")
    print("=" * 60)
    
    mensaje_completo = """
Hola {{guest_name}},

¡Bienvenido a {{property_name}}!

📅 Detalles de tu reserva:
   • Check-in: {{checkin_date}}
   • Check-out: {{checkout_date}}
   • Huéspedes: {{guests_count}}
   • Reserva #{{reservation_id}}
   • Canal: {{booking_source}}

🔗 Completa tu check-in aquí: {{chekin_signup_form_link}}

¡Esperamos que disfrutes tu estancia!
    """.strip()
    
    print("📝 Mensaje con todas las variables:")
    print(mensaje_completo)
    print("\n✅ Variables disponibles:")
    variables = [
        "{{guest_name}} - Nombre del huésped",
        "{{chekin_signup_form_link}} - URL real de check-in",
        "{{checkin_date}} - Fecha de llegada", 
        "{{checkout_date}} - Fecha de salida",
        "{{reservation_id}} - ID de la reserva",
        "{{guests_count}} - Número de huéspedes",
        "{{property_name}} - Nombre de la propiedad",
        "{{booking_source}} - Canal de reserva"
    ]
    
    for var in variables:
        print(f"   • {var}")

def main():
    """Función principal - ejecuta todos los ejemplos"""
    print("🏠 EJEMPLOS DE USO - HOSTIFY BROADCAST SYSTEM")
    print("=" * 80)
    
    try:
        ejemplo_verificacion_sistema()
        ejemplo_mensaje_personalizado()
        ejemplo_mensaje_simple()
        ejemplo_mensaje_desde_archivo()
        
        print("\n" + "=" * 80)
        print("🎉 ¡Ejemplos completados!")
        print("\n💡 Para uso real:")
        print("   python3 hostify_broadcast_final.py")
        
    except Exception as e:
        print(f"\n❌ Error ejecutando ejemplos: {e}")
        print("   Asegúrate de que el sistema esté configurado correctamente")

if __name__ == "__main__":
    main()
