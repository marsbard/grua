#!/bin/bash

cd "`dirname $0`"

#grua mode noisy
grua mode quiet

grua fill

export GRUA_TEST_ENV="asd123poi" 
grua stack

sleep 1

grua enter envtest sh -c "echo \$GRUA_TEST_ENV"
grua mode quiet
CHECK=`grua enter envtest sh -c "echo \$GRUA_TEST_ENV"| sed "s/\r//g"`
#grua mode noisy

sleep 1

if [ "$CHECK" = "$GRUA_TEST_ENV" ]
then
	echo "[OK] env test passed: $CHECK=$GRUA_TEST_ENV"
	RESULT=0
else
	echo "[ER] env test failed: $CHECK!=$GRUA_TEST_ENV"
	RESULT=99
fi


grua unstack
sleep 1


grua mode noisy
exit $RESULT
