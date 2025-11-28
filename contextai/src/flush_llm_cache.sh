#!/bin/bash

echo "Flushing RAM and VRAM caches"
sudo sync
echo 3 | sudo tee /proc/sys/vm/drop_caches > /dev/null
sudo nvidia-smi --gpu-reset -i 0
echo "Caches cleared, you can now load another model into memory or have your system set up for general use!"
