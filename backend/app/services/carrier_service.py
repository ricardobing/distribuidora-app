"""
Carrier detection service.
Migra: classifyTransportRegex_(), classifyTransportAI_(), determinarCategoriaFinal_()
"""
import re
import logging
from dataclasses import dataclass
from typing import Optional

from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select

from app.models.carrier import Carrier
from app.core.constants import RE_PICKUP
from app.services import ai_service

logger = logging.getLogger(__name__)


@dataclass
class CarrierDetection:
    carrier_id: Optional[int]
    nombre_canonico: str
    source: str  # 'regex', 'ai', 'rule', 'default'
    confidence: float = 1.0


def detect_pickup(texto: str) -> bool:
    """Detecta si el texto indica un retiro (sync, sin DB)."""
    if not texto:
        return False
    return bool(re.search(RE_PICKUP, texto.upper(), re.IGNORECASE))


async def detect(
    db: AsyncSession,
    texto: str,
    provincia: Optional[str] = None,
) -> CarrierDetection:
    """
    Cascade de detección de carrier:
    1. Pickup regex (hardcoded)
    2. Carriers de DB con regex (prioridad_regex ASC)
    3. AI fallback
    4. Reglas finales
    """
    if not texto:
        texto = ""
    upper_text = texto.upper()

    # 1. Pickup hardcoded
    if re.search(RE_PICKUP, upper_text, re.IGNORECASE):
        carrier = await _find_by_name(db, "RETIRO EN GALPON")
        return CarrierDetection(
            carrier_id=carrier.id if carrier else None,
            nombre_canonico="RETIRO EN GALPON",
            source="regex",
            confidence=1.0,
        )

    # 2. Regex de DB ordenados por prioridad
    result = await db.execute(
        select(Carrier)
        .where(Carrier.activo == True, Carrier.regex_pattern.isnot(None))  # noqa: E712
        .order_by(Carrier.prioridad_regex)
    )
    carriers = result.scalars().all()

    for carrier in carriers:
        try:
            if re.search(carrier.regex_pattern, upper_text, re.IGNORECASE):
                return CarrierDetection(
                    carrier_id=carrier.id,
                    nombre_canonico=carrier.nombre_canonico,
                    source="regex",
                    confidence=1.0,
                )
        except re.error:
            logger.warning(f"Invalid regex in carrier {carrier.nombre_canonico}: {carrier.regex_pattern}")

    # 3. AI fallback
    ai_result = await ai_service.classify_transport(texto)
    if ai_result and ai_result.confianza >= 0.85:
        for carrier in carriers:
            if carrier.nombre_canonico.upper() == ai_result.transportista.upper():
                return CarrierDetection(
                    carrier_id=carrier.id,
                    nombre_canonico=carrier.nombre_canonico,
                    source="ai",
                    confidence=ai_result.confianza,
                )

    # 4. Reglas finales
    return await _determinar_categoria_final(db, provincia)


async def _determinar_categoria_final(
    db: AsyncSession,
    provincia: Optional[str],
) -> CarrierDetection:
    """Fallback cuando no se detectó carrier."""
    if provincia and provincia.upper().strip() != "MENDOZA":
        carrier = await _find_by_name(db, "DESCONOCIDO")
        return CarrierDetection(
            carrier_id=carrier.id if carrier else None,
            nombre_canonico="DESCONOCIDO",
            source="rule",
            confidence=0.5,
        )

    carrier = await _find_by_name(db, "ENVIO PROPIO")
    return CarrierDetection(
        carrier_id=carrier.id if carrier else None,
        nombre_canonico="ENVIO PROPIO",
        source="default",
        confidence=0.5,
    )


async def _find_by_name(db: AsyncSession, nombre: str) -> Optional[Carrier]:
    result = await db.execute(
        select(Carrier).where(Carrier.nombre_canonico == nombre)
    )
    return result.scalar_one_or_none()
