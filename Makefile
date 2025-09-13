## WSL 환경

SHELL := /bin/bash

VENV := .venv
PY   := $(VENV)/bin/python
PIP  := $(PY) -m pip 
PORT := 8000

where ?= 

init:
	wsl

run:
	$(PY) manage.py runserver 0.0.0.0:$(PORT)

migrate:
	$(PY) manage.py migrate

venv:
	test -d $(VENV) || python3 -m venv $(VENV)
	$(PIP) -q install -U pip

install-all: venv
	$(PIP) install -q django requests python-dotenv whitenoise

request:
	curl -X $(method) -H "Content-Type: application/json" -d '$(data)' http://localhost:$(PORT)/api/$(where)/

clean:
	rm -rf $(VENV) __pycache__ */__pycache__

#vercel
collectstatic:
	$(PY) manage.py collectstatic --noinput

vercel-preview:
	npx -y vercel@latest

vercel-prod:
	npx -y vercel@latest --prod