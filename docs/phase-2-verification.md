# Verifica della fase 2 — user-service

Data: 25 settembre 2026. Ambiente: macOS, Python 3.12.14, pytest 8.4.2.
Ambito: soltanto user-service. Le fasi event-service e registration-service non
sono state anticipate; nessun tag finale o collaudo dell'intera piattaforma.

## Task e implementazione

| Task | Risultato | Commit |
|---|---|---|
| T-04 | GET singolo/lista, filtri role/email, paginazione | 19f9479 |
| T-05 | PUT, default, conservazione id/created_at, unicità | 471e282 |
| T-06 | PATCH, campi parziali, oggetto vuoto senza mutazioni | d129017 |
| T-07 | DELETE e contratti delle sette operazioni API | f079b20 |
| T-08 | Manifest user, collaudo su tre backend e documentazione | Commit di questo report |

I task precedenti e le specifiche restano nella cronologia. La checklist viene
spuntata dopo implementazione e test. Non sono stati modificati i metadati delle
sessioni precedenti.

## Risultati misurati

| Verifica | Esito |
|---|---|
| Unit e contract test | 597 passati |
| Linee | 599/607, 98,68% |
| Rami | 168/172, 97,67% |
| Coverage combinata | 98,46%, soglia 80% superata |
| Collaudo docente con memory | 8 passati, 0 skipped |
| Collaudo docente con json | 8 passati, 0 skipped |
| Collaudo docente con sqlite | 8 passati, 0 skipped |
| Checksum | 17 file integri nella root e nella copia originale |
| Ambiente | Python 3.12, dipendenze disponibili, pip check superato |
| Cleanup | Porta 15001 libera dopo ogni esecuzione, directory temporanee eliminate |

Gli unit test parametrizzati esercitano tutti i backend. I contratti coprono
health, POST, GET lista, GET singolo, PUT, PATCH e DELETE, oltre agli errori
dichiarati. I 400 di PUT/PATCH e i path/metodi non dichiarati sono verificati
direttamente: non si aggiungono operazioni agli OpenAPI del docente.

## Ripetizione delle verifiche

Dalla root:

```bash
make test-unit SERVICE=user-service
make check
```

Per eseguire il collaudo con dati separati senza lasciare file nel progetto:

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
            [".venv/bin/python", "-m", "pytest", "tests/integration/test_user.py", "-v"],
            env=env,
            check=True,
        )
PY
```

Il manifest dichiara solo user, con comando `../../.venv/bin/python -m app`.
La suite avvia il processo sulla PORT=15001 assegnata e lo termina nel teardown.
I comandi sono per macOS/Linux. La persistenza JSON prevede un solo processo
scrittore per directory; i test di concorrenza verificano richieste nello stesso
processo e vincoli atomici del repository.

## Problema emerso durante il collaudo

Il primo tentativo JSON ha prodotto otto errori di setup: l'avvio restava
bloccato in socket.getfqdn, chiamato da HTTPServer.server_bind. Nessuna richiesta
funzionale JSON è stata eseguita in quel tentativo. La diagnosi ha individuato
una dipendenza dall'attesa del resolver locale, non un errore di persistenza.

La [issue #6](https://github.com/Manuel-Mezzanotte/itt-marconi-workshops/issues/6)
è stata riprodotta con una regressione inizialmente rossa. Il fix ce5b863
sul branch fix/user-6 passa a Werkzeug un socket TCP già aperto, evitando la
risoluzione inversa durante il bind senza modificare le librerie installate,
la configurazione del Mac o il collaudo del docente.

Dopo il fix sono passati unit/contract, coverage e tutti e tre i collaudi.
Le regressioni verificano anche health via HTTP reale, PORT configurata,
assenza di debugger/reloader con FLASK_DEBUG=1 e chiusura dei socket.

I log locali sono in `.checks/user-t08-*.log` e `.checks/issue-6-*.log`;
sono esclusi da Git. [BUGS.md](../BUGS.md) collega i sei difetti ai requisiti,
alle regressioni e ai commit.
