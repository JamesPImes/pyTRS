from setuptools import setup

from pyTRS import _constants


descrip = (
    'A library for parsing Public Land Survey System (PLSS) '
    'land descriptions into their component parts'
)

long_description = (
    'pyTRS is a pure Python library for parsing Public Land Survey System '
    '(PLSS) land descriptions (or "legal descriptions") into their component '
    'parts, in a format that is more useful for data analysis, GIS mapping, '
    'spreadsheets, and databases generally. It accounts for common variations '
    'in layout, abbreviations, typos, etc. and can therefore process a range '
    'of real-world data.'
    "\n\n"
    "Visit [the GitHub repository](https://github.com/JamesPImes/pyTRS) "
    "for a quickstart guide."
)


setup(
    name='pyTRS',
    version=_constants.__version__,
    packages=[
        'pyTRS', 'pyTRS.parser', 'pyTRS.check', 'pyTRS.quick', 'pyTRS.utils',
        'pyTRS.csv_suite', 'pyTRS.interface_tools'
    ],
    url=_constants.__website__,
    license='Modified Academic Public License',
    author=_constants.__author__,
    author_email=_constants.__email__,
    description=descrip,
    long_description=long_description,
    long_description_content_type="text/markdown",
    include_package_data=True
)
