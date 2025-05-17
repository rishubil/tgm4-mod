import argparse
import os

from libs.alz import alz_decompress
from tqdm import tqdm


def decompress(input_dir, output_dir):
    os.makedirs(output_dir, exist_ok=True)

    file_list = []
    for root, _, files in os.walk(input_dir):
        for file in files:
            file_path = os.path.relpath(os.path.join(root, file), input_dir)
            file_list.append(file_path)

    file_list.sort()

    with tqdm(total=len(file_list), desc="Extracting files") as pbar:
        for file_path in file_list:
            pbar.set_postfix_str(f"Extracting: {file_path:<32}")
            with open(os.path.join(input_dir, file_path), "rb") as f:
                file_data = f.read()
            decompressed_data = alz_decompress(file_data)
            output_path = os.path.join(output_dir, file_path)
            os.makedirs(os.path.dirname(output_path), exist_ok=True)
            with open(output_path, "wb") as f:
                f.write(decompressed_data)
            pbar.update(1)
    print("Decompression completed")


if __name__ == "__main__":
    parser = argparse.ArgumentParser(
        description="TGM4 ALZ Decompressor",
        formatter_class=argparse.ArgumentDefaultsHelpFormatter,
    )
    parser.add_argument(
        "--input_dir",
        type=str,
        default="resources/extracted_resources",
        help="Input directory path",
    )
    parser.add_argument(
        "--output_dir",
        type=str,
        default="resources/decompressed_resources",
        help="Output directory path",
    )
    args = parser.parse_args()

    decompress(
        args.input_dir,
        args.output_dir,
    )
