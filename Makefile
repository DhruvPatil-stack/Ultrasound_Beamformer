.PHONY: install test demo quick verify clean

install:
	python -m pip install -r requirements.txt

test:
	python -m pytest -q

demo:
	python run_demo.py

quick:
	python run_demo.py --quick

verify: test
	python -m tools.render_readme --check

clean:
	-$(RM) -r __pycache__ .pytest_cache src/__pycache__ tests/__pycache__
