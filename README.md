# Music Usage AI Detector 🎵

Aplicación web para detectar usos de canciones en internet, con análisis clasificatorio impulsado por IA. Construida con Streamlit, YouTube Data API, SerpAPI, Spotify API y OpenAI.

## Funcionalidades

### Dos modos de búsqueda

**🔍 Búsqueda Rápida**
- Ingresa solo el nombre de la canción
- Identificación automática del artista vía Spotify (fallback a OpenAI)
- Muestra hasta 3 candidatos con links de YouTube y web sin clasificación de IA
- Desde cada candidato se puede lanzar un Análisis Profundo

**🔬 Análisis Profundo**
- Ingresa canción + artista directamente
- Búsqueda exhaustiva: 14 variaciones en YouTube, 7 en web
- Clasificación de cada resultado con IA (OpenAI `gpt-4o-mini`)
- Reporte ejecutivo + descarga en PDF

### Categorías de clasificación IA

| Categoría | Descripción |
|-----------|-------------|
| Uso Directo de Canción | Uso directo de la canción en el contenido |
| Cover / Interpretación | Versiones o covers del tema |
| Uso Promocional | Uso en marketing o publicidad |
| Solo Referencia | Menciones sin uso real de la canción |

### Otras funcionalidades
- Autenticación con login por usuario y contraseña hasheada
- Dashboard de métricas con niveles de riesgo (Alto / Medio / Bajo)
- Descarga de reporte PDF con resumen ejecutivo
- Soporte para deployment en Streamlit Cloud y desarrollo local con `.env`

## Estructura del proyecto

```
music_usage_detector/
├── app.py                  # Aplicación principal Streamlit
├── config.py               # Gestión de API keys (secrets + .env)
├── login.py                # Autenticación de usuarios
├── song_metadata.py        # Identificación de canción vía Spotify/OpenAI
├── quick_search.py         # Búsqueda rápida de links (YouTube + web)
├── youtube_search.py       # Integración con YouTube Data API v3
├── web_search.py           # Integración con SerpAPI
├── ai_analysis.py          # Clasificación y análisis con OpenAI
├── pdf_generator.py        # Generación de reportes PDF
├── requirements.txt        # Dependencias Python
└── tests/                  # Tests unitarios
    ├── conftest.py
    ├── test_song_metadata.py
    └── test_quick_search.py
```

## Instalación local

### Prerrequisitos

- Python 3.10 o superior
- API keys para YouTube, SerpAPI, OpenAI y Spotify

### 1. Clonar el repositorio

```bash
git clone <repository-url>
cd music_usage_detector
```

### 2. Crear entorno virtual

```bash
python -m venv venv
source venv/bin/activate        # macOS/Linux
venv\Scripts\activate           # Windows
```

### 3. Instalar dependencias

```bash
pip install -r requirements.txt
```

### 4. Configurar variables de entorno

Crea un archivo `.env` en la raíz del proyecto:

```env
YOUTUBE_API_KEY=tu_youtube_api_key
SERPAPI_API_KEY=tu_serpapi_api_key
OPENAI_API_KEY=tu_openai_api_key
SPOTIFY_CLIENT_ID=tu_spotify_client_id
SPOTIFY_CLIENT_SECRET=tu_spotify_client_secret

# Autenticación
LOGIN_SALT=tu_salt_aleatorio
LOGIN_USER_PEDRO=hash_pbkdf2_de_la_contraseña
LOGIN_USER_SACVEN=hash_pbkdf2_de_la_contraseña
LOGIN_USER_INVITADO=hash_pbkdf2_de_la_contraseña
```

> **Importante:** El archivo `.env` está en `.gitignore` y nunca debe subirse al repositorio.

Para generar el hash de una contraseña nueva (usa el mismo `LOGIN_SALT`):

```bash
python -c "import hashlib; print(hashlib.pbkdf2_hmac('sha256', b'PASSWORD', b'SALT', 100000).hex())"
```

### 5. Ejecutar la aplicación

```bash
streamlit run app.py
```

La app abre en `http://localhost:8501`.

## Obtener API Keys

| Servicio | Dónde obtenerla |
|---------|----------------|
| YouTube Data API v3 | [Google Cloud Console](https://console.cloud.google.com/) → APIs → YouTube Data API v3 |
| SerpAPI | [serpapi.com](https://serpapi.com/) → Dashboard |
| OpenAI | [platform.openai.com](https://platform.openai.com/) → API Keys |
| Spotify | [developer.spotify.com](https://developer.spotify.com/dashboard) → Create App (usar Client Credentials) |

## Deployment en Streamlit Cloud

1. Haz push del código a GitHub (rama `main`)
2. En [share.streamlit.io](https://share.streamlit.io/), conecta el repositorio
3. En **Settings → Secrets**, agrega todas las variables del `.env`:

```toml
YOUTUBE_API_KEY = "..."
SERPAPI_API_KEY = "..."
OPENAI_API_KEY = "..."
SPOTIFY_CLIENT_ID = "..."
SPOTIFY_CLIENT_SECRET = "..."
LOGIN_SALT = "..."
LOGIN_USER_PEDRO = "..."
LOGIN_USER_SACVEN = "..."
LOGIN_USER_INVITADO = "..."
```

4. Streamlit Cloud detectará el push y redesplegará automáticamente

## Límites de API

| API | Límite gratuito |
|-----|----------------|
| YouTube Data API v3 | 10,000 unidades/día |
| SerpAPI | 100 búsquedas/mes |
| OpenAI | Pago por uso |
| Spotify | Sin límite práctico (Client Credentials) |

## Tests

```bash
pytest tests/ -v
```

## Límite de clasificaciones IA

`AIAnalyzer` tiene un cap de **20 clasificaciones por búsqueda** para controlar costos de OpenAI. Los resultados adicionales se clasifican como `reference_only` con confianza 0.5. El cap se resetea en cada nueva búsqueda.

---

Construido con Streamlit · YouTube Data API · SerpAPI · OpenAI · Spotify API · fpdf2
