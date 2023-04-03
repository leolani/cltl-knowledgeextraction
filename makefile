SHELL = /bin/bash

project_dependencies ?= $(addprefix $(project_root)/, emissor cltl-requirements cltl-knowledgerepresentation)

git_remote ?= https://github.com/leolani

artifact_name = cltl.triple_extraction

include util/make/makefile.base.mk
include util/make/makefile.component.mk
include util/make/makefile.py.base.mk
include util/make/makefile.git.mk


.PHONY: download
download:
	mkdir -p resources/conversational_triples
	wget "https://vu.data.surfsara.nl/index.php/s/WpL1vFChlQpkbqW/download" -O resources/conversational_triples/models.zip
	unzip -j -d resources/conversational_triples resources/conversational_triples/models.zip
	rm resources/conversational_triples/models.zip

docker:
	$(info "No docker build for $(project_name)")
