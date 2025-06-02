from setuptools import setup, find_packages

setup(
    name="ocs_shared_models",
    version="0.1.0",
    description="Shared SQLAlchemy models for OCS services",
    packages=find_packages(),
    install_requires=[
        "sqlalchemy>=2.0.0",
        "psycopg2-binary>=2.9.0",
    ],
    python_requires=">=3.10",
)
