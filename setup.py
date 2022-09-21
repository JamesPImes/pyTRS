import setuptools
from setuptools import setup


description = (
    'A library for parsing Public Land Survey System (PLSS) land '
    'descriptions.'
)

long_description = (
    'pyTRS (imported as `pytrs`) is a pure Python library for parsing '
    'Public Land Survey System (PLSS) land descriptions (or "legal '
    'descriptions") for use in data analysis, GIS mapping, spreadsheets, '
    'etc. It accounts for common variations in layout, abbreviations, '
    'typos, etc. and can therefore process a range of real-world data.'
    "\n\n"
    "Visit [the GitHub repository](https://github.com/JamesPImes/pyTRS) "
    "for a quickstart guide, or read the "
    "[official documentation](https://pytrs.readthedocs.io/)."
)

MODULE_DIR = "pytrs"


def get_constant(constant):
    setters = {
        "version": "__version__ = ",
        "author": "__author__ = ",
        "author_email": "__email__ = ",
        "url": "__website__ = "
    }
    var_setter = setters[constant]
    with open(rf".\{MODULE_DIR}\_constants.py", "r") as file:
        for line in file:
            if line.startswith(var_setter):
                return line[len(var_setter):].strip('\'\n \"')
        raise RuntimeError(f"Could not get {constant} info.")


setup(
    name='pyTRS',
    version=get_constant("version"),
    packages=setuptools.find_packages(),
    url=get_constant("url"),
    license='Modified Academic Public License',
    author=get_constant("author"),
    author_email=get_constant("author_email"),
    description=description,
    long_description=long_description,
    long_description_content_type="text/markdown",
    include_package_data=True
)
