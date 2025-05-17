# TGM4 MOD

A modding tool that allows you to unpack, modify, and repack TGM4 game files. This tool supports converting textures between the game's native format and PNG for easy editing.

> [!WARNING]  
> This is an unofficial modding tool for TGM4.  
> It is not affiliated with or endorsed by the original developers.  
> Use at your own risk.

## Usage

### Prerequisites

This tool must be run within a devcontainer environment.

You can use the [Visual Studio Code Dev Containers](https://marketplace.visualstudio.com/items?itemName=ms-vscode-remote.remote-containers) extension to set this up. After installing the extension, open the project and click the green button in the bottom left corner, then select "Reopen in Container."

When opening the project for the first time, install dependencies by running:

```bash
uv sync --locked
```

### Unpacking Game Files

First, copy the following files from your original TGM4 installation to the `resources/original_gamefiles` directory:

- `INFO.DAT`
- `GAME.DAT`

Then run these commands to unpack and convert the game files:

```bash
uv run scripts/unpack.py # extracts to resources/extracted_resources
uv run scripts/decompress.py # decompresses to resources/decompressed_resources
uv run scripts/convert_tws_to_png.py # converts textures to resources/extracted_textures
```

To create a backup of the unpacked files:

```bash
cp -R resources/extracted_textures resources/extracted_textures_backup
```

### Editing Files

You can now edit the files in:
- `resources/decompressed_resources` for game data
- `resources/extracted_textures` for texture images

> [!CAUTION]
> **DO NOT** change the dimensions (width and height) of any images.

For faster repacking, remove any unmodified files from these directories.

### Repacking Files

After editing, repack your modified files with:

```bash
uv run scripts/convert_png_to_tws.py # converts back to game format to resources/decompressed_resources_edited
uv run scripts/compress.py # compresses modified resources to resources/extracted_resources_edited
uv run scripts/pack.py # creates final game files to resources/packed_gamefiles
```

Your newly packed game files will be in the `resources/packed_gamefiles` directory.
Copy these files to your TGM4 installation directory to test your modifications.

## License

MIT License
