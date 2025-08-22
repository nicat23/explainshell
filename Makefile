serve:
	python runserver.py

test:
	python -m pytest tests/ explainshell/ --doctest-modules --cov=explainshell

test-manager:
	python -m pytest tests/test_manager_simple.py -v

test-manager-full:
	python -m pytest tests/test_manager_expanded.py tests/test_manager_edge_cases.py tests/test_manager_performance.py -v

test-manager-suite:
	python tests/test_manager_suite.py run-suite

test-manager-stress:
	python tests/test_manager_suite.py run-suite --include-stress

# Docker commands
build:
	docker build . -t explainshell

start:
	docker compose up -d
	docker compose logs -f

stop:
	docker compose stop


up:
	docker compose up -d

down:
	docker compose down

logs:
	docker compose logs -f

restart:
	docker compose restart
	
# Database commands
db-dump:
	docker compose exec db mongodump --archive --gzip --db explainshell > ./output.gz

db-restore:
	docker compose exec -T db mongorestore --archive --gzip --db explainshell 

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


.PHONY: setup serve test test-manager test-manager-full test-manager-suite test-manager-stress build up down logs restart db-dump db-restore clean clean-all clean-app load_data