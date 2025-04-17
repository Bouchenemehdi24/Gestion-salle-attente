from setuptools import setup, find_packages

setup(
    name="my_medical_app",
    version="0.1",
    description="A medical practice management application",
    long_description=open("README.md").read(),
    author="Your Name",
    author_email="your.email@example.com",
    url="https://github.com/yourusername/my-medical-app",
    packages=find_packages(),
    scripts=[
        "app.py"
    ],
    install_requires=[
        "numpy",
        "pandas",
        "matplotlib",
        "SQLAlchemy",
        "bcrypt",
        "python-dotenv",
        "pyjwt",
        "python-multipart",
        "Pillow",
        "opencv-python",
        "pywin32"
    ],
    classifiers=[
        "Programming Language :: Python :: 3",
        "License :: OSI Approved :: MIT License",
        "Operating System :: Windows",
    ],
    python_requires=">=3.6",
)
