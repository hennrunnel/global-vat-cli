run:
	source ../global-vat-cli-venv/bin/activate && python main.py --allow-fallbacks

run-strict:
	source ../global-vat-cli-venv/bin/activate && python main.py

dry-run:
	source ../global-vat-cli-venv/bin/activate && python main.py --dry-run

monitor:
	source ../global-vat-cli-venv/bin/activate && python main.py --monitor

test:
	source ../global-vat-cli-venv/bin/activate && PYTHONPATH=. pytest -q
