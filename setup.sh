#!/bin/bash

cd brick_manager
poetry install
poetry update
poetry run python app.py