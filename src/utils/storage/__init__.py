from typing import TypedDict, Union

class PageMetadata(TypedDict):
  url: str

class ScrapedPage(TypedDict):
  path: str
  content: str
  screenshot_path: Union[None, str]
  metadata: PageMetadata


class S3StorageMetadata(TypedDict):
  version: int
  version_id: str
  last_modified: str
  size: str

class S3Page(TypedDict):
  content: str
  metadata: PageMetadata
  storage_metadata: S3StorageMetadata