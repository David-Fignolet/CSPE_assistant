from setuptools import setup, find_packages

setup(
    name="cspe_assistant",
    version="0.1.0",
    packages=find_packages(where="src"),
    package_dir={"": "src"},
    install_requires=[
        "pytz>=2023.3",
        "python-dateutil>=2.8.2"
    ],
    python_requires=">=3.8",
)
