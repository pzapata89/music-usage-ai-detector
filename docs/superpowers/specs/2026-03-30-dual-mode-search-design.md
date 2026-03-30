# Diseño: Sistema de Búsqueda Dual (Quick Search + Análisis Profundo)

**Fecha:** 2026-03-30
**Estado:** Aprobado

---

## Resumen

Agregar un modo de Búsqueda Rápida (Quick Search) a la app existente "Detector de Uso de Música con IA", sin romper el Análisis Profundo ya existente.

El flujo nuevo reemplaza el formulario de 2 campos (canción + artista) por un único campo de texto. El sistema identifica automáticamente la canción y el artista via Spotify API (con fallback a OpenAI), muestra hasta 3 candidatos cada uno con hasta 10 links de YouTube y 10 de la web, y ofrece un botón por candidato para lanzar el Análisis Profundo existente.

Toda la interfaz de usuario usa **español latinoamericano**.

---

## Arquitectura

### Módulos nuevos

#### `song_metadata.py`
Responsabilidad única: identificar canción y artista a partir de texto libre del usuario.

```python
@dataclass
class SongCandidate:
    song_name: str
    artist_name: str
    album: str
    spotify_id: str   # vacío si vino de OpenAI fallback
    confidence: float # 1.0 para Spotify, estimado para OpenAI

def get_song_metadata(user_input: str) -> List[SongCandidate]:
    ...
```

**Flujo interno:**
1. Llama a Spotify Search API (`GET /v1/search?q={input}&type=track&limit=3`) usando Client Credentials flow (sin login de usuario)
2. Si retorna ≥1 resultado → convierte a `SongCandidate` list, `confidence=1.0`
3. Si Spotify falla o retorna 0 → llama a OpenAI `gpt-4o-mini` con prompt estructurado que pide JSON con los 3 mejores candidatos
4. Si OpenAI también falla → lanza excepción que `app.py` captura y muestra mensaje amigable

**Credenciales requeridas (nuevas):**
- `SPOTIFY_CLIENT_ID`
- `SPOTIFY_CLIENT_SECRET`

El token de Spotify (Client Credentials) se cachea en memoria durante la vida del objeto (válido 1 hora).

---

#### `quick_search.py`
Responsabilidad única: obtener links rápidos sin clasificación IA.

```python
def search_links(song_name: str, artist_name: str) -> dict:
    ...
```

**Retorna:**
```json
{
  "song": "...",
  "artist": "...",
  "links": [
    {"type": "YouTube", "title": "...", "url": "..."},
    {"type": "Web", "title": "...", "url": "..."}
  ]
}
```

**Implementación:**
- Instancia `YouTubeSearcher` y llama directamente a `_fetch_query_results(query, max_per_query=10)` — un solo query, sin el loop de 14 variaciones del modo profundo
- Instancia `WebSearcher` y llama directamente a `_fetch_web_results(query, num_results=10)` — un solo query
- Query única: `"{song_name} {artist_name}"`
- Sin llamadas a OpenAI (rápido y económico)
- Nota: los métodos con prefijo `_` son privados por convención en Python, no por restricción. Llamarlos desde `quick_search.py` es intencional para evitar el overhead del loop multi-query.

---

### Módulos modificados

#### `config.py`
Se agregan dos nuevas claves:
```python
self.spotify_client_id = self._get_api_key("SPOTIFY_CLIENT_ID")
self.spotify_client_secret = self._get_api_key("SPOTIFY_CLIENT_SECRET")
```

#### `app.py`
- **Formulario:** reemplaza el formulario de 2 campos por uno de campo único
- **Estado de sesión:** nuevas claves agregadas, existentes sin cambios
- **Flujo principal:** orquesta Quick Search → muestra candidatos → botón Deep Analysis
- **`perform_search()`:** recibe `song_name` y `artist_name` (ya identificados), sin cambios internos
- **Texto UI:** todo en español latinoamericano (incluyendo textos que ya existían)

---

## Estado de sesión (`st.session_state`)

### Claves nuevas
| Clave | Tipo | Descripción |
|-------|------|-------------|
| `mode` | `str` | `'idle'` \| `'quick_results'` \| `'deep_analysis'` |
| `song_candidates` | `List[SongCandidate]` | Hasta 3 candidatos identificados |
| `quick_links` | `List[dict]` | Links por candidato (índice = posición en `song_candidates`) |
| `selected_candidate_idx` | `int` | Índice del candidato elegido para análisis profundo |
| `user_query` | `str` | Input original del usuario |

### Claves existentes (sin cambios)
`search_results`, `search_performed`, `loading`

---

## Flujo de UI

```
[Campo: "Nombre de la canción..."]  [🔍 Buscar]
          ↓ (al hacer clic / Enter)
  Spinner: "Identificando canción..."
          ↓
  [Hasta 3 tarjetas de candidatos, side by side]

  Cada tarjeta:
  ┌──────────────────────────────────────────┐
  │ 🎵 Despacito                             │
  │ 👤 Luis Fonsi                            │
  │ 💿 Vida (2017)                           │
  │ ─────────────────────────────────────── │
  │ 📺 [título video YouTube 1]              │
  │ 📺 [título video YouTube 2]              │
  │ ... (hasta 10)                           │
  │ 🌐 [título resultado web 1]              │
  │ 🌐 [título resultado web 2]              │
  │ ... (hasta 10)                           │
  │                                          │
  │  [🔍 Ejecutar Análisis Profundo]         │
  └──────────────────────────────────────────┘

          ↓ (al hacer clic en el botón)
  Análisis Profundo existente (debajo de las tarjetas)
  (AI Report + Dashboard de Métricas + Tarjetas de resultados)
```

---

## Manejo de errores

| Escenario | Comportamiento |
|-----------|---------------|
| Spotify falla, OpenAI también falla | `st.error("No pudimos identificar la canción. Intenta con un nombre más específico.")` |
| Spotify retorna 0 resultados | Fallback silencioso a OpenAI |
| YouTube falla en Quick Search | `st.warning("No se pudieron cargar los videos de YouTube.")` — continúa con web |
| SerpAPI falla en Quick Search | `st.warning("No se pudieron cargar los resultados web.")` — continúa con YouTube |
| Deep Analysis falla | Comportamiento existente sin cambios |
| Input vacío | `st.warning("Por favor ingresa el nombre de una canción.")` |

---

## Logging

```python
# Quick Search
logger.info(f"Búsqueda rápida iniciada: '{user_input}'")
logger.info(f"Spotify identificó {n} candidato(s) para '{user_input}'")
logger.warning(f"Spotify falló para '{user_input}', usando fallback OpenAI")
logger.info(f"Quick links obtenidos para '{song}' de '{artist}': {n_yt} YouTube, {n_web} web")

# Deep Analysis (existente, sin cambios)
logger.info(f"Análisis profundo iniciado para '{song}' de '{artist}'")
```

---

## Configuración de credenciales

### `.env` (desarrollo local)
```
SPOTIFY_CLIENT_ID=tu_client_id_aqui
SPOTIFY_CLIENT_SECRET=tu_client_secret_aqui
```

### Streamlit Cloud Secrets
```toml
SPOTIFY_CLIENT_ID = "tu_client_id_aqui"
SPOTIFY_CLIENT_SECRET = "tu_client_secret_aqui"
```

Las credenciales de Spotify se obtienen en: https://developer.spotify.com/dashboard

---

## Reporte Ejecutivo en Análisis Profundo

### Prominencia en la UI
El reporte ejecutivo de OpenAI debe mostrarse siempre en el Análisis Profundo, destacado visualmente al inicio de los resultados. Se usará `st.info()` o un contenedor estilizado en lugar del `st.markdown()` actual, para que sea imposible pasarlo por alto.

### PDF siempre incluye el reporte ejecutivo
**Bug existente a corregir:** `app.py` actualmente construye `summary_for_pdf` sin incluir `ai_report`, por lo que el PDF nunca muestra el reporte ejecutivo aunque `pdf_generator.py` ya tiene la sección preparada (líneas 200–207).

**Fix:** en `display_summary()`, pasar `ai_report` como parámetro e incluirlo en `summary_for_pdf` antes de llamar a `get_pdf_download_link()`.

```python
# Antes (bug):
summary_for_pdf = summary.copy()
summary_for_pdf['high_risk_count'] = high_risk
summary_for_pdf['medium_risk_count'] = medium_risk

# Después (fix):
summary_for_pdf = summary.copy()
summary_for_pdf['high_risk_count'] = high_risk
summary_for_pdf['medium_risk_count'] = medium_risk
summary_for_pdf['ai_report'] = ai_report  # ← nuevo
```

`display_summary()` recibirá un nuevo parámetro `ai_report: str = ""`.

### Garantía de siempre generar el reporte
`generate_ai_report()` ya tiene un fallback (`_generate_fallback_report()`) que nunca falla. No se requieren cambios en `ai_analysis.py`.

---

## Lo que NO cambia

- `youtube_search.py` — sin modificaciones
- `web_search.py` — sin modificaciones
- `ai_analysis.py` — sin modificaciones
- `pdf_generator.py` — sin modificaciones (ya tiene soporte para `ai_report` en PDF)
- `login.py` — sin modificaciones
- `perform_search()` en `app.py` — sin cambios internos (solo se llama con parámetros ya identificados)
- Lógica de clasificación IA, métricas de riesgo — intacta
