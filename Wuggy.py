#!/usr/bin/env python
from ui.wx.app import WuggyApp
import argparse

if __name__ == "__main__":
    parser = argparse.ArgumentParser(
        description="Wuggy - A Multilingual Pseudoword Generator"
    )
    parser.add_argument("--data", help="specify a non-default data directory", action="store")
    args = parser.parse_args()

    wuggy = WuggyApp(data_path=args.data)
    wuggy.MainLoop()
