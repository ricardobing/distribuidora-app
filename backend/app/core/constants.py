# Bounding box de Mendoza (ampliado para cubrir departamentos periféricos)
MENDOZA_LAT_MIN = -33.5
MENDOZA_LAT_MAX = -32.0
MENDOZA_LNG_MIN = -69.5
MENDOZA_LNG_MAX = -68.0

# Centros conocidos de ciudades (para excluir geocodificaciones genéricas)
# (lat, lng) de centros exactos de localidades
KNOWN_CITY_CENTERS = [
    (-32.8908, -68.8272),   # Ciudad de Mendoza
    (-32.9887, -68.8361),   # Godoy Cruz
    (-32.8833, -68.7833),   # Guaymallén
    (-32.8500, -68.8833),   # Las Heras
    (-33.0712, -68.8868),   # Luján de Cuyo
    (-32.9833, -68.6000),   # Maipú
]
CITY_CENTER_TOLERANCE_DEG = 0.001  # ~100m

# Depósito por defecto
DEPOT_LAT = -32.91973
DEPOT_LNG = -68.81829
DEPOT_DIRECCION = "Elpidio González 2753, Guaymallén, Mendoza"

# Localidades conocidas de Mendoza (para validación)
KNOWN_LOCALITIES = [
    "GODOY CRUZ", "GUAYMALLÉN", "LAS HERAS", "LUJÁN DE CUYO",
    "MAIPÚ", "SAN RAFAEL", "CAPITAL", "CIUDAD", "MENDOZA",
    "TUNUYÁN", "SAN MARTÍN", "RIVADAVIA", "JUNÍN",
    "GUAYMALLEN", "LUJAN DE CUYO", "MAIPU",
]

# Ventanas horarias (minutos desde medianoche)
WINDOW_AM_FROM = 9 * 60    # 09:00 → 540
WINDOW_AM_TO = 13 * 60     # 13:00 → 780
WINDOW_PM_FROM = 14 * 60   # 14:00 → 840
WINDOW_PM_TO = 18 * 60     # 18:00 → 1080

# Pickup regex (hardcoded porque es estable y crítico)
RE_PICKUP = r'\b(?:RETIRA(?!R)(?:\s+POR|\s+EN)?\s*(?:COMERCIAL|DEP[OÓ]SITO|LOCAL|TIENDA|SUCURSAL)?|SE\s+RETIRA|RETIRO\s+CLIENTE|PASA\s+A\s+RETIRAR)\b'

# App version
APP_VERSION = "1.0.0"
CODE_VERSION = "v1.0.0-molymarket"

# Velocidad urbana estimada (km/h) para Haversine pre-filtro
URBAN_SPEED_KMH = 40.0

# Max waypoints por link de Google Maps
MAX_GMAPS_WAYPOINTS = 10

# Max distancia desde depósito para incluir en ruta
MAX_DISTANCE_FROM_DEPOT_KM = 45.0
