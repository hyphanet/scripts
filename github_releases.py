import json
import http.client
import ssl
import os
import mimetypes


class GitHubError(Exception):
    """
    GitHub gave a response other than success. Check the response attribute
    for details.
    """
    def __init__(self, response):
        self.response = response


class UnknownMIMETypeError(Exception):
    """
    A MIME type for the file could not be detected automatically.
    """
    pass


class GitHubReleases(object):

    def __init__(self, oauth_token, user_agent):
        self.base_headers = {
            'Accept': 'application/vnd.github.v3+json',
            'Authorization': 'token {}'.format(oauth_token),
            'User-Agent': user_agent,
        }

        # Python 3.4 adds ssl.create_default_context(), which is preferable, but
        # Debian Wheezy provides Python 3.2. Except for cipher settings, these
        # are those used by ssl.create_default_context().
        context = ssl.SSLContext(ssl.PROTOCOL_SSLv23)
        context.set_default_verify_paths()
        context.verify_mode = ssl.CERT_REQUIRED
        context.options |= ssl.OP_NO_SSLv2 | ssl.OP_NO_SSLv3

        # TODO: Connect once at the start or for each request?
        self.api_host = http.client.HTTPSConnection('api.github.com',
                                                    context=context)
        self.api_host.connect()

        self.uploads_host = http.client.HTTPSConnection('uploads.github.com',
                                                        context=context)
        self.uploads_host.connect()

    def create(self, owner, repo, tag):
        """
        Create a release from a tag in a repo.

        Note that this is a small subset of the GitHub API v3 release creation
        capabilities.

        :param owner: The owner user or organization.
        :param repo: The name of the repository.
        :param tag: The tag to create a release from.
        """
        self.api_host.request("POST",
                              "/repos/{}/{}/releases".format(owner, repo),
                              json.dumps(
                                  {
                                      'tag_name': tag,
                                      'draft': False,
                                      'prerelease': False,
                                  }), self.base_headers)
        return self.__get_response(self.api_host)

    def get(self, owner, repo, tag):
        """
        Get the release for the given tag.

        :param owner: The owner user or organization.
        :param repo: The name of the repository.
        :param tag: The tag to find the release of.
        :return: result for the release with that tag, or None if no such
                 release.
        """
        self.api_host.request("GET",
                              "/repos/{}/{}/releases".format(owner, repo, tag),
                              headers=self.base_headers)
        response = self.__get_response(self.api_host, expecting_code=200)

        for release in response:
            if release['tag_name'] == tag:
                return release
        else:
            return None

    def upload_asset(self, owner, repo, release_id, asset_path,
                     asset_type=None):
        """
        Upload an asset to a release.

        :param owner: The owner user or organization.
        :param repo: The name of the repository.
        :param release_id: ID of the release to upload to.
        :param asset_path: Path to the file to upload.
        :param asset_type: Optional MIME type of the asset. If None or not
                           specified it will be detected.
        :throws UnknownMimeTypeError:
        """
        filename = os.path.basename(asset_path)

        if asset_type is None:
            asset_type = mimetypes.guess_type(filename)[0]
            if asset_type is None:
                raise UnknownMIMETypeError()

        headers = {'Content-Type': asset_type}
        headers.update(self.base_headers)

        self.uploads_host.request(
            "POST",
            "/repos/{}/{}/releases/{}/assets?name={}"
            .format(owner, repo, release_id, filename),
            open(asset_path, "rb"),
            headers
        )
        return self.__get_response(self.uploads_host)

    def list_assets(self, owner, repo, release_id):
        """
        List assets in the release.

        :param owner: The owner user or organization.
        :param repo: The name of the repository.
        :param release_id: ID of the release to list assets from.
        :returns: List of assets.
        """
        self.api_host.request(
            "GET",
            "/repos/{}/{}/releases/{}/assets"
            .format(owner, repo, release_id),
            headers=self.base_headers
        )
        return self.__get_response(self.api_host, expecting_code=200)

    @staticmethod
    def __get_response(host, expecting_code=201):
        # TODO: Does GitHub _always_ give something that's valid JSON? What
        # error handling to have here?
        # TODO: What encoding?
        response = host.getresponse()
        body = response.read()
        result = json.loads(body.decode("utf8"))

        if response.code != expecting_code:
            raise GitHubError(result)

        return result
