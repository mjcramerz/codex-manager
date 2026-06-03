PYTHON ?= python3
INSTALLER := src/install/codex_install.py
COMPILED_DIR ?= src/misc/compiled
# Keep Python bytecode out of the repo for all Makefile-driven Python commands.
PYTHON_PYCACHE_PREFIX ?= /tmp/c0d3x-pycache

export LC_ALL := C
export TZ := UTC
export PYTHONDONTWRITEBYTECODE := 1
export PYTHONHASHSEED := 0
export PYTHONPYCACHEPREFIX := $(PYTHON_PYCACHE_PREFIX)
export PYTHONPATH := $(CURDIR)/src/python

PYTHON_ENV := LC_ALL=C TZ=UTC PYTHONPATH=$(CURDIR)/src/python PYTHONDONTWRITEBYTECODE=1 PYTHONHASHSEED=0 PYTHONPYCACHEPREFIX=$(PYTHON_PYCACHE_PREFIX)

.PHONY: preflight verify install home admin upgrade export tmpfs-mnt tmpfs-umt vars-init vars-reset nuke

preflight:
	$(PYTHON_ENV) $(PYTHON) $(INSTALLER) preflight

verify:
	$(PYTHON_ENV) $(PYTHON) -m compileall -q src

install:
	@printf "Confirm 'make install' will apply runtime changes. Continue? [y/N] "; \
	read -r confirm; \
	case "$$confirm" in [yY]|[yY][eE][sS]) ;; *) printf "Aborted.\n"; exit 1 ;; esac
	$(PYTHON_ENV) $(PYTHON) $(INSTALLER) install --compiled-dir $(COMPILED_DIR)

home:
	$(PYTHON_ENV) $(PYTHON) $(INSTALLER) home --compiled-dir $(COMPILED_DIR)

admin:
	$(PYTHON_ENV) $(PYTHON) $(INSTALLER) admin --compiled-dir $(COMPILED_DIR)

upgrade:
	$(PYTHON_ENV) $(PYTHON) $(INSTALLER) upgrade --compiled-dir $(COMPILED_DIR)

export:
	$(PYTHON_ENV) $(PYTHON) -m lib.keyring_env shell --env-file $(CURDIR)/.env

tmpfs-mnt:
	$(PYTHON_ENV) $(PYTHON) $(INSTALLER) tmpfs-mnt --compiled-dir $(COMPILED_DIR)

tmpfs-umt:
	$(PYTHON_ENV) $(PYTHON) $(INSTALLER) tmpfs-umt --compiled-dir $(COMPILED_DIR)

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
	$(PYTHON_ENV) $(PYTHON) $(INSTALLER) nuke --compiled-dir $(COMPILED_DIR)
