from setuptools import setup, find_packages

setup(name='latools',
      version='0.2.3-dev',
      description='Tools for LA-ICPMS data analysis.',
      url='https://github.com/oscarbranson/latools',
      author='Oscar Branson',
      author_email='oscarbranson@gmail.com',
      license='MIT',
      packages=find_packages(),
      classifiers=['Development Status :: 3 - Alpha',
                   'Intended Audience :: Scientists',
                   'Topic :: Data Processing :: Laser Ablation Mass Spectrometry',
                   'Programming Language :: Python :: 2',
                   'Programming Language :: Python :: 3',
                   ],
      install_requires=['numpy',
                        'pandas',
                        'brewer2mpl',
                        'matplotlib',
                        'uncertainties',
                        'sklearn',
                        'scipy',
                        'mpld3',
                        'Ipython',
                        'configparser',
                        'tqdm',
                        'fuzzywuzzy',
                        ],
      package_data={
        'latools': ['latools.cfg',
                    'resources/*',
                    'resources/test_data/*',
                    'resources/data_formats/*'],
      },
      zip_safe=False)
