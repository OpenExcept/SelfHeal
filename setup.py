from setuptools import setup, find_packages

setup(
    name="selfheal",
    version="0.1.0",
    packages=find_packages(),
    install_requires=[
        "litellm>=1.52.3",
        "slack-sdk>=3.33.3",
        "openai>=1.54.3",
        "boto3>=1.34.69",
    ],
    author="Your Name",
    description="A debugging framework with Slack integration",
    python_requires=">=3.7",
) 