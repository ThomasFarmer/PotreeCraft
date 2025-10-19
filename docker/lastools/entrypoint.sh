#!/usr/bin/env bash

CMD="$1"
shift

if [ "$CMD" = "" ]; then
    echo "Available executables:"
    cd /LAStools/bin/ && find . -name "*.exe"
else
    wine /LAStools/bin/$CMD.exe $@;
fi