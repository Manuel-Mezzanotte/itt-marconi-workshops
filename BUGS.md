# Registro dei bug

Il primo problema è emerso durante la revisione dei requisiti di user-service;
il secondo durante la verifica dell'entrypoint del T-01. Il secondo è corretto
e verificato con gli unit test; le issue restano aperte fino al collaudo del servizio.

| ID | Issue | Trovato da | Tipo | Requisito | Causa radice | Test di regressione | Commit |
|---|---|---|---|---|---|---|---|
| BUG-01 | [#1](https://github.com/Manuel-Mezzanotte/itt-marconi-workshops/issues/1) | Revisione di requirements.md | spec | REQ-USR-01, REQ-USR-10 | La bozza chiedeva di ignorare id e timestamp del client, ma il contratto vieta quei campi | Da eseguire nei task di validazione di POST/PUT/PATCH | Issue aperta |
| BUG-02 | [#2](https://github.com/Manuel-Mezzanotte/itt-marconi-workshops/issues/2) | Verifica dell'entrypoint con FLASK_DEBUG=1 | impl | REQ-USR-09, design e T-01 | app.run non disabilitava esplicitamente debug e reloader; il test intercettava Flask.run e non le opzioni effettive del server | test_main_ignores_flask_debug_env: fallimento osservato prima del fix in Kiro Default/Vibe; poi 25 test verdi senza warning | 9aeb2a5, branch fix/user-2; collaudo completo previsto nel T-08 |

Registrare soltanto difetti reali. Per il processo di gestione e la distinzione
tra bug di implementazione e di specifica, vedere `.kiro/steering/structure.md`
e `Exam/Exam.MD`, §6.5.
