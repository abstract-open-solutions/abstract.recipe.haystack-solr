from setuptools import setup, find_packages


version = "0.1dev"

setup(
    name = 'abstract.recipe.haystack-solr',
    version = version,
    author = "Simone Deponti",
    author_email = "simone.deponti@abstract.it",
    description = ("Buildout recipe for installing a SOLR instance "
                   "for django-haystack"),
    long_description=(open('README.rst').read() + '\n' +
                      open('CHANGES.txt').read()),
    license = "BSD",
    keywords = "solr django-haystack buildout",
    url=('http://github.com/abstract-open-solutions/'
         'abstract.recipe.haystack-solr'),
    classifiers=[
        "License :: OSI Approved :: BSD License",
        "Framework :: Buildout",
        "Framework :: Buildout :: Recipe",
    ],
    tests_require=['zope.testing'],
    packages = find_packages('src'),
    include_package_data = True,
    package_dir = { '': 'src' },
    namespace_packages = ['abstract', 'abstract.recipe'],
    install_requires = [
        'setuptools',
        'zc.buildout',
        'zc.recipe.egg',
        'Django',
        'django-haystack',
        'Tempita'
    ],
    zip_safe=False,
    entry_points = {
        'zc.buildout': ['default = abstract.recipe.haystack_solr:Recipe']
    },
)
