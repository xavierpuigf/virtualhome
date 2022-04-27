#!/bin/bash
echo $OSTYPE
if [[ "$OSTYPE" == "linux-gnu" ]]; then
    name_script="linux_sim"
elif [[ "$OSTYPE" == "darwin"* ]]; then
    name_script="mac_sim"
else
    echo "OS not recognized"
fi

base_url="http://virtual-home.org/release/simulator/"
url=$base_url$name_script".zip"
echo "Downloading"
wget $url
mv $name_script.zip simulation/
cd simulation
unzip $name_script.zip
cd ..
echo "Executable moved to simulation folder"
