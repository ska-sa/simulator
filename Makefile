#!make
IMAGE_NAME=radioastro/simulator

.PHONY: all build run force-build

all: build

build:
	`pwd`/copy_src.sh && docker build -t $(IMAGE_NAME) .

force-build:
	`pwd`/copy_src.sh && docker build -t $(IMAGE_NAME) --no-cache=true .

run:
	docker run -v `pwd`:/results $(IMAGE_NAME)
