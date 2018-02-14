import tempfile
import os
import shutil

from datafreeze.app import freeze
from morphium import Archive

from memorious.core import datastore


def export_tables(params):
    """Dump tables to csv files and upload to s3 bucket"""
    tempdir = tempfile.mkdtemp()
    for entry in params:
        table = datastore[entry["table"]]
        filename = entry.get("csv_filename", entry["table"] + ".csv")
        bucket = entry.get("bucket")
        freeze(table.all(), filename=filename, prefix=tempdir)
        file_path = os.path.join(tempdir, filename)

        archive = Archive(bucket=bucket)
        archive.upload_file(file_path)
    shutil.rmtree(tempdir)
