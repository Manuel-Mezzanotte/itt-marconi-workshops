# registration-service

Gestione iscrizioni con verifica utente ed evento via HTTP.

Stato: cartelle predisposte nella fase 1, nessun codice applicativo e nessun test proprio.
Prima dell'implementazione creare e committare in Kiro requirements, design e tasks
in `.kiro/specs/registration-service/`.

La struttura interna segue `.kiro/steering/structure.md`.
Il comando previsto nel manifest e `../../.venv/bin/python -m app`;
non e ancora eseguibile. Il servizio non e dichiarato nel manifest attivo.

Dalla root, dopo l'implementazione: `make test-unit SERVICE=registration-service`.
