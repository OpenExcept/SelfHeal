from setuptools import setup, find_packages

with open("README.md", "r", encoding="utf-8") as fh:
    long_description = fh.read()

setup(
    name="selfheal",
    version="1.0.1",
    author="OpenExcept",
    author_email="ai.observability.eng@gmail.com",
    description="Make all code self-healing with automatic debug state capture and LLM analysis",
    long_description=long_description,
    long_description_content_type="text/markdown",
    url="https://github.com/openexcept/selfheal",
    packages=find_packages(),
    classifiers=[
        "Development Status :: 4 - Beta",
        "Intended Audience :: Developers",
        "License :: OSI Approved :: MIT License",
        "Operating System :: OS Independent",
        "Programming Language :: Python :: 3",
        "Programming Language :: Python :: 3.7",
        "Programming Language :: Python :: 3.8",
        "Programming Language :: Python :: 3.9",
        "Programming Language :: Python :: 3.10",
        "Topic :: Software Development :: Debuggers",
    ],
    python_requires=">=3.7",
    install_requires=[
        "boto3>=1.34.0",
        "slack-sdk>=3.33.0",
        "litellm>=1.52.0",
        "openai>=1.54.0",
        "streamlit>=1.30.0",
    ],
) 