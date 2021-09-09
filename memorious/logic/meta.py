# from typing_extensions import TypedDict
from typing import Optional, TypedDict


class MetaBase(TypedDict):
    crawler: Optional[str]
    foreign_id: Optional[str]
    source_url: Optional[str]
    title: Optional[str]
    author: Optional[str]
    publisher: Optional[str]
    file_name: Optional[str]
    retrieved_at: Optional[str]
    modified_at: Optional[str]
    published_at: Optional[str]
    headers: any
    keywords: any


class Meta(MetaBase, total=False):
    parent: any
    languages: any
    countries: any
    mime_type: any
