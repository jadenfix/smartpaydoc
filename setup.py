from setuptools import setup, find_packages

with open("README.md", "r", encoding="utf-8") as fh:
    long_description = fh.read()

with open("requirements.txt", "r", encoding="utf-8") as fh:
    requirements = [line.split("#", 1)[0].strip() for line in fh if line.split("#", 1)[0].strip()]

setup(
    name="smartpaydoc",
    version="0.1.0",
    author="Jaden Fix",
        description="LLM-Powered Developer Assistant for Stripe Integrations",
    long_description=long_description,
    long_description_content_type="text/markdown",
    url="https://github.com/jadenfix/smartpaydoc",
    packages=find_packages(include=["web", "smartpaydoc"]),
    py_modules=["main", "rag_engine", "codegen", "error_helper", "llm", "web_app"],
    classifiers=[
        "Development Status :: 3 - Alpha",
        "Intended Audience :: Developers",
        "License :: OSI Approved :: MIT License",
        "Operating System :: OS Independent",
        "Programming Language :: Python :: 3",
        "Programming Language :: Python :: 3.8",
        "Programming Language :: Python :: 3.9",
        "Programming Language :: Python :: 3.10",
        "Programming Language :: Python :: 3.11",
    ],
    python_requires=">=3.9",
    install_requires=requirements,
    entry_points={
        "console_scripts": [
            "smartpaydoc=main:app",
        ],
    },
    include_package_data=False,
    package_data={
        "web": ["templates/*.html", "static/*.css", "static/*.js"],
    },
)