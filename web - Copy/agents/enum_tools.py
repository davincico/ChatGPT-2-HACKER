import subprocess

"""
Module for Enumeration tools
"""
# basic sV nmap scan
def run_nmap(target):
    print(f"Running nmap on {target}...")
    result = subprocess.run(['nmap', '-sV', '-Pn', '-p-', target], capture_output=True, text=True)
    return result.stdout


#default wordlist is dirb/common.txt, consider using dirb/big.txt
def run_gobuster(url):
    print(f"Running gobuster on {url}...")
    result = subprocess.run(['gobuster', 'dir', '-u', url, '-w', '/usr/share/wordlists/dirb/common.txt'], capture_output=True, text=True)
    return result.stdout   

# enumerate users on wordpress
def run_wpscan(url):
    print(f"Running wpscan on {url}...")
    result = subprocess.run(['wpscan', '--url', url, '--enumerate u'], capture_output=True, text=True)
    return result.stdout

# api_token = An API Token from wpvulndb.com to help search for more vulnerabilities.
# wpscan --url {http_scheme}://{addressv6}:{port}/ --no-update -e vp,vt,tt,cb,dbe,u,m --plugins-detection aggressive --plugins-version-detection aggressive -f cli-no-color' + api_token + ' 2>&1 | tee "{scandir}/{protocol}_{port}_{http_scheme}_wpscan.txt

#wordpress bruteforce with passwords list
def wpscan_bruteforce(url):
    print(f"Running wpscan bruteforce on {url}...")
    result = subprocess.run(['wpscan', '--url', url, '--passwords /usr/share/wordlists/rockyou.txt'], capture_output=True, text=True)
    return result.stdout  