# jit.py
import numpy as np
import subprocess
import tempfile
from pathlib import Path
from piler import generate_simd_c  # import the transpiler

def jit(tcc_path):
    def decorator(func):
        def wrapper(a: np.ndarray, b: np.ndarray, out: np.ndarray):
            assert a.dtype == b.dtype == out.dtype == np.float32, "Only float32 supported"
            n = a.size
            c_code = generate_simd_c(["a","b","out"], n)

            with tempfile.NamedTemporaryFile(suffix=".c", delete=False) as tmp:
                tmp.write(c_code.encode())
                tmp_path = tmp.name

            # compile & run in milliseconds
            subprocess.run([tcc_path, "-run", tmp_path], check=True)

            Path(tmp_path).unlink(missing_ok=True)
        return wrapper
    return decorator
