PYTHON ?= python3
INSTALLER := src/install/codex_install.py
COMPILED_DIR ?= src/misc/compiled
INSTALLER_ARGS ?=
# Use `make <target> -- --dry-run` for installer-managed dry runs, for example:
# `make build-src -- --dry-run`, `make build-install -- --dry-run`, or
# `make install -- --dry-run`. This passes the flag through without triggering
# GNU Make's own dry-run mode.
# Keep Python bytecode out of the repo for all Makefile-driven Python commands.
PYTHON_PYCACHE_PREFIX ?= /tmp/codex-pycache

ifneq ($(filter --dry-run,$(MAKECMDGOALS)),)
INSTALLER_ARGS += --dry-run
endif

ifeq ($(DRY_RUN),1)
INSTALLER_ARGS += --dry-run
endif

export LC_ALL := C
export TZ := UTC
export PYTHONDONTWRITEBYTECODE := 1
export PYTHONHASHSEED := 0
export PYTHONPYCACHEPREFIX := $(PYTHON_PYCACHE_PREFIX)
export PYTHONPATH := $(CURDIR)/src/python

PYTHON_ENV := LC_ALL=C TZ=UTC PYTHONPATH=$(CURDIR)/src/python PYTHONDONTWRITEBYTECODE=1 PYTHONHASHSEED=0 PYTHONPYCACHEPREFIX=$(PYTHON_PYCACHE_PREFIX)

.PHONY: preflight build-src build-install install runtime runtime-home runtime-skills runtime-instructions vars-init vars-reset nuke --dry-run

preflight:
	@printf "[make] preflight -> validating installer inputs, runtime contracts, and Python bytecode outputs\n"
	$(PYTHON_ENV) $(PYTHON) $(INSTALLER) preflight
	$(PYTHON_ENV) $(PYTHON) -m compileall src tests

build-src:
	@printf "[make] build-src -> building source artifacts and patched schema\n"
	$(PYTHON_ENV) $(PYTHON) $(INSTALLER) build-src $(INSTALLER_ARGS)

build-install:
	@printf "Confirm 'make build-install' will build and apply runtime changes. Continue? [y/N] "; \
	read -r confirm; \
	case "$$confirm" in [yY]|[yY][eE][sS]) ;; *) printf "Aborted.\n"; exit 1 ;; esac
	@printf "[make] build-install -> building from source and installing runtime assets\n"
	$(PYTHON_ENV) $(PYTHON) $(INSTALLER) build-install --compiled-dir $(COMPILED_DIR) $(INSTALLER_ARGS)

install:
	@printf "Confirm 'make install' will install dependencies, refresh runtime assets, and replace managed files in place. Continue? [y/N] "; \
	read -r confirm; \
	case "$$confirm" in [yY]|[yY][eE][sS]) ;; *) printf "Aborted.\n"; exit 1 ;; esac
	@printf "[make] install -> installing dependencies and packaged runtime assets\n"
	$(PYTHON_ENV) $(PYTHON) $(INSTALLER) install --compiled-dir $(COMPILED_DIR) $(INSTALLER_ARGS)

runtime:
	@printf "[make] runtime -> refreshing managed runtime assets without dependency installation\n"
	$(PYTHON_ENV) $(PYTHON) $(INSTALLER) runtime --compiled-dir $(COMPILED_DIR) $(INSTALLER_ARGS)

runtime-home:
	@printf "[make] runtime-home -> refreshing runtime-home pack, agents, instructions, and system config\n"
	$(PYTHON_ENV) $(PYTHON) $(INSTALLER) runtime-home --compiled-dir $(COMPILED_DIR) $(INSTALLER_ARGS)

runtime-skills:
	@printf "[make] runtime-skills -> refreshing skills, plugins, marketplace, and system skill bundles\n"
	$(PYTHON_ENV) $(PYTHON) $(INSTALLER) runtime-skills --compiled-dir $(COMPILED_DIR) $(INSTALLER_ARGS)

runtime-instructions:
	@printf "[make] runtime-instructions -> refreshing instruction assets and rendered instruction paths\n"
	$(PYTHON_ENV) $(PYTHON) $(INSTALLER) runtime-instructions --compiled-dir $(COMPILED_DIR) $(INSTALLER_ARGS)

# Standalone env refresh/reset targets. Install, runtime, and nuke manage their
# own environment flows directly and do not route through these targets.
vars-init:
	$(PYTHON_ENV) $(PYTHON) $(INSTALLER) vars-init --compiled-dir $(COMPILED_DIR)

vars-reset:
	$(PYTHON_ENV) $(PYTHON) $(INSTALLER) vars-reset --compiled-dir $(COMPILED_DIR)

nuke:
	@printf "Confirm 'make nuke' will remove runtime state. Continue? [y/N] "; \
	read -r confirm; \
	case "$$confirm" in [yY]|[yY][eE][sS]) ;; *) printf "Aborted.\n"; exit 1 ;; esac
	@printf "[make] nuke -> removing runtime state and managed shell exports while preserving secret-tool tokens\n"
	$(PYTHON_ENV) $(PYTHON) $(INSTALLER) nuke --compiled-dir $(COMPILED_DIR) $(INSTALLER_ARGS)

--dry-run:
	@:
