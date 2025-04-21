import io
from typing import Union

from minio import Minio
from minio.versioningconfig import VersioningConfig
from minio.commonconfig import ENABLED
from minio.error import S3Error

from . import ScrapedPage, S3Page
from ..config import Config

class S3Client():
  client: Minio
  _bucket_content: str
  _bucket_screenshot: str

  def __init__(self, config: Config):
    self._bucket_content = config.storage["bucket_content"]
    self._bucket_screenshot = config.storage["bucket_screenshot"]

    self.client = Minio(
      config.storage["s3"]["endpoint"],
      access_key = config.storage["s3"]["access_key"],
      secret_key = config.storage["s3"]["secret_key"],
      secure = False
    )

    for bucket in [self._bucket_content, self._bucket_screenshot]:
      if not self.client.bucket_exists(bucket): 
        self.client.make_bucket(bucket)

      self.client.set_bucket_versioning(bucket, VersioningConfig(ENABLED))

  def store_page(self, project_name: str, page: ScrapedPage):
    data = page['content'].encode('utf8')
    self.client.put_object(
      bucket_name = self._bucket_content, 
      object_name = f"{project_name}/{page['path']}", 
      data = io.BytesIO(page['content'].encode('utf8')),
      length = len(data),
      content_type = 'text/html',
      metadata = page['metadata'] # type: ignore
    )

    if (page['screenshot_path'] != None):
      screenshot_type = page['screenshot_path'].split('.')[-1]

      self.client.fput_object(
        bucket_name = self._bucket_screenshot,
        object_name = f"{project_name}/{page['path']}.{screenshot_type}", 
        file_path = page['screenshot_path'],
        content_type = f"image/{screenshot_type}",
      )


  def get_page_versions(self, project_name: str, path: str) -> list[str]:
    results = self.client.list_objects(self._bucket_content, f"{project_name}/{path}", include_version=True)
    return [(r.version_id) for r in results if r.version_id is not None]

  def get_page(self, project_name: str, path: str, version_id: Union[str, None]) -> Union[S3Page, None]: 
    response = None
    try:
      response = self.client.get_object(self._bucket_content, f"{project_name}/{path}", version_id=version_id)
      data = response.read()

      stats = self.client.stat_object(self._bucket_content, f"{project_name}/{path}")

      return {
        'content': data.decode('utf8'),
        'metadata': stats.metadata,
        'storage_metadata': {
          'version': response.version,
          'version_id': stats.version_id,
          'last_modified': stats.last_modified.isoformat(), # type: ignore
          'size': stats.size,
        }
      }

    except S3Error:
      return None

    finally:
      if response:
        response.close()
        response.release_conn()
