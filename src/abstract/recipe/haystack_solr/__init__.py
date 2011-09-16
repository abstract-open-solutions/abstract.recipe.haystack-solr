# -*- coding: utf-8 -*-
import os, shutil
from tempita import Template
from zc.buildout import UserError
from zc.recipe.egg import Egg


TEMPLATE_DIR = os.path.join(os.path.dirname(__file__), 'templates')


class Recipe(object):
    """This recipe is used by zc.buildout"""

    def __init__(self, buildout, name, options):
        self.name, self.options, self.buildout = name, options, buildout
        self.part_dir = os.path.join(
            buildout['buildout']['parts-directory'],
            name
        )
        self.var_dir = os.path.join(
            self.buildout['buildout']['directory'],
            'var',
            self.name
        )
        self.data_dir = os.path.join(self.var_dir, 'data')

        options['eggs'] = options.get(
            'eggs',
            self.buildout['buildout'].get('eggs', '')
        ).strip().split()

        options['host'] = options.get('host', '127.0.0.1').strip()
        options['port'] = options.get('port', '8070').strip()

        options['django-settings'] = options.get('django-settings', '').strip()
        options['django-settings-file'] = options.get(
            'django-settings-file', '').strip()
        if (not options['django-settings']) and \
                (not options['django-settings-file']):
            raise UserError("One between 'django-settings' and "
                            "'django-settings-file' must be specified")
        options['solr-location'] = options['solr-location'].strip()
        options['solr-config'] = options.get('solr-config', '')

        # Java startup commands
        options['java-opts'] = options.get('java-opts', '')
        options['java-args'] = options.get('java-args', '')

    def parse_java_opts(self):
        """Parsed the java opts and arguments from `options`. """
        cmd = [
            'java',
            '-Dsolr.solr.home=%s' % self.part_dir,
            '-Dsolr.solr.dataDir=%s' % self.data_dir
        ]
        if self.options['java-opts']:
            cmd.extend(self.options['java-opts'].strip().splitlines())
        cmd.extend([
            '-jar',
            os.path.join(self.part_dir, 'start.jar')
        ])
        if self.options['java-args']:
            cmd.extend(self.options['java-args'].strip().splitlines())
        return cmd

    def get_namespace(self):
        return {
            'options': self.options,
            'buildout': self.buildout
        }

    def generate(self, src, dst, **kwargs):
        namespace = self.get_namespace()
        namespace.update(kwargs)
        # pylint: disable-msg=C0321
        with open(src, 'rb') as src_stream, open(dst, 'rb') as dst_stream:
            template = Template(src_stream.read())
            dst_stream.write(template.substitute(**namespace))

    def install(self, update=False):
        """installer
        """

        parts = [self.part_dir, self.var_dir]

        if not update:
            for path in parts:
                if not os.path.exists(path):
                    shutil.rmtree(path)

            # Copy the solr files
            shutil.copytree(
                os.path.join(
                    self.options['solr-location'],
                    'example'
                ),
                self.part_dir
            )

        dirs = [
            self.data_dir,
            os.path.join(self.var_dir, 'logs')
        ]

        logdir = dirs[1]

        for path in dirs:
            if not os.path.exists(path):
                os.makedirs(path)

        solrconfig_path = os.path.join(
            self.part_dir, 'solr', 'conf', 'solrconfig.xml'
        )
        if not self.options['solr-config']:
            with open(solrconfig_path, 'rb') as src:
                solrconfig = src.read().replace(
                    'dir="../..',
                    'dir="%s' % self.options['solr-location']
                )
            with open(solrconfig_path, 'rb') as dst:
                dst.write(solrconfig)
        else:
            shutil.copy(self.options['solr-config'], solrconfig_path)

        eggs = Egg(self.buildout, self.options['recipe'], self.options)
        requisites = [ 'django-haystack', 'Django' ]
        __, working_set = eggs.working_set(
            requisites.extend(self.options['eggs'])
        )

        self.generate(
            src=os.path.join(TEMPLATE_DIR, 'templates', 'solr.tmpl'),
            dst=os.path.join(self.buildout['buildout']['bin-directory'],
                             self.name),
            schema_file=os.path.join(
                self.part_dir,
                'solr',
                'conf',
                'schema.xml'
            ),
            extrapaths=[dist.location for dist in working_set],
            pidfile=os.path.join(self.var_dir, 'solr.pid'),
            logfile=os.path.join(logdir, 'solr.log'),
            buildoutdir=self.buildout['buildout']['directory'],
            basedir=self.part_dir,
            djangosettings=self.options['django-settings'],
            djangosettings_file=self.options['django-settings-file'],
            startcmd=self.parse_java_opts()
        )

        # returns installed files
        return parts

    def update(self):
        """updater"""
        self.install(update=True)
