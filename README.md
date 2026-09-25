# TechConf

Progetto per l'esame pratico Spec-Driven Development con Kiro.
Fork: [Manuel-Mezzanotte/itt-marconi-workshops](https://github.com/Manuel-Mezzanotte/itt-marconi-workshops).
Traccia: [Exam/Exam.MD](Exam/Exam.MD).

## Stato: fase 3 completata — user-service ed event-service

User-service ed event-service espongono CRUD, filtri e paginazione. Event-service
verifica l'organizzatore tramite HTTP e applica validazioni di date, prezzo,
capienza e ciclo di vita. Le specifiche precedono il codice; i task sono
completati con verifiche e commit distinti.

| Servizio | Casi unitari/contratto superati | Coverage con rami |
|---|---:|---:|
| user-service | 597 | 98,46% |
| event-service | 431 | 99,59% |

Il collaudo del docente user+event passa **16/16 su ciascuno dei tre backend**,
senza skipped. Passano inoltre **12 test propri con processi reali** per
successo, riferimenti/ruoli invalidi, dipendenza spenta e persistenza ai riavvii.
Report: [fase 2](docs/phase-2-verification.md) e [fase 3](docs/phase-3-verification.md).

`services.yaml` abilita user ed event. Registration-service resta alla fase 4:
il collaudo dell'intera piattaforma non è ancora completato. Un test skipped
non equivale a un test superato.

## Ambiente riproducibile

Prerequisiti: Python **3.12**, Git, Kiro IDE; `make` e `shasum` per i comandi rapidi.

```bash
git clone https://github.com/Manuel-Mezzanotte/itt-marconi-workshops.git
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
l'integrità del template e la raccolta del collaudo; non avvia microservizi.
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
| registration-service | 5003 | user-service, event-service | non implementato |
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

Configurazione, API ed esempi: [user-service](services/user-service/README.md)
ed [event-service](services/event-service/README.md).

## Comandi di verifica e test

| Comando dalla root | Scopo |
|---|---|
| `make check` | ambiente, checksum di entrambe le copie, raccolta del collaudo |
| `make check-template` | verifica i 17 file protetti e i manifest |
| `make check-collection` | raccoglie i test forniti senza eseguirli |
| `make test-unit SERVICE=user-service` | unit e contract test del singolo servizio, coverage ≥80% |
| `make test-unit SERVICE=event-service` | unit e contract eventi con HTTP mockato, coverage ≥80% |
| `make test-unit-all` | unit test dei tre servizi in processi separati |
| `make test-own-integration` | test propri in `tests/service_integration/` |
| `make acceptance` | collaudo dei servizi obbligatori |
| `make test` | unit, integrazione propria, collaudo obbligatorio, in sequenza |

Per il collaudo dei servizi completati:
`.venv/bin/python -m pytest tests/integration/test_user.py tests/integration/test_event.py -v`.
Il report della fase 3 contiene la ripetizione isolata sui tre backend.
`make test-own-integration` esegue i test reali di event-service su tutti i backend.
I comandi globali per i tre servizi richiedono anche la fase 4.

## Git, bug e consegna

- Account di lavoro: `Manuel-Mezzanotte`; `origin` è il fork, `upstream` il docente.
- Preparazione: branch `chore/phase-1-setup`, integrazione in `main` dopo le verifiche.
- Servizi: branch dedicati, commit spec e task preservati senza squash.
- Bug d'implementazione: issue, branch `fix/<svc>-<issue#>`, regressione rossa,
  correzione in Vibe, verifiche verdi e commit con `closes #N`.
- Bug di specifica: aggiornare requirements, design e tasks e passare dalla spec.
- [BUGS.md](BUGS.md) contiene sei difetti reali corretti e verificati, con issue,
  requisiti, regressioni e commit. La chiusura delle issue segue l'integrazione
  delle correzioni su `main`.
- `collaudo.txt` e tag `v1.0.0` appartengono alla consegna finale; non vengono
  creati nella preparazione.

## Provenienza e file protetti

Il template era distribuito sotto `Exam/techconf-exam/`. I suoi file sono copiati
identici nella root per usare i percorsi richiesti dal collaudo e da Kiro; la
cartella originale resta intatta. Non sviluppare nella copia sotto `Exam/`.
Vedere [provenienza](docs/template-provenance.md) e [verifiche della fase 1](docs/phase-1-verification.md).

Nel materiale attuale vengono raccolti **37 test**, mentre la traccia ne menziona
49. È una differenza del template ricevuto, non una riduzione del collaudo.

Il precedente README dei workshop è conservato in
[docs/workshops-readme.md](docs/workshops-readme.md).
