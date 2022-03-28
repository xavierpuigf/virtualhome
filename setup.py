from setuptools import setup

setup(
      name = 'VirtualHome',
      packages = find_packages(),
      include_package_data = True,
      version = '2.3',
      license='Creative Commons',
      description = 'VirtualHome',
      author = 'Xavier Puig',
      author_email = 'xavierpuig@csail.mit.edu',
      url = 'https://github.com/xavierpuigf/virtualhome',
      keywords = [
      'artificial intelligence',
      'reinforcement learning',
      'computer vision',
      'simulator',
      'language-control'
      ],
      install_requires=[
            'certifi',
            'chardet',
            'idna',
            'matplotlib',
            'networkx',
            'numpy',
            'opencv-python',
            'pillow',
            'plotly',
            'requests',
            'termcolor',
            'tqdm',
            'urllib3'
      ],
      classifiers=[
            'Development Status :: 2.3 - Release',
            'Intended Audience :: Researchers',
            'Topic :: Scientific/Engineering :: Artificial Intelligence', 'Machine Learning', 'Computer Vision', 'Reinforcement Learning',
            'License :: OSI Approved :: Creative Commons License',
            'Programming Language :: Python :: 3.8',
      ],
)

