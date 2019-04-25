from setuptools import setup, find_packages
import sys, os

here = os.path.abspath(os.path.dirname(__file__))

version = '1.0'

install_requires = [
    'opencv-python',
    'configparser',
    'PyOpenGL',
    'PyOpenGL_accelerate',
]


setup(name='pyglview',
    version=version,
    description="Python OpenGL direct viewer instead of OpenCV imshow/waitKey.",
    long_description="See https://github.com/aieater/gpueater_pyglview",
    classifiers=(
        "License :: OSI Approved :: MIT License",
        "Operating System :: OS Independent",
        'Programming Language :: Python :: 2',
        'Programming Language :: Python :: 2.7',
        'Programming Language :: Python :: 3',
        'Programming Language :: Python :: 3.4',
        'Programming Language :: Python :: 3.5',
        'Programming Language :: Python :: 3.6',
        'Programming Language :: Python :: 3.7',
    ),
    keywords='opencv opengl python imshow waitkey viewer realtime',
    author='Pegara, Inc.',
    author_email='info@pegara.com',
    url='https://github.com/aieater/python_pyglview',
    license='MIT',
    packages=['pyglview'],
    zip_safe=False,
    install_requires=install_requires,
    entry_points={}
)