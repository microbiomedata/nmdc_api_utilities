# ============ Hint for for Windows Users ============

# On Windows the "sh" shell that comes with Git for Windows should be used.
# If it is not on path, provide the path to the executable in the following line.
#set windows-shell := ["C:/Program Files/Git/usr/bin/sh", "-cu"]

# ============ Variables used in recipes ============

# Set shebang line for cross-platform Python recipes (assumes presence of launcher on Windows)
shebang := if os() == 'windows' {
  'py'
} else {
  '/usr/bin/env python3'
}


# ============== Project recipes ==============

# List all commands as default command. The prefix "_" hides the command.
_default: _status
    @just --list


# Run all tests
[group('model development')]
test: pytest mypy format

test-full: test pytest-integration

pytest:
  uv run pytest

# include integration tests
pytest-integration:
	$(RUN) pytest -m ""

doctest:
  uv run pytest  --doctest-modules src

mypy:
  uv run mypy src tests

format:
	uv run ruff check .

# ============== Notebook recipes ==============

# Run a notebook with papermill and convert to HTML
[group('notebooks')]
run-notebook notebook output_name="":
	#!/usr/bin/env bash
	set -euo pipefail
	NOTEBOOK_PATH="{{notebook}}"
	NOTEBOOK_NAME=$(basename "$NOTEBOOK_PATH" .ipynb)
	OUTPUT_NAME="{{ if output_name != "" { output_name } else { "${NOTEBOOK_NAME}_executed" } }}"
	OUTPUT_DIR=$(dirname "$NOTEBOOK_PATH")

	echo "Executing notebook: $NOTEBOOK_PATH"
	uv run papermill "$NOTEBOOK_PATH" "${OUTPUT_DIR}/${OUTPUT_NAME}.ipynb"

	echo "Converting to HTML..."
	uv run jupyter nbconvert --to html "${OUTPUT_DIR}/${OUTPUT_NAME}.ipynb"

	echo "✓ Notebook executed and saved to:"
	echo "  - ${OUTPUT_DIR}/${OUTPUT_NAME}.ipynb"
	echo "  - ${OUTPUT_DIR}/${OUTPUT_NAME}.html"

# Run the study analysis notebook
[group('notebooks')]
run-study-notebook:
	just run-notebook notebooks/study_analysis_nmdc_sty_11_aygzgv51.ipynb

# Run all notebooks in the notebooks directory
[group('notebooks')]
run-all-notebooks:
	#!/usr/bin/env bash
	set -euo pipefail
	for notebook in notebooks/*.ipynb; do
		# Skip already executed notebooks
		if [[ ! "$notebook" =~ _executed\.ipynb$ ]]; then
			echo "Processing $notebook..."
			just run-notebook "$notebook"
		fi
	done

# ============== Hidden internal recipes ==============

_status:
  @echo "OK"

