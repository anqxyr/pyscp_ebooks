import setuptools
import subprocess

with open('README.md') as f:
    readme = f.read()

major_version = '2.0'
commits = subprocess.check_output(
    ['/usr/bin/git', 'rev-list', 'HEAD', '--count']).decode('utf8').strip()

setuptools.setup(
    name='pyscp',
    version='{}.{}'.format(major_version, commits),
    description='Create ebook versions of wikidot sites.',
    long_description=readme,
    url='https://github.com/anqxyr/pyscp_ebooks/',
    author='anqxyr',
    author_email='anqxyr@gmail.com',
    license='MIT',
    classifiers=[
        'Development Status :: 4 - Beta',
        'Intended Audience :: Other Audience',
        'License :: OSI Approved :: MIT License',
        'Operating System :: OS Independent',
        'Programming Language :: Python :: 3.4'],
    packages=['pyscp'],
    install_requires=[
        'pyscp',
        'sh'],
)
