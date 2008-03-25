#!/bin/bash
#
# A small script to verify 'indent only' commits server-side comparing the java bytecode
#
# Parameters: take the svn-revision number as its first parameter
# Author: Florent Daignière
# Year: 2007

RAND=$RANDOM
REPOSITORY="/var/freenet-svn/svn/"
REV=$1
PREVIOUSREV=$(( $REV - 1 ))
AUTHOR="$(svnlook author $REPOSITORY --revision $REV)"
JAVACOPT=" -target 1.4 -nowarn -g:none"
CLASSPATH="/var/www/downloads/alpha/$(cat /var/www/downloads/alpha/.latest):/var/www/downloads/alpha/freenet-ext.jar"

if [[ $(svnlook info $REPOSITORY --revision $REV | grep -icE '^[ ]*[Ii]ndent(ing)?([ ])*(:|$)') -gt 0 ]]
then
	mkdir $TMP/$RAND
	cd $TMP/$RAND
	touch ok nok
	svnlook changed $REPOSITORY --revision $REV |awk '{print $2;}'|grep -iE .java$ > list
	while read file
	do
		RESULT=0
		FILENAME="$(echo $file|sed 's/.*\///g')"
		mkdir "$RAND-$FILENAME" && cd "$RAND-$FILENAME"

		mkdir orig && cd orig
		svnlook cat $REPOSITORY "$file" --revision $PREVIOUSREV > "$FILENAME"
		javac -classpath $CLASSPATH $JAVACOPT "$FILENAME"
		RESULT=$(( $RESULT + $? ))
		rm "$FILENAME"
		cd ..

		mkdir new && cd new
		svnlook cat $REPOSITORY "$file" --revision $REV > "$FILENAME"
		javac -classpath $CLASSPATH $JAVACOPT "$FILENAME"
		RESULT=$(( $RESULT + $? ))
		rm "$FILENAME"
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

		if [[ $RESULT -ne 0 ]]
		then
			echo "$FILENAME failed pre-compilation: we can't check whether it's a commit indent or not"  >> ../nok
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
fi
