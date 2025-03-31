import setuptools

setuptools.setup(
    name="visual-scout",
    version="0.1.0",
    packages=setuptools.find_packages(),
    entry_points={
        "console_scripts": [
            "visual-scout=visual_scout.cli:main",
        ],
    },
)
