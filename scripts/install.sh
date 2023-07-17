#!/usr/bin/env bash

set -Ee

S_DIR="$( cd -- "$( dirname -- "${BASH_SOURCE[0]}" )" &> /dev/null && pwd -P)/../"
KP_DIR="/home/${SUDO_USER}/klipper"

if [[ "${SUDO_USER}" = "root" ]]; then
    echo "Please do not execute it under the root user"
    exit 1
fi

if [[ -z "${SUDO_USER}" ]]; then
    echo "Requires sudo privileges"
    exit 1
fi

[[ -n "${BASE_USER}" ]] || BASE_USER="${SUDO_USER}"

if [ ! -d "${KP_DIR}" ];then
    echo "No installed klipper found"
    exit 1
fi

if [ -e "${KP_DIR}/src/Makefile_old" ];then
    mv "${KP_DIR}/src/Makefile_old" "${KP_DIR}/src/Makefile"
fi

if [ -e "${KP_DIR}/klippy/extras/probe.py_old" ];then
    mv "${KP_DIR}/klippy/extras/probe.py_old" "${KP_DIR}/klippy/extras/probe.py"
fi

mv "${KP_DIR}/src/Makefile" "${KP_DIR}/src/Makefile_old"
mv "${KP_DIR}/klippy/extras/probe.py" "${KP_DIR}/klippy/extras/probe.py_old"

cp -rf "${S_DIR}/codes/Makefile" "${KP_DIR}/src/Makefile"
cp -rf "${S_DIR}/codes/probe.py" "${KP_DIR}/klippy/extras/probe.py"
cp -rf "${S_DIR}/codes/fly_probe.c" "${KP_DIR}/src/fly_probe.c"
cp -rf "${S_DIR}/codes/fly_probe.py" "${KP_DIR}/klippy/extras/fly_probe.py"

sudo systemctl restart klipper

echo "Done!"
