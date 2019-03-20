# 640 480 Beautiful
xvfb-run --auto-servernum --server-args="-screen 0 624x324x24" \
    unity_vol/executable_unix/synvid.x86_64 -batchmode \
    -screen-width=$1 -screen-height=$2 -screen-quality=$3 \
    -http-port=8080
