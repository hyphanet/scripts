import argparse
import glob
import os

parser = argparse.ArgumentParser(description="""
Filter lines (except "End") present in the first file from others matching the
pattern.

The directory containing the source file is searched for files matching the
pattern.
""")
parser.add_argument("source",
                    help="Path to source file of key-value pairs to remove")
parser.add_argument("pattern",
                    help="Glob expression matching files to remove from")
args = parser.parse_args()

with open(args.source) as source_file:
    source_lines = set(source_file.readlines())

os.chdir(os.path.dirname(args.source))

for filename in glob.iglob(args.pattern):
    if not os.path.isfile(filename):
        continue
    if filename == os.path.basename(args.source):
        continue

    with open(filename) as matched_file:
        lines = matched_file.readlines()

    removals = 0
    with open(filename, "w") as output_file:
        for line in lines:
            if line != "End\n" and line in source_lines:
                removals += 1
                continue
            output_file.write(line)
    if removals:
        print("Removed {} lines from {}".format(removals, filename))
