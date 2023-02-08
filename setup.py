import setuptools

version = {}
with open("./xclingo/_version.py") as fp:
    exec(fp.read(), version)

with open("README.md", "r") as fh:
    long_description = fh.read()

setuptools.setup(
    name="xclingo",
    version=version["__version__"],
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
        "logic programming",
        "answer set programming",
    ],
    include_package_data=True,
    python_requires=">=3.8.0",
    install_requires=[
        "clingo>=5.5.0.post3",
        "argparse",
        "importlib_resources",
        "clingraph",
    ],
    packages=[
        "xclingo",
        "xclingo.error",
        "xclingo.preprocessor",
        "xclingo.preprocessor.xclingo_ast",
        "xclingo.explanation",
        "xclingo.xclingo_lp",
        "xclingo.explainer",
        "xclingo.explainer.error",
        "xclingo.extensions",
        "xclingo.error",
    ],
    entry_points={"console_scripts": ["xclingo=xclingo.__main__:main"]},
)
