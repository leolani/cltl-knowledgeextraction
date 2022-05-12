SHELL=/bin/bash

project_components ?=


git_local ?=
git_remote ?= https://github.com/leolani


.PHONY: git-status
git-status:
	git submodule foreach 'git status'


.PHONY: git-update
git-update:
	git submodule update --remote --force --recursive


.PHONY: git-local
git-local:
	@for component in $(notdir $(project_components)); do \
		git submodule set-url -- $$component $(git_local)/$$component; \
	done

.PHONY: git-remote
git-remote:
	@for component in $(notdir $(project_components)); do \
		git submodule set-url -- $$component $(git_remote)/$$component; \
	done
