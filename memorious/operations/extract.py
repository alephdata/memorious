import tempfile
import zipfile
import os
import tarfile
import py7zlib


def extract_zip(file_path, extract_dir):
    with zipfile.ZipFile(file_path, "r") as zip_ref:
        zip_ref.extractall(extract_dir)
        extracted_files = [os.path.join(extract_dir, path)
                           for path in zip_ref.namelist()]
        return extracted_files


def extract_tar(file_path, extract_dir, context):
    with tarfile.open(file_path, "r:*") as tar_ref:
        extracted_files = []
        for name in tar_ref.getnames():
            # Make it safe. See warning at
            # https://docs.python.org/2/library/tarfile.html#tarfile.TarFile.extractall #noqa
            if name.startswith("..") or name.startswith("/"):
                context.log.info(
                    "Bad path %s while extracting archive at %s",
                    name, file_path
                )
            else:
                tar_ref.extract(name, extract_dir)
                extracted_files.append(os.path.join(extract_dir, name))
        return extracted_files


def extract_7zip(file_path, extract_dir):
    with open(file_path, "rb+") as fp:
        archive = py7zlib.Archive7z(fp)
        extracted_files = []
        for name in archive.getnames():
            outfilename = os.path.join(extract_dir, name)
            outdir = os.path.dirname(outfilename)
            if not os.path.exists(outdir):
                os.makedirs(outdir)
            with open(outfilename, 'wb') as outfile:
                outfile.write(archive.getmember(name).read())
            extracted_files.append(outfilename)
        return extracted_files


def extract(context, data):
    """Extract a compressed file"""
    with context.http.rehash(data) as result:
        file_path = result.file_path
        content_type = result.content_type
        content_hash = result.content_hash
        extract_dir = tempfile.mkdtemp(prefix="memorious_"+content_hash)
        # TODO: contenttype may vary. Include more.
        if content_type == "application/zip":
            extracted_files = extract_zip(file_path, extract_dir)
        elif content_type == "application/x-gzip":
            extracted_files = extract_tar(file_path, extract_dir, context)
        elif content_type == "application/x-7z-compressed":
            extracted_files = extract_7zip(file_path, extract_dir)
        else:
            context.log.warning(
                "Unsupported archive content type: %s", content_type
            )
            return
        data["extracted_files"] = extracted_files
        context.emit(data=data)
