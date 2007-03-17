#!/bin/bash
# The cvs@freenetproject.org list receives all commits, apart from huge commits which are
# simply unpacking a tarfile. The objective is to make it easy to reconstruct the history
# from human-readable patches.

# This script verifies that a patch from the CVS list is in fact pure whitespace, or shows
# the bits that are not whitespace.
WORKINGCOPY=/usr/src/cvs/eclipse-workspace/Freenet\ 0.7
echo -n "Please enter revision number after patch applied? "
read REVISION
OLDREVISION=$(($REVISION-1))
echo -n "Please enter location of patch from mailing list? "
read FILENAME
# Make a temporary directory
TEMPDIR=`mktemp -d ~/verify-patch-temp-XXXXXXXXXX`
echo Temporary directory: $TEMPDIR
OLDDIR=$TEMPDIR/old
NEWDIR=$TEMPDIR/new
mkdir $OLDDIR $NEWDIR
cp -a "$WORKINGCOPY" $OLDDIR/
cd $OLDDIR
DNAME=`ls`
mv */* */.[a-z0-9]* .
rm -R "$DNAME"
svn revert -R .
svn update -r $OLDREVISION
ant distclean
find -iname .svn | xargs rm -R
rm -R .[a-z0-9]*
cp -a $OLDDIR/* $NEWDIR
cd $NEWDIR
if ! patch -p2 < $FILENAME ; then exit Failed to apply patch ; else echo Applied patch successfully. ; fi
diff -urw $OLDDIR $NEWDIR > $TEMPDIR/diff-uw
if [ -s $TEMPDIR/diff-uw ] ; then less $TEMPDIR/diff-uw ; mv $TEMPDIR/diff-uw ~/${REVISION}.diff ; echo Saved diff in ~/${REVISION}.diff ; else echo No differences found after compensating for whitespace; fi
rm -R $TEMPDIR
