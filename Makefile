default: env
	env/bin/pip install --requirement requirements.txt
env:
	python3 -m venv env

launch:
	env/bin/python3 set_status.py


