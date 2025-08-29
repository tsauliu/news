#!/usr/bin/env python3
import sys
import os
sys.path.insert(0, os.path.dirname(__file__))
from cdn_server import run_server

if __name__ == "__main__":
    run_server(80, '0.0.0.0')