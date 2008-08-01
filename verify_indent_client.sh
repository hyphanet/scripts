#!/bin/bash
#
# A small script to verify 'indent only' commits client-side comparing the java bytecode
#
# Parameters: take the svn-revision number as its first parameter
# Author: Florent Daignière
# Year: 2007
#
# *WARNING* keep in mind that it operates only on .java files!

TMP="/tmp"
LC_ALL=en_GB
RAND=$RANDOM
REV=$1
PREVIOUSREV=$(( $REV - 1 ))
JAVACOPT="-source 1.5 -target 1.5 -nowarn -g:none"
REPOSITORY="https://emu.freenetproject.org/svn"
CLASSPATH="/home/nextgens/src/freenet/node1/freenet-cvs-snapshot.jar:/home/nextgens/src/freenet/node1/freenet-ext.jar"

mkdir $TMP/$RAND
cd $TMP/$RAND

# get the sum-up of the commit
svn log --limit=1 -v -r $REV $REPOSITORY >log

# get the name of the author of the commit
AUTHOR="$(head -2 log|tail -1|awk '{print $3;}')"
touch ok nok

# ensure that they are only modified files in the commit
if [[ $(grep -cE '^[ ]{3}[^M] /' log) -gt 0 ]]
then
	echo "Some files have been added or deleted..." > nok
fi

# build the file list
grep -E '^[ ]{3}M /' log |awk '{print $2;}'|grep -iE .java$ > list

while read file
do
	FILENAME="$(echo $file|sed 's/.*\///g')"
	mkdir "$RAND-$FILENAME" && cd "$RAND-$FILENAME"

	mkdir orig && cd orig
	svn cat -r $PREVIOUSREV $REPOSITORY/$file > "$FILENAME"
	javac -classpath "$CLASSPATH" $JAVACOPT "$FILENAME"
	rm $FILENAME
	cd ..

	mkdir new && cd new
	svn cat -r $REV $REPOSITORY/$file > "$FILENAME"
	javac -classpath "$CLASSPATH" $JAVACOPT "$FILENAME"
	rm $FILENAME
	cd ../

	diff -Naurq orig new >> ../nok
	if [[ $? -eq 0 ]]
	then
		for hash in $(find orig -type f -name \*class|sort)
		do
			sha1sum "$hash" |awk '{print $2 " : " $1;}' >> ../ok
		done
	else
		for hash in $(find orig -type f -name \*class|sort)
		do
			echo $hash : $(sha1sum "$hash"|awk '{print $1;}') : $(sha1sum "${hash/orig/new}"|awk '{print $1;}') >> ../nok
		done
	fi
	cd ..
done <list
echo "$AUTHOR has declared that $REV is an 'indent only' commit:"
if test -s nok
then 
	echo -e "\tThat's FALSE.\n"
elif test -s list
then
	echo -e "\tThat's TRUE.\n"
fi
cat ok nok
rm -r $TMP/$RAND
