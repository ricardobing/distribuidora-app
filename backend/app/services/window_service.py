"""
Sistema de ventanas horarias.
Migra: interpretarObservacionUnificado_(), asignarVentana_() del sistema original.
"""
import re
import logging
from dataclasses import dataclass
from typing import Optional

from app.core.constants import (
    WINDOW_AM_FROM, WINDOW_AM_TO, WINDOW_PM_FROM, WINDOW_PM_TO,
    RE_PICKUP,
)

logger = logging.getLogger(__name__)


@dataclass
class WindowResult:
    tipo: str  # 'PICKUP', 'CARRIER', 'VENTANA', 'SIN_HORARIO'
    desde_min: Optional[int] = None   # minutos desde medianoche
    hasta_min: Optional[int] = None
    ventana_tipo: Optional[str] = None  # 'AM', 'PM', 'SIN_HORARIO'
    llamar_antes: bool = False
    raw_text: Optional[str] = None


def _parse_hhmm(s: str) -> int:
    """Convierte 'HH:MM' a minutos desde medianoche."""
    h, m = s.split(":")
    return int(h) * 60 + int(m)


def _ranges_intersect(a_from: int, a_to: int, b_from: int, b_to: int) -> bool:
    return a_from < b_to and b_from < a_to


def parse_window(observation_text: str) -> WindowResult:
    """
    Cascade de interpretación de ventana horaria.
    Equivalente a interpretarObservacionUnificado_().

    Pasos:
    1. Regex RETIRA/RETIRO → PICKUP
    2. Formato HH:MM-HH:MM explícito
    3. "DESDE LAS HH:MM"
    4. "HASTA LAS HH:MM"
    5. Palabras vagas (MAÑANA, TARDE, HORARIO COMERCIAL)
    6. LLAMAR ANTES
    7. SIN_HORARIO
    """
    if not observation_text:
        return WindowResult(tipo="SIN_HORARIO", ventana_tipo="SIN_HORARIO")

    text = observation_text.upper().strip()

    # 1. Pickup
    if re.search(RE_PICKUP, text, re.IGNORECASE):
        return WindowResult(tipo="PICKUP", ventana_tipo="SIN_HORARIO", raw_text=text)

    # 2. Formato explícito HH:MM-HH:MM
    m = re.search(r'(\d{1,2}:\d{2})\s*[–\-]\s*(\d{1,2}:\d{2})', text)
    if m:
        desde = _parse_hhmm(m.group(1))
        hasta = _parse_hhmm(m.group(2))
        return WindowResult(
            tipo="VENTANA",
            desde_min=desde,
            hasta_min=hasta,
            ventana_tipo=_assign_am_pm(desde, hasta),
            raw_text=text,
        )

    # 3. "DESDE LAS HH:MM" o "A PARTIR DE HH:MM"
    m = re.search(r'(?:DESDE|A PARTIR DE)\s+(?:LAS?\s+)?(\d{1,2}:\d{2})', text)
    if m:
        desde = _parse_hhmm(m.group(1))
        hasta = 23 * 60
        return WindowResult(
            tipo="VENTANA",
            desde_min=desde,
            hasta_min=hasta,
            ventana_tipo=_assign_am_pm(desde, hasta),
            raw_text=text,
        )

    # 4. "HASTA LAS HH:MM"
    m = re.search(r'HASTA\s+(?:LAS?\s+)?(\d{1,2}:\d{2})', text)
    if m:
        hasta = _parse_hhmm(m.group(1))
        desde = 0
        return WindowResult(
            tipo="VENTANA",
            desde_min=desde,
            hasta_min=hasta,
            ventana_tipo=_assign_am_pm(desde, hasta),
            raw_text=text,
        )

    # 5. Palabras vagas
    if re.search(r'\bMa[ÑN]ANA\b', text):
        return WindowResult(tipo="VENTANA", desde_min=8*60, hasta_min=13*60, ventana_tipo="AM", raw_text=text)
    if re.search(r'\bTARDE\b', text):
        return WindowResult(tipo="VENTANA", desde_min=14*60, hasta_min=21*60, ventana_tipo="PM", raw_text=text)
    if re.search(r'HORARIO COMERCIAL', text):
        return WindowResult(tipo="VENTANA", desde_min=9*60, hasta_min=18*60, ventana_tipo="SIN_HORARIO", raw_text=text)

    # 6. Llamar antes
    llamar = bool(re.search(r'LLAMAR\s+ANTES|AVISAR\s+ANTES|LLAMAR\s+ANTES\s+DE', text))
    if llamar:
        return WindowResult(tipo="SIN_HORARIO", ventana_tipo="SIN_HORARIO", llamar_antes=True, raw_text=text)

    return WindowResult(tipo="SIN_HORARIO", ventana_tipo="SIN_HORARIO", raw_text=text)


def _assign_am_pm(desde_min: int, hasta_min: int) -> str:
    """Asigna AM, PM o SIN_HORARIO a un rango de minutos."""
    if _ranges_intersect(desde_min, hasta_min, WINDOW_AM_FROM, WINDOW_AM_TO):
        if _ranges_intersect(desde_min, hasta_min, WINDOW_PM_FROM, WINDOW_PM_TO):
            return "SIN_HORARIO"
        return "AM"
    if _ranges_intersect(desde_min, hasta_min, WINDOW_PM_FROM, WINDOW_PM_TO):
        return "PM"
    return "SIN_HORARIO"


def is_within_config_window(
    window: WindowResult, hora_desde_str: str, hora_hasta_str: str
) -> bool:
    """
    Verifica si la ventana del remito intersecta con la ventana operativa de CONFIG_RUTA.
    Equivalente a filtrarPorVentanaHoraria_().
    """
    if window.tipo in ("SIN_HORARIO", "PICKUP", "CARRIER"):
        return True  # Sin restricción horaria → siempre pasa
    if window.desde_min is None or window.hasta_min is None:
        return True
    config_from = _parse_hhmm(hora_desde_str)
    config_to = _parse_hhmm(hora_hasta_str)
    return _ranges_intersect(window.desde_min, window.hasta_min, config_from, config_to)
