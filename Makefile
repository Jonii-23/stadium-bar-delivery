.PHONY: install test docker-build docker-test ci

install:
	python3 -m pip install -r requirements.txt

test:
	pytest -q

docker-build:
	docker build -t stadium-bar-delivery .

docker-test: docker-build
	docker run --rm stadium-bar-delivery

ci: test
