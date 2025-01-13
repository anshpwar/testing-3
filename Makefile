PY ?= python3

.PHONY: build test test-c
build:
	@true

test-c:
	@true

test:
	$(PY) manage.py test tests --settings=hospital.settings.test --noinput
