#!make
IMAGE_NAME=radioastro/simulator

.PHONY: all build run force-build

all: build

build:
	rm -rf src && docker build -t $(IMAGE_NAME) .

force-build:
	rm -rf src && docker build -t $(IMAGE_NAME) --no-cache=true .

run:
	docker run -v `pwd`:/results $(IMAGE_NAME)
