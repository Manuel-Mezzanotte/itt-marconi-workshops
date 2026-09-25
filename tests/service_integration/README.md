# Integrazione propria

La suite avvia user-service, event-service e registration-service come processi reali con porte libere,
DATA_DIR temporanee e backend parametrizzato memory/json/sqlite. Non usa import
delle fixture del docente, né importa codice applicativo dei servizi nel runner.

`test_event_http.py` contiene quattro scenari per ciascun backend, 12 casi:

- CRUD completo e verifica reale dell'organizzatore.
- Utente inesistente e ruolo errato: 422, nessuna creazione.
- Arresto del processo user: POST/PUT/PATCH con riferimento producono 503 senza
  mutare l'evento; health, letture e operazioni senza riferimento restano disponibili.
- Riavvio event: JSON/SQLite recuperano la stessa risorsa, memory riparte vuoto.

`test_registration_http.py` aggiunge 21 casi sui tre backend:

- Evento con due posti, terza iscrizione rifiutata, cancellazione, nuova iscrizione,
  statistiche coerenti e conservazione del prezzo storico.
- Utente/evento inesistenti e evento draft/cancelled.
- Arresto separato di user o event: 503 in creazione, dati invariati, letture e
  cancellazioni locali ancora disponibili.
- Otto richieste HTTP concorrenti per un posto o per la stessa coppia: un solo
  vincitore, gli altri 409 con codice coerente.
- Riavvio registration: persistenza di righe confirmed/cancelled su JSON/SQLite,
  archivio vuoto su memory.

Ogni risposta è verificata tramite il validator del contratto. Il teardown termina
i processi, controlla le porte e rimuove la directory temporanea. Le attese di
startup e arresto sono limitate; eventuali problemi riportano il log del servizio.

Dalla root: `make test-own-integration`.
La suite del docente rimane separata in `tests/integration/`: eseguire i due
gruppi in processi pytest distinti, come già previsto dal Makefile.
Totale attuale: **33 casi superati**, 12 event e 21 registration.
