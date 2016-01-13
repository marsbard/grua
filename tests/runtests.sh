#!/bin/bash

cd "`dirname $0`"

function announce	{
  echo
	echo "[runtests] $*"
}

DIRS=`ls -F | grep /`
announce $DIRS
for d in $DIRS
do
	announce "Running test in '$d'"
	if [ -f $d/DESCR ]
	then
		cat $d/DESCR
	fi
	$d/runtest.sh
	ERR=$?
	echo $ERR
	if [ "$ERR" = "0" ]
	then
		announce "Test [$d] passed"
	else
		announce "Test [$d] passed"
		exit 1
	fi
done
