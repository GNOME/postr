#!/usr/bin/env python

from distutils.core import setup
from glob import glob
from src.version import __version__

setup(name='Postr',
      version=__version__,
      description='Flickr Uploader',
      author='Ross Burton',
      author_email='ross@burtonini.com',
      url='http://www.burtonini.com/',

      scripts=['postr'],
      package_dir={'postr': 'src'},
      packages=['postr'],
      package_data={'postr': ['postr.glade']},
      data_files=[('share/applications', ['data/postr.desktop']),
                  ('lib/nautilus/extensions-1.0/python', ['nautilus/postrExtension.py']),
                  ('share/icons/hicolor/16x16/apps', glob('data/16x16/*.png')),
                  ('share/icons/hicolor/22x22/apps', glob('data/22x22/*.png')),
                  ('share/icons/hicolor/24x24/apps', glob('data/24x24/*.png')),
                  ('share/icons/hicolor/32x32/apps', glob('data/32x32/*.png')),
                  ('share/icons/hicolor/scalable/apps', glob('data/scalable/*.svg')),
                  ],
      
      )

# TODO: install translations
# TODO: update icon cache
