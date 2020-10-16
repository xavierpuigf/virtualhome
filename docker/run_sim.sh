# 640 480 Beautiful
xvfb-run --auto-servernum --server-args="-screen 0 640x480x24" \
    unity_vol/executable_unix/exec_linux.x86_64 -batchmode \
    -http-port=8080
    #-screen-width=$1 -screen-height=$2 -screen-quality=$3 \
