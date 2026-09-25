# user-service

Anagrafica utenti: task T-01..T-08 completati. Il servizio è abilitato in
`services.yaml` e non ha dipendenze HTTP da altri servizi.

## Avvio

Dalla root, dopo `make setup`:

```bash
cd services/user-service
PORT=5001 STORAGE_BACKEND=memory ../../.venv/bin/python -m app
```

| Variabile | Default | Significato |
|---|---|---|
| PORT | 5001 | Intero tra 1 e 65535 |
| STORAGE_BACKEND | memory | memory, json oppure sqlite |
| DATA_DIR | ./data | Directory dei dati, relativa al cwd |

JSON usa `users.json`; SQLite usa `users.db`. Entrambi conservano i dati
ai riavvii; memory riparte vuoto. Per JSON si prevede un solo processo scrittore
per directory dati. I tre backend condividono la stessa business logic.

L'avvio su macOS/Linux usa un socket locale passato al server Werkzeug, evitando
la risoluzione DNS inversa bloccante. Ascolta su 127.0.0.1, senza debug/reloader
anche con FLASK_DEBUG=1. È un server locale di sviluppo e collaudo.

## API

| Metodo | Percorso | Comportamento |
|---|---|---|
| GET | /health | Stato del servizio |
| POST | /api/v1/users | Creazione, 201 e Location |
| GET | /api/v1/users | Lista con page, page_size, role, email |
| GET | /api/v1/users/{id} | Singolo utente, 200 o 404 |
| PUT | /api/v1/users/{id} | Sostituzione completa |
| PATCH | /api/v1/users/{id} | Aggiornamento parziale |
| DELETE | /api/v1/users/{id} | 204 senza body, oppure 404 |

POST e PUT richiedono first_name, last_name ed email. Company è opzionale,
role assume attendee se omesso. L'email è salvata in minuscolo e deve essere
univoca senza distinzione di maiuscole. Il server genera UUID v4 e timestamp UTC.
I campi id, created_at e updated_at inviati dal client vengono rifiutati.

PUT ripristina company=null e role=attendee quando omessi. PATCH preserva
i campi assenti; un oggetto vuoto restituisce la risorsa invariata, timestamp incluso.
Le richieste invalide e i conflitti non modificano il record.

La paginazione parte da page=1, page_size=20, massimo 100. Il totale è calcolato
dopo i filtri e prima della paginazione. Role ed email si combinano con AND;
email è normalizzata anche nelle query. L'ordine è created_at e id crescenti.
Una pagina oltre il totale restituisce items vuoto.

Esempio di creazione:

```bash
curl -i http://127.0.0.1:5001/api/v1/users \
  -H 'Content-Type: application/json' \
  -d '{"first_name":"Ada","last_name":"Lovelace","email":"ada@example.com","role":"organizer"}'
```

Gli errori seguono `{"error":{"code":"...","message":"...","details":{}}}`:
400 JSON malformato/Content-Type errato, 404 risorsa assente, 405 metodo non
previsto, 409 EMAIL_ALREADY_EXISTS, 422 VALIDATION_ERROR. Anche gli errori interni
producono JSON: 500 INTERNAL_ERROR, senza dettagli dell'eccezione nel body.

## Verifiche

Dalla root:

```bash
make test-unit SERVICE=user-service
.venv/bin/python -m pytest tests/integration/test_user.py -v
make check
```

Risultati aggiornati alla fase 5, 25 settembre 2026: **599 casi unitari e di contratto
superati**, coverage **98,47% includendo i rami** (linee 98,69%, rami 97,67%).
IT-U01..IT-U08: **8/8 superati per ciascuno dei tre backend**, con processi
reali, dati temporanei separati e cleanup verificato.

Specifiche: `.kiro/specs/user-service/`. Report:
[verifica fase 2](../../docs/phase-2-verification.md) e
[verifica complessiva fase 5](../../docs/phase-5-verification.md).
