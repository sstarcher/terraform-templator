from setuptools import setup, find_packages

setup(
    name='terraform-templator',
    version='0.0',
    description='Command line wrapper for terraform',
    author='Shane Starcher',
    author_email='shane.starcher@gmail.com',
    url='http://github.com/sstarcher/terraform-templator',
    packages=find_packages(),
    install_requires=[
        'blessings==1.6',
        'invoke==0.12.2',
        'python-consul==0.6.0'
    ],

    entry_points={
        'console_scripts': [
            'tft = tft.main:main'
        ]
    },

    classifiers=[
        'Development Status :: 1 - Alpha',
        'Environment :: Console',
        'Intended Audience :: Developers',
        'Intended Audience :: System Administrators',
        'Operating System :: OS Independent',
        'Programming Language :: Python :: 2.7',
        'Topic :: System :: Clustering',
        'Topic :: System :: Systems Administration',
        'Topic :: Utilities'
    ]
)
