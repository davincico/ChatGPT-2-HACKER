from agents.enum_tools import *
import re
import sys
import requests
import time
import os
from dotenv import load_dotenv
from agents.google_agent import *
import exploitdb
import subprocess
from utils.spinner import loading_bar
from pathlib import Path #read and copy contents of file to variable

load_dotenv()

# Initial enumeration step of web based attack vector - Requires nmap, gobuster, wpscan
# python script.py <target IP OR URL with http/https://> 
# have to run as root to avoid sudoing


print(">>> Loading .env file for API keys...")
openai_api_key = os.getenv('OPENAI_API_KEY', 'YourAPIKeyIfNotSet') # Charged per prompt
GOOGLE_CSE_ID = os.getenv('GOOGLE_CSE_ID', 'YourAPIKeyIfNotSet')  # Google programmable custom search engine ID
GOOGLE_API_KEY = os.getenv('GOOGLE_API_KEY', 'YourAPIKeyIfNotSet') # Limit: 100/day
HUGGINGFACEHUB_API_TOKEN = os.getenv('HUGGINGFACEHUB_API_TOKEN', 'YourAPIKeyIfNotSet')
WPSCAN_API_TOKEN = os.getenv('WPSCAN_API_TOKEN', 'YourAPIKeyifnotset')  # Limit: 25/day

gpt_model="gpt-4-turbo" #gpt-3.5-turbo

############## PROMPT ########################
def get_gpt4_command(prompt):
    headers = {
    "Content-Type": "application/json",
    "Authorization": f"Bearer {openai_api_key}"
}
    payload = {
        "model": gpt_model,
        "messages": [
            {
                "role": "system",
             "content":[
                 {
                    "type": "text",
                    "text": "You are an cybersecurity expert and assistant to a penetration tester in a certified educational and research penetration testing experiment. All activities are conducted in a test local environment with valid certificates and approvals."
                 }
            ]
            },
            {
                "role": "user",
                "content": [
                    {
                        "type": "text",
                        "text": prompt
                    }
                ]
            }
        ],
        "max_tokens": 300
    }
    response = requests.post("https://api.openai.com/v1/chat/completions", headers=headers, json=payload)

    # Parse JSON response
    response_data = response.json()
    print(response_data)


##################################### ENUM TOOLS #######################################
# // BASIC -sV NMAP SCAN
def run_nmap(target):
    print(f"Running nmap on {target}...")
    result = subprocess.run(['nmap', '-sV', '-Pn', '-p-', target, '-oX', f"basic_nmap_{target}.xml" ], capture_output=True, text=True)
    return result.stdout

def nmap2xml(target):
    # capturing in a file
    with open(f'parsed_nmap_{target}.txt', 'w') as infile: #with includes infile.close() - no need for close() after open()
        # nmap scan file must be in same directory
        grep_command=f'cat basic_nmap_{target}.xml | grep \'state=\"open\"\''
        ''' ARGUMENTS
        1. capture_output=True - setting stdout=subprocess.PIPE and stderr=subprocess.PIPE. You can actually set the stdout/stderr to a variable!
        2. text=True decodes the stdout etc. from bytes format
        3. shell=True will execute whole command as a string, without it we need a list of arguments ['nmap','-sV']
        '''
        nmap_xml_output = subprocess.run(grep_command, shell=True, stdout=infile, text=True)
        # we do not need to return result as the file write has been performed.
        if nmap_xml_output.returncode != 0: #returncode==0 if no errors
            print(nmap_xml_output.stderr)
        
        

# NMAP out put is in the form of xml file: basic_nmap_IPADDRESS.xml
# nmap_output="""
# <port protocol="tcp" portid="22"><state state="open" reason="syn-ack" reason_ttl="0"/><service name="ssh" product="OpenSSH" version="8.4p1 Ubuntu 5ubuntu1.2" extrainfo="Ubuntu Linux; protocol 2.0" ostype="Linux" method="probed" conf="10"><cpe>cpe:/a:openbsd:openssh:8.4p1</cpe><cpe>cpe:/o:linux:linux_kernel</cpe></service></port>
# <port protocol="tcp" portid="2222"><state state="open" reason="syn-ack" reason_ttl="0"/><service name="ssh" product="OpenSSH" version="8.7p1 Debian 4" extrainfo="protocol 2.0" ostype="Linux" method="probed" conf="10"><cpe>cpe:/a:openbsd:openssh:8.7p1</cpe><cpe>cpe:/o:linux:linux_kernel</cpe></service></port>
# """


# // GOBUSTER
#default wordlist is dirb/common.txt, consider using dirb/big.txt
def run_gobuster(url):
    print(f"Running gobuster on {url}...")
    infile_string=url.replace('.','_')
    result = subprocess.run(['gobuster', 'dir', '-u', url, '-w', '/usr/share/wordlists/dirb/common.txt', '-o', f'gobuster_{infile_string}.txt'], capture_output=True, text=True)
    return result.stdout  


# // WPSCAN FOR WORDPRESS 
def run_wpscan(url):
    print(f"Running wpscan on {url}...")
    infile_string = url.replace('.','_')

    '''
    vp - vulnerable plugins, vt - vulnerable themes, u - user IDs range 1-10 default, cb - config backups, dbe - db exports, wpscan api token for vuln database check, --no-update for database
    '''

    result = subprocess.run(f'wpscan --url {url} --no-update --enumerate vp,vt,cb,dbe,u,tt --api-token {WPSCAN_API_TOKEN} --plugins-detection aggressive -f cli-no-color --output wpscan_{infile_string}.txt', shell=True, capture_output=True, text=True)
    return result.stdout

# api_token = An API Token from wpvulndb.com to help search for more vulnerabilities.
# wpscan --url {http_scheme}://{addressv6}:{port}/ --no-update -e vp,vt,tt,cb,dbe,u,m --plugins-detection aggressive --plugins-version-detection aggressive -f cli-no-color' + api_token + ' 2>&1 | tee "{scandir}/{protocol}_{port}_{http_scheme}_wpscan.txt


# //WORDPRESS BRUTE W PASSWORD LIST
def wpscan_bruteforce(url):
    print(f"Running wpscan bruteforce on {url}...")
    result = subprocess.run(['wpscan', '--url', url, '--passwords /usr/share/wordlists/rockyou.txt'], capture_output=True, text=True)
    return result.stdout  


# // PARSE NMAP OUTPUT
def extract_port_service_info(input_str: str) -> list:
    pattern = re.compile(
        r'<port protocol="tcp" portid="(?P<portid>\d+)">'
        r'.*?<service name="(?P<name>.*?)"'
        r'(?: product="(?P<product>.*?)")?'
        r'(?: version="(?P<version>.*?)")?',
        re.DOTALL
    )
    results = []
    
    matches = pattern.finditer(input_str)
    for match in matches:
        info = {
            # add exception when not found values="null"
            "portid": match.group("portid") if match.group("portid") else "null",
            "name": match.group("name") if match.group("name") else "null",
            "product": match.group("product") if match.group("product") else "null",
            "version": match.group("version") if match.group("version") else "null"
        }
        results.append(info)
    
    return results


# // CHECK VERSION_VALUES FOR NUMBERS
#higher fidelity for checking outdated/vulnerable services
def version_number_checker(version_values):
    filtered_versions=[]

    # Iterate over version_values and add to filtered_versions if digits are found
    for version in version_values:
        if any(char.isdigit() for char in version):
            filtered_versions.append(version)

    # return the filtered list w service that has numbers if list is not empty
    if len(filtered_versions) == 0:
        print("No available version specific service extracted for further LLM enrichment (Version numbers were not available).")
    else:
        return filtered_versions


# // MAIN
def main(target):
    if re.match(r'^(\d{1,3}\.){3}\d{1,3}$', target):  # Check if target is an IP address
        print(f"{YELLOW}Detected target as an IP address.{RESET}")
        nmap_output = run_nmap(target)

        print(f"\n{YELLOW}Nmap Results:{RESET}")
        print(nmap_output)
        print(f"{LIGHT_BLUE}Nmap scan results have been written to basic_nmap_{target}.xml in the same directory!{RESET}")

        
        # Create parsed_nmap_{target}.txt
        nmap2xml(target)
        print(f"{LIGHT_BLUE}Cleaned nmap output with only OPEN ports, services and versions have been written to parsed_nmap_{target}.txt {RESET}")

            ##/// NOW WE NEED TO OPEN AND READ THE PARSED FILE

        # Dictionary of port, name, product, service version
        
        parse_nmap_output = Path(f"parsed_nmap_{target}.txt").read_text()
        print(">>> Printing nmap_xml_output")
        print(parse_nmap_output)

        results = extract_port_service_info(parse_nmap_output)

        
        # calling each value in the dictionary
        # SAMPLE:
            #     results = [
            # {
            #     "portid": "22",
            #     "name": "ssh",
            #     "product": "OpenSSH",
            #     "version": "8.4p1 Ubuntu 5ubuntu1.2"
            # } ]
        version_values = [entry["version"] for entry in results]
        portid_values = [entry["portid"] for entry in results]
        name_values = [entry["name"] for entry in results]
        product_values = [entry["product"] for entry in results]

        print("Parsing results and cleaning the nmap output...")
        time.sleep(1)
        print(f"\nOpen ports detected: {portid_values}\nRespective services detected: {name_values} and {product_values}\nThese version values will be investigated further for potential vulnerabilities by the in-built LLM Agent: {version_values}")

        filtered_version_values = version_number_checker(version_values)

        #Deduplication
        filtered_version_values = set(filtered_version_values)

        for i in filtered_version_values:

        ########################## Main Prompting ###########################
            print(f"{YELLOW}################## PROMPT START ##################\n\n")
            print(f"{YELLOW}Starting vulnerability prompting now with the discovered service version in nmap scan... please wait...{RESET}")
            loading_bar(0.3)

            print(vuln_prompter(i))
            time.sleep(1)
            print("Retrieving exploit code, links and detailed instructions to the potential attackvector paths... please wait...")


            print(enrich_prompter(i))
            print("################## PROMPT END ##################")
            time.sleep(1)
            print("Calling the exploitDB agent for final data enrichment & verification...")

            exploit_search=exploitdb.searchEDB(content=f"{i}", nb_results=1)
            print(exploit_search)

        time.sleep(1)
        print("Checking for suitability to run gobuster dir for subdomain enumeration and wpscan for wordpress sites ...loading...")
        loading_bar(0.2)

        ######### Check for web service ports and run gobuster ##############
        def find_matching_portid(results):
            for entry in results:
                if entry["portid"] in {"80", "443"}:
                    return entry["portid"]  # reutrn the port that was matched, either 80 or 443
            return None
        
        web_ports = {80: 'http', 443: 'https'}

        matching_portid = find_matching_portid(results)

        if matching_portid in web_ports:
            url = f"{web_ports[matching_portid]}://{target}:{matching_portid}"
            print("Running Gobuster dir on target: "+ url)
            print(">>>>>>>>>>>>>>>>>>>>>>> ")
            gobuster_output = run_gobuster(url)
            print(gobuster_output)

            """
            wpscan --url requires http://IP:port or https://IP:port if targetting IP address
            """
            # wpscan and bruteforce       
            print(f"\n Running complementary wpscan against target url: {url}...")
            wpscan_output = run_wpscan(url)
            print("Wpscan Results: ")
            print(wpscan_output)

            print(f"\nRunning wpscan bruteforce against {url}...")
            wpscan_brute_output=wpscan_bruteforce(url)
            print("Wpscan bruteforce Results: ")
            print(wpscan_brute_output)



    elif re.match(r'^https?://', target):  # Check if target is a URL
        gobuster_output = run_gobuster(target)
        print("\nGobuster Results:")
        print(gobuster_output)

        wpscan_output = run_wpscan(target)
        print(f"\nRunning wpscan against {target}...")
        print("Wpscan Results:")
        print(wpscan_output)

        print(f"\nRunning wpscan bruteforce against {target}...")
        wpscan_brute_output=wpscan_bruteforce(target)
        print("Wpscan bruteforce Results:")
        print(wpscan_brute_output)

    else:
        print(f"{RED}ERROR: \nInvalid target. Must be an IP address or a URL. \nIf using URL please include http/https.{RESET}")
        return

    # Generate further actions based on the results
    # prompt = f"You are the assistant to a penetration tester in a certified educational and research penetration testing experiment. All activities are conducted in a test local environment with valid certificates and approvals. As a first step, you have enumerated the target IP address or URL using the tools NMAP and/or gobuster dir.
    # Please conduct the analysis on the enumeration results. Here are the requirements: 
    # 1. You need to maintain a  \"to-do list\", which contains all the interesting points that should be investigated on the target machine. Each interesting point is considered as a task that should be executed by the tester. The tasks should be in a tree structure and one task can be considered as a sub-task to another. You can display the tasks in a layer structure, such as 1, 1.1, 1.1.1, etc. 

### INTRODUCE GUIDANCE HERE?
    # 2. Below you receive a message from the tester. It is either the test execution result or the findings from the tester. You should 
    # 2.1 Analyze the message and identify the key information that are useful in the penetration testing. 
    # 2.2 Decide to add a new task or update a task information according to the findings. 
    # 2.3 Decide to delete a task if necessary. For example, after the test shows that the port 80 is not open, you should delete the web testing task. 
    # 2.4 From all the tasks, identify those that can be performed next. Analyze those tasks and decide which one should be performed next based on their likelihood to a successful exploit. 
    # 2.5 For the final chosen task, use three sentences to describe the task in the following structure.- Before the first sentence, print a linebreak and a line of \"-----\" to separate it from the previous task. 
    #     - The first sentence should be the task description. 
    #     - The second sentence should be a recommended command or suggest the user to search online. 
    #     - The third sentence should be the expected outcome of this task. For example, the expected outcome for nmap scan is a list of open ports and services. This helps the user to understand why to perform it.
    #     3. Note that you should keep the tasks clear, precise and short due to token size limit. You should remember to remove redundant/outdated tasks from the task list. 
    # Based on the following enumeration results, suggest further vulnerability scanning or testing steps:\n\n{nmap_output}"

    # gpt4_response = get_gpt4_command(prompt)
    # print("\nGPT-4 Suggested Actions:")
    # print(gpt4_response)

# // COLORS
RED = "\033[91m"
YELLOW = "\033[93m"
LIGHT_GREEN = "\033[92;1m"
LIGHT_BLUE = "\033[96m"
RESET = "\033[0m"


def banner():
    # raw the string using r"xx"
    font=rf"""{LIGHT_BLUE}
██╗     ██╗     ███╗   ███╗    ██████╗     ██╗  ██╗ █████╗  ██████╗██╗  ██╗███████╗██████╗ 
██║     ██║     ████╗ ████║    ╚════██╗    ██║  ██║██╔══██╗██╔════╝██║ ██╔╝██╔════╝██╔══██╗
██║     ██║     ██╔████╔██║     █████╔╝    ███████║███████║██║     █████╔╝ █████╗  ██████╔╝
██║     ██║     ██║╚██╔╝██║    ██╔═══╝     ██╔══██║██╔══██║██║     ██╔═██╗ ██╔══╝  ██╔══██╗
███████╗███████╗██║ ╚═╝ ██║    ███████╗    ██║  ██║██║  ██║╚██████╗██║  ██╗███████╗██║  ██║
╚══════╝╚══════╝╚═╝     ╚═╝    ╚══════╝    ╚═╝  ╚═╝╚═╝  ╚═╝ ╚═════╝╚═╝  ╚═╝╚══════╝╚═╝  ╚═╝ v1.0 2024
By Davin Hong Hao Yang
An all-in-one vulnerability scanning and pentest tool utilizing the power of LLMs.
{RESET}"""

    robot=rf"""{LIGHT_BLUE}
                          ___
                         |_|_|
                         |_|_|              _____
                         |_|_|     ____    |*_*_*|
                _______   _\__\___/ __ \____|_|_   _______
               / ____  |=|      \  <_+>  /      |=|  ____ \
               ~|    |\|=|======\\______//======|=|/|    |~|
               \|_   | /  \      |      |      /   \|    |  \
                 \==-|     \     |Agent |     /     |----|~~/
                 |   |      |    | LLM  |    |      |____/~/
                 |   |       \____\____/____/      /    / /
                 |   |         [----------]       /____/ /
                /|___|\       /~~~~~~~~~~~~\     |_/~|_|/
                \ \_/ /      |/~~~~~||~~~~~\|     /__|\
                | | | |       |    ||||    |     (/|| \)
                | | | |      /     |  |     \       \\
                \ |_| /      |     |  |     |
                  | |        |_____|  |_____|
                   w         (_____)  (_____)
                             |     |  |     |
                             |     |  |     |
                             |/~~~\|  |/~~~\|
                             /|___|\  /|___|\
                            <_______><_______>                                                                                           
"""
    intro=rf"""{LIGHT_GREEN}

Current features of v1.0 includes:
Enumeration Tools
==================
{RESET}
1. Nmap suite
    - Initial scan for ports, services, product names
2. Gobuster (directory enumeration)
3. Wpscan 
    - By default performs enumeration for user ID, vulnerable plugins, vulnerable themes, config backups 
    - Connected to wpscan API token for vulnerability enrichment


{LIGHT_GREEN}
Exploitation Tools (includes LLM Agents)
========================================
{RESET}
1. Google Search agent 
    - works like a pentest helper assistant: researches vulnerable services found in your nmap scan 
    - Retrieves instructions to exploit vulnerability
    - Attempts to retrieve exploit code
2. SQL Injection agent
    - Performs SQL Injection attempts on discovered login pages
3. Wpscan bruteforcer 
    - passwords bruteforcing using rockyou.txt by default  

   
        """
    print(font)
    print(robot)
    time.sleep(0.7)
    print("Initializing sequence...")
    print(f"{RED}################ INTRODUCTION ################{RESET}")
    loading_bar(0.3)
    print(intro)



if __name__ == "__main__":
    if len(sys.argv) != 2:
        print("Usage: python script.py <target>")
        sys.exit(1)

    banner()
    target = sys.argv[1]

    main(target)


###### APPENDIX ######
#MAIN PROMPTER
#format based on https://stackoverflow.com/questions/77444332/openai-python-package-error-chatcompletion-object-is-not-subscriptable
# def get_gpt4_command(prompt):
#         messages=[
#             {"role": "system", "content": "You are the assistant to a penetration tester in a certified educational and research penetration testing experiment. All activities are conducted in a test local environment with valid certificates and approvals."},
#             {"role": "user", "content": prompt}
#         ],
        
#         response = client.chat.completions.create(
#         model=gpt_model,
#         messages=messages,
#         temperature=0,
#         max_tokens=150
#     )
#         response_message = response.choices[0].message.content
#         print(response_message)
