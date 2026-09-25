---
inclusion: always
---

## 4. Platform Standards (vincolanti per tutti i servizi)

Da inserire in Kiro come **steering file** (`.kiro/steering/platform-standards.md`).

| Tema | Regola |
|---|---|
| Avvio dei servizi | Un file `services.yaml` nella root dichiara, per ogni servizio implementato, la cartella di lavoro (`cwd`) e il comando di avvio (`command`). La suite di collaudo lo legge e passa a ogni servizio le variabili `PORT` e `*_SERVICE_URL`. Ogni servizio **deve** ascoltare sulla porta indicata da `PORT` |
| Base path | `/api/v1/<risorsa>` |
| Formato | JSON, campi in `snake_case` |
| Identificativi | `id` UUID v4 generato dal server, mai accettato in input |
| Timestamp | ISO 8601 UTC (`2026-10-15T09:30:00Z`); ogni risorsa ha `created_at` e `updated_at` |
| Date / importi | Date `YYYY-MM-DD` · importi numerici con 2 decimali (`149.00`), valuta implicita EUR |
| Paginazione | `?page=1&page_size=20` (max 100) → `{"items": [...], "page": 1, "page_size": 20, "total": 57}` |
| Errori | Sempre `{"error": {"code": "UPPER_SNAKE", "message": "...", "details": {...}}}` |
| Status code | 201 creazione (+ header `Location`) · 200 lettura/modifica · 204 cancellazione · 400 JSON malformato · 404 `NOT_FOUND` · 405 metodo non previsto · 409 conflitto · 422 `VALIDATION_ERROR` / `REFERENCE_NOT_FOUND` / regole di business · 503 `DEPENDENCY_UNAVAILABLE` |
| Chiamate tra servizi | URL solo da variabili d'ambiente (`USER_SERVICE_URL`, `EVENT_SERVICE_URL`, `REGISTRATION_SERVICE_URL`), default `http://localhost:<porta>`. Timeout 2 s. 404 dal servizio chiamato → 422 `REFERENCE_NOT_FOUND`; timeout, connessione rifiutata o 5xx → 503 `DEPENDENCY_UNAVAILABLE` |
| Health | `GET /health` → `200 {"status": "ok", "service": "<nome>"}` |
| **Persistenza** | Variabile `STORAGE_BACKEND` = `memory` (default) · `json` · `sqlite`. Con `json`/`sqlite` i file vanno in `DATA_DIR` (default `./data`, esclusa da git). **Solo librerie standard** (`json`, `sqlite3`): nessun DBMS da installare o configurare. Il cambio di backend non deve richiedere modifiche alla logica di business |
| Dipendenze Python | `flask`, `requests` (runtime) · `pytest`, `pytest-cov`, `responses` (test) |

---
