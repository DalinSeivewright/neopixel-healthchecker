from distutils.core import setup

setup(
    name='NeoPixel-Healthchecker',
    version='1.0.1',
    scripts=['bin/neopixel-healthchecker.py'],
    license='LICENSE',
    description='Ping servers and display the result on a neopixel-like display',
    long_description=open('README.rst').read(),
    install_requires=[
        "rpi_ws281x >= 4.2.3",
        "adafruit-circuitpython-neopixel >= 6.0.0",
        "adafruit-blinka >= 4.9.0"
    ],
)
