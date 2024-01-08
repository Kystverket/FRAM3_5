from pathlib import Path
from setuptools import setup, find_packages

setup(
    name="fram",
    version=(Path(__file__).parent / "fram" / "generelle_hjelpemoduler" / "version.py")
    .read_text()
    .split("=")[-1]
    .replace('"', "")
    .strip(),
    url="https://github.com/kystverket/FRAM",
    author="Menon Economics AS",
    author_email="post@menon.no",
    description=(Path(__file__).parent / "README.rst").read_text(),
    packages=find_packages(),
    include_package_data=True,
    entry_points={"console_scripts": ["kjor-fram=fram.generelle_hjelpemoduler.main_script:run"]},
    install_requires=(
        (Path(__file__).parent / "requirements.txt").read_text().splitlines(),
    ),
)
