#!make
IMAGE_NAME=radioastro/simulator

ifndef config
	config=parameters.json
endif	

.PHONY: all build run force-build

all: build

build:
	docker build -t $(IMAGE_NAME) .

run:
	docker run -ti -v `pwd`/input:/input:ro -v `pwd`/output:/output:rw -e config=$(config) $(IMAGE_NAME)

shell:
	docker run -ti -v `pwd`/input:/input:ro -v `pwd`/output:/output:rw $(IMAGE_NAME) bash
