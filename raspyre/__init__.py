from pkgutil import extend_path
from ._version import get_versions

__path__ = extend_path(path, __name__)

__version__ = get_versions()['version']
del get_versions
