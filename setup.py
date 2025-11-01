from setuptools import setup, find_packages

setup(
    name="SimplerJIT",
    version="2.6",
    description="Ultra-lightweight Python JIT using TCC and SIMD",
    author="Intiha",
    url="https://github.com/Gund4422/SimplerJIT",
    packages=find_packages(),
    python_requires=">=3.8",
    install_requires=[
        "numpy>=1.21"
    ],
    include_package_data=True,
)



