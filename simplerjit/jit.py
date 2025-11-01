# jit.py
import os
import subprocess
import tempfile
import zipfile
import tarfile
from pathlib import Path
from urllib.request import urlretrieve
from functools import wraps
import hashlib
import inspect
import platform
import shutil

from .piler import generate_c_from_func

# Directories
TCC_DIR = Path.home() / ".simplerjit" / "tcc"
CACHE_DIR = Path.home() / ".simplerjit" / "cache"

# Detect OS and architecture
SYSTEM = platform.system().lower()
ARCH, _ = platform.architecture()

if SYSTEM == "windows":
    if "64" in ARCH:
        TCC_URL = "https://download-mirror.savannah.gnu.org/releases/tinycc/tcc-0.9.27-win64-bin.zip"
    else:
        TCC_URL = "https://download-mirror.savannah.gnu.org/releases/tinycc/tcc-0.9.27-win32-bin.zip"
    TCC_EXE = TCC_DIR / "tcc.exe"
elif SYSTEM == "linux":
    TCC_URL = "http://download.savannah.gnu.org/releases/tinycc/tcc-0.9.27.tar.bz2"
    TCC_EXE = TCC_DIR / "tcc"
else:
    raise RuntimeError(f"[SimplerJIT] Unsupported OS: {SYSTEM}")

def find_tcc_recursively(root: Path) -> Path | None:
    for path in root.rglob("tcc*"):
        if path.is_file() and os.access(path, os.X_OK):
            return path
    return None

def download_and_extract_tcc(target_dir: Path):
    target_dir.mkdir(parents=True, exist_ok=True)
    file_name = TCC_URL.split("/")[-1]
    archive_path = target_dir / file_name
    print(f"[SimplerJIT] Downloading TinyCC from {TCC_URL} ...")
    urlretrieve(TCC_URL, archive_path)

    if SYSTEM == "windows":
        print(f"[SimplerJIT] Extracting Windows TCC...")
        with zipfile.ZipFile(archive_path, "r") as zip_ref:
            zip_ref.extractall(target_dir)
    elif SYSTEM == "linux":
        print(f"[SimplerJIT] Extracting Linux TCC source...")
        with tarfile.open(archive_path, "r:bz2") as tar:
            tar.extractall(target_dir)
        tcc_src_dir = next(target_dir.iterdir())  # first folder inside
        print(f"[SimplerJIT] Compiling TCC for Linux...")
        subprocess.check_call(["./configure"], cwd=tcc_src_dir)
        subprocess.check_call(["make"], cwd=tcc_src_dir)
        shutil.copy(tcc_src_dir / "tcc", TCC_EXE)

    archive_path.unlink()
    print(f"[SimplerJIT] TinyCC ready at {TCC_EXE}")

def ensure_tcc() -> str:
    if TCC_EXE.exists() and os.access(TCC_EXE, os.X_OK):
        return str(TCC_EXE)

    found = find_tcc_recursively(Path.home())
    if found:
        return str(found)

    download_and_extract_tcc(TCC_DIR)

    if TCC_EXE.exists() and os.access(TCC_EXE, os.X_OK):
        return str(TCC_EXE)

    raise FileNotFoundError("[SimplerJIT] TinyCC could not be found or built.")

def _hash_func_source(py_func):
    source = inspect.getsource(py_func)
    return hashlib.sha256(source.encode("utf-8")).hexdigest()

def run_func(py_func, *args, cache=False):
    tcc_path = ensure_tcc()
    func_hash = _hash_func_source(py_func)
    CACHE_DIR.mkdir(parents=True, exist_ok=True)
    exe_path = CACHE_DIR / f"{py_func.__name__}_{func_hash}.exe" if SYSTEM=="windows" else CACHE_DIR / f"{py_func.__name__}_{func_hash}"

    # Run cached exe if available
    if cache and exe_path.exists():
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
            subprocess.check_call([tcc_path, "-o", str(exe_path), c_path])
            result = subprocess.check_output([str(exe_path)], universal_newlines=True).strip()
        else:
            result = subprocess.check_output([tcc_path, "-run", c_path], universal_newlines=True).strip()
        return float(result)
    finally:
        os.unlink(c_path)

def sjit(_func=None, *, cache=False):
    def decorator(py_func):
        @wraps(py_func)
        def wrapper(*args, **kwargs):
            return run_func(py_func, *args, cache=cache)
        return wrapper
    if _func is None:
        return decorator
    else:
        return decorator(_func)
