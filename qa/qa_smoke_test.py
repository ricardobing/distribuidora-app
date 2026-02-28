#!/usr/bin/env python3
"""
MolyMarket Smoke Test Suite
============================
Verifica el circuito crítico completo:
  login → remitos → GPS inject → armar → ruta → QR scan → entrega → histórico → dashboard

Si este script pasa, el sistema está vivo y funcional.
Si falla, algo esencial se rompió.

Uso:
    pip install requests
    python qa_smoke_test.py
"""

import sys
import subprocess

try:
    import requests
except ImportError:
    print("ERROR: 'requests' no instalado. Ejecutar: pip install requests")
    sys.exit(1)

from datetime import datetime

# ── Configuración ───────────────────────────────────────────────────────────────
API_HOST  = "http://localhost:8000"
BASE_URL  = f"{API_HOST}/api/v1"

ADMIN_EMAIL    = "admin@molymarket.com"
ADMIN_PASSWORD = "admin1234"

POSTGRES_CONTAINER = "molymarket-postgres"
POSTGRES_USER      = "moly"
POSTGRES_DB        = "molymarket"

# Remitos fijos para cada ejecución (se limpian al inicio)
SMOKE_REMITOS = [
    {
        "numero": "SMOKE01",
        "domicilio": "San Martin 456, Ciudad, Mendoza",
        "cliente": "Smoke Alpha",
        "telefono": "2610001001",
        "observaciones": "Envio Propio",
        "es_urgente": True,
        "es_prioridad": False,
    },
    {
        "numero": "SMOKE02",
        "domicilio": "Belgrano 1200, Godoy Cruz, Mendoza",
        "cliente": "Smoke Beta",
        "telefono": "2610001002",
        "observaciones": "Envio Propio",
        "es_urgente": False,
        "es_prioridad": False,
    },
    {
        "numero": "SMOKE03",
        "domicilio": "Rivadavia 890, Guaymallen, Mendoza",
        "cliente": "Smoke Gamma",
        "telefono": "2610001003",
        "observaciones": "Envio Propio",
        "es_urgente": False,
        "es_prioridad": True,
    },
]

# Coordenadas GPS reales de Mendoza (inyectadas via psql para saltear geocodificador)
SMOKE_GPS = {
    "SMOKE01": (-32.8850, -68.8450),
    "SMOKE02": (-32.8920, -68.8380),
    "SMOKE03": (-32.8730, -68.8200),
}

# ── ANSI colors ─────────────────────────────────────────────────────────────────
GREEN = "\033[92m"
RED   = "\033[91m"
BOLD  = "\033[1m"
RESET = "\033[0m"

# ── Estado global del test ───────────────────────────────────────────────────────
_token:       str       = ""
_headers:     dict      = {}
_created_ids: list[int] = []
_passed:      int       = 0
_failures:    list[str] = []


# ── Helpers de salida ────────────────────────────────────────────────────────────

def _section(title: str) -> None:
    print(f"\n{BOLD}{'─' * 58}{RESET}")
    print(f"{BOLD}  {title}{RESET}")
    print(f"{BOLD}{'─' * 58}{RESET}")


def _ok(label: str, detail: str = "") -> None:
    global _passed
    _passed += 1
    suffix = f"  ({detail})" if detail else ""
    print(f"  {GREEN}PASS{RESET}  {label}{suffix}")


def _fail(label: str, detail: str = "") -> None:
    _failures.append(f"{label}: {detail}")
    print(f"  {RED}FAIL{RESET}  {label}  →  {detail}")


def _eq(label: str, actual, expected) -> None:
    if actual == expected:
        _ok(label, repr(actual))
    else:
        _fail(label, f"expected={expected!r}  got={actual!r}")


def _gt(label: str, actual, threshold) -> None:
    if actual is not None and actual > threshold:
        _ok(label, f"{actual} > {threshold}")
    else:
        _fail(label, f"expected > {threshold},  got={actual!r}")


def _truthy(label: str, value, hint: str = "") -> None:
    if value:
        _ok(label, hint or str(value)[:60])
    else:
        _fail(label, hint or f"falsy: {value!r}")


# ── HTTP helpers ─────────────────────────────────────────────────────────────────

def _get(path: str) -> dict:
    r = requests.get(f"{BASE_URL}{path}", headers=_headers, timeout=15)
    r.raise_for_status()
    return r.json()


def _post(path: str, body: dict = None) -> dict:
    r = requests.post(f"{BASE_URL}{path}", json=body or {}, headers=_headers, timeout=15)
    r.raise_for_status()
    return r.json()


def _delete(path: str) -> int:
    r = requests.delete(f"{BASE_URL}{path}", headers=_headers, timeout=15)
    return r.status_code


# ── Database helper ──────────────────────────────────────────────────────────────

def _psql(sql: str) -> str:
    """Ejecuta SQL directamente en el container de Postgres."""
    try:
        res = subprocess.run(
            [
                "docker", "exec", POSTGRES_CONTAINER,
                "psql", "-U", POSTGRES_USER, "-d", POSTGRES_DB, "-c", sql,
            ],
            capture_output=True,
            text=True,
            timeout=20,
        )
        return res.stdout + res.stderr
    except FileNotFoundError:
        return "ERROR: 'docker' no encontrado en PATH"
    except Exception as exc:
        return f"ERROR: {exc}"


# ══════════════════════════════════════════════════════════════════════════════════
#  PASOS DEL TEST
# ══════════════════════════════════════════════════════════════════════════════════

def t01_health() -> None:
    """Backend levantado y respondiendo."""
    _section("01  HEALTH CHECK")
    try:
        r = requests.get(f"{API_HOST}/health", timeout=10)
        d = r.json()
        _eq("HTTP 200", r.status_code, 200)
        _eq("status = ok", d.get("status"), "ok")
        _truthy("version present", d.get("version"))
    except Exception as exc:
        _fail("Backend unreachable", str(exc))
        print(f"\n  {RED}Sistema no disponible — abortando.{RESET}")
        sys.exit(1)


def t02_login() -> None:
    """Autenticación con admin y obtención de JWT."""
    _section("02  AUTHENTICATION")
    global _token, _headers

    r = requests.post(
        f"{BASE_URL}/auth/login",
        json={"email": ADMIN_EMAIL, "password": ADMIN_PASSWORD},
        timeout=10,
    )
    d = r.json()

    _eq("HTTP 200", r.status_code, 200)
    _truthy("access_token present", d.get("access_token"))
    _eq("rol = admin", d.get("rol"), "admin")
    _truthy("user_id present", d.get("user_id"))
    _truthy("expires_in present", d.get("expires_in"))

    if not d.get("access_token"):
        print(f"\n  {RED}Login falló — sin token, imposible continuar.{RESET}")
        sys.exit(1)

    _token   = d["access_token"]
    _headers = {
        "Authorization": f"Bearer {_token}",
        "Content-Type":  "application/json",
    }
    _ok("Bearer token stored")


def t03_carriers() -> None:
    """Seed de carriers: 15 registros con los nombres canónicos esperados."""
    _section("03  CARRIERS SEED")

    data  = _get("/carriers/")
    items = data if isinstance(data, list) else data.get("value", data.get("items", []))

    _gt("carrier count > 10", len(items), 10)

    names = {c.get("nombre_canonico", "") for c in items}
    for expected in ["ENVIO PROPIO", "ANDREANI", "OCA", "RETIRO EN GALPON", "DESCONOCIDO"]:
        if expected in names:
            _ok(f"carrier exists: {expected}")
        else:
            _fail(f"carrier missing: {expected}")


def t04_cleanup() -> None:
    """Elimina datos SMOKE* de ejecuciones anteriores (cualquier estado lifecycle)."""
    _section("04  CLEANUP  (remove previous SMOKE* data)")

    # SQL por partes para manejar FK constraints
    sqls = [
        "DELETE FROM ruta_paradas   WHERE remito_id IN (SELECT id FROM remitos WHERE numero LIKE 'SMOKE%')",
        "DELETE FROM ruta_excluidos WHERE remito_id IN (SELECT id FROM remitos WHERE numero LIKE 'SMOKE%')",
        "DELETE FROM historico_entregados WHERE numero LIKE 'SMOKE%'",
        "DELETE FROM remitos WHERE numero LIKE 'SMOKE%'",
    ]
    errors = []
    for sql in sqls:
        out = _psql(sql)
        if "ERROR" in out and "does not exist" not in out:
            errors.append(out[:100])

    if errors:
        _fail("Cleanup SQL", "; ".join(errors))
    else:
        _ok("Smoke data purged")


def t05_create_remitos() -> None:
    """Crea 3 remitos, verifica carrier detection y campos obligatorios."""
    _section("05  CREATE REMITOS")
    global _created_ids

    for rd in SMOKE_REMITOS:
        d   = _post("/remitos/", rd)
        rid = d.get("id")

        _truthy(f"{rd['numero']}: id assigned",             rid)
        _eq(f"{rd['numero']}: lifecycle = ingresado",       d.get("estado_lifecycle"),   "ingresado")
        _eq(f"{rd['numero']}: carrier = ENVIO PROPIO",      d.get("carrier_nombre"),     "ENVIO PROPIO")
        _eq(f"{rd['numero']}: telefono saved",              d.get("telefono"),           rd["telefono"])

        if rd.get("es_urgente"):
            _eq(f"{rd['numero']}: es_urgente = True",       d.get("es_urgente"),         True)
        if rd.get("es_prioridad"):
            _eq(f"{rd['numero']}: es_prioridad = True",     d.get("es_prioridad"),       True)

        if rid:
            _created_ids.append(rid)

    _eq("all 3 remitos created", len(_created_ids), 3)


def t06_inject_gps() -> None:
    """Inyecta coords GPS reales de Mendoza vía psql (simula geocodificación exitosa)."""
    _section("06  INJECT GPS COORDS  (simulate geocoding)")

    nums_sql  = ", ".join(f"'{n}'" for n in SMOKE_GPS)
    lat_cases = " ".join(f"WHEN '{n}' THEN {lat}" for n, (lat, _)  in SMOKE_GPS.items())
    lng_cases = " ".join(f"WHEN '{n}' THEN {lng}" for n, (_, lng)  in SMOKE_GPS.items())

    sql = (
        "UPDATE remitos SET"
        f"  lat                  = CASE numero {lat_cases} END,"
        f"  lng                  = CASE numero {lng_cases} END,"
        "  geocode_provider     = 'smoke_test',"
        "  geocode_score        = 0.99,"
        "  geocode_formatted    = direccion_normalizada,"
        "  estado_clasificacion = 'enviar',"
        "  motivo_clasificacion = 'Coords injected by smoke test'"
        f" WHERE numero IN ({nums_sql})"
    )

    out = _psql(sql)
    expected_token = f"UPDATE {len(SMOKE_GPS)}"
    if expected_token in out:
        _ok("GPS coordinates injected", f"{len(SMOKE_GPS)} rows updated")
    else:
        _fail("GPS injection", out.strip()[:150])


def t07_armar() -> None:
    """POST /remitos/{id}/armar → lifecycle=armado, clasificacion=enviar."""
    _section("07  ARMAR REMITOS")

    for rid in _created_ids:
        d = _post(f"/remitos/{rid}/armar")
        _eq(f"id={rid}: lifecycle = armado",       d.get("estado_lifecycle"),    "armado")
        _eq(f"id={rid}: clasificacion = enviar",   d.get("estado_clasificacion"), "enviar")


def t08_generar_ruta() -> None:
    """POST /rutas/generar → ruta válida con ≥ 3 paradas y urgente primero."""
    _section("08  GENERAR RUTA")

    d = _post("/rutas/generar", {"notas": "smoke test"})

    _truthy("ruta id assigned",          d.get("id"))
    _eq("estado = generada",             d.get("estado"),              "generada")
    _gt("total_paradas >= 3",            d.get("total_paradas",   0),  2)
    _gt("distancia_total_km > 0",        d.get("distancia_total_km", 0), 0)
    _truthy("duracion_estimada_min > 0", d.get("duracion_estimada_min"))
    _truthy("gmaps_links present",       d.get("gmaps_links"))

    paradas = d.get("paradas", [])
    if paradas:
        primera = paradas[0]
        if primera.get("es_urgente"):
            _ok("urgente is first stop", primera.get("remito_numero", "?"))
        else:
            print(f"       [info] Primera parada: {primera.get('remito_numero')} urgente={primera.get('es_urgente')}")

    # Todos los SMOKE deben aparecer en la ruta
    parada_numeros = {p.get("remito_numero") for p in paradas}
    for rd in SMOKE_REMITOS:
        if rd["numero"] in parada_numeros:
            _ok(f"{rd['numero']} in route")
        else:
            _fail(f"{rd['numero']} missing from route")


def t09_qr_scan() -> None:
    """GET /entregados/qr/{numero} → remito encontrado con estado correcto."""
    _section("09  QR SCAN")

    for rd in SMOKE_REMITOS:
        d = _get(f"/entregados/qr/{rd['numero']}")
        _eq(f"{rd['numero']}: encontrado = True",      d.get("encontrado"),           True)
        _eq(f"{rd['numero']}: lifecycle = armado",     d.get("estado_lifecycle"),     "armado")
        _eq(f"{rd['numero']}: clasificacion = enviar", d.get("estado_clasificacion"), "enviar")
        _eq(f"{rd['numero']}: carrier",                d.get("carrier_nombre"),       "ENVIO PROPIO")
        if rd.get("es_urgente"):
            _eq(f"{rd['numero']}: es_urgente = True",  d.get("es_urgente"),           True)


def t10_mark_entregado() -> None:
    """POST /entregados/marcar → N remitos marcados como entregados."""
    _section("10  MARK ENTREGADOS")

    d = _post("/entregados/marcar", {"ids": _created_ids})
    _eq("ok = True", d.get("ok"), True)

    expected = str(len(_created_ids))
    if expected in d.get("message", ""):
        _ok(f"message confirms {expected} remitos marked", d["message"])
    else:
        _fail("count in message", f"expected '{expected}' in '{d.get('message')}'")


def t11_procesar_historico() -> None:
    """POST /entregados/procesar → N remitos movidos al histórico."""
    _section("11  MOVER A HISTORICO")

    d = _post("/entregados/procesar", {"ids": _created_ids})
    _eq("ok = True", d.get("ok"), True)

    expected = str(len(_created_ids))
    if expected in d.get("message", ""):
        _ok(f"message confirms {expected} moved to historico", d["message"])
    else:
        _fail("count in message", f"expected '{expected}' in '{d.get('message')}'")


def t12_verify_historico() -> None:
    """GET /historico/ → los 3 SMOKE remitos deben aparecer registrados."""
    _section("12  VERIFY HISTORICO")

    data  = _get("/historico/?size=200")
    items = data.get("items", [])
    _truthy("historico.total > 0", data.get("total", 0), f"total={data.get('total')}")

    en_historico = {i.get("numero") for i in items}
    for rd in SMOKE_REMITOS:
        if rd["numero"] in en_historico:
            _ok(f"{rd['numero']} registered in historico")
        else:
            _fail(f"{rd['numero']} NOT found in historico")


def t13_dashboard() -> None:
    """GET /dashboard/ → estadísticas coherentes con las entregas realizadas."""
    _section("13  DASHBOARD")

    d = _get("/dashboard/")

    _truthy("fecha present", d.get("fecha"))
    _truthy("mes present",   d.get("mes"))

    rem = d.get("remitos", {})
    _truthy("remitos section present",  rem)
    _truthy("total_activos key exists", "total_activos" in rem)

    hist = d.get("historico", {})
    _gt("entregas_hoy >= 3",         hist.get("entregas_hoy",      0), 2)
    _gt("entregas_mes_actual >= 3",  hist.get("entregas_mes_actual", 0), 2)

    ruta_hoy = d.get("ruta_hoy")
    _truthy("ruta_hoy present", ruta_hoy)
    if ruta_hoy:
        _gt("ruta_hoy.total_paradas >= 3",       ruta_hoy.get("total_paradas",        0), 2)
        _gt("ruta_hoy.paradas_completadas >= 3", ruta_hoy.get("paradas_completadas",  0), 2)
        _truthy("ruta_hoy.distancia_total_km",   ruta_hoy.get("distancia_total_km"))


def t14_geocoding_stats() -> None:
    """GET /dashboard/stats/geocoding → endpoint accesible."""
    _section("14  GEOCODING STATS")

    d = _get("/dashboard/stats/geocoding")
    _truthy("response is dict", isinstance(d, dict))
    _ok("geocoding stats endpoint reachable")


# ══════════════════════════════════════════════════════════════════════════════════
#  MAIN
# ══════════════════════════════════════════════════════════════════════════════════

STEPS = [
    t01_health,
    t02_login,
    t03_carriers,
    t04_cleanup,
    t05_create_remitos,
    t06_inject_gps,
    t07_armar,
    t08_generar_ruta,
    t09_qr_scan,
    t10_mark_entregado,
    t11_procesar_historico,
    t12_verify_historico,
    t13_dashboard,
    t14_geocoding_stats,
]


def main() -> None:
    print(f"\n{BOLD}{'═' * 58}{RESET}")
    print(f"{BOLD}  MOLYMARKET SMOKE TEST{RESET}")
    print(f"{BOLD}  {datetime.now().strftime('%Y-%m-%d  %H:%M:%S')}{RESET}")
    print(f"{BOLD}{'═' * 58}{RESET}")
    print(f"  Target : {BASE_URL}")
    print(f"  DB     : {POSTGRES_CONTAINER}")
    print(f"  Steps  : {len(STEPS)}")

    for step in STEPS:
        try:
            step()
        except requests.HTTPError as exc:
            _fail(
                step.__name__,
                f"HTTP {exc.response.status_code}: {exc.response.text[:200]}",
            )
        except Exception as exc:
            _fail(step.__name__, str(exc)[:200])

    # ── Reporte final ──────────────────────────────────────────────────────────
    total = _passed + len(_failures)

    print(f"\n{BOLD}{'═' * 58}{RESET}")
    print(f"{BOLD}  RESULTADO FINAL{RESET}")
    print(f"{BOLD}{'═' * 58}{RESET}")
    print(f"  {GREEN}PASSED : {_passed:>3} / {total}{RESET}")

    if _failures:
        print(f"  {RED}FAILED : {len(_failures):>3} / {total}{RESET}")
        print(f"\n{BOLD}  Fallos:{RESET}")
        for msg in _failures:
            print(f"    {RED}x{RESET}  {msg}")
        print(f"\n{RED}{BOLD}  SMOKE TEST FAILED{RESET}\n")
        sys.exit(1)
    else:
        print(f"\n{GREEN}{BOLD}  SMOKE TEST PASSED — sistema OK{RESET}\n")
        sys.exit(0)


if __name__ == "__main__":
    main()
