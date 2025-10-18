#!/usr/bin/env python3
"""Project entry script, mirroring Django's manage.py style.

This delegates to the viewer app's main function so you can run:
    python manage.py
"""

from lenk.apps.viewer.app import main


if __name__ == "__main__":
    main()

