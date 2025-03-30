from setuptools import find_packages, setup

setup(
    name="clickup_python_async",
    version="0.1.0",
    packages=find_packages(where="src"),
    package_dir={"": "src"},
    install_requires=[
        "httpx",
        "pydantic>=2.0.0",
        "python-dotenv",
    ],
    extras_require={
        "test": [
            "pytest",
            "pytest-asyncio",
        ],
    },
    python_requires=">=3.9",
    author="Your Name",
    author_email="your.email@example.com",
    description="A modern, elegant Python interface for the ClickUp API",
    long_description=open("README.md").read(),
    long_description_content_type="text/markdown",
    url="https://github.com/yourusername/clickup_python_async",
    classifiers=[
        "Development Status :: 3 - Alpha",
        "Intended Audience :: Developers",
        "License :: OSI Approved :: MIT License",
        "Programming Language :: Python :: 3",
        "Programming Language :: Python :: 3.9",
        "Programming Language :: Python :: 3.10",
        "Programming Language :: Python :: 3.11",
    ],
)
