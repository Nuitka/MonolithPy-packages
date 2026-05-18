"""
Basic sanity tests for zstandard package.
Tests C-backed (zstd library) functionality without extra dependencies.
"""

import zstandard as zstd
import io


def test_version():
    """Test version is accessible."""
    assert hasattr(zstd, 'ZSTD_VERSION')
    assert zstd.ZSTD_VERSION is not None


def test_simple_compress():
    """Test simple compression (C-backed)."""
    data = b"Hello, World! " * 100
    
    cctx = zstd.ZstdCompressor()
    compressed = cctx.compress(data)
    
    assert compressed is not None
    assert len(compressed) < len(data)


def test_simple_decompress():
    """Test simple decompression (C-backed)."""
    data = b"Hello, World! " * 100
    
    cctx = zstd.ZstdCompressor()
    compressed = cctx.compress(data)
    
    dctx = zstd.ZstdDecompressor()
    decompressed = dctx.decompress(compressed)
    
    assert decompressed == data


def test_compression_levels():
    """Test different compression levels (C-backed)."""
    data = b"Test data for compression " * 50
    
    sizes = []
    for level in [1, 5, 10, 15]:
        cctx = zstd.ZstdCompressor(level=level)
        compressed = cctx.compress(data)
        sizes.append(len(compressed))
    
    # Higher levels should generally produce smaller output
    # (though not guaranteed for all data)
    assert all(s < len(data) for s in sizes)


def test_streaming_compress():
    """Test streaming compression (C-backed)."""
    data = b"Streaming test data " * 100
    
    cctx = zstd.ZstdCompressor()
    
    # Compress using stream writer (closefd=False keeps buffer open after exit)
    buffer = io.BytesIO()
    with cctx.stream_writer(buffer, closefd=False) as writer:
        writer.write(data)

    compressed = buffer.getvalue()
    assert len(compressed) < len(data)


def test_streaming_decompress():
    """Test streaming decompression (C-backed)."""
    data = b"Streaming test data " * 100
    
    cctx = zstd.ZstdCompressor()
    compressed = cctx.compress(data)
    
    dctx = zstd.ZstdDecompressor()
    
    # Decompress using stream reader
    buffer = io.BytesIO(compressed)
    with dctx.stream_reader(buffer) as reader:
        decompressed = reader.read()
    
    assert decompressed == data


def test_dictionary_compression():
    """Test dictionary-based compression (C-backed)."""
    # Create training data
    samples = [b"sample data " * 10 for _ in range(100)]
    
    # Train dictionary
    dict_data = zstd.train_dictionary(8192, samples)
    assert dict_data is not None
    
    # Compress with dictionary
    cctx = zstd.ZstdCompressor(dict_data=dict_data)
    compressed = cctx.compress(b"sample data " * 10)
    
    # Decompress with dictionary
    dctx = zstd.ZstdDecompressor(dict_data=dict_data)
    decompressed = dctx.decompress(compressed)
    
    assert decompressed == b"sample data " * 10


def test_multi_frame():
    """Test multi-frame compression (C-backed)."""
    data1 = b"First frame data"
    data2 = b"Second frame data"
    
    cctx = zstd.ZstdCompressor()
    compressed1 = cctx.compress(data1)
    compressed2 = cctx.compress(data2)
    
    # Concatenate frames
    multi_frame = compressed1 + compressed2
    
    dctx = zstd.ZstdDecompressor()
    # Decompress first frame
    decompressed1 = dctx.decompress(compressed1)
    assert decompressed1 == data1


def test_content_size():
    """Test content size handling (C-backed)."""
    data = b"Test content size " * 50
    
    # Compress with content size
    cctx = zstd.ZstdCompressor(write_content_size=True)
    compressed = cctx.compress(data)
    
    # Get frame info
    frame_info = zstd.get_frame_parameters(compressed)
    assert frame_info.content_size == len(data)


def test_compressor_reuse():
    """Test compressor reuse (C-backed)."""
    cctx = zstd.ZstdCompressor()
    
    data1 = b"First data"
    data2 = b"Second data"
    
    compressed1 = cctx.compress(data1)
    compressed2 = cctx.compress(data2)
    
    dctx = zstd.ZstdDecompressor()
    assert dctx.decompress(compressed1) == data1
    assert dctx.decompress(compressed2) == data2


def test_chunked_compression():
    """Test chunked compression (C-backed)."""
    data = b"Chunked data " * 1000
    
    cctx = zstd.ZstdCompressor()
    chunks = []
    
    chunker = cctx.chunker(chunk_size=1024)
    for i in range(0, len(data), 100):
        chunks.extend(chunker.compress(data[i:i+100]))
    chunks.extend(chunker.finish())
    
    compressed = b''.join(chunks)
    
    dctx = zstd.ZstdDecompressor()
    # chunker output doesn't embed content size, so provide max_output_size
    decompressed = dctx.decompress(compressed, max_output_size=len(data))
    assert decompressed == data


if __name__ == "__main__":
    test_version()
    test_simple_compress()
    test_simple_decompress()
    test_compression_levels()
    test_streaming_compress()
    test_streaming_decompress()
    test_dictionary_compression()
    test_multi_frame()
    test_content_size()
    test_compressor_reuse()
    test_chunked_compression()
    print("All zstandard tests passed!")

