#!/bin/bash

TS_1=`docker logs gruatests_before1`
TS_2=`docker logs gruatests_before2`

echo -n "Checking that 2nd container is started before the first: "

if [ $TS1 -gt $TS2 ]
then
	echo PASS
	RESULT=0
else
	echo FAIL
	RESULT=99
fi



exit $RESULT
