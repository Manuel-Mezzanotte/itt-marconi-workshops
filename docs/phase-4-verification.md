# Verifica della fase 4 — registration-service

Data: 25 settembre 2026. Ambiente: macOS, Python 3.12.14, pytest 8.4.2.
Ambito: registration-service e flusso dei tre servizi obbligatori. Restano
revisione complessiva e consegna delle fasi 5/6; nessun tag finale in questa fase.

## Cronologia

| Passaggio | Commit | Contenuto |
|---|---|---|
| Requirements | 05f8f71 | EARS, riferimenti, capienza, importo, stati e statistiche |
| Design | 85bdeb1 | Componenti, HTTP, transazioni e verifica |
| Tasks | 6fbdfe0 | Sette task prima del codice |
| T-01 | 4e50570 | Configurazione, health, errori e avvio |
| T-02 | 9256e30 | Repository con capienza/duplicati atomici |
| T-03 | 6d81217 | Validazione, client user/event e POST |
| T-04 | 3e7729b | GET, query e statistiche |
| T-05 | 633d2ae | PATCH, DELETE, PUT 405 e contratti completi |
| T-06 | dc16437 | Integrazione reale, concorrenza HTTP e riavvii |
| T-07 | Commit di questo report | Manifest, collaudo e documentazione |

## Risultati misurati

| Verifica | Esito |
|---|---|
| Unit/contract registration | 377 passati |
| Linee registration | 389/389, 100% |
| Rami registration | 89/90, 98,89% |
| Coverage combinata registration | 99,79%, soglia 80% superata |
| Unit/contract user | 597 passati, coverage 98,46% |
| Unit/contract event | 431 passati, coverage 99,59% |
| Integrazione propria | 33 passati: 21 registration + 12 event |
| Mandatory memory | 27 passati, 10 bonus deselected, 0 skipped |
| Mandatory json | 27 passati, 10 bonus deselected, 0 skipped |
| Mandatory sqlite | 27 passati, 10 bonus deselected, 0 skipped |
| Checksum | 17 file integri nella root e nella copia originale |
| Ambiente | Python 3.12, import e pip check superati |
| Cleanup collaudo | Porte 15001/15002/15003/15102/15103 libere dopo ogni esecuzione |

Il totale degli unit/contract dei tre processi è 1405 casi. La suite del docente
contiene 37 test: la selezione mandatory ne esegue 27 ed esclude i dieci bonus.
Questo conteggio non attribuisce esiti ai servizi facoltativi non implementati.

## Casi verificati

- Unit HTTP con responses per entrambe le dipendenze: riferimenti assenti,
  timeout, connessione rifiutata, status inattesi e dati non validi.
- Otto operazioni del contratto, incluso PUT 405; rifiuto dei campi controllati
  dal server, UUID normalizzati, errori senza mutazioni.
- Sedici tentativi concorrenti al repository per l'ultimo posto o stessa coppia:
  esattamente un vincitore. SQLite anche con due istanze distinte sullo stesso file.
- Otto richieste HTTP concorrenti tra processi reali: un solo 201, sette 409.
- Solo confirmed occupano posti; cancellazione e DELETE liberano il posto,
  una nuova iscrizione dopo cancellazione ha un nuovo id.
- Prezzo storico invariato dopo modifica dell'evento. Statistiche con capienza
  corrente, 404 per evento assente, disponibilità zero se la capienza viene ridotta.
- Arresto separato di ciascuna dipendenza, mantenendo disponibili le operazioni
  locali; recupero delle iscrizioni confirmed/cancelled dopo riavvio JSON/SQLite.
- IT-J01: due posti, terzo utente rifiutato, cancellazione, terzo utente accettato,
  statistiche finali coerenti. Passato su tutti i backend.

## Ripetizione

Dalla root:

```bash
make test-unit-all
make test-own-integration
make check
```

Collaudo obbligatorio su dati temporanei separati:

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
            [".venv/bin/python", "-m", "pytest", "tests/integration", "-m", "mandatory", "-v"],
            env=env,
            check=True,
        )
PY
```

Log locali esclusi da Git:
`.checks/registration-t06-integration.log`,
`.checks/registration-t07-all-unit.log`,
`.checks/registration-t07-mandatory-*.log`,
`.checks/registration-t07-integrity.log` e
`.checks/registration-t07-coverage.json`.

## Perimetro dell'atomicità

Memory/JSON serializzano le richieste nel singolo processo; JSON prevede un
processo scrittore per directory. SQLite usa BEGIN IMMEDIATE e un indice univoco
parziale per le coppie confirmed, anche con connessioni/istanze distinte.
Le chiamate HTTP avvengono prima della transazione locale: capienza, prezzo e
stato dell'evento sono quelli della risposta ricevuta. Non si implementa una
transazione distribuita con modifiche concorrenti dell'evento.

Non sono emersi nuovi bug nelle verifiche eseguite. I sei difetti reali delle
fasi precedenti restano nel registro; le loro regressioni sono state rieseguite.
I sorgenti user/event e il materiale del docente non sono stati modificati.
