#!/bin/sh


PROG=`ps -e | awk -F" " -v NAME="watch_caffe.sh" '{if($4==NAME)print $1 " "}'`
for M in ${PROG}
do
	kill -9 ${M}
done

killall python