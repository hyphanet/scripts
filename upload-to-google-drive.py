from pydrive.auth import GoogleAuth
from pydrive.drive import GoogleDrive
from os.path import exists, dirname, abspath, isfile
import argparse

description = """This uploads a release to Google Drive: the .jar,
the source archive, the Java installer, the Windows installer, and signatures
for each. It assumes the build tag is 'build' followed by the build number
zero-padded on the left to 5 characters."""
parser = argparse.ArgumentParser(description=description)
parser.add_argument('release_directory', help="Path to the FreenetReleased "
                                              "directory containing the files")
parser.add_argument('build_number', help="Build number of the release",
                    type=int)
parser.add_argument('--auth_type', choices=['cmdline', 'browser'],
                    default='browser',
                    help="Type of authentication to use. Either cmdline or "
                         "browser. Defaults to browser.")
args = parser.parse_args()

args.build_tag = "build{0:05d}".format(args.build_number)

# Build file names.
files = [
    "freenet-{0}.jar".format(args.build_tag),
    "freenet-{0}-source.tar.bz2".format(args.build_tag),
    "new_installer_offline_{0}.jar".format(args.build_number),
    "FreenetInstaller-{0}.exe".format(args.build_number),
]

# Add a signature for each file.
signature_files = []
for filename in files:
    signature_files.append(filename + ".sig")

files.extend(signature_files)

# Prefix path to release directory.
parser.release_directory = abspath(dirname(args.release_directory))
files = map(lambda x: parser.release_directory + '/' + x, files)

# All must exist.
for filename in files:
    if not exists(filename):
        print 'Error: Cannot find "{0}".'.format(filename)
        exit(1)
    if not isfile(filename):
        print 'Error: "{0}" is not a file.'.format(filename)
        exit(1)

gauth = GoogleAuth()
if args.auth_type == 'cmdline':
    gauth.CommandLineAuth()
elif args.auth_type == 'browser':
    # If it tries multiple ports it might not match the registered callback URL,
    # so only try one.
    gauth.LocalWebserverAuth(port_numbers=[8080])
else:
    raise RuntimeError('Programming error: nothing to do for auth_type value '
                       '{0}'.format(args.auth_type))

drive = GoogleDrive(gauth)

print "Uploading:"
for filename in files:
    new_file = drive.CreateFile()
    new_file.SetContentFile(filename)
    print filename
    new_file.Upload()

print "Upload complete."

# TODO: Delete files of previous releases to avoid running out of space.
# Drive has 15 GB of space so this is not an immediately pressing concern.
