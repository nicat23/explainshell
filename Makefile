# Development commands
serve:
	python runserver.py

test:
	pytest tests/ explainshell/ --doctest-modules --cov=explainshell

# Docker commands
build:
	docker-compose build

up:
	docker-compose up -d

down:
	docker-compose down

logs:
	docker-compose logs -f

restart:
	docker-compose restart
	
# Database commands
db-dump:
	docker-compose exec db mongodump --archive --gzip --db explainshell

db-restore:
	docker-compose exec -T db mongorestore --archive --gzip --db explainshell

# Cleanup commands
clean:
	docker system prune -f
	pip cache purge

clean-all:
	docker system prune -af
	docker volume prune -f

clean-app:
	find . -type f -name '*.py[co]' -delete -o -type d -name __pycache__ -delete
	rm .pytest_cache/ -rf
	rm -rf .mypy_cache/
	rm .coverage

load_data:
	curl -L -o /tmp/dump.gz https://github.com/idank/explainshell/releases/download/db-dump/dump.gz
	docker compose exec -T db mongorestore --archive --gzip < /tmp/dump.gz
	rm /tmp/dump.gz

# Default


.PHONY: serve test build up down logs restart db-dump db-restore clean clean-all clean-app load_data
