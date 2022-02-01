#!/usr/bin/env python

"""The setup script."""

from setuptools import setup, find_packages

with open('README.rst') as readme_file:
    readme = readme_file.read()

requirements = [ ]

test_requirements = ['pytest>=3', ]

setup(
    author="Major Hayden",
    author_email='major@mhtx.net',
    python_requires='>=3.10',
    classifiers=[
        'Development Status :: 2 - Pre-Alpha',
        'Intended Audience :: Developers',
        'License :: OSI Approved :: Apache Software License',
        'Natural Language :: English',
        'Programming Language :: Python :: 3',
        'Programming Language :: Python :: 3.6',
        'Programming Language :: Python :: 3.7',
        'Programming Language :: Python :: 3.8',
    ],
    description="Notifications for the ThetaGang Discord",
    install_requires=requirements,
    license="Apache Software License 2.0",
    long_description=readme,
    include_package_data=True,
    keywords='thetagang_notifications',
    name='thetagang_notifications',
    packages=find_packages(include=['thetagang_notifications', 'thetagang_notifications.*']),
    test_suite='tests',
    tests_require=test_requirements,
    url='https://github.com/major/thetagang_notifications',
    version='0.1.0',
    zip_safe=False,
)
