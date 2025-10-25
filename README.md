# SimplerJIT

**SimplerJIT** (`@sjit`) is a lightweight Python Just-In-Time (JIT) compiler that converts Python functions to C using TinyCC (TCC) for blazing-fast execution. It’s designed for **local builds**, caching, and easy experimentation with multiple optimization strategies. `NOTE: THIS IS FOR CURRENTLY ONLY WIN64, PLEASE DO NOT DOWNLOAD IF ON LINUX. WE WILL EVENTUALLY ADD SUPPORT FOR WIN32 AND LINUX`

## Features

* **Python → C Compilation:** Converts Python functions to C code for fast execution.
* **Caching Support:** Optionally cache compiled binaries for repeated use.
* **Local Installation:** No PyPI; install and use directly on your machine.
* **Minimal Dependencies:** Only requires Python 3.x and TCC (auto-downloadable).

## Installation

Clone the repo and install in editable mode:

```bash
git clone <repo-url>
cd SimplerJIT
pip install -e .
```

This allows you to modify SimplerJIT locally and test changes immediately.

## Usage

### Basic Example

```python
import time
from simplerjit import sjit

# --- SimplerJIT version ---
@sjit(cache=True)
def count_to_sjit(n):
    x = 0
    for i in range(n):
        x += 1
    return x

# --- Pure Python version ---
def count_to_py(n):
    x = 0
    for i in range(n):
        x += 1
    return x

N = 248_669_921

print(f"Counting to {N:,}...\n")

# --- SJIT run ---
start = time.time()
sjit_result = count_to_sjit(N)
sjit_elapsed = time.time() - start

# --- Python run ---
start = time.time()
py_result = count_to_py(N)
py_elapsed = time.time() - start

# --- Compare ---
print(f"SimplerJIT Result: {sjit_result}")
print(f"SimplerJIT Time:   {sjit_elapsed:.6f} sec")
print(f"Python Result:     {py_result}")
print(f"Python Time:       {py_elapsed:.6f} sec")

speedup = py_elapsed / sjit_elapsed if sjit_elapsed > 0 else 0
print(f"\nSpeedup: {speedup:.2f}x faster")
```

### Notes

* Only **positional arguments** are supported.
* Functions are automatically converted to C and executed via TCC.
* Caching speeds up repeated executions.

### Advanced: Custom Version / Loop Unrolling

SimplerJIT supports aggressive **32× loop unrolling** and uses `long double` internally for high-precision arithmetic.

```python
@sjit(cache=True)
def sum_squares(n):
    result = 0
    for i in range(n):
        result += i*i
    return result
```

## Contributing

Fork, tweak, and submit pull requests! Performance improvements, bug fixes, and new JIT features are welcome.

## License

GPL v3 License. See `LICENSE` for details.
