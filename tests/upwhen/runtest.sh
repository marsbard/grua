#!/bin/bash

cd "`dirname $0`"


grua mode quiet
grua fill -q

grua stack -q

OUT=`docker logs gruatests_upwhen`

# search for "Timed out"
echo -n "Don't want to see 'Timed Out' here: "
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

# search for "WOOPWOOP" (from grua.yaml)
echo -n "Want to see WOOPWOOP here: "
echo $OUT | grep "WOOPWOOP" 2>&1 > /dev/null
if [ $? = 0 ]
then
	echo PASS
	RESULT=0
else
	echo FAIL
	RESULT=99
fi


grua unstack -q

exit $RESULT

