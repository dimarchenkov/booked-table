.PHONY: install migrate test

install:
	pip install -r requirements.txt

migrate:
	alembic upgrade head

test:
	pytest
