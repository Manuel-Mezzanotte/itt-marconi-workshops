# Consegna TechConf v1.0.0

Data: 25 settembre 2026.
Repository: [Manuel-Mezzanotte/itt-marconi-workshops](https://github.com/Manuel-Mezzanotte/itt-marconi-workshops).
Versione di consegna: [v1.0.0](https://github.com/Manuel-Mezzanotte/itt-marconi-workshops/tree/v1.0.0),
tag annotato sul commit finale di main.
Perimetro: user-service, event-service e registration-service; bonus esclusi.

## Checklist della traccia

- [x] Quattro [steering](../.kiro/steering/) e almeno un
  [hook](../.kiro/hooks/check-workspace.json) configurato e provato.
  Il comando dell'hook, make check, supera anche la verifica finale.
- [x] Tre [spec](../.kiro/specs/), ciascuna con requirements, design e tasks:
  8 task utenti, 7 eventi e 7 iscrizioni completati.
  La [cronologia verificata](phase-5-verification.md#requisiti-e-cronologia)
  conserva requirements → design → tasks → codice in commit distinti.
- [x] [services.yaml](../services.yaml) completo e tre servizi avviabili con
  PORT e URL configurabili; memory, JSON e SQLite collaudati.
- [x] Unit e contract test con coverage superiore all'80% per ogni servizio.
- [x] 33 integrazioni proprie con processi reali per eventi e iscrizioni,
  inclusi riferimenti inesistenti, dipendenze spente, riavvii e concorrenza.
- [x] Collaudo mandatory eseguito sui tre backend; output integrale salvato
  in [collaudo.txt](../collaudo.txt).
- [x] [BUGS.md](../BUGS.md): nove problemi reali corretti e issue chiuse,
  inclusi difetti di implementazione con test di regressione.
- [x] [README](../README.md) con installazione, avvio dei tre servizi,
  variabili d'ambiente e comandi di test.
- [x] Contratti e collaudo del docente invariati: 17 checksum validi nella
  root e nella copia originale sotto Exam/techconf-exam; manifest identici.
- [x] Tag annotato v1.0.0 sul main del fork, pubblicato insieme ai commit.

## Risultati

| Servizio | Unit/contract superati | Coverage combinata linee e rami |
|---|---:|---:|
| user-service | 599 | 98,47% |
| event-service | 431 | 99,59% |
| registration-service | 377 | 99,79% |

I 1407 unit/contract e le 33 integrazioni proprie sono stati eseguiti nella
[prova della fase 5](phase-5-verification.md) da una copia dei soli file
committati, con virtualenv nuovo e dipendenze da requirements.lock.
La [matrice](traceability.md) e make check-traceability collegano tutti i
41 requisiti ai test: nessun caso proprio senza riferimento valido.

Il collaudo finale verifica il commit fa6c1da1a7b4b3a6a94c5449fec977056a757c49:
27/27 mandatory su memory, 27/27 su JSON e 27/27 su SQLite, incluso IT-J01.
In totale 81 esecuzioni passate, nessun mandatory saltato; i 10 test bonus
sono esclusi in ciascuna esecuzione. Dati temporanei eliminati e processi
terminati dopo ogni prova.

Codice, test e comandi di esecuzione non cambiano rispetto alla prova pulita
del commit 08e5f01572b9625c66adec54a98897dc86b0db21. La fase 6 aggiunge
soltanto l'output del collaudo e aggiorna la documentazione di consegna.
I report delle fasi precedenti conservano gli esiti riferiti a quelle fasi.

Per ripetere le verifiche: make setup, make check e make test dalla root.
Per il mandatory sui tre backend usare la
[procedura con dati isolati](phase-4-verification.md).
