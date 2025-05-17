import argparse
import os

from libs.tws import TwsFile
from tqdm import tqdm


def twx_to_png(input_dir, file_path, output_dir):
    input_file_path = os.path.join(input_dir, file_path)
    with open(input_file_path, "rb") as f:
        data = f.read()

    tws_file = TwsFile.from_bytes(data)
    png_data = tws_file.to_png()
    output_file_path = os.path.join(output_dir, file_path + ".png")
    os.makedirs(os.path.dirname(output_file_path), exist_ok=True)
    with open(output_file_path, "wb") as f:
        f.write(png_data)
    return True


def process_all_twx_files(input_dir, output_dir):
    os.makedirs(output_dir, exist_ok=True)

    file_list = []
    for root, _, files in os.walk(input_dir):
        for file in files:
            if file.lower().endswith(".twx"):
                file_path = os.path.relpath(os.path.join(root, file), input_dir)
                file_list.append(file_path)

    file_list.sort()

    with tqdm(total=len(file_list), desc="Processing TWX files") as pbar:
        for file_path in file_list:
            pbar.set_postfix_str(f"Processing: {file_path:<32}")
            success = twx_to_png(input_dir, file_path, output_dir)
            if not success:
                raise ValueError(
                    f"Error processing {file_path}: Failed to convert texture"
                )
            pbar.update(1)

    print("Processing completed")


if __name__ == "__main__":
    parser = argparse.ArgumentParser(
        description="TGM4 TWX to PNG Converter",
        formatter_class=argparse.ArgumentDefaultsHelpFormatter,
    )
    parser.add_argument(
        "--input_dir",
        type=str,
        default="resources/decompressed_resources",
        help="Input directory path (TWX files to be converted)",
    )
    parser.add_argument(
        "--output_dir",
        type=str,
        default="resources/extracted_textures",
        help="Output directory (PNG files will be saved here)",
    )
    args = parser.parse_args()

    process_all_twx_files(args.input_dir, args.output_dir)
