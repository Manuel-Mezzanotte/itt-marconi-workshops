# Tracciabilità dei requisiti

La tabella collega tutti i 41 ID delle specifiche a task, implementazione e
test rappresentativi. I nomi dei metodi e dei test permettono una ricerca diretta
con rg. I percorsi della tabella sono relativi alla cartella del servizio.

La verifica eseguibile è `make check-traceability`, inclusa in `make check`.
Raccoglie i casi in processi pytest separati; rifiuta test senza riferimenti,
ID non dichiarati e requisiti senza test associati. Non modifica né raccoglie
la suite protetta del docente. I riferimenti pytest sono marker req, nomi o
docstring del singolo test; i marker sulle classi sono ereditati dai casi.

Gli elenchi completi di nodi parametrizzati e requisiti sono rigenerati in
`.checks/traceability-<gruppo>.json`; non sono mantenuti a mano.
Questa verifica controlla i collegamenti, non sostituisce la revisione delle
asserzioni né l'esecuzione dei test.

## User-service

Base: [services/user-service](../services/user-service).
Spec: [requirements](../.kiro/specs/user-service/requirements.md),
[design](../.kiro/specs/user-service/design.md),
[tasks](../.kiro/specs/user-service/tasks.md).

| Requisito | Task | Implementazione | Test rappresentativo |
|---|---|---|---|
| REQ-USR-01 | T-03 | app/service.py: create_user; app/routes.py: create_user | tests/test_routes_post.py: TestPostUsersCreate |
| REQ-USR-B01 | T-02/03/05/06 | app/repositories/: create/update e vincolo email | tests/test_repositories.py: TestEmailUniqueness, TestConcurrentEmail |
| REQ-USR-B02 | T-03/04/05/06 | app/validation.py: validate_user_create/update; service.list_users | tests/test_service.py: test_create_email_normalized |
| REQ-USR-02 | T-04 | app/service.py: get_user | tests/test_routes_get.py: test_get_existing_and_missing |
| REQ-USR-03 | T-02/04 | app/service.py: list_users; repositories.list | tests/test_routes_get.py: test_pagination_stable_and_total_before_slice |
| REQ-USR-B03 | T-02/04 | repositories.list; service.list_users | tests/test_repositories.py: TestList; tests/test_routes_get.py: test_filters_combine_and_preserve_empty_email |
| REQ-USR-04 | T-05 | app/service.py: replace_user | tests/test_routes_put.py: test_put_replaces_fields_resets_defaults_and_refreshes_timestamp |
| REQ-USR-05 | T-06 | app/service.py: update_user | tests/test_routes_patch.py: test_empty_patch_preserves_entire_resource |
| REQ-USR-06 | T-07 | service.delete_user; repositories.delete | tests/test_routes_delete.py: test_delete_removes_only_target_and_releases_email |
| REQ-USR-07 | T-01 | app/__init__.py: health | tests/test_app.py: test_health_matches_contract |
| REQ-USR-08 | T-01/07 | app/errors.py: register_error_handlers | tests/test_app.py: test_unknown_path_error_format; test_internal_storage_error_returns_uniform_json_without_details |
| REQ-USR-09 | T-01/02/08 | app/config.py, __main__.py, repositories/ | tests/test_config.py; tests/test_repositories.py: TestPersistence; tests/test_startup.py |
| REQ-USR-10 | T-03/05/06 | app/service.py: _format_timestamp, UUID e conservazione created_at | tests/test_service.py: test_create_timestamp_microseconds_six_digits; test_create_timestamp_microseconds_one |
| REQ-USR-11 | T-03/05/06 | app/validation.py: validate_user_create/update | tests/test_validation.py: TestUserCreateValidation, TestUserUpdateValidation |
| REQ-USR-12 | T-01..08 | tests/, validator del contratto, Makefile | tests/test_contract.py: test_complete_user_lifecycle_matches_contract |

## Event-service

Base: [services/event-service](../services/event-service).
Spec: [requirements](../.kiro/specs/event-service/requirements.md),
[design](../.kiro/specs/event-service/design.md),
[tasks](../.kiro/specs/event-service/tasks.md).

| Requisito | Task | Implementazione | Test rappresentativo |
|---|---|---|---|
| REQ-EVT-01 | T-03 | app/validation.py: validate_event; service.create | tests/test_post.py: test_post_contract_defaults_and_explicit_status |
| REQ-EVT-B01 | T-03/05 | app/clients.py: require_organizer | tests/test_post.py: test_upstream_errors_do_not_create |
| REQ-EVT-B02 | T-03/05 | app/clients.py: controllo role | tests/test_post.py: test_upstream_errors_do_not_create |
| REQ-EVT-B03 | T-03/05 | validation.validate_dates; service._save_changes | tests/test_updates.py: test_patch_dates_validated_after_merge |
| REQ-EVT-B04 | T-03/05 | validation.validate_transition; repositories.update | tests/test_updates.py: test_state_transitions_on_both_methods; test_concurrent_publication_cannot_revive_cancelled_event |
| REQ-EVT-02 | T-02/04 | service.get/list; repositories.paginate | tests/test_get.py: test_single_event_and_missing; test_pagination_and_filters |
| REQ-EVT-B06 | T-02/04 | validation.validate_query; repositories.paginate | tests/test_get.py: test_empty_city_is_distinct_from_no_filter |
| REQ-EVT-03 | T-05/06 | service.replace/patch/delete e update atomico | tests/test_updates.py; tests/test_contract.py: test_complete_lifecycle_contract |
| REQ-EVT-B05 | T-03/05/07 | clients.require_organizer, timeout/mapping errori | tests/test_post.py: test_dependency_transport_and_invalid_json |
| REQ-EVT-04 | T-01/03..06 | app/errors.py, routes.py, __init__.py | tests/test_app.py: test_health_without_dependency; test_uniform_http_errors |
| REQ-EVT-05 | T-01/02/07 | app/config.py, __main__.py, repositories/ | tests/test_repositories.py: test_persistence_and_memory_isolation; test_concurrent_updates_do_not_lose_changes |
| REQ-EVT-06 | T-01..07 | tests/, contratti e integrazione reale | tests/test_contract.py: test_complete_lifecycle_contract |

## Registration-service

Base: [services/registration-service](../services/registration-service).
Spec: [requirements](../.kiro/specs/registration-service/requirements.md),
[design](../.kiro/specs/registration-service/design.md),
[tasks](../.kiro/specs/registration-service/tasks.md).

| Requisito | Task | Implementazione | Test rappresentativo |
|---|---|---|---|
| REQ-REG-01 | T-03 | validation.validate_create; service.create | tests/test_post.py: test_creation_amount_and_contract |
| REQ-REG-B01 | T-03/06 | clients.get_user e _get | tests/test_post.py: test_dependency_errors |
| REQ-REG-B02 | T-03/06 | clients.get_event e _get | tests/test_post.py: test_dependency_errors |
| REQ-REG-B03 | T-03 | service.create: status published | tests/test_post.py: test_event_not_open |
| REQ-REG-B06 | T-03/05/06 | service.create: amount acquisito dall'evento | tests/test_updates_contract.py: test_amount_remains_historical |
| REQ-REG-B04 | T-02/03/05/06 | repositories.reserve/check_slot; indice parziale SQLite | tests/test_repositories.py: test_concurrent_reservations_have_one_winner |
| REQ-REG-B05 | T-02/03/05/06 | reserve/count_confirmed sotto lock/transazione | tests/test_repositories.py: test_sqlite_distinct_instances_share_capacity_and_unique_constraint |
| REQ-REG-02 | T-02/04 | service.get/list; validation.validate_query | tests/test_get_stats.py: test_filters_pagination_and_totals |
| REQ-REG-B07 | T-02/05/06 | repositories.change_status/update_status | tests/test_updates_contract.py: test_cancellation_is_idempotent_and_cannot_reactivate |
| REQ-REG-03 | T-02/05 | service.patch/delete; routing PUT non consentito | tests/test_updates_contract.py: test_unknown_ids_and_put_405 |
| REQ-REG-B08 | T-04 | service.stats; repositories.count_confirmed | tests/test_get_stats.py: test_stats_counts_and_capacity_reduction; test_stats_missing_or_unavailable_event |
| REQ-REG-B09 | T-03/04/06 | clients._get/get_event | tests/test_post.py: test_transport_and_body_failures |
| REQ-REG-04 | T-01/02/05/06/07 | config, errors, __main__, repositories | tests/test_app.py; tests/test_repositories.py: test_filter_pagination_and_persistence |
| REQ-REG-05 | T-01..07 | tests/, validator e integrazione reale | tests/test_updates_contract.py: test_all_eight_contract_operations_in_capacity_journey |

## Integrazione reale e collaudo

[test_event_http.py](../tests/service_integration/test_event_http.py) collega
REQ-EVT-B01/B02/B05/06 a processi reali. [test_registration_http.py](../tests/service_integration/test_registration_http.py)
collega riferimenti, capienza, duplicati, prezzo storico, cancellazioni,
statistiche e dipendenze a richieste HTTP reali e riavvii.

Il collaudo protetto copre IT-U01..U08, IT-E01..E08, IT-R01..R10 e IT-J01.
Non gli vengono aggiunti marker o modifiche: la sua tracciabilità resta quella
degli ID forniti dal docente. I 27 mandatory sono eseguiti separatamente dai test
propri e ripetuti sui tre backend.
