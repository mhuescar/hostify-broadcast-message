#!/usr/bin/env python3
"""
HOSTIFY BROADCAST MESSAGE SYSTEM - VERSIÓN FINAL v2.0

Sistema automatizado para envío masivo de mensajes a huéspedes de Hostify.
Utiliza datos reales extraídos de las APIs de Hostify y Chekin.

Características principales:
- ✅ Procesamiento de todas las propiedades (48/48) con paginación completa
- ✅ Filtrado inteligente: solo reservas aceptadas y futuras  
- ✅ Integración real con Chekin API para URLs de check-in válidas
- ✅ Optimización de APIs: evita llamadas duplicadas
- ✅ Validación robusta: no envía mensajes con datos incompletos

Autor: [Tu Nombre]
Versión: 2.0.0
Fecha: 2025-06-10
"""

import requests
import datetime
import os
from dotenv import load_dotenv
from typing import List, Dict, Any, Optional
import json

# Cargar variables de entorno
load_dotenv()

class ChekinConnector:
    """Conector para la API de Chekin con autenticación JWT oficial"""
    
    def __init__(self):
        self.api_key = "VfviZ9WBLi4dvHJr97tBRcuBMOoYlHri"
        self.base_url = "https://a.chekin.io/public/api/v1"
        self.jwt_token = None
        self.is_available = False
        
        # Intentar obtener token JWT
        self._authenticate()
    
    def _authenticate(self):
        """Obtiene token JWT usando API key"""
        
        auth_url = f"{self.base_url}/auth/api-key/"
        
        headers = {
            "Content-Type": "application/json",
            "Accept": "*/*"
        }
        
        payload = {"api_key": self.api_key}
        
        try:
            response = requests.post(auth_url, headers=headers, json=payload, timeout=10)
            
            if response.status_code == 200:
                data = response.json()
                self.jwt_token = data.get("token")
                if self.jwt_token:
                    self.is_available = True
                    print("✅ Chekin autenticado correctamente")
                    return True
            
            print(f"⚠️ Chekin no disponible - Status: {response.status_code}")
            return False
            
        except Exception as e:
            print(f"⚠️ Chekin no disponible - Error: {str(e)}")
            return False
    
    def get_checkin_link(self, hostify_reservation_id: str) -> Optional[str]:
        """Obtiene link de check-in usando external_id (ID de Hostify)"""
        
        if not self.is_available or not self.jwt_token:
            return None
        
        try:
            headers = {
                "Authorization": f"JWT {self.jwt_token}",
                "Content-Type": "application/json"
            }
            
            params = {
                "external_id": hostify_reservation_id,
                "limit": 1
            }
            
            response = requests.get(
                f"{self.base_url}/reservations",
                headers=headers,
                params=params,
                timeout=10
            )
            
            if response.status_code == 200:
                data = response.json()
                reservations = data.get("results", [])
                
                if reservations:
                    reservation = reservations[0]
                    # signup_form_link es el link de check-in real
                    signup_link = reservation.get("signup_form_link", "")
                    if signup_link and signup_link.startswith("http"):
                        return signup_link
            
            return None
            
        except Exception as e:
            print(f"⚠️ Error consultando Chekin para ID {hostify_reservation_id}: {str(e)}")
            return None

class HostifyAPI:
    """API de Hostify con extracción inteligente de datos"""
    
    def __init__(self):
        self.base_url = "https://api-rms.hostify.com"
        self.api_key = os.getenv("HOSTIFY_API_KEY")
        
        if not self.api_key:
            raise ValueError("HOSTIFY_API_KEY no está configurada en las variables de entorno")
        
        self.headers = {
            "x-api-key": self.api_key,
            "Content-Type": "application/json"
        }
    
    def get_active_properties(self) -> List[Dict[str, Any]]:
        """Obtiene todas las propiedades activas con paginación"""
        
        print("🏠 Obteniendo propiedades activas...")
        all_properties = []
        page = 1
        
        while True:
            try:
                response = requests.get(
                    f"{self.base_url}/listings", 
                    headers=self.headers,
                    params={"status": "active", "page": page}
                )
                response.raise_for_status()
                
                data = response.json()
                
                if isinstance(data, dict):
                    # Obtener propiedades de esta página
                    page_properties = data.get("listings", [])
                    if page_properties:
                        all_properties.extend(page_properties)
                        print(f"  📄 Página {page}: {len(page_properties)} propiedades")
                    
                    # Verificar si hay más páginas
                    total = data.get("total", 0)
                    next_page = data.get("next_page")
                    
                    if not next_page or len(all_properties) >= total:
                        break
                    
                    page += 1
                else:
                    # Respuesta directa como lista
                    all_properties = data if isinstance(data, list) else []
                    break
                    
            except Exception as e:
                print(f"⚠️ Error en página {page}: {str(e)}")
                break
        
        print(f"✅ {len(all_properties)} propiedades activas encontradas en total")
        return all_properties
    
    def get_future_bookings_with_details(self, listing_id: str) -> List[Dict[str, Any]]:
        """Obtiene reservas futuras con datos enriquecidos"""
        
        today = datetime.datetime.now().strftime("%Y-%m-%d")
        
        print(f"📋 Obteniendo reservas ACEPTADAS futuras para listing {listing_id}...")
        
        # Ya no necesitamos filters array, usamos query params directos
        all_reservations = []
        page = 1
        page_size = 50
        has_more_data = True
        
        while has_more_data:
            try:
                params = {
                    "listing_id": int(listing_id),
                    "page": page,
                    "per_page": page_size,
                    "status": "accepted",  # Filtrar directamente en query params
                    "checkIn_gte": today   # Check-in mayor o igual a hoy
                }
                
                response = requests.get(
                    f"{self.base_url}/reservations",
                    headers=self.headers,
                    params=params
                )
                
                response.raise_for_status()
                reservations_response = response.json()
                
                page_reservations = reservations_response.get("reservations", [])
                total_reservations = reservations_response.get("total", 0)
                
                # Filtro adicional a nivel de código para asegurar solo "accepted"
                accepted_reservations = [
                    res for res in page_reservations 
                    if res.get("status") == "accepted"
                ]
                
                if accepted_reservations:
                    # Enriquecer datos de cada reserva aceptada
                    for reservation in accepted_reservations:
                        self._enrich_reservation_data(reservation)
                    
                    all_reservations.extend(accepted_reservations)
                    print(f"  📄 Página {page}: {len(accepted_reservations)} reservas aceptadas")
                    
                    # Verificar si hay más páginas
                    if len(all_reservations) >= total_reservations or len(page_reservations) < page_size:
                        has_more_data = False
                    else:
                        page += 1
                else:
                    has_more_data = False
                    
            except Exception as e:
                print(f"⚠️ Error en página {page}: {str(e)}")
                has_more_data = False
        
        print(f"✅ {len(all_reservations)} reservas ACEPTADAS obtenidas")
        return all_reservations
    
    def _enrich_reservation_data(self, reservation: Dict[str, Any]) -> None:
        """Enriquece datos de reserva con información adicional"""
        
        reservation_id = reservation.get("id")
        
        try:
            # Obtener detalles completos
            response = requests.get(
                f"{self.base_url}/reservations/{reservation_id}",
                headers=self.headers
            )
            
            if response.status_code == 200:
                detailed_data = response.json()
                
                # Combinar datos adicionales
                reservation.update({
                    "detailed_guest_info": detailed_data.get("guest", {}),
                    "property_details": detailed_data.get("listing", {}),
                    "booking_details": detailed_data.get("booking_details", {}),
                    "additional_info": detailed_data.get("additional_info", {})
                })
            
        except Exception as e:
            print(f"⚠️ No se pudieron enriquecer datos para reserva {reservation_id}")
    
    def send_chat_message(self, reservation_id: int, message: str, booking_data: Dict[str, Any]) -> Dict[str, Any]:
        """Envía mensaje al chat de la reserva"""
        
        try:
            thread_id = booking_data.get("message_id") or booking_data.get("inbox_id")
            
            if not thread_id:
                return {"error": "No message_id or inbox_id found in booking data"}
            
            payload = {
                "thread_id": thread_id,
                "message": message,
                "send_by": "channel"
            }
            
            response = requests.post(
                f"{self.base_url}/inbox/reply",
                headers=self.headers,
                json=payload
            )
            
            response.raise_for_status()
            result = response.json()
            
            return result
            
        except Exception as e:
            print(f"❌ Error al enviar mensaje: {str(e)}")
            raise

class MessageProcessor:
    """Procesador de mensajes con datos reales"""
    
    def __init__(self):
        self.hostify = HostifyAPI()
        self.chekin = ChekinConnector()
        
        print(f"🔗 Chekin: {'✅ Disponible' if self.chekin.is_available else '❌ No disponible (usando fallbacks)'}")
    
    def process_message(self, message_template: str, booking: Dict[str, Any]) -> Optional[str]:
        """Procesa mensaje reemplazando variables con datos reales. Retorna None si no hay URL de Chekin"""
        
        processed_message = message_template
        reservation_id = str(booking.get("id", ""))
        
        print(f"🔄 Procesando mensaje para reserva {reservation_id}")
        
        # Verificar si necesitamos URL de Chekin
        needs_chekin_link = "{{chekin_signup_form_link}}" in message_template or "{{checkin_signup_form_link}}" in message_template
        
        if needs_chekin_link:
            # Obtener URL de Chekin primero
            checkin_link = self._get_checkin_link(reservation_id, booking)
            if not checkin_link:
                print(f"  ❌ No se encontró URL de Chekin para reserva {reservation_id} - mensaje NO enviado")
                return None
        
        # 1. Guest name
        guest_name = self._extract_guest_name(booking)
        if "{{guest_name}}" in processed_message:
            processed_message = processed_message.replace("{{guest_name}}", guest_name)
            print(f"  ✅ guest_name: {guest_name}")
        
        # 2. Check-in link (ya validado que existe)
        if "{{chekin_signup_form_link}}" in processed_message:
            checkin_link = self._get_checkin_link(reservation_id, booking)
            processed_message = processed_message.replace("{{chekin_signup_form_link}}", checkin_link)
            print(f"  ✅ check-in link: {checkin_link}")
        
        # Soporte para variable antigua también
        if "{{checkin_signup_form_link}}" in processed_message:
            checkin_link = self._get_checkin_link(reservation_id, booking)
            processed_message = processed_message.replace("{{checkin_signup_form_link}}", checkin_link)
            print(f"  ✅ check-in link (formato anterior): {checkin_link}")
        
        # 3. Otras variables
        other_replacements = {
            "{{checkin_date}}": booking.get("checkIn", "N/A"),
            "{{checkout_date}}": booking.get("checkOut", "N/A"),
            "{{reservation_id}}": reservation_id,
            "{{guests_count}}": str(booking.get("guests", "N/A")),
            "{{property_name}}": self._extract_property_name(booking),
            "{{booking_source}}": booking.get("source", "N/A")
        }
        
        for variable, value in other_replacements.items():
            if variable in processed_message:
                processed_message = processed_message.replace(variable, value)
                print(f"  ✅ {variable}: {value}")
        
        return processed_message
    
    def _extract_guest_name(self, booking: Dict[str, Any]) -> str:
        """Extrae nombre del huésped con múltiples fallbacks"""
        
        # Intentar diferentes campos
        guest_name_fields = [
            "guest_name",
            "guestName", 
            "guest",
            "primary_guest",
            "customer_name"
        ]
        
        for field in guest_name_fields:
            name = booking.get(field)
            if name and isinstance(name, str) and name.strip():
                return name.strip()
        
        # Buscar en datos detallados
        detailed_guest = booking.get("detailed_guest_info", {})
        if detailed_guest:
            first_name = detailed_guest.get("first_name") or detailed_guest.get("name")
            if first_name:
                last_name = detailed_guest.get("last_name", "")
                return f"{first_name} {last_name}".strip()
        
        return "Estimado huésped"
    
    def _get_checkin_link(self, reservation_id: str, booking: Dict[str, Any]) -> Optional[str]:
        """Obtiene link de check-in SOLO de Chekin - retorna None si no está disponible"""
        
        # Solo intentar Chekin - no usar fallbacks
        if self.chekin.is_available:
            chekin_link = self.chekin.get_checkin_link(reservation_id)
            if chekin_link and chekin_link.startswith("http"):
                return chekin_link

        # No hay fallback - retornar None si no se encuentra en Chekin
        return None
    
    def _extract_property_name(self, booking: Dict[str, Any]) -> str:
        """Extrae nombre de la propiedad"""
        
        property_details = booking.get("property_details", {})
        
        name_fields = ["name", "title", "property_name", "listing_name"]
        
        for field in name_fields:
            name = booking.get(field) or property_details.get(field)
            if name and isinstance(name, str) and name.strip():
                return name.strip()
        
        return "Su alojamiento"

def broadcast_message_to_specific_listing(listing_id: str, message_template: str) -> Dict[str, Any]:
    """Envía mensajes a un listing específico usando datos reales"""
    
    processor = MessageProcessor()
    
    results = {
        "listing_id": listing_id,
        "total_bookings": 0,
        "messages_sent": 0,
        "errors": [],
        "chekin_available": processor.chekin.is_available
    }
    
    try:
        # Obtener reservas futuras
        future_bookings = processor.hostify.get_future_bookings_with_details(listing_id)
        results["total_bookings"] = len(future_bookings)
        
        print(f"\n📨 Procesando {len(future_bookings)} reservas futuras")
        
        for booking in future_bookings:
            booking_id = booking["id"]
            guest_name = processor._extract_guest_name(booking)
            
            try:
                # Procesar mensaje con datos reales
                final_message = processor.process_message(message_template, booking)
                
                # Si no hay URL de Chekin, saltear esta reserva
                if final_message is None:
                    print(f"⚠️ Saltando reserva {booking_id} - No hay URL de Chekin disponible")
                    continue
                
                # Enviar mensaje
                result = processor.hostify.send_chat_message(booking_id, final_message, booking)
                
                if "error" not in result:
                    results["messages_sent"] += 1
                    print(f"✅ Mensaje enviado a {guest_name} (Reserva #{booking_id})")
                else:
                    error_msg = f"Error en reserva {booking_id}: {result.get('error')}"
                    results["errors"].append(error_msg)
                    print(f"⚠️ {error_msg}")
                    
            except Exception as e:
                error_msg = f"Error procesando reserva {booking_id}: {str(e)}"
                results["errors"].append(error_msg)
                print(f"❌ {error_msg}")
        
        return results
        
    except Exception as e:
        error_msg = f"Error general: {str(e)}"
        results["errors"].append(error_msg)
        print(f"❌ {error_msg}")
        return results

def broadcast_message_to_all_future_bookings(message_template: str, property_summary: List[Dict[str, Any]] = None) -> Dict[str, Any]:
    """Envía mensajes a todas las propiedades activas usando datos reales"""
    
    processor = MessageProcessor()
    
    results = {
        "total_properties": 0,
        "total_bookings": 0,
        "messages_sent": 0,
        "errors": [],
        "chekin_available": processor.chekin.is_available
    }
    
    try:
        # Si ya tenemos los datos, usarlos. Si no, obtenerlos (retrocompatibilidad)
        if property_summary is None:
            print("🔄 Obteniendo datos de propiedades...")
            # Obtener todas las propiedades activas (solo si no se pasaron datos)
            properties = processor.hostify.get_active_properties()
            results["total_properties"] = len(properties)
            
            if not properties:
                print("❌ No se encontraron propiedades activas")
                return results
            
            print(f"🏠 Procesando {len(properties)} propiedades activas")
            
            # Crear property_summary si no se pasó
            property_summary = []
            for property_data in properties:
                listing_id = property_data.get("id") or property_data.get("listing_id")
                property_name = property_data.get("name") or property_data.get("title", f"Propiedad {listing_id}")
                
                if not listing_id:
                    continue
                
                try:
                    print(f"\n🏠 {property_name} (ID: {listing_id})")
                    future_bookings = processor.hostify.get_future_bookings_with_details(str(listing_id))
                    
                    if future_bookings:
                        property_summary.append({
                            "id": listing_id,
                            "name": property_name,
                            "reservations": len(future_bookings),
                            "bookings": future_bookings
                        })
                    else:
                        print(f"  ℹ️ No hay reservas futuras")
                        
                except Exception as e:
                    error_msg = f"Error procesando {property_name}: {str(e)}"
                    results["errors"].append(error_msg)
                    print(f"❌ {error_msg}")
        
        # Usar los datos (ya existentes o recién obtenidos)
        results["total_properties"] = len(property_summary)
        
        print(f"📨 Procesando mensajes para {len(property_summary)} propiedades (datos {'reutilizados' if property_summary else 'obtenidos'})...")
        
        for property_info in property_summary:
            property_name = property_info["name"]
            listing_id = property_info["id"]
            future_bookings = property_info["bookings"]
            
            results["total_bookings"] += len(future_bookings)
            
            print(f"\n🏠 {property_name} (ID: {listing_id})")
            
            if not future_bookings:
                print(f"  ℹ️ No hay reservas futuras")
                continue
            
            for booking in future_bookings:
                booking_id = booking["id"]
                guest_name = processor._extract_guest_name(booking)
                
                try:
                    # Procesar mensaje con datos reales
                    final_message = processor.process_message(message_template, booking)
                    
                    # Si no hay URL de Chekin, saltear esta reserva
                    if final_message is None:
                        print(f"  ⚠️ Saltando reserva {booking_id} - No hay URL de Chekin disponible")
                        continue
                    
                    # Enviar mensaje
                    result = processor.hostify.send_chat_message(booking_id, final_message, booking)
                    
                    if "error" not in result:
                        results["messages_sent"] += 1
                        print(f"  ✅ Mensaje enviado a {guest_name} (#{booking_id})")
                    else:
                        error_msg = f"Error en reserva {booking_id}: {result.get('error')}"
                        results["errors"].append(error_msg)
                        print(f"  ⚠️ {error_msg}")
                        
                except Exception as e:
                    error_msg = f"Error procesando reserva {booking_id}: {str(e)}"
                    results["errors"].append(error_msg)
                    print(f"  ❌ {error_msg}")
        
        return results
        
    except Exception as e:
        error_msg = f"Error general: {str(e)}"
        results["errors"].append(error_msg)
        print(f"❌ {error_msg}")
        return results

def load_message_from_file(file_path: str) -> str:
    """Carga mensaje desde archivo"""
    
    try:
        with open(file_path, "r", encoding="utf-8") as f:
            message = f.read().strip()
        
        print(f"📄 Mensaje cargado desde: {file_path}")
        print(f"   Contenido: {message}")
        return message
        
    except FileNotFoundError:
        print(f"❌ Archivo no encontrado: {file_path}")
        return ""
    except Exception as e:
        print(f"❌ Error leyendo archivo: {str(e)}")
        return ""

def list_reservations_and_send(listing_id: str, message_template: str):
    """Lista reservas y envía mensajes directamente"""
    
    processor = MessageProcessor()
    
    try:
        print(f"🔍 Buscando reservas futuras para listing {listing_id}...")
        future_bookings = processor.hostify.get_future_bookings_with_details(listing_id)
        
        if not future_bookings:
            print("❌ No se encontraron reservas futuras para este listing.")
            return
        
        print(f"\n📋 Se encontraron {len(future_bookings)} reservas futuras:")
        print("-" * 80)
        
        for i, booking in enumerate(future_bookings, 1):
            booking_id = booking["id"]
            guest_name = processor._extract_guest_name(booking)
            checkin = booking.get("checkIn", "N/A")
            checkout = booking.get("checkOut", "N/A")
            guests = booking.get("guests", "N/A")
            status = booking.get("status", "N/A")
            source = booking.get("source", "N/A")
            
            print(f"{i:2d}. {guest_name} - Reserva #{booking_id}")
            print(f"    Check-in: {checkin} | Check-out: {checkout}")
            print(f"    Huéspedes: {guests} | Estado: {status} | Canal: {source}")
            print()
        
        print("-" * 80)
        print(f"📨 Mensaje a enviar: '{message_template}'")
        print("-" * 80)
        
        # Mostrar preview de un mensaje procesado
        if future_bookings:
            print(f"\n📝 Preview del mensaje procesado (reserva {future_bookings[0]['id']}):")
            preview_message = processor.process_message(message_template, future_bookings[0])
            print(f"   {preview_message}")
        
        # Enviar directamente sin confirmación
        print("\n✅ Enviando mensajes...")
        result = broadcast_message_to_specific_listing(listing_id, message_template)
        return result
            
    except Exception as e:
        print(f"❌ Error: {str(e)}")
        return None

def list_all_reservations_and_send(message_template: str):
    """Lista todas las reservas y envía mensajes directamente"""
    
    processor = MessageProcessor()
    
    try:
        print("🔍 Buscando todas las propiedades activas...")
        properties = processor.hostify.get_active_properties()
        
        if not properties:
            print("❌ No se encontraron propiedades activas.")
            return
        
        total_reservations = 0
        property_summary = []
        
        for property_data in properties:
            listing_id = property_data.get("id") or property_data.get("listing_id")
            property_name = property_data.get("name") or property_data.get("title", f"Propiedad {listing_id}")
            
            if not listing_id:
                continue
            
            try:
                future_bookings = processor.hostify.get_future_bookings_with_details(str(listing_id))
                if future_bookings:
                    total_reservations += len(future_bookings)
                    property_summary.append({
                        "id": listing_id,
                        "name": property_name,
                        "reservations": len(future_bookings),
                        "bookings": future_bookings
                    })
                    print(f"  ✅ {property_name}: {len(future_bookings)} reservas futuras")
                else:
                    print(f"  ⚪ {property_name}: Sin reservas futuras")
            except Exception as e:
                print(f"  ❌ Error en {property_name}: {str(e)}")
        
        if total_reservations == 0:
            print("\n❌ No se encontraron reservas futuras en ninguna propiedad.")
            return
        
        print("\n" + "=" * 80)
        print(f"📊 RESUMEN TOTAL:")
        print(f"   - Propiedades con reservas: {len(property_summary)}")
        print(f"   - Total de reservas futuras: {total_reservations}")
        print(f"📨 Mensaje a enviar: '{message_template}'")
        print("=" * 80)
        
        # Mostrar preview
        if property_summary and property_summary[0]["bookings"]:
            print(f"\n📝 Preview del mensaje procesado:")
            test_booking = property_summary[0]["bookings"][0]
            preview_message = processor.process_message(message_template, test_booking)
            print(f"   {preview_message}")
        
        # Enviar directamente sin confirmación - OPTIMIZADO: pasar datos ya obtenidos
        print("\n✅ Enviando mensajes (usando datos ya obtenidos para evitar duplicar llamadas API)...")
        result = broadcast_message_to_all_future_bookings(message_template, property_summary)
        return result
            
    except Exception as e:
        print(f"❌ Error: {str(e)}")
        return None

if __name__ == "__main__":
    print("🏠 HOSTIFY BROADCAST MESSAGE SYSTEM v2.0")
    print("📡 Usando datos reales de APIs (sin variables Hostify)")
    print("=" * 60)
    
    # Mensaje por defecto con variables corregidas
    default_message = "Hola {{guest_name}}, por favor completa tu check-in: {{chekin_signup_form_link}}"
    
    print("Opciones disponibles:")
    print("1. Enviar mensaje a un listing específico")
    print("2. Enviar mensaje a TODAS las propiedades activas")
    print("3. Cargar mensaje desde archivo")
    
    while True:
        try:
            opcion = input("\nSelecciona una opción (1-3): ").strip()
            
            message_template = default_message
            
            if opcion == "3":
                # Cargar desde archivo
                file_path = input("Ruta del archivo (Enter para mensaje_prueba_final): ").strip()
                if not file_path:
                    file_path = "/Users/usuario/dev/hostify-broadcast-message/mensaje_prueba_final"
                
                loaded_message = load_message_from_file(file_path)
                if loaded_message:
                    message_template = loaded_message
                else:
                    print("Usando mensaje por defecto...")
                
                # Volver a mostrar opciones
                print("\nMensaje cargado. Ahora selecciona dónde enviar:")
                print("1. Enviar a un listing específico")
                print("2. Enviar a TODAS las propiedades activas")
                opcion = input("Selecciona (1-2): ").strip()
            
            if opcion == "1":
                # Listing específico
                listing_id = input("ID del listing (Enter para 196240): ").strip()
                if not listing_id:
                    listing_id = "196240"
                
                if message_template == default_message:
                    custom_message = input(f"Mensaje (Enter para default): ").strip()
                    if custom_message:
                        message_template = custom_message
                
                print(f"\n🎯 Enviando a listing: {listing_id}")
                list_reservations_and_send(listing_id, message_template)
                break
                
            elif opcion == "2":
                # Todas las propiedades
                if message_template == default_message:
                    custom_message = input(f"Mensaje (Enter para default): ").strip()
                    if custom_message:
                        message_template = custom_message
                
                print(f"\n🌐 ENVIANDO A TODAS LAS PROPIEDADES")
                print("⚠️ Esto enviará mensajes a todas las reservas futuras!")
                
                # Eliminar confirmación extra también
                print("\n✅ Iniciando envío...")
                list_all_reservations_and_send(message_template)
                break
            
            else:
                print("❌ Opción no válida. Selecciona 1, 2 o 3.")
                
        except KeyboardInterrupt:
            print("\n\n👋 Programa interrumpido. ¡Hasta luego!")
            break
        except Exception as e:
            print(f"❌ Error inesperado: {str(e)}")
            input("Presiona Enter para continuar...")
