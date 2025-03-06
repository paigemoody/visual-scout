from setuptools import setup, find_packages

# Read dependencies from requirements.txt
## TODO break out dev and package requirements
def read_requirements():
    with open("requirements.txt", encoding="utf-8") as f:
        return [line.strip() for line in f if line.strip() and not line.startswith("#")]

setup(
    name="visual-scout",
    version="0.1.0",
    packages=find_packages(),
    install_requires=read_requirements(),  # Load requirements from file
    entry_points={
        "console_scripts": [
            "visual-scout=visual_scout.cli:main",
        ],
    },
)
