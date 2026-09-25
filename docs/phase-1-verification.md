# Verifica fase 1 — preparazione

Data: 2026-09-25. Scope: preparazione del repository e dell'ambiente;
nessuna implementazione applicativa, nessuna spec di servizio e nessun task eseguito.

## Account e provenienza

- Fork: `Manuel-Mezzanotte/itt-marconi-workshops`, parent `r3recube/itt-marconi-workshops`.
- GitHub API conferma il fork e i permessi di push dell'account `Manuel-Mezzanotte`.
- Autore e committer locali: `Manuel <manuel.mezzanotte@marconirovereto.it>`;
  email coincidente con quella pubblica dell'account GitHub verificato.
- `origin` punta al fork; repository predefinito di GitHub CLI impostato sul fork.
- Branch di preparazione: `chore/phase-1-setup`; commit reali e integrazione senza squash.
- Baseline upstream: `18eaf23a71761e255305935b854a4d0a3886257c`.
- Importazione del template nella root: `6b3cf62`, copie byte per byte.

## Controlli eseguiti

| Verifica | Esito |
|---|---|
| Python del virtualenv | 3.12.14 |
| Installazione da `requirements.lock` con `make setup` | riuscita |
| Import di Flask, requests, pytest, pytest-cov, responses, PyYAML, jsonschema | riuscito |
| `pip check` | nessuna dipendenza incompatibile |
| `shasum -a 256 -c CHECKSUMS.sha256` dalla root | 17/17 file OK |
| Stesso controllo sotto `Exam/techconf-exam/` | 17/17 file OK |
| Confronto dei due manifest SHA-256 | identici |
| Diff di `Exam/` rispetto a upstream | vuoto |
| Standard in `platform-standards.md` rispetto al §4 della traccia | testo identico, oltre al frontmatter Kiro |
| Quattro steering e `inclusion: always` | verificati |
| YAML del manifest, JSON dell'hook e TOML di pytest/coverage | validi |
| Manifest letto dall'harness originale | root corretta, zero servizi attivi |
| Validator originale sui cinque contratti `/health` | accetta risposta conforme e rifiuta risposta invalida |
| Raccolta collaudo completo | 37 test |
| Raccolta con marker mandatory | 27 selezionati, 10 deselezionati |
| Codice Python sotto `services/` | nessun file |
| `.kiro/specs/` | nessuna spec creata |
| `collaudo.txt` e tag finale `v1.0.0` | non creati |

Le risposte sintetiche usate per verificare il validator sono dati temporanei
passati all'helper: non sono risposte di server TechConf e non provano il funzionamento
applicativo. Anche la raccolta dei test non è un collaudo funzionale.

## Verifica effettiva in Kiro

La root Git è aperta in Kiro IDE 1.1.70. Nel pannello sono visibili i quattro
steering del workspace e l'hook `Controllo ambiente e integrita prima del prompt`.
Dopo la fiducia alla sola cartella è stata ricaricata la finestra per attivare gli hook.

È stato inviato un prompt di sola lettura, chiedendo di confermare stack,
servizi obbligatori, sequenza pre-codice, file protetti e manifest vuoto.
Kiro ha confermato correttamente tutti i punti, senza creare file, spec o servizi.
La sessione si intitola `TechConf Fase 1: Verifica Preparazione Read-Only`.

L'interfaccia ha mostrato `Run Command Hook`; il comando ha prodotto
`.checks/pre-prompt.log` con ambiente valido, checksum OK e `37 tests collected`.
Il log è locale, ignorato da Git; il riepilogo qui è committato.

L'hook usa il trigger `UserPromptSubmit` riconosciuto dall'app installata.
Non esegue unit test inesistenti e non avvia server: controlla l'ambiente e il
materiale protetto prima delle richieste. Il costo stimato mostrato da Kiro per
la verifica di sola lettura è stato 0,12 crediti.

## Vincoli rispettati e lavoro futuro

- I Python presenti nella root sono soltanto validator e test immutabili del docente.
- Cartelle app/tests predisposte per user, event e registration, con soli `.gitkeep`.
- `services.yaml` mantiene `services: {}` fino alla prima implementazione funzionante.
- Nessun test di integrazione applicativo eseguito, nessuna coverage dichiarata.
- Il numero 37 deriva dalla versione distribuita del template; la traccia menziona
  49. La differenza resta documentata senza modificare il materiale protetto.
- `BUGS.md` è predisposto e vuoto: il requisito dei due bug reali non è ancora soddisfatto.
- Prossima fase: requirements-first di user-service in Kiro, prima di qualsiasi codice.
