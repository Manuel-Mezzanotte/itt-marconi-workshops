# Design — registration-service

Riferimenti: requirements.md e contracts/openapi/registration-service.yaml.
Il servizio conserva solo iscrizioni e consulta utenti/eventi esclusivamente via HTTP.

## Componenti

| Modulo | Responsabilità |
|---|---|
| app/config.py | PORT=5003, URL user/event, backend e DATA_DIR, override validati |
| app/errors.py | ApiError e handler JSON uniformi |
| app/validation.py | UUID, payload create/patch, query, paginazione |
| app/clients.py | ReferenceClients: lettura user/event con timeout e mapping errori |
| app/repositories/ | Protocollo, factory e implementazioni atomiche |
| app/service.py | UUID/timestamp, coordinamento HTTP e repository, stats |
| app/routes.py | Parsing e risposte Flask, nessuna regola di persistenza |
| app/__init__.py | Factory, dipendenze per istanza, health |
| app/__main__.py | Socket locale e Werkzeug senza debug/reloader o reverse DNS |

Gli helper restano nel servizio, senza import da user/event. Stack e dipendenze
rimangono quelli esistenti; solo json/sqlite3 standard library per i file.

## Input e dati

Create: oggetto con soli user_id/event_id obbligatori. Patch: oggetto con solo
status obbligatorio confirmed/cancelled; {} non è un no-op valido in questo schema.
Ogni campo extra è rifiutato, inclusi id, amount e timestamp. Verificare i tipi
prima di enum e confronti. UUID canonici con trattini, normalizzati in minuscolo.

La risorsa ha sette campi: id, user_id, event_id, amount, status, created_at,
updated_at. Id UUID v4 e timestamp ISO UTC a sei cifre di microsecondi con Z.
Il prezzo della risposta event viene copiato, senza ricalcolarlo in seguito.
I riferimenti non vengono ricontrollati per letture o cancellazioni di iscrizioni
esistenti, né si applicano cancellazioni a cascata se user/event sono eliminati.

## Repository e capienza atomica

Protocollo comune:

| Metodo | Risultato |
|---|---|
| reserve(record,capacity) | record creato oppure ApiError 409 |
| get(id) | copia o None |
| list(filters,page,page_size) | (items,total) |
| count_confirmed(event_id) | conteggio delle sole confirmed |
| update_status(id,status,updated_at) | record aggiornato/invariato oppure None |
| delete(id) | bool |

Reserve controlla prima la coppia user/event confirmed, poi il totale confirmed
per l'evento rispetto alla capienza ricevuta, poi inserisce. La verifica di stato
published e l'acquisizione del prezzo sono nel service; HTTP viene completato
prima di acquisire lock o transazione.

- Memory: dict per istanza e RLock; l'intera reserve e ogni modifica sono protette.
  Le letture e i valori restituiti sono copie; un errore non altera lo stato.
- JSON: registrations.json con {"registrations":[...]}; stesse operazioni sotto
  RLock, lettura del file, verifica e scrittura nella stessa sezione critica.
  File temporaneo nella stessa directory e os.replace; errore di scrittura
  preserva il precedente. Un processo scrittore per directory.
- SQLite: registrations.db con tabella a sette colonne, id TEXT PRIMARY KEY,
  user_id/event_id/status/timestamp TEXT, amount REAL, campi NOT NULL.
  Indice UNIQUE(user_id,event_id) WHERE status='confirmed'; indice event_id/status.
  Connessione per operazione, scritture BEGIN IMMEDIATE, commit/rollback e close.
  Reserve usa query di duplicato e COUNT(*) nella stessa transazione dell'INSERT.
  L'indice parziale consente più righe storiche cancelled e una sola confirmed.

Update_status legge il record nella sezione critica: stesso stato restituisce
il record invariato; confirmed→cancelled aggiorna status/updated_at; cancelled→confirmed
solleva 422. Delete rimuove la riga, liberando un posto se era confirmed.

Filtri user/event/status con AND; ordine (created_at,id). Memory/JSON usano una
funzione locale; SQLite usa WHERE parametrizzato e COUNT prima di LIMIT/OFFSET,
evitando il binding di offset enormi quando la pagina è già oltre total.
Campi e operatori SQL sono fissi, mai costruiti da nomi ricevuti dal client.

L'atomicità riguarda le prenotazioni sullo stesso archivio. Memory/JSON hanno un
solo processo; SQLite serializza anche istanze con connessioni distinte.
Capacity, price e status sono una fotografia dell'evento letta via HTTP:
nessuna transazione distribuita protegge una modifica contemporanea dell'evento.
Ridurre la capienza o cancellare l'evento non modifica retroattivamente le iscrizioni.

## Client e service

ReferenceClients riceve URL validati dalla configurazione. requests.get con
timeout=2 e allow_redirects=False. La risposta 200 deve essere un oggetto con id
coerente con quello richiesto. Per event sono inoltre richiesti status valido,
capacity intera 1..10000 e price finito non negativo (bool esclusi).

404 user/event in POST→422 REFERENCE_NOT_FOUND. Solo in stats, 404 event→404 NOT_FOUND.
Timeout/connessione, 5xx, altri status o body anomali→503 DEPENDENCY_UNAVAILABLE.
Non richiedere uno specifico ruolo per iscrivere un utente.

Create: valida payload → GET user → GET event → published → id/amount/timestamp →
repository.reserve(capacity). Nessuna creazione se una chiamata o regola fallisce.
Get/list: repository locale con 404/paginazione. Patch: valida status →
repository.update_status; nessuna dipendenza HTTP. Delete: repository.delete.
Stats: valida event_id obbligatorio → GET event → count_confirmed locale →
available=max(0,capacity-confirmed). Anche draft/cancelled possono avere statistiche.

## HTTP, configurazione e avvio

Route /stats definita come percorso letterale, distinta da /{id}. POST 201 e
Location relativo; letture/PATCH 200; DELETE 204 vuoto; PUT non registrato:
Flask produce 405 anche per id assente e il validator verifica l'operazione
esplicitamente dichiarata nel contratto.

JSON malformato/Content-Type errato→400; JSON valido non oggetto→422.
Il 400 di PATCH deriva dallo standard generale, non è dichiarato dall'OpenAPI:
test diretto senza alterare il contratto. Tutti gli errori sono JSON con details.

Configurazione alla factory: PORT valida 1..65535; backend riconosciuto; URL
HTTP/HTTPS con host, senza credenziali/query/fragment; DATA_DIR come Path.
Avvio macOS/Linux con socket.create_server e make_server(fd=...), adottando
la soluzione già verificata per il blocco DNS della issue #6. Health è locale.

## Verifica

Unit/contract parametrizzati sui backend; marker req e ID nelle docstring.
Repository: CRUD, copie, rollback/persistenza, JSON replace fallito, duplicati
prima di capienza, cancellazione/riiscrizione, filtri, pagine enormi.
Concorrenza: molti aspiranti all'ultimo posto, molti tentativi della stessa coppia;
SQLite anche da istanze distinte, con esattamente un vincitore.

responses per entrambe le dipendenze: successo, 404, timeout, refused, 5xx,
JSON/schema anomalo; timeout e URL verificati. Test dell'importo storico e
rifiuto dei campi client, tutte le coppie di stato e stats anche dopo riduzione capienza.
Contratti su tutte le otto operazioni, incluso PUT 405.

Integrazione propria: tre processi reali, porte libere e directory isolate,
flusso capienza 2, cancellazione e riiscrizione, riferimenti assenti,
arresto separato di user/event, concorrenza HTTP e riavvio dei backend.
Si estendono le fixture esistenti senza importare quelle protette.

Ultimo task: manifest con i tre servizi; unit/coverage>=80%; integrazione propria
e pytest tests/integration -m mandatory -v con memory/json/sqlite. Checksum e
cleanup; README, BUGS e report della fase. Niente tag o collaudo.txt finale.
