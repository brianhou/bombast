from setuptools import setup

setup(
    name='bombast',
    version='v0.2.0',
    description='An obfuscator for Python source code that manipulates the AST.',
    url='https://github.com/brianhou/bombast',
    author='Brian Hou',
    packages=['bombast'],
    install_requires=['astunparse'],
    entry_points={
        'console_scripts': [
            'bombast=bombast.__init__:main',
        ],
    }
)
