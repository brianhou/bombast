from setuptools import setup
import bombast

setup(
    name='bombast',
    version='v0.1.1',
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
