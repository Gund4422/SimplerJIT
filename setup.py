from setuptools import setup, find_packages

setup(
    name="SimplerJIT",
    version="0.1.0",
    description="Ultra-lightweight Python JIT using TCC and SIMD",
    author="Intiha",
    url="https://github.com/Gund4422/SimplerJIT",
    packages=find_packages(),
    python_requires=">=3.8",
    install_requires=[
        "numpy>=1.21"
    ],
    classifiers=[
        "Programming Language :: Python :: 3",
        "License :: OSI Approved :: WTFPL",
    ],
    include_package_data=True,
)

