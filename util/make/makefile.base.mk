SHELL=/bin/bash

project_root ?= $(realpath ..)
project_name ?= $(notdir $(realpath .))
project_version ?= $(shell cat VERSION)
project_repo ?= ${project_root}/cltl-requirements/leolani
project_mirror ?= ${project_root}/cltl-requirements/mirror
# Add required components
project_dependencies ?=

timestamp ?= $(shell date +%s)

$(info Project $(project_name), version: $(project_version), in $(project_root), timestamp: $(timestamp))


# Implicit rules
.PHONY: depend
depend:

.PHONY: clean
clean: base-clean

.PHONY: touch-version
touch-version:

.PHONY: version
version: VERSION

VERSION: $(addsuffix /VERSION, $(project_dependencies))

.PHONY: version
build: VERSION

.PHONY: test
test: build

.PHONY: install
install:

# Explicit rules
.PHONY: base-clean
base-clean:
	@rm -rf makefile.d

VERSION:
	$(info Update version of ${project_root}/$(project_name))
	@cat VERSION | cut -f 1 -d '+' | xargs -I{} echo {}+$(timestamp) > version.increment
	@mv version.increment VERSION

touch-version:
	touch VERSION

depend:
ifdef project_dependencies
	echo ${project_root}/$(project_name): $(project_dependencies) > makefile.d
else
	touch makefile.d
endif
