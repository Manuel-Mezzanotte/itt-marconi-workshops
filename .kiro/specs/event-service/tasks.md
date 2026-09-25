# Task — event-service

Eseguire un task alla volta, verificarlo, spuntarlo e creare un commit prima del
successivo. Requirements e design precedono questo piano nella cronologia.
Per i test intermedi dalla directory del servizio:
`../../.venv/bin/python -m pytest -c ../../pyproject.toml tests -q`.
Non modificare contracts/, tests/integration/ o Exam/.

- [x] T-01 — Configurazione, errori, factory e avvio
  - Implementare config, ApiError, health e server locale senza reverse DNS.
  - Test di configurazione/ambiente, errori 404/405, contratto health e avvio con PORT.
  - _Requirements: REQ-EVT-04, REQ-EVT-05, REQ-EVT-06_

- [x] T-02 — Repository memory, JSON e SQLite
  - Implementare interfaccia, selezione backend, CRUD con copie, filtri/paginazione
    e update atomico tramite transform.
  - Test sui tre backend: persistenza, isolamento, rollback, replace JSON fallito,
    query combinate, pagine enormi, concorrenti senza aggiornamenti persi.
  - _Requirements: REQ-EVT-02, REQ-EVT-B06, REQ-EVT-03, REQ-EVT-05, REQ-EVT-06_

- [ ] T-03 — Validazione, client HTTP e POST
  - Implementare EventCreate/EventUpdate, date, numeri, UUID e controllo transizioni.
  - Client user con timeout e mapping errori; service.create, route POST e factory.
  - Test responses, tipo/limiti/read-only, creazione sui backend, default,
    organizzatore inesistente/ruolo errato/dipendenza indisponibile e contratti.
  - _Requirements: REQ-EVT-01, REQ-EVT-B01, REQ-EVT-B02, REQ-EVT-B03,
    REQ-EVT-B04, REQ-EVT-B05, REQ-EVT-04, REQ-EVT-06_

- [ ] T-04 — GET, lista e query
  - Aggiungere GET singolo/lista con filtri status/city e paginazione stabile.
  - Test sui tre backend: assente/presente, filtri singoli/AND, città vuota,
    totali, limiti e query invalide; contratti di successo/errore.
  - _Requirements: REQ-EVT-02, REQ-EVT-B06, REQ-EVT-04, REQ-EVT-06_

- [ ] T-05 — PUT e PATCH
  - Implementare sostituzione e aggiornamento parziale con update atomico;
    timestamp, no-op, date risultanti, transizioni e controllo organizer.
  - Test su tre backend, stati consentiti/vietati, conflitti di transizione tra
    richieste concorrenti, riferimento/dipendenza in errore e nessuna mutazione.
  - _Requirements: REQ-EVT-03, REQ-EVT-B01, REQ-EVT-B02, REQ-EVT-B03,
    REQ-EVT-B04, REQ-EVT-B05, REQ-EVT-04, REQ-EVT-06_

- [ ] T-06 — DELETE e contratti completi
  - Aggiungere DELETE 204 vuoto/404 e completare i test delle sette operazioni API.
  - Verificare cancellazione isolata, lettura successiva 404, totale aggiornato,
    errori uniformi e indipendenza delle letture dalla disponibilità di user.
  - _Requirements: REQ-EVT-02, REQ-EVT-03, REQ-EVT-04, REQ-EVT-06_

- [ ] T-07 — Integrazione reale, collaudo e documentazione
  - Aggiungere fixture/processi e casi reali positivi, 422 e 503; riavvii persistenti.
  - Abilitare solo event oltre a user in services.yaml.
  - Eseguire unit/contract con coverage >=80%, integrazione propria e collaudo
    user+event su memory/json/sqlite con directory isolate e cleanup verificato.
  - Registrare i bug reali con issue, regressione e fix dedicato; verificare
    checksum e aggiornare README, report e BUGS senza anticipare la fase 4.
  - _Requirements: REQ-EVT-B01, REQ-EVT-B02, REQ-EVT-B05, REQ-EVT-05, REQ-EVT-06_
