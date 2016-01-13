#!/bin/bash

cd "`dirname $0`"

#grua mode noisy
grua mode quiet

grua fill

grua stack
sleep 1

GRUA_TEST="foo0301qc[p"

grua enter voltest sh -c "echo $GRUA_TEST > /data/testfile"

CHECK=`cat /var/lib/grua/volumes/gruatests/voltest/data/testfile`

#echo CHECK=$CHECK
grua enter voltest sh -c "rm /data/testfile"

sleep 1

if [ "$CHECK" = "$GRUA_TEST" ]
then
	echo "[OK] env test passed: $CHECK=$GRUA_TEST"
	RESULT=0
else
	echo "[ER] env test failed: $CHECK!=$GRUA_TEST"
	RESULT=99
fi


grua unstack
sleep 1


grua mode noisy
exit $RESULT
