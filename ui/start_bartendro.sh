#!/bin/sh
cd bartendro/ui
export BARTENDRO_SOFTWARE_ONLY=1
python ./bartendro_server.py --debug  
#python ./bartendro_server.py --debug -t 10.0.0.1 
