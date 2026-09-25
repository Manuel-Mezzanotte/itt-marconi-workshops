# registration-service

Iscrizioni con verifica HTTP di utenti ed eventi, capienza atomica e statistiche.
T-01..T-07 completati; servizio dichiarato nel manifest.

## Avvio

Avviare prima user-service ed event-service. Dalla root, dopo make setup:

```bash
cd services/registration-service
PORT=5003 STORAGE_BACKEND=sqlite DATA_DIR=./data USER_SERVICE_URL=http://localhost:5001 EVENT_SERVICE_URL=http://localhost:5002 ../../.venv/bin/python -m app
```

| Variabile | Default | Significato |
|---|---|---|
| PORT | 5003 | Intero 1..65535 |
| USER_SERVICE_URL | http://localhost:5001 | Base URL del servizio utenti |
| EVENT_SERVICE_URL | http://localhost:5002 | Base URL del servizio eventi |
| STORAGE_BACKEND | memory | memory, json o sqlite |
| DATA_DIR | ./data | Directory relativa al cwd |

Server locale macOS/Linux su 127.0.0.1, senza debugger/reloader anche con
FLASK_DEBUG=1, senza risoluzione DNS inversa durante il bind.

## API

| Metodo | Percorso | Esito |
|---|---|---|
| GET | /health | 200, indipendente dalle dipendenze |
| POST | /api/v1/registrations | 201 con Location e iscrizione |
| GET | /api/v1/registrations | Lista filtrata e paginata |
| GET | /api/v1/registrations/{id} | Risorsa oppure 404 |
| PATCH | /api/v1/registrations/{id} | Solo status |
| DELETE | /api/v1/registrations/{id} | 204 senza body oppure 404 |
| PUT | /api/v1/registrations/{id} | Sempre 405 |
| GET | /api/v1/registrations/stats?event_id=UUID | Capienza e conteggi oppure 404/422/503 |

POST accetta esclusivamente:

```json
{"user_id":"UUID-UTENTE","event_id":"UUID-EVENTO"}
```

Sostituire i segnaposto con UUID reali. Il servizio verifica che utente ed evento
esistano, che l'evento sia published, che non vi sia già una confirmed per la
coppia e che rimangano posti. L'importo viene copiato da event.price; cambi di
prezzo successivi non modificano le iscrizioni esistenti. Qualsiasi ruolo utente
può iscriversi. Id, amount, status e timestamp non sono accettati nel POST.

PATCH richiede `{"status":"cancelled"}` per annullare una confirmed. La transizione
cancelled→confirmed è vietata. Reinviare lo stato corrente restituisce la risorsa
invariata, timestamp incluso; {} è invece invalido perché lo schema richiede status.
Per reiscriversi dopo una cancellazione si invia un nuovo POST, che genera un nuovo id.
Anche DELETE di una confirmed libera il posto; eliminare una cancelled non altera
il numero dei posti occupati.

Lista: page=1/page_size=20, massimo 100, filtri user_id/event_id/status combinati
con AND, UUID normalizzati in minuscolo, ordine created_at/id crescente e total
calcolato prima della paginazione. Pagina oltre il totale restituisce items vuoto.

Stats legge la capienza corrente dall'evento e conta solo confirmed:
available=max(0,capacity-confirmed). Se la capienza viene ridotta sotto il numero
degli iscritti, quelli esistenti rimangono e available è zero. Sono consultabili
anche eventi draft/cancelled. Event_id mancante o invalido produce 422.

## Errori e dipendenze

Formato uniforme: `{"error":{"code":"...","message":"...","details":{}}}`.

| Caso | HTTP / codice |
|---|---|
| JSON malformato o Content-Type errato | 400 MALFORMED_JSON |
| Campi, tipi o UUID invalidi | 422 VALIDATION_ERROR |
| Riferimento mancante in POST | 422 REFERENCE_NOT_FOUND |
| Evento non pubblicato | 422 EVENT_NOT_OPEN |
| Coppia già confirmed | 409 ALREADY_REGISTERED |
| Capienza esaurita | 409 EVENT_FULL |
| Riattivazione vietata | 422 INVALID_STATUS_TRANSITION |
| Iscrizione assente / evento assente in stats | 404 NOT_FOUND |
| Timeout, connessione rifiutata, 5xx o dati inattesi | 503 DEPENDENCY_UNAVAILABLE |

Entrambi i client HTTP usano timeout=2 s, URL di configurazione e nessun redirect.
GET singolo/lista, PATCH, DELETE e health non interrogano dipendenze. Stats chiama
solo event-service. Un errore non lascia scritture parziali.

## Persistenza e concorrenza

Memory usa un dizionario per istanza; JSON salva registrations.json; SQLite salva
registrations.db. Nessun import o accesso ai dati degli altri servizi.
JSON/SQLite sopravvivono ai riavvii, memory riparte vuoto.

Duplicati, conteggio confirmed e inserimento condividono la stessa sezione
critica/transazione. Memory e JSON usano RLock; JSON richiede un solo processo
scrittore per directory e scrive con file temporaneo/os.replace. SQLite usa
BEGIN IMMEDIATE e un indice univoco parziale sulle coppie confirmed.
ALREADY_REGISTERED ha priorità su EVENT_FULL.

La capienza è quella della risposta HTTP ricevuta: non c'è una transazione
distribuita con event-service. Una modifica concorrente dell'evento non è
serializzata con le iscrizioni; prezzo e riferimenti già salvati rimangono storici.

## Verifiche

Dalla root:

```bash
make test-unit SERVICE=registration-service
make test-own-integration
.venv/bin/python -m pytest tests/integration -m mandatory -v
make check
```

25 settembre 2026: **377 unit/contract passati**, coverage **99,79% con rami**
(linee 100%, rami 98,89%). Otto operazioni del contratto verificate, incluso PUT 405.
**21 integrazioni proprie registration**, più 12 event, passate sui tre backend.
Il collaudo mandatory passa **27/27 per backend**, incluso il percorso IT-J01;
dieci test bonus esclusi, nessun mandatory saltato.

Specifiche: `.kiro/specs/registration-service/`.
[Report della fase 4](../../docs/phase-4-verification.md).
