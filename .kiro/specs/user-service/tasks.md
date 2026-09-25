# Implementation Plan: user-service

## Overview

Otto task da eseguire in ordine, uno alla volta con Start task. Ogni task include
implementazione e test del proprio comportamento. Dopo la verifica si crea il
commit corrispondente; Git è gestito separatamente, non dall'agente che esegue il task.

Il codice vive in services/user-service. Nei task intermedi usare dalla directory
del servizio `../../.venv/bin/python -m pytest -c ../../pyproject.toml tests -q`.
La soglia di coverage finale si verifica con make test-unit nel T-08. Non usare
il comando globale python, non creare stub di comportamenti futuri e non avviare
il task successivo. Non modificare contratti, collaudo o la copia sotto Exam/.

## Tasks

- [x] 1. Avvio, configurazione e health [T-01]
  - Crea app/config.py, app/errors.py, app/__init__.py e app/__main__.py secondo il design. La factory di questo task registra solo configurazione, health e handler: repository e service saranno collegati nel T-03, senza placeholder o import di file inesistenti.
  - Configurazione letta nella factory, default e override verificati; PORT valido, backend noto, DATA_DIR come Path. L'entrypoint usa PORT senza debug o reloader.
  - Aggiungi fixture e test per configurazione, app indipendenti, health conforme al contratto, 404 e 405 in JSON. Per testare __main__ intercetta app.run: non lasciare server avviati.
  - Mantieni services.yaml vuoto. Ferma l'esecuzione dopo i test del T-01.
  - _Requirements: 10.1, 11.1, 11.2, 12.1, 12.6, 15.1, 15.2, 15.5_
  - _Traceability: REQ-USR-07, REQ-USR-08, REQ-USR-09, REQ-USR-12_

- [x] 2. Repository memory, JSON e SQLite [T-02]
  - Implementa l'interfaccia UserRepository e la factory get_repository. Operazioni: create, get, get_by_email, list, update, delete. Mantieni i valori di ritorno definiti nel design.
  - Memory per istanza con RLock; JSON con RLock e scrittura atomica; SQLite con connessioni chiuse per operazione e transazioni esplicite. Unicità email verificata insieme alla scrittura anche negli update; le operazioni rifiutate non mutano i dati.
  - Ordinamento stabile, filtri combinati, totale filtrato e pagine fuori intervallo vuote, anche con indici molto grandi. Restituisci copie dei record.
  - Test parametrizzati sui tre backend: CRUD, duplicati create/update, aggiornamento della propria email, copie, filtri e paginazione, scritture concorrenti con la stessa email. Con tmp_path verifica riapertura JSON/SQLite e isolamento memory. Verifica che un errore di scrittura JSON non corrompa il file esistente.
  - _Requirements: 2.1, 2.2, 2.3, 2.4, 5.2, 6.1, 6.3, 6.4, 12.2, 12.3, 12.4, 12.5, 12.7, 12.8, 15.3, 15.5_
  - _Traceability: REQ-USR-B01, REQ-USR-03, REQ-USR-B03, REQ-USR-09, REQ-USR-12_

- [x] 3. Validazione e creazione utenti [T-03]
  - Implementa validation.py, UserService.create_user e la route POST esattamente su /api/v1/users, senza redirect dovuto a slash finale. Collega repository, service e blueprint nella factory; ogni app ha istanze proprie.
  - Applica i vincoli di UserCreate/UserUpdate, rifiuta campi extra/read-only, tipi sbagliati e JSON non oggetto. Non modificare il dict del chiamante. Email con fullmatch e successiva normalizzazione; id UUID v4 e timestamp UTC con Z creati dal service; default role e company.
  - Parsing silent=False: JSON malformato ->400; JSON null/array/scalare valido ->422. POST riuscito ->201 con Location; duplicato ->409. Gli errori delle scritture rimangono atomici.
  - Aggiungi test di validazione, service e POST sui tre backend, ai limiti dei campi e con errori di tipo. Per inviare JSON null usa il body letterale null con Content-Type application/json. Verifica id e timestamp e usa il validator sul successo e sugli errori dichiarati.
  - Issue #1: parametrizza i tre campi read-only e verifica 422 senza creazione di utenti.
  - _Requirements: 1.1, 1.2, 1.3, 1.4, 1.5, 1.6, 1.7, 2.1, 3.1, 13.1, 13.2, 13.4, 14.1, 14.2, 14.3, 14.5, 14.6, 14.7, 14.9, 15.1, 15.2, 15.5_
  - _Traceability: REQ-USR-01, REQ-USR-B01, REQ-USR-B02, REQ-USR-10, REQ-USR-11, REQ-USR-12_

- [x] 4. Lettura utenti, filtri e paginazione [T-04]
  - Implementa UserService.get_user/list_users e GET /api/v1/users e /api/v1/users/{id} con validazione della query e normalizzazione del filtro email. Distingui filtro assente e stringa vuota.
  - Test sui tre backend: record presente/assente, lista vuota, default, pagine consecutive stabili, pagina oltre il totale, page_size=100 e valori invalidi, filtri role/email singoli e combinati, totale dopo i filtri, email con maiuscole.
  - Usa il validator per GET singolo/lista e relativi errori dichiarati. Errori 404 e 422 restano nel formato uniforme.
  - _Requirements: 4.1, 4.2, 5.1, 5.2, 5.3, 5.4, 6.1, 6.2, 6.3, 6.4, 3.3, 15.1, 15.2, 15.5_
  - _Traceability: REQ-USR-02, REQ-USR-03, REQ-USR-B03, REQ-USR-B02, REQ-USR-12_

- [x] 5. Sostituzione completa con PUT [T-05]
  - Implementa UserService.replace_user e PUT /api/v1/users/{id} usando UserCreate. Preserva id/created_at, aggiorna updated_at e ripristina i default dei campi opzionali omessi.
  - Test sui tre backend: sostituzione e default, normalizzazione email, propria email consentita, email di altro utente ->409 senza mutazioni, utente inesistente ->404, campi obbligatori mancanti e tipi errati ->422, JSON malformato ->400.
  - Issue #1: tutti e tre i campi read-only nel body ->422 con record invariato. Validator sul successo e su 404/409/422; 400 PUT verificato direttamente, come spiegato nel design.
  - _Requirements: 7.1, 7.2, 7.3, 7.4, 7.5, 7.6, 7.7, 2.2, 2.4, 3.2, 13.3, 13.4, 14.1, 14.2, 14.3, 14.9, 15.1, 15.2, 15.5_
  - _Traceability: REQ-USR-04, REQ-USR-B01, REQ-USR-B02, REQ-USR-10, REQ-USR-11, REQ-USR-12_

- [ ] 6. Aggiornamento parziale con PATCH [T-06]
  - Implementa UserService.update_user e PATCH /api/v1/users/{id} usando UserUpdate. Aggiorna solo i campi inviati; {} restituisce la risorsa invariata, incluso updated_at.
  - Test sui tre backend: campo singolo, company null, preservazione degli altri valori, timestamp, propria email, normalizzazione, duplicato ->409 senza mutazioni, id inesistente ->404, campi extra/tipi errati ->422 e JSON malformato ->400.
  - Issue #1: parametrizza id/created_at/updated_at e verifica 422 con record invariato. Validator sul successo e su 404/409/422; 400 PATCH verificato direttamente.
  - _Requirements: 8.1, 8.2, 8.3, 8.4, 8.5, 2.3, 2.4, 3.2, 13.3, 13.4, 14.4, 14.5, 14.6, 14.7, 14.8, 14.9, 15.1, 15.2, 15.5_
  - _Traceability: REQ-USR-05, REQ-USR-B01, REQ-USR-B02, REQ-USR-10, REQ-USR-11, REQ-USR-12_

- [ ] 7. Cancellazione e verifica dei contratti [T-07]
  - Implementa UserService.delete_user e DELETE /api/v1/users/{id}: 204 senza body oppure 404. Non imporre requisiti sugli header non previsti dalla traccia.
  - Test sui tre backend: cancellazione, GET successivo 404, seconda cancellazione 404, riduzione del totale, riutilizzo dell'email liberata.
  - Completa i contract test per le sette operazioni dichiarate, con adattatore dict. Per 204 usa json=None. Verifica direttamente errori su path sconosciuti e metodi non previsti: il validator non può validare un'operazione assente dall'OpenAPI, quindi non chiamarlo su tali casi.
  - _Requirements: 9.1, 9.2, 11.1, 11.2, 15.1, 15.2, 15.5_
  - _Traceability: REQ-USR-06, REQ-USR-08, REQ-USR-12_

- [ ] 8. Abilitazione, collaudo e documentazione [T-08]
  - Abilita soltanto la chiave user in services.yaml, con cwd services/user-service e comando ../../.venv/bin/python -m app. Nessun event/registration/bonus.
  - Esegui make test-unit SERVICE=user-service e verifica coverage almeno 80%, linee e rami. Aggiungi soltanto eventuali test mancanti coerenti con i requisiti.
  - Esegui .venv/bin/python -m pytest tests/integration/test_user.py -v con memory, json e sqlite; DATA_DIR temporanea diversa per ogni esecuzione. Conserva risultati reali, verifica i checksum e assicurati che i processi siano terminati.
  - Se emergono bug, fermati e riporta riproduzione, requisito e fallimento. Non correggerli in questo task Spec: il coordinamento Git/issue e l'eventuale sessione Vibe seguono il processo della traccia; poi si riprende il collaudo.
  - Aggiorna README del servizio e stato del README root con avvio, configurazione, comandi e risultati misurati. Aggiorna BUGS.md con i test effettivi della issue #1, senza inventare bug o chiusure. Non creare il tag v1.0.0 o collaudo.txt finale.
  - _Requirements: 12.1, 12.2, 12.3, 12.4, 12.5, 12.6, 12.7, 12.8, 15.1, 15.2, 15.3, 15.4, 15.5_
  - _Traceability: REQ-USR-09, REQ-USR-12; collaudo IT-U01..IT-U08_

## Task Dependency Graph

```json
{
  "waves": [
    {
      "id": 0,
      "tasks": [
        "1"
      ]
    },
    {
      "id": 1,
      "tasks": [
        "2"
      ]
    },
    {
      "id": 2,
      "tasks": [
        "3"
      ]
    },
    {
      "id": 3,
      "tasks": [
        "4"
      ]
    },
    {
      "id": 4,
      "tasks": [
        "5"
      ]
    },
    {
      "id": 5,
      "tasks": [
        "6"
      ]
    },
    {
      "id": 6,
      "tasks": [
        "7"
      ]
    },
    {
      "id": 7,
      "tasks": [
        "8"
      ]
    }
  ]
}
```
