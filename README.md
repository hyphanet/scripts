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
    $ git clone git://github.com/freenet/fred-official.git
    $ git clone git://github.com/freenet/lib-pyFreenet-staging.git
    $ cp scripts/freenetrc-sample ~/.freenetrc
    $ scripts/set-freenetrc-base
    $ mkdir FreenetReleased
    $ wget https://downloads.freenetproject.org/alpha/freenet-ext.jar -O FreenetReleased/freenet-ext.jar
    $ wget http://www.bouncycastle.org/download/bcprov-jdk15on-149.jar -O FreenetReleased/bcprov.jar
    $ wget http://amphibian.dyndns.org/flogmirror/mykey.gpg -O toad.gpg
    $ gpg --import toad.gpg
    $ cd lib-pyFreenet-staging
    # python setup.py install

Now everything should be installed and sufficiently configured. Make sure a Freenet node is accessible by FCP.


    $ cd ../scripts
    $ ./verify-build

## Merging localization files

The `MergeSFS` utility is in the Fred source tree: `src/freenet/tools/MergeSFS.java`.

    java -cp freenet.jar freenet.tools.MergeSFS src/freenet/node/l10n/freenet.l10n.ja.properties freenet.l10n.ja.override.properties

This will write the changes in the override file to the source file. To write the merged values to standard output instead, use `--stdout` as the third argument.

## Releasing Freenet

To upload things to the FPI webserver requires SSH access and membership (`usermod -aG [group] [user]`)in the `www-downloads` group.

To set up a release environment, set up freenetrc, then (read through and) run `setup-release-environment`. Performing a release requires:

* push access to `fred-staging` and `fred-official`
* SSH access to the FPI webserver. (Osprey)
* FPI Google Code credentials (in `~/.send2goog.conf.gpg` - see `release-to-googlecode`
* (Encrypted) auto-update keys at the location set in `insertKeys` in `freenetrc`.
* A published gpg keypair.
* [`send2goog`](https://code.google.com/p/send2goog/) (as included in the repo) on the path.
* A jarsigner certificate. This can be a self-signed one, though once (or if) one exists for FPI one should use it. See [here](http://docs.oracle.com/javase/6/docs/technotes/tools/windows/keytool.html). For example: `keytool -genkeypair -keyalg RSA -sigalg SHA256withRSA -keysize 4096 -dname "cn=Robert Releaserson, o=The Freenet Project Inc, c=US" -alias freenet -storepass SomePassphrase -validity 365 -keystore ~/.keystore`
 * Set freenetrc `jarsignerAlias` and `jarsignerPassword` to the alias and store passphrase, respectively.


Run `release-build`. It will run these steps:

1. `tag-build [build number]` tags a build and prompts for a changelog.

2. `release-fred` builds the Fred jar and source archive, signs them, creates l10n diffs, and uploads all to osprey.
If used with `--snapshot` inserts the Fred jar and signature into Freenet.

3. `release-installer` builds the Linux/OS X installer and uploads it to osprey.

4. `release-wininstaller` builds the Windows installer and uploads it to osprey.

5. `java -jar [location of released jars]/new_installer_offline_[buildnumber].jar` runs an installer. The release manager should test installing a node both with the Linux / OS X installer and the Windows one. It should be able to bootstrap successfully, access FProxy, and otherwise have no obvious problems.

6. `upload-snapshots-googlecode` uploads the jars and installers to Google Code which serves the majority of downloads.

7. `deploy-website`, when run from osprey, updates the website to point to the latest version as defined by the given `fred-official` repository. The script's `-u` switch updates both `fred-offical` and `website-staging`, so if one wants to avoid pulling in website changes as well it may be preferable to manually update the `fred-official` repository only. For extra security check that the HEAD object ID matches between that on osprey and a local copy of the repository.

8. `insert-update` inserts the jars over FCP via a node on port 9482. This is intended to be the test node which was installed by testing the installer as above. This is so that a development node which may have heavy logging does not leak the keys into the logs.

9. Once the inserts have completed announce the release.
