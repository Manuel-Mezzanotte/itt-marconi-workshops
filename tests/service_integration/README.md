# Integrazione propria

La suite avvia user-service ed event-service come processi reali con porte libere,
DATA_DIR temporanee e backend parametrizzato memory/json/sqlite. Non usa import
delle fixture del docente, né importa codice applicativo dei servizi nel runner.

`test_event_http.py` contiene quattro scenari per ciascun backend, 12 casi:

- CRUD completo e verifica reale dell'organizzatore.
- Utente inesistente e ruolo errato: 422, nessuna creazione.
- Arresto del processo user: POST/PUT/PATCH con riferimento producono 503 senza
  mutare l'evento; health, letture e operazioni senza riferimento restano disponibili.
- Riavvio event: JSON/SQLite recuperano la stessa risorsa, memory riparte vuoto.

Ogni risposta è verificata tramite il validator del contratto. Il teardown termina
i processi, controlla le porte e rimuove la directory temporanea. Le attese di
startup e arresto sono limitate; eventuali problemi riportano il log del servizio.

Dalla root: `make test-own-integration`.
La suite del docente rimane separata in `tests/integration/`: eseguire i due
gruppi in processi pytest distinti, come già previsto dal Makefile.
Gli scenari di registration-service saranno aggiunti nella fase 4.
