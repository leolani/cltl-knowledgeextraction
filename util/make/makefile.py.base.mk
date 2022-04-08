project_name ?= $(notdir $(realpath .))
project_repo ?= ${project_root}/cltl-requirements/leolani
project_mirror ?= ${project_root}/cltl-requirements/mirror


sources ?= $(shell find $(project_root)/$(project_name)/src/*)
artifact_name ?= $(subst cltl-,cltl.,$(project_name))


VERSION: $(sources)


.PHONY: py-clean
py-clean:
	$(info Clean $(project_name))
	@rm -rf venv dist build *.egg-info

venv: requirements.txt setup.py VERSION
	$(info Create virutal environment for $(project_name))

	python -m venv venv
	source venv/bin/activate; \
		pip install --upgrade pip; \
		pip install wheel; \
		pip install -r requirements.txt --upgrade --upgrade-strategy eager --pre \
			 --no-index --find-links="$(project_mirror)" --find-links="$(project_repo)"; \
		deactivate

build: py-install

test:
	source venv/bin/activate; \
		python -m unittest; \
		deactivate

dist: $(sources) venv
	$(info Create distribution for $(project_name))

	# Ensure the timestamp changes
	rm -rf dist

	# TODO Is the pip install needed?
	source venv/bin/activate; \
		pip install -r requirements.txt --upgrade --upgrade-strategy eager --pre \
				--no-index --find-links="$(project_mirror)" --find-links="$(project_repo)"; \
		python setup.py sdist; \
		rm -rf src/*.egg-info; \
		deactivate

.PHONY: py-install
py-install: dist
	$(info Install $(project_name))
	@rm -rf $(project_repo)/$(artifact_name)-{0..9}*+{0..9}*.tar.gz
	@cp dist/*.tar.gz $(project_repo)
