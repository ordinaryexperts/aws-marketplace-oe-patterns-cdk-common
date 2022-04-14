bash: build
	docker-compose run -w /code --rm devenv bash

build:
	docker-compose build devenv

rebuild:
	docker-compose build --no-cache devenv

python: build
	docker-compose run -w /code --rm devenv python3

test: build
	docker-compose run -w /code --rm devenv pytest -s
