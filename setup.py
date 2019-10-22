import setuptools

with open("README.md", "r") as fh:
    long_description = fh.read()

setuptools.setup(
    name="sav.channels",
    version="0.5",
    author="Sander Voerman",
    author_email="sander@savoerman.nl",
    description="Iterable streams between coroutines",
    long_description=long_description,
    long_description_content_type="text/markdown",
    url="https://github.com/sandervoerman/channels",
    packages=['sav.channels'],
    package_data={
        'sav.channels': ['py.typed'],
    },
    python_requires='>=3.8',
    classifiers=[
        "Development Status :: 3 - Alpha",
        "Programming Language :: Python :: 3.7",
        "License :: OSI Approved :: MIT License",
        "Operating System :: OS Independent",
    ],
)
