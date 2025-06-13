from setuptools import setup, find_packages

setup(
    name="ocs_shared_models",
    version="0.1.0",
    description="Shared SQLAlchemy models for OCS services",
    packages=find_packages(),
    install_requires=[
        "sqlalchemy>=2.0.0",
        "psycopg2-binary>=2.9.0",
        "pyjwt>=2.8.0",
        "cryptography>=41.0.3",  # Required by PyJWT for certain algorithms
        "fastapi>=0.103.1",  # For auth middleware
        "python-dotenv>=1.0.0",
        "pytz>=2023.3",  # For timezone utilities
    ],
    python_requires=">=3.10",
)
