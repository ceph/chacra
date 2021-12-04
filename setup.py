# -*- coding: utf-8 -*-
try:
    from setuptools import setup, find_packages
except ImportError:
    from ez_setup import use_setuptools
    use_setuptools()
    from setuptools import setup, find_packages


setup(
    name='chacra',
    version='0.1',
    description='',
    author='Alfredo Deza',
    author_email='adeza@redhat.com',
    license = "MIT",
    install_requires=[
        "pecan",
        "sqlalchemy==1.3.0",
        "psycopg2==2.8.2",
        "pecan-notario",
        "python-statsd",
        "requests",
        "celery<=6.2.5",
        # celery imports kombu, which imports importlib_metadata
        # for py earlier than 3.8 (in 3.8 importlib.metadata is supplied
        # in py's stdlib).  But there's a deprecated interface that
        # kombu uses (see https://github.com/celery/kombu/issues/1339).
        # Constrain the version of the external importlib_metadata
        # to avoid the compatibility problem.  (kombu will eventually
        # have to change, as the stdlib version is also removing the
        # SelectableGroups dict interface.
        "importlib_metadata<=3.6; python_version<'3.8'",
    ],
    test_suite='chacra',
    zip_safe=False,
    include_package_data=True,
    packages=find_packages(exclude=['ez_setup']),
    classifiers = [
        'Development Status :: 4 - Beta',
        'Intended Audience :: Developers',
        'License :: OSI Approved :: MIT License',
        'Topic :: Utilities',
        'Operating System :: MacOS :: MacOS X',
        'Operating System :: POSIX',
        'Programming Language :: Python :: 2.6',
        'Programming Language :: Python :: 2.7',
        'Programming Language :: Python :: 3.3',
    ],
    entry_points="""
        [pecan.command]
        populate=chacra.commands.populate:PopulateCommand
        """
)
