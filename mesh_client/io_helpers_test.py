from __future__ import absolute_import
from unittest import TestCase, main
import io
import gzip
import six
import tempfile
from .io_helpers import GzipInputStream, SplitFile, SplitBytes, CombineStreams

try:
    from itertools import izip
except ImportError:
    izip = zip

mebibyte = 1024 * 1024
small_chunk = 10


class IOHelpersTest(TestCase):
    def test_gzip_input_stream(self):
        underlying = io.BytesIO(b"This is a short test stream")
        instance = GzipInputStream(underlying, block_size=4)
        result = b""
        for i in range(1000):
            read_result = instance.read(i)
            result += read_result
            if len(read_result) < i:
                break
        self.assertEqual(b"", instance.read(10))
        self.assertEqual(b"", instance.read())

        # Decode with GzipFile
        test_decoder = gzip.GzipFile('', mode='r', fileobj=io.BytesIO(result))
        self.assertEqual(b"This is a short test stream", test_decoder.read())

    def test_gzip_input_stream_read_all(self):
        underlying = io.BytesIO(b"This is a short test stream")
        instance = GzipInputStream(underlying, block_size=4)
        result = instance.read()
        self.assertEqual(b"", instance.read(10))
        self.assertEqual(b"", instance.read())

        # Decode with GzipFile
        test_decoder = gzip.GzipFile('', mode='r', fileobj=io.BytesIO(result))
        self.assertEqual(b"This is a short test stream", test_decoder.read())

    def test_split_file(self):
        with tempfile.TemporaryFile() as f:
            f.write(b"a" * mebibyte)
            f.write(b"b" * mebibyte)
            f.flush()
            instance = SplitFile(f, mebibyte)
            self.assertEqual(len(instance), 2)
            for m, c in izip(instance, [b"a", b"b"]):
                self.assertEqual(m.read(mebibyte), c * mebibyte)

    def test_split_file_irregular_size(self):
        with tempfile.TemporaryFile() as f:
            f.write(b"a" * mebibyte)
            f.write(b"b")
            f.flush()
            instance = SplitFile(f, mebibyte)
            self.assertEqual(len(instance), 2)
            iterator = iter(instance)
            chunk1 = six.next(iterator)
            self.assertEqual(b"a" * mebibyte, chunk1.read(mebibyte))
            chunk2 = six.next(iterator)
            self.assertEqual(b"b", chunk2.read(mebibyte))

    def test_split_file_irregular_size_2(self):
        with tempfile.TemporaryFile() as f:
            f.write(b"a" * mebibyte)
            f.write(b"b" * (mebibyte - 1))
            f.flush()
            instance = SplitFile(f, mebibyte)
            self.assertEqual(len(instance), 2)
            iterator = iter(instance)
            chunk1 = six.next(iterator)
            self.assertEqual(b"a" * mebibyte, chunk1.read(mebibyte))
            chunk2 = six.next(iterator)
            self.assertEqual(b"b" * (mebibyte - 1), chunk2.read(mebibyte))

    def test_split_bytes(self):
        instance = SplitBytes(b"a" * small_chunk + b"b" * small_chunk,
                              small_chunk)
        self.assertEqual(len(instance), 2)
        for m, c in izip(instance, [b"a", b"b"]):
            self.assertEqual(c * small_chunk, m.read(small_chunk))

    def test_split_bytes_irregular_size(self):
        instance = SplitBytes(b"a" * small_chunk + b"b", small_chunk)
        self.assertEqual(len(instance), 2)
        iterator = iter(instance)
        chunk1 = six.next(iterator)
        self.assertEqual(b"a" * small_chunk, chunk1.read(small_chunk))
        chunk2 = six.next(iterator)
        self.assertEqual(b"b", chunk2.read(small_chunk))

    def test_split_bytes_irregular_size_2(self):
        instance = SplitBytes(b"a" * small_chunk + b"b" * (small_chunk - 1),
                              small_chunk)
        self.assertEqual(len(instance), 2)
        iterator = iter(instance)
        chunk1 = six.next(iterator)
        self.assertEqual(b"a" * small_chunk, chunk1.read(small_chunk))
        chunk2 = six.next(iterator)
        self.assertEqual(b"b" * (small_chunk - 1), chunk2.read(small_chunk))

    def test_combine_streams(self):
        instance = CombineStreams(io.BytesIO(b"Hello") for i in range(20))
        result = b""
        for i in range(1000):
            read_result = instance.read(i)
            result += read_result
            if len(read_result) < i:
                break

        self.assertEqual(instance.read(10), b"")
        self.assertEqual(instance.read(), b"")
        self.assertEqual(result, b"Hello" * 20)

    def test_combine_streams_readall(self):
        instance = CombineStreams(io.BytesIO(b"Hello") for i in range(20))
        result = instance.read()

        self.assertEqual(instance.read(10), b"")
        self.assertEqual(instance.read(), b"")
        self.assertEqual(result, b"Hello" * 20)

if __name__ == '__main__':
    main()