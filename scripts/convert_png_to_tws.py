import argparse
import os

from libs.tws import TwsFile
from PIL import Image
from tqdm import tqdm


def png_to_twx(input_dir, original_extract_dir, file_path, output_dir):
    input_file_path = os.path.join(input_dir, file_path)
    original_file_path = os.path.join(original_extract_dir, file_path[:-4])
    with open(original_file_path, "rb") as f:
        data = f.read()

    tws_file = TwsFile.from_bytes(data)

    with Image.open(input_file_path) as image:
        tws_file.load_from_image(image)

    output_file_path = os.path.join(output_dir, file_path[:-4])
    os.makedirs(os.path.dirname(output_file_path), exist_ok=True)
    with open(output_file_path, "wb") as f:
        f.write(tws_file.to_bytes(data))
    return True


def process_all_png_files(input_dir, original_extract_dir, output_dir):
    os.makedirs(output_dir, exist_ok=True)

    file_list = []
    for root, _, files in os.walk(input_dir):
        for file in files:
            if file.lower().endswith(".png"):
                file_path = os.path.relpath(os.path.join(root, file), input_dir)
                file_list.append(file_path)

    file_list.sort()

    with tqdm(total=len(file_list), desc="Processing PNG files") as pbar:
        for file_path in file_list:
            pbar.set_postfix_str(f"Processing: {file_path:<36}")  # 32 + 4 for '.png'
            success = png_to_twx(input_dir, original_extract_dir, file_path, output_dir)
            if not success:
                raise ValueError(
                    f"Error processing {file_path}: Failed to convert texture"
                )
            pbar.update(1)

    print("Processing completed")


if __name__ == "__main__":
    parser = argparse.ArgumentParser(
        description="TGM4 PNG to TWX Converter",
        formatter_class=argparse.ArgumentDefaultsHelpFormatter,
    )
    parser.add_argument(
        "--input_dir",
        type=str,
        default="resources/extracted_textures",
        help="Input directory path (PNG files to be converted)",
    )
    parser.add_argument(
        "--original_extract_dir",
        type=str,
        default="resources/decompressed_resources",
        help="Directory containing original resources",
    )
    parser.add_argument(
        "--output_dir",
        type=str,
        default="resources/decompressed_resources_edited",
        help="Output directory (TWX files will be saved here)",
    )
    args = parser.parse_args()

    process_all_png_files(args.input_dir, args.original_extract_dir, args.output_dir)
