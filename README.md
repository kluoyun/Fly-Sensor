# Fly-Sensor

## Install

Note: The old version of klipper is not supported, please be sure to use the latest version of klipper

1. Pull the latest version of klipper

    ```
    cd ~/klipper
    git pull
    ```
    
    * If you have modified klipper in the past and the pull failed, please use the following command. (This operation will discard files you have previously modified)
  
    ```
    cd ~/klipper
    git checkout .
    git pull
    ```
      
2. Pull the warehouse source code and install it to klipper

    ```
    cd ~/
    git clone https://github.com/kluoyun/Fly-Sensor
    sudo chmod +x ./Fly-Sensor/scripts/install.sh
    sudo ./Fly-Sensor/scripts/install.sh

    ```
3. Notice!!!

    * During the installation process, any error message before outputting "Done!" may indicate that the installation failed.
    * A clean terminal output of "Done!" indicates that the installation is successful.
