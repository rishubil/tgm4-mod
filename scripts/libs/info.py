import struct
from dataclasses import dataclass
from typing import BinaryIO

from tqdm import tqdm

FILE_ENTRY_SIZE = 0x30  # 48 bytes
FILE_BLOCK_SIZE = 0x800  # 2048 bytes


@dataclass
class FileEntry:
    name: str
    size: int
    block_count: int
    block_offset: int
    file_count: int  # maybe first entry only

    @classmethod
    def from_indexed_bytes(cls, data: bytes) -> "FileEntry":
        part_0x00 = struct.unpack("<32s", data[0x00:0x20])[0]
        part_0x20 = struct.unpack("<I", data[0x20:0x24])[0]
        part_0x24 = struct.unpack("<I", data[0x24:0x28])[0]
        part_0x28 = struct.unpack("<I", data[0x28:0x2C])[0]
        part_0x2C = struct.unpack("<I", data[0x2C:0x30])[0]

        # print(f"data: {data.hex()}")

        name = part_0x00.decode("utf-8").rstrip("\x00")
        size = part_0x20
        block_count = part_0x28
        block_offset = part_0x24
        file_count = part_0x2C

        return cls(name, size, block_count, block_offset, file_count)

    @classmethod
    def from_unindexed_bytes(cls, data: bytes, index: int) -> "FileEntry":
        entry_offset = 0x30 + index * FILE_ENTRY_SIZE
        return cls.from_indexed_bytes(
            data[entry_offset : entry_offset + FILE_ENTRY_SIZE]
        )

    def to_unindexed_bytes(self) -> bytes:
        name_bytes = struct.pack(
            "<32s", self.name.encode("utf-8").ljust(32, b"\x00")[:0x20]
        )
        size_bytes = struct.pack("<I", self.size)
        block_count_bytes = struct.pack("<I", self.block_count)
        block_offset_bytes = struct.pack("<I", self.block_offset)
        file_count = struct.pack("<I", self.file_count)

        return (
            name_bytes
            + size_bytes
            + block_offset_bytes
            + block_count_bytes
            + file_count
        )

    def read_from_game_file(self, game_file: BinaryIO) -> bytes:
        if self.block_count == 0:
            return b""
        game_file.seek(self.block_offset * FILE_BLOCK_SIZE)
        data = game_file.read(self.size)
        return data

    def write_to_game_file(self, game_file: BinaryIO, file_data: bytes):
        if self.block_count == 0:
            return
        game_file.seek(self.block_offset * FILE_BLOCK_SIZE)
        game_file.write(file_data)

    def update_info(self, file_data: bytes):
        self.size = len(file_data)
        self.block_count = (len(file_data) + FILE_BLOCK_SIZE - 1) // FILE_BLOCK_SIZE
        self.block_offset = 0  # Offset is not used in this context


@dataclass
class InfoDat:
    header: bytes
    file_count: int
    entries: list[FileEntry]

    @classmethod
    def from_plain_bytes(cls, data: bytes) -> "InfoDat":
        header = data[:0x30]
        first_entry = FileEntry.from_indexed_bytes(header)
        file_count = first_entry.file_count
        entries = []

        for i in tqdm(range(file_count), desc="Processing file entries"):
            entry = FileEntry.from_unindexed_bytes(data, i)
            entries.append(entry)
        return cls(header, file_count, entries)

    @classmethod
    def from_encrypted_bytes(cls, data: bytes) -> "InfoDat":
        decrypted_data = cls.decrypt_toc(data)
        return cls.from_plain_bytes(decrypted_data)

    def to_plain_bytes(self) -> bytes:
        body = b"".join(entry.to_unindexed_bytes() for entry in self.entries)
        return self.header + body

    def to_encrypted_bytes(self) -> bytes:
        body = b"".join(entry.to_unindexed_bytes() for entry in self.entries)
        return self.encrypt_toc(self.header + body)

    def recalculate_offsets(self):
        last_offset = 0
        for entry in self.entries:
            if entry.block_count == 0:
                continue
            entry.block_offset = last_offset
            last_offset += entry.block_count

    @staticmethod
    def decrypt_toc(data: bytes) -> bytes:
        if data[0] == 0 or len(data) <= 16:
            return data

        result = bytearray(data)

        for offset in range(16, len(data), 16):
            for i in range(16):
                if offset + i >= len(data):
                    break

                byte_val = result[offset + i]
                swapped = ((byte_val >> 4) | (byte_val << 4)) & 0xFF
                not_val = ~swapped & 0xFF
                result[offset + i] = (not_val - data[i]) & 0xFF

        return bytes(result)

    @staticmethod
    def encrypt_toc(data: bytes) -> bytes:
        if data[0] == 0 or len(data) <= 16:
            return data

        header = data[:16]
        result = bytearray(data)

        for offset in range(16, len(data), 16):
            for i in range(16):
                pos = offset + i
                if pos >= len(data):
                    break

                plain = result[pos]
                tmp = (plain + header[i]) & 0xFF
                x = ~tmp & 0xFF
                enc = ((x >> 4) | (x << 4)) & 0xFF
                result[pos] = enc

        return bytes(result)
