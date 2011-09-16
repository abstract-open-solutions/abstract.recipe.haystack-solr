Overview
========

This is a recipe to set up and configure SOLR_ in a django-haystack_
environment.


Basic setup
-----------

A basic buildout configuration using this recipe looks like this (using
`djc.recipe`_)::

    [buildout]
    eggs = django-haystack
    parts =
        solr-download
        solr
        django

    [django]
    recipe = djc.recipe
    project = dummydjangoprj

    [solr-download]
    recipe = gocept.download
    url = http://mirror.nohup.it/apache/lucene/solr/3.4.0/apache-solr-3.4.0.tgz
    strip-top-level-dir = true

    [solr]
    recipe = abstract.recipe.haystack-solr
    solr-location = ${solr-download:location}
    django-settings-file = ${django:location}/settings.py
    eggs =
        ${buildout:eggs}
        ${django:project}


This will download SOLR and create an executable at ``bin/solr``. The name of
the script is the name of the section.

To test the setup run ``bin/solr fg`` and check the console output. By default
this will run a Jetty server on port 8080. The SOLR instance is accessible in a
browser at ``http://127.0.0.1:8080/solr/``.

When SOLR is started the first time, django-haystack_ is invoked to create the
SOLR schema: the same will happen (overwriting any existing schema) if you run
``bin/solr reset``.

SOLR will write all its log files into ``var/solr/log``. All its configuration
including jobs and past runs will go into ``var/solr/data``.  The directory
name in ``var`` will have the name of the recipe section.


Options
-------

The recipe supports the following options:

eggs
    Optional. The eggs the solr script should load. Since django-haystack_ is
    invoked, it must be atleast all the eggs that are necessary to run Django
    management commands.

django-settings
    If your Django settings are in a module in ``sys.path``, put here the
    module name. Either this or ``django-settings-file`` should be specified.

django-settings-file
    If your Django settings are in a file not in ``sys.path``, put here the
    file name. Either this or ``django-settings`` should be specified.

solr-location
    The location of the part where the SOLR_ distribution has been downloaded.

solr-config
    Optional. The file name containing the SOLR_ config (``solrconfig.xml``).

java-opts
    Optional. Parameters to pass to the Java Virtual Machine (JVM) used to
    run Jetty. Each option is specified on a separated line.
    If you run into memory problems it's typical to pass::

        [solr]
        ...
        java-opts =
          -Xms512M
          -Xmx1024M
        ...

java-args
    Optional. Extra arguments to pass to the Java Virtual Machine (JVM): this
    are typically all the parameters you'd pass after the jar file.


Development
-----------

The code and issue tracker can be found at:
https://github.com/abstract-open-solutions/abstract.recipe.haystack-solr


.. _SOLR : http://lucene.apache.org/solr/
.. _django-haystack : http://haystacksearch.org/
.. _`djc.recipe`: http://pypi.python.org/pypi/djc.recipe
