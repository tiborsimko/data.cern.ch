from github import GithubException, UnknownObjectException
from unittest.mock import Mock, patch
from pytest import raises

from cap.modules.repos.errors import (GitError, GitIntegrationError,
                                      GitObjectNotFound,
                                      GitRequestWithInvalidSignature)
from cap.modules.repos.github_api import Github, GithubAPI


@patch.object(
    Github, 'get_repo',
    Mock(
        side_effect=UnknownObjectException(404, headers={}, data={'message': 'Not Found'}))
)
def test_github_api_when_project_doesnt_exist_or_no_access():
    with raises(GitObjectNotFound):
        GithubAPI('github.com', 'owner', 'repodoesntexist')


@patch.object(Github, 'get_repo')
def test_github_api_auth_headers_when_token_provided(m_get_repo, github_token,
                                                     example_user):
    class MockProject:
        def get_branch(self, name):
            mock = Mock()
            mock.name = name
            mock.commit.sha = 'mybranchsha'
            return mock

    m_get_repo.return_value = MockProject()

    api = GithubAPI('github.com',
                    'owner',
                    'repository',
                    'my-branch',
                    user_id=example_user.id)

    assert api.token == 'some-token'
    assert api.auth_headers == {'Authorization': 'token some-token'}


@patch.object(Github, 'get_repo')
def test_github_api_auth_headers_when_no_token_provided_returns_empty_dict(
        m_get_repo, example_user):
    class MockProject:
        def get_branch(self, name):
            mock = Mock()
            mock.name = name
            mock.commit.sha = 'mybranchsha'
            return mock

    m_get_repo.return_value = MockProject()

    api = GithubAPI(
        'github.com',
        'owner',
        'repository',
        'my-branch',
        example_user.id,
    )

    assert api.token is None
    assert api.auth_headers == {}


@patch.object(Github, 'get_repo')
def test_github_api_repo_id(m_get_repo):
    class MockProject:
        id = 12

        def get_branch(self, name):
            mock = Mock()
            mock.name = name
            mock.commit.sha = 'mybranchsha'
            return mock

    m_get_repo.return_value = MockProject()

    api = GithubAPI(
        'github.com',
        'owner',
        'repository',
        'my-branch',
    )

    assert api.repo_id == 12


@patch.object(Github, 'get_repo')
def test_github_api_with_branch(m_get_repo):
    class MockProject:
        def get_branch(self, name):
            mock = Mock()
            mock.name = name
            mock.commit.sha = 'mybranchsha'
            return mock

    m_get_repo.return_value = MockProject()

    api = GithubAPI(
        'github.com',
        'owner',
        'repository',
        'my-branch',
    )

    assert api.host == 'github.com'
    assert api.owner == 'owner'
    assert api.repo == 'repository'
    assert api.branch == 'my-branch'
    assert api.sha == 'mybranchsha'
    assert api.token == None

    m_get_repo.assert_called_with('owner/repository', lazy=False)

    assert str(api) == 'API for github.com/owner/repository/my-branch'


@patch.object(Github, 'get_repo')
def test_github_api_with_default_branch_when_no_branch_nor_sha_given(
    m_get_repo):
    class MockProject:
        @property
        def default_branch(self):
            return 'def-branch'

        def get_branch(self, name):
            mock = Mock()
            mock.name = name
            mock.commit.sha = 'mybranchsha'
            return mock

    m_get_repo.return_value = MockProject()

    api = GithubAPI('github.com', 'owner', 'repository')

    assert api.host == 'github.com'
    assert api.owner == 'owner'
    assert api.repo == 'repository'
    assert api.branch == 'def-branch'
    assert api.sha == 'mybranchsha'
    assert api.token is None

    m_get_repo.assert_called_with('owner/repository', lazy=False)

    assert str(api) == 'API for github.com/owner/repository/def-branch'


@patch.object(Github, 'get_repo')
def test_github_api_with_sha(m_get_repo):
    class MockProject:
        def get_branch(self, name):
            raise GithubException(404, headers={}, data={'message': 'Branch not found'})

        def get_commit(self, sha):
            mock = Mock()
            mock.sha = sha
            return mock

    m_get_repo.return_value = MockProject()

    api = GithubAPI('github.com', 'owner', 'repository', 'mycommitsha')

    assert api.host == 'github.com'
    assert api.owner == 'owner'
    assert api.repo == 'repository'
    assert api.branch is None
    assert api.sha == 'mycommitsha'
    assert api.token is None

    m_get_repo.assert_called_with('owner/repository', lazy=False)

    assert str(api) == 'API for github.com/owner/repository/mycommitsha'


@patch.object(Github, 'get_repo')
def test_github_api_when_commit_or_branch_with_sha_doesnt_exist_raises_GitObjectNotFound(
    m_get_repo):
    class MockProject:
        def get_branch(self, name):
            raise GithubException(404, headers={}, data={'message': 'Branch not found'})

        def get_commit(self, sha):
            raise GithubException(422, headers={},
                                  data={'message': 'No commit found for SHA:'})

    m_get_repo.return_value = MockProject()

    with raises(GitObjectNotFound):
        GithubAPI('github.com', 'owner', 'repository', 'mycommitsha')


@patch.object(Github, 'get_repo',
              Mock(side_effect=UnknownObjectException(
                  status=404, headers={}, data={'message': 'Not Found'})))
def test_github_api_when_repostiory_doesnt_exist_or_no_access_raises_GitObjectNotFound(
):
    with raises(GitObjectNotFound):
        GithubAPI('github.com', 'owner', 'non-existing-repo')


@patch.object(Github, 'get_repo')
def test_github_api_when_just_created_repo_without_any_branches_raises_GitObjectNotFound(
    m_get_repo):
    class MockProject:
        @property
        def default_branch(self):
            return 'def-branch'

        def get_branch(self, name):
            assert name == 'def-branch'
            raise GithubException(404, headers={}, data={'message': 'Branch not found'})

        def get_commit(self, sha):
            raise GithubException(422, headers={},
                                  data={'message': 'No commit found for SHA:'})

    m_get_repo.return_value = MockProject()

    with raises(GitObjectNotFound):
        GithubAPI('github.com', 'owner', 'repo')


@patch.object(Github, 'get_repo')
def test_github_api_get_repo_download(m_get_repo, example_user, github_token):
    class MockProject:
        def get_branch(self, name):
            mock = Mock()
            mock.name = name
            mock.commit.sha = 'mybranchsha'
            return mock

        def get_archive_link(self, format, ref):
            assert format == 'tarball'
            assert ref == 'mybranchsha'
            return ('https://codeload.github.com/owner/repository/'
                    'legacy.tar.gz/mybranchsha?token=generated_token')

    m_get_repo.return_value = MockProject()

    api = GithubAPI('github.com', 'owner', 'repository', 'my-branch',
                    example_user.id)

    assert api.get_repo_download() == (
        'https://codeload.github.com/owner/repository/'
        'legacy.tar.gz/mybranchsha')


@patch.object(Github, 'get_repo')
def test_github_api_get_file_download(m_get_repo):
    class MockProject:
        def get_branch(self, name):
            mock = Mock()
            mock.name = name
            mock.commit.sha = 'mybranchsha'
            return mock

        def get_file_contents(self, filepath, ref):
            assert filepath == 'README.md'
            assert ref == 'mybranchsha'
            return Mock(download_url='https://raw.githubusercontent.com/owner/'
                        'repository/mybranchsha/README.md',
                        size=21)

    m_get_repo.return_value = MockProject()

    api = GithubAPI('github.com', 'owner', 'repository', 'my-branch')

    assert api.get_file_download('README.md') == (
        'https://raw.githubusercontent.com/owner/repository'
        '/mybranchsha/README.md', 21)


@patch.object(Github, 'get_repo')
def test_github_api_get_file_download_when_file_does_not_exist_raises_GitObjectNotFound(
    m_get_repo):
    class MockProject:
        def get_branch(self, name):
            return Mock()

        def get_file_contents(self, filepath, ref):
            raise UnknownObjectException(404, headers={}, data={'message': 'Not Found'})

    m_get_repo.return_value = MockProject()

    api = GithubAPI('github.com', 'owner', 'repository', 'my-branch')

    with raises(GitObjectNotFound):
        api.get_file_download('README.md')


@patch.object(Github, 'get_repo')
def test_github_api_get_file_download_when_filepath_is_a_directory_raises_GitError(
    m_get_repo):
    class MockProject:
        def get_branch(self, name):
            return Mock()

        def get_file_contents(self, filepath, ref):
            assert filepath == 'dir'
            return [Mock(path="dir/a.txt"), Mock(path='dir/b.txt')]

    m_get_repo.return_value = MockProject()

    api = GithubAPI('github.com', 'owner', 'repository', 'my-branch')

    with raises(GitError):
        api.get_file_download('dir')


@patch('cap.modules.repos.github_api.generate_secret',
       Mock(return_value='mysecret'))
@patch.object(Github, 'get_repo')
def test_github_api_create_webhook(m_get_repo, app):
    class MockProject:
        def get_branch(self, name):
            return Mock()

        def create_hook(self, name, config, events, active):
            assert name == 'web'
            assert config == {
                'url': 'http://analysispreservation.cern.ch/api/repos/event',
                'content_type': 'json',
                'secret': 'mysecret'
            }
            assert events == ['release']
            assert active is True
            return Mock(
                url="https://api.github.com/repos/owner/repo/hooks/186091239",
                id=186091239)

    m_get_repo.return_value = MockProject()

    api = GithubAPI('github.com', 'owner', 'repository', 'my-branch')

    assert api.create_webhook() == (186091239, 'mysecret')


@patch('cap.modules.repos.github_api.generate_secret',
       Mock(return_value='mysecret'))
@patch.object(Github, 'get_repo')
def test_github_api_create_webhook_when_webhook_already_exist_raises_GitIntegrationError(
    m_get_repo, app):
    app.config['DEBUG'] = False

    class MockProject:
        def get_branch(self, name):
            return Mock()

        def create_hook(self, name, config, events, active):
            raise GithubException(
                422,
                headers={},
                data={
                    'message': 'Validation Failed',
                    'errors': [{
                        'resource': 'Hook',
                        'code': 'custom',
                        'message': 'Hook already exists on this repository'
                    }],
                })

    m_get_repo.return_value = MockProject()

    api = GithubAPI('github.com', 'owner', 'repository', 'my-branch')

    with raises(GitIntegrationError):
        api.create_webhook()


@patch('cap.modules.repos.github_api.generate_secret',
       Mock(return_value='mysecret'))
@patch.object(Github, 'get_repo')
def test_github_api_create_webhook_when_no_permissions_to_create_a_webhook_raises_GitIntegrationError(
    m_get_repo, app):
    app.config['DEBUG'] = False

    class MockProject:
        def get_branch(self, name):
            mock = Mock()
            mock.name = name
            mock.commit.sha = 'mybranchsha'
            return mock

        def create_hook(self, name, config, events, active):
            raise UnknownObjectException(404, headers={}, data={'message': 'Not Found'})

    m_get_repo.return_value = MockProject()

    api = GithubAPI('github.com', 'owner', 'repository', 'my-branch')

    with raises(GitIntegrationError):
        api.create_webhook()


@patch.object(Github, 'get_repo')
def test_github_api_delete_webhook(m_get_repo, app):
    class MockProject:
        def get_branch(self, name):
            return Mock()

        def get_hook(self, hook_id):
            assert hook_id == 12345
            return Mock(
                url="https://api.github.com/repos/owner/repo/hooks/186091239",
                id=12345,
                delete=Mock(return_value=None))

    m_get_repo.return_value = MockProject()

    api = GithubAPI('github.com', 'owner', 'repository', 'my-branch')

    api.delete_webhook(12345)


@patch.object(Github, 'get_repo')
def test_github_api_delete_webhook_when_hook_doesnt_exist_or_no_permission_raises_GitObjectNotFound(m_get_repo, app):
    class MockProject:
        def get_branch(self, name):
            return Mock()

        def get_hook(self, hook_id):
            assert hook_id == 12345
            raise UnknownObjectException(404, headers={}, data={'message': 'Not Found'})

    m_get_repo.return_value = MockProject()

    api = GithubAPI('github.com', 'owner', 'repository', 'my-branch')

    with raises(GitObjectNotFound):
        api.delete_webhook(12345)


@patch.object(Github, 'get_repo', Mock())
def test_github_api_verify_request_when_sha_and_secret_match(app):
    with app.test_request_context(
            '/',
            headers=
        {'X-Hub-Signature': 'sha1=eaa6b28f890556a3f01b3db830564fc9b641f898'},
            data='somepayloaddata'):
        api = GithubAPI('github.com', 'owner', 'repository')
        api.verify_request('mysecretsecret')


@patch.object(Github, 'get_repo', Mock())
def test_github_api_verify_request_when_sha_and_secret_dont_match_raises_GitRequestWithInvalidSignature(
    app):
    with app.test_request_context(
            '/',
            headers={'X-Hub-Signature': 'sha1=veryfakesha'},
            data='somepayloaddata'):
        api = GithubAPI('github.com', 'owner', 'repository')
        with raises(GitRequestWithInvalidSignature):
            api.verify_request('mysecretsecret')


@patch.object(Github, 'get_repo')
def test_github_api_ping_webhook(m_get_repo):
    class MockProject:
        def get_branch(self, name):
            return Mock()

        def get_hook(self, hook_id):
            assert hook_id == 123
            Mock(
                url=
                "https://api.github.com/repos/owner_name/myrepository/hooks/123",
                id=123)

    m_get_repo.return_value = MockProject()

    api = GithubAPI('github.com', 'owner', 'repository', 'my-branch')

    api.ping_webhook(123)


@patch.object(Github, 'get_repo')
def test_github_api_ping_webhook_when_hook_doesnt_exist_raises_GitObjectNotFound(
    m_get_repo):
    class MockProject:
        def get_branch(self, name):
            return Mock()

        def get_hook(self, hook_id):
            assert hook_id == 123
            raise UnknownObjectException(404, headers={}, data={'message': 'Not Found'})

    m_get_repo.return_value = MockProject()

    api = GithubAPI('github.com', 'owner', 'repository', 'my-branch')

    with raises(GitObjectNotFound):
        api.ping_webhook(123)
