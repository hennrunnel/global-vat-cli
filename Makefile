run:
	source ../global-vat/bin/activate && python main.py --allow-fallbacks

run-strict:
	source ../global-vat/bin/activate && python main.py

dry-run:
	source ../global-vat/bin/activate && python main.py --dry-run

monitor:
	source ../global-vat/bin/activate && python main.py --monitor

test:
	source ../global-vat/bin/activate && PYTHONPATH=. pytest -q
