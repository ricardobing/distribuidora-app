import re
import unicodedata


# Mapa de abreviaciones → forma completa
_ABBREV_MAP = {
    r'\bav\b': 'avenida',
    r'\bavda\b': 'avenida',
    r'\bdpto\b': 'departamento',
    r'\bdep\b': 'departamento',
    r'\bbv\b': 'boulevard',
    r'\bblvd\b': 'boulevard',
    r'\bcjal\b': 'concejal',
    r'\bgral\b': 'general',
    r'\bgte\b': 'gente',
    r'\bpje\b': 'pasaje',
    r'\bpas\b': 'pasaje',
    r'\bsdte\b': 'subdelegado',
    r'\bpte\b': 'presidente',
    r'\bdr\b': 'doctor',
    r'\bsam\b': 'san martin',
    r'\bprov\b': 'provincia',
    r'\bloc\b': 'localidad',
    r'\bhdez\b': 'hernandez',
    r'\bfdez\b': 'fernandez',
    r'\bfco\b': 'francisco',
    r'\bjse\b': 'jose',
}

# Localidades de Mendoza y sus variantes para normalización
_CITY_ALIASES = {
    "CIUDAD": "MENDOZA",
    "CAPITAL": "MENDOZA",
    "CIUDAD DE MENDOZA": "MENDOZA",
    "MZA": "MENDOZA",
    "GCR": "GODOY CRUZ",
    "GUAYMALLEN": "GUAYMALLÉN",
    "MAIPU": "MAIPÚ",
    "LUJAN": "LUJÁN DE CUYO",
    "LUJAN DE CUYO": "LUJÁN DE CUYO",
}


def normalize(address: str) -> str:
    """
    Normaliza una dirección:
    1. NFD decomposition → strip diacríticos
    2. Lowercase
    3. Expandir abreviaciones
    4. Colapsar espacios

    Equivalente a normalizarDireccion_() del sistema original.
    """
    if not address:
        return ""
    # NFD → strip combining characters (diacríticos)
    nfd = unicodedata.normalize("NFD", address)
    stripped = "".join(c for c in nfd if unicodedata.category(c) != "Mn")
    lower = stripped.lower().strip()

    for pattern, replacement in _ABBREV_MAP.items():
        lower = re.sub(pattern, replacement, lower, flags=re.IGNORECASE)

    # Colapsar espacios múltiples
    normalized = re.sub(r'\s+', ' ', lower).strip()
    return normalized


def normalize_key(address: str) -> str:
    """Clave de cache: normalizada + uppercase + sin puntuación."""
    n = normalize(address)
    key = n.upper()
    key = re.sub(r'[^\w\s]', '', key)
    key = re.sub(r'\s+', '_', key.strip())
    return key


def fix_ciudad_mendoza(address: str) -> str:
    """
    Reemplaza variantes de 'Ciudad/Capital, Mendoza' por 'MENDOZA, MENDOZA'.
    Equivalente a reemplazarCiudadMendoza_().
    """
    upper = address.upper()
    for alias, canonical in _CITY_ALIASES.items():
        upper = re.sub(r'\b' + re.escape(alias) + r'\b', canonical, upper)
    return upper


def extract_street_base(address: str) -> str:
    """
    Extrae el nombre de calle sin número, departamento ni prefijos.
    Equivalente a extraerCalleBase_().
    """
    # Remover número de calle
    no_num = re.sub(r'\b\d+\b', '', address)
    # Remover prefijos comunes
    no_prefix = re.sub(r'\b(calle|av|avenida|bv|boulevard|pasaje|pje)\b', '', no_num, flags=re.IGNORECASE)
    return re.sub(r'\s+', ' ', no_prefix).strip()


def reorder_components(address: str, localidad: str = "Mendoza") -> str:
    """
    Asegura el formato: CALLE NUMERO, LOCALIDAD, MENDOZA
    Si la localidad no aparece, la agrega.
    """
    parts = [p.strip() for p in address.split(",")]
    if len(parts) == 1:
        return f"{parts[0]}, {localidad}, Mendoza"
    if len(parts) == 2:
        return f"{parts[0]}, {parts[1]}, Mendoza"
    return address
