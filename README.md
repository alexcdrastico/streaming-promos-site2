# StreamPromos España 🇪🇸

Página web que monitoriza automáticamente las promociones de prueba gratuita de plataformas de streaming en España. Se actualiza cada día a las 7:00 UTC (9:00h en verano).

## Estructura

```
├── index.html                       ← Página web (lee promos.json)
├── promos.json                      ← Datos de promociones (auto-actualizado)
├── requirements.txt                 ← Dependencias Python del scraper
├── scripts/
│   └── check_promos.py              ← Scraper que comprueba cada plataforma
└── .github/
    └── workflows/
        └── update-promos.yml        ← Cron diario de GitHub Actions
```

## Cómo desplegarlo

### 1. Crear el repositorio en GitHub

```bash
git init
git add .
git commit -m "feat: initial setup"
gh repo create streaming-promos-espana --public --push --source .
```

### 2. Conectar con Netlify

1. Ve a [app.netlify.com](https://app.netlify.com) → **Add new site → Import an existing project**
2. Conecta tu cuenta de GitHub y selecciona este repositorio
3. Configuración del build:
   - **Build command**: *(vacío, no hay build)*
   - **Publish directory**: `.` (la raíz del proyecto)
4. Clic en **Deploy site**

Netlify detectará automáticamente cualquier push al repo y redesplegará la página en ~10 segundos.

### 3. Verificar GitHub Actions

Una vez en GitHub, ve a **Actions** → deberías ver el workflow `update-promos.yml`.

Para probarlo manualmente: **Actions → Actualizar promociones diariamente → Run workflow**.

## Cómo funciona el scraper

`scripts/check_promos.py` visita la URL oficial de cada plataforma, extrae el texto visible y busca keywords como *"gratis"*, *"prueba gratuita"*, *"free trial"*, *"meses gratis"*. Si encuentra alguna, marca la plataforma como activa e intenta extraer el texto de la promo (ej: "3 meses gratis").

### Añadir o modificar plataformas

Edita el array `PLATFORMS` en `check_promos.py`. Cada entrada tiene:
- `id`: identificador único
- `name`: nombre visible
- `category`: `"video"` o `"music"`
- `url`: URL a scrapear (página de precios/suscripción)
- `fallback_url`: URL alternativa si la principal falla
- `keywords`: palabras que indican promo activa
- `negative_keywords`: palabras que invalidan los keywords positivos
- `cta_url`: URL del botón "Activar prueba"
- `logo`, `logo_bg`: icono de Simple Icons CDN y color de fondo

## Ejecución local

```bash
pip install -r requirements.txt
python scripts/check_promos.py
# Abre index.html en el navegador (necesita servidor local por el fetch)
python -m http.server 8000
```

## Notas

- El scraper funciona sobre HTML estático. Algunas plataformas cargan ofertas via JavaScript — en ese caso puede dar falsos negativos. Si notas uno, ajusta la `url` a una página que cargue la oferta en el HTML inicial.
- Las promociones pueden cambiar en cualquier momento. Verifica siempre en el sitio oficial.
