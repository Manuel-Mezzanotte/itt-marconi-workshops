# Registro dei bug

Il primo problema è emerso durante la revisione dei requisiti di user-service;
il secondo durante la verifica dell'entrypoint del T-01. Le issue restano aperte
fino alla verifica delle rispettive correzioni e dei test di regressione.

| ID | Issue | Trovato da | Tipo | Requisito | Causa radice | Test di regressione | Commit |
|---|---|---|---|---|---|---|---|
| BUG-01 | [#1](https://github.com/Manuel-Mezzanotte/itt-marconi-workshops/issues/1) | Revisione di requirements.md | spec | REQ-USR-01, REQ-USR-10 | La bozza chiedeva di ignorare id e timestamp del client, ma il contratto vieta quei campi | Da eseguire nei task di validazione di POST/PUT/PATCH | Issue aperta |
| BUG-02 | [#2](https://github.com/Manuel-Mezzanotte/itt-marconi-workshops/issues/2) | Verifica dell'entrypoint con FLASK_DEBUG=1 | impl | REQ-USR-09, design e T-01 | app.run non disabilita esplicitamente debug e reloader; il test intercetta Flask.run e non le opzioni effettive del server | Riproduzione nella issue; regressione persistente e fix Vibe ancora da eseguire | Issue aperta |

Registrare soltanto difetti reali. Per il processo di gestione e la distinzione
tra bug di implementazione e di specifica, vedere `.kiro/steering/structure.md`
e `Exam/Exam.MD`, §6.5.
