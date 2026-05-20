#!/usr/bin/env python3
"""
Scraper diario de promociones de streaming para España.
Visita cada URL oficial y busca señales de prueba gratuita activa.
Escribe los resultados en ../promos.json.
"""

import json, re, sys
from datetime import date, datetime
from pathlib import Path

try:
    import requests
    from bs4 import BeautifulSoup
except ImportError:
    print("Instala dependencias: pip install requests beautifulsoup4")
    sys.exit(1)

HEADERS = {
    "User-Agent": (
        "Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) "
        "AppleWebKit/537.36 (KHTML, like Gecko) "
        "Chrome/124.0.0.0 Safari/537.36"
    ),
    "Accept-Language": "es-ES,es;q=0.9",
    "Accept": "text/html,application/xhtml+xml,application/xhtml+xml,application/xml;q=0.9,*/*;q=0.8",
}

TIMEOUT = 15  # segundos por request

# ─── Definición de plataformas ───────────────────────────────────────────────
# keywords: si alguna aparece en el HTML visible → promo activa
# negative_keywords: si aparece junto a las anteriores → falso positivo, ignorar
# url: página donde se anuncia la promo (idealmente la de precios/suscripción)
PLATFORMS = [
    # ── Cine / Series ──
    {
        "id": "max",
        "name": "Max (HBO)",
        "category": "video",
        "url": "https://www.max.com/es/es/subscribe",
        "fallback_url": "https://www.max.com/es/es",
        "keywords": ["prueba gratuita", "gratis", "free trial", "días gratis", "meses gratis"],
        "negative_keywords": ["ya no", "sin prueba", "eliminado"],
        "cta_url": "https://www.max.com/es/es/subscribe",
        "logo": "https://cdn.simpleicons.org/hbo/000000",
        "logo_bg": "#000",
    },
    {
        "id": "skyshowtime",
        "name": "SkyShowtime",
        "category": "video",
        "url": "https://www.skyshowtime.com/es/upgrade",
        "fallback_url": "https://www.skyshowtime.com/es",
        "keywords": ["prueba gratuita", "gratis", "free trial", "días gratis", "meses gratis"],
        "negative_keywords": [],
        "cta_url": "https://www.skyshowtime.com/es/upgrade",
        "logo": "https://cdn.simpleicons.org/skyshowtime",
        "logo_bg": "#0b0c10",
    },
    {
        "id": "disneyplus",
        "name": "Disney+",
        "category": "video",
        "url": "https://www.disneyplus.com/es-es/subscribe",
        "fallback_url": "https://www.disneyplus.com/es-es",
        "keywords": ["prueba gratuita", "gratis", "free trial", "días gratis", "meses gratis"],
        "negative_keywords": [],
        "cta_url": "https://www.disneyplus.com/es-es/subscribe",
        "logo": "https://cdn.simpleicons.org/disneyplus",
        "logo_bg": "#001e62",
    },
    {
        "id": "appletv",
        "name": "Apple TV+",
        "category": "video",
        "url": "https://www.apple.com/es/apple-tv-plus/",
        "fallback_url": None,
        "keywords": ["días gratis", "meses gratis", "prueba gratuita", "free trial", "gratis"],
        "negative_keywords": [],
        "cta_url": "https://www.apple.com/es/apple-tv-plus/",
        "logo": "https://cdn.simpleicons.org/appletv/000000",
        "logo_bg": "#000",
    },
    # ── Música ──
    {
        "id": "spotify",
        "name": "Spotify",
        "category": "music",
        "url": "https://www.spotify.com/es/premium/",
        "fallback_url": None,
        "keywords": ["meses gratis", "mes gratis", "prueba gratuita", "free", "gratis"],
        "negative_keywords": [],
        "cta_url": "https://www.spotify.com/es/premium/",
        "logo": "https://cdn.simpleicons.org/spotify",
        "logo_bg": "#191414",
    },
    {
        "id": "applemusic",
        "name": "Apple Music",
        "category": "music",
        "url": "https://www.apple.com/es/apple-music/",
        "fallback_url": None,
        "keywords": ["mes gratis", "meses gratis", "prueba gratuita", "free trial"],
        "negative_keywords": [],
        "cta_url": "https://www.apple.com/es/apple-music/",
        "logo": "https://cdn.simpleicons.org/applemusic/fa243c",
        "logo_bg": "#000",
    },
    {
        "id": "tidal",
        "name": "Tidal",
        "category": "music",
        "url": "https://tidal.com/es/try",
        "fallback_url": "https://tidal.com/es",
        "keywords": ["días gratis", "meses gratis", "prueba gratuita", "free trial", "gratis"],
        "negative_keywords": [],
        "cta_url": "https://tidal.com/es/try",
        "logo": "https://cdn.simpleicons.org/tidal",
        "logo_bg": "#000",
    },
    {
        "id": "qobuz",
        "name": "Qobuz",
        "category": "music",
        "url": "https://www.qobuz.com/es-es/music/subscribe",
        "fallback_url": "https://www.qobuz.com/es-es",
        "keywords": ["mes gratis", "meses gratis", "prueba gratuita", "essai gratuit", "free trial", "gratis"],
        "negative_keywords": [],
        "cta_url": "https://www.qobuz.com/es-es/music/subscribe",
        "logo": "https://cdn.simpleicons.org/qobuz",
        "logo_bg": "#192f5a",
    },
    {
        "id": "deezer",
        "name": "Deezer",
        "category": "music",
        "url": "https://www.deezer.com/es/offers/premium",
        "fallback_url": "https://www.deezer.com/es/offers",
        "keywords": ["mes gratis", "meses gratis", "prueba gratuita", "free trial", "gratis"],
        "negative_keywords": [],
        "cta_url": "https://www.deezer.com/es/offers/premium",
        "logo": "https://cdn.simpleicons.org/deezer",
        "logo_bg": "#fff",
    },
    {
        "id": "soundcloud",
        "name": "SoundCloud",
        "category": "music",
        "url": "https://soundcloud.com/go",
        "fallback_url": None,
        "keywords": ["days free", "day free", "días gratis", "mes gratis", "prueba gratuita", "free trial", "gratis"],
        "negative_keywords": [],
        "cta_url": "https://soundcloud.com/go",
        "logo": "https://cdn.simpleicons.org/soundcloud",
        "logo_bg": "#fff",
    },
]


def fetch_text(url: str) -> str | None:
    """Descarga el HTML visible (sin JS) de una URL. Devuelve None si falla."""
    try:
        resp = requests.get(url, headers=HEADERS, timeout=TIMEOUT)
        resp.raise_for_status()
        soup = BeautifulSoup(resp.text, "html.parser")
        # Eliminar scripts y estilos para quedarnos solo con texto visible
        for tag in soup(["script", "style", "noscript"]):
            tag.decompose()
        return soup.get_text(" ", strip=True).lower()
    except Exception as e:
        print(f"  ⚠ Error fetching {url}: {e}")
        return None


def extract_promo_label(text: str, keywords: list[str]) -> str:
    """
    Intenta extraer el texto de la promo (ej: "3 meses gratis")
    buscando patrones de número + unidad + keyword cerca de un keyword.
    """
    patterns = [
        r"(\d+)\s*(meses?\s+gratis)",
        r"(\d+)\s*(días?\s+gratis)",
        r"(\d+)\s*(semanas?\s+gratis)",
        r"(\d+)\s*(month[s]?\s+free)",
        r"(\d+)\s*(day[s]?\s+free)",
        r"(prueba\s+gratuita\s+de\s+\d+\s+\w+)",
        r"(\d+\s+\w+\s+de\s+prueba\s+gratis)",
    ]
    for pat in patterns:
        m = re.search(pat, text)
        if m:
            raw = m.group(0).strip()
            # Capitalizar primera letra
            return raw[:1].upper() + raw[1:]
    return "Prueba gratuita disponible"


def check_platform(p: dict) -> dict:
    """Comprueba si una plataforma tiene promo activa. Devuelve el resultado."""
    print(f"  Checking {p['name']}...")
    text = fetch_text(p["url"])
    if text is None and p.get("fallback_url"):
        print(f"    → Trying fallback: {p['fallback_url']}")
        text = fetch_text(p["fallback_url"])

    if text is None:
        # No se pudo conectar → mantenemos estado desconocido
        return {**p, "active": False, "promo_label": None, "error": True}

    # Comprobar keywords positivos
    found = any(kw.lower() in text for kw in p["keywords"])
    # Comprobar keywords negativos (invalidan el positivo)
    blocked = any(kw.lower() in text for kw in p.get("negative_keywords", []))

    active = found and not blocked
    label = extract_promo_label(text, p["keywords"]) if active else None

    return {**p, "active": active, "promo_label": label, "error": False}


def main():
    print("\n🔍 Comprobando promociones de streaming en España...")
    print(f"   Fecha: {date.today().isoformat()}\n")

    results = []
    for platform in PLATFORMS:
        result = check_platform(platform)
        status = "✅ ACTIVA" if result["active"] else ("⚠ ERROR" if result.get("error") else "❌ Sin promo")
        label = f" → {result['promo_label']}" if result.get("promo_label") else ""
        print(f"   {status}  {platform['name']}{label}")
        results.append(result)

    output = {
        "last_updated": datetime.utcnow().strftime("%Y-%m-%dT%H:%M:%SZ"),
        "last_updated_display": date.today().strftime("%-d de %B de %Y").replace(
            "January","enero").replace("February","febrero").replace("March","marzo")
            .replace("April","abril").replace("May","mayo").replace("June","junio")
            .replace("July","julio").replace("August","agosto").replace("September","septiembre")
            .replace("October","octubre").replace("November","noviembre").replace("December","diciembre"),
        "platforms": results,
    }

    out_path = Path(__file__).parent.parent / "promos.json"
    out_path.write_text(json.dumps(output, ensure_ascii=False, indent=2), encoding="utf-8")
    print(f"\n✅ promos.json actualizado en {out_path}")

    active_count = sum(1 for r in results if r["active"])
    print(f"   {active_count}/{len(results)} plataformas con promo activa.\n")


if __name__ == "__main__":
    main()
