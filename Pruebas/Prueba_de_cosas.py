# --- PARCHE PARA PYTHON 3.13 ---
import sys
try:
    import pkg_resources
except ImportError:
    try:
        from setuptools import pkg_resources
    except ImportError:
        import pip
        print("Intentando parche de emergencia...")
        # Esto instala una versión específica que todavía tiene el soporte
        import subprocess
        subprocess.check_call([sys.executable, "-m", "pip", "install", "setuptools==69.5.1"])
# -------------------------------

import face_recognition_models # Ahora ya no debería dar error