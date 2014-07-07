#!/usr/bin/env python

import os
from shutil import copyfile
from distutils.core import setup
from distutils.command.install_data import install_data
from glob import glob
from DistUtilsExtra.command import build_help, build_extra, build_icons
from DistUtilsExtra.command import build_i18n, clean_i18n
import os.path
from src.version import __version__


class InstallData(install_data):
    def run(self):
        self.data_files.extend(self._nautilus_plugin())
        install_data.run(self)

    def _nautilus_plugin(self):
        files = []
        cmd = os.popen('pkg-config --variable=pythondir nautilus-python', 'r')
        res = cmd.readline().strip()
        ret = cmd.close()

        if ret is None:
            dest = res[5:]
            files.append((dest, ['nautilus/postrExtension.py']))

        return files


class BuildHelp(build_help.build_help):
    '''Override DistUtilsExtra "build_help" command to add Mallard support
       with translations.'''
    def translate_help(self, help_files, target, lang):
        po_dir = os.path.join(self.help_dir, lang)
        po_file = os.path.join(po_dir, '%s.po' % lang)
        build_target = os.path.join('build', target, lang)
        translated_files = []

        if not os.path.exists(build_target):
            os.makedirs(build_target)

        if os.path.isfile(po_file):
            for f in help_files:
                file_merged = os.path.join(build_target, os.path.basename(f))
                cmd = ['xml2po', '-p', po_file, '-o', file_merged, f]
                self.spawn(cmd)

                translated_files.append(file_merged)

        return translated_files

    def translate_omf(self, omf_file, target, lang):
        po_dir = os.path.join(self.help_dir, lang)
        po_file = os.path.join(po_dir, '%s.po' % lang)
        build_target = os.path.join('build', target)
        translated_files = []
        name = self.distribution.metadata.name
        dest = os.path.join(build_target, '%s-%s.omf')

        if not os.path.exists(build_target):
            os.makedirs(build_target)

        if os.path.isfile(po_file):
            file_merged = dest % (name, lang)
            cmd = ['xml2po', '-p', po_file, '-o', file_merged, omf_file]
            self.spawn(cmd)
            translated_files.append(file_merged)
        elif lang is 'C':
            file_merged = dest % (name, lang)
            copyfile(omf_file, file_merged)
            translated_files.append(file_merged)

        return translated_files

    def get_data_files(self):
        data_files = []
        name = self.distribution.metadata.name
        target = os.path.join('share', 'gnome', 'help', name)
        target_omf = os.path.join('share', 'omf', name)
        omf_file = os.path.join(self.help_dir, '%s.omf.in' % name)

        help_files = (glob(os.path.join(self.help_dir, 'C', '*.page')))
        data_files.append((os.path.join(target, name, 'C'), help_files))

        langs = [d for d in os.listdir(self.help_dir) 
                   if os.path.isdir(os.path.join(self.help_dir, d))]

        for lang in langs:
            path = os.path.join(self.help_dir, lang)
            path_xml = os.path.join(target, lang)
            path_figures = os.path.join(target, lang, 'figures')

            translated_files = self.translate_help(help_files, target, lang)

            data_files.append((path_xml, translated_files))

            figures = glob(os.path.join(path, 'figures', '*.png'))
            if not figures:
                figures = glob(os.path.join(self.help_dir, 'C', 'figures', '*.png'))
            data_files.append((path_figures, figures))

            translated_files = self.translate_omf(omf_file, target_omf, lang)
            if translated_files:
                data_files.append((target_omf, translated_files))

        return data_files


setup(name='postr',
      version=__version__,
      description='Flickr Uploader',
      author='Ross Burton',
      author_email='ross@burtonini.com',
      url='https://wiki.gnome.org/Apps/Postr',

      scripts=['postr'],
      package_dir={'postr': 'src'},
      packages=['postr'],
      package_data={'postr': ['postr.glade']},
      data_files=[
                  ('share/icons/hicolor/16x16/apps', glob('data/16x16/*.png')),
                  ('share/icons/hicolor/22x22/apps', glob('data/22x22/*.png')),
                  ('share/icons/hicolor/24x24/apps', glob('data/24x24/*.png')),
                  ('share/icons/hicolor/32x32/apps', glob('data/32x32/*.png')),
                  ('share/icons/hicolor/scalable/apps', glob('data/scalable/*.svg')),
                  ],
      cmdclass={'install_data': InstallData,
                'build' : build_extra.build_extra,
                'build_i18n' :  build_i18n.build_i18n,
                'build_help' :  BuildHelp,
                'build_icons' : build_icons.build_icons,
                'clean_i18n' :  clean_i18n.clean_i18n
                }
      )

# TODO: update icon cache
# TODO: rewrite in autotools because this is getting silly
