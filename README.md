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
from simplerjit import sjit

@sjit(cache=True)
def compute():
    result = 0
    for i in range(10_000_000):
        result += i
    return result

print(compute())
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
