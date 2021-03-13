
from setuptools import setup


description = (
    'A library for parsing Public Land Survey System (PLSS) '
    'land descriptions into their component parts'
)

long_description = (
    'pyTRS (imported as `pytrs`) is a pure Python library for parsing '
    'Public Land Survey System (PLSS) land descriptions (or "legal '
    'descriptions") into their component parts, in a format that is '
    'more useful for data analysis, GIS mapping, spreadsheets, and '
    'databases generally. It accounts for common variations in layout, '
    'abbreviations, typos, etc. and can therefore process a range of '
    'real-world data.'
    "\n\n"
    "Visit [the GitHub repository](https://github.com/JamesPImes/pyTRS) "
    "for a quickstart guide."
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
                version = line[len(var_setter):].strip('\'\n \"')
                return version
        raise RuntimeError(f"Could not get {constant} info.")


setup(
    name='pyTRS',
    version=get_constant("version"),
    packages=[
        'pytrs',
        'pytrs.parser',
        'pytrs.check',
        'pytrs.quick',
        'pytrs.utils',
        'pytrs.csv_suite',
        'pytrs.interface_tools'
    ],
    url=get_constant("url"),
    license='Modified Academic Public License',
    author=get_constant("author"),
    author_email=get_constant("author_email"),
    description=description,
    long_description=long_description,
    long_description_content_type="text/markdown",
    include_package_data=True
)
