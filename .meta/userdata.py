import requests
import time
import pyperclip

from pydantic import BaseModel
from typing import Optional
from ui import ui


class LimitedGitHubUser(BaseModel):
    id: int
    login: str
    url: str
    repos_url: str

    type: str
    name: Optional[str] = None
    email: Optional[str] = None
    public_repos: int = 0
    private_repos: int = 0

    class Config:
        extra = "ignore"


class LimitedGitHubRepo(BaseModel):
    id: int
    name: str
    full_name: str
    private: bool
    owner: LimitedGitHubUser
    html_url: str
    description: Optional[str]
    fork: bool
    url: str
    forks_url: str
    permissions: dict

    class Config:
        extra = "ignore"


class Project(BaseModel):
    package_name: str
    distribution_name: str
    author: str
    email: str

    class Config:
        extra = "ignore"


class PlaceholderData(BaseModel):
    user: LimitedGitHubUser
    repo: LimitedGitHubRepo
    project: Project
    choices: Optional[dict]
    
    date = {
        "formatted": time.strftime("%Y-%m-%d"),
        "year": time.localtime().tm_year,
        "month": time.localtime().tm_mon,
        "day": time.localtime().tm_mday,
    }

    class Config:
        extra = "ignore"


class GitHubDeviceAuth:
    def __init__(self, client_id):
        self.client_id = client_id
        self.device_code = None
        self.access_token = None

    def request_device_code(self):
        response = requests.post(
            "https://github.com/login/device/code",
            data={"client_id": self.client_id, "scope": "user, repo"},
            headers={"Accept": "application/json"},
        )
        device_code_info = response.json()
        self.device_code = device_code_info["device_code"]
        return device_code_info["verification_uri"], device_code_info["user_code"]

    def wait_for_authorization(self, interval=5):
        while True:
            time.sleep(interval)
            response = requests.post(
                "https://github.com/login/oauth/access_token",
                data={
                    "client_id": self.client_id,
                    "device_code": self.device_code,
                    "grant_type": "urn:ietf:params:oauth:grant-type:device_code",
                },
                headers={"Accept": "application/json"},
            )
            token_info = response.json()
            if "access_token" in token_info:
                self.access_token = token_info["access_token"]
                self.headers = {
                    "Authorization": f"token {self.access_token}",
                    "Accept": "application/json",
                }
                return self.access_token

    def authorize(self):
        if not self.device_code:
            self.request_device_code()
        if not self.access_token:
            self.wait_for_authorization()

    def get_user_info(self):
        self.authorize()
        user_response = requests.get(
            "https://api.github.com/user", headers=self.headers
        )

        user = user_response.json()

        self.user = LimitedGitHubUser(**user)
        return self.user

    def getRepositories(self):
        self.authorize()
        if not self.user:
            self.get_user_info()
        public_repos_response = requests.get(
            self.user.repos_url, headers=self.headers, params={"type": "public"}
        )
        private_repos_response = requests.get(
            "https://api.github.com/user/repos",
            headers=self.headers,
            params={"type": "private"},
        )
        public_repos = public_repos_response.json()
        private_repos = private_repos_response.json()
        self.repos = [
            LimitedGitHubRepo(**repo) for repo in public_repos + private_repos
        ]
        return self.repos

    def getWriteRepositories(self):
        self.authorize()
        repos = self.getRepositories()
        write_repos = [repo for repo in repos if repo.permissions["admin"]]
        return write_repos

    def getEmails(self):
        response = requests.get(
            "https://api.github.com/user/emails", headers=self.headers
        )

        if response.status_code == 200:
            emails = response.json()
            return [
                email["email"]
                for email in emails
                if not "@users.noreply.github.com" in email["email"]
            ]
        else:
            return None


class Github:
    def __init__(self, client_id):
        self.client_id = client_id
        self.device_code = None
        self.access_token = None
        self.github = GitHubDeviceAuth(client_id)

    def authorize(self):
        verification_uri, user_code = self.github.request_device_code()
        ui.prompt(f"Please got to: {verification_uri} \nand enter the code: {user_code}", "Copy Code")
        # copy the code to the user's clipboard
        pyperclip.copy(user_code)
        
        self.github.wait_for_authorization()

    def load_user_info(self):
        self.user = self.github.get_user_info()
        self.write_repos = self.github.getWriteRepositories()
        self.emails = self.github.getEmails()

    def prompt_app_install(self):
        tries = 0
        installation_url = "https://github.com/apps/py-lib-template"
        while tries < 3:
            if self.user and self.write_repos and self.emails:
                return True
            else:
                input(
                    f"Please install the app from {installation_url} and press enter to continue"
                )
                self.load_user_info()
                tries += 1
        return False

    def choose_repo(self):
        add_repositories_url = "https://github.com/settings/installations"
        options = [repo.full_name for repo in self.write_repos] + ["Not listed"]
        selected_name = ui.single_select(
            "Choose a repo to configure the template for", options
        )
        selected_repo = [
            repo for repo in self.write_repos if repo.full_name == selected_name
        ]
        if selected_name == "Not listed":
            ui.prompt(
                "Add the repo in question to the app at "
                + add_repositories_url
                + " and save the changes.",
                "I'm done",
            )
            self.load_user_info()
            return self.choose_repo()
        self.repo = selected_repo[0]
        return self.repo

    def choose_email(self):
        options = self.emails + ["Not listed"]
        choice = ui.single_select("Choose an email to credit the app with", options)
        if choice == "Not listed":
            return ui.input("Enter a custom email")
        return choice

    def choose_author(self):
        options = [self.user.name, self.user.login, "Custom"]
        choice = ui.single_select("Choose an author name to attribute the project to", options)
        if choice == "Custom":
            return ui.input("Enter a custom author name")
        return choice

    def choose_package_name(self):
        choice = ui.input(
            "Enter the name of your package",
            default=self.repo.name.replace("-", "_").replace(" ", "_"),
        )
        return choice

    def choose_distribution_name(self):
        choice = ui.input(
            "Enter the name of your package",
            default=self.repo.name.replace(" ", "-").replace("_", "-").lower(),
        )
        return choice

    def set_repo_settings(self):
        headers = self.github.headers
        data = {
            "required_status_checks": {"strict": True, "contexts": ["tests-passed"]},
            "enforce_admins": False,
            "required_pull_request_reviews": {"required_approving_review_count": 1},
            "restrictions": {
                "users": [],  # No user restrictions
                "teams": [],  # No team restrictions
                "apps": []   # No app restrictions
            },
            "allow_force_pushes": True,  # Allow force pushes           
        }
        url = f"https://api.github.com/repos/{self.repo.full_name}/branches/master/protection"
        response = requests.put(url, headers=headers, json=data)

        if response.status_code == 200:
            return True
        else:
            raise Exception("Failed to set repo settings " + response.text)

    def get_data(self):
        self.authorize()
        self.load_user_info()
        if self.prompt_app_install():
            self.repo = self.choose_repo()
            project = Project(
                package_name=self.choose_package_name(),
                distribution_name=self.choose_distribution_name(),
                author=self.choose_author(),
                email=self.choose_email()
            )
            return PlaceholderData(
                user=self.user, repo=self.repo, project=project, choices={}
            )
        else:
            return False

