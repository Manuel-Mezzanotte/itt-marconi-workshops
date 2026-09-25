# Provenienza del template

- Repository del docente: https://github.com/r3recube/itt-marconi-workshops
- Fork di lavoro: https://github.com/Manuel-Mezzanotte/itt-marconi-workshops
- Commit upstream iniziale: `18eaf23a71761e255305935b854a4d0a3886257c`.
- Traccia: `Exam/Exam.MD`.
- Template distribuito: `Exam/techconf-exam/`.

La traccia descrive un repository `techconf-exam` autonomo, ma il materiale
pubblico fornito si trova nella sottocartella del repository dei workshop.
Il fork mantiene il rapporto GitHub con il repository del docente.

Per usare la root Git come workspace Kiro e consentire al collaudo di trovare
`services.yaml` nella root, sono state copiate senza alterazioni `contracts/`,
`tests/integration/`, `CHECKSUMS.sha256` e `services.example.yaml`.
La `.gitignore` iniziale è stata copiata e poi estesa perché non è un file protetto.

I 17 file elencati nel manifest SHA-256 della copia operativa sono identici a
quelli originali. Anche `CHECKSUMS.sha256` è identico. Il contenuto originale sotto
`Exam/techconf-exam/` non è stato modificato, spostato o cancellato.

L'importazione del template è isolata nel commit `6b3cf62`. I file Python di quel
commit sono esclusivamente il validator e il collaudo forniti dal docente, non
implementazioni dei servizi. Per lo sviluppo si usano soltanto i percorsi nella
root; la copia sotto `Exam/` è un riferimento e non va inclusa nella raccolta
generale dei test. Il README originario dei workshop è in `docs/workshops-readme.md`;
i suoi link relativi originali partono dalla root.

## Verifica

Eseguire `make check-template`: controlla entrambe le copie e confronta i due
manifest SHA-256. Non rigenerare i checksum per far passare una modifica.

## Differenza rilevata nella descrizione del collaudo

La traccia menziona 49 casi. In questo commit del template, pytest raccoglie
**37 test** dai file forniti. La differenza è documentata; non sono stati aggiunti,
rimossi o modificati test del docente per cambiare quel numero. La raccolta dei
test non dimostra che le API funzionino.
