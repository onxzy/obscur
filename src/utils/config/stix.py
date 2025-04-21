from typing import TypedDict, Optional

class StixMalware(TypedDict):
  name: Optional[str]
  aliases: Optional[list[str]]
  is_family: bool
