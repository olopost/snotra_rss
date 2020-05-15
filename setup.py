import setuptools

with open("README.md", "r") as fh:
    long_description = fh.read()
with open("requirements.txt", "r") as rp:
    req = rp.read()

setuptools.setup(
    name="snotra_rss",
    version="0.2.5.2",
    author="Samuel MEYNARD",
    author_email="samuel@meyn.fr",
    description="Wagtail app - with rss aggregator and tweeter aggregator feature",
    long_description=long_description,
    long_description_content_type="text/markdown",
    url="https://github.com/olopost/snotra_rss",
    install_requires=req,
    packages=setuptools.find_packages(),
    package_data={
        'examples': ['templates/*.html']
    },
    include_package_data=True,
    package_dir={'snotra_rss': 'snotra_rss'},
    classifiers=[
        "Programming Language :: Python :: 3",
        "License :: OSI Approved :: MIT License",
        "Operating System :: OS Independent",
    ],
)