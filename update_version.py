#!/usr/bin/env python2
import re
import argparse
import timeparser
import datetime
import calendar

parser = argparse.ArgumentParser(description="""
Modify Version.java with the given build number, optionally changing the
mandatory date.
""")
parser.add_argument("build", help="Build number to set", type=int)
parser.add_argument("path", help="Path to Version.java")
parser.add_argument("--change-mandatory",
                    help="Change mandatory information. If specified, --date "
                         "must also be specified.",
                    action="store_true")
parser.add_argument("--version-only", help="Change Version.java, but not the "
                                           "mandatory build.",
                    action="store_true")
parser.add_argument("--date", help="Date the current build goes mandatory in "
                                   "ISO 8601.",
                    type=lambda s: datetime.datetime.strptime(s, "%Y-%m-%d"))
args = parser.parse_args()


def match_number(line):
    return re.compile(line.format(r"(\d+)"))

build_number_line = "private static final int buildNumber = {};"
build_match = match_number(build_number_line)

old_line = "private static final int oldLastGoodBuild = {};"
old_match = match_number(old_line)

new_line = "private static final int newLastGoodBuild = {};"
new_match = match_number(new_line)

# Year, month name, day
mandatory_line = "_cal.set( {}, Calendar.{}, {}, 0, 0, 0 );"
mandatory_match = re.compile(r"_cal\.set\( (\d+), Calendar\.([A-Z]+), (\d+), 0, 0, 0 \);")


def main():
    if args.version_only and args.change_mandatory:
        print("--version-only and --change-mandatory cannot both be specified.")
        exit(1)

    with open(args.path) as version_file:
        version_contents = version_file.readlines()
        version_contents = "".join(version_contents)

    # Replace the build number in Version.java.
    build_replacement = build_number_line.format(args.build)
    version_contents = build_match.sub(build_replacement, version_contents)
    print("Set build number to {}.".format(args.build))

    if args.version_only:
        write_version(version_contents)
        exit()

    if args.change_mandatory:
        write_version(update_mandatory(version_contents, args.date))
        exit()

    write_version(interactive(version_contents))
    exit()


def write_version(version_contents):
    with open(args.path, "w") as version_file:
        version_file.write(version_contents)


def interactive(version_contents):
    if not prompt("Will this build be mandatory?"):
        write_version(version_contents)
        exit()

    print("Durations can be things like '1 week' or '5 days'.")
    today = datetime.datetime.now().date()
    while True:
        try:
            duration_input = raw_input("How long until until mandatory? ")
            duration = timeparser.parsetimedelta(duration_input)
            mandatory_date = today + duration

            if prompt("Go mandatory on {}?".format(mandatory_date)):
                break
        except EOFError:
            print("")
        except ValueError as e:
            print(e)

    return update_mandatory(version_contents, mandatory_date)


def prompt(message):
    while True:
        try:
            # TODO: Python 3 renames raw_input() to input()
            choice = raw_input(message + " [y/n] ")
            return choice.lower() == "y"
        except EOFError:
            pass


def replace(version_contents, match, value):
    contents, replacements = match.subn(value, version_contents)
    if replacements != 1:
        print("Cannot substitute '{}'".format(value))
        exit(1)
    return contents


def update_mandatory(version_contents, mandatory_date):
    previous_new = new_match.search(version_contents)
    if not previous_new:
        print("Cannot find newLastGoodBuild")
        exit(1)

    previous_new = previous_new.group(1)
    # Previous newLastGoodBuild becomes current oldLastGoodBuild
    current_old = old_line.format(previous_new)
    version_contents = replace(version_contents, old_match, current_old)

    # Current build becomes newLastGoodBuild
    # TODO: Only when self-mandatory; allow this to be done differently.
    current_new = new_line.format(args.build)
    version_contents = replace(version_contents, new_match, current_new)

    current_mandatory = mandatory_line.format(
        mandatory_date.year,
        calendar.month_name[mandatory_date.month].upper(),
        mandatory_date.day
    )
    version_contents = replace(version_contents,
                               mandatory_match, current_mandatory)
    return version_contents

if __name__ == "__main__":
    main()
