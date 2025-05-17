import argparse
import os

from libs.info import InfoDat
from tqdm import tqdm


def pack(info_path, original_extract_dir, extract_dir, output_dir):
    os.makedirs(output_dir, exist_ok=True)
    new_info_path = os.path.join(output_dir, "INFO.DAT")
    new_game_path = os.path.join(output_dir, "GAME.DAT")

    with open(info_path, "rb") as f:
        info_data = f.read()
    info_dat = InfoDat.from_encrypted_bytes(info_data)

    # Update entries with new file data
    for entry in info_dat.entries:
        if not os.path.exists(os.path.join(extract_dir, entry.name)):
            continue
        print(f"Updating {entry.name}...")
        with open(os.path.join(extract_dir, entry.name), "rb") as f:
            file_data = f.read()
        entry.update_info(file_data)

    # Recalculate block offsets
    info_dat.recalculate_offsets()

    # Save new INFO.DAT file
    with open(new_info_path, "wb") as f:
        f.write(info_dat.to_encrypted_bytes())

    # Write new GAME.DAT file
    with open(new_game_path, "wb") as new_game_file:
        with tqdm(total=info_dat.file_count, desc="Packing files") as pbar:
            for entry in info_dat.entries:
                pbar.set_postfix_str(f"Packing: {entry.name}")

                original_file_path = os.path.join(original_extract_dir, entry.name)
                new_file_path = os.path.join(extract_dir, entry.name)
                file_data = None

                if not os.path.exists(original_file_path):
                    raise ValueError(
                        f"Error: {entry.name} - Original file does not exist"
                    )

                if not os.path.exists(new_file_path):
                    # Use original file if new file does not exist
                    with open(original_file_path, "rb") as f:
                        file_data = f.read()
                else:
                    # Use new file if it exists
                    with open(new_file_path, "rb") as f:
                        file_data = f.read()

                if file_data is None:
                    raise ValueError(f"Error: {entry.name} - Failed to read data")

                entry.write_to_game_file(new_game_file, file_data)

                pbar.update(1)
    print("Packing completed")


if __name__ == "__main__":
    parser = argparse.ArgumentParser(
        description="TGM4 Packer",
        formatter_class=argparse.ArgumentDefaultsHelpFormatter,
    )
    parser.add_argument(
        "--info_path",
        type=str,
        default="resources/original_gamefiles/INFO.DAT",
        help="Path of original INFO.DAT",
    )
    parser.add_argument(
        "--original_extract_dir",
        type=str,
        default="resources/extracted_resources",
        help="Directory containing original resources",
    )
    parser.add_argument(
        "--extract_dir",
        type=str,
        default="resources/extracted_resources_edited",
        help="Directory containing edited resources",
    )
    parser.add_argument(
        "--output_dir",
        type=str,
        default="resources/packed_gamefiles",
        help="Output directory path",
    )
    args = parser.parse_args()

    pack(
        args.info_path,
        args.original_extract_dir,
        args.extract_dir,
        args.output_dir,
    )
