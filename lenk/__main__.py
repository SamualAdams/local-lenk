#!/usr/bin/env python3
"""Package entrypoint to support `python -m lenk`.

Delegates to the viewer app's main() in the Django-like layout.
"""

from .apps.viewer.app import main


if __name__ == "__main__":
    main()
