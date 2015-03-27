#!make
IMAGE_NAME=skasa/simulator

.PHONY: all build run force-build

all: download build run

download:
	./download.sh

build:
	docker build -t $(IMAGE_NAME) .

force-build:
	docker build --pull -t $(IMAGE_NAME) --no-cache=true .

run:
	docker run -v `pwd`/input:/input:ro -v `pwd`/output:/output:rw $(IMAGE_NAME) 

shell:
	docker run -ti -v `pwd`/input:/input:ro -v `pwd`/output:/output:rw $(IMAGE_NAME) bash
