import argparse
import os

from libs.alz import alz_compress
from tqdm import tqdm


def compress(input_dir, output_dir):
    os.makedirs(output_dir, exist_ok=True)

    file_list = []
    for root, _, files in os.walk(input_dir):
        for file in files:
            file_path = os.path.relpath(os.path.join(root, file), input_dir)
            file_list.append(file_path)

    file_list.sort()

    with tqdm(total=len(file_list), desc="Compressing files") as pbar:
        for file_path in file_list:
            pbar.set_postfix_str(f"Compressing: {file_path:<32}")
            with open(os.path.join(input_dir, file_path), "rb") as f:
                file_data = f.read()
            compressed_data = alz_compress(file_data)
            output_path = os.path.join(output_dir, file_path)
            os.makedirs(os.path.dirname(output_path), exist_ok=True)
            with open(output_path, "wb") as f:
                f.write(compressed_data)
            pbar.update(1)

    print("Compression completed")


if __name__ == "__main__":
    parser = argparse.ArgumentParser(
        description="TGM4 ALZ Compressor",
        formatter_class=argparse.ArgumentDefaultsHelpFormatter,
    )
    parser.add_argument(
        "--input_dir",
        type=str,
        default="resources/decompressed_resources_edited",
        help="Input directory path",
    )
    parser.add_argument(
        "--output_dir",
        type=str,
        default="resources/extracted_resources_edited",
        help="Output directory path",
    )
    args = parser.parse_args()

    compress(
        args.input_dir,
        args.output_dir,
    )
