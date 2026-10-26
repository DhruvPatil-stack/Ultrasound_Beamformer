install:
	python -m pip install -r requirements.txt

test:
	pytest -q

demo:
	python run_demo.py

clean:
	-$(RM) -r __pycache__ .pytest_cache src/__pycache__ tests/__pycache__ results figures
