import re
import argparse
import timeparser
import datetime
import calendar

parser = argparse.ArgumentParser(description="""
Modify Version.java with the given build number, and prompt for when the
build is mandatory.
""")
parser.add_argument("build", help="Build number to set", type=int)
parser.add_argument("path", help="Path to Version.java")
args = parser.parse_args()

with open(args.path) as version_file:
    version_contents = version_file.readlines()
    version_contents = "".join(version_contents)


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

build_replacement = build_number_line.format(args.build)
version_contents = build_match.sub(build_replacement, version_contents)
print("Set build number to {}.".format(args.build))


def write_version():
    with open(args.path, "w") as version_file:
        version_file.write(version_contents)


def prompt(prompt):
    while True:
        try:
            # TODO: Python 3 renames raw_input() to input()
            choice = raw_input(prompt + " [y/n] ")
            return choice.lower() == "y"
        except EOFError:
            pass

if not prompt("Will this build be mandatory?"):
    write_version()
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

if not old_match.search(version_contents):
    print("Cannot find oldLastGoodBuild")
    exit(1)

previous_new = new_match.search(version_contents)
if not previous_new:
    print("Cannot find newLastGoodBuild")
    exit(1)

if not mandatory_match.search(version_contents):
    print("Cannot find previous mandatory")
    exit(1)

previous_new = previous_new.group(1)
# Previous newLastGoodBuild becomes current oldLastGoodBuild
current_old = old_line.format(previous_new)
version_contents = old_match.sub(current_old, version_contents)

# Current build becomes newLastGoodBuild
current_new = new_line.format(args.build)
version_contents = new_match.sub(current_new, version_contents)

current_mandatory = mandatory_line.format(
    mandatory_date.year,
    calendar.month_name[mandatory_date.month].upper(),
    mandatory_date.day
)
version_contents = mandatory_match.sub(current_mandatory, version_contents)

write_version()
