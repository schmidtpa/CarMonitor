#!/bin/bash

while IFS='' read -r line || [[ -n "$line" ]]; do
	if [[ $line == TRACK_PATH* ]]; then
		path = ${line##*=}	
		ls -t "${path}*.log" | tail -n +2 | xargs bzip2 -f
		exit
	fi	
done < "$1"
