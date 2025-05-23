from setuptools import setup, find_packages

setup(
    name="prompt_manager",
    version="0.1.0",
    packages=find_packages(where="src"),
    package_dir={"": "src"},
    install_requires=[
        "fastapi>=0.110.0",
        "uvicorn>=0.29.0",
        "pydantic>=2.6.0",
        "jinja2>=3.1.3",
        "python-multipart>=0.0.7",
        "websockets>=12.0",
        "loguru>=0.7.2",
        "aiofiles>=23.2.1",
        "pyyaml>=6.0",
        "httpx>=0.27.0",
    ],
    python_requires=">=3.9",
    entry_points={
        "console_scripts": [
            "prompt-manager=prompt_manager.server:main",
        ],
    },
)
