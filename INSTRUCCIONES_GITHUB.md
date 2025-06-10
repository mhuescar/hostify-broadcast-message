# 🚀 Instrucciones para subir a GitHub

## 1. Configurar Git (si es la primera vez)

```bash
git config --global user.name "Tu Nombre"
git config --global user.email "tu-email@example.com"
```

## 2. Crear repositorio en GitHub

1. Ve a [GitHub.com](https://github.com)
2. Haz clic en "New repository"
3. Nombre sugerido: `hostify-broadcast-message`
4. Descripción: `Sistema automatizado para envío masivo de mensajes a huéspedes de Hostify con APIs reales`
5. **NO** marques "Add README" (ya tenemos uno)
6. Haz clic en "Create repository"

## 3. Conectar repositorio local con GitHub

```bash
# Añadir el remote origin (reemplaza TU-USUARIO con tu username de GitHub)
git remote add origin https://github.com/TU-USUARIO/hostify-broadcast-message.git

# Verificar que se añadió correctamente
git remote -v

# Subir el código por primera vez
git push -u origin main
```

## 4. Verificar que todo subió correctamente

Ve a tu repositorio en GitHub y verifica que aparezcan todos los archivos:

✅ README.md (se mostrará automáticamente)
✅ hostify_broadcast_final.py (script principal)
✅ setup.sh (script de instalación)
✅ requirements.txt (dependencias)
✅ .env.example (plantilla de configuración)
✅ LICENSE (licencia MIT)

## 5. Hacer el repositorio más atractivo

### Añadir topics en GitHub:
- `hostify`
- `automation`
- `python`
- `api-integration`
- `messaging`
- `property-management`

### Configurar GitHub Pages (opcional):
1. Ve a Settings → Pages
2. Selecciona "Deploy from a branch"
3. Branch: main, folder: / (root)

## 6. Comandos útiles para futuras actualizaciones

```bash
# Añadir cambios
git add .

# Commit con mensaje descriptivo
git commit -m "feat: nueva funcionalidad" 
# o
git commit -m "fix: corrección de bug"

# Subir cambios
git push origin main
```

## 7. Ejemplo de uso para el README

Puedes añadir este badge al README para mostrar el número de estrellas:

```markdown
![GitHub stars](https://img.shields.io/github/stars/TU-USUARIO/hostify-broadcast-message?style=social)
```

## 8. ¡Listo! 🎉

Tu proyecto estará disponible en:
`https://github.com/TU-USUARIO/hostify-broadcast-message`

Otros desarrolladores podrán:
- Clonarlo con: `git clone https://github.com/TU-USUARIO/hostify-broadcast-message.git`
- Usar el setup automático: `./setup.sh`
- Verificar instalación: `python3 verify_setup.py`
