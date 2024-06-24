from setuptools import setup, find_packages

setup(
    name="sqlite-worker",
    version="0.0.4",
    packages=find_packages(),
    description="Thread-safe SQLite3 worker for Python",
    long_description=open('ReadMe.md').read(),
    long_description_content_type='text/markdown',
    author="Roshan Lamichhane",
    author_email="roshanlamichhanenepali@gmail.com",
    url="https://github.com/roshanlam/sqlite-worker",
    license="MIT",
    install_requires=[],
    classifiers=[
        "Programming Language :: Python :: 3",
        "License :: OSI Approved :: MIT License",
        "Operating System :: OS Independent",
    ],
    python_requires='>=3.6',
)
