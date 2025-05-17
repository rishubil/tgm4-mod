import io
import struct
from dataclasses import dataclass

from PIL import Image
from quicktex import RawTexture
from quicktex.s3tc.bc1 import BC1Decoder, BC1Encoder, BC1Texture
from quicktex.s3tc.bc3 import BC3Decoder, BC3Encoder, BC3Texture

FORMAT_RGB = 7
FORMAT_RGBA = 8
FORMAT_BC1 = 9
FORMAT_BC3 = 11
FORMAT_BC3_2 = 13

TWS_HEADER_SIZE = 0x30
TWS_MAGIC = 0x30585754  # 'TWX0' in little-endian


@dataclass
class TwsFile:
    image_data: bytes
    width: int
    height: int
    data_format: int
    max_mipmap_level: int = 0

    @classmethod
    def from_bytes(cls, file_data: bytes) -> "TwsFile":
        if len(file_data) < TWS_HEADER_SIZE:
            raise ValueError("The file is too small to be a TWX file")

        # Check magic number
        magic = struct.unpack("<I", file_data[0:4])[0]
        if magic != TWS_MAGIC:
            raise ValueError(f"Invalid TWX file magic number: {file_data[0:4].hex()}")

        # Extract header information
        width = struct.unpack("<H", file_data[8:10])[0]
        height = struct.unpack("<H", file_data[10:12])[0]
        data_format = struct.unpack("<H", file_data[12:14])[0]

        image_data = file_data[TWS_HEADER_SIZE:]

        max_mipmap_level = cls.check_size(image_data, width, height, data_format)

        return cls(image_data, width, height, data_format, max_mipmap_level)

    def to_bytes(self, original_data: bytes) -> bytes:
        return original_data[:TWS_HEADER_SIZE] + self.image_data

    def to_png(self) -> bytes:
        image = None
        if self.data_format == FORMAT_RGB:
            image = Image.frombytes(
                "RGB", (self.width, self.height), self.image_data
            ).convert("RGBA")
        elif self.data_format == FORMAT_RGBA:
            image = Image.frombytes("RGBA", (self.width, self.height), self.image_data)
        elif self.data_format == FORMAT_BC1:
            image = Image.frombytes(
                "RGBA",
                (self.width, self.height),
                self.decode_bc1(self.image_data, self.width, self.height),
            )
        elif self.data_format == FORMAT_BC3 or self.data_format == FORMAT_BC3_2:
            # Use the first level of mipmap data only for convert to PNG
            level0_size = (self.width // 4) * (self.height // 4) * 16
            level0_data = self.image_data[:level0_size]
            image = Image.frombytes(
                "RGBA",
                (self.width, self.height),
                self.decode_bc3(level0_data, self.width, self.height),
            )

        if image is None:
            raise ValueError(f"Unsupported format: {self.data_format}, image is None")

        result = io.BytesIO()
        image.save(result, format="PNG")
        return result.getvalue()

    def load_from_image(self, image: Image.Image):
        new_image = b""

        if self.data_format == FORMAT_RGB:
            new_image = image.convert("RGB").tobytes("raw", "RGB")
        elif self.data_format == FORMAT_RGBA:
            new_image = image.convert("RGBA").tobytes("raw", "RGBA")
        elif self.data_format == FORMAT_BC1:
            new_image = self.encode_bc1(
                image.convert("RGBA").tobytes("raw", "RGBA"), self.width, self.height
            )
        elif self.data_format == FORMAT_BC3 or self.data_format == FORMAT_BC3_2:
            mipmap_level = 0
            mipmap_width = self.width
            mipmap_height = self.height
            new_image = b""
            image = image.convert("RGBA")
            while mipmap_level <= self.max_mipmap_level:
                new_image += self.encode_bc3(
                    image.tobytes("raw", "RGBA"),
                    mipmap_width,
                    mipmap_height,
                )
                mipmap_width = max(1, mipmap_width // 2)
                mipmap_height = max(1, mipmap_height // 2)
                mipmap_level += 1
                image = image.resize((mipmap_width, mipmap_height), Image.LANCZOS)

        if not new_image:
            raise ValueError(
                f"Unsupported format: {self.data_format}, new_image is None"
            )

        self.check_size(new_image, self.width, self.height, self.data_format)
        self.image_data = new_image

    @staticmethod
    def check_size(image_data: bytes, width: int, height: int, data_format: int) -> int:
        """
        Check the size of the image data based on the format and dimensions.

        If the data format is BC3 or BC3_2, it will return the maximum mipmap level.
        """

        max_mipmap_level = 0

        if data_format == FORMAT_RGB:
            expected_size = width * height * 3
            if len(image_data) != expected_size:
                raise ValueError(
                    f"Invalid image data size for FORMAT_RGB: {len(image_data)} / {expected_size}"
                )
        elif data_format == FORMAT_RGBA:
            expected_size = width * height * 4
            if len(image_data) != expected_size:
                raise ValueError(
                    f"Invalid image data size for FORMAT_RGBA: {len(image_data)} / {expected_size}"
                )
        elif data_format == FORMAT_BC1:
            expected_size = (width // 4) * (height // 4) * 8
            if len(image_data) != expected_size:
                raise ValueError(
                    f"Invalid image data size for FORMAT_BC1: {len(image_data)} / {expected_size}"
                )
        elif data_format == FORMAT_BC3 or data_format == FORMAT_BC3_2:
            mipmap_level = 0
            mipmap_width = width
            mipmap_height = height
            expected_size = (mipmap_width // 4) * (mipmap_height // 4) * 16
            while len(image_data) >= expected_size:
                # print(
                #     f"mipmap level: {mipmap_level}, size: {mipmap_width}x{mipmap_height}, total expected size: {expected_size}"
                # )
                if len(image_data) == expected_size:
                    break
                mipmap_level += 1
                mipmap_width = max(1, mipmap_width // 2)
                mipmap_height = max(1, mipmap_height // 2)
                expected_size += (mipmap_width // 4) * (mipmap_height // 4) * 16
            if len(image_data) != expected_size:
                raise ValueError(
                    f"Invalid image data size for FORMAT_BC3({data_format}): {len(image_data)} / {expected_size}"
                )
            max_mipmap_level = mipmap_level
        else:
            raise ValueError(f"Unsupported format: {data_format}")

        return max_mipmap_level

    @staticmethod
    def decode_bc1(buf: bytes, w: int, h: int) -> bytes:
        texture = BC1Texture.from_bytes(buf, w, h)
        decoder = BC1Decoder(
            write_alpha=True,
        )
        raw_texture = decoder.decode(texture)
        return raw_texture.tobytes()

    @staticmethod
    def encode_bc1(buf: bytes, w: int, h: int, compress_level: int = 10) -> bytes:
        texture = RawTexture.frombytes(buf, w, h)
        encoder = BC1Encoder(
            level=compress_level, color_mode=BC1Encoder.ColorMode.FourColor
        )
        encoded_texture = encoder.encode(texture)
        return encoded_texture.tobytes()

    @staticmethod
    def decode_bc3(buf: bytes, w: int, h: int) -> bytes:
        texture = BC3Texture.from_bytes(buf, w, h)
        decoder = BC3Decoder()
        raw_texture = decoder.decode(texture)
        return raw_texture.tobytes()

    @staticmethod
    def encode_bc3(buf: bytes, w: int, h: int, compress_level: int = 10) -> bytes:
        texture = RawTexture.frombytes(buf, w, h)
        encoder = BC3Encoder(level=compress_level)
        encoded_texture = encoder.encode(texture)
        return encoded_texture.tobytes()
