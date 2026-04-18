PYTHON  := python3
TARGET  := ./fio_testfile.dat
RESULTS := ./results
RUNTIME := 30

.PHONY: help test lint run run-concurrent

help:
	@echo "Usage: make <target>"
	@echo ""
	@echo "Targets:"
	@echo "  test           Run parser tests with pytest"
	@echo "  lint           Lint source files with ruff"
	@echo "  run            Run a single oltp_like profile"
	@echo "  run-concurrent Run streaming_like + background_backup concurrently"
	@echo ""
	@echo "Overridable variables:"
	@echo "  TARGET   fio test file path   (default: $(TARGET))"
	@echo "  RESULTS  output directory     (default: $(RESULTS))"
	@echo "  RUNTIME  runtime in seconds   (default: $(RUNTIME))"

test:
	$(PYTHON) -m pytest tests/ -v

lint:
	$(PYTHON) -m ruff check .

run:
	$(PYTHON) main.py run \
		--profile oltp_like \
		--target $(TARGET) \
		--runtime $(RUNTIME) \
		--output-dir $(RESULTS)

run-concurrent:
	$(PYTHON) main.py run-concurrent \
		--profile1 streaming_like \
		--profile2 background_backup \
		--target $(TARGET) \
		--runtime $(RUNTIME) \
		--output-dir $(RESULTS)
