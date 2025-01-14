#!/bin/bash

python -m etl.extract &
sleep 30
python -m etl.load