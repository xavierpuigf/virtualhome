#wget http://virtual-home.org/release/simulator/linux_sim.zip
unzip linux_sim.zip
mkdir executable_unix
mv *.x86_64 executable_unix/exec_linux.x86_64
mv *Data executable_unix/exec_linux_Data
mkdir unity_vol
chmod 777 unity_vol
mv executable_unix unity_vol/
