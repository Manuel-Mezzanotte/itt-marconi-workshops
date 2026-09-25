# user-service

Anagrafica utenti.

Stato: specifiche committate e task T-01/T-02 eseguiti in Kiro.
Sono presenti configurazione, application factory, `/health`, handler degli errori
e repository memory, JSON e SQLite. Le API utenti iniziano nel T-03.
I repository sono verificati separatamente e saranno collegati alla factory
insieme al service nel T-03.

La struttura interna segue `.kiro/steering/structure.md`.
Per avviare il solo health endpoint dalla directory del servizio:
`../../.venv/bin/python -m app`. La porta predefinita è 5001, modificabile con PORT.
Il servizio non è ancora dichiarato nel manifest attivo: l'abilitazione è nel T-08.

Per i test dalla root: `make test-unit SERVICE=user-service`.
Le specifiche sono in `.kiro/specs/user-service/`.

Verifica al T-02: 149 test superati, coverage complessiva con branch 96,23%.
`make check` passa; il collaudo delle API sarà eseguito nel T-08.
