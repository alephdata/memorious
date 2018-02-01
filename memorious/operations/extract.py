import tempfile
import zipfile
import os
import tarfile


def extract(context, data):
    """Extract a compressed file"""
    with context.http.rehash(data) as result:
        file_path = result.file_path
        content_type = result.content_type
        content_hash = result.content_hash
        extract_dir = tempfile.mkdtemp(prefix="memorious_"+content_hash)
        # TODO: contenttype may vary. Include more.
        if content_type == "application/zip":
            with zipfile.ZipFile(file_path, "r") as zip_ref:
                zip_ref.extractall(extract_dir)
                extracted_files = [os.path.join(extract_dir, path)
                                   for path in zip_ref.namelist()]
            data["extracted_files"] = extracted_files
            context.emit(data=data)
        if content_type == "application/x-gzip":
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
            data["extracted_files"] = extracted_files
            context.emit(data=data)