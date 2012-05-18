# -*- coding: utf-8 -*-
import os, stat, re, shutil
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
        )
        self.eggs = options['eggs'].strip().split()

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

    @staticmethod
    def listify(data):
        lines = []
        for raw_line in data.splitlines():
            line = raw_line.strip()
            if line != '':
                lines.append(line)
        return lines

    def parse_java_opts(self):
        """Parsed the java opts and arguments from `options`. """
        cmd = [
            'java',
            '-Dsolr.solr.home=%s' % os.path.join(self.part_dir, 'solr'),
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
        with open(src, 'rb') as src_stream, open(dst, 'wb') as dst_stream:
            template = Template(src_stream.read())
            dst_stream.write(template.substitute(**namespace))

    # pylint: disable-msg=R0912,R0914
    def install(self, update=False):
        """installer
        """

        parts = [self.part_dir, self.var_dir]

        if not update:
            for path in parts:
                if os.path.exists(path):
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

        for path in parts + dirs:
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
            with open(solrconfig_path, 'wb') as dst:
                dst.write(solrconfig)
        else:
            shutil.copy(self.options['solr-config'], solrconfig_path)

        eggs = Egg(self.buildout, self.options['recipe'], self.options)
        __, working_set = eggs.working_set(
            self.eggs
        )

        # The initialization code is expressed as a list of lines
        initialization = []

        # Gets the initialization code: the tricky part here is to preserve
        # indentation. This is obtained by getting all the lines and then
        # finding the initial whitespace common to all lines, excluding blank
        # lines: the obtained whitespace is then subtracted from all lines.
        raw_code = []
        residual_whitespace = None
        whitespace_regex = re.compile(r'^([ ]+)')
        for line in self.options.get("initialization", "").splitlines():
            if line != "":
                m = whitespace_regex.search(line)
                if m is None:
                    initial_whitespace = 0
                else:
                    initial_whitespace = len(m.group(1))
                if residual_whitespace is None or \
                        initial_whitespace < residual_whitespace:
                    residual_whitespace = initial_whitespace
                raw_code.append(line)
        for line in raw_code:
            initialization.append(line[residual_whitespace:])

        # Gets the environment-vars option and generates code to set the
        # enviroment variables via os.environ
        environment_vars = []
        for line in self.listify(self.options.get("environment-vars", "")):
            try:
                var_name, raw_value = line.split(" ", 1)
            except ValueError:
                raise RuntimeError(
                    "Bad environment-vars contents: %s" % line
                )
            environment_vars.append(
                'os.environ["%s"] = r"%s"' % (
                    var_name,
                    raw_value.strip()
                )
            )
        if len(environment_vars) > 0:
            initialization.append("import os")
            initialization.extend(environment_vars)

        script_file = os.path.join(self.buildout['buildout']['bin-directory'],
                                   self.name)
        schema_file = os.path.join(
                self.part_dir,
                'solr',
                'conf',
                'schema.xml'
            )
        if os.path.exists(schema_file):
            os.remove(schema_file)
        self.generate(
            src=os.path.join(TEMPLATE_DIR, 'solr.tmpl'),
            dst=script_file,
            schema_file=schema_file,
            executable=self.buildout['buildout']['executable'],
            extrapaths=[dist.location for dist in working_set],
            otherpaths=self.options.get('extra-paths', '').split(),
            pidfile=os.path.join(self.var_dir, 'solr.pid'),
            logfile=os.path.join(logdir, 'solr.log'),
            buildoutdir=self.buildout['buildout']['directory'],
            basedir=self.part_dir,
            djangosettings=self.options['django-settings'],
            djangosettings_file=self.options['django-settings-file'],
            startcmd=self.parse_java_opts(),
            initialization=initialization
        )

        os.chmod(
            script_file,
            stat.S_IRWXU | stat.S_IRWXG | stat.S_IROTH | stat.S_IXOTH
        )

        # returns installed files
        return parts

    def update(self):
        """updater"""
        self.install(update=True)
