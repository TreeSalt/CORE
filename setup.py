from setuptools import find_packages, setup

setup(
    name="antigravity_harness",
    version="4.7.14",
    packages=find_packages(),
    install_requires=[
        "numpy",
        "pandas",
        "pydantic",
        "pyyaml",
        "joblib",
        "scipy",
        "rich",
        # Add other dependencies from requirements.in if needed, 
        # but for -e . --no-deps it doesn't matter much as long as environment is set up.
    ],
    python_requires=">=3.10",
)
