# event-service

Gestione conferenze, con verifica dell'organizzatore tramite user-service.
T-01..T-07 completati; servizio dichiarato nel manifest.

## Avvio

Prima avviare user-service. Dalla root, dopo `make setup`:

```bash
cd services/event-service
PORT=5002 STORAGE_BACKEND=sqlite DATA_DIR=./data USER_SERVICE_URL=http://localhost:5001 ../../.venv/bin/python -m app
```

| Variabile | Default | Significato |
|---|---|---|
| PORT | 5002 | Porta TCP, intero 1..65535 |
| USER_SERVICE_URL | http://localhost:5001 | Base URL HTTP/HTTPS del servizio utenti |
| STORAGE_BACKEND | memory | memory, json, sqlite |
| DATA_DIR | ./data | Directory dati relativa al cwd |

Il server locale ascolta su 127.0.0.1, senza debugger/reloader e senza risoluzione
DNS inversa durante l'avvio. Target macOS/Linux, sviluppo e collaudo.
Memory è isolato per istanza e si svuota ai riavvii. JSON usa events.json,
SQLite usa events.db: entrambi persistono ai riavvii. I nomi distinti da quelli
degli utenti permettono anche una DATA_DIR comune.

JSON prevede un solo processo scrittore per directory. SQLite conserva documenti
JSON in una tabella e usa transazioni per le scritture; liste e filtri effettuano
una scansione dei record, adeguata al dataset del progetto. La logica di dominio
non dipende dal backend. Update legge, valida e scrive nello stesso lock/transazione.

## API e regole

| Metodo | Percorso | Esito |
|---|---|---|
| GET | /health | 200 con status=ok e service=event-service, anche senza user-service |
| POST | /api/v1/events | 201 e Location |
| GET | /api/v1/events | Lista paginata con filtri status/city |
| GET | /api/v1/events/{id} | Evento oppure 404 |
| PUT | /api/v1/events/{id} | Sostituzione completa |
| PATCH | /api/v1/events/{id} | Aggiornamento parziale |
| DELETE | /api/v1/events/{id} | 204 senza body oppure 404 |

POST e PUT richiedono title, organizer_id, venue, city, start_date, end_date,
capacity e price. Title ha 3..120 caratteri; venue massimo 100, city massimo 60,
description massimo 2000 e può essere null. Date reali YYYY-MM-DD, con fine non
precedente all'inizio; capacity intero 1..10000, price numerico finito non negativo.
Il prezzo è arrotondato a centesimi con ROUND_HALF_UP.

Id UUID v4 e timestamp UTC sono generati dal server. Campi extra, id e timestamp
nel body sono rifiutati. Description/status omessi diventano null/draft.
EventCreate consente uno status esplicito anche alla creazione.

Le sole transizioni sono draft→published, draft→cancelled e published→cancelled.
Reinviare lo stesso stato è consentito. PUT ripristina i default: su un evento
published, omettere status tenta un ritorno a draft e viene rifiutato.
PATCH preserva i campi omessi; {} non cambia nulla, timestamp incluso.
Date e transizioni del PATCH sono controllate sul record risultante.

L'organizzatore viene verificato su POST, PUT e quando organizer_id è presente
nel PATCH, con GET /api/v1/users/{id}, timeout 2 s e redirect disabilitati.
Le chiamate terminano prima della transazione di scrittura.

| Problema | HTTP / codice |
|---|---|
| JSON malformato o Content-Type non JSON | 400 MALFORMED_JSON |
| Tipo, formato o vincolo locale errato | 422 VALIDATION_ERROR |
| Organizzatore inesistente | 422 REFERENCE_NOT_FOUND |
| Ruolo diverso da organizer | 422 INVALID_ORGANIZER |
| Transizione vietata | 422 INVALID_STATUS_TRANSITION |
| Timeout, connessione rifiutata, 5xx o risposta anomala | 503 DEPENDENCY_UNAVAILABLE |
| Evento assente / metodo non previsto | 404 NOT_FOUND / 405 METHOD_NOT_ALLOWED |

Gli errori non lasciano modifiche parziali. GET, lista, DELETE e health non chiamano
user-service. I filtri status/city sono esatti e combinati con AND, con distinzione
tra città vuota e filtro assente. Paginazione 1/20, page_size massimo 100, totale
calcolato prima dello slice e ordine created_at/id crescente.

## Verifiche

Dalla root:

```bash
make test-unit SERVICE=event-service
make test-own-integration
.venv/bin/python -m pytest tests/integration/test_user.py tests/integration/test_event.py -v
make check
```

Risultati del 25 settembre 2026: **431 unit/contract superati**, coverage
**99,59% includendo i rami** (linee 100%, rami 97,96%). Tutte e sette le operazioni
sono validate con il contratto del docente. **12 test di integrazione propri**
passati su tre backend; collaudo user+event **16/16 per backend** senza skipped.

Specifiche: `.kiro/specs/event-service/`.
[Report riproducibile della fase 3](../../docs/phase-3-verification.md).
