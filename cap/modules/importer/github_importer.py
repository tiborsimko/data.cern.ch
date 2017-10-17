import os
import urllib
import utils
from github import Github
from importer import Importer


class GithubImporter(Importer):

    def __init__(self, repo, token=None):
        self.repo = repo
        self.token = token

    def archive_repository(self):
        """ download and archive repo via PyGithub """
        if self.token:
            gh = Github(self.token)
        else:
            gh = Github()
        # self.repo format: username/repository
        repo = gh.get_repo(self.repo)
        link = repo.get_archive_link("tarball")
        urllib.urlretrieve(link, os.path.join(os.getcwd(), "archive.tar.gz"))

    def parse_url(self, url):
        utils.parse_urls(url)
