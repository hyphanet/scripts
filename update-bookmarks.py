#!/usr/bin/env python2
import fcp
import argparse

parser = argparse.ArgumentParser(description="""
Read a SFS of name-value pairs and update any URIs (whose names end in "URI")
with new editions.
""")
parser.add_argument("--host", default="127.0.0.1", help="FCP host")
parser.add_argument("--port", default=9481, type=int, help="FCP port")
parser.add_argument("--verbose", "-v", action="store_true",
                    help="Whether to print URIs as they are fetched")
parser.add_argument("path", help="File to update")

args = parser.parse_args()

# TODO: Import constants from Java
# https://wiki.freenetproject.org/FCPv2/GetFailed#Fetch_Error_Codes
REDIRECT = 27

node = fcp.node.FCPNode(host=args.host, port=args.port)

with open(args.path) as bookmark_file:
    bookmarks = bookmark_file.readlines()

with open(args.path, "w") as bookmark_file:
    for line in bookmarks:
        if line and line != "End\n":
            key, value = line.split("=", 1)
            if key.endswith("URI"):
                try:
                    # readlines() lines end with a newline.
                    uri = value.rstrip()

                    if args.verbose:
                        print("Fetching {}".format(uri))

                    node.get(uri, nodata=True)

                    if args.verbose:
                        print("Success - up to date.")
                except fcp.FCPGetFailed as e:
                    if e.info['Code'] == REDIRECT:
                        if args.verbose:
                            print("Updating")
                        uri = e.info['RedirectURI']
                        bookmark_file.write("{}={}\n".format(key, uri))
                        continue
                    else:
                        print("Get failed unexpectedly: {}".format(e))
                        exit(1)

        # Either successful get or not URI line.
        bookmark_file.write(line)
