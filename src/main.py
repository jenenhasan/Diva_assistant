
import sys
import os
sys.path.insert(0, os.path.dirname(__file__))
sys.path.insert(0, os.path.join(os.path.dirname(__file__), ".."))

from app import create_app


def main():
    app = create_app()
    app.run()


if __name__ == "__main__":
    main()