# Freenet Utility Scripts

See `freenetrc-sample` for script configuration.

Anything which is useful for the development of freenet, which isn't an app, a plugin, or part of Freenet itself.

Obviously the actual private keys etc won't be included...

Note that some of these scripts are supposed to run as different users:

- Most stuff involved in releasing a build is on one user.
- Some of it is on a different user.
- grabbackup is on a third user (which is just used for backups).

You will also need ssh access to osprey.

## Merging localization files

The `MergeSFS` utility is in the Fred source tree: `src/freenet/tools/MergeSFS.java`.

    java -cp freenet.jar freenet.tools.MergeSFS src/freenet/node/l10n/freenet.l10n.ja.properties freenet.l10n.ja.override.properties

This will write the changes in the override file to the source file. To write the merged values to standard output instead, use `--stdout` as the third argument.

## Releasing Freenet

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

