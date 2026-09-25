---
inclusion: always
---

# Tecnologie e vincoli tecnici

## Ambiente

- Python **3.12**, ambiente virtuale `.venv/` nella root Git.
- Runtime: Flask e requests. Dipendenze dichiarate in `requirements.txt`.
- Test: pytest, pytest-cov, responses, PyYAML e jsonschema. Dipendenze del
  collaudo importate senza modificarle tramite `requirements-dev.txt`.
- `requirements.lock` congela le versioni risolte. `make setup` ricrea l'ambiente.
- Usare `.venv/bin/python` dalla root e `../../.venv/bin/python` dalla cartella
  di un servizio. Non dipendere dal comando globale `python` o da un virtualenv attivato.
- Nessun framework ORM, DBMS esterno, container o nuova dipendenza senza una
  motivazione nella specifica e compatibilità con la traccia.

## API e configurazione

- Endpoint, payload, status e campi ammessi seguono il contratto OpenAPI del servizio.
- `id`, timestamp e campi calcolati sono assegnati dal server secondo il contratto;
  non aggiungere campi di risposta non previsti.
- Configurazione letta in un solo modulo `app/config.py` per servizio:
  `PORT`, URL delle dipendenze, `STORAGE_BACKEND`, `DATA_DIR`.
- I default localhost sono ammessi soltanto nella configurazione. Le chiamate
  HTTP usano le variabili `*_SERVICE_URL`, con timeout di 2 secondi.
- Applicare il formato uniforme degli errori anche a JSON malformato, 404 e 405.
  Le eccezioni di mapping documentate per `stats` e `summary` restano valide.
- `/health` deve funzionare senza interrogare le dipendenze: il collaudo deve poter
  avviare istanze con una dipendenza spenta e provarne le API.
- Verificare il tipo prima di confronti con enum o limiti numerici: liste e
  oggetti JSON devono produrre 422, non TypeError; bool non è un importo o una capienza.
- Location deve rispettare il design senza dipendere da route di task futuri.
  I timestamp seguono la precisione scelta nel design, senza troncamenti impliciti.

## Persistenza

Ogni servizio implementa repository intercambiabili `memory`, `json`, `sqlite`.
La business logic dipende dall'interfaccia del repository, non dal backend.
Usare esclusivamente `json` e `sqlite3` della standard library per la persistenza.
I file risiedono in `DATA_DIR` (default `./data`) e sono esclusi da Git; i nomi
devono distinguere i servizi anche quando viene fornita una directory comune.

## Verifica

- Unit test: HTTP simulato con `responses`; repository parametrizzati sui tre
  backend, usando `tmp_path` per i file; ID `REQ-...` nei marker, nomi o docstring.
- Almeno un test per operazione API con `assert_matches_contract` del template.
  Con Flask test client usare l'adattatore dict `status_code`, `headers`, `json`
  supportato dal validator, senza cambiare `contracts/validator.py`.
- I test intermedi usano soltanto le API già implementate. Verificare codici
  e dati richiesti dal contratto, evitando vincoli arbitrari sul testo dei messaggi.
- Usare pytest con output conciso e codice di uscita diretto, senza pipe a head
  o tail. Dopo una suite verde, ripeterla soltanto se cambiano file o restano
  problemi concreti da verificare; altrimenti concludere il task.
- Coverage almeno 80% per servizio; `make test-unit SERVICE=user-service` misura
  soltanto l'app di quel servizio. La configurazione include anche i rami.
- Test di integrazione propri con processi reali, porte libere, directory temporanee
  e cleanup garantito: almeno successo, riferimento inesistente (422), dipendenza
  spenta (503) per ogni servizio che dipende da un altro.
- Collaudo fornito: `make acceptance`. `make check-collection` raccoglie i test
  senza avviare servizi: non equivale al collaudo funzionale.
- `make check` verifica ambiente, integrità e raccolta del collaudo. L'hook
  pre-prompt lo esegue e conserva l'output locale in `.checks/pre-prompt.log`.
