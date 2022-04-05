python3 -m venv venv

sudo apt-get update
sudo apt-get install libjpeg-dev

venv/bin/pip install --upgrade pip
venv/bin/pip install wheel
venv/bin/pip install -r python_reqs.txt
