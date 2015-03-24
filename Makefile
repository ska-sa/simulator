#!make
IMAGE_NAME=skasa/simulator

.PHONY: all build run force-build

all: build

build:
	rm -rf src && docker build --pull -t $(IMAGE_NAME) .

force-build:
	rm -rf src && docker build --pull -t $(IMAGE_NAME) --no-cache=true .

run:
	docker run -v `pwd`/input:/input:ro $(IMAGE_NAME) 

shell:
	docker run -ti -v `pwd`/input:/input:ro $(IMAGE_NAME) bash
