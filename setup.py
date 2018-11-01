import setuptools

with open("README.md", "r") as fh:
    long_description = fh.read()

setuptools.setup(
    name="snotra_rss",
    version="0.0.1",
    author="Samuel MEYNARD",
    author_email="samule@meyn.fr",
    description="Wagtail app - with rss aggregator feature",
    long_description=long_description,
    long_description_content_type="text/markdown",
    url="https://github.com/olopost/snotra_rss",
    packages=setuptools.find_packages(),
    classifiers=[
        "Programming Language :: Python :: 3",
        "License :: OSI Approved :: MIT License",
        "Operating System :: OS Independent",
    ],
)