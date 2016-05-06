#!/bin/bash

cd "`dirname $0`"


GRUA_TEST="foo0301qc[p"

grua -:q enter voltest sh -c "echo $GRUA_TEST > /data/testfile"

CHECK=`cat /var/lib/grua/volumes/gruatests/voltest/data/testfile`



if [ "$CHECK" = "$GRUA_TEST" ]
then
	echo "[OK] env test passed: $CHECK=$GRUA_TEST"
	RESULT=0
else
	echo "[ER] env test failed: $CHECK!=$GRUA_TEST"
	RESULT=99
fi

grua -:q enter voltest sh -c "rm /data/testfile"

exit $RESULT
