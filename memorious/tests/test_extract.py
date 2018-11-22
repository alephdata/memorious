import os
import tempfile
from memorious.operations.extract import extract_7zip, extract_tar, extract_zip


def test_extract_7zip(context):
    file_path = os.path.realpath(__file__)
    archive_path = os.path.normpath(os.path.join(
        file_path, "../testdata/test.7z"
    ))
    extract_dir = tempfile.mkdtemp(prefix="memorious_test")
    assert extract_7zip(archive_path, extract_dir, context) == [
        os.path.join(extract_dir, "test/a/1.txt")
    ]


def test_extract_zip(context):
    file_path = os.path.realpath(__file__)
    archive_path = os.path.normpath(os.path.join(
        file_path, "../testdata/test.zip"
    ))
    extract_dir = tempfile.mkdtemp(prefix="memorious_test")
    assert extract_zip(archive_path, extract_dir, context) == [
        os.path.join(extract_dir, "test/a/1.txt")
    ]


def test_extract_tar(context):
    file_path = os.path.realpath(__file__)
    archive_path = os.path.normpath(os.path.join(
        file_path, "../testdata/test.tar.gz"
    ))
    extract_dir = tempfile.mkdtemp(prefix="memorious_test")
    assert extract_tar(archive_path, extract_dir, context) == [
        os.path.join(extract_dir, "test/a/1.txt")
    ]
