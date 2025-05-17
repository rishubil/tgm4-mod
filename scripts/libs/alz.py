import numpy as np
from numba import njit


@njit
def alz_decompress_numba(data: np.ndarray) -> np.ndarray:
    _WINDOW = 0x1000
    _START = 0xFEE

    # Check header - ALZ + version number (0x31)
    if (
        len(data) < 4
        or data[0] != 65
        or data[1] != 76
        or data[2] != 90
        or (data[3] & 0x7F) != 0x31
    ):
        # not alz: raw copy
        return data

    hdr_len = 8 if (data[3] & 0x80) else 4
    src = data[hdr_len:]
    src_pos = 0
    src_len = len(src)

    # sliding window buffer
    window = np.zeros(_WINDOW, dtype=np.uint8)
    win_pos = _START

    # Pre-allocate output buffer
    estimated_output_size = max(src_len * 3, 1024)
    out = np.zeros(estimated_output_size, dtype=np.uint8)
    out_pos = 0

    flags = 0

    while src_pos < src_len:
        flags >>= 1
        if (flags & 0x100) == 0:
            if src_pos >= src_len:
                break
            flags = src[src_pos] | 0xFF00
            src_pos += 1

        if src_pos >= src_len:
            break

        if flags & 1:  # literal
            byte = src[src_pos]
            src_pos += 1

            # Expand output buffer if needed
            if out_pos >= len(out):
                new_out = np.zeros(len(out) * 2, dtype=np.uint8)
                new_out[:out_pos] = out[:out_pos]
                out = new_out

            out[out_pos] = byte
            out_pos += 1
            window[win_pos] = byte
            win_pos = (win_pos + 1) & 0xFFF
        else:  # back-reference
            if src_pos + 1 >= src_len:
                break

            b1 = src[src_pos]
            b2 = src[src_pos + 1]
            src_pos += 2

            offset = ((b2 & 0xF0) << 4) | b1
            length = (b2 & 0x0F) + 3

            # Expand output buffer if needed
            if out_pos + length >= len(out):
                new_size = max(len(out) * 2, out_pos + length + 1024)
                new_out = np.zeros(new_size, dtype=np.uint8)
                new_out[:out_pos] = out[:out_pos]
                out = new_out

            for i in range(length):
                byte = window[(offset + i) & 0xFFF]
                out[out_pos] = byte
                out_pos += 1
                window[win_pos] = byte
                win_pos = (win_pos + 1) & 0xFFF

    # Return only the used portion of the output buffer
    # Numba-compatible: avoid using .tobytes()
    return out[:out_pos]


def alz_decompress(data: bytes) -> bytes:
    data_array = np.frombuffer(data, dtype=np.uint8)
    result_array = alz_decompress_numba(data_array)

    return bytes(result_array)


@njit
def alz_compress_numba(data: np.ndarray) -> np.ndarray:
    _WINDOW = 0x1000
    _START = 0xFEE

    n = len(data)
    if n == 0:
        # There is no data to compress
        result = np.zeros(4, dtype=np.uint8)
        result[0] = 65  # 'A'
        result[1] = 76  # 'L'
        result[2] = 90  # 'Z'
        result[3] = 0x31
        return result

    # Initialize hash table (2-byte hash)
    HASH_SIZE = 1 << 16
    last_pos = np.full(HASH_SIZE, -1, dtype=np.int32)

    # 2-byte hash function
    def h(p):
        if p + 1 < n:
            return ((data[p] << 8) ^ data[p + 1]) & 0xFFFF
        return 0

    # Initialize sliding window
    window = np.zeros(_WINDOW, dtype=np.uint8)
    win_pos = _START

    # Prepare output buffer
    max_output_size = n + (n // 7) + 100
    output = np.zeros(max_output_size, dtype=np.uint8)
    output[0] = 65  # 'A'
    output[1] = 76  # 'L'
    output[2] = 90  # 'Z'
    output[3] = 0x31
    output_pos = 4

    # Token management variables
    token_flags = 0
    token_start_pos = output_pos
    output_pos += 1  # Reserve flag byte
    token_count = 0

    # Token bundle processing function
    def flush_tokens():
        nonlocal token_start_pos, output_pos, token_count, token_flags
        if token_count > 0:
            output[token_start_pos] = token_flags
            token_flags = 0
            token_start_pos = output_pos
            output_pos += 1
            token_count = 0

    # Compression starts
    i = 0
    while i < n:
        if token_count == 8:
            flush_tokens()

        # Optimal match search
        best_len = 0
        best_dist = 0

        if i + 2 < n:
            key = h(i)
            prev = last_pos[key]
            last_pos[key] = i

            # Match search
            if prev >= 0 and (i - prev) <= 0xFFF and data[i] == data[prev]:
                dist = i - prev
                match_len = 1
                max_match = min(18, n - i)

                # Match length calculation
                while (
                    match_len < max_match
                    and data[i + match_len] == data[prev + match_len]
                ):
                    match_len += 1

                # At least 3 bytes match
                if match_len >= 3:
                    best_len = match_len
                    best_dist = dist

        # Back-reference or literal encoding
        if best_len >= 3:
            # Back-reference token
            off = (win_pos - best_dist) & 0xFFF
            output[output_pos] = off & 0xFF
            output[output_pos + 1] = ((off >> 4) & 0xF0) | (best_len - 3)
            output_pos += 2

            # Update window
            for k in range(best_len):
                window[win_pos] = data[i + k]
                win_pos = (win_pos + 1) & 0xFFF

            i += best_len
        else:
            # Literal token
            token_flags |= 1 << token_count
            output[output_pos] = data[i]
            output_pos += 1

            # Update window
            window[win_pos] = data[i]
            win_pos = (win_pos + 1) & 0xFFF

            i += 1

        token_count += 1

    # Process last token bundle
    flush_tokens()

    # Check compressed size
    compressed_size = output_pos

    # Important: If no compression gain, return original data without ALZ header
    if compressed_size >= n:
        return data

    # Return compressed result
    result = np.zeros(compressed_size, dtype=np.uint8)
    result[:compressed_size] = output[:compressed_size]
    return result


def alz_compress(data: bytes) -> bytes:
    data_array = np.frombuffer(data, dtype=np.uint8).copy()
    result_array = alz_compress_numba(data_array)
    return bytes(result_array)
