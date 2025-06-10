# Hostify Broadcast Message System

Sistema automatizado para envío masivo de mensajes a huéspedes de Hostify utilizando datos reales de APIs (Hostify + Chekin).

## 🚀 Características Principales

- ✅ **Datos reales**: Extrae información de APIs (no variables de Hostify)
- ✅ **URLs de check-in reales**: Integración con Chekin API
- ✅ **Filtrado inteligente**: Solo reservas aceptadas y futuras  
- ✅ **Paginación completa**: Procesa todas las propiedades (48/48)
- ✅ **Optimización de APIs**: Evita llamadas duplicadas
- ✅ **Validación robusta**: No envía mensajes con datos incompletos

## 🔧 Requisitos

- Python 3.7+
- Cuentas activas en:
  - [Hostify](https://hostify.com) (API key requerida)
  - [Chekin](https://chekin.io) (API key incluida)

## 📦 Instalación

### Opción 1: Setup Automático (Recomendado)

```bash
git clone <tu-repo-url>
cd hostify-broadcast-message
./setup.sh
```

### Opción 2: Setup Manual

1. **Clonar el repositorio:**
```bash
git clone <tu-repo-url>
cd hostify-broadcast-message
```

2. **Crear entorno virtual:**
```bash
python3 -m venv venv
source venv/bin/activate  # En macOS/Linux
# o en Windows: venv\Scripts\activate
```

3. **Instalar dependencias:**
```bash
pip install -r requirements.txt
```

4. **Configurar variables de entorno:**
```bash
cp .env.example .env
# Editar .env con tu API key de Hostify
```

### Verificar Instalación

```bash
python3 verify_setup.py
```

Este script verifica que todo esté configurado correctamente.

### Probar con Ejemplos

```bash
python3 ejemplos_uso.py
```

Script con ejemplos de uso y verificación del sistema.

## ⚙️ Configuración

Edita el archivo `.env`:

```env
HOSTIFY_API_KEY=tu_api_key_de_hostify_aqui
```

**Nota**: La API key de Chekin ya está incluida y configurada.

## 🎯 Uso

### Ejecución Principal

```bash
python3 hostify_broadcast_final.py
```

### Opciones Disponibles

1. **Envío a propiedad específica**
   - Permite seleccionar una propiedad por ID
   - Muestra preview del mensaje antes de enviar

2. **Envío masivo a todas las propiedades**
   - Procesa automáticamente las 48 propiedades activas
   - Optimizado para evitar llamadas API duplicadas

3. **Carga de mensaje desde archivo**
   - Usar archivo `mensaje_prueba_final` como ejemplo
   - Soporte para mensajes personalizados

### Variables Disponibles

El sistema reemplaza automáticamente estas variables:

- `{{guest_name}}` - Nombre del huésped
- `{{chekin_signup_form_link}}` - URL real de check-in de Chekin
- `{{checkin_date}}` - Fecha de check-in
- `{{checkout_date}}` - Fecha de check-out
- `{{reservation_id}}` - ID de la reserva
- `{{guests_count}}` - Número de huéspedes
- `{{property_name}}` - Nombre de la propiedad
- `{{booking_source}}` - Canal de reserva

## 📊 Ejemplo de Mensaje

**Archivo `mensaje_prueba_final`:**
```
PRUEBA FINAL {{guest_name}}: link {{chekin_signup_form_link}} - sin procesamiento local
```

**Resultado procesado:**
```
PRUEBA FINAL Juan Pérez: link https://chekin.io/signup/abc123 - sin procesamiento local
```

## 🔍 Funcionamiento Interno

### 1. Obtención de Datos
- **Propiedades**: Paginación completa (48 propiedades en 3 páginas)
- **Reservas**: Solo `status: "accepted"` y fechas futuras
- **Validación**: Double-check en código (API ignora algunos filtros)

### 2. Procesamiento de Mensajes
- Verifica disponibilidad de URL de Chekin **antes** de procesar
- Si no hay URL de Chekin → No envía mensaje (evita spam)
- Extrae datos reales de múltiples campos con fallbacks

### 3. Optimizaciones
- **Reutilización de datos**: Evita llamadas API duplicadas
- **Paginación automática**: Detecta y procesa todas las páginas
- **Error handling**: Continúa procesando aunque falle una reserva

## 📈 Métricas y Resultados

El sistema proporciona información detallada:

```
📊 RESUMEN TOTAL:
   - Propiedades con reservas: 15/48
   - Total de reservas futuras: 234
   - Mensajes enviados: 198
   - Mensajes saltados: 36 (sin URL Chekin)
   - Errores: 0
```

## 🛠️ Estructura del Proyecto

```
hostify-broadcast-message/
├── hostify_broadcast_final.py     # Script principal
├── requirements.txt               # Dependencias Python
├── .env.example                   # Plantilla de configuración
├── mensaje_prueba_final           # Mensaje de ejemplo
├── README.md                      # Este archivo
├── CORRECCION_PAGINACION.md      # Documentación técnica
└── SISTEMA_OPTIMIZADO_FINAL.md   # Detalles de optimización
```

## 🔒 Seguridad y Buenas Prácticas

- ✅ API keys protegidas en variables de entorno
- ✅ Validación de datos antes de envío
- ✅ Rate limiting implícito por paginación
- ✅ Logs detallados para debugging
- ✅ Manejo robusto de errores

## 🚨 Limitaciones Conocidas

1. **API de Hostify**: El filtro `status=accepted` en query params no funciona
   - **Solución**: Filtro adicional implementado en código

2. **Chekin API**: Algunas reservas pueden no tener URL de check-in
   - **Solución**: Sistema salta automáticamente esas reservas

3. **Rate Limiting**: APIs tienen límites no documentados
   - **Solución**: Paginación natural proporciona throttling

## 🔧 Desarrollo y Debugging

### Activar modo debug:
```python
# En hostify_broadcast_final.py, añadir más logs si es necesario
print(f"Debug: {variable_a_inspeccionar}")
```

### Probar con una sola propiedad:
```bash
# Ejecutar y seleccionar opción 1
python3 hostify_broadcast_final.py
# Introducir ID: 196240 (propiedad de prueba)
```

### Verificar conexiones API:
```python
from hostify_broadcast_final import MessageProcessor
processor = MessageProcessor()
# Verifica que ambas APIs estén disponibles
```

## 🤝 Contribución

1. Fork el proyecto
2. Crea una rama para tu feature (`git checkout -b feature/nueva-funcionalidad`)
3. Commit tus cambios (`git commit -am 'Añadir nueva funcionalidad'`)
4. Push a la rama (`git push origin feature/nueva-funcionalidad`)
5. Crea un Pull Request

## 📄 Licencia

Este proyecto está bajo la Licencia MIT. Ver archivo `LICENSE` para más detalles.

## 📞 Soporte

Para problemas o consultas:
- Crear un issue en GitHub
- Revisar documentación en `SISTEMA_OPTIMIZADO_FINAL.md`
- Verificar logs de ejecución para debugging

---

**Desarrollado con ❤️ para automatizar la comunicación con huéspedes de Hostify**
