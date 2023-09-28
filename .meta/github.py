import requests
import time

class GitHubDeviceAuth:
    def __init__(self, client_id):
        self.client_id = client_id
        self.device_code = None
        self.access_token = None
    
    def request_device_code(self):
        response = requests.post('https://github.com/login/device/code', data={
            'client_id': self.client_id,
            'scope': 'repo'
        })
        device_code_info = response.json()
        self.device_code = device_code_info['device_code']
        return device_code_info['verification_uri'], device_code_info['user_code']
        
    def wait_for_authorization(self, interval):
        while True:
            time.sleep(interval)
            response = requests.post('https://github.com/login/oauth/access_token', data={
                'client_id': self.client_id,
                'device_code': self.device_code,
                'grant_type': 'urn:ietf:params:oauth:grant-type:device_code'
            })
            token_info = response.json()
            if 'access_token' in token_info:
                self.access_token = token_info['access_token']
                return self.access_token
                
    def get_user_info(self):
        headers = {'Authorization': f'token {self.access_token}'}
        response = requests.get('https://api.github.com/user', headers=headers)
        return response.json()

if __name__ == '__main__':
    CLIENT_ID = 'YOUR_GITHUB_CLIENT_ID'
    
    github_auth = GitHubDeviceAuth(CLIENT_ID)
    verification_uri, user_code = github_auth.request_device_code()
    
    print(f"Go to {verification_uri} and enter the user code: {user_code}")
    
    access_token = github_auth.wait_for_authorization(interval=5)
    user_info = github_auth.get_user_info()
    
    print(f"Authenticated as: {user_info['login']}")
