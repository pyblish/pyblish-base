from setuptools import setup, find_packages
import publish


classifiers = [
    'Development Status :: 3 - Alpha',
    'Intended Audience :: Developers',
    'License :: OSI Approved :: GNU Lesser General Public License v3 (LGPLv3)',
    'Programming Language :: Python',
    'Programming Language :: Python :: 2.7',
    'Topic :: Software Development :: Libraries :: Python Modules',
    'Topic :: Utilities'
]

setup(
    name='pyPublish',
    version=publish.version,
    description='quality assurance for content',
    long_description=open('README.txt').read(),
    author='Marcus Ottosson',
    author_email='marcus@abstractfactory.com',
    url='https://github.com/abstractfactory/publish',
    license="LICENSE.txt",
    packages=find_packages(),
    include_package_data=True,
    zip_safe=False,
    classifiers=classifiers,
    package_data={
        'publish': ['*.json']
    },
)
