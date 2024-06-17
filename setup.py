from setuptools import setup, find_packages

setup(
    name='birdtalk-client',
    version='1.0.0',
    author='Robin Fox',
    author_email='bird2fish@qq.com',
    description='A WebSocket client for BirdTalk Server',
    long_description='A Python WebSocket client library for interacting with BirdTalk server.',
    long_description_content_type='text/markdown',
    url='https://github.com/yourusername/birdtalk-client',
    packages=find_packages(),
    install_requires=[
        'websockets>=10.0'
    ],
    classifiers=[
        'Programming Language :: Python :: 3',
        'License :: OSI Approved :: MIT License',
        'Operating System :: OS Independent',
    ],
)
