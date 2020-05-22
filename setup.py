from setuptools import setup, find_packages
import os

def get_description():
    """Get long description."""

    with open("README.md", 'r') as f:
        desc = f.read()
    return desc


def get_requirements(req):
    """Load list of dependencies."""

    install_requires = []
    with open(req) as f:
        for line in f:
            if not line.startswith("#"):
                install_requires.append(line.strip())
    return install_requires


setup(
    name="pymd-extensions-lz",
    version="0.0.1",
    author="lzimd",
    author_email="29934671+lzimd@users.noreply.github.com",
    description="Python Markdown Extensions",
    long_description=get_description(),
    long_description_content_type='text/markdown',
    url="https://github.com/lzimd/py-markdown-extensions-lz",
    packages=find_packages(exclude=['test*']),
    install_requires=get_requirements("requirements.txt"),
    license='MIT License',
    classifiers=(
        'Programming Language :: Python :: 3',
        'Programming Language :: Python :: 3.5',
        'Programming Language :: Python :: 3.6',
        'Programming Language :: Python :: 3.7',
        'Programming Language :: Python :: 3.8',
    ),
    zip_safe=False
)