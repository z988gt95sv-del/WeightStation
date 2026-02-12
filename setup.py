from setuptools import setup, find_packages

setup(
    name="WeightStation",
    version="1.0.0",
    description="Weight Station Management System",
    author="Your Name",
    python_requires=">=3.8",
    install_requires=[
        "pyserial>=3.5",
    ],
    entry_points={
        "console_scripts": [
            "weightstation=main:main",
        ],
    },
)
