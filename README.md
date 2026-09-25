# TechConf

Progetto per l'esame pratico Spec-Driven Development con Kiro.
Fork: [Manuel-Mezzanotte/itt-marconi-workshops](https://github.com/Manuel-Mezzanotte/itt-marconi-workshops).
Traccia: [Exam/Exam.MD](Exam/Exam.MD).

## Consegna v1.0.0

User-service, event-service e registration-service sono implementati. Le iscrizioni
verificano utenti/eventi via HTTP, acquisiscono il prezzo dall'evento e gestiscono
duplicati, capienza, cancellazioni e statistiche. Le specifiche precedono il codice;
i task sono completati con verifiche e commit distinti.

| Servizio | Casi unitari/contratto superati | Coverage con rami |
|---|---:|---:|
| user-service | 599 | 98,47% |
| event-service | 431 | 99,59% |
| registration-service | 377 | 99,79% |

Il collaudo obbligatorio del docente passa **27/27 su ciascuno dei tre backend**,
incluso il percorso completo IT-J01; zero skipped, dieci test bonus esclusi dalla
selezione mandatory. Passano inoltre **33 test propri con processi reali**,
inclusi concorrenza, ciascuna dipendenza spenta e persistenza ai riavvii.
La verifica è stata ripetuta da una copia dei soli file committati, con ambiente
virtuale nuovo e dipendenze installate da requirements.lock: 1407 unit/contract
e 33 integrazioni proprie superate. Il controllo automatico collega tutti i
41 requisiti a test raccolti da pytest.
Report: [fase 2](docs/phase-2-verification.md), [fase 3](docs/phase-3-verification.md),
[fase 4](docs/phase-4-verification.md) e [fase 5](docs/phase-5-verification.md).
La [matrice di tracciabilità](docs/traceability.md) collega requisiti, task, codice e test.

`services.yaml` abilita i tre servizi obbligatori. La consegna è identificata dal
[tag annotato v1.0.0](https://github.com/Manuel-Mezzanotte/itt-marconi-workshops/tree/v1.0.0)
su `main`. Il [collaudo finale](collaudo.txt) contiene l'output integrale delle
tre esecuzioni mandatory; la [checklist di consegna](docs/delivery-checklist.md)
riporta le verifiche concluse. I due servizi bonus non sono implementati.

## Ambiente riproducibile

Prerequisiti di esecuzione: Python **3.12**, Git; `make` e `shasum` per i comandi rapidi.

```bash
git clone --branch v1.0.0 https://github.com/Manuel-Mezzanotte/itt-marconi-workshops.git
cd itt-marconi-workshops
make setup
make check
```

`make setup` crea `.venv/` e installa le versioni di `requirements.lock`.
In alternativa:

```bash
python3.12 -m venv .venv
.venv/bin/python -m pip install -r requirements.lock
```

Le dipendenze runtime sono in `requirements.txt`; quelle di sviluppo in
`requirements-dev.txt`, che include i requisiti intatti del collaudo.
Il virtualenv è locale e non va committato. Non serve modificare il Python
predefinito del Mac. I comandi e il manifest sono predisposti per macOS/Linux.

## Workspace Kiro

Aprire questa root Git in Kiro, non `Exam/techconf-exam/`.
Gli steering in `.kiro/steering/` definiscono prodotto, stack, struttura e standard.
Il file degli standard riproduce il §4 della traccia.

L'hook `.kiro/hooks/check-workspace.json` esegue `make check` prima di un prompt
e salva l'esito in `.checks/pre-prompt.log`, escluso da Git. Verifica l'ambiente,
l'integrità del template, la raccolta del collaudo e la tracciabilità dei test
propri; non avvia microservizi.
Se l'hook risulta disattivato dopo aver autorizzato la cartella, ricaricare la
finestra di Kiro per inizializzare il workspace come trusted.

Per ogni servizio: requirements con EARS e commit, design e commit, tasks e
commit, quindi **Start task** uno alla volta con verifica e commit per task.
Non scrivere codice applicativo prima del commit di tasks.

## Servizi previsti e variabili

| Servizio | Porta di sviluppo | Dipendenze HTTP | Stato |
|---|---:|---|---|
| user-service | 5001 | nessuna | completo e collaudato sui tre backend |
| event-service | 5002 | user-service | completo e collaudato sui tre backend |
| registration-service | 5003 | user-service, event-service | completo e collaudato sui tre backend |
| feedback-service | 5004 | registration-service, event-service | bonus non avviato |
| notification-service | 5005 | user-service, registration-service | bonus non avviato |

| Variabile | Significato e default previsto dalla traccia |
|---|---|
| `PORT` | porta del servizio; default di sviluppo della tabella |
| `USER_SERVICE_URL` | default `http://localhost:5001` |
| `EVENT_SERVICE_URL` | default `http://localhost:5002` |
| `REGISTRATION_SERVICE_URL` | default `http://localhost:5003`, per i bonus |
| `STORAGE_BACKEND` | `memory` (default), `json`, `sqlite` |
| `DATA_DIR` | cartella dati; default `./data` relativo alla directory di avvio |

Il collaudo inietta porte 15001–15005 e URL coerenti; le istanze di resilienza
usano 15101+. Ogni processo deve rispettare l'ambiente ricevuto.

Il comando di avvio è `../../.venv/bin/python -m app`, dalla directory
`services/<servizio>`. Per avviare gli utenti:

```bash
cd services/user-service
PORT=5001 STORAGE_BACKEND=sqlite DATA_DIR=./data ../../.venv/bin/python -m app
```

In un secondo terminale dalla root:

```bash
cd services/event-service
PORT=5002 STORAGE_BACKEND=sqlite DATA_DIR=./data USER_SERVICE_URL=http://localhost:5001 ../../.venv/bin/python -m app
```

In un terzo terminale dalla root:

```bash
cd services/registration-service
PORT=5003 STORAGE_BACKEND=sqlite DATA_DIR=./data USER_SERVICE_URL=http://localhost:5001 EVENT_SERVICE_URL=http://localhost:5002 ../../.venv/bin/python -m app
```

Configurazione, API ed esempi: [user-service](services/user-service/README.md),
[event-service](services/event-service/README.md) e
[registration-service](services/registration-service/README.md).

## Comandi di verifica e test

| Comando dalla root | Scopo |
|---|---|
| `make check` | ambiente, checksum, raccolta del collaudo e tracciabilità |
| `make check-template` | verifica i 17 file protetti e i manifest |
| `make check-collection` | raccoglie i test forniti senza eseguirli |
| `make check-traceability` | controlla gli ID di ogni caso proprio e i 41 requisiti coperti |
| `make test-unit SERVICE=user-service` | unit e contract test del singolo servizio, coverage ≥80% |
| `make test-unit SERVICE=event-service` | unit e contract eventi con HTTP mockato, coverage ≥80% |
| `make test-unit SERVICE=registration-service` | unit/contract iscrizioni, concorrenza e coverage ≥80% |
| `make test-unit-all` | unit test dei tre servizi in processi separati |
| `make test-own-integration` | test propri in `tests/service_integration/` |
| `make acceptance` | collaudo dei servizi obbligatori |
| `make test` | unit, integrazione propria, collaudo obbligatorio, in sequenza |

Il collaudo obbligatorio è `.venv/bin/python -m pytest tests/integration -m mandatory -v`.
L'output finale sui tre backend è in [collaudo.txt](collaudo.txt); la procedura
per ripeterlo con dati isolati è nel [report della fase 4](docs/phase-4-verification.md).
`make test-own-integration` esegue già i casi event/registration su tutti i backend.
I comandi globali sono utilizzabili; i package app dei tre servizi vengono
testati in processi separati per evitare collisioni negli import.

## Git, bug e consegna

- Account di lavoro: `Manuel-Mezzanotte`; `origin` è il fork, `upstream` il docente.
- Preparazione: branch `chore/phase-1-setup`, integrazione in `main` dopo le verifiche.
- Servizi: branch dedicati, commit spec e task preservati senza squash.
- Bug d'implementazione: issue, branch `fix/<svc>-<issue#>`, regressione rossa,
  correzione in Vibe, verifiche verdi e commit con `closes #N`.
- Bug di specifica: aggiornare requirements, design e tasks e passare dalla spec.
- [BUGS.md](BUGS.md) contiene nove difetti reali corretti e verificati, con issue,
  requisiti, regressioni e commit. Tutte le nove issue sono chiuse e le
  correzioni integrate su `main`.
- Il tag annotato `v1.0.0` su `main` include `collaudo.txt`, documentazione,
  specifiche, implementazioni e test della consegna.

## Provenienza e file protetti

Il template era distribuito sotto `Exam/techconf-exam/`. I suoi file sono copiati
identici nella root per usare i percorsi richiesti dal collaudo e da Kiro; la
cartella originale resta intatta. Non sviluppare nella copia sotto `Exam/`.
Vedere [provenienza](docs/template-provenance.md) e [verifiche della fase 1](docs/phase-1-verification.md).

Nel materiale attuale vengono raccolti **37 test**, mentre la traccia ne menziona
49. È una differenza del template ricevuto, non una riduzione del collaudo.

Il precedente README dei workshop è conservato in
[docs/workshops-readme.md](docs/workshops-readme.md).
