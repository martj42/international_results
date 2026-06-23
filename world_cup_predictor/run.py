#!/usr/bin/env python3
"""Convenience launcher so the app can be started without the -m flag.

    python world_cup_predictor/run.py          # interactive predictor
    python world_cup_predictor/run.py --train  # (re)train the model first

It simply ensures the repository root is importable and delegates to the
package modules.
"""

import os
import sys

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

if __name__ == "__main__":
    if "--train" in sys.argv:
        from world_cup_predictor.train import main as train_main

        train_main()
    from world_cup_predictor.predict import main as predict_main

    predict_main()
