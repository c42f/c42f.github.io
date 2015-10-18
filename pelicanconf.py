#!/usr/bin/env python
# -*- coding: utf-8 -*- #
from __future__ import unicode_literals

AUTHOR = u'Chris Foster'
SITENAME = u'Chris Foster'
SITEURL = 'https://c42f.github.io'

SITESUBTITLE = u"Yup, that's a blog alright"
MENUITEMS = [('blog','/')]

PROFILE_IMAGE_URL = "/images/chris.jpg"

# Mathjax plugin from
# https://github.com/amic-github/python-markdown-mathjax
MD_EXTENSIONS = ['codehilite(css_class=highlight)','extra','mathjax']

PATH = 'content'
STATIC_PATHS = ['images', 'blog']
ARTICLE_PATHS = ['blog']

ARTICLE_URL = '{date:%Y}/{date:%m}/{date:%d}/{slug}.html'
ARTICLE_SAVE_AS = '{date:%Y}/{date:%m}/{date:%d}/{slug}.html'

THEME = './theme_crowsfoot'

TIMEZONE = 'Australia/Brisbane'

DEFAULT_LANG = u'en'

# Feed generation is usually not desired when developing
FEED_ALL_ATOM = None
CATEGORY_FEED_ATOM = None
TRANSLATION_FEED_ATOM = None
AUTHOR_FEED_ATOM = None
AUTHOR_FEED_RSS = None

EMAIL_ADDRESS = 'chris42f@gmail.com'
GITHUB_ADDRESS = 'http://github.com/c42f'

DEFAULT_PAGINATION = False

SHOW_ARTICLE_AUTHOR = False

LICENSE_NAME = "CC BY-SA"
LICENSE_URL = "https://creativecommons.org/licenses/by-sa/4.0/"

