# Configuration file for the Sphinx documentation builder.
#
# For the full list of built-in configuration values, see the documentation:
# https://www.sphinx-doc.org/en/master/usage/configuration.html
import os
import sys

# -- Project information -----------------------------------------------------
# https://www.sphinx-doc.org/en/master/usage/configuration.html#project-information

project = 'CubesatSimulator'
copyright = '2025, Adrian Payne'
author = 'Adrian Payne'
release = '1.0 RC1'

# -- General configuration ---------------------------------------------------
# https://www.sphinx-doc.org/en/master/usage/configuration.html#general-configuration

extensions = []

templates_path = ['_templates']
exclude_patterns = []

# Add your project root so Sphinx can find your packages
sys.path.insert(0, os.path.abspath('../../'))

autodoc_mock_imports = [
    "PySide6",
    "pyvista",
    "pyvistaqt",
    "vtk",
    "cartopy",
    "cartopy.crs",
    "matplotlib",
    "orekit",
]

# Extensions
extensions = [
    'sphinx.ext.autodoc',          # automatic doc generation from docstrings
    'sphinx.ext.napoleon',         # Google / NumPy style
]

# Choose theme
html_theme = 'sphinx_rtd_theme'

# -- Options for HTML output -------------------------------------------------
# https://www.sphinx-doc.org/en/master/usage/configuration.html#options-for-html-output

html_theme = "pydata_sphinx_theme"

# Optional: theme configuration
html_theme_options = {
    "navbar_end": ["search-field.html"],
    "navigation_depth": 3,
    "show_prev_next": False,
}

html_static_path = ['_static']
