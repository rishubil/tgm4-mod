#!/bin/bash

set -e

uv run scripts/convert_png_to_tws.py # converts back to game format to resources/decompressed_resources_edited
uv run scripts/compress.py # compresses modified resources to resources/extracted_resources_edited
uv run scripts/pack.py # creates final game files to resources/packed_gamefiles
