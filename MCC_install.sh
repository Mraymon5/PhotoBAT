#!/bin/bash

sudo apt-get update
sudo apt-get upgrade
sudo pip3 install --upgrade setuptools

# Detect operating system
if [[ "$OSTYPE" == "msys"* || "$OSTYPE" == "win32"* ]]; then
    # Code that may need to be run ahead of time?
    #chmod +x setup_script.sh
    #./setup_script.sh

    echo "Detected Windows environment."
    echo "Please install InstaCal from the following link:"
    echo "https://digilent.com/reference/software/instacal/start"
    echo ""
    echo "After installation, open InstaCal and configure your I/O board."
    read -p "Press Enter when done"

    # Upgrade pip
    python -m pip install --upgrade pip

    # Install MCCULW library for Python
    python -m pip install mcculw

    echo "Windows setup complete. Ensure InstaCal is installed and configured separately."

elif [[ "$OSTYPE" == "linux"* ]]; then
    echo "Detected Linux environment."

    # Install required build tools
    sudo apt-get update
    sudo apt-get install -y gcc g++ make

    # Install libusb library
    sudo apt-get install -y libusb-1.0-0-dev

    # Download, extract, and install libuldaq
    wget -N https://github.com/mccdaq/uldaq/releases/download/v1.2.1/libuldaq-1.2.1.tar.bz2
    tar -xvjf libuldaq-1.2.1.tar.bz2
    cd libuldaq-1.2.1
    ./configure && make
    sudo make install
    cd ..

    # Install Python uldaq library
    python3 -m pip install uldaq

    echo "Linux setup complete."
else
    echo "Unsupported operating system: $OSTYPE"
    exit 1
fi

pip install numpy
pip install board
pip install easygui
pip install RPI.GPIO
pip3 install adafruit-circuitpython-mpr121
pip install opencv-python
pip install tkintertable
pip install pandas
