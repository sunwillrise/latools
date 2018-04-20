from setuptools import setup, find_packages

setup(name='latools',
      version='0.3.4',
      description='Tools for LA-ICPMS data analysis.',
      url='https://github.com/oscarbranson/latools',
      author='Oscar Branson',
      author_email='oscarbranson@gmail.com',
      license='MIT',
      packages=find_packages(),
      classifiers=['Development Status :: 4 - Beta',
                   'Intended Audience :: Science/Research',
                   'Topic :: Scientific/Engineering',
                   'Programming Language :: Python :: 2',
                   'Programming Language :: Python :: 3',
                   ],
      python_requires='>3.6',
      install_requires=['numpy',
                        'pandas',
                        'matplotlib',
                        'uncertainties',
                        'sklearn',
                        'scipy',
                        'Ipython',
                        'configparser',
                        'tqdm'
                        ],
      package_data={
        'latools': ['latools.cfg',
                    'resources/*',
                    'resources/data_formats/*',
                    'resources/test_data/*'],
      },
      zip_safe=False)
