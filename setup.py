from setuptools import setup, find_packages

setup(
    name='kinos',
    version='0.1.0',
    packages=find_packages(),
    install_requires=[
        'flask',
        'portalocker',
        'anthropic',
        'openai',
        'argparse',
        # Add other dependencies from your requirements
    ],
    entry_points={
        'console_scripts': [
            'kin=kinos_cli:main',
        ],
    },
    python_requires='>=3.8',
    author='Your Name',
    description='KinOS CLI Tool',
    long_description=open('README.md').read(),
    long_description_content_type='text/markdown',
)
