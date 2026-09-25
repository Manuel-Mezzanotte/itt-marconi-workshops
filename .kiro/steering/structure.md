---
inclusion: always
---

# Struttura, responsabilità e processo

## Aggiornamento dell'esecutore — 25 settembre 2026

Dal T-04 di user-service si usa Codex, su indicazione del partecipante che riferisce
l'autorizzazione del docente. Questa decisione prevale sulle istruzioni Kiro
operative sotto riportate. Restano ordine delle spec, singoli task, test, commit
e workflow dei bug; non si inventano esecuzioni nell'IDE. Vedere
`docs/execution-process.md` per il confine tra le attività Kiro e Codex.

## Repository e confini

Un solo repository: il fork `Manuel-Mezzanotte/itt-marconi-workshops`.
Il template del docente era in `Exam/techconf-exam/`: una copia identica è stata
portata nella root per rispettare il workspace Kiro e i percorsi del collaudo.
La cartella originale `Exam/` rimane intatta come riferimento, non si sviluppa lì.
La provenienza e i controlli sono descritti in `docs/template-provenance.md`.

Il monorepo mantiene insieme contratti, cinque possibili servizi, specifiche,
collaudo e tag di consegna. Repository separati complicano inutilmente il manifest
e il versionamento del collaudo fornito.

```text
.kiro/steering/                     regole comuni
.kiro/hooks/                        automazioni Kiro del progetto
.kiro/specs/<servizio>/             requirements, design, tasks della singola spec
services/<servizio>/app/            codice di quel servizio
services/<servizio>/tests/          suoi test unitari e di contratto
tests/service_integration/          integrazione propria tra processi reali
tests/integration/                 collaudo del docente, immutabile
contracts/                         contratti e validator del docente, immutabili
docs/                              provenienza, verifiche e documentazione
services.yaml                      soli servizi implementati
requirements*.txt / requirements.lock
Makefile / pyproject.toml
BUGS.md / README.md / CHECKSUMS.sha256
```

Nessun import del codice di un altro servizio e nessun accesso ai suoi file dati.
La comunicazione fra servizi passa esclusivamente dalle rispettive API HTTP.
Controllare gli import nelle revisioni di task. Un servizio può essere estratto
dal monorepo senza trascinarsi la business logic degli altri.

## Codice comune

Inizialmente ogni servizio conserva i propri piccoli helper per errori,
paginazione, validazione e chiamate HTTP. È una duplicazione deliberata per
mantenere indipendenza e limitare gli import tra servizi. La coerenza è verificata
dai contratti e dai test. Non creare una libreria condivisa di business logic.
Un'eventuale estrazione di sola infrastruttura richiederà una decisione documentata
e task dedicati, non avverrà implicitamente durante la generazione.

## Struttura interna prevista

- `app/__init__.py`: application factory, dipendenze e registrazione delle route.
- `app/__main__.py`: avvio con la porta dalla configurazione.
- `app/config.py`: lettura e validazione dell'ambiente, una sola volta.
- `app/routes.py`: parsing HTTP, adattamento delle risposte, niente regole di dominio.
- `app/service.py`: regole `REQ-*-B*` e coordinamento delle operazioni.
- `app/validation.py`: validazione esplicita degli input secondo contratto.
- `app/repositories/`: interfaccia minima e implementazioni memory, JSON, SQLite.
- `app/clients.py`: richieste HTTP alle dipendenze, timeout e mapping degli errori;
  assente dove non serve, come in user-service.

I file Python verranno creati solo dai task delle rispettive spec. Le cartelle
vuote della fase di preparazione non sono servizi avviabili.

Il design del singolo servizio definirà modelli, firme, gestione di unicità,
concorrenza e transazioni. Queste decisioni devono preservare l'interfaccia comune
del repository, così il cambio di storage non modifica `service.py`.
I client HTTP separati consentono ai test di simulare requests con `responses`.

## Ambiente e avvio

Un unico `.venv/` e un lock delle dipendenze: tutti i servizi hanno lo stack
imposto dalla traccia. È una scelta di semplicità, non una dipendenza tra i domini.
Se in futuro servissero versioni incompatibili, si valuteranno ambienti separati
con un cambiamento esplicito della configurazione.

Ogni servizio usa lo stesso comando `../../.venv/bin/python -m app` con `cwd`
`services/<servizio>` nel manifest. I percorsi sono relativi e funzionano anche
quando la root contiene spazi. `PORT` e `*_SERVICE_URL` sono forniti dal collaudo;
non sostituirli con le porte di sviluppo. Abilitare in `services.yaml` soltanto
servizi che hanno un entrypoint e un `/health` effettivamente funzionanti.

## Test e isolamento

I tre package si chiamano tutti `app`: eseguire gli unit test di ciascun servizio
in un processo pytest distinto per evitare collisioni in `sys.modules`.

- Singolo servizio: `make test-unit SERVICE=user-service` (analogamente per gli altri).
- Tutti gli unit test: `make test-unit-all`.
- Integrazione propria: `make test-own-integration`.
- Collaudo obbligatorio: `make acceptance`.
- Intera piattaforma: `make test`, nell'ordine unit, integrazione propria, collaudo.
- Preparazione: `make check`, senza dichiarare superati test funzionali non eseguiti.

I test propri avviano i processi con fixture, porte libere e `DATA_DIR` temporanea;
li terminano sempre nel teardown, anche in caso di fallimento. Il collaudo del
docente usa invece le porte 15001–15005 e 15101+; non modificarlo.
I comandi completi di test potranno passare solo dopo l'implementazione. Durante
la fase 1 non ci sono unit test applicativi, né una percentuale di coverage da dichiarare.

## Spec e tracciabilità

Una spec per servizio in `.kiro/specs/user-service/`, `.kiro/specs/event-service/`,
`.kiro/specs/registration-service/`. Questa granularità coincide con i contratti
e consente di completare e collaudare i servizi in ordine di dipendenza.

`structure.md` contiene regole trasversali. `design.md` contiene le scelte del
servizio: componenti, modelli, repository, client, errori e strategia di test.
Ogni requisito ha un ID stabile `REQ-...`; i task e i test lo citano esplicitamente.
Se Kiro richiede riferimenti numerici nel proprio formato, mantenere anche la
corrispondenza con gli ID della traccia: non sostituirli senza una mappa.

Prima di implementare qualsiasi servizio:
1. Requirements con EARS e copertura dei campi, endpoint, regole ed errori; revisione
   e commit `spec(<svc>): requirements`.
2. Design; revisione e commit `spec(<svc>): design`.
3. Task atomici inclusivi dei test, con ID `T-01`, `T-02`, ecc. e riferimenti ai
   requisiti; revisione e commit `spec(<svc>): tasks`.
4. Eseguire da Kiro **Start task**, un task alla volta. Controllare diff e verifiche,
   poi commit `feat(<svc>): <descrizione> [T-01]` (oppure `test(...)` per soli test).

Non usare Run all tasks, Quick Spec, Design-First o Vibe per creare l'applicazione.
Nessun codice applicativo prima del commit di tasks. Date reali dei commit,
nessuna ricostruzione o retrodatazione della cronologia.

Il task attivo delimita anche i metodi del service e le route: non anticipare
operazioni assegnate ai task successivi. Eseguire il lavoro nella sessione Spec
aperta da Start task, mantenendo il flusso nativo di esecuzione di Kiro e una
sola revisione per task. Limitare le letture duplicate. Ogni bug riprodotto va segnalato:
fermarsi prima della correzione, che seguirà il workflow dedicato sotto.

## Branch e bug

Preparazione su `chore/phase-1-setup`, da integrare in `main` dopo le verifiche.
Per i servizi usare branch dedicati `feat/user-service`, `feat/event-service`,
`feat/registration-service`, mantenendo tutti i commit spec/task nel merge, senza squash.
Il nome di questi branch organizzativi è una scelta locale; il branch dei fix
`fix/<svc>-<issue#>` è previsto dalla traccia.

Ogni bug effettivamente individuato o test di collaudo fallito va registrato in una
issue del fork, con requisito, riproduzione, atteso e ottenuto.
- Implementazione: branch `fix/<svc>-<issue#>`, Vibe con il testo dell'issue e il
  fallimento; prima test di regressione rosso, poi fix, poi unit e collaudo verdi.
- Specifica: aggiornare requirements, design e tasks; eseguire il nuovo task dalla
  spec, senza correggere la specifica in Vibe.
- Commit `fix(<svc>): <descrizione> (closes #N)`, merge su `main`, aggiornamento `BUGS.md`.

Servono almeno due bug reali chiusi, di cui almeno uno d'implementazione. Non
inserire deliberatamente difetti né inventare issue per raggiungere il numero.
GitHub CLI deve avere come repository predefinito il fork dell'account
`Manuel-Mezzanotte`. Push a `origin`; `upstream` è il riferimento del docente.

## Dati e consegna

File JSON/SQLite in `DATA_DIR`; `data/`, `.it-logs/`, `.checks/`, `.venv/`, file
`.env`, cache e coverage locali sono esclusi da Git. I test usano dati temporanei.
`CHECKSUMS.sha256`, `contracts/` e `tests/integration/` non vengono modificati;
si verificano sia la copia operativa sia quella originale sotto `Exam/`.
Il tag `v1.0.0` e `collaudo.txt` appartengono alla consegna finale, non alla preparazione.
