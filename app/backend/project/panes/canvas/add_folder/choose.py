"""Ask macOS which folder, and return its path.

The page cannot see a real path. This dialog runs in the Python
process, which can. Cancel is not an error: the path comes back empty.
"""

import subprocess
import sys


def choose_folder() -> str:
    """POSIX path of the folder the user picked, or "" if they cancelled."""
    if sys.platform != "darwin":
        raise ValueError("folder chooser is only available on macOS")
    result = subprocess.run(
        [
            "osascript",
            "-e",
            'POSIX path of (choose folder with prompt "Choose a folder")',
        ],
        capture_output=True,
        text=True,
    )
    if result.returncode != 0:
        return ""
    path = result.stdout.strip()
    if len(path) > 1 and path.endswith("/"):
        path = path[:-1]
    return path
