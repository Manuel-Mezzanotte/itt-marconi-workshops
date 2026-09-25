# Integrazione propria

Questa cartella ospiterà i test con servizi reali scritti durante le fasi event
e registration. Il collaudo del docente rimane in `tests/integration/`.

Usare fixture pytest con processi separati, porte libere, `DATA_DIR` temporanee
e teardown garantito. Per ogni servizio con dipendenze: successo, riferimento
inesistente (422), dipendenza spenta (503), con riferimenti ai requisiti.

Nella fase 1 non sono presenti test applicativi. `make test-own-integration`
sarà utilizzabile quando verranno implementati i relativi task.
