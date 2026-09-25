# Requirements Document

## Introduction

Il `user-service` gestisce l'anagrafica degli utenti della piattaforma TechConf: partecipanti (`attendee`), relatori (`speaker`) e organizzatori (`organizer`). Espone un'API REST su `/api/v1/users` ed è chiamato da `event-service` e `registration-service` per verificare l'esistenza e il ruolo degli utenti. Non chiama a sua volta nessun altro servizio.

La revisione dei campi read-only è tracciata nella [issue #1](https://github.com/Manuel-Mezzanotte/itt-marconi-workshops/issues/1).

## Glossary

- **User**: risorsa che rappresenta un utente registrato nella piattaforma; identificata da un UUID generato dal server.
- **User_Service**: il microservizio descritto in questo documento.
- **UserCreate**: schema di input per la creazione e la sostituzione completa di un utente (`first_name`, `last_name`, `email` obbligatori; `company`, `role` opzionali).
- **UserUpdate**: schema di input per l'aggiornamento parziale di un utente (tutti i campi opzionali).
- **Role**: enumerazione dei ruoli ammessi: `attendee` (default), `speaker`, `organizer`.
- **Email normalizzata**: l'indirizzo email convertito in minuscolo prima del salvataggio.
- **Repository**: modulo intercambiabile di accesso ai dati; può essere `memory`, `json` o `sqlite`.
- **STORAGE_BACKEND**: variabile d'ambiente che seleziona il repository attivo.
- **DATA_DIR**: directory in cui il repository `json` scrive `users.json` e il repository `sqlite` scrive `users.db`.
- **IT-U01..IT-U08**: identificativi dei test di collaudo del docente presenti in `tests/integration/test_user.py`.
- **Formato errore standard**: ogni risposta di errore ha il body `{"error": {"code": "CODICE", "message": "testo leggibile", "details": {}}}`. Nei criteri di accettazione gli errori sono indicati con solo il codice HTTP e il codice errore (es. "422 `VALIDATION_ERROR`"); il body segue sempre questo formato.

---

## Requirements

### REQ-USR-01 — Creazione utente

**User story:** As a client application, I want to create a new user with valid data, so that the user is registered and retrievable by other services.

**Acceptance criteria:**

1. WHEN il client invia `POST /api/v1/users` con un body JSON valido contenente `first_name`, `last_name` ed `email`, THE User_Service SHALL creare la risorsa, assegnare un UUID v4 come `id`, impostare `created_at` e `updated_at` all'istante corrente in formato ISO 8601 UTC con suffisso `Z`, e restituire 201 con il body della risorsa creata e l'header `Location: /api/v1/users/{id}`.
2. WHEN il client invia `POST /api/v1/users` senza specificare `role`, THE User_Service SHALL impostare `role` al valore `attendee`.
3. WHEN il client invia `POST /api/v1/users` senza specificare `company`, THE User_Service SHALL impostare `company` a `null`.
4. IF il body JSON inviato a `POST /api/v1/users` è malformato o non è JSON valido, THEN THE User_Service SHALL rispondere 400 con codice `MALFORMED_JSON`.
5. IF il body JSON di `POST /api/v1/users` è privo di uno o più campi obbligatori (`first_name`, `last_name`, `email`) o contiene valori che violano i vincoli di tipo o lunghezza, THEN THE User_Service SHALL rispondere 422 con codice `VALIDATION_ERROR`.
6. IF il body JSON di `POST /api/v1/users` contiene campi non previsti dallo schema `UserCreate`, THEN THE User_Service SHALL rispondere 422 con codice `VALIDATION_ERROR`.
7. IF il body JSON di `POST /api/v1/users` contiene uno o più dei campi read-only `id`, `created_at`, `updated_at`, THEN THE User_Service SHALL rispondere 422 con codice `VALIDATION_ERROR`.

---

### REQ-USR-B01 — Unicità dell'email (case-insensitive)

**User story:** As a platform administrator, I want each email address to be unique regardless of letter case, so that the same person cannot register twice with variants of the same address.

**Acceptance criteria:**

1. WHEN il client invia `POST /api/v1/users` con un'email che, convertita in minuscolo, coincide con quella di un utente esistente, THE User_Service SHALL rispondere 409 con codice `EMAIL_ALREADY_EXISTS`.
2. WHEN il client invia `PUT /api/v1/users/{id}` con un'email che, convertita in minuscolo, coincide con quella di un utente diverso dall'utente con `id` specificato, THE User_Service SHALL rispondere 409 con codice `EMAIL_ALREADY_EXISTS`.
3. WHEN il client invia `PATCH /api/v1/users/{id}` con un campo `email` che, convertita in minuscolo, coincide con quella di un utente diverso dall'utente con `id` specificato, THE User_Service SHALL rispondere 409 con codice `EMAIL_ALREADY_EXISTS`.
4. WHEN il client invia `PUT /api/v1/users/{id}` o `PATCH /api/v1/users/{id}` con la stessa email già associata all'utente con `id` specificato, THE User_Service SHALL accettare l'operazione senza segnalare conflitto.

---

### REQ-USR-B02 — Normalizzazione dell'email in minuscolo

**User story:** As a client application, I want email addresses stored and returned in lowercase, so that comparisons are consistent regardless of the case used during input.

**Acceptance criteria:**

1. WHEN il client invia `POST /api/v1/users` con un campo `email` contenente lettere maiuscole, THE User_Service SHALL convertire l'email in minuscolo prima del salvataggio e restituire l'email in minuscolo nel body della risposta.
2. WHEN il client invia `PUT /api/v1/users/{id}` o `PATCH /api/v1/users/{id}` con un campo `email`, THE User_Service SHALL convertire l'email in minuscolo prima del salvataggio e restituire l'email in minuscolo nel body della risposta.
3. THE User_Service SHALL restituire l'email in minuscolo in tutti gli endpoint che includono la risorsa utente nella risposta.

---

### REQ-USR-02 — Recupero utente per identificatore

**User story:** As a client application, I want to retrieve a user by its unique identifier, so that I can display or use the user's data.

**Acceptance criteria:**

1. WHEN il client invia `GET /api/v1/users/{id}` con un `id` che corrisponde a un utente esistente, THE User_Service SHALL rispondere 200 con il body della risorsa utente.
2. IF il client invia `GET /api/v1/users/{id}` con un `id` che non corrisponde ad alcun utente, THEN THE User_Service SHALL rispondere 404 con codice `NOT_FOUND`.

---

### REQ-USR-03 — Lista utenti con paginazione

**User story:** As a client application, I want to retrieve a paginated list of users, so that I can browse or search the registry without loading all records at once.

**Acceptance criteria:**

1. WHEN il client invia `GET /api/v1/users` senza parametri, THE User_Service SHALL rispondere 200 con `{"items": [...], "page": 1, "page_size": 20, "total": N}` usando i valori di default `page=1` e `page_size=20`.
2. WHEN il client invia `GET /api/v1/users?page=P&page_size=S`, THE User_Service SHALL rispondere 200 con la pagina `P` di utenti, `page_size` elementi al massimo per pagina, e il totale degli utenti nel campo `total`.
3. IF il client invia `GET /api/v1/users` con `page_size` superiore a 100, THEN THE User_Service SHALL rispondere 422 con codice `VALIDATION_ERROR`.
4. IF il client invia `GET /api/v1/users` con `page` o `page_size` non interi o minori di 1, THEN THE User_Service SHALL rispondere 422 con codice `VALIDATION_ERROR`.

---

### REQ-USR-B03 — Filtri sulla lista utenti

**User story:** As a client application, I want to filter the user list by role or email, so that I can retrieve only the subset of users relevant to a specific operation.

**Acceptance criteria:**

1. WHEN il client invia `GET /api/v1/users?role=R`, THE User_Service SHALL restituire nella lista solo gli utenti con `role` uguale a `R`; il campo `total` deve riflettere il numero di utenti corrispondenti al filtro.
2. IF il client invia `GET /api/v1/users?role=R` con un valore `R` non compreso nell'enumerazione `attendee | speaker | organizer`, THEN THE User_Service SHALL rispondere 422 con codice `VALIDATION_ERROR`.
3. WHEN il client invia `GET /api/v1/users?email=E`, THE User_Service SHALL restituire nella lista solo gli utenti la cui email normalizzata corrisponde esattamente alla stringa `E` convertita in minuscolo.
4. WHEN il client invia `GET /api/v1/users?role=R&email=E`, THE User_Service SHALL applicare entrambi i filtri in congiunzione.

---

### REQ-USR-04 — Sostituzione completa utente (PUT)

**User story:** As a client application, I want to replace all fields of an existing user, so that the record reflects a completely updated set of data.

**Acceptance criteria:**

1. WHEN il client invia `PUT /api/v1/users/{id}` con un body JSON valido secondo lo schema `UserCreate`, THE User_Service SHALL sovrascrivere tutti i campi della risorsa, aggiornare `updated_at` all'istante corrente, e rispondere 200 con la risorsa aggiornata.
2. WHEN il client invia `PUT /api/v1/users/{id}` senza il campo `company`, THE User_Service SHALL impostare `company` a `null`.
3. WHEN il client invia `PUT /api/v1/users/{id}` senza il campo `role`, THE User_Service SHALL impostare `role` a `attendee`.
4. THE User_Service SHALL mantenere invariati `id` e `created_at` a seguito di un `PUT`.
5. IF il client invia `PUT /api/v1/users/{id}` con un `id` che non corrisponde ad alcun utente, THEN THE User_Service SHALL rispondere 404 con codice `NOT_FOUND`.
6. IF il body JSON di `PUT /api/v1/users/{id}` è malformato, THEN THE User_Service SHALL rispondere 400 con codice `MALFORMED_JSON`.
7. IF il body JSON di `PUT /api/v1/users/{id}` contiene campi non previsti dallo schema `UserCreate` o viola i vincoli di tipo o lunghezza, THEN THE User_Service SHALL rispondere 422 con codice `VALIDATION_ERROR`.

---

### REQ-USR-05 — Aggiornamento parziale utente (PATCH)

**User story:** As a client application, I want to update only specific fields of an existing user without replacing the entire record, so that unchanged fields are preserved.

**Acceptance criteria:**

1. WHEN il client invia `PATCH /api/v1/users/{id}` con un body JSON contenente uno o più campi validi secondo lo schema `UserUpdate`, THE User_Service SHALL aggiornare solo i campi presenti nel body, lasciare invariati tutti gli altri campi, aggiornare `updated_at` all'istante corrente, e rispondere 200 con la risorsa aggiornata.
2. THE User_Service SHALL mantenere invariati `id` e `created_at` a seguito di un `PATCH`.
3. IF il client invia `PATCH /api/v1/users/{id}` con un `id` che non corrisponde ad alcun utente, THEN THE User_Service SHALL rispondere 404 con codice `NOT_FOUND`.
4. IF il body JSON di `PATCH /api/v1/users/{id}` è malformato, THEN THE User_Service SHALL rispondere 400 con codice `MALFORMED_JSON`.
5. IF il body JSON di `PATCH /api/v1/users/{id}` contiene campi non previsti dallo schema `UserUpdate` o viola i vincoli di tipo o lunghezza, THEN THE User_Service SHALL rispondere 422 con codice `VALIDATION_ERROR`.

---

### REQ-USR-06 — Cancellazione utente

**User story:** As a client application, I want to delete a user by its identifier, so that the record is permanently removed from the registry.

**Acceptance criteria:**

1. WHEN il client invia `DELETE /api/v1/users/{id}` con un `id` che corrisponde a un utente esistente, THE User_Service SHALL rimuovere la risorsa e rispondere 204 senza body.
2. IF il client invia `DELETE /api/v1/users/{id}` con un `id` che non corrisponde ad alcun utente, THEN THE User_Service SHALL rispondere 404 con codice `NOT_FOUND`.

---

### REQ-USR-07 — Health check

**User story:** As an operations tool or integration test harness, I want a health endpoint that responds immediately without querying external dependencies, so that I can verify that the service process is alive independently of its storage backend.

**Acceptance criteria:**

1. WHEN il client invia `GET /health`, THE User_Service SHALL rispondere 200 con `{"status": "ok", "service": "user-service"}` senza interrogare il repository o dipendenze esterne.

---

### REQ-USR-08 — Gestione di path sconosciuti e metodi non previsti

**User story:** As a client application, I want consistent error responses for unknown paths and unsupported HTTP methods, so that error handling is uniform across the entire API.

**Acceptance criteria:**

1. IF il client invia una richiesta a un path non definito nell'API, THEN THE User_Service SHALL rispondere 404 con codice `NOT_FOUND`.
2. IF il client invia una richiesta con un metodo HTTP non previsto su un path esistente, THEN THE User_Service SHALL rispondere 405 con codice `METHOD_NOT_ALLOWED`.

---

### REQ-USR-09 — Configurazione e avvio

**User story:** As a deployment environment, I want the service to read all its configuration from environment variables at startup, so that the same artifact can run with different backends and ports without code changes.

**Acceptance criteria:**

1. THE User_Service SHALL leggere `PORT` (default `5001`), `STORAGE_BACKEND` (default `memory`) e `DATA_DIR` (default `./data`) esclusivamente nel modulo `app/config.py`.
2. WHEN `STORAGE_BACKEND` è `memory`, THE User_Service SHALL conservare i dati in memoria senza scrivere file su disco.
3. WHEN `STORAGE_BACKEND` è `json`, THE User_Service SHALL leggere e scrivere i dati nel file `users.json` all'interno di `DATA_DIR`.
4. WHEN `STORAGE_BACKEND` è `sqlite`, THE User_Service SHALL leggere e scrivere i dati nel file `users.db` all'interno di `DATA_DIR` usando esclusivamente il modulo `sqlite3` della standard library.
5. WHEN `STORAGE_BACKEND` cambia tra un avvio e l'altro, THE User_Service SHALL selezionare il backend indicato dalla configurazione senza richiedere modifiche al codice.
6. THE User_Service SHALL ascoltare sulla porta indicata da `PORT`.
7. WHEN il servizio viene riavviato con `STORAGE_BACKEND` `json` o `sqlite`, THE User_Service SHALL ritrovare i dati scritti nella sessione precedente rileggendo i file in `DATA_DIR`.
8. WHEN due istanze del servizio girano con `STORAGE_BACKEND` `memory`, THE User_Service SHALL mantenere i dati di ciascuna istanza isolati e indipendenti dall'altra.

---

### REQ-USR-10 — Generazione di identificatori e timestamp

**User story:** As a client application, I want identifiers and timestamps to be generated server-side, so that clients do not need to supply or predict them.

**Acceptance criteria:**

1. THE User_Service SHALL generare `id` come UUID v4 tramite `uuid.uuid4()` al momento della creazione di ogni risorsa.
2. THE User_Service SHALL generare `created_at` e `updated_at` come timestamp UTC in formato ISO 8601 con suffisso `Z` (es. `2026-10-15T09:30:00Z`), ammettendo frazioni di secondo.
3. WHEN una risorsa viene modificata tramite `PUT` o `PATCH`, THE User_Service SHALL aggiornare `updated_at` al timestamp corrente mantenendo `created_at` invariato.
4. IF il body di POST, PUT o PATCH contiene i campi `id`, `created_at` o `updated_at`, THEN THE User_Service SHALL rispondere 422 con codice `VALIDATION_ERROR` senza effettuare alcuna modifica alla risorsa.

---

### REQ-USR-11 — Vincoli sui campi della risorsa

**User story:** As a client application, I want field-level constraints enforced on every write operation, so that stored data is always consistent with the contract.

**Acceptance criteria:**

1. IF su POST o PUT `first_name` è assente, ha lunghezza 0 o supera i 50 caratteri, THEN THE User_Service SHALL rispondere 422 con codice `VALIDATION_ERROR`.
2. IF su POST o PUT `last_name` è assente, ha lunghezza 0 o supera i 50 caratteri, THEN THE User_Service SHALL rispondere 422 con codice `VALIDATION_ERROR`.
3. IF su POST o PUT `email` è assente o non è un indirizzo email nel formato standard, THEN THE User_Service SHALL rispondere 422 con codice `VALIDATION_ERROR`.
4. IF su PATCH `first_name`, `last_name` o `email` è presente ma viola i rispettivi vincoli di lunghezza o formato, THEN THE User_Service SHALL rispondere 422 con codice `VALIDATION_ERROR`.
5. IF `company` è presente (in POST, PUT o PATCH) e il valore non è una stringa di max 100 caratteri né `null`, THEN THE User_Service SHALL rispondere 422 con codice `VALIDATION_ERROR`.
6. IF `role` è presente (in POST, PUT o PATCH) e il valore non appartiene all'enumerazione `attendee | speaker | organizer`, THEN THE User_Service SHALL rispondere 422 con codice `VALIDATION_ERROR`.
7. IF il body JSON è valido ma non è un oggetto JSON (es. array, stringa, numero), THEN THE User_Service SHALL rispondere 422 con codice `VALIDATION_ERROR`.
8. WHEN il client invia `PATCH /api/v1/users/{id}` con un body JSON `{}`, THE User_Service SHALL rispondere 200 con la risorsa invariata (nessun campo aggiornato, `updated_at` non modificato).
9. IF `first_name`, `last_name` o `email` è presente ma non è una stringa non nulla, THEN THE User_Service SHALL rispondere 422 con codice `VALIDATION_ERROR`, senza convertire automaticamente numeri, booleani o altri tipi in stringhe.

---

### REQ-USR-12 — Copertura dei test unitari

**User story:** As a developer, I want comprehensive unit tests for all endpoints and business rules, so that regressions are caught before integration.

**Acceptance criteria:**

1. THE User_Service SHALL essere coperto da test unitari con `pytest` che usano il Flask test client.
2. THE User_Service SHALL avere almeno un test per ciascun endpoint che valida la risposta con `assert_matches_contract` di `contracts/validator.py`.
3. THE User_Service SHALL avere i test del repository parametrizzati su tutti e tre i backend (`memory`, `json`, `sqlite`), usando `tmp_path` per i backend su file.
4. THE User_Service SHALL raggiungere una coverage ≥ 80% misurata con `pytest --cov=app`, inclusiva dei rami.
5. THE User_Service SHALL citare l'ID `REQ-USR-*` corrispondente nel marker pytest, nel nome o nella docstring di ogni test che verifica una regola di business o un acceptance criterion.
