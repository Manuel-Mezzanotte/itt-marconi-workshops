# Registro dei bug

Il primo problema è emerso durante la revisione dei requisiti di user-service.
La correzione della specifica è pronta; la issue resterà aperta fino alla verifica
dei test sull'implementazione.

| ID | Issue | Trovato da | Tipo | Requisito | Causa radice | Test di regressione | Commit |
|---|---|---|---|---|---|---|---|
| BUG-01 | [#1](https://github.com/Manuel-Mezzanotte/itt-marconi-workshops/issues/1) | Revisione di requirements.md | spec | REQ-USR-01, REQ-USR-10 | La bozza chiedeva di ignorare id e timestamp del client, ma il contratto vieta quei campi | Da eseguire nei task di validazione di POST/PUT/PATCH | Issue aperta |

Registrare soltanto difetti reali. Per il processo di gestione e la distinzione
tra bug di implementazione e di specifica, vedere `.kiro/steering/structure.md`
e `Exam/Exam.MD`, §6.5.
