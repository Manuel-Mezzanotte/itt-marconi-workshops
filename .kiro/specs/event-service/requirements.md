# Requisiti — event-service

Fonte: Exam/Exam.MD §§4, 5.2, 6; contratto immutabile
`contracts/openapi/event-service.yaml`. Ambito: servizio eventi, porta 5002,
dipendenza HTTP da user-service. Registration e bonus esclusi da questa fase.

## REQ-EVT-01 — Creazione e campi

Come organizzatore voglio creare una conferenza con date, sede, prezzo e capienza.

- WHEN POST /api/v1/events riceve un EventCreate valido, THE event-service SHALL
  restituire 201, Location relativo /api/v1/events/{id} e la risorsa persistita.
- THE event-service SHALL richiedere title (3..120 caratteri), organizer_id UUID,
  venue (max 100), city (max 60), start_date/end_date in YYYY-MM-DD,
  capacity intero 1..10000 e price numerico finito >=0.
- THE event-service SHALL accettare description null o stringa max 2000 e status
  draft/published/cancelled; se omessi SHALL usare description=null e status=draft.
  Lo status esplicito alla creazione è ammesso da EventCreate.
- IF un campo richiesto manca, un tipo è errato, un vincolo è violato o sono
  presenti campi extra/read-only, THEN THE event-service SHALL rispondere
  422 VALIDATION_ERROR senza scrivere dati. Booleani non sono numeri validi.
- THE event-service SHALL generare UUID v4, created_at/updated_at UTC con Z e
  rappresentare gli importi come numeri arrotondati a due decimali.

## REQ-EVT-B01 / REQ-EVT-B02 — Organizzatore

Come utente voglio che gli eventi siano associati a un organizzatore esistente.

- WHEN viene creato un evento, sostituito con PUT o inviato organizer_id in PATCH,
  THE event-service SHALL interrogare GET /api/v1/users/{organizer_id}.
- IF user-service restituisce 404, THEN THE event-service SHALL rispondere
  422 REFERENCE_NOT_FOUND senza modifiche.
- IF l'utente esiste ma role non è organizer, THEN THE event-service SHALL
  rispondere 422 INVALID_ORGANIZER senza modifiche.

## REQ-EVT-B03 — Date

Come partecipante voglio un intervallo di date valido.

- THE event-service SHALL accettare solo date reali nel formato YYYY-MM-DD.
- IF end_date precede start_date, THEN THE event-service SHALL rispondere
  422 VALIDATION_ERROR senza modifiche; per PATCH SHALL valutare la risorsa
  risultante dall'unione dei campi ricevuti con quelli persistiti.

## REQ-EVT-B04 — Ciclo di vita

Come organizzatore voglio pubblicare o cancellare una conferenza.

- WHEN lo stato cambia, THE event-service SHALL consentire soltanto draft→published,
  draft→cancelled e published→cancelled, sia con PUT sia con PATCH.
- IF il cambio non è consentito, THEN THE event-service SHALL rispondere
  422 INVALID_STATUS_TRANSITION senza modificare la risorsa.
- WHEN viene inviato lo stato già presente, THE event-service SHALL trattarlo
  come assenza di cambio di stato.

## REQ-EVT-02 / REQ-EVT-B06 — Letture, filtri e paginazione

Come client voglio recuperare singoli eventi e liste filtrate.

- WHEN GET /api/v1/events/{id} identifica un evento, THE event-service SHALL
  restituire 200 e la risorsa; IF assente SHALL restituire 404 NOT_FOUND.
- WHEN GET /api/v1/events riceve page/page_size validi, THE event-service SHALL
  restituire items, page, page_size e total con default 1/20 e page_size massimo 100.
- THE event-service SHALL ordinare per created_at e id crescenti, applicare filtri
  esatti status/city combinati con AND e calcolare total prima della paginazione.
  City vuota è distinta dal filtro assente.
- IF page/page_size non sono interi positivi o status non appartiene all'enum,
  THEN THE event-service SHALL restituire 422 VALIDATION_ERROR.
- WHEN page supera il totale, THE event-service SHALL restituire items vuoto,
  anche per numeri di pagina molto grandi.

## REQ-EVT-03 — Modifica e cancellazione

Come organizzatore voglio correggere o rimuovere i miei eventi.

- WHEN PUT /api/v1/events/{id} riceve EventCreate valido, THE event-service SHALL
  sostituire i campi modificabili, preservare id/created_at e aggiornare updated_at.
  Description e status omessi SHALL tornare ai default null/draft: se questo
  implica una transizione vietata, SHALL rispondere 422 INVALID_STATUS_TRANSITION.
- WHEN PATCH riceve EventUpdate valido, THE event-service SHALL modificare solo
  i campi inviati e updated_at; WHEN il body è {}, SHALL restituire l'intera
  risorsa invariata, senza interrogare user-service.
- WHEN DELETE trova l'evento, THE event-service SHALL eliminarlo e restituire 204
  senza body. IF l'id di GET/PUT/PATCH/DELETE è assente, SHALL rispondere 404 NOT_FOUND.
- IF una validazione o chiamata HTTP fallisce, THE event-service SHALL preservare
  integralmente i dati. Gli aggiornamenti SHALL validare lo stato corrente
  atomicamente con la scrittura, evitando transizioni fondate su letture obsolete.

## REQ-EVT-B05 — Dipendenza HTTP

Come client voglio errori prevedibili quando user-service è indisponibile.

- THE event-service SHALL leggere USER_SERVICE_URL dall'ambiente, default
  http://localhost:5001, e applicare timeout HTTP di 2 secondi.
- IF la dipendenza va in timeout, rifiuta la connessione, restituisce 5xx,
  una risposta inattesa o un body illeggibile, THEN THE event-service SHALL
  restituire 503 DEPENDENCY_UNAVAILABLE senza scrivere dati.

## REQ-EVT-04 — Errori e health

Come client voglio interfacce uniformi.

- THE event-service SHALL usare sempre JSON con campi snake_case e l'errore
  {"error":{"code":"UPPER_SNAKE","message":"...","details":{}}}.
- IF un body è JSON malformato o ha Content-Type non JSON, THEN THE event-service
  SHALL rispondere 400 MALFORMED_JSON. JSON valido non oggetto SHALL produrre 422.
- IF path o metodo non sono supportati, THEN THE event-service SHALL produrre
  rispettivamente 404 NOT_FOUND o 405 METHOD_NOT_ALLOWED.
- WHEN GET /health è chiamato, THE event-service SHALL restituire
  200 {"status":"ok","service":"event-service"} senza interrogare dipendenze.

## REQ-EVT-05 — Configurazione e persistenza

Come valutatore voglio eseguire il servizio in ambienti isolati.

- THE event-service SHALL leggere PORT (default 5002, intero 1..65535),
  STORAGE_BACKEND (memory/json/sqlite) e DATA_DIR (default ./data) alla creazione
  dell'app, con istanze indipendenti.
- THE event-service SHALL conservare i dati JSON/SQLite ai riavvii, isolare
  memory per istanza, restituire copie dei record e lasciare invariata la
  business logic al cambio backend. Nessun DBMS esterno o import di altri servizi.
- THE event-service SHALL avviarsi senza debugger/reloader, anche con FLASK_DEBUG=1,
  e senza dipendere dalla risoluzione DNS inversa dell'indirizzo locale.

## REQ-EVT-06 — Verificabilità

Come valutatore voglio verificare contratto, regole e interazione reale.

- THE test suite SHALL coprire i tre repository, mock HTTP con responses,
  almeno una verifica assert_matches_contract per ogni operazione API e
  coverage di app >=80%, misurando anche i rami.
- THE integration tests SHALL avviare user ed event reali su porte libere con
  dati temporanei e verificare successo, riferimento inesistente 422 e
  dipendenza spenta 503, terminando sempre i processi.
- THE delivery SHALL abilitare user/event nel manifest e superare IT-U01..IT-U08
  e IT-E01..IT-E08 con memory, JSON e SQLite, senza modificare i file protetti.
