# Registro dei bug

Sei problemi reali individuati durante specifica, implementazione e collaudo di
user-service. Tutte le correzioni sono verificate: 597 unit/contract superati e
IT-U01..IT-U08 superati su memory, JSON e SQLite. Le issue vengono chiuse con
l'integrazione delle correzioni su main.

| ID | Issue | Trovato da | Tipo | Requisito | Causa radice | Test di regressione | Commit |
|---|---|---|---|---|---|---|---|
| BUG-01 | [#1](https://github.com/Manuel-Mezzanotte/itt-marconi-workshops/issues/1) | Revisione di requirements.md | spec | REQ-USR-01, REQ-USR-10 | La bozza chiedeva di ignorare id e timestamp del client, ma il contratto vieta quei campi | test_post_readonly_field_422_no_create; test_put_invalid_fields_leave_record_unchanged e test_patch_invalid_fields_do_not_mutate parametrizzati su id/created_at/updated_at, con verifica del record invariato | spec 9f29b5a, POST 8f5b067, PUT 471e282, PATCH d129017; collaudo superato |
| BUG-02 | [#2](https://github.com/Manuel-Mezzanotte/itt-marconi-workshops/issues/2) | Verifica dell'entrypoint con FLASK_DEBUG=1 | impl | REQ-USR-09, design e T-01 | app.run non disabilitava esplicitamente debug e reloader; il test intercettava Flask.run e non le opzioni effettive del server | test_main_ignores_flask_debug_env: fallimento osservato prima del fix in Kiro Default/Vibe; poi 25 test verdi senza warning | 9aeb2a5, branch fix/user-2; collaudo superato sui tre backend |
| BUG-03 | [#3](https://github.com/Manuel-Mezzanotte/itt-marconi-workshops/issues/3) | Revisione e riproduzione della validazione nel T-03 | impl | REQ-USR-11 | Il confronto del ruolo con un frozenset avviene prima del controllo del tipo: array e oggetti causano TypeError | Regressioni HTTP rosse in Kiro, controllo del tipo in entrambi i validatori e test di atomicita; poi 318 test verdi | 44aadb5, branch fix/user-3; collaudo superato sui tre backend |
| BUG-04 | [#4](https://github.com/Manuel-Mezzanotte/itt-marconi-workshops/issues/4) | Prova del blueprint POST del T-03 con Flask test_client | impl | REQ-USR-01, REQ-USR-11, design Errori e parsing | Location dipende da una route GET non ancora implementata; UnsupportedMediaType non viene convertito nell'errore JSON previsto | Regressioni rosse su tre backend per Location e Content-Type; fix Kiro Default/Vibe, poi 297 test verdi | f0cf6c8, branch fix/user-4; collaudo superato sui tre backend |
| BUG-05 | [#5](https://github.com/Manuel-Mezzanotte/itt-marconi-workshops/issues/5) | Revisione del formato timestamp del T-03 | impl | REQ-USR-10, design UserService | Lo slicing [:-3] elimina tre cifre dei microsecondi; il test del formato replica la precisione errata | Nove casi rossi prima del fix Kiro Default/Vibe, poi formato a sei cifre e 324 test verdi | fd7dc26, branch fix/user-5; collaudo superato sui tre backend |
| BUG-06 | [#6](https://github.com/Manuel-Mezzanotte/itt-marconi-workshops/issues/6) | Collaudo T-08: 8 errori di setup del backend JSON | impl | REQ-USR-09, REQ-USR-07 | HTTPServer.server_bind esegue getfqdn sull'indirizzo locale e attende il resolver prima di accettare richieste | test_main_starts_when_reverse_dns_is_unavailable: rosso prima del fix; poi 597 unit/contract verdi e IT-U01..IT-U08 verdi su memory, JSON e SQLite | ce5b863, branch fix/user-6; socket TCP passato a Werkzeug tramite fd |
| BUG-07 | [#7](https://github.com/Manuel-Mezzanotte/itt-marconi-workshops/issues/7) | Audit di tracciabilità della fase 5 | impl (test) | REQ-USR-12.5 | Riferimenti presenti solo nelle descrizioni di classe/modulo, non esposti sui singoli casi pytest | scripts/check_traceability.py: 254 casi invalidi prima, zero dopo; 597 unit e 8 casi di collaudo user superati | branch fix/user-7; marker req espliciti ed ereditabili |
| BUG-08 | [#8](https://github.com/Manuel-Mezzanotte/itt-marconi-workshops/issues/8) | Revisione della gestione errori della fase 5 | impl | Platform Standards §4, design user-service Errori e parsing | Un'eccezione inattesa dal repository arrivava all'handler HTML 500 predefinito di Flask | test_internal_storage_error_returns_uniform_json_without_details: rosso con text/html, poi JSON INTERNAL_ERROR senza dettagli interni; 598 unit e 27 mandatory passati | branch fix/user-8; handler HTTP 500 uniforme |
| BUG-09 | [#9](https://github.com/Manuel-Mezzanotte/itt-marconi-workshops/issues/9) | Verifica della suite con ambiente valorizzato | impl (test) | REQ-USR-09, REQ-USR-12 | test_defaults assumeva PORT/STORAGE_BACKEND/DATA_DIR assenti e falliva con configurazione esterna valida | Prima 1 failed/11 passed con PORT=15501 e backend sqlite; poi 599 unit e 27 mandatory verdi nello stesso ambiente, con test esplicito di ambiente/override | branch fix/user-9; fixture isola l'ambiente dei test di configurazione |

Registrare soltanto difetti reali. Per il processo di gestione e la distinzione
tra bug di implementazione e di specifica, vedere `.kiro/steering/structure.md`
e `Exam/Exam.MD`, §6.5.

## Verifiche della fase 3

Non sono emersi nuovi difetti nelle verifiche eseguite su event-service:
431 unit/contract, 12 integrazioni proprie e collaudo user+event 16/16 per
backend. Non sono state aggiunte issue artificiali. Il modello di avvio introdotto
con la correzione BUG-06 è stato adottato anche per event-service e verificato
con resolver indisponibile e FLASK_DEBUG=1.

## Verifiche della fase 4

Non sono emersi nuovi difetti nelle verifiche eseguite su registration-service.
Passano 377 unit/contract del servizio, 33 integrazioni reali complessive e
27 test mandatory per ciascun backend. Le regressioni delle fasi precedenti
rimangono verdi: user-service 597 casi, event-service 431.
Nessuna nuova issue aggiunta; le sei correzioni registrate restano chiuse.
