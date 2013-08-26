#!/bin/sh

# Goal: We need to edit ini file to change some relative pateches into absolute path.
# Purpose: this is needed as part of verify-build for example.
# Tool: sed.  Will use expressions like: s/releaseDir="\.\./releaseDir="\/home\/fn_verify\/01453/g

# *** First get absolute path to freenet installation that is 1-level up form location of this script (../)
this_script_filename=`realpath $0` 
this_script_dir=`dirname ${this_script_filename}`
freenet_dir=`realpath "${this_script_dir}/../"` # 1 above

# Escape for sed string. Replae "/" with "\/". But "\\/" because sed-escaped, "\\\\/" because bash
freenet_dir_escapedsed=`echo "$freenet_dir" | sed -e 's|/|\\\\/|g'`

for varname in "releaseDir" "fredDir" # replacing
do
	expr1='s/'; expr2='="\.\./'; expr3='="'; expr4='/g' 
	expr="${expr1}${varname}${expr2}${varname}${expr3}${freenet_dir_escapedsed}${expr4}"; 
	sed -e "$expr" ~/.freenetrc > ~/.freenetrc-absolute ; mv ~/.freenetrc-absolute ~/.freenetrc
	# e.g.: sed -e 's/fredDir="\.\./fredDir="\/home\/fn_verify\/01453/g' /home/fn_verify/.freenetrc
done

echo "Fixed the patches, should be absolute now (where needed)"

