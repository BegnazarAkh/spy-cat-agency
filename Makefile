.PHONY: install
install:
	pip install -r requirements.txt

.PHONY: test
test:
	python manage.py test

.PHONY: coverage
coverage:
	coverage run --source='.' manage.py test
	coverage report
	coverage html

.PHONY: lint
lint:
	pylint spy_cats/ spy_cat_agency/

.PHONY: bandit
bandit:
	bandit -r spy_cats/ spy_cat_agency/

.PHONY: clean
clean:
	find . -type f -name "*.pyc" -delete
	find . -type d -name "__pycache__" -delete
	rm -rf htmlcov/
	rm -f .coverage

.PHONY: run
run:
	python manage.py runserver

.PHONY: migrate
migrate:
	python manage.py makemigrations
	python manage.py migrate

.PHONY: setup
setup: install migrate
	python manage.py collectstatic --noinput

.PHONY: verify
verify: lint bandit test coverage