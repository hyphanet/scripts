# Freenet Utility Scripts

See `freenetrc-sample` for script configuration.

Anything which is useful for the development of freenet, which isn't an app, a plugin, or part of Freenet itself.

Obviously the actual private keys etc won't be included...

Note that some of these scripts are supposed to run as different users:

- Most stuff involved in releasing a build is on one user.
- Some of it is on a different user.
- grabbackup is on a third user (which is just used for backups).

You will also need ssh access to osprey.

## Verifying Fred builds

Currently the official builds are made using Debian Squeeze, and verify-build verifies only freenet.jar. It does not verify freenet-ext, libraries, source archives, or installers. `lib-pyFreenet` is used for `fcpget` to fetch and verify the freenet.jar inserted into Freenet.

Enable non-free repositories so that Oracle's Java package is available. Add `non-free` to the end of the main repository line. (Ex. `deb http://ftp.us.debian.org/debian squeeze main`.) Then `apt-get update` to apply those changes. Of course the following is just one way to do things.

    # apt-get install git-core python sun-java6-jdk ant unzip
    $ git clone git://github.com/freenet/scripts.git
    $ git clone git://github.com/freenet/fred.git
    $ git clone git://github.com/freenet/lib-pyFreenet.git
    $ cp scripts/freenetrc-sample ~/.freenetrc
    $ scripts/set-freenetrc-base
    $ mkdir FreenetReleased
    $ wget https://downloads.freenetproject.org/alpha/freenet-ext.jar -O FreenetReleased/freenet-ext.jar
    $ wget http://www.bouncycastle.org/download/bcprov-jdk15on-149.jar -O FreenetReleased/bcprov.jar
    $ wget http://amphibian.dyndns.org/flogmirror/mykey.gpg -O toad.gpg
    $ gpg --import toad.gpg
    $ cd lib-pyFreenet
    # python setup.py install

Now everything should be installed and sufficiently configured. Make sure a Freenet node is accessible by FCP.


    $ cd ../scripts
    $ ./verify-build

## Merging localization files

The `MergeSFS` utility is in the Fred source tree: `src/freenet/tools/MergeSFS.java`.

    java -cp freenet.jar freenet.tools.MergeSFS src/freenet/node/l10n/freenet.l10n.ja.properties freenet.l10n.ja.override.properties

This will write the changes in the override file to the source file. To write the merged values to standard output instead, use `--stdout` as the third argument.

## Releasing plugins

Run `release-plugin [plugin name]`. This requires that there is a repository of that plugin (or a link to one) at `$freenetRoot/plugin-[plugin name]`. Update the key in the plugin manager, and test that the plugin loads correctly. Do not increment the mandatory version for connection-essential plugins like UPnP: they will not be loaded and the new version cannot be fetched without a connection.

## Releasing Freenet

To upload things to the FPI webserver requires SSH access and membership (`usermod -aG [group] [user]`) in the `www-downloads` and `www-freenet-website` groups.

To set up a release environment, set up freenetrc, then (read through and) run
`setup-release-environment`. This will install required packages (under Debian
Wheezy), clone the repositories, and download the IP to country database.
This should be kept up to date - maybe a cronjob would be good. Note
that this should not be at the start of an hour
[lest their server be overwhelmed](http://software77.net/faq.html#automated).

Performing a release requires:
* push access to `fred`
* SSH access to the FPI webserver. (Osprey) Take care to set a host `~/.ssh/config` entry if you need a different username.
* (Encrypted) auto-update insert key at the location set in `insertKeys` in `freenetrc`.
This should contain `NEWKEY=SSK@...,...,...` (bare SSK - no name or trailing
slash. Surrounding the value with double quotes is optional.)
* A published gpg keypair.
* A copy of the `seedrefs` directory from another release manager. (If updating seednodes.fref)
* Dependencies such as plugins either built or
[downloaded](https://github.com/freenet/fred/blob/next/src/freenet/pluginmanager/OfficialPlugins.java#L23),
(listing of loadedFrom() CHKs) into FreenetReleased. Repositories using these files can be set up with symlinks.
* That pyDrive is [set up](http://pythonhosted.org/PyDrive/quickstart.html#authentication).
  (Already installed by `setup-release-environment`.) Note that this
  requires setting a product name and email address on the "APIs & Auth" > "Consent Screen" page.
  To avoid the application launching a browser as in the authentication directed by the quick start guide,
  create an "installed application" OAuth client ID and change `googleDriveAuth` in `freenetrc` to `"cmdline"`.
* A jarsigner certificate. This can be a self-signed one, though once (or if) one exists for FPI one should use it. See [here](http://docs.oracle.com/javase/6/docs/technotes/tools/windows/keytool.html). For example: `keytool -genkeypair -keyalg RSA -sigalg SHA256withRSA -keysize 4096 -dname "cn=Robert Releaserson, o=The Freenet Project Inc, c=US" -alias freenet -storepass SomePassphrase -validity 365 -keystore ~/.keystore`
 * Set freenetrc `jarsignerAlias` and `jarsignerPassword` to the alias and store passphrase, respectively.
* For the Java installer: [launch4j](http://sourceforge.net/projects/launch4j/)
(3.0.2 as of this writing) as `lib/launch4j`, and [IzPack](http://izpack.org/) 4's
`standalone-compiler.jar` in `lib/`.
* For the Windows installer: see the list in the header of `build.cmd`, though
`release-wininstaller` assumes locations in `FreenetReleased/` and `FreenetReleased/dependencies`.
Note that non-L AutoHotKey appears to no longer be hosted, and AutoHotKey-L
triggers some resource packaging bug in Wine that results in 0-byte files. See
[here](https://bugs.freenetproject.org/view.php?id=5456#c9812). In the case of
configuration problems or prompts it might be useful to also install `xnest` and
run `release-wininstaller --dry-run --xnest` first.
* The FPI code signing certificate set up as though with

    keytool -importkeystore -srckeystore code-signing.p12  -srcstoretype pkcs12 -srcalias "freenet project inc's comodo ca limited id" -destkeystore ~/.gnupg/freenet/code-signing/code-signing.jks -deststoretype jks -destalias freenet -destkeypass "password"

The node that updates are inserted on cannot be set to log heavily, lest the
update insert key be leaked into logs. freenetrc defaults to using port 9481
for inserting updates under the assumption that the newly installed testing node
is on the port. If it is a node with heavy logging, change fcpUpdatePort.
TODO: The more thorough solution to this would be to check that the logging level
is sufficiently low over FCP.

Also take care that the unencrypted key is not written to disk - disable
swap (or have it encrypted with a random key) and mount `/tmp` on `tmpfs`.

To test auto-updating, useful while setting things up:

1. Set up a node of the previous version. (The new one is the one being deployed currently.)
2. Set the FCP port to the expected one.
3. Make the update insert to local storage at higher priority for speed: Include `LocalRequestOnly=true` and the line before `PCLASS` is used set it to 0.
4. Generate a new SSK keypair.
5. Set up a configuration file with the insert URI.
6. Set the node's autoupdate source to `USK@ssk,contents,.../build number`
7. Restart the node.
8. Run the insert-update script.
9. The node should find, download, verify, and apply the update.

Ensure the fred, scripts, website, Java installer, and Windows installer repositories are up to
date before starting the release. Ensure the bundled plugins in the `FreenetReleased`
(or equivalent) directory are up to date as well.

The first release with an environment, run these steps individually to get all the configuration right. Once everything works, run `release-build [build number]`, which automates running these steps:

0. `update-bookmarks` updates the default bookmark editions and commits if any changes have been made.

0. `update-version` updates the version number, and prompts for and updates the mandatory dates if applicable.

1. `tag-build [build number]` tags a build and prompts for a changelog.

2. `release-fred` builds the Fred jar and source archive, signs them, creates l10n diffs, and uploads all to osprey.
If used with `--snapshot` inserts the Fred jar and signature into Freenet.

3. `release-installer` builds the Linux/OS X installer and uploads it to osprey.

4. `release-wininstaller` builds the Windows installer and uploads it to osprey.

5. `java -jar [location of released jars]/new_installer_offline_[buildnumber].jar` runs an installer. The release manager should test installing a node both with the Linux / OS X installer and the Windows one. It should be able to bootstrap successfully, access FProxy, and otherwise have no obvious problems.

6. `upload-to-google-drive.py` uploads the jars and installers to Google Drive which serves the majority of downloads.

7. `deploy-website`, when run from osprey, updates the website to point to the latest version as defined by the given `fred` repository. The script's `-u` switch updates both `fred` and `website`, so if one wants to avoid pulling in website changes as well it may be preferable to manually update the `fred` repository only, or use the `--force-*-id` options.

8. `insert-update` inserts the jars over FCP. This is intended to be the test node which was installed by testing the installer as above. This is so that a development node which may have heavy logging does not leak the keys into the logs.

9. Once the inserts have completed announce the release: FMS, IRC (including the channel topic), devl, support, website, Wikipedia article.
