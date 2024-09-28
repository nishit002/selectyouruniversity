from setuptools import setup, find_packages

setup(
    name='selectyouruniversity',
    version='0.1',
    packages=find_packages(),
    include_package_data=True,
    package_data={
        '': ['selectyouruniversity/*.xlsx'],  # Include the Excel files in the package
    },
    install_requires=[
        'streamlit',
        'pandas',
        'openpyxl',
        'pkg_resources',
    ],
)
