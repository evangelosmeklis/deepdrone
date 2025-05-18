from setuptools import setup, find_packages

setup(
    name="deepdrone",
    version="0.1.0",
    description="DeepDrone - AI-powered drone control and mission planning",
    author="DeepDrone Team",
    packages=find_packages(),
    install_requires=[
        "dronekit",
        "smolagents",
        "streamlit",
        "huggingface_hub",
        "python-dotenv",
    ],
) 