import setuptools

with open("README.md", "r", encoding="utf-8") as fh:
    long_description = fh.read()

setuptools.setup(
    name="virtualhome",
    version="2.3.0",
    author="Xavier Puig",
    author_email="xavierpuig@csail.mit.edu",
    description="Python API to communicate with the VirtualHome environment",
    long_description=long_description,
    long_description_content_type="text/markdown",
    url="https://github.com/xavierpuigf/virtualhome",
    project_urls={
        "Documentation": "http://virtual-home.org/docs/",
        "Bug Tracker": "https://github.com/xavierpuigf/virtualhome/issues"
    },
    classifiers=[
        "Programming Language :: Python :: 3",
        "License :: OSI Approved :: MIT License",
        "Operating System :: OS Independent",
    ],
    install_requires=[
        'certifi==2022.12.7',
        'chardet==3.0.4',
        'idna==2.8',
        'matplotlib>=3.4.2',
        'networkx==2.3',
        'numpy>=1.19.3',
        'opencv-python==4.5.1.48',
        'pillow>=8.3.1',
        'plotly==3.10.0',
        'requests>=1.21.0',
        'ipdb==0.13.9',
        'termcolor==1.1.0',
        'tqdm==4.31.1',
        'urllib3>=1.24.3'
    ],
    package_dir={"": "src"},
    packages=setuptools.find_packages(where="src"),
    python_requires=">=3.10",
)

