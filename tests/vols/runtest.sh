#!/bin/bash

cd "`dirname $0`"


GRUA_TEST="foo0301qc[p"
GRUA_TEST2="kdqjf40"
GRUA_TEST3="kasdeffq1"

grua -:q enter voltest sh -c "echo $GRUA_TEST > /data/testfile"

CHECK=`cat /var/lib/grua/volumes/gruatests/voltest/data/testfile`


TEST="default vol test"

if [ "$CHECK" = "$GRUA_TEST" ]
then
	echo "[OK] $TEST passed: $CHECK=$GRUA_TEST"
	RESULT=0
else
	echo "[ER] $TEST failed: $CHECK!=$GRUA_TEST"
	RESULT=99
fi
grua -:q enter voltest sh -c "rm /data/testfile"

grua -:q enter voltest sh -c "echo $GRUA_TEST2 > /local/testfile"

TEST="local vol test"
CHECK2=`cat ./local/testfile`
if [ "$CHECK2" = "$GRUA_TEST2" ]
then
	echo "[OK] $TEST passed: $CHECK2=$GRUA_TEST2"
	RESULT=0
else
	echo "[ER] $TEST failed: $CHECK2!=$GRUA_TEST2"
	RESULT=98
fi
grua -:q enter voltest sh -c "rm -rf /local/testfile"

grua -:q enter voltest sh -c "echo $GRUA_TEST3 > /abs/testfile"

TEST="abs vol test"
CHECK3=`cat /tmp/testfile`
if [ "$CHECK3" = "$GRUA_TEST3" ]
then
	echo "[OK] $TEST passed: $CHECK3=$GRUA_TEST3"
	RESULT=0
else
	echo "[ER] $TEST failed: $CHECK3!=$GRUA_TEST3"
	RESULT=97
fi
grua -:q enter voltest sh -c "rm -rf /abs/testfile"


rm -rf /var/lib/grua/volumes/gruatests/voltest/data/testfile ./local

exit $RESULT
