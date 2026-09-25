# Verifica della fase 3 — event-service

Data: 25 settembre 2026. Ambiente: macOS, Python 3.12.14, pytest 8.4.2.
Ambito: event-service e collegamento reale con user-service; registration e bonus
restano esclusi. Non è il collaudo finale dell'intera piattaforma.

## Cronologia e task

| Passaggio | Commit | Contenuto |
|---|---|---|
| Requirements | 830c0e2 | Requisiti EARS, campi, endpoint, errori e tracciabilità |
| Design | 6590627 | HTTP, validazione, stato, repository e verifiche |
| Tasks | 4e82f29 | Sette task sequenziali prima del codice |
| T-01 | 6735b79 | Configurazione, errori, factory, health e avvio |
| T-02 | 9713bae | Repository intercambiabili e aggiornamento atomico |
| T-03 | 712387d | Input, client user e creazione eventi |
| T-04 | 3ba7fd2 | GET singolo/lista, filtri e paginazione |
| T-05 | 11e1519 | PUT/PATCH, date, riferimenti e transizioni |
| T-06 | 8f4625d | DELETE e contratti completi |
| T-07 | Commit di questo report | Integrazione, manifest, collaudo e documentazione |

## Risultati

| Verifica | Esito |
|---|---|
| Unit/contract event-service | 431 passati |
| Linee event-service | 385/385, 100% |
| Rami event-service | 96/98, 97,96% |
| Coverage combinata | 99,59%, soglia 80% superata |
| Integrazione propria | 12 passati, quattro scenari per backend |
| Collaudo user+event, memory | 16 passati, 0 skipped |
| Collaudo user+event, json | 16 passati, 0 skipped |
| Collaudo user+event, sqlite | 16 passati, 0 skipped |
| Checksum | 17 file integri nella root e nella copia originale |
| Ambiente | Python 3.12, dipendenze presenti, pip check superato |
| Cleanup collaudo | Porte 15001, 15002 e 15102 libere dopo ogni esecuzione |

Le chiamate unit sono mockate con responses; la suite propria e quella del
docente eseguono HTTP tra processi reali. Il collaudo include IT-U01..IT-U08 e
IT-E01..IT-E08, incluso il 503 con dipendenza irraggiungibile.

I test propri verificano anche l'arresto effettivo di user-service dopo la
creazione di un evento, l'assenza di modifiche dopo errori e il recupero esatto
dei dati JSON/SQLite dopo riavvio. Directory temporanee separate e cleanup nel
teardown; nessun test punta ai dati di sviluppo.

Le sette operazioni API sono verificate con assert_matches_contract. I 400 di
PUT/PATCH e i metodi non dichiarati sono controllati direttamente, senza
modificare il contratto. Le coppie di stato sono verificate su entrambi i metodi
di modifica e sui tre storage; un test concorrente controlla che una pubblicazione
non possa far tornare attivo un evento cancellato.

## Ripetizione

Dalla root:

```bash
make test-unit SERVICE=event-service
make test-own-integration
make check
```

Collaudo con dati isolati su tutti i backend:

```bash
.venv/bin/python - <<'PY'
import os
import subprocess
import tempfile

for backend in ("memory", "json", "sqlite"):
    with tempfile.TemporaryDirectory(prefix=f"techconf-{backend}-") as directory:
        env = {**os.environ, "STORAGE_BACKEND": backend, "DATA_DIR": directory}
        print(f"Backend: {backend}", flush=True)
        subprocess.run(
            [".venv/bin/python", "-m", "pytest",
             "tests/integration/test_user.py", "tests/integration/test_event.py", "-v"],
            env=env,
            check=True,
        )
PY
```

I log locali del collaudo, coverage e integrità sono in
`.checks/event-t07-*.log` e `.checks/event-t07-coverage.json`, esclusi da Git.

## Scelte e limiti

EventCreate ammette status esplicito alla creazione. PUT applica i default dello
schema, perciò omettere status su un evento pubblicato viene rifiutato come
tentativo published→draft. PATCH controlla date e transizione sul record corrente
dentro la transazione. Un PATCH vuoto non modifica timestamp né chiama user.

JSON è previsto per un solo processo scrittore per directory; i lock coprono
le richieste concorrenti dello stesso processo. SQLite conserva documenti JSON
in una tabella e filtra i record in memoria: il costo della lista cresce con il
numero di eventi, scelta esplicita per questo piccolo progetto.

Nessuna nuova issue è stata necessaria in questa fase. Le sei issue della fase 2
rimangono nel [registro dei bug](../BUGS.md). Registration-service, collaudo
completo e tag v1.0.0 restano alle fasi successive.
