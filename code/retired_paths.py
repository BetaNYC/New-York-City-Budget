"""
retired_paths.py — where the old PDF-parser CSVs live.

The old parse of each family-year the checked process has redone (data/pdf_years.csv) moved from
data/fyNN/<family>/ to data/retired/fyNN/<family>/, same file names (#218; data/retired/README.md).
The years not yet redone (FY2009–FY2017) stay under data/fyNN/<family>/. These helpers find a
family's files in whichever place they are, so the scripts that still read them keep working.

  family_dir(data_dir, "fy26", "schedule_c")   -> <data_dir>/retired/fy26/schedule_c (or <data_dir>/fy26/...)
  family_glob(data_dir, "schedule_c", "*.csv") -> every year's files, in fiscal-year order
  current_path("data/fy18/schedule_c/x.csv")   -> "data/retired/fy18/schedule_c/x.csv" once moved

data_dir is the repository's data/ folder (or a test's stand-in for it).
"""
import glob
import os
import re

def family_dir(data_dir, yy, family):
    """data/retired/<yy>/<family> if that year's old parse was retired, else data/<yy>/<family>."""
    retired = os.path.join(data_dir, "retired", yy, family)
    return retired if os.path.isdir(retired) else os.path.join(data_dir, yy, family)


def family_glob(data_dir, family, pattern="*"):
    """Every data/fyNN/<family>/<pattern> and data/retired/fyNN/<family>/<pattern>, sorted as if
    they were all still under data/fyNN/ (so fiscal years come out in order)."""
    paths = (glob.glob(os.path.join(data_dir, "fy*", family, pattern))
             + glob.glob(os.path.join(data_dir, "retired", "fy*", family, pattern)))
    return sorted(paths, key=lambda p: p.replace(os.sep + "retired" + os.sep, os.sep))


def current_path(path, root="."):
    """A data/fyNN/<family>/... path as recorded before the move (older crosswalks and sidecars
    carry them) -> where the file is now. Unchanged if it was not moved."""
    m = re.match(r"(.*?)data([\\/])(fy\d\d[\\/].*)$", path)
    if m and not os.path.exists(os.path.join(root, path)):
        moved = f"{m.group(1)}data{m.group(2)}retired{m.group(2)}{m.group(3)}"
        if os.path.exists(os.path.join(root, moved)):
            return moved
    return path


def fy_of(path):
    """'data/retired/fy18/schedule_c/x.csv' or 'data/fy18/...' -> 'fy18'. None if no fyNN segment."""
    m = re.search(r"(?:^|[\\/])(fy\d\d)[\\/]", path)
    return m.group(1) if m else None
