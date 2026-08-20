#!/usr/bin/env python3
# -*- coding: utf-8 -*-

"""
Wrapper de to_metricool.py para la carpeta automation.
Permite importar o ejecutar to_metricool directamente desde automation/.
"""

import os
import sys

# Permitir importar desde la raíz del proyecto
current_dir = os.path.dirname(os.path.abspath(__file__))
parent_dir = os.path.dirname(current_dir)
if parent_dir not in sys.path:
    sys.path.insert(0, parent_dir)

from to_metricool import init_firebase_storage, upload_to_storage, generate_metricool_csv

if __name__ == "__main__":
    import subprocess
    subprocess.run([sys.executable, os.path.join(parent_dir, "to_metricool.py")])
