
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


def get_version():
    version_var_setter = "__version__ = "
    with open(r".\pytrs\_constants.py", "r") as file:
        for line in file:
            if line.startswith(version_var_setter):
                version = line[len(version_var_setter):].strip('\'\n \"')
                return version
        raise RuntimeError("Could not get __version__ info.")


setup(
    name='pyTRS',
    version=get_version(),
    packages=[
        'pytrs',
        'pytrs.parser',
        'pytrs.check',
        'pytrs.quick',
        'pytrs.utils',
        'pytrs.csv_suite',
        'pytrs.interface_tools'
    ],
    url='https://github.com/JamesPImes/pyTRS',
    license='Modified Academic Public License',
    author='James P. Imes',
    author_email='jamesimes@gmail.com',
    description=description,
    long_description=long_description,
    long_description_content_type="text/markdown",
    include_package_data=True
)
