def next_path(data):
    return data.get('path') + [data.get('url', '')]
