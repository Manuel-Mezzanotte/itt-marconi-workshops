# Requisiti — registration-service

Fonte: Exam/Exam.MD §§4, 5.3, 6 e contratto immutabile
`contracts/openapi/registration-service.yaml`. Porta 5003; dipendenze HTTP:
user-service ed event-service. Nessun feedback o notifica in questa fase.

## REQ-REG-01 — Creazione

Come partecipante voglio iscrivermi a una conferenza pubblicata.

- WHEN POST /api/v1/registrations riceve RegistrationCreate valido e tutte le
  regole di riferimento/capienza sono rispettate, THE registration-service SHALL
  creare una risorsa e rispondere 201 con Location relativo e body Registration.
- THE registration-service SHALL accettare soltanto user_id ed event_id, entrambi
  obbligatori e UUID canonici; SHALL normalizzare gli UUID in minuscolo.
- IF il body non è un oggetto, mancano campi, il formato è invalido o sono presenti
  campi aggiuntivi, THEN THE registration-service SHALL rispondere 422
  VALIDATION_ERROR senza scrivere dati. Amount, status, id e timestamp non sono
  accettati dal client in POST.
- THE registration-service SHALL generare id UUID v4, status=confirmed,
  created_at e updated_at identici in formato ISO 8601 UTC con Z.

## REQ-REG-B01 / REQ-REG-B02 — Riferimenti

Come partecipante voglio che l'iscrizione punti a risorse esistenti.

- WHEN viene creata un'iscrizione, THE registration-service SHALL verificare
  user_id con GET /api/v1/users/{id} ed event_id con GET /api/v1/events/{id}.
- IF una di queste chiamate restituisce 404, THEN THE registration-service SHALL
  rispondere 422 REFERENCE_NOT_FOUND senza creazione.
- THE registration-service SHALL consentire l'iscrizione di un utente esistente
  indipendentemente dal suo ruolo; il ruolo organizer è un vincolo degli eventi.

## REQ-REG-B03 / REQ-REG-B06 — Stato dell'evento e importo

Come partecipante voglio iscrivermi solo a eventi aperti, al loro prezzo corrente.

- IF event.status non è published, THEN THE registration-service SHALL rispondere
  422 EVENT_NOT_OPEN senza creazione.
- WHEN l'iscrizione viene creata, THE registration-service SHALL copiare
  event.price nel campo amount, senza accettare un importo dal client.
- WHEN il prezzo dell'evento cambia successivamente, THE registration-service
  SHALL conservare l'importo dell'iscrizione già creata.

## REQ-REG-B04 — Iscrizioni duplicate

Come organizzatore voglio evitare doppie iscrizioni attive.

- IF esiste un'iscrizione confirmed dello stesso user_id allo stesso event_id,
  THEN THE registration-service SHALL rispondere 409 ALREADY_REGISTERED.
- WHEN esistono solo iscrizioni cancelled per la coppia, THE registration-service
  SHALL consentire una nuova iscrizione con nuovo id, se rimane capienza.
- THE registration-service SHALL verificare duplicati atomicamente con
  l'inserimento e dare priorità ad ALREADY_REGISTERED rispetto a EVENT_FULL.

## REQ-REG-B05 — Capienza

Come organizzatore voglio impedire prenotazioni oltre i posti disponibili.

- IF il numero di iscrizioni confirmed dell'evento è >= event.capacity,
  THEN THE registration-service SHALL rispondere 409 EVENT_FULL senza scritture.
- THE registration-service SHALL contare solo confirmed e rendere atomici
  conteggio, verifica dei duplicati e inserimento, anche con richieste concorrenti.
- WHEN un'iscrizione confirmed è cancellata o eliminata, THE registration-service
  SHALL rendere il posto disponibile per una nuova iscrizione.

## REQ-REG-02 — Letture e paginazione

Come client voglio consultare iscrizioni e filtrarle.

- WHEN GET /api/v1/registrations/{id} trova una risorsa, THE registration-service
  SHALL restituire 200 e Registration; IF assente SHALL rispondere 404 NOT_FOUND.
- WHEN GET /api/v1/registrations è chiamato, THE registration-service SHALL
  restituire items/page/page_size/total, ordinati per created_at e id crescenti.
- THE registration-service SHALL usare page=1/page_size=20 di default,
  accettare solo interi positivi e page_size<=100; IF invalidi SHALL rispondere 422.
- THE registration-service SHALL filtrare per user_id, event_id e status con AND,
  validare UUID/enum e calcolare total prima della paginazione. Pagina oltre la
  fine, anche molto grande, SHALL restituire items vuoto.
- THE registration-service SHALL leggere dati locali senza interrogare dipendenze
  per GET singolo/lista.

## REQ-REG-B07 / REQ-REG-03 — Modifica e cancellazione

Come partecipante voglio annullare un'iscrizione.

- WHEN PATCH riceve RegistrationPatch, THE registration-service SHALL richiedere
  soltanto status, con valore confirmed o cancelled; {} è invalido.
- WHEN una risorsa confirmed riceve status=cancelled, THE registration-service
  SHALL aggiornarne status e updated_at, preservando id, riferimenti, amount e created_at.
- IF viene richiesto cancelled→confirmed, THEN THE registration-service SHALL
  rispondere 422 INVALID_STATUS_TRANSITION senza mutazioni.
- WHEN viene reinviato lo stato corrente, THE registration-service SHALL
  restituire la risorsa invariata (operazione idempotente, nessuna transizione).
- WHEN DELETE trova una risorsa, THE registration-service SHALL eliminarla e
  restituire 204 senza body. IF PATCH/DELETE non trovano l'id, SHALL rispondere
  404 NOT_FOUND.
- WHEN PUT /api/v1/registrations/{id} viene richiesto, THE registration-service
  SHALL rispondere sempre 405 METHOD_NOT_ALLOWED.
- THE registration-service SHALL eseguire PATCH/DELETE localmente, senza
  dipendenze HTTP, serializzando le modifiche con le prenotazioni.

## REQ-REG-B08 — Statistiche

Come organizzatore voglio conoscere capienza e iscrizioni attive.

- WHEN GET /api/v1/registrations/stats riceve event_id UUID valido,
  THE registration-service SHALL recuperare la capienza corrente da event-service,
  contare le iscrizioni confirmed e restituire event_id/capacity/confirmed/available.
- THE registration-service SHALL calcolare available=max(0, capacity-confirmed).
  Una riduzione della capienza non SHALL cancellare iscrizioni esistenti.
- IF event_id è assente/vuoto/invalido, THEN THE registration-service SHALL
  rispondere 422 VALIDATION_ERROR.
- IF l'evento non esiste, THEN THE registration-service SHALL rispondere
  404 NOT_FOUND, diversamente dal 422 di creazione.
- THE registration-service SHALL fornire stats anche per eventi draft/cancelled
  esistenti, senza interrogare user-service.

## REQ-REG-B09 — Dipendenze HTTP

Come client voglio distinguere dati mancanti da servizi indisponibili.

- THE registration-service SHALL leggere USER_SERVICE_URL ed EVENT_SERVICE_URL
  dall'ambiente, default http://localhost:5001 e http://localhost:5002,
  ed eseguire le chiamate con timeout di 2 secondi.
- IF una dipendenza non risponde, restituisce 5xx, uno status inatteso o dati
  illeggibili/incoerenti, THEN THE registration-service SHALL rispondere
  503 DEPENDENCY_UNAVAILABLE senza modifiche.

## REQ-REG-04 — Standard, configurazione e persistenza

Come valutatore voglio API uniformi e servizi isolati.

- THE registration-service SHALL usare JSON snake_case ed errori
  {"error":{"code":"UPPER_SNAKE","message":"...","details":{}}}.
- IF JSON è malformato o Content-Type non JSON, THEN THE registration-service
  SHALL rispondere 400 MALFORMED_JSON; path/metodi sconosciuti SHALL produrre
  404 NOT_FOUND/405 METHOD_NOT_ALLOWED.
- WHEN GET /health è chiamato, THE registration-service SHALL restituire
  200 {"status":"ok","service":"registration-service"} senza chiamare dipendenze.
- THE registration-service SHALL leggere PORT (default 5003, intero 1..65535),
  STORAGE_BACKEND (memory/json/sqlite), DATA_DIR (default ./data) alla factory.
- THE registration-service SHALL usare istanze memory isolate e persistenza
  JSON/SQLite ai riavvii, con copie dei record, rollback e business logic invariata.
  Nessun database esterno o import di altri servizi.
- THE registration-service SHALL avviarsi senza debug/reloader e senza dipendere
  dal DNS inverso locale, rispettando la PORT ricevuta.

## REQ-REG-05 — Verifica

Come valutatore voglio prove ripetibili di regole e collaborazione tra servizi.

- THE suite SHALL coprire i tre backend, concorrenza su duplicati/capienza,
  HTTP mockato con responses, i contratti di tutte le otto operazioni dichiarate
  (incluso PUT 405), coverage app>=80% anche sui rami.
- THE integration suite SHALL avviare i tre servizi reali su porte libere con
  dati temporanei e verificare successo, riferimenti mancanti 422, ciascuna
  dipendenza spenta 503, capienza/cancellazioni e persistenza dopo riavvio.
- THE phase delivery SHALL abilitare i tre servizi nel manifest e superare
  il collaudo mandatory sui tre backend, incluso IT-J01, senza modificare il
  materiale protetto. Revisione finale e tag appartengono alle fasi 5 e 6.
