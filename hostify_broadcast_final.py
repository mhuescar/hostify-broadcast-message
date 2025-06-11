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
import time
from pathlib import Path

# Cargar variables de entorno
load_dotenv()

class ChekinConnector:
    """Conector para la API de Chekin con autenticación JWT oficial"""
    
    def __init__(self):
        self.api_key = os.getenv("CHEKIN_API_KEY")
        self.base_url = "https://a.chekin.io/public/api/v1"
        self.jwt_token = None
        self.is_available = False
        
        if not self.api_key:
            print("⚠️ CHEKIN_API_KEY no está configurada en las variables de entorno")
            return
        
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
    
    def get_child_listings(self, parent_id: int) -> List[Dict[str, Any]]:
        """Obtiene las propiedades child (Booking, Airbnb, Vrbo, etc.) para un parent_id específico"""
        
        all_child_listings = []
        page = 1
        max_pages = 10  # Límite de seguridad
        
        while page <= max_pages:
            try:
                params = {'page': page}
                url_children = f"{self.base_url}/listings/children/{parent_id}"
                
                response = requests.get(url_children, headers=self.headers, params=params)
                response.raise_for_status()
                
                data = response.json()
                
                if 'listings' not in data or not data['listings']:
                    break
                
                page_children = data['listings']
                all_child_listings.extend(page_children)
                
                # Si recibimos menos que una página completa, no hay más datos
                if len(page_children) < 20:  # Tamaño típico de página
                    break
                    
                page += 1
                
            except Exception as e:
                print(f"⚠️ Error obteniendo children de {parent_id}, página {page}: {str(e)}")
                break
        
        return all_child_listings

    def get_all_listing_ids(self) -> Dict[str, List[int]]:
        """
        Obtiene TODOS los IDs de listings: tanto PARENT como CHILDREN
        
        Returns:
            Dict con keys 'parent_ids' y 'all_ids' (parent + children)
        """
        
        print("🏠 Obteniendo todas las propiedades activas (PARENT)...")
        parent_properties = self.get_active_properties()
        
        parent_ids = []
        all_listing_ids = []
        
        print(f"📊 Procesando {len(parent_properties)} propiedades parent...")
        
        for i, property_data in enumerate(parent_properties, 1):
            parent_id = property_data.get("id")
            property_name = property_data.get("name", f"Propiedad {parent_id}")
            
            if not parent_id:
                continue
                
            parent_ids.append(parent_id)
            all_listing_ids.append(parent_id)
            
            print(f"  {i:2d}. 🏠 Parent: {property_name} (ID: {parent_id})")
            
            # Obtener children de esta propiedad
            try:
                child_listings = self.get_child_listings(parent_id)
                
                if child_listings:
                    print(f"      📋 Children encontrados: {len(child_listings)}")
                    
                    for child in child_listings:
                        child_id = child.get('id')
                        fs_type = child.get('fs_integration_type')
                        is_listed = child.get('is_listed', 0)
                        
                        if child_id:
                            all_listing_ids.append(child_id)
                            
                            # Mostrar tipo de integración
                            integration_name = "Desconocido"
                            if fs_type == 22:
                                integration_name = "Booking.com"
                            elif fs_type == 26:
                                integration_name = "Vrbo"
                            elif fs_type == 1 and is_listed == 1:
                                integration_name = "Airbnb"
                            elif fs_type == 1:
                                integration_name = "Airbnb (no listado)"
                            
                            print(f"         └─ Child: {child_id} ({integration_name})")
                else:
                    print(f"      📋 Sin children")
                    
            except Exception as e:
                print(f"      ❌ Error obteniendo children de {parent_id}: {str(e)}")
                continue
        
        result = {
            'parent_ids': parent_ids,
            'all_ids': all_listing_ids
        }
        
        print(f"\n📊 RESUMEN DE IDs:")
        print(f"   📁 Parent IDs: {len(parent_ids)}")
        print(f"   🔗 Total IDs (Parent + Children): {len(all_listing_ids)}")
        print(f"   📈 Children promedio por Parent: {(len(all_listing_ids) - len(parent_ids)) / len(parent_ids) if parent_ids else 0:.1f}")
        
        return result

    def get_active_properties(self) -> List[Dict[str, Any]]:
        """Obtiene todas las propiedades activas con paginación (solo PARENT)"""
        
        print("🏠 Obteniendo propiedades activas (PARENT)...")
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
        
        print(f"✅ {len(all_properties)} propiedades parent encontradas en total")
        return all_properties
    
    def get_future_bookings_with_details(self, listing_id: str) -> List[Dict[str, Any]]:
        """Obtiene reservas futuras con datos enriquecidos"""
        
        today = datetime.datetime.now().strftime("%Y-%m-%d")
        
        print(f"📋 Obteniendo reservas ACEPTADAS futuras para listing {listing_id}...")
        print(f"    🗓️ Filtro de fecha: check-in >= {today}")
        
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
                
                print(f"  📊 Página {page}: {len(page_reservations)} reservas recibidas de API")
                
                # Filtro adicional a nivel de código para asegurar solo "accepted" Y fechas futuras
                today_date = datetime.datetime.now().date()
                accepted_reservations = []
                
                for res in page_reservations:
                    reservation_id = res.get('id')
                    checkin_str = res.get("checkIn", "")
                    status = res.get("status", "")
                    
                    # Verificar status
                    if status != "accepted":
                        continue
                    
                    # Verificar fecha de check-in futura
                    if checkin_str:
                        try:
                            checkin_date = datetime.datetime.strptime(checkin_str, "%Y-%m-%d").date()
                            if checkin_date >= today_date:
                                accepted_reservations.append(res)
                                print(f"    ✅ Reserva {reservation_id} ACEPTADA: check-in={checkin_str}")
                        except ValueError:
                            continue
                    else:
                        continue
                
                # Enriquecer datos de cada reserva aceptada (si las hay)
                if accepted_reservations:
                    for reservation in accepted_reservations:
                        self._enrich_reservation_data(reservation)
                    all_reservations.extend(accepted_reservations)
                
                print(f"  📄 Página {page}: {len(accepted_reservations)} reservas aceptadas de {len(page_reservations)} recibidas")
                
                # Verificar si hay más páginas BASADO EN LOS DATOS CRUDOS, no en los filtrados
                if len(page_reservations) < page_size or len(page_reservations) == 0:
                    # Si recibimos menos reservas que el tamaño de página, es la última página
                    has_more_data = False
                else:
                    # Continuar a la siguiente página
                    page += 1
                    
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
                checkin_date = booking.get("checkIn", "N/A")
                print(f"  ❌ Reserva {reservation_id} (check-in: {checkin_date}) - Sin URL de Chekin disponible - mensaje NO enviado")
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

class ProgressTracker:
    """Controlador de progreso para evitar procesar propiedades ya completadas"""
    
    def __init__(self, progress_file: str = "broadcast_progress.json"):
        self.progress_file = progress_file
        self.completed_properties = self._load_progress()
        self.current_session = {
            "start_time": datetime.datetime.now().isoformat(),
            "properties_processed": 0,
            "messages_sent": 0,
            "errors": []
        }
    
    def _load_progress(self) -> set:
        """Carga propiedades ya completadas"""
        try:
            if os.path.exists(self.progress_file):
                with open(self.progress_file, 'r', encoding='utf-8') as f:
                    data = json.load(f)
                    completed = set(data.get("completed_properties", []))
                    print(f"📋 Progreso cargado: {len(completed)} propiedades ya procesadas")
                    return completed
        except Exception as e:
            print(f"⚠️ Error cargando progreso: {e}")
        
        return set()
    
    def _save_progress(self):
        """Guarda el progreso actual"""
        try:
            progress_data = {
                "completed_properties": list(self.completed_properties),
                "last_update": datetime.datetime.now().isoformat(),
                "session_summary": self.current_session
            }
            
            with open(self.progress_file, 'w', encoding='utf-8') as f:
                json.dump(progress_data, f, indent=2, ensure_ascii=False)
                
        except Exception as e:
            print(f"⚠️ Error guardando progreso: {e}")
    
    def is_property_completed(self, property_id: str) -> bool:
        """Verifica si una propiedad ya fue procesada"""
        return str(property_id) in self.completed_properties
    
    def mark_property_completed(self, property_id: str, messages_sent: int):
        """Marca una propiedad como completada"""
        self.completed_properties.add(str(property_id))
        self.current_session["properties_processed"] += 1
        self.current_session["messages_sent"] += messages_sent
        self._save_progress()
        print(f"✅ Propiedad {property_id} marcada como completada ({messages_sent} mensajes)")
    
    def add_error(self, error_msg: str):
        """Añade un error al registro"""
        self.current_session["errors"].append(error_msg)
        self._save_progress()
    
    def get_summary(self) -> dict:
        """Obtiene resumen del progreso"""
        return {
            "total_completed": len(self.completed_properties),
            "session": self.current_session
        }
    
    def reset_progress(self):
        """Reinicia el progreso (elimina archivo)"""
        try:
            if os.path.exists(self.progress_file):
                os.remove(self.progress_file)
                print("🗑️ Progreso reiniciado")
            self.completed_properties = set()
        except Exception as e:
            print(f"⚠️ Error reiniciando progreso: {e}")

def broadcast_message_to_specific_listing(listing_id: str, message_template: str) -> Dict[str, Any]:
    """Envía mensajes a un listing específico usando datos reales - TODAS las reservas"""
    
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
        
        print(f"\n📨 Procesando TODAS las {len(future_bookings)} reservas futuras")
        
        for i, booking in enumerate(future_bookings, 1):
            booking_id = booking["id"]
            guest_name = processor._extract_guest_name(booking)
            
            print(f"📧 {i}/{len(future_bookings)}: Procesando reserva #{booking_id} ({guest_name})")
            
            try:
                # Procesar mensaje con datos reales
                final_message = processor.process_message(message_template, booking)
                
                # Si no hay URL de Chekin, saltear esta reserva
                if final_message is None:
                    print(f"   ⚠️ Saltando reserva {booking_id} - No hay URL de Chekin disponible")
                    continue
                
                # Enviar mensaje
                result = processor.hostify.send_chat_message(booking_id, final_message, booking)
                
                if "error" not in result:
                    results["messages_sent"] += 1
                    print(f"   ✅ Mensaje enviado a {guest_name} (Reserva #{booking_id})")
                else:
                    error_msg = f"Error en reserva {booking_id}: {result.get('error')}"
                    results["errors"].append(error_msg)
                    print(f"   ⚠️ {error_msg}")
                    
            except Exception as e:
                error_msg = f"Error procesando reserva {booking_id}: {str(e)}"
                results["errors"].append(error_msg)
                print(f"   ❌ {error_msg}")
        
        print(f"\n📊 RESUMEN LISTING {listing_id}:")
        print(f"   📋 Reservas encontradas: {results['total_bookings']}")
        print(f"   ✅ Mensajes enviados: {results['messages_sent']}")
        print(f"   ❌ Errores: {len(results['errors'])}")
        
        return results
        
    except Exception as e:
        error_msg = f"Error general: {str(e)}"
        results["errors"].append(error_msg)
        print(f"❌ {error_msg}")
        return results

def broadcast_message_to_all_future_bookings(message_template: str, restart_progress: bool = False, listing_data: Dict[str, List[int]] = None) -> Dict[str, Any]:
    """Envía mensajes a TODAS las reservas futuras (PARENT + CHILDREN) con control de progreso paso a paso"""
    
    processor = MessageProcessor()
    progress = ProgressTracker()
    
    # Opción para reiniciar progreso
    if restart_progress:
        progress.reset_progress()
    
    results = {
        "total_parent_properties": 0,
        "total_listing_ids": 0,
        "properties_processed": 0,
        "properties_skipped": 0,
        "total_bookings": 0,
        "messages_sent": 0,
        "errors": [],
        "chekin_available": processor.chekin.is_available,
        "progress_file": progress.progress_file
    }
    
    try:
        # 1. OBTENER TODOS LOS IDs (PARENT + CHILDREN) - SOLO SI NO SE PASARON
        if listing_data is None:
            print("🔄 Paso 1: Obteniendo TODOS los IDs de listings (Parent + Children)...")
            listing_data = processor.hostify.get_all_listing_ids()
        else:
            print("🔄 Paso 1: Usando IDs previamente obtenidos...")
        
        parent_ids = listing_data['parent_ids']
        all_listing_ids = listing_data['all_ids']
        
        results["total_parent_properties"] = len(parent_ids)
        results["total_listing_ids"] = len(all_listing_ids)
        
        if not all_listing_ids:
            print("❌ No se encontraron listings activos")
            return results
        
        print(f"✅ Sistema expandido: {len(parent_ids)} propiedades parent → {len(all_listing_ids)} IDs totales")
        
        # Mostrar resumen de progreso previo
        if progress.completed_properties:
            print(f"📋 Progreso anterior: {len(progress.completed_properties)} IDs ya completados")
        
        # 2. PROCESAR CADA LISTING ID PASO A PASO (PARENT + CHILDREN)
        for i, listing_id in enumerate(all_listing_ids, 1):
            # Determinar si es parent o child
            is_parent = listing_id in parent_ids
            listing_type = "PARENT" if is_parent else "CHILD"
            
            print(f"\n{'='*60}")
            print(f"🏠 LISTING {i}/{len(all_listing_ids)}: ID {listing_id} ({listing_type})")
            print(f"{'='*60}")
            
            # Verificar si ya fue procesado
            if progress.is_property_completed(str(listing_id)):
                print(f"⏭️ Listing ya completado anteriormente - SALTANDO")
                results["properties_skipped"] += 1
                continue
            
            try:
                # 3. OBTENER RESERVAS DE ESTE LISTING
                print(f"📋 Paso 2: Obteniendo reservas futuras del listing {listing_id}...")
                future_bookings = processor.hostify.get_future_bookings_with_details(str(listing_id))
                
                if not future_bookings:
                    print(f"ℹ️ No hay reservas futuras - marcando como completado")
                    progress.mark_property_completed(str(listing_id), 0)
                    results["properties_processed"] += 1
                    continue
                
                print(f"✅ {len(future_bookings)} reservas futuras encontradas")
                results["total_bookings"] += len(future_bookings)
                
                # 4. ENVIAR MENSAJES PARA TODAS LAS RESERVAS DE ESTE LISTING
                print(f"📨 Paso 3: Enviando mensajes a TODAS las {len(future_bookings)} reservas...")
                listing_messages_sent = 0
                
                for j, booking in enumerate(future_bookings, 1):
                    booking_id = booking["id"]
                    guest_name = processor._extract_guest_name(booking)
                    
                    print(f"   📧 {j}/{len(future_bookings)}: Procesando reserva #{booking_id} ({guest_name})")
                    
                    try:
                        # Procesar mensaje con datos reales
                        final_message = processor.process_message(message_template, booking)
                        
                        # Si no hay URL de Chekin, saltear esta reserva
                        if final_message is None:
                            print(f"      ⚠️ Sin URL de Chekin - saltando")
                            continue
                        
                        # Enviar mensaje
                        result = processor.hostify.send_chat_message(booking_id, final_message, booking)
                        
                        if "error" not in result:
                            listing_messages_sent += 1
                            results["messages_sent"] += 1
                            print(f"      ✅ Mensaje enviado exitosamente")
                        else:
                            error_msg = f"Error en reserva {booking_id}: {result.get('error')}"
                            results["errors"].append(error_msg)
                            progress.add_error(error_msg)
                            print(f"      ⚠️ Error: {result.get('error')}")
                            
                    except Exception as e:
                        error_msg = f"Error procesando reserva {booking_id}: {str(e)}"
                        results["errors"].append(error_msg)
                        progress.add_error(error_msg)
                        print(f"      ❌ Error: {str(e)}")
                
                # 5. MARCAR LISTING COMO COMPLETADO
                progress.mark_property_completed(str(listing_id), listing_messages_sent)
                results["properties_processed"] += 1
                
                print(f"✅ Listing completado: {listing_messages_sent} mensajes enviados de {len(future_bookings)} reservas")
                
                # Pequeña pausa para no sobrecargar APIs
                if i < len(all_listing_ids):  # No pausar en el último listing
                    print(f"⏳ Pausa de 2 segundos antes del siguiente listing...")
                    time.sleep(2)
                        
            except Exception as e:
                error_msg = f"Error general en listing {listing_id}: {str(e)}"
                results["errors"].append(error_msg)
                progress.add_error(error_msg)
                print(f"❌ {error_msg}")
                continue  # Continuar con el siguiente listing
        
        # RESUMEN FINAL
        print(f"\n{'='*60}")
        print(f"🎯 RESUMEN FINAL")
        print(f"{'='*60}")
        print(f"🏠 Propiedades PARENT: {results['total_parent_properties']}")
        print(f"🔗 Total listings procesados (Parent + Children): {results['total_listing_ids']}")
        print(f"✅ Listings completados: {results['properties_processed']}")
        print(f"⏭️ Listings saltados (ya completados): {results['properties_skipped']}")
        print(f"📨 Total de mensajes enviados: {results['messages_sent']}")
        print(f"❌ Errores: {len(results['errors'])}")
        print(f"📋 Archivo de progreso: {progress.progress_file}")
        
        return results
        
    except Exception as e:
        error_msg = f"Error crítico: {str(e)}"
        results["errors"].append(error_msg)
        progress.add_error(error_msg)
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
    """Lista todas las reservas y envía mensajes directamente usando sistema Parent + Children OPTIMIZADO"""
    
    processor = MessageProcessor()
    
    try:
        print("🔍 Verificando conectividad y configuración...")
        
        # CAPTURAR IDs UNA SOLA VEZ
        print("📋 Obteniendo estructura de listings (UNA SOLA VEZ)...")
        listing_data = processor.hostify.get_all_listing_ids()
        parent_ids = listing_data['parent_ids'] 
        all_listing_ids = listing_data['all_ids']
        
        if not all_listing_ids:
            print("❌ No se encontraron listings activos.")
            return
        
        print(f"✅ Sistema expandido detectado:")
        print(f"   📁 {len(parent_ids)} propiedades PARENT")
        print(f"   🔗 {len(all_listing_ids)} listings TOTALES (Parent + Children)")
        print(f"   📈 Expansión: {len(all_listing_ids) - len(parent_ids)} children adicionales")
        print(f"📨 Mensaje a enviar: '{message_template}'")
        
        # Mostrar preview rápido si es posible
        try:
            # Obtener una muestra de reserva para preview (del primer listing)
            if all_listing_ids:
                sample_listing_id = all_listing_ids[0]
                sample_bookings = processor.hostify.get_future_bookings_with_details(str(sample_listing_id))
                if sample_bookings:
                    print(f"\n📝 Preview del mensaje procesado (listing {sample_listing_id}):")
                    preview_message = processor.process_message(message_template, sample_bookings[0])
                    print(f"   {preview_message}")
        except:
            print("\n📝 Preview no disponible (se generará durante el envío)")
        
        # PASAR LOS IDs YA OBTENIDOS para evitar recaptura
        print("\n✅ Iniciando envío paso a paso con sistema Parent + Children...")
        result = broadcast_message_to_all_future_bookings(message_template, listing_data=listing_data)
        return result
            
    except Exception as e:
        print(f"❌ Error: {str(e)}")
        return None

if __name__ == "__main__":
    print("🏠 HOSTIFY BROADCAST MESSAGE SYSTEM v2.0")
    print("📡 Usando datos reales de APIs (sin variables Hostify)")
    print("=" * 60)
    
    # Mensaje por defecto con variables corregidas
    default_message = "Ignore este mensaje si ya completó el check-in: Hola {{guest_name}}, hemos mejorado nuestro proceso de check-in y ahora el enlace para completarlo es este. No dude en preguntarnos ante cualquier duda: {{chekin_signup_form_link}} "
    
    print("Opciones disponibles:")
    print("1. Enviar mensaje a un listing específico")
    print("2. Enviar mensaje a TODAS las propiedades activas")
    print("3. Cargar mensaje desde archivo")
    print("4. Reiniciar progreso y empezar desde cero")
    
    while True:
        try:
            opcion = input("\nSelecciona una opción (1-4): ").strip()
            
            message_template = default_message
            
            if opcion == "4":
                # Reiniciar progreso
                from pathlib import Path
                progress_file = "broadcast_progress.json"
                if Path(progress_file).exists():
                    confirm = input("⚠️ ¿Seguro que quieres eliminar el progreso guardado? (s/N): ").strip().lower()
                    if confirm == 's':
                        try:
                            Path(progress_file).unlink()
                            print("✅ Progreso reiniciado")
                        except Exception as e:
                            print(f"❌ Error eliminando archivo: {e}")
                    else:
                        print("Cancelado")
                else:
                    print("ℹ️ No hay progreso guardado para eliminar")
                continue
            
            elif opcion == "3":
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
                print("❌ Opción no válida. Selecciona 1, 2, 3 o 4.")
                
        except KeyboardInterrupt:
            print("\n\n👋 Programa interrumpido. ¡Hasta luego!")
            break
        except Exception as e:
            print(f"❌ Error inesperado: {str(e)}")
            input("Presiona Enter para continuar...")
