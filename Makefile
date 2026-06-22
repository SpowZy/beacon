.PHONY: install demo test ollama-demo

install:
	python -m venv .venv
	. .venv/bin/activate && pip install -e ".[dev]"

demo:
	python -m beacon.demo

test:
	pytest -q

ollama-demo:
	BEACON_LLM_BACKEND=ollama python -m beacon.demo
