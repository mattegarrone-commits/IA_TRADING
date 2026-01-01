# ☁️ Cómo subir tu App a la Nube (Gratis)

Para usar la App desde tu móvil **sin tener la computadora prendida**, necesitas subir el código a un servidor en la nube.
La forma más fácil y gratuita es usar **GitHub** + **Streamlit Cloud**.

Sigue estos pasos (toma unos 10-15 minutos):

### Paso 1: Crear cuenta en GitHub
1. Ve a [github.com](https://github.com) y crea una cuenta gratuita.
2. Una vez dentro, busca el botón **"New Repository"** (Nuevo Repositorio).
3. Ponle un nombre (ej: `trading-app`).
4. Selecciona **"Public"**.
5. Marca la casilla **"Add a README file"**.
6. Dale a **"Create repository"**.

### Paso 2: Subir los archivos
1. En tu nuevo repositorio, haz clic en **"Add file"** > **"Upload files"**.
2. Arrastra **TODOS** los archivos de tu carpeta `IA_TRADING` dentro del recuadro, **EXCEPTO**:
   - ❌ La carpeta `.venv_mobile` (¡NO la subas!)
   - ❌ La carpeta `.git` (si existe)
   - ❌ Archivos temporales
   - ✅ **SÍ SUBE**: `main.py`, `requirements.txt`, `data_loader.py`, `start_dashboard.bat` (opcional), carpeta `core/`, carpeta `analysis/`.
3. Espera a que carguen y dale al botón verde **"Commit changes"**.

### Paso 3: Publicar en Streamlit Cloud
1. Ve a [share.streamlit.io](https://share.streamlit.io) y regístrate con tu cuenta de GitHub.
2. Dale a **"New app"**.
3. Selecciona el repositorio que creaste (`trading-app`).
4. En "Main file path", asegúrate que diga `main.py`.
5. Dale a **"Deploy!"**.

### 📱 ¡Listo!
Streamlit te dará una **URL (enlace web)**.
- Copia ese enlace.
- Mándalo a tu WhatsApp o Telegram.
- **Ábrelo en tu móvil desde cualquier lugar del mundo**, sin necesidad de tu PC.

---

**Nota:** Como es una versión gratuita en la nube, el "Diario de Trading" (historial) podría borrarse si la app se reinicia sola (pasa a veces en servidores gratuitos). Pero el análisis en tiempo real funcionará siempre.
