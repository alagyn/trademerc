#!/bin/bash

home=`dirname $0`
cd $home
venv/bin/python -m cash_money.easy_run_alpaca
