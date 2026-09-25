# user-service

Anagrafica utenti.

Stato: specifiche committate e task T-01/T-02/T-03 completati in Kiro.
Sono presenti configurazione, application factory, `/health`, handler degli errori
e repository memory, JSON e SQLite. `POST /api/v1/users` crea utenti con validazione,
email normalizzata e univoca, UUID v4 e timestamp UTC con microsecondi.
I repository e il service sono collegati alla factory. GET, PUT, PATCH e DELETE
sono previsti nei task T-04..T-07.

La struttura interna segue `.kiro/steering/structure.md`.
Per avviare gli endpoint implementati dalla directory del servizio:
`../../.venv/bin/python -m app`. La porta predefinita è 5001, modificabile con PORT.
Il servizio non è ancora dichiarato nel manifest attivo: l'abilitazione è nel T-08.

Per i test dalla root: `make test-unit SERVICE=user-service`.
Le specifiche sono in `.kiro/specs/user-service/`.

Verifica al T-03: 324 test superati, copertura delle linee 88,59%.
La verifica conclusiva con copertura dei rami è prevista nel T-08.
`make check` passa; il collaudo delle API sarà eseguito nel T-08.
