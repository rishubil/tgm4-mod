import argparse
import os

from libs.info import InfoDat
from tqdm import tqdm


def unpack(info_path, game_path, output_dir):
    os.makedirs(output_dir, exist_ok=True)

    with open(info_path, "rb") as f:
        info_data = f.read()
    info_dat = InfoDat.from_encrypted_bytes(info_data)

    # Extract files
    with open(game_path, "rb") as game_file:
        with tqdm(total=info_dat.file_count, desc="Unpacking files") as pbar:
            for entry in info_dat.entries:
                pbar.set_postfix_str(f"Unpacking: {entry.name:<32}")
                file_data = entry.read_from_game_file(game_file)
                if file_data is None:
                    raise ValueError(
                        f"Error: {entry.name} - Failed to read data from GAME.DAT"
                    )
                output_file_path = os.path.join(output_dir, entry.name)
                os.makedirs(os.path.dirname(output_file_path), exist_ok=True)
                with open(output_file_path, "wb") as output_file:
                    output_file.write(file_data)
                pbar.update(1)
    print("Unpacking completed")


if __name__ == "__main__":
    parser = argparse.ArgumentParser(
        description="TGM4 Unpacker",
        formatter_class=argparse.ArgumentDefaultsHelpFormatter,
    )
    parser.add_argument(
        "--info_path",
        type=str,
        default="resources/original_gamefiles/INFO.DAT",
        help="Path of original INFO.DAT",
    )
    parser.add_argument(
        "--game_path",
        type=str,
        default="resources/original_gamefiles/GAME.DAT",
        help="Path of original GAME.DAT",
    )
    parser.add_argument(
        "--output_dir",
        type=str,
        default="resources/extracted_resources",
        help="Output directory path",
    )
    args = parser.parse_args()

    unpack(
        args.info_path,
        args.game_path,
        args.output_dir,
    )
