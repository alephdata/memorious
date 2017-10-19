
WEB = [
    'text/html',
    'text/plain',
    'text/xml',
    'application/xml',
]

IMAGES = [
    'image/jpeg',
    'image/bmp',
    'image/png',
    'image/tiff',
    'image/gif',
    'application/postscript',
    'image/vnd.dxf',
    'image/svg+xml',
    'image/x-pict',
    'image/x-ms-bmp'
]

MEDIA = [
    'audio/mpeg',
    'video/x-flv',
    'video/mp4',
    'video/mp2t',
    'video/3gpp',
    'video/quicktime',
    'video/x-msvideo',
    'video/x-ms-wmv',
]

DOCUMENTS = [
    'application/vnd.ms-excel',
    'application/msword',
    'application/pdf',
    '.pdf',  # seen in the wild (TM)
    'application/vnd.ms-powerpoint',
    'text/richtext',
    'application/vnd.oasis.opendocument.text',
    'application/rtf',
    'application/vnd.oasis.opendocument.spreadsheet',
    'application/x-rtf',
    'application/vnd.oasis.opendocument.graphics',
    'application/vnd.oasis.opendocument.presentation',
    'application/vnd.openxmlformats-officedocument.spreadsheetml.sheet', # noqa
    'application/vnd.openxmlformats-officedocument.wordprocessingml.document', # noqa
    'application/vnd.openxmlformats-officedocument.presentationml.presentation' # noqa
]

ARCHIVES = [
    'application/zip',
    'application/x-rar-compressed',
    'application/x-tar',
    'application/x-gzip',
    'application/x-7z-compressed'
]

ASSETS = [
    'text/css',
    'application/javascript',
    'application/json',
    'image/x-icon',
    'application/rss+xml',
    'application/atom+xml',
    'application/opensearchdescription+xml',
]

GROUPS = {
    'web': WEB,
    'images': IMAGES,
    'media': MEDIA,
    'documents': DOCUMENTS,
    'archives': ARCHIVES,
    'assets': ASSETS
}

KNOWN = WEB + IMAGES + MEDIA + DOCUMENTS + ARCHIVES + ASSETS
NON_HTML = [t for t in KNOWN if t not in WEB]
