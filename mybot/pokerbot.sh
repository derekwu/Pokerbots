#!/bin/sh
export LD_LIBRARY_PATH=`pwd`/export/darwin/lib:$LD_LIBRARY_PATH
python Player.py "$@"
