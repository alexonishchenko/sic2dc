from pathlib import Path

from setuptools import find_packages, setup


def requirements(filename: str) -> str:
    file_reqs = Path(__file__).parent / filename
    with open(str(file_reqs.absolute())) as file:
        return "".join(line for line in file.readlines() if not line.startswith("-"))


setup(
    name='sic2dc',
    version='0.0.1',
    description="Simple indented config to dict compare.",
    package_dir={"": "app"},
    packages=find_packages(include="sic2dc.src"),
    author="Alexander Onishchenko",
    license="MIT",
    install_requires=requirements("requirements.txt"),
    extras_require={"dev": requirements("requirements_tests.txt")},
    entry_points={
        'console_scripts': ['sic2dc = sic2dc.cli:main'],
    },
    python_requires=">=3.11",
)
