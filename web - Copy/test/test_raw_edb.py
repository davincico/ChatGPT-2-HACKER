import requests
import re


input_string = "[Exploit(id='78', description='WU-FTPD 2.6.2 - Remote Command Execution', type='remote', platform='Linux', date_published='2003-08-11', verified=1, port='21', tag_if_any=[], author='Xpl017Elz', link='https://www.exploit-db.com/exploits/78')]"

# Use regex to find the id value
id = re.search(r"id='(\d+)'", input_string).group(1)

print(f"Extracted id: {id}")

raw_url = f"https://exploit-db.com/raw/{id}"
headers = {"User-Agent": "Mozilla/5.0 (Windows NT 10.0; WOW64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/109.0.0.0 Safari/537.36"} 
exploit_code = requests.get(raw_url, headers=headers)
if exploit_code.status_code == 200:
    print(exploit_code.text)
else:
    print('Failed to retrieve the webpage. Status code:', exploit_code.status_code)