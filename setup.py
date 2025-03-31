from setuptools import setup, find_packages

setup(
    name="visual-scout",
    version="0.1.0",
    packages=find_packages(),
    entry_points={
        "console_scripts": [
            "visual-scout=visual_scout.cli:main",
        ],
    },
)
