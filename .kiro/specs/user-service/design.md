# Design Document

## Overview

User-service gestisce l'anagrafica TechConf. Espone le API del
[contratto user-service](../../../contracts/openapi/user-service.yaml) e non
chiama altri servizi. L'implementazione usa Flask, Python 3.12 e i tre backend
richiesti. Nessuna dipendenza aggiuntiva.

Il rifiuto di id e timestamp ricevuti dal client è tracciato nella
[issue #1](https://github.com/Manuel-Mezzanotte/itt-marconi-workshops/issues/1).

## Architecture

Flusso: route HTTP → validazione → UserService → UserRepository → risposta HTTP.

Le route leggono richieste e producono risposte. Il service gestisce default,
normalizzazione, identificativi e timestamp. I repository conservano i dati e
rendono atomico il controllo di unicità insieme alla scrittura. Le eccezioni
locali sono convertite in HTTP solo negli handler Flask.

Ogni chiamata a `create_app` costruisce configurazione, repository e service
propri. Nessun singleton di dati o blueprint con stato condiviso tra app.

## Components and Interfaces

| Modulo | Responsabilità |
|---|---|
| `app/config.py` | `load_config(overrides=None)`: legge ambiente all'avvio della factory e applica gli override dei test |
| `app/errors.py` | Eccezioni ValidationError, UserNotFound, EmailAlreadyExists e handler HTTP |
| `app/validation.py` | Validazione create/update e query di paginazione/filtri |
| `app/service.py` | UserService e generazione UUID/timestamp |
| `app/repositories/` | Interfaccia UserRepository, factory e tre implementazioni |
| `app/routes.py` | Blueprint costruito per ogni app, con UserService iniettato |
| `app/__init__.py` | `create_app(config=None)`, collegamento dei componenti, health e handler |
| `app/__main__.py` | Avvio senza debug/reloader, usando PORT |

### Configurazione

`load_config` è l'unico punto che legge `os.environ`; non memorizza valori
all'import del modulo. Default: PORT=5001, STORAGE_BACKEND=memory, DATA_DIR=./data.
PORT deve essere un intero tra 1 e 65535; un backend sconosciuto è un errore di
configurazione. DATA_DIR diventa un Path; i backend su file creano la directory.

L'entrypoint ascolta su `127.0.0.1` e sulla porta configurata. Nei test si passa
un override alla factory senza ricaricare moduli. Health restituisce esattamente
`{"status":"ok","service":"user-service"}` e non interroga lo storage.

Per evitare che la risoluzione DNS inversa blocchi l'avvio locale (issue #6),
l'entrypoint apre il socket TCP con `socket.create_server` e passa il descrittore
a `werkzeug.serving.make_server`. L'applicazione rimane Flask; il server usa
thread per le richieste, senza debugger o reloader. Entrambi i socket sono chiusi
tramite context manager. Questa modalità di avvio è destinata a macOS/Linux,
come il manifest, e non è un server di produzione.

### Errori e parsing

Le eccezioni di dominio non costruiscono response Flask. Gli handler producono
sempre `{"error":{"code":"CODICE","message":"testo leggibile","details":{}}}`.

Le route di scrittura usano `request.get_json(silent=False)`: BadRequest per JSON
malformato e UnsupportedMediaType sono convertiti in 400 MALFORMED_JSON. Un JSON
valido che decodifica a null, array, stringa, numero o booleano arriva invece alla
validazione e produce 422 VALIDATION_ERROR. Non usare `silent=True`, perché
renderebbe indistinguibili null e un errore di decodifica.

### Validazione

`validate_user_create(data)` richiede first_name, last_name ed email ed è usata
anche dal PUT. `validate_user_update(data)` valida soltanto i campi presenti e
accetta `{}`. Entrambe restituiscono un nuovo dict senza modificare l'input.

Campi ammessi: first_name, last_name, email, company, role. Altri campi, inclusi
id/created_at/updated_at, causano 422 prima di qualsiasi scrittura. I tre campi
obbligatori devono essere stringhe non nulle; nomi tra 1 e 50 caratteri, company
null o stringa fino a 100 caratteri, role esattamente attendee/speaker/organizer.
Non convertire tipi invalidi in stringhe e non eliminare silenziosamente campi.

Per l'email si usa una regex minimale con `re.fullmatch`: parte locale non vuota,
un solo @, dominio non vuoto con almeno un punto, nessuno spazio. Pattern:
`[^@\s]+@[^@\s]+\.[^@\s]+`. Il controllo è completo sulla stringa, incluse
le eventuali newline finali; non è un parser completo RFC né fa lookup DNS.

La query valida page e page_size come interi positivi, default 1 e 20, massimo
page_size=100. Role deve appartenere all'enum. Email è un filtro di uguaglianza
normalizzato in minuscolo; i due filtri si combinano con AND. Filtri assenti ed
email vuota sono distinti: la stringa vuota cerca una corrispondenza vuota.

### Repository

Interfaccia comune, con documentazione dei valori di ritorno:

| Metodo | Risultato |
|---|---|
| `create(user)` | record creato; EmailAlreadyExists in caso di conflitto |
| `get(user_id)` | record o None |
| `get_by_email(email)` | record o None, confronto normalizzato |
| `list(filters, page, page_size)` | `(items, total)` dopo i filtri |
| `update(user_id, user)` | record aggiornato o None; EmailAlreadyExists senza mutazioni |
| `delete(user_id)` | True se rimosso, False se inesistente |

Il service passa record completi a create/update. I repository restituiscono
copie, non riferimenti modificabili allo stato interno. L'unicità dell'email è
verificata nella stessa sezione critica/transazione della scrittura; una query
preventiva nel service non è sufficiente. L'update esclude il proprio id dal
controllo dei duplicati.

L'ordinamento della lista è `(created_at, id)` crescente, uguale sui tre backend.
`total` conta i record filtrati prima della paginazione. Una pagina oltre la fine
restituisce items vuoto; un offset enorme va confrontato con total prima di
passarlo a SQLite, per evitare overflow senza introdurre limiti non previsti.

- **MemoryRepository**: dict per istanza e threading.RLock. Letture, verifica
  unicità e scritture sono protette. Nessuna variabile globale o file.
- **JsonRepository**: file DATA_DIR/users.json con struttura `{"users":[...]}`.
  RLock per istanza; lettura, verifica e scrittura nella stessa sezione critica.
  La scrittura passa da un file temporaneo nella stessa directory a os.replace.
  Un errore prima del replace non deve alterare il file precedente. L'uso previsto
  è un solo processo scrittore per directory dati; non si aggiungono lock distribuiti.
- **SqliteRepository**: file DATA_DIR/users.db. Tabella users con gli otto campi
  della risorsa, id TEXT PRIMARY KEY, email TEXT NOT NULL UNIQUE COLLATE NOCASE;
  company nullable. Connessione aperta e chiusa per ogni operazione, senza
  condividerla fra thread. `isolation_level=None` disabilita le transazioni
  implicite: le scritture usano BEGIN IMMEDIATE e poi COMMIT o ROLLBACK, chiudendo
  sempre la connessione. Il vincolo di unicità viene tradotto in EmailAlreadyExists.
  Le righe sqlite3.Row sono convertite in dict.

`get_repository(backend, data_dir)` seleziona l'implementazione. JSON e SQLite
ritrovano i dati dopo la costruzione di una nuova istanza nella stessa directory;
una nuova istanza memory è vuota. Non è prevista migrazione dei dati tra backend.

### UserService e route

| Metodo del service | Operazione |
|---|---|
| `create_user(data)` | lowercase email, UUID v4, timestamp UTC identici, default role/company, repository.create |
| `get_user(id)` | repository.get; UserNotFound se assente |
| `list_users(role, email, page, page_size)` | filtri normalizzati e busta paginata |
| `replace_user(id, data)` | mantiene id/created_at, sostituisce i campi, ripristina i default omessi, nuovo updated_at |
| `update_user(id, data)` | se esiste e data è vuoto ritorna il record invariato; altrimenti merge dei soli campi presenti e nuovo updated_at |
| `delete_user(id)` | repository.delete; UserNotFound se False |

I timestamp usano `datetime.now(UTC)` e ISO 8601 con microsecondi e suffisso Z.
I valori forniti dal client per id e timestamp non entrano mai nel service.
EmailAlreadyExists, anche se generata dal vincolo SQLite o dal lock del repository,
arriva all'handler 409. Le operazioni rifiutate lasciano invariati i dati.

Le route seguono i sette metodi del contratto, incluso health. POST restituisce
201 e Location relativo `/api/v1/users/{id}`; DELETE 204 con corpo vuoto.
GET/PUT/PATCH restituiscono 200. Le route non importano un backend concreto.

## Data Models

La risorsa segue lo schema User del contratto: id, first_name, last_name, email,
company, role, created_at, updated_at. Company è sempre restituita, anche se null;
non si aggiungono altri campi. UserCreate è usato da POST e PUT, UserUpdate da PATCH.

La busta lista contiene items, page, page_size, total. Campi input e limiti sono
quelli del contratto; i repository salvano già l'email normalizzata dal service.

## Correctness Properties

Mappa degli indici usati dal validatore Kiro verso gli ID stabili:

| Indice | ID |
|---|---|
| 1 | REQ-USR-01 |
| 2 | REQ-USR-B01 |
| 3 | REQ-USR-B02 |
| 4 | REQ-USR-02 |
| 5 | REQ-USR-03 |
| 6 | REQ-USR-B03 |
| 7 | REQ-USR-04 |
| 8 | REQ-USR-05 |
| 9 | REQ-USR-06 |
| 10 | REQ-USR-07 |
| 11 | REQ-USR-08 |
| 12 | REQ-USR-09 |
| 13 | REQ-USR-10 |
| 14 | REQ-USR-11 |
| 15 | REQ-USR-12 |

### Property 1: Email uniqueness
For any create or update, two stored users cannot have the same normalised email.
**Validates: Requirements 2.1, 2.2, 2.3, 2.4**

### Property 2: Email normalisation
For any supplied email, successful writes store and return its lowercase form.
**Validates: Requirements 3.1, 3.2, 3.3**

### Property 3: Read-only fields rejection
For any POST/PUT/PATCH containing id or timestamps, the result is 422 and storage is unchanged.
**Validates: Requirements 1.7, 13.4**

### Property 4: PUT substitution
For any successful PUT, omitted optional fields regain their defaults and id/created_at remain unchanged.
**Validates: Requirements 7.2, 7.3, 7.4**

### Property 5: Empty PATCH
For any existing user, PATCH with an empty object returns the unchanged resource, including updated_at.
**Validates: Requirements 14.8, 8.2**

### Property 6: Pagination
For any filter and valid page, total counts matching records and items contains at most page_size records in stable order.
**Validates: Requirements 5.1, 5.2, 5.3, 5.4, 6.1, 6.3, 6.4**

### Property 7: Backend substitutability
For any valid CRUD sequence, the three backends have equivalent results, excluding server-generated ids and timestamps when comparing independent runs.
**Validates: Requirements 12.2, 12.3, 12.4, 12.5, 12.7, 12.8**

## Error Handling

| Caso | HTTP | Codice |
|---|---:|---|
| JSON malformato o Content-Type non JSON | 400 | MALFORMED_JSON |
| JSON valido ma non oggetto, campo extra/read-only, tipo o vincolo invalido | 422 | VALIDATION_ERROR |
| Email di un altro utente | 409 | EMAIL_ALREADY_EXISTS |
| Utente o percorso inesistente | 404 | NOT_FOUND |
| Metodo non previsto | 405 | METHOD_NOT_ALLOWED |
| Errore interno inatteso | 500 | INTERNAL_ERROR |

Gli errori 404/405 sono registrati a livello app, non solo nel blueprint.
Anche il 500 mantiene l'involucro JSON uniforme, con messaggio generico e details
vuoto: il dettaglio dell'eccezione rimane nei log del server (issue #8).
Poiché 500 non è dichiarato dall'OpenAPI, la regressione lo verifica direttamente.
La regola generale 400 per JSON malformato si applica anche a PUT/PATCH secondo
il §4: il loro contratto elenca 404/409/422 e non dichiara 400. I test dei casi
400 PUT/PATCH verificano direttamente status e corpo, senza modificare il contratto.

## Testing Strategy

Pytest e Flask test client, senza dipendenze HTTP da simulare. Fixture per app e
repository parametrizzate sui tre backend, con tmp_path per i file. Ogni test
cita gli ID dei requisiti con marker, nome o docstring.

File previsti: test_config.py, test_validation.py, test_repositories.py,
test_service.py, test_routes.py e test_contract.py, con fixture in conftest.py.
I test vengono aggiunti nei task che implementano il comportamento corrispondente.

Casi necessari: CRUD, input ai limiti e tipi errati, JSON null/array/malformato,
read-only su POST/PUT/PATCH senza mutazioni (issue #1), unicità anche concorrente,
update della propria email, default PUT, PATCH vuoto, paginazione/filtri combinati,
404/405, isolamento memory, copia dei record e persistenza JSON/SQLite dopo riapertura.

Almeno un test per ogni operazione API usa assert_matches_contract del template
con il dict status_code/headers/json ottenuto dalla risposta Flask. I test del
contratto coprono successi e gli errori dichiarati, compreso il DELETE senza corpo.

`make test-unit SERVICE=user-service` esegue dalla directory del servizio pytest
con copertura di app, linee e rami, e soglia minima 80%. Al termine si abilita solo
user in services.yaml e si esegue `.venv/bin/python -m pytest tests/integration/test_user.py -v`.
Il collaudo va ripetuto con STORAGE_BACKEND=memory/json/sqlite e dati temporanei
separati. Il materiale del docente e i relativi checksum restano immutati.
