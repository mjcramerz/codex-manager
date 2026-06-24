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

.PHONY: preflight verify build-src build-install install update home admin upgrade export vars-init vars-reset uninstall nuke --dry-run

preflight:
	@printf "[make] preflight -> validating installer inputs and runtime contracts\n"
	$(PYTHON_ENV) $(PYTHON) $(INSTALLER) preflight

verify:
	@printf "[make] verify -> byte-compiling src and tests with visible progress\n"
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
	@printf "Confirm 'make install' will apply runtime changes. Continue? [y/N] "; \
	read -r confirm; \
	case "$$confirm" in [yY]|[yY][eE][sS]) ;; *) printf "Aborted.\n"; exit 1 ;; esac
	@printf "[make] install -> installing packaged runtime assets\n"
	$(PYTHON_ENV) $(PYTHON) $(INSTALLER) install --compiled-dir $(COMPILED_DIR) $(INSTALLER_ARGS)

update:
	$(PYTHON_ENV) $(PYTHON) $(INSTALLER) update --compiled-dir $(COMPILED_DIR)

home:
	$(PYTHON_ENV) $(PYTHON) $(INSTALLER) home --compiled-dir $(COMPILED_DIR)

admin:
	$(PYTHON_ENV) $(PYTHON) $(INSTALLER) admin --compiled-dir $(COMPILED_DIR)

upgrade:
	$(PYTHON_ENV) $(PYTHON) $(INSTALLER) upgrade --compiled-dir $(COMPILED_DIR)

export:
	$(PYTHON_ENV) $(PYTHON) -m lib.keyring_env shell --env-file $(CURDIR)/.env

# Standalone env refresh/reset targets. Install, upgrade, and nuke manage their
# own environment flows directly and do not route through these targets.
vars-init:
	$(PYTHON_ENV) $(PYTHON) $(INSTALLER) vars-init --compiled-dir $(COMPILED_DIR)

vars-reset:
	$(PYTHON_ENV) $(PYTHON) $(INSTALLER) vars-reset --compiled-dir $(COMPILED_DIR)

nuke:
	@printf "Confirm 'make nuke' will remove runtime state. Continue? [y/N] "; \
	read -r confirm; \
	case "$$confirm" in [yY]|[yY][eE][sS]) ;; *) printf "Aborted.\n"; exit 1 ;; esac
	@printf "[make] nuke -> removing runtime state, managed shell exports, and best-effort managed secrets\n"
	$(PYTHON_ENV) $(PYTHON) $(INSTALLER) nuke --compiled-dir $(COMPILED_DIR) $(INSTALLER_ARGS)

uninstall:
	@printf "Confirm 'make uninstall' will remove runtime state. Continue? [y/N] "; \
	read -r confirm; \
	case "$$confirm" in [yY]|[yY][eE][sS]) ;; *) printf "Aborted.\n"; exit 1 ;; esac
	@printf "[make] uninstall -> removing runtime state, managed shell exports, and best-effort managed secrets\n"
	$(PYTHON_ENV) $(PYTHON) $(INSTALLER) uninstall --compiled-dir $(COMPILED_DIR) $(INSTALLER_ARGS)

--dry-run:
	@:
