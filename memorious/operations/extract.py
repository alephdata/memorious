import zipfile
import os
import tarfile
import subprocess

from memorious.util import random_filename

ZIP_MIME_TYPES = [
    'application/zip',
    'application/x-zip',
    'multipart/x-zip',
    'application/zip-compressed',
    'application/x-zip-compressed',
]

TAR_MIME_TYPES = [
    'application/tar',
    'application/x-tar',
    'application/x-tgz',
    'application/x-gtar',
    'application/x-gzip',
    'application/gzip',
]

SEVENZIP_MIME_TYPES = [
    'application/x-7z-compressed',
    'application/7z-compressed'
]


def extract_zip(file_path, extract_dir, context):
    with zipfile.ZipFile(file_path, "r") as zip_ref:
        if zip_ref.testzip() is not None:
            context.log.warning("Bad zip file: %s", file_path)
        zip_ref.extractall(extract_dir)
        extracted_files = []
        for name in zip_ref.namelist():
            file_path = os.path.join(extract_dir, name)
            if os.path.isfile(file_path):
                extracted_files.append(file_path)
        return extracted_files


def extract_tar(file_path, extract_dir, context):
    with tarfile.open(file_path, "r:*") as tar_ref:
        extracted_files = []
        for name in tar_ref.getnames():
            # Make it safe. See warning at
            # https://docs.python.org/2/library/tarfile.html#tarfile.TarFile.extractall  # noqa
            if name.startswith("..") or name.startswith("/"):
                context.log.info(
                    "Bad path %s while extracting archive at %s",
                    name, file_path
                )
            else:
                tar_ref.extract(name, extract_dir)
                file_path = os.path.join(extract_dir, name)
                if os.path.isfile(file_path):
                    extracted_files.append(file_path)
        return extracted_files


def extract_7zip(file_path, extract_dir, context):
    return_code = subprocess.call(
        ['7z', 'x', file_path, '-r', '-o%s' % extract_dir])
    if return_code != 0:
        context.log.warning(
            "Couldn't extract file: %s", file_path
        )
        return
    extracted_files = []
    for root, directories, filenames in os.walk(extract_dir):
        for filename in filenames:
            extracted_files.append(os.path.join(root, filename))
    return extracted_files


def extract(context, data):
    """Extract a compressed file"""
    with context.http.rehash(data) as result:
        file_path = result.file_path
        content_type = result.content_type
        extract_dir = random_filename(context.work_path)
        if content_type in ZIP_MIME_TYPES:
            extracted_files = extract_zip(file_path, extract_dir, context)
        elif content_type in TAR_MIME_TYPES:
            extracted_files = extract_tar(file_path, extract_dir, context)
        elif content_type in SEVENZIP_MIME_TYPES:
            extracted_files = extract_7zip(file_path, extract_dir, context)
        else:
            context.log.warning(
                "Unsupported archive content type: %s", content_type
            )
            return
        extracted_content_hashes = {}
        for path in extracted_files:
            relative_path = os.path.relpath(path, extract_dir)
            content_hash = context.store_file(path)
            extracted_content_hashes[relative_path] = content_hash
            data['content_hash'] = content_hash
            data['file_name'] = relative_path
            context.emit(data=data.copy())
