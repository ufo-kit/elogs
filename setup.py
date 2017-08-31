from setuptools import setup, find_packages

setup(
    name='elogs',
    version='0.1.0',
    author='Matthias Vogelgesang',
    author_email='matthias.vogelgesang@kit.edu',
    description="Python module to query static elog data",
    url='http://github.com/ufo-kit/elogs',
    packages=find_packages(exclude=['*.tests']),
    scripts=['elogsd'],
    long_description=open('README.md').read(),
    install_requires=[
        'python-dateutil',
        'inotify',
    ],
)
