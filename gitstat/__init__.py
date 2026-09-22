"""gitstat — offline contribution analytics from a local git history."""

from .collect import Commit, collect, parse_log
from .aggregate import author_table, file_density, totals, weekly_heat

__version__ = "1.0.0"
