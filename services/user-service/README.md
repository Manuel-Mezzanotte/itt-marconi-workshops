# user-service

Anagrafica utenti.

Stato: cartelle predisposte nella fase 1, nessun codice applicativo e nessun test proprio.
Prima dell'implementazione creare e committare in Kiro requirements, design e tasks
in `.kiro/specs/user-service/`.

La struttura interna segue `.kiro/steering/structure.md`.
Il comando previsto nel manifest e `../../.venv/bin/python -m app`;
non e ancora eseguibile. Il servizio non e dichiarato nel manifest attivo.

Dalla root, dopo l'implementazione: `make test-unit SERVICE=user-service`.
