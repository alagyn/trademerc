#!/bin/bash
home=$(realpath $(dirname $0)/..)
cd $home

venv/bin/python -m "cash_money.strategy_gui"
