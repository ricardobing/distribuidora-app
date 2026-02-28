"""
Wrapper OpenAI para clasificación, normalización y extracción de ventanas horarias.
Todas las llamadas son async con httpx, no con el SDK oficial para mejor control.
"""
import logging
from typing import Optional
from dataclasses import dataclass

from openai import AsyncOpenAI
from app.config import settings

logger = logging.getLogger(__name__)

_client: Optional[AsyncOpenAI] = None


def _get_client() -> AsyncOpenAI:
    global _client
    if _client is None:
        _client = AsyncOpenAI(api_key=settings.OPENAI_API_KEY)
    return _client


@dataclass
class AIClassification:
    transportista: str
    confianza: float
    raw_response: str


@dataclass
class AINormalization:
    direccion_normalizada: str
    confianza: float
    localidad: str


@dataclass
class AITimeWindow:
    resultado: str  # "HH:MM-HH:MM" o "NONE"
    confianza: float


async def classify_transport(texto: str) -> Optional[AIClassification]:
    """
    Clasifica el transportista a partir de texto libre.
    Model: gpt-4o-mini, temperature=0.
    Retorna None si la llamada falla (no propaga el error — degradación graceful).
    """
    if not settings.OPENAI_API_KEY:
        return None
    try:
        client = _get_client()
        response = await client.chat.completions.create(
            model=settings.OPENAI_MODEL,
            temperature=settings.OPENAI_TEMPERATURE,
            messages=[
                {
                    "role": "system",
                    "content": (
                        "Sos un clasificador de textos de logística en Argentina. "
                        "Dado un texto, identificás el transportista. "
                        "Respondé SOLO con JSON: {\"transportista\": \"NOMBRE\", \"confianza\": 0.95}. "
                        "Si no podés identificarlo con certeza, usá 'DESCONOCIDO'. "
                        "Nombres válidos: VIA CARGO, ANDREANI, ANDESMAR, BUS PACK, OCASA, OCA, URBANO, "
                        "CRUZ DEL SUR, VIA BARILOCHE, ACORDIS, VELOX, TRANSPORTE VESRPINI, "
                        "ENVÍO PROPIO (MOLLY MARKET), RETIRO EN COMERCIAL, EXCLUIDO, DESCONOCIDO."
                    ),
                },
                {"role": "user", "content": f"Texto: {texto[:500]}"},
            ],
            max_tokens=100,
        )
        import json
        raw = response.choices[0].message.content.strip()
        data = json.loads(raw)
        return AIClassification(
            transportista=data.get("transportista", "DESCONOCIDO"),
            confianza=float(data.get("confianza", 0.5)),
            raw_response=raw,
        )
    except Exception as e:
        logger.warning(f"AI classify_transport error: {e}")
        return None


async def normalize_address(address: str) -> Optional[AINormalization]:
    """
    Canonización de dirección: formato 'CALLE NUMERO, LOCALIDAD, MENDOZA'.
    """
    if not settings.OPENAI_API_KEY:
        return None
    try:
        client = _get_client()
        response = await client.chat.completions.create(
            model=settings.OPENAI_MODEL,
            temperature=settings.OPENAI_TEMPERATURE,
            messages=[
                {
                    "role": "system",
                    "content": (
                        "Sos un normalizador de direcciones de Mendoza, Argentina. "
                        "Dado un texto, extraé la dirección en formato: CALLE NUMERO, LOCALIDAD, MENDOZA. "
                        "Respondé SOLO con JSON: {\"direccion\": \"...\", \"localidad\": \"...\", \"confianza\": 0.95}. "
                        "Localidades válidas de Mendoza: Godoy Cruz, Guaymallén, Las Heras, "
                        "Luján de Cuyo, Maipú, Mendoza, San Rafael, Tunuyán, San Martín, Rivadavia, Junín. "
                        "Si no podés normalizarla con certeza, confianza < 0.5."
                    ),
                },
                {"role": "user", "content": f"Dirección: {address[:300]}"},
            ],
            max_tokens=150,
        )
        import json
        raw = response.choices[0].message.content.strip()
        data = json.loads(raw)
        return AINormalization(
            direccion_normalizada=data.get("direccion", address),
            confianza=float(data.get("confianza", 0.5)),
            localidad=data.get("localidad", ""),
        )
    except Exception as e:
        logger.warning(f"AI normalize_address error: {e}")
        return None


async def extract_time_window(texto: str) -> Optional[AITimeWindow]:
    """
    Extrae ventana horaria de texto libre.
    Retorna "HH:MM-HH:MM" o "NONE".
    """
    if not settings.OPENAI_API_KEY:
        return None
    try:
        client = _get_client()
        response = await client.chat.completions.create(
            model=settings.OPENAI_MODEL,
            temperature=settings.OPENAI_TEMPERATURE,
            messages=[
                {
                    "role": "system",
                    "content": (
                        "Extraé la ventana horaria de entrega del texto. "
                        "Respondé SOLO con JSON: {\"resultado\": \"HH:MM-HH:MM\", \"confianza\": 0.9}. "
                        "Si no hay ventana, resultado = 'NONE'."
                    ),
                },
                {"role": "user", "content": texto[:300]},
            ],
            max_tokens=60,
        )
        import json
        raw = response.choices[0].message.content.strip()
        data = json.loads(raw)
        return AITimeWindow(
            resultado=data.get("resultado", "NONE"),
            confianza=float(data.get("confianza", 0.5)),
        )
    except Exception as e:
        logger.warning(f"AI extract_time_window error: {e}")
        return None


async def resolve_poi(name: str, context: str = "Mendoza") -> Optional[dict]:
    """
    Resuelve un nombre de POI a dirección canónica.
    """
    if not settings.OPENAI_API_KEY:
        return None
    try:
        client = _get_client()
        response = await client.chat.completions.create(
            model=settings.OPENAI_MODEL,
            temperature=settings.OPENAI_TEMPERATURE,
            messages=[
                {
                    "role": "system",
                    "content": (
                        f"Conocés ubicaciones en {context}, Argentina. "
                        "Dado un nombre de lugar, retorná su dirección. "
                        "Respondé SOLO con JSON: {\"direccion\": \"...\", \"confianza\": 0.9}. "
                        "Si no conocés el lugar, confianza = 0."
                    ),
                },
                {"role": "user", "content": name[:200]},
            ],
            max_tokens=100,
        )
        import json
        raw = response.choices[0].message.content.strip()
        return json.loads(raw)
    except Exception as e:
        logger.warning(f"AI resolve_poi error: {e}")
        return None
