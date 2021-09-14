from typing import TypedDict


class DataBase(TypedDict):
    url: str
    request_id: str
    status_code: int
    content_hash: str
    headers: dict
    retrieved_at: str
    modified_at: str


class Data(DataBase, total=False):
    schema: str
    properties: dict
    entity_id: str
