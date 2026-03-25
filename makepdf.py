# This script has been replaced by makefiletype.py which supports multiple file types
# and command-line arguments. Please use makefiletype.py instead.
#
# Example usage:
#   python makefiletype.py --type pdf --size 5120
#   python makefiletype.py --type pdf --size 51200
#   python makefiletype.py --type pdf --size 5120000
#
# Run `python makefiletype.py --help` for full usage information.

import sys
import subprocess

if __name__ == "__main__":
    print("makepdf.py has been replaced by makefiletype.py.")
    print("Redirecting to: python makefiletype.py --type pdf --size 5120")
    sys.exit(subprocess.call([sys.executable, "makefiletype.py", "--type", "pdf", "--size", "5120"]))