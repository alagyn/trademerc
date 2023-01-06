python3 -m venv venv

sudo apt-get update
sudo apt-get install libjpeg-dev libatlas-base-dev

venv/bin/pip install --upgrade pip
venv/bin/pip install wheel
venv/bin/pip install -r requirements.txt
