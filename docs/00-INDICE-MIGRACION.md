# Migración MolyMarket — Índice de Documentos de Diseño

**Fecha:** 28-02-2026  
**Stack destino:** FastAPI + PostgreSQL/PostGIS + Next.js  
**Deploy:** Railway (backend + DB) + Vercel (frontend)

---

## Documentos

| # | Documento | Contenido |
|---|-----------|-----------|
| 01 | [Sistema Actual](01-SISTEMA-ACTUAL.md) | Resumen completo del sistema existente, flujos, componentes, hojas, APIs externas |
| 02 | [Modelo de Base de Datos](02-MODELO-BASE-DE-DATOS.md) | Tablas, campos, tipos, relaciones, índices, PostGIS, scripts SQL |
| 03 | [Arquitectura API FastAPI](03-ARQUITECTURA-API-FASTAPI.md) | Endpoints, servicios, estructura de carpetas, migración de lógica |
| 04 | [Arquitectura Frontend Next.js](04-ARQUITECTURA-FRONTEND-NEXTJS.md) | Páginas, componentes, mapa Leaflet, flujos de usuario |
| 05 | [Plan de Migración](05-PLAN-MIGRACION.md) | Fases, convivencia con Sheets, orden de implementación, reutilización de código |

---

*Cada documento es autónomo. Otra instancia de Claude puede leer cualquiera de ellos e implementar esa sección sin ambigüedades.*
