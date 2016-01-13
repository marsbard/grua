#!/bin/bash

cd "`dirname $0`"

grua mode quiet
#grua mode noisy

grua fill

OUT=`grua stack 2>&1`

# search for "Timed out"
echo $OUT | grep "Timed out" 2>&1 > /dev/null
if [ $? = 0 ]
then
	# found it, therefore test failed
	echo FAIL
	RESULT=9
else
	echo PASS
	RESULT=0
fi


grua unstack

exit $RESULT

