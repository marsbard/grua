#!/bin/bash

cd "`dirname $0`"

#grua mode noisy
grua mode quiet

grua fill

export GRUA_TEST_ENV="asd123poi" 
export GRUA_TEST_DEFAULT2="Overridden"

grua stack

sleep 1

grua mode quiet
CHECK=`grua enter envtest sh -c "echo \$GRUA_TEST_ENV"| sed "s/\r//g"`
#grua mode noisy

sleep 1

echo ">> Checking passing environment to container"
if [ "$CHECK" = "$GRUA_TEST_ENV" ]
then
	echo "[OK] env test passed: $CHECK=$GRUA_TEST_ENV"
	RESULT=0
else
	echo "[ER] env test failed: $CHECK!=$GRUA_TEST_ENV"
	RESULT=99
fi

echo ">> Checking default value"
CHECK2=$(grua enter envtest sh -c "echo \$GRUA_TEST_DEFAULT" | sed "s/\r//g")

sleep 1
if [ "$CHECK2" = "This is the default value" ]
then
	echo "[OK] env test passed: $CHECK2"
	RESULT=0
else
	echo "[ER] env test failed: $CHECK2"
	RESULT=99
fi

echo ">> Checking default value override"
CHECK2=$(grua enter envtest sh -c "echo \$GRUA_TEST_DEFAULT2" | sed "s/\r//g")

sleep 1
if [ "$CHECK2" = "Overridden" ]
then
	echo "[OK] env test passed: $CHECK2"
	RESULT=0
else
	echo "[ER] env test failed: $CHECK2"
	RESULT=99
fi

grua unstack
sleep 1


grua mode noisy
exit $RESULT
