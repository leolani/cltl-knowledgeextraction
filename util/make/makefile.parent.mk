SHELL=/bin/bash

export project_root ?= $(realpath .)
project_name ?= "app"
project_version ?= $(shell cat VERSION)

project_repo ?= ${project_root}/cltl-requirements/leolani
project_mirror ?= ${project_root}/cltl-requirements/mirror


project_components ?=


dependencies ?= $(addsuffix /makefile.d, $(project_components))


.DEFAULT_GOAL := execute


$(info Run $(target) for $(project_name), version: $(project_version), in $(project_root))


.PHONY: clean
clean:
	$(MAKE) target=clean

.PHONY: build
build:
	$(MAKE) target=build

.PHONY: install
install:
	$(MAKE) target=install

.PHONY: run
run:
	$(MAKE) --directory=$(project_name) run

.PHONY: stop
stop:
	$(MAKE) --directory=$(project_name) stop

.PHONY: execute
execute: $(project_components)

.PHONY: $(project_components)
$(project_components):
	$(MAKE) --directory=$@ $(target)

.PHONY: depend
depend: $(dependencies)

$(dependencies):
	$(MAKE) --directory=$(dir $@) depend


include $(dependencies)
