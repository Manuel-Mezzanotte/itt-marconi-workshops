# Verifica complessiva — fase 5

Data: 25 settembre 2026. Perimetro: requisiti, implementazione, test, configurazione,
storage, HTTP, tracciabilità e cronologia Git dei tre servizi obbligatori.
La consegna finale della fase 6 non è ancora eseguita.

## Esito della prova riproducibile

Il codice verificato è il commit **08e5f01572b9625c66adec54a98897dc86b0db21**.
È stato esportato con git archive in una directory temporanea: soltanto file
committati, senza .git, dati di sviluppo, cache o virtualenv del workspace.
Un nuovo ambiente Python 3.12.14 ha installato le 27 dipendenze esatte da
requirements.lock. Nessun pacchetto condiviso tramite system-site-packages.

Nella copia pulita sono stati eseguiti:

1. make check: ambiente, pip check, checksum delle due copie, raccolta del collaudo
   e controllo di tracciabilità.
2. make test con backend memory e DATA_DIR temporanea: unit/coverage di tutti i
   servizi, integrazione propria già parametrizzata sui tre backend e mandatory.
3. Mandatory con backend json e sqlite, ognuno con DATA_DIR temporanea separata.

| Verifica | Esito |
|---|---|
| User unit/contract | 599 passati |
| Event unit/contract | 431 passati |
| Registration unit/contract | 377 passati |
| Totale unit/contract | 1407 passati |
| Integrazione propria | 33 passati, 12 event e 21 registration |
| Mandatory memory | 27 passati, 10 bonus deselected, 0 skipped |
| Mandatory json | 27 passati, 10 bonus deselected, 0 skipped |
| Mandatory sqlite | 27 passati, 10 bonus deselected, 0 skipped |
| Checksum | 17 file nella root e gli stessi 17 sotto Exam/techconf-exam integri |
| Configurazione dipendenze | pip check senza errori |
| Cleanup | Porte 15001/15002/15003/15102/15103 libere dopo il collaudo |

| Servizio | Linee | Rami | Coverage combinata |
|---|---:|---:|---:|
| user-service | 602/610, 98,69% | 168/172, 97,67% | 98,47% |
| event-service | 385/385, 100% | 96/98, 97,96% | 99,59% |
| registration-service | 389/389, 100% | 89/90, 98,89% | 99,79% |

I report sono separati per servizio: non si sommano percentuali o moduli app
caricati da directory diverse. I documenti delle fasi precedenti conservano
i risultati storici riferiti ai rispettivi commit.

## Correzioni della revisione

| Issue | Problema | Correzione e prove |
|---|---|---|
| #7 | 254 casi utenti senza riferimenti espliciti raccolti da pytest | 0641efa: marker ereditabili; controllo prima fallito, poi zero casi invalidi |
| #8 | Errore del repository utenti restituito come HTML 500 | a4f09ad: JSON INTERNAL_ERROR con messaggio generico; regressione rossa e poi verde |
| #9 | Test dei default dipendente da PORT/STORAGE_BACKEND/DATA_DIR della shell | 6c34dc8: ambiente isolato nel test e verifica separata di env/override; prima 1 fallimento, poi suite verde con ambiente valorizzato |

I branch fix/user-7, fix/user-8 e fix/user-9 mantengono le correzioni distinte.
Il registro [BUGS.md](../BUGS.md) contiene nove problemi reali; il minimo richiesto
di due, incluso un difetto applicativo, è coperto. Le chiusure sono associate
all'integrazione dei commit su main.

Il commit b35546c aggiunge il controllo dei riferimenti e completa i marker
delle regole di business per event/registration. Le asserzioni esistenti non
sono state indebolite e il collaudo del docente rimane invariato.

## Requisiti e cronologia

La [matrice di tracciabilità](traceability.md) collega **41 requisiti** a task,
moduli/metodi e test rappresentativi. make check-traceability controlla:

- 599 casi user, 431 event, 377 registration e 33 integrazioni: **1440 casi propri**;
- nessun caso privo di ID valido e nessun riferimento a requisiti inesistenti;
- tutti i 15 requisiti user, 12 event e 14 registration presenti nei test del servizio.

Il controllo esamina i marker effettivamente ereditati, oltre a nome/docstring del
test. Non attribuisce copertura funzionale dalla sola presenza di un marker:
le asserzioni sono state riviste ed eseguite nelle suite.

La verifica tramite git merge-base --is-ancestor conferma commit distinti e ordinati:

| Servizio | Requirements | Design | Tasks | Primo codice | Task conclusi |
|---|---|---|---|---|---:|
| user | 9f29b5a | 587c2b7 | a7b0513 | 0bc1fd6 | 8/8 |
| event | 830c0e2 | 6590627 | 4e82f29 | 6735b79 | 7/7 |
| registration | 05f8f71 | 85bdeb1 | 6fbdfe0 | 4e50570 | 7/7 |

Ogni implementazione inizia dopo il commit di tasks; i merge conservano i commit
senza squash. Le quattro steering sono presenti e platform-standards riproduce
il §4 originale. L'hook esistente esegue make check, il cui comando è stato
verificato anche nella copia pulita.

## Architettura e interfacce

- Manifest completo: user, event, registration, ciascuno con cwd, comando e health.
- Porte e URL configurabili; default delle dipendenze soltanto nei moduli config.
  Timeout HTTP di 2 secondi verificato nei test dei client.
- Nessun import applicativo fra servizi e nessun client per DBMS esterni.
  Persistenza con json/sqlite3 e dati separati; venv, dati e log assenti dai file tracciati.
- Contratti verificati sulle 22 operazioni complessive: 7 user, 7 event, 8 registration,
  incluso PUT 405. I casi generali 400/500 non dichiarati sono testati direttamente.
- Integrazione reale con riferimenti assenti, ruolo organizzatore invalido,
  ciascuna dipendenza spenta, riavvii, capienza e richieste concorrenti.
- IT-J01 passa sui tre backend: ultimo posto, rifiuto, cancellazione, nuova
  iscrizione e statistiche coerenti.

## Limiti operativi già definiti

I server sono destinati a sviluppo/collaudo locale su macOS/Linux. JSON richiede
un solo processo scrittore per directory; i lock serializzano le richieste di
quel processo. SQLite serializza le prenotazioni con transazioni e indice
univoco parziale. Le chiamate HTTP non costituiscono una transazione distribuita
con modifiche concorrenti dell'evento. Sono scelte documentate, non garanzie
di esercizio in produzione.

## Evidenze e ripetizione

Dalla root: make check, make test; ripetizione mandatory sui tre backend con
la procedura isolata del [report fase 4](phase-4-verification.md).

Log locali esclusi da Git:
`.checks/phase5-clean-install.log`, `phase5-clean-check.log`,
`phase5-clean-test.log`, `phase5-clean-mandatory-json.log`,
`phase5-clean-mandatory-sqlite.log`, `phase5-clean-results.json`,
`phase5-clean-coverage-*.json`, `phase5-history.json` e le regressioni
`issue-7-*.log`, `issue-8-*.log`, `issue-9-*.log`.

Restano alla fase 6: documento finale di collaudo, controllo della checklist di
consegna, tag v1.0.0 su main e link definitivo. I due servizi bonus sono esclusi.
