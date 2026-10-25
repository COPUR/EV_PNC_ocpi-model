# OCPI_SPEC_DIR: checkout of COPUR/ocpi at the commit in tools/ocpi-spec-pin.json
OCPI_SPEC_DIR ?= ../ocpi

.PHONY: generate check test spec-checkout

generate:
	python3 tools/ocpi_to_schema.py --spec $(OCPI_SPEC_DIR)
	python3 tools/gen_kotlin.py
	tools/gen_python.sh

check:
	python3 tools/ocpi_to_schema.py --spec $(OCPI_SPEC_DIR) --check
	python3 tools/gen_kotlin.py --check
	tools/gen_python.sh --check

test:
	cd generated/python && OCPI_SPEC_DIR=$(OCPI_SPEC_DIR) uv run --extra test python -m pytest -q
	cd generated/kotlin && OCPI_SPEC_DIR=$(OCPI_SPEC_DIR) gradle test --no-daemon -q

# fetch the pinned spec commit into ./.spec
spec-checkout:
	rm -rf .spec && git init -q .spec
	git -C .spec fetch -q --depth 1 https://github.com/COPUR/ocpi $$(python3 -c "import json;print(json.load(open('tools/ocpi-spec-pin.json'))['commit'])")
	git -C .spec checkout -q FETCH_HEAD
