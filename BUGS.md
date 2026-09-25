# Registro dei bug

Il primo problema è emerso durante la revisione dei requisiti di user-service;
il secondo durante la verifica dell'entrypoint del T-01. Il secondo è corretto
e verificato con gli unit test; le issue restano aperte fino al collaudo del servizio.

| ID | Issue | Trovato da | Tipo | Requisito | Causa radice | Test di regressione | Commit |
|---|---|---|---|---|---|---|---|
| BUG-01 | [#1](https://github.com/Manuel-Mezzanotte/itt-marconi-workshops/issues/1) | Revisione di requirements.md | spec | REQ-USR-01, REQ-USR-10 | La bozza chiedeva di ignorare id e timestamp del client, ma il contratto vieta quei campi | Da eseguire nei task di validazione di POST/PUT/PATCH | Issue aperta |
| BUG-02 | [#2](https://github.com/Manuel-Mezzanotte/itt-marconi-workshops/issues/2) | Verifica dell'entrypoint con FLASK_DEBUG=1 | impl | REQ-USR-09, design e T-01 | app.run non disabilitava esplicitamente debug e reloader; il test intercettava Flask.run e non le opzioni effettive del server | test_main_ignores_flask_debug_env: fallimento osservato prima del fix in Kiro Default/Vibe; poi 25 test verdi senza warning | 9aeb2a5, branch fix/user-2; collaudo completo previsto nel T-08 |
| BUG-03 | [#3](https://github.com/Manuel-Mezzanotte/itt-marconi-workshops/issues/3) | Revisione e riproduzione della validazione nel T-03 | impl | REQ-USR-11 | Il confronto del ruolo con un frozenset avviene prima del controllo del tipo: array e oggetti causano TypeError | Regressioni HTTP rosse in Kiro, controllo del tipo in entrambi i validatori e test di atomicita; poi 318 test verdi | Branch fix/user-3; collaudo finale pendente |
| BUG-04 | [#4](https://github.com/Manuel-Mezzanotte/itt-marconi-workshops/issues/4) | Prova del blueprint POST del T-03 con Flask test_client | impl | REQ-USR-01, REQ-USR-11, design Errori e parsing | Location dipende da una route GET non ancora implementata; UnsupportedMediaType non viene convertito nell'errore JSON previsto | Regressioni rosse su tre backend per Location e Content-Type; fix Kiro Default/Vibe, poi 297 test verdi | f0cf6c8, branch fix/user-4; collaudo finale pendente |
| BUG-05 | [#5](https://github.com/Manuel-Mezzanotte/itt-marconi-workshops/issues/5) | Revisione del formato timestamp del T-03 | impl | REQ-USR-10, design UserService | Lo slicing [:-3] elimina tre cifre dei microsecondi; il test del formato replica la precisione errata | Riprodotto 123456 microsecondi ->123; regressione e fix Vibe da eseguire | Issue aperta |

Registrare soltanto difetti reali. Per il processo di gestione e la distinzione
tra bug di implementazione e di specifica, vedere `.kiro/steering/structure.md`
e `Exam/Exam.MD`, §6.5.
