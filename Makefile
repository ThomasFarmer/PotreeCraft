PYTEST ?= pytest
RUFF ?= ruff
PB_TOOL ?= pb_tool
PLUGIN_DIR ?= qgis_plugin

.PHONY: help lint lint-plugin lint-tests compile deploy zip unit-test qgis-dialog-test test

help:
	@echo "make lint              Run linting for the whole plugin and tests"
	@echo "make lint-plugin       Run linting for the full qgis_plugin package"
	@echo "make lint-tests        Run linting for the tests package"
	@echo "make compile           Run pb_tool compile in qgis_plugin"
	@echo "make deploy            Run pb_tool deploy in qgis_plugin"
	@echo "make zip               Run pb_tool zip in qgis_plugin"
	@echo "make unit-test         Run plain pytest tests that do not need QGIS fixtures"
	@echo "make qgis-dialog-test  Run the pytest-qgis dialog smoke test"
	@echo "make test              Run the full starter test suite"

lint:
	$(RUFF) check qgis_plugin tests

lint-plugin:
	$(RUFF) check qgis_plugin

lint-tests:
	$(RUFF) check tests

compile:
	cd $(PLUGIN_DIR) && $(PB_TOOL) compile

deploy:
	cd $(PLUGIN_DIR) && $(PB_TOOL) deploy

zip:
	cd $(PLUGIN_DIR) && $(PB_TOOL) zip

unit-test:
	$(PYTEST) -q tests/test_plugin_factory.py

qgis-dialog-test:
	$(PYTEST) -q tests/test_plugin_qgis.py

test:
	$(PYTEST) -q tests/test_plugin_factory.py tests/test_plugin_qgis.py
