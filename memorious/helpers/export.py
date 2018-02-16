import tempfile
import os
import shutil
from datetime import datetime
import mimetypes
import logging

from datafreeze.app import freeze
import boto3

from memorious.core import datastore
from memorious.settings import ARCHIVE_AWS_KEY_ID, ARCHIVE_AWS_SECRET


log = logging.getLogger(__name__)
TAG_LATEST = 'latest'
PREFIX = 'data'


def s3_upload(bucket, file_path):
    """
    Upload a given file to a s3 bucket. Stores 2 versions: 1 timestamped
    version and one latest version.
    """
    session = boto3.Session(aws_access_key_id=ARCHIVE_AWS_KEY_ID,
                            aws_secret_access_key=ARCHIVE_AWS_SECRET)
    client = session.client('s3')
    file_name = os.path.basename(file_path)
    mime_type, _ = mimetypes.guess_type(file_name)
    mime_type = mime_type or 'application/octet-stream'
    tag = datetime.utcnow().date().isoformat()
    key_name = os.path.join(PREFIX, tag, file_name)
    log.info("Uploading [%s]: %s", bucket, key_name)
    args = {
        'ContentType': mime_type,
        'ACL': 'public-read',
    }
    client.upload_file(file_path, bucket, key_name, ExtraArgs=args)
    copy_name = os.path.join(PREFIX, TAG_LATEST, file_name)
    copy_source = {'Key': key_name, 'Bucket': bucket}
    client.copy(copy_source, bucket, copy_name, ExtraArgs=args)
    log.info('File available at http://%s/%s', bucket, key_name)


def export_tables(params):
    """Dump tables to csv files and upload to s3 bucket"""
    tempdir = tempfile.mkdtemp()
    for entry in params:
        table = datastore[entry["table"]]
        filename = entry.get("csv_filename", entry["table"] + ".csv")
        bucket = entry.get("bucket")
        freeze(table.all(), filename=filename, prefix=tempdir)
        file_path = os.path.join(tempdir, filename)
        s3_upload(bucket, file_path)
    shutil.rmtree(tempdir)
