# jit.py
import os
import subprocess
import tempfile
import zipfile
from pathlib import Path
from urllib.request import urlretrieve
from functools import wraps
import hashlib
import inspect

from .piler import generate_c_from_func

TCC_URL = "https://download-mirror.savannah.gnu.org/releases/tinycc/tcc-0.9.27-win64-bin.zip"
TCC_DIR = Path.home() / ".simplerjit" / "tcc"
TCC_EXE = TCC_DIR / "tcc.exe"
CACHE_DIR = Path.home() / ".simplerjit" / "cache"

def find_tcc_recursively(root: Path) -> Path | None:
    """Recursively search for tcc.exe starting from root folder."""
    for path in root.rglob("tcc.exe"):
        if path.is_file():
            return path
    return None

def download_and_extract_tcc(target_dir: Path):
    target_dir.mkdir(parents=True, exist_ok=True)
    zip_path = target_dir / "tcc.zip"
    print("Downloading TinyCC...")
    urlretrieve(TCC_URL, zip_path)
    print("Extracting TinyCC...")
    with zipfile.ZipFile(zip_path, "r") as zip_ref:
        zip_ref.extractall(target_dir)
    zip_path.unlink()
    print(f"TinyCC installed to {target_dir}")

def ensure_tcc() -> str:
    """Ensure tcc.exe exists: check default, search recursively, or download."""
    if TCC_EXE.exists():
        return str(TCC_EXE)
    found = find_tcc_recursively(Path.home())
    if found:
        return str(found)
    download_and_extract_tcc(TCC_DIR)
    if TCC_EXE.exists():
        return str(TCC_EXE)
    raise FileNotFoundError("TinyCC could not be found or downloaded.")

def _hash_func_source(py_func):
    """Generate a hash of the function source for caching."""
    source = inspect.getsource(py_func)
    return hashlib.sha256(source.encode("utf-8")).hexdigest()

def run_func(py_func, *args, cache=False):
    """Compile Python function to C via SimplerJIT + TCC and run."""
    tcc_path = ensure_tcc()
    func_hash = _hash_func_source(py_func)
    CACHE_DIR.mkdir(parents=True, exist_ok=True)
    exe_path = CACHE_DIR / f"{py_func.__name__}_{func_hash}.exe"

    # If cached, run directly
    if cache and exe_path.exists():
        arg_list = [str(a) for a in args]
        result = subprocess.check_output([str(exe_path)], universal_newlines=True).strip()
        return float(result)

    # Generate C code
    c_code = generate_c_from_func(py_func)
    arg_list_str = ', '.join(map(str, args))
    wrapper = f"""
#include <stdio.h>
#include <math.h>

{c_code}

int main() {{
    long double result = {py_func.__name__}({arg_list_str});
    printf("%.20Lf\\n", result);
    return 0;
}}
"""
    # Temp C file
    with tempfile.NamedTemporaryFile(suffix=".c", delete=False) as f:
        f.write(wrapper.encode("utf-8"))
        c_path = f.name

    try:
        if cache:
            # Compile to exe and cache it
            subprocess.check_call([tcc_path, "-o", str(exe_path), c_path])
            result = subprocess.check_output([str(exe_path)], universal_newlines=True).strip()
        else:
            # Run directly via tcc -run
            result = subprocess.check_output([tcc_path, "-run", c_path],
                                             universal_newlines=True).strip()
        return float(result)
    finally:
        os.unlink(c_path)

def sjit(_func=None, *, cache=False):
    """Decorator for SimplerJIT with optional caching."""
    def decorator(py_func):
        @wraps(py_func)
        def wrapper(*args, **kwargs):
            # Only supports positional args
            return run_func(py_func, *args, cache=cache)
        return wrapper
    if _func is None:
        return decorator
    else:
        return decorator(_func)
