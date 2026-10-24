.PHONY: run build test check check-consumers
run:
	$(MAKE) -C go run
build:
	$(MAKE) -C go build
test:
	$(MAKE) -C go test
	python3 -m unittest discover -s tests -v
check:
	$(MAKE) -C go check
	python3 tools/export_tokens.py --check
	python3 tools/check_palette.py design/themes/lazyora-candidate.csv
	python3 tools/check_links.py
	sh -n shell/examples/terminal-colors.sh
check-consumers:
	python3 tools/check_consumers.py
