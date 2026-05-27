.PHONY: test lint run clean help

help:
	@echo "SON Optimizer Makefile"
	@echo "----------------------"
	@echo "test      : Run all tests with pytest"
	@echo "lint      : Check code style with black & ruff"
	@echo "run       : Run the 1024-cell simulation"
	@echo "clean     : Remove temp files and pycache"
	@echo "docs      : Generate documentation"

test:
	pytest tests/unit/

verify:
	python research/verification/critical_verification.py

run:
	python scripts/run_pipeline.py --cells 1024 --policy dynamic

lint:
	ruff check src/
	black --check src/

install:
	pip install -r requirements.txt
	@echo "Installation complete. Please ensure 'cbc' solver is installed on your system."

clean:
	find . -type d -name "__pycache__" -exec rm -rf {} +
	rm -rf .pytest_cache
	rm -rf .coverage
	rm -rf htmlcov
