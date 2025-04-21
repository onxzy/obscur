from typing import TypedDict

class S3(TypedDict):
  port: int
  endpoint: str
  region: str
  access_key: str
  secret_key: str

class Storage(TypedDict):
  s3: S3

  bucket_content: str
  bucket_screenshot: str