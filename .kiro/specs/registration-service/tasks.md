# Task — registration-service

Un task alla volta: implementazione, test, checklist e commit. Le specifiche
requirements e design precedono questo piano. Comando intermedio dalla cartella
del servizio: `../../.venv/bin/python -m pytest -c ../../pyproject.toml tests -q`.
Materiale protetto e altri servizi non vengono modificati.

- [x] T-01 — Configurazione, errori, health e avvio
  - Factory e configurazione user/event, PORT, backend/DATA_DIR; handler JSON.
  - Avvio locale senza debugger/reloader/reverse DNS, health indipendente.
  - Test configurazione, isolamento, health/contratto e metodi/path errati.
  - _Requirements: REQ-REG-04, REQ-REG-05_

- [x] T-02 — Repository e prenotazioni atomiche
  - Memory/JSON/SQLite con reserve, get/list/count, update_status e delete.
  - Duplicati prima di capienza, solo confirmed contate; transazioni/lock,
    indice parziale SQLite, riiscrizione dopo cancellazione, copie e rollback.
  - Test concorrenti sull'ultimo posto e sulla stessa coppia, tutti i backend;
    SQLite con istanze distinte. Persistenza, filtri e pagine enormi.
  - _Requirements: REQ-REG-B04, REQ-REG-B05, REQ-REG-B07, REQ-REG-02,
    REQ-REG-03, REQ-REG-04, REQ-REG-05_

- [ ] T-03 — Validazione, dipendenze HTTP e creazione
  - Payload create/patch, UUID e client user/event con timeout/mapping errori.
  - POST: verifica riferimenti, evento published, importo dal servizio eventi,
    UUID/timestamp e reserve atomica.
  - Test responses, input errati, risorse mancanti, dipendenze indisponibili,
    capienza/duplicati e contract test su tre backend.
  - _Requirements: REQ-REG-01, REQ-REG-B01, REQ-REG-B02, REQ-REG-B03,
    REQ-REG-B04, REQ-REG-B05, REQ-REG-B06, REQ-REG-B09, REQ-REG-05_

- [ ] T-04 — Letture, filtri e statistiche
  - GET singolo/lista, query validate, filtri AND e paginazione.
  - Stats con capienza da event, conteggio confirmed e 404 speciale.
  - Test backend/contratti: totali, UUID invalidi, pagina enorme, stats 422/404/503,
    disponibilità dopo riduzione capienza, assenza di chiamate HTTP nelle letture locali.
  - _Requirements: REQ-REG-02, REQ-REG-B08, REQ-REG-B09, REQ-REG-05_

- [ ] T-05 — Cancellazioni, DELETE e contratto completo
  - PATCH status, idempotenza, transizione vietata; DELETE e PUT 405.
  - Test importo storico, posto liberato, riiscrizione con nuovo id, campi
    riservati, errori senza mutazioni e otto operazioni del contratto.
  - _Requirements: REQ-REG-03, REQ-REG-B04, REQ-REG-B05, REQ-REG-B06,
    REQ-REG-B07, REQ-REG-04, REQ-REG-05_

- [ ] T-06 — Integrazione reale dei tre servizi
  - Estendere fixture per avviare registration con user/event reali.
  - Test flusso completo, riferimenti inesistenti, user/event spenti separatamente,
    concorrenza HTTP, importo storico e persistenza dopo riavvio sui tre backend.
  - Cleanup garantito e verifica delle integrazioni event già presenti.
  - _Requirements: REQ-REG-B01, REQ-REG-B02, REQ-REG-B04, REQ-REG-B05,
    REQ-REG-B06, REQ-REG-B07, REQ-REG-B09, REQ-REG-04, REQ-REG-05_

- [ ] T-07 — Manifest, collaudo e documentazione
  - Dichiarare registration nel manifest con cwd e comando coerenti.
  - Eseguire unit/coverage>=80%, integrazione propria e collaudo mandatory con
    tutti i backend, incluso IT-J01, dati isolati e processi terminati.
  - Registrare eventuali bug reali con issue/regressione/fix; verificare checksum
    e aggiornare README, BUGS e report. Nessun bonus, tag o collaudo.txt finale.
  - _Requirements: REQ-REG-04, REQ-REG-05; IT-R01..IT-R10, IT-J01_
