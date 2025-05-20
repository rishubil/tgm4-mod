#!/bin/bash

set -e

uv run scripts/unpack.py # extracts to resources/extracted_resources
uv run scripts/decompress.py # decompresses to resources/decompressed_resources
uv run scripts/convert_tws_to_png.py # converts textures to resources/extracted_textures
cp -R resources/extracted_textures resources/extracted_textures_backup