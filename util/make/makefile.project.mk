SHELL = /bin/bash

project_root ?= $(realpath ..)
project_name ?= $(notdir $(realpath .))
project_version ?= $(shell cat VERSION)

project_repo ?= ${project_root}/cltl-requirements/leolani
project_mirror ?= ${project_root}/cltl-requirements/mirror

# Add dependencies for component makefile
project_dependencies ?= $(addprefix $(project_root)/, \
		cltl-requirements \
		cltl-component)

# Add components for parent makefile
project_components ?= $(addprefix ${project_root}/, \
		cltl-requirements \
		cltl-combot \
		cltl-app \
		cltl-app-component)

# Add version control remote
remote ?= https://github.com/leolani

include $(project_root)/$(project_name)/*.mk