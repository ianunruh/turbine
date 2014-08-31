from paramiko.client import SSHClient, WarningPolicy
import requests

"""
Check functions should perform in the following way:

- Accept the check options as kwargs
- Return any output that may be useful to blue teams
- Raise an exception if the check should fail
"""

def check_ssh(host, username, password):
    client = SSHClient()
    client.set_missing_host_key_policy(WarningPolicy())
    client.connect(host, username=username, password=password, timeout=10)

    client.exec_command('whoami', timeout=10)

def check_http(url, matcher):
    response = requests.get(url, timeout=10)
    
def check_ftp(host, protocol, username, password):
    raise RuntimeError('Not implemented')
