PYTHON := $(CURDIR)/.venv/bin/python
SERVICE ?=
MANDATORY_SERVICES := user-service event-service registration-service

.PHONY: setup check check-env check-template check-collection check-traceability test test-unit test-unit-all test-own-integration acceptance

setup:
	python3.12 -m venv .venv
	"$(PYTHON)" -m pip install -r requirements.lock

check: check-env check-template check-collection check-traceability

check-env:
	"$(PYTHON)" -c 'import sys; assert sys.version_info[:2] == (3, 12), sys.version; import flask, requests, pytest, pytest_cov, responses, yaml, jsonschema; print("Python 3.12 e dipendenze disponibili")'
	"$(PYTHON)" -m pip check

check-template:
	shasum -a 256 -c CHECKSUMS.sha256
	cd Exam/techconf-exam && shasum -a 256 -c CHECKSUMS.sha256
	cmp CHECKSUMS.sha256 Exam/techconf-exam/CHECKSUMS.sha256

check-collection:
	"$(PYTHON)" -m pytest tests/integration --collect-only -q

check-traceability:
	"$(PYTHON)" scripts/check_traceability.py

test-unit:
	@case "$(SERVICE)" in user-service|event-service|registration-service|feedback-service|notification-service) ;; *) echo 'Specificare SERVICE, ad esempio: make test-unit SERVICE=user-service'; exit 2 ;; esac
	cd "services/$(SERVICE)" && "$(PYTHON)" -m pytest -c ../../pyproject.toml tests --cov=app --cov-branch --cov-report=term-missing --cov-fail-under=80

test-unit-all:
	@set -eu; for service in $(MANDATORY_SERVICES); do $(MAKE) test-unit SERVICE="$$service"; done

test-own-integration:
	"$(PYTHON)" -m pytest tests/service_integration -v

acceptance:
	"$(PYTHON)" -m pytest tests/integration -m mandatory -v

test:
	$(MAKE) test-unit-all
	$(MAKE) test-own-integration
	$(MAKE) acceptance
