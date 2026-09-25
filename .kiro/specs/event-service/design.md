# Design — event-service

Riferimenti: requirements.md e contratto `contracts/openapi/event-service.yaml`.
Il servizio mantiene dati propri e comunica con user-service soltanto via HTTP.

## Componenti

| Modulo | Responsabilità |
|---|---|
| app/config.py | PORT=5002, USER_SERVICE_URL=http://localhost:5001, STORAGE_BACKEND=memory, DATA_DIR=./data; override per test |
| app/errors.py | ApiError(status, code, message, details) e handler JSON uniformi |
| app/validation.py | EventCreate/EventUpdate, UUID, date reali, prezzi, query e transizioni |
| app/clients.py | UserClient.require_organizer, requests.get, timeout 2 s |
| app/repositories/ | Interfaccia EventRepository, implementazioni e factory |
| app/service.py | EventService: regole, UUID/timestamp, coordinamento HTTP/storage |
| app/routes.py | Parsing HTTP e serializzazione; blueprint con service iniettato |
| app/__init__.py | create_app con dipendenze per istanza, health e handler |
| app/__main__.py | Socket locale su PORT passato a Werkzeug, senza debug/reloader |

Non si importano moduli di user-service. Gli helper brevi rimangono locali,
come previsto dallo steering. Nessuna dipendenza nuova.

## Input, stato e rappresentazione

Validazione esplicita: oggetto JSON, campi ammessi, richiesti soltanto in
EventCreate (anche PUT). Controllo del tipo prima di confronti/enum; bool non è
capacity o price. Title 3..120; venue/city possono essere vuote perché lo schema
impone solo il massimo. Description può essere null; gli altri campi non possono.

UUID di riferimento nel formato canonico con trattini, normalizzato in minuscolo.
Date tramite formato esatto YYYY-MM-DD e date.fromisoformat; niente date inesistenti.
Date finali confrontate dopo il merge del PATCH. Price finito e non negativo:
Decimal da stringa, arrotondamento ROUND_HALF_UP a centesimi, restituzione numerica
JSON. Nessuna conversione di stringhe o booleani in numeri.

POST applica description=null e status=draft solo quando assenti. PUT applica
gli stessi default: omettere status su un evento published implica il tentativo
published→draft e quindi 422. PATCH preserva tutti i campi assenti; {} è un no-op
senza HTTP o aggiornamento dei timestamp.

Lo stesso stato è accettato senza transizione. I cambi ammessi sono
draft→published, draft→cancelled e published→cancelled. Anche dopo cancellazione
si possono modificare campi non di stato: la traccia non vieta questa operazione.
Non sono introdotti vincoli su iscrizioni, eventi passati o cancellazione fisica.

Gli id generati sono UUID v4; timestamp ISO UTC con sei cifre di microsecondi e Z.
Id e created_at restano invariati negli aggiornamenti.

## Repository e atomicità

Interfaccia comune: create(record), get(id), list(filters,page,page_size),
update(id,transform), delete(id). Get/update restituiscono None se assente;
delete restituisce bool. List restituisce (items,total).

La funzione transform riceve una copia dello stato corrente e restituisce il
record nuovo. Update esegue lettura, transform e scrittura nella stessa sezione
critica/transazione; le eccezioni annullano la modifica. Questo evita aggiornamenti
persi e transizioni validate contro stati superati da un'altra richiesta.
Le chiamate HTTP sono completate prima di entrare nella transazione.

- Memory: dizionario per istanza, RLock; letture e scritture restituiscono copie.
- JSON: DATA_DIR/events.json, {"events":[...]}, RLock per istanza, file temporaneo
  nella stessa directory e os.replace. Nessun dato viene perso se il replace
  fallisce. Un processo scrittore per directory; file corrotto non viene ignorato
  o sovrascritto silenziosamente.
- SQLite: DATA_DIR/events.db, tabella events(id TEXT PRIMARY KEY, document TEXT
  NOT NULL). Il documento conserva i tipi JSON della risorsa. Ogni operazione
  apre/chiude una connessione; scritture con BEGIN IMMEDIATE, commit/rollback.
  Update legge e trasforma il documento dentro la transazione.

Filtri e paginazione condividono una funzione pura locale: status e city esatti,
AND, ordine (created_at,id), totale prima dello slice. SQLite carica i documenti
per usare lo stesso comportamento degli altri backend: scelta adeguata al piccolo
dataset d'esame, con scansione lineare deliberata. Nessun offset enorme passato
come intero a SQLite.

## Client HTTP e service

UserClient costruisce URL dal solo valore di configurazione, togliendo lo slash
finale. GET con timeout=2, redirect disabilitati. 404→422 REFERENCE_NOT_FOUND;
connessione/timeout, status inatteso o JSON non interpretabile→503 DEPENDENCY_UNAVAILABLE.
Un oggetto con role diverso da organizer produce 422 INVALID_ORGANIZER.

POST: validazione locale e date → verifica organizer → UUID/timestamp → create.
GET: get o 404. List: validazione query → repository → busta paginata.
PUT: verifica esistenza → valida payload → verifica organizer → update atomico,
che controlla la transizione sullo stato corrente e preserva id/created_at.
PATCH: verifica esistenza → valida campi → per {} restituisce il record → verifica
organizer solo se presente nel payload → update atomico con merge, date/transizione
e timestamp. La mancata esistenza al momento dell'update rimane un 404.
DELETE: delete o 404; nessuna cascata o chiamata alla dipendenza.

## HTTP, configurazione e avvio

Le route seguono il contratto: POST 201 con Location relativo; GET/PUT/PATCH 200;
DELETE 204 vuoto. Errori con details sempre oggetto. Body malformato e Content-Type
errato→400 MALFORMED_JSON; JSON non oggetto→422 VALIDATION_ERROR.
Il 400 di PUT/PATCH deriva dagli standard del §4 ma non è elencato nel loro
OpenAPI: test diretto, senza forzare il validator su risposte non dichiarate.

Configurazione letta alla factory, non all'import. PORT valido 1..65535;
backend riconosciuto; URL HTTP/HTTPS con host e senza query/fragment o credenziali.
Override dei test attraversano la stessa validazione. DATA_DIR è un Path.
Health non richiede una chiamata HTTP e restituisce il nome event-service.
L'avvio usa socket.create_server e make_server(fd=...) per evitare il blocco
DNS già diagnosticato nella issue #6. Target operativo macOS/Linux.

## Strategia di verifica

Test con marker req o ID in docstring. Repository sui tre backend: CRUD, copie,
filtri, persistenza, rollback di transform e scritture concorrenti. Validazione:
tipi/limiti, date, NaN/infinito, campi riservati, tutte le coppie di stato.
HTTP mockato con responses: organizer, 404, ruolo, timeout, connessione, 5xx,
risposta anomala e rispetto del timeout configurato.

Contract test tramite assert_matches_contract del docente, almeno uno per
ciascuna delle sette operazioni. Test di no-op, errori senza mutazioni,
PUT con default e PATCH con date parziali e cambi di organizzatore.

Integrazione propria sotto tests/service_integration: user ed event come processi
reali su porte libere, DATA_DIR temporanea, startup bounded e teardown in finally.
Copertura di successo, riferimento mancante, ruolo errato, dipendenza spenta e
persistenza ai riavvii. Nessun import delle fixture protette.

Verifica finale: make test-unit SERVICE=event-service, coverage >=80%;
integrazione propria sui tre storage; test_user.py + test_event.py del docente sui
tre backend. Manifest con user/event, checksum e processi verificati, documentazione
aggiornata. Registration e collaudo completo restano alle fasi successive.
