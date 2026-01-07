from setuptools import setup, find_packages

setup(
    name="aicfg",
    version="0.1.1",
    packages=find_packages(),
    include_package_data=True,
    package_data={
        "aicfg": ["*.yaml"],
    },
    install_requires=[
        "click",
        "toml",
        "rich",
        "pyyaml",
        "mcp",
    ],
    extras_require={
        "dev": ["pytest"],
    },
    entry_points={
        "console_scripts": [
            "aicfg=aicfg.cli:cli",
            "aicfg-mcp=aicfg.mcp.server:run_server",
        ],
    },
)
