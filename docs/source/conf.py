# Configuration file for the Sphinx documentation builder.
#
# This file only contains a selection of the most common options. For a full
# list see the documentation:
# http://www.sphinx-doc.org/en/master/config

# -- Path setup --------------------------------------------------------------

# If extensions (or modules to document with autodoc) are in another directory,
# add these directories to sys.path here. If the directory is relative to the
# documentation root, use os.path.abspath to make it absolute, like shown here.
#
import os
import sys
sys.path.insert(0, os.path.abspath('../..'))

from recommonmark.transform import AutoStructify

# -- Project information -----------------------------------------------------

project = 'Runway Model SDK'
copyright = '2019, Runway AI, Inc.'
author = 'Runway AI, Inc.'

# The full version, including alpha/beta/rc tags
release = 'v0.1.0'


# -- General configuration ---------------------------------------------------

# Add any Sphinx extension module names here, as strings. They can be
# extensions coming with Sphinx (named 'sphinx.ext.*') or your custom
# ones.
extensions = [
    'sphinx.ext.autodoc',
    # https://recommonmark.readthedocs.io/en/latest/auto_structify.html
    'recommonmark'
]

source_suffixes = {
    '.rst': 'restructuredtext',
    '.md': 'markdown'
}

# http://www.sphinx-doc.org/en/master/usage/extensions/autodoc.html#confval-autodoc_mock_imports
autodoc_mock_imports = [
    'flask',
    'flask_cors',
    'gevent',
    'numpy',
    'PIL',
    'wget',
]

# Add any paths that contain templates here, relative to this directory.
templates_path = ['_templates']

# List of patterns, relative to source directory, that match files and
# directories to ignore when looking for source files.
# This pattern also affects html_static_path and html_extra_path.
exclude_patterns = []


# -- Options for HTML output -------------------------------------------------

# The theme to use for HTML and HTML Help pages.  See the documentation for
# a list of builtin themes.
html_theme = 'sphinx_rtd_theme'

# Add any paths that contain custom static files (such as style sheets) here,
# relative to this directory. They are copied after the builtin static files,
# so a file named "default.css" will overwrite the builtin "default.css".
html_static_path = ['_static']
html_logo = '_static/images/icon.png'

# https://sphinx-rtd-theme.readthedocs.io/en/stable/configuring.html
html_theme_options = {
    'canonical_url': 'https://sdk.runwayml.com',
    'analytics_id': 'UA-115776892-6',  #  Provided by Google in your dashboard
    'logo_only': False,
    'display_version': True,
    'prev_next_buttons_location': 'bottom',
    'style_external_links': False,
    'style_nav_header_background': '#efefef',
    # Toc options
    'collapse_navigation': True,
    'sticky_navigation': True,
    'navigation_depth': 1,
    'includehidden': True,
    'titles_only': False
}

# don't think this one is working...
github_url = 'https://github.com/runwayml/model-sdk'

# app setup hook
def setup(app):
    app.add_config_value('recommonmark_config', {
        #'url_resolver': lambda url: github_doc_root + url,
        'auto_toc_tree_section': 'Contents',
        'enable_eval_rst': True
    }, True)
    app.add_transform(AutoStructify)
    app.add_stylesheet('css/custom.css')
