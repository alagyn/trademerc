#!/bin/bash
home=$(realpath $(dirname $0)/..)
cd $home

venv/bin/python -m "cash_money.backtester_gui"
