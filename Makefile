SHELL := /bin/bash

REPO := https://github.com/ISARICResearch/ARC

PACKAGE_NAME := arc
BRANCH := $(shell git rev-parse --abbrev-ref HEAD)
HEAD := $(shell git rev-parse --short=8 HEAD)
PACKAGE_VERSION := $(shell grep __version__ src/arc/__init__.py | cut -d '=' -f 2 | xargs)

PROJECT_ROOT := $(PWD)

TESTS_ROOT := $(PROJECT_ROOT)/tests

DOCS_ROOT := $(PROJECT_ROOT)/docs
DOCS_BUILD := $(DOCS_ROOT)/_build
DOCS_BUILD_HTML := $(DOCS_ROOT)/_build/html

# Make everything (possible)
all:

# Git
git-stage:
	@echo "$(PACKAGE_NAME)[$(BRANCH)@$(HEAD)]: Staging new, modified, deleted and/or renamed files in Git\n"
	git status -uno | grep modified | tr -s ' ' | cut -d ' ' -f 2 | xargs git add && \
	git status -uno | grep deleted | tr -s ' ' | cut -d ' ' -f 2 | xargs git add -A && \
	git status -uno

# Housekeeping
clean:
	@echo "\n$(PACKAGE_NAME)[$(BRANCH)@$(HEAD)]: Deleting all temporary files\n"
	rm -fr docs/_build/* .pytest_cache *.pyc *__pycache__* ./dist/* ./build/* *.egg-info*

# A simple version check for the installed package (local, sdist or wheel)
version-check:
	@echo "\n$(PACKAGE_NAME)[$(BRANCH)@$(HEAD)]: Checking installed package version (if it is installed)\n"
	python3 -c "import os; os.chdir('src/arc'); from __init__ import __version__; print(__version__); os.chdir('../')"

version-extract:
	echo "$(PACKAGE_VERSION)"

# Dependency management
sync-deps-exact:
	@echo "\n$(PACKAGE_NAME)[$(BRANCH)@$(HEAD)]: Syncing all package + development dependencies with lockfile, removing unrelated dependencies\n"
	rm -f uv.lock && \
	uv sync --verbose --active --all-groups --no-install-project --no-cache --refresh

sync-deps-inexact:
	@echo "\n$(PACKAGE_NAME)[$(BRANCH)@$(HEAD)]: Syncing all package + development dependencies with lockfile, preserving unrelatd dependencies\n"
	rm -f uv.lock && \
	uv sync --verbose --active --all-groups --no-install-project --no-cache --refresh --inexact

# Documentation
docs: clean
	@echo "\n$(PACKAGE_NAME)[$(BRANCH)@$(HEAD)]: Building Sphinx docs\n"
	make -C docs html

# Pre-commit
pre-commit: clean
	@echo "\n$(PACKAGE_NAME)[$(BRANCH)@$(HEAD)]: Running pre-commit hooks\n"
	pre-commit run --all-files

# Unit tests - "critical or high"
unittests-critical-high: clean
	@echo "\n$(PACKAGE_NAME)[$(BRANCH)@$(HEAD)]: Running critical/high unit tests + measuring coverage\n"
	PYTHONPATH="src" uv run --active pytest \
                                     -q -m "critical or high" \
			                         --cache-clear \
				                     --capture=no \
				                     --code-highlight=yes \
				                     --color=yes \
				                     --cov=src \
				                     --cov-report=term-missing:skip-covered \
				                     -ra \
				                     --tb=native \
				                     --verbosity=3 \
				                    tests/unit

# Unit tests - "medium or low"
unittests-medium-low: clean
	@echo "\n$(PACKAGE_NAME)[$(BRANCH)@$(HEAD)]: Running medium/low unit tests + measuring coverage\n"
	PYTHONPATH="src" uv run --active pytest \
                                     -q -m "medium or low" \
			                         --cache-clear \
				                     --capture=no \
				                     --code-highlight=yes \
				                     --color=yes \
				                     --cov=src \
				                     --cov-report=term-missing:skip-covered \
				                     -ra \
				                     --tb=native \
				                     --verbosity=3 \
				                    tests/unit
