#!/bin/bash

cd "`dirname $0`"

function announce	{
	echo "[runtests] $*"
}

function pass {
  echo -e "[runtests] \033[32m" $* "\033[39m"
}


FAILS=()
function fail {
  echo -e "[runtests] \033[31m" $* "\033[39m"
	FAILS+=("$*")
}

function descr {
  echo -e "\033[33m"
	echo ----------------------------------
	cat $1
	echo ----------------------------------
  echo -e "\033[39m"
}

if [ "$1" != "" ]
then
  for x in $*
	do
    if [ ! -d $x ]
		then
			echo "There is no test folder named '$x'"
			exit 1
	  fi
	done
	DIRS=$*
else
  DIRS=`ls -F | grep /`
fi

for d in $DIRS
do
	e=`basename $d`

	announce "Running test in '$e'"
	if [ -f $e/DESCR ]
	then
		descr $e/DESCR
	fi
	
	cd $d

	
	announce Filling $e
	grua fill -:q
	
	announce Stacking $e
	grua stack -:q
	
	announce Running tests:
	./runtest.sh
	ERR=$?
	
	announce Unstacking $e
	grua unstack -:q
	
	cd ..

	if [ "$ERR" = "0" ]
	then
		pass "Test [$e] passed"
	else
		fail "Test [$e] failed"
		#exit 1
	fi
 
	echo

done

if [ ${#FAILS[@]} -gt 0 ]
then
	echo "There were failures: "
	for fail in ${!FAILS[@]}
  do
		echo -e "[runtests] \033[31m" ${FAILS[$fail]}  "\033[39m"
	done
	exit 99
else 
	echo "All tests passed"
fi

exit 0
