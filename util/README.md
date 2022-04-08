# cltl-build

Build tools for the Leolani platform.

## Makefiles for multi-modular build

The `make/` directory contains makefiles to support building artifacts for components of the platform and manage the
build for multiple components from a parent directory.

### Project layout

In the following we will describe the layout for a project with Python modules, though also modules using other programming
languages  can be included in the build.

The directory layout of an application typically has the following structure:

```
parent/
│   makefile
│
└───@cltl-requirements
│   └───mirror/
│   └───leolani/
│   └───@cltl-build/
│   │   requirements.txt
│   │   makefile
│
└───@cltl-component-one
│   └───src/
│   └───venv/
│   └───@cltl-build/
│   │   setup.py
│   │   makefile
└───@cltl-component-two
│   └───src/
│   └───venv/
│   └───@cltl-build/
│   │   setup.py
│   │   makefile
```

* The parent folder contains a makefile that starts the build of all submodules.
* Components are git submodules.
* `cltl-requirements/` stores external (`mirror/`) and internal (`leolani/`)
  dependencies, and is used by the components as artifact repository (package index). Dependency versions for external
  dependencies can be managed centrally in the requirements.txt file of this directory.
* Each component is contained in its own directory and provides its own makefile that sets up the component
  using `cltl-requirements/` repository and publishes the build result there.
* Build order is determined by the dependencies of each module as defined in its makefile.

### Makefiles

#### Targets
* **clean**: 
  Remove all artifacts created during the build process
* **build**:
  Setup venvs, build the project artifacts and publish them to the repository.

#### Parent makefile

To set up the parent makefile, include the `/make/makefile.parent.mk` template and specify `project_name` and `project_components`:

```makefile
SHELL = /bin/bash

project_name ?= "cltl-my-app"

project_components = $(addprefix ${project_root}/, \
                cltl-requirements \
                cltl-my-app \
                cltl-component-one \
                cltl-component-two)

include util/make/makefile.parent.mk
```

`project_components` should be the directory names of the included components. 

#### Component makefile

To include a component in the build, typically it is enough to include the makefiles provided in this repository and to
specify the component dependecies:

```makefile
SHELL = /bin/bash

# Add dependencies for component makefile
project_dependencies ?= $(addprefix $(project_root)/, \
		cltl-requirements \
		cltl-component)

include util/make/makefile.base.mk
include util/make/makefile.py.base.mk
include util/make/makefile.git.mk
include util/make/makefile.component.mk
```

#### Makefile variables

The makefiles use the following variables that can be overridden:

| Variable  | Default                      |
|-----------|------------------------------|
| project_root | parent directory          |
| project_name | directory name            |
| project_version | VERSION file           |
| project_repo | cltl-requirements/leolani |
| project_mirror | cltl-requirements/mirror |
| project_dependencies | empty             |

