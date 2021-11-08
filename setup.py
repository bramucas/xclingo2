import setuptools
from xclingo import __version__

with open("README.md", "r") as fh:
    long_description = fh.read()

setuptools.setup(
    name="xclingo",
    version=__version__,
    author="Brais Muñiz",
    author_email="mc.brais@gmail.com",
    description="Tool for explaining and debugging Answer Set Programs.",
    long_description=long_description,
    long_description_content_type="text/markdown",
    url="https://github.com/bramucas/xclingo2",
    classifiers=[
        "Programming Language :: Python :: 3",
        "License :: OSI Approved :: MIT License",
        "Operating System :: OS Independent",
    ],
    keywords=[
        'logic programming',
        'answer set programming',
    ],
    include_package_data=True,
    python_requires='>=3.6.0',
    install_requires=[
        'clingo>=5.5.0.post3',
        'argparse',
    ],
    packages=['xclingo', 'xclingo.preprocessor', 'xclingo.explanation', 'xclingo.xclingo_lp'],
    entry_points={'console_scripts': ['xclingo=xclingo.__main__:main']})
