import logging
from typing import Optional, Dict, Any, cast, Literal
from utils.config import Project, Site, Route

try:
    from colorama import init, Fore, Style
    # Initialize colorama to work on all platforms
    init(autoreset=True)
    COLORS_AVAILABLE = True
except ImportError:
    # If colorama is not available, define dummy color constants
    COLORS_AVAILABLE = False
    class DummyColor:
        def __getattr__(self, name):
            return ""
    Fore = DummyColor()
    Style = DummyColor()

# Define color mappings for different log levels
LEVEL_COLORS = {
    logging.DEBUG: Fore.CYAN,
    logging.INFO: Fore.GREEN,
    logging.WARNING: Fore.YELLOW,
    logging.ERROR: Fore.RED,
    logging.CRITICAL: Fore.RED + Style.BRIGHT
}

class CTIFormatter(logging.Formatter):
  """
  Custom formatter that adds CTI-specific context to log messages with colored output
  """
  def __init__(self, fmt=None, datefmt=None, style: Literal['%', '{', '$'] = '%'):
    if not fmt:
      fmt = '%(asctime)s\t%(name)s\t%(levelname)s\t%(message)s'
    super().__init__(fmt, datefmt, style)
    
  def format(self, record):
    # Extract context from the record if it exists
    project_name = getattr(record, 'project_name', '')
    site_name = getattr(record, 'site_name', '')
    route_path = getattr(record, 'route_path', '')
    url = getattr(record, 'url', '')
    
    # Build prefix
    prefix = ""
    if project_name:
        prefix += f"{project_name}/"
    if site_name:
        prefix += f"{site_name}/"
    if route_path:
        prefix += f"{route_path}"
    if url:
      if record.levelno > logging.DEBUG:
        # For higher levels, show shortened URL without scheme
        shortened_url = url
        if shortened_url.startswith(('http://', 'https://')):
          scheme_end = shortened_url.find('//') + 2
          shortened_url = shortened_url[scheme_end:]
        # Take only the first 10 chars
        shortened_url = shortened_url[:16]
        prefix += f" ({shortened_url})"
      else:
        # For debug level, show the full URL
        prefix += f" ({url})"
    if prefix:
        prefix += "\t"
    
    # Get color for the current log level
    level_color = LEVEL_COLORS.get(record.levelno, "")
    
    # Format the level name with color if available
    if COLORS_AVAILABLE:
        colored_levelname = f"{level_color}{record.levelname}{Style.RESET_ALL}"
        record.levelname = colored_levelname
    
    # Append prefix to message
    record.message = record.getMessage()
    
    record.msg = f"{prefix}{record.msg}"
    
    return super().format(record)

class CTILogger(logging.Logger):
  """
  Logger specialized for CTI operations with context awareness
  """
  def __init__(self, name, level=logging.NOTSET):
    super().__init__(name, level)
    self._context = {
      'project_name': "",
      'site_name': "",
      'route_path': "",
      'url': ""
    }
  
  def set_context(self, project: Optional[Project] = None, site: Optional[Site] = None, 
                  route: Optional[Route] = None, url: Optional[str] = None):
    """Set the context for subsequent log messages"""
    if project:
      self._context['project_name'] = project['name']
    if site:
      self._context['site_name'] = site['name']
    if route:
      self._context['route_path'] = route['path']
    if url:
      self._context['url'] = url
    return self
  
  def _log(self, level, msg, args, exc_info=None, extra=None, stack_info=False, stacklevel=1, **kwargs):
    """Override _log to include context info in extra"""
    if extra is None:
      extra = {}
        
    # Add context to extra
    for key, value in self._context.items():
      if value is not None:
        extra[key] = value
          
    return super()._log(level, msg, args, exc_info, extra, stack_info, stacklevel, **kwargs)

# Register our logger class
logging.setLoggerClass(CTILogger)

# Configure the root logger only once
def configure_logging(level=logging.INFO):
  """Configure the root logger with our custom formatter"""
  root_logger = logging.getLogger()
  
  # Clear any existing handlers to prevent duplication
  for handler in root_logger.handlers[:]:
    root_logger.removeHandler(handler)
    
  # Add a single console handler with our formatter
  console_handler = logging.StreamHandler()
  console_handler.setFormatter(CTIFormatter())
  root_logger.addHandler(console_handler)
  root_logger.setLevel(level)

def get_logger(name: str) -> CTILogger:
  """Get a logger instance with the CTI formatter applied"""
  return cast(CTILogger, logging.getLogger(name))

