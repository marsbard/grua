#!/bin/bash

TS_1=`docker logs gruatests_after1`
TS_2=`docker logs gruatests_after2`

echo -n "Checking that 1st container is started after the 2nd: "

if [ $TS1 -gt $TS2 ]
then
	echo PASS
	RESULT=0
else
	echo FAIL
	RESULT=99
fi



exit $RESULT
