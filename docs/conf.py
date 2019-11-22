# Configuration file for the Sphinx documentation builder.
#
# This file only contains a selection of the most common options. For a full
# list see the documentation:
# https://www.sphinx-doc.org/en/master/usage/configuration.html

# -- Path setup --------------------------------------------------------------

# If extensions (or modules to document with autodoc) are in another directory,
# add these directories to sys.path here. If the directory is relative to the
# documentation root, use os.path.abspath to make it absolute, like shown here.
#
import os
import sys
sys.path.insert(0, os.path.abspath('..'))


# -- Project information -----------------------------------------------------

project = 'Channels'
copyright = '2019, Sander Voerman'
author = 'Sander Voerman'

# The full version, including alpha/beta/rc tags
release = '0.5'


# -- General configuration ---------------------------------------------------

# If your documentation needs a minimal Sphinx version, state it here.
#
needs_sphinx = '2.2'

# Add any Sphinx extension module names here, as strings. They can be
# extensions coming with Sphinx (named 'sphinx.ext.*') or your custom
# ones.
extensions = [
    'sphinx.ext.autodoc',
    'sphinx.ext.intersphinx',
]

# List of patterns, relative to source directory, that match files and
# directories to ignore when looking for source files.
# This pattern also affects html_static_path and html_extra_path.
exclude_patterns = ['_build', 'Thumbs.db', '.DS_Store']

# The default domain.
primary_domain = "py"

# The default reStructuredText role.
default_role = 'any'


# -- Options for HTML output -------------------------------------------------

# The theme to use for HTML and HTML Help pages.  See the documentation for
# a list of builtin themes.
#
html_theme = 'alabaster'

html_static_path = ['static']

html_theme_options = {
    'nosidebar': True,
    'canonical_url': '/channels/'
}


# -- Extension configuration -------------------------------------------------

# -- Options for intersphinx extension ---------------------------------------

# Refer to the Python standard library.
intersphinx_mapping = {'python': ('https://docs.python.org/3', None)}


# -- Options for autodoc extension -------------------------------------------
