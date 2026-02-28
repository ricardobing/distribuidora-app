# MolyMarket — Smoke Test

Script de verificación automática del circuito crítico.

## Qué valida

El test replica el flujo QA manual completo en 14 pasos secuenciales:

| Paso | Qué verifica |
|------|-------------|
| 01 Health Check | Backend responde en `/health` con `status=ok` |
| 02 Authentication | Login retorna JWT válido, rol=admin, user_id |
| 03 Carriers Seed | 15 carriers cargados, nombres canónicos presentes |
| 04 Cleanup | Elimina datos SMOKE* de ejecuciones anteriores |
| 05 Create Remitos | Crea 3 remitos: carrier detectado, es_urgente/es_prioridad/telefono guardados |
| 06 Inject GPS | Inyecta coordenadas reales de Mendoza via `docker exec psql` (simula geocodificación) |
| 07 Armar | `POST /remitos/{id}/armar` → lifecycle=armado, clasificacion=enviar |
| 08 Generar Ruta | Ruta con ≥ 3 paradas, distancia > 0, link Google Maps generado |
| 09 QR Scan | `GET /entregados/qr/{numero}` retorna remito con estado correcto |
| 10 Mark Entregados | `POST /entregados/marcar` → N remitos marcados |
| 11 Mover Histórico | `POST /entregados/procesar` → N remitos en histórico |
| 12 Verify Histórico | Los 3 SMOKE* aparecen en `GET /historico/` |
| 13 Dashboard | `entregas_hoy ≥ 3`, `ruta_hoy` presente con paradas_completadas ≥ 3 |
| 14 Geocoding Stats | Endpoint `/dashboard/stats/geocoding` accesible |

## Requisitos

- Python 3.11+
- `docker` en el PATH
- Contenedores corriendo: `molymarket-postgres`, `molymarket-backend`

```bash
# Instalar dependencia
pip install requests

# O con el requirements.txt local
pip install -r qa/requirements.txt
```

## Cómo ejecutar

```bash
# Desde la raíz del proyecto
python qa/qa_smoke_test.py
```

Salida esperada si todo OK:

```
══════════════════════════════════════════════════════
  MOLYMARKET SMOKE TEST
  2026-02-28  22:30:00
══════════════════════════════════════════════════════
  Target : http://localhost:8000/api/v1
  ...
  RESULTADO FINAL
══════════════════════════════════════════════════════
  PASSED :  38 / 38

  SMOKE TEST PASSED — sistema OK
```

Exit code `0` = sistema OK.  
Exit code `1` = al menos un assert falló.

## Cuándo correrlo

| Situación | Acción |
|-----------|--------|
| Antes de hacer un deploy | Correr para confirmar que el sistema base está OK |
| Después de un deploy | Correr para confirmar que nada se rompió |
| Después de cambiar código de backend | Correr para detectar regresiones |
| Al reportar un bug | Correr para reproducirlo o descartarlo |
| En CI/CD pipeline | Añadir como step post-deploy |

## Qué significa que falle

```
FAIL  SMOKE02: carrier = ENVIO PROPIO  →  expected='ENVIO PROPIO'  got='DESCONOCIDO'
```

Cada línea `FAIL` indica:
- **qué paso falló** (ej: `SMOKE02: carrier = ENVIO PROPIO`)
- **qué se esperaba** vs **qué llegó**

### Fallos comunes y su causa probable

| Error | Causa probable |
|-------|---------------|
| `Backend unreachable` | El container `molymarket-backend` no está corriendo |
| `Login falló` | Credenciales cambiadas o tabla `usuarios` vacía |
| `carrier count > 10` | Migración 002 no corrió o falló |
| `GPS injection` | Container `molymarket-postgres` no está corriendo o nombre cambió |
| `lifecycle = armado` | Bug en `POST /remitos/{id}/armar` |
| `total_paradas >= 3` | Bug en route_service o remitos no tienen coords |
| `{num} NOT found in historico` | Bug en delivery_service.move_to_historico |
| `entregas_hoy >= 3` | Bug en dashboard o zona horaria del servidor |

## Configuración

Las variables de entorno pueden sobreescribirse editando las constantes al inicio del script:

```python
API_HOST           = "http://localhost:8000"
ADMIN_EMAIL        = "admin@molymarket.com"
ADMIN_PASSWORD     = "admin1234"
POSTGRES_CONTAINER = "molymarket-postgres"
POSTGRES_USER      = "moly"
POSTGRES_DB        = "molymarket"
```

## Arquitectura del test

```
main()
  ├── t01_health()           HTTP GET /health
  ├── t02_login()            HTTP POST /auth/login  → guarda JWT
  ├── t03_carriers()         HTTP GET /carriers/
  ├── t04_cleanup()          docker exec psql DELETE FROM remitos WHERE numero LIKE 'SMOKE%'
  ├── t05_create_remitos()   HTTP POST /remitos/ x3
  ├── t06_inject_gps()       docker exec psql UPDATE remitos SET lat/lng
  ├── t07_armar()            HTTP POST /remitos/{id}/armar x3
  ├── t08_generar_ruta()     HTTP POST /rutas/generar
  ├── t09_qr_scan()          HTTP GET /entregados/qr/{numero} x3
  ├── t10_mark_entregado()   HTTP POST /entregados/marcar
  ├── t11_procesar_hist()    HTTP POST /entregados/procesar
  ├── t12_verify_hist()      HTTP GET /historico/
  ├── t13_dashboard()        HTTP GET /dashboard/
  └── t14_geocoding_stats()  HTTP GET /dashboard/stats/geocoding
```

Cada paso falla de forma aislada — un fallo en t07 no cancela t08..t14.  
Solo `t01_health` y `t02_login` hacen `sys.exit(1)` inmediato (sin token no puede continuar).
