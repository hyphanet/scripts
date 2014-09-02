from pydrive.auth import GoogleAuth
from pydrive.drive import GoogleDrive
from os.path import exists, dirname, basename, abspath, isfile
import argparse

description = """This uploads a release to Google Drive: the .jar,
the source archive, the Java installer, the Windows installer, and signatures
for each.

It also outputs links to the files as Bash variables for use in the website
scripts.

It assumes the build tag is 'build' followed by the build number
zero-padded on the left to 5 characters."""
parser = argparse.ArgumentParser(description=description)
parser.add_argument('--release_directory',
                    help="Path to the FreenetReleased directory containing the "
                         "files. Must be specified if uploading.")
parser.add_argument('build_number', help="Build number of the release",
                    type=int)
parser.add_argument('--list_file', default='google_drive_links',
                    help="File to output links to. Defaults to "
                         "google_drive_links")
parser.add_argument('--auth_type', choices=['cmdline', 'browser'],
                    default='browser',
                    help="Type of authentication to use. Either cmdline or "
                         "browser. Defaults to browser.")
parser.add_argument('--skip_upload', action="store_true",
                    help="If specified skip uploading files, but still list "
                         "them.")
args = parser.parse_args()

args.build_tag = "build{0:05d}".format(args.build_number)


# TODO: These functions could be moved to a module to make the
# top-level clearer when reading from the top.
def upload(files, parent_id, drive, release_directory):
    # Prefix path to release directory.
    parser.release_directory = abspath(dirname(release_directory))
    files = map(lambda x: release_directory + '/' + x, files)

    # All must exist.
    for filename in files:
        if not exists(filename):
            print 'Error: Cannot find "{0}".'.format(filename)
            exit(1)
        if not isfile(filename):
            print 'Error: "{0}" is not a file.'.format(filename)
            exit(1)

    print "Uploading:"
    for filename in files:
        print filename
        new_file = drive.CreateFile()
        new_file.SetContentFile(filename)
        new_file['title'] = basename(filename)
        new_file['parents'] = [{'id': parent_id}]
        # TODO: If descriptions are desirable they would be set here.
        new_file.Upload()

    print "Upload complete."

    # TODO: Delete files of previous releases to avoid running out of space.
    # Drive has 15 GB of space so this is not an immediately pressing concern.


def list_files(files, parent_id, drive):
    """
    Look up content links to files with titles equal to the given file names.

    Return content links in order of the names in files, and an empty string
    if a unique file with the title was not found.
    """
    links = []
    for filename in files:
        query = "'{0}' in parents and title='{1}'".format(parent_id, filename)
        file_listing = drive.ListFile({'q': query}).GetList()
        if len(file_listing) != 1:
            print 'Warning: Cannot find unique file with title "{0}".'.format(
                filename)
            link = ''
        else:
            link = file_listing[0]['webContentLink']

        links.append(link)

    return links

# Build file names.
files = [
    "freenet-{0}.jar".format(args.build_tag),
    "freenet-{0}-source.tar.bz2".format(args.build_tag),
    "new_installer_offline_{0}.jar".format(args.build_number),
    "FreenetInstaller-{0}.exe".format(args.build_number),
]

# Add a signature for each file.
files.extend(map(lambda x: x + '.sig', files))

# Bash script names for each file. Output in the link list. Used for
# generating the website.
file_variables = [
    'FREENET_MAIN_JAR',
    'FREENET_SOURCE',
    'FREENET_INSTALLER',
    'FREENET_WINDOWS_INSTALLER',
]

# Add _SIG entries for signatures.
file_variables.extend(map(lambda x: x + '_SIG', file_variables))

# Add _URL to the end of each. It should be really clear that this
# substitution key is for a URL.
file_variables = map(lambda x: x + '_URL', file_variables)

if len(files) != len(file_variables):
    raise AssertionError('Programming error: the number of files differs from '
                         'the number of Bash variables for files.')

gauth = GoogleAuth()
if args.auth_type == 'cmdline':
    gauth.CommandLineAuth()
elif args.auth_type == 'browser':
    # If it tries multiple ports it might not match the registered callback URL,
    # so only try one.
    gauth.LocalWebserverAuth(port_numbers=[8080])
else:
    raise AssertionError('Programming error: nothing to do for auth_type value '
                         '{0}'.format(args.auth_type))

drive = GoogleDrive(gauth)

folder_name = "Downloads for Freenet"
query = "title='{0}'and mimeType='application/vnd.google-apps.folder'"\
    .format(folder_name)
file_listing = drive.ListFile({'q': query}).GetList()

if len(file_listing) != 1:
    raise RuntimeError('Could not find unique folder with the title "{0}".'
                       .format(folder_name))
folder = file_listing[0]
parent_id = folder['id']

if not args.skip_upload:
    upload(files, parent_id, drive, args.release_directory)

with open(args.list_file, 'w') as list_out:
    list_out.write("""# Generated for build {0} with upload-to-google-drive.py
# This file should probably not be manually modified - just generated again.
linkBuildNumber={0}\n""".format(args.build_number))
    links = list_files(files, parent_id, drive)
    for variable, link in zip(file_variables, links):
        list_out.write('{0}="{1}"\n'.format(variable, link))
