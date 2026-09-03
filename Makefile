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


# --- Git ---
#
# Git staging
git-stage:
	@echo "$(PACKAGE_NAME)[$(BRANCH)@$(HEAD)]: Staging new, modified, deleted and/or renamed files in Git"
	git status -uno | grep modified | tr -s ' ' | cut -d ' ' -f 2 | xargs git add && \
	git status -uno | grep deleted | tr -s ' ' | cut -d ' ' -f 2 | xargs git add -A && \
	git status -uno

# --- Housekeeping ---
.PHONY: clean
clean:
	@echo "$(PACKAGE_NAME)[$(BRANCH)@$(HEAD)]: Deleting all temporary files"
	rm -fr docs/_build/* .pytest_cache *.pyc *__pycache__* ./dist/* ./build/* *.egg-info*

# --- Version commands ---
#
# A simple file-based version check for the installed package (local, sdist or wheel)
version-check:
	@echo "$(PACKAGE_NAME)[$(BRANCH)@$(HEAD)]: Checking installed package version (if it is installed)"
	python3 -c "import os; os.chdir('src/arc'); from __init__ import __version__; print(__version__); os.chdir('../')"

# Just display the version
version-extract:
	echo "$(PACKAGE_VERSION)"

# --- Member inspection of Python files ---
#
# To list functions use:
#
#     list-members MEMBER_REGEX="def" FILE_PATH="/path/to/py/file"
#
# To list classes use:
#
#     list-members MEMBER_REGEX="class" FILE_PATH="/path/to/py/file"
#
# To list functions or classes use:
#
#     list-members MEMBER_REGEX="def\|class" FILE_PATH="/path/to/py/file"
list-callables:
	@echo "$(PACKAGE_NAME)[$(BRANCH)@$(HEAD)]: Parametrised command for listing the callable members (functions or classes) of a Python file"
	grep "$(MEMBER_REGEX)" $(FILE_PATH) | sort | cut -d ' ' -f 2 | cut -d '(' -f 1

# --- Dependency management ---
sync-deps-exact:
	@echo "$(PACKAGE_NAME)[$(BRANCH)@$(HEAD)]: Syncing all package + development dependencies with lockfile, removing unrelated dependencies"
	rm -f uv.lock && \
	uv sync --verbose --active --all-groups --no-install-project --no-cache --refresh

sync-deps-inexact:
	@echo "$(PACKAGE_NAME)[$(BRANCH)@$(HEAD)]: Syncing all package + development dependencies with lockfile, preserving unrelated dependencies"
	rm -f uv.lock && \
	uv sync --verbose --active --all-groups --no-install-project --no-cache --refresh --inexact

# --- Documentation ---
.PHONY: clean
docs: clean
	@echo "$(PACKAGE_NAME)[$(BRANCH)@$(HEAD)]: Building Sphinx docs"
	make -C docs html

# --- Pre-commit ---
.PHONY: clean
pre-commit: clean
	@echo "$(PACKAGE_NAME)[$(BRANCH)@$(HEAD)]: Running pre-commit hooks"
	pre-commit run --all-files

# --- Tests ---
#
# Unit tests - "critical or high"
unittests-critical-high: clean
	@echo "$(PACKAGE_NAME)[$(BRANCH)@$(HEAD)]: Running critical/high unit tests + measuring coverage"
	PYTHONPATH="src" uv run --verbose --active pytest \
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
	@echo "$(PACKAGE_NAME)[$(BRANCH)@$(HEAD)]: Running medium/low unit tests + measuring coverage"
	PYTHONPATH="src" uv run --verbose --active pytest \
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

# Doctests
.PHONY: clean
doctests: clean
	@echo "$(PACKAGE_NAME)[$(BRANCH)@$(HEAD)]: Running doctests in all core libraries"
	PYTHONPATH="src" uv run --verbose --active python3 -m doctest -v src/arc/*.py
