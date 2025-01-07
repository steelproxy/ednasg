from setuptools import setup, find_packages

setup(
    name="ednasg",
    version="0.3",
    author="Collin Rodes",
    author_email="steelproxy@protonmail.com",
    description="A Python program to generate news scripts from RSS feeds using OpenAI.",
    packages=find_packages(),
    install_requires=[
        "feedparser",
        "openai",
        "keyring",
        "jsonschema",
        "windows-curses",
        "pygooglenews",
    ],
    entry_points={
        'console_scripts': [
            'ednasg=ednasg:main',
        ],
    },
    classifiers=[
        "Programming Language :: Python :: 3",
        "Operating System :: OS Independent",
    ],
    python_requires='>=3.6',
)
