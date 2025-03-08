import zstandard as zstd
import os


def compress_file(
    input_file_path: str,
    output_file_path: str | None = None,
    compression_level=3,
    remove_input_file=False,
):
    if output_file_path is None:
        output_file_path = input_file_path + ".zst"

    with open(input_file_path, "rb") as input_file:
        data = input_file.read()

    cctx = zstd.ZstdCompressor(level=compression_level)
    compressed_data = cctx.compress(data)

    with open(output_file_path, "wb") as output_file:
        output_file.write(compressed_data)
    if remove_input_file:
        os.remove(input_file_path)

    return output_file_path


def decompress_file(input_file_path, output_file_path=None):
    if output_file_path is None:
        output_file_path = input_file_path.replace(".zst", "").replace(".zstd", "")

    # Read the compressed data from the input file
    with open(input_file_path, "rb") as input_file:
        compressed_data = input_file.read()

    decompressed_data = decompress_bytes(compressed_data)

    # Write the decompressed data to the output file
    with open(output_file_path, "wb") as output_file:
        output_file.write(decompressed_data)


def decompress_bytes(data: bytes) -> bytes:
    dctx = zstd.ZstdDecompressor()
    return dctx.decompress(data)
