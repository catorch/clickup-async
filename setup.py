import setuptools

with open("README.md", "r", encoding="utf-8") as fh:
    long_description = fh.read()

setuptools.setup(
    name="clickup-async",
    version="0.1.0",
    author="catorch",
    author_email="catorch@example.com",
    description="Modern async Python client for ClickUp API with type hints, rate limiting and fluent interface",
    long_description=long_description,
    long_description_content_type="text/markdown",
    url="https://github.com/catorch/clickup-async",
    packages=setuptools.find_packages(where="src"),
    package_dir={"": "src"},
    classifiers=[
        "Development Status :: 4 - Beta",
        "Intended Audience :: Developers",
        "License :: OSI Approved :: MIT License",
        "Programming Language :: Python :: 3",
        "Programming Language :: Python :: 3.9",
        "Programming Language :: Python :: 3.10",
        "Programming Language :: Python :: 3.11",
        "Programming Language :: Python :: 3.12",
        "Topic :: Software Development :: Libraries :: Python Modules",
        "Framework :: AsyncIO",
        "Typing :: Typed",
    ],
    python_requires=">=3.9",
    install_requires=[
        "httpx>=0.23.0",
        "pydantic>=2.0.0",
        "python-dotenv",
    ],
    extras_require={
        "test": [
            "pytest",
            "pytest-asyncio",
            "pytest-cov",
        ],
        "dev": [
            "black",
            "isort",
            "mypy",
            "pre-commit",
        ],
    },
)
