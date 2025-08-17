import re
import os
import sys
import time
import requests
import argparse
import subprocess
from agents.enum_tools import *
from SQLi_agent import SQLi_LLM_Agent
from utils.spinner import loading_bar
from exploitdb.exploitdb_agent import searchEDB
from agents.google_agent import vuln_prompter, enrich_prompter
from Server.client import send_prompt_llama3, send_prompt_qwen2, send_prompt_lily

try:
    import asyncio
    from dotenv import load_dotenv
    from playwright.async_api import async_playwright
    from pathlib import Path #read and copy contents of file to variable

except:
    print("[!] Missing modules! Pip install python-dotenv, playwright, pathlib, asyncio")
    sys.exit(1)

load_dotenv()
 
print(">>> Loading .env file for API keys...")
openai_api_key = os.getenv('OPENAI_API_KEY', 'YourAPIKeyIfNotSet') # Charged per prompt
GOOGLE_CSE_ID = os.getenv('GOOGLE_CSE_ID', 'YourAPIKeyIfNotSet')  # Google programmable custom search engine ID
GOOGLE_API_KEY = os.getenv('GOOGLE_API_KEY', 'YourAPIKeyIfNotSet') # Limit: 100/day
HUGGINGFACEHUB_API_TOKEN = os.getenv('HUGGINGFACEHUB_API_TOKEN', 'YourAPIKeyIfNotSet')
WPSCAN_API_TOKEN = os.getenv('WPSCAN_API_TOKEN', 'YourAPIKeyifnotset')  # Limit: 25/day

#gpt_model="gpt-4-turbo" #gpt-3.5-turbo

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
"""
add -p- for scanning of all ports
"""
def run_nmap(target):
    print(f"[*] Running nmap on {target}...")
    result = subprocess.run(['nmap', '-sV', '-Pn', target, '-oX', f"basic_nmap_{target}.xml" ], capture_output=True, text=True)
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


# // GOBUSTER
#default wordlist is dirb/common.txt, consider using dirb/big.txt
async def run_gobuster(url):
    print(f"Running gobuster on {url}...")
    result = subprocess.Popen(['gobuster', 'dir', '-u', url, '-w', '/usr/share/wordlists/dirb/common.txt', '-o', 'gobuster_scan.txt'], text=True)
    result.wait
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
def wpscan_bruteforce(url, wordlist):
    print(f"Running wpscan bruteforce on {url}...")
    result = subprocess.run(['wpscan', '--url', url, '--passwords', wordlist], capture_output=True, text=True)
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

# // extract service and versions 
def extract_service_versions(results):
    service_versions = []
    
    for entry in results:
        product = entry.get("product", "")
        version = entry.get("version", "")
        
        if product and version:
            service_version = f"{product} {version}"
            service_versions.append(service_version)
    
    return service_versions

# // CHECK VERSION_VALUES FOR NUMBERS - higher fidelity for checking outdated/vulnerable services
def version_number_checker(service_versions):
    filtered_versions=[]
    for version in service_versions:
        if any(char.isdigit() for char in version):
            filtered_versions.append(version)

    if len(filtered_versions) == 0:
        print(f"{RED}[*] No available version specific service extracted for further LLM enrichment (Version numbers were not available)!")
    else:
        # return the filtered list w service that has numbers
        return filtered_versions

# // CHECK FOR WEB PORTS OPEN
def find_matching_portid(results):
    for entry in results:
        if entry["portid"] in {"80", "443"}:
            return entry["portid"]  # reutrn the port that was matched, either 80 or 443
    return None

# // USER INPUT 
def user_confirmation(confirmation_prompt: str) -> bool:
    """Prompt the user for confirmation (Y/N).
    Prompts repeatedly until a valid input choice is entered.

    Parameters
    ----------
    prompt : str
        The message prompt.

    Returns
    -------
    bool - True if user confirms else False.
    """ 
    while True:
        user_input = input(f"{confirmation_prompt} [y/n]: ").strip().lower()
        if user_input in ('y', 'yes'):
            return True
        elif user_input in ('n', 'no'):
            return False
        else:
            print("Invalid input. Please enter only 'y/yes' or 'n/no'.")


def LLM_banner():
    print(rf"""{YELLOW}
Activating the in-built ---
  _    _    __  __  __   __    _         ___                  _        _                _   
 | |  | |  |  \/  | \ \ / /  _| |_ _ ___/ __| ___ __ _ _ _ __| |_     /_\  __ _ ___ _ _| |_ 
 | |__| |__| |\/| |  \ V / || | | ' \___\__ \/ -_) _` | '_/ _| ' \   / _ \/ _` / -_) ' \  _|
 |____|____|_|  |_|   \_/ \_,_|_|_||_|  |___/\___\__,_|_| \__|_||_| /_/ \_\__, \___|_||_\__|
                                                                          |___/             
Initializing vulnerability prompting with discovered services from Nmap scanning ...{RESET}             
                  """)
    
def EDB_banner():
    print(rf"""{LIGHT_GREEN}
  _____            _       _ _   ____  ____    ____                      _     
 | ____|_  ___ __ | | ___ (_) |_|  _ \| __ )  / ___|  ___  __ _ _ __ ___| |__  
 |  _| \ \/ / '_ \| |/ _ \| | __| | | |  _ \  \___ \ / _ \/ _` | '__/ __| '_ \ 
 | |___ >  <| |_) | | (_) | | |_| |_| | |_) |  ___) |  __/ (_| | | | (__| | | |
 |_____/_/\_\ .__/|_|\___/|_|\__|____/|____/  |____/ \___|\__,_|_|  \___|_| |_| Module
            |_|                                                                    
Intializing exploitdb search for given services ...
          {RESET}""")

async def sqli_LLM_agent(sqli_target):
    await asyncio.sleep(0.5)
            # url = "http://localhost:3456/"
    print(f"{YELLOW}[+] Initializing...{RESET}")
    sqli_LLM_Agent: SQLi_LLM_Agent = SQLi_LLM_Agent(base_url=sqli_target)
    print("[+] Setting up playwright for browser interactions...")
    async with async_playwright() as playwright:
        print("[+] Playwright starting - browser ready")
        await sqli_LLM_Agent.startup(playwright)
        print(f"{YELLOW}[+] Beginning SQL Injection rounds on target...")
        await sqli_LLM_Agent.inject()
        await asyncio.sleep(0.5)
        input(f'\n{LIGHT_GREEN}[*] Press enter to shutdown the browser !{RESET}')
        await sqli_LLM_Agent.shutDown()


# // MAIN
async def main(target):
        # target = args.target
        # sqli = args.sql_inject #True or false
        # output_file = args.original_output
        # sum_output_file = args.sum_output

    if re.match(r'^(\d{1,3}\.){3}\d{1,3}$', target):  # Check if target is an IP address
        print(f"{LIGHT_GREEN}Detected target as an IP address. Running nmap scan on all ports. {RESET}")
        nmap_output = run_nmap(target)

        print(f"\n{LIGHT_GREEN}======================================= Nmap Results: ======================================={RESET}")
        print(nmap_output)
        print(f"{LIGHT_BLUE}Nmap scan results have been written to basic_nmap_{target}.xml in the same directory!{RESET}")

        # Create parsed_nmap_{target}.txt
        nmap2xml(target)
        print(f"{LIGHT_BLUE}Cleaned nmap output with only OPEN ports, services and versions have been written to parsed_nmap_{target}.txt {RESET}")

        parse_nmap_output = Path(f"parsed_nmap_{target}.txt").read_text()
        results = extract_port_service_info(parse_nmap_output)
        
        # calling each value in the dictionary
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

        # Returns service_version = product + version
        service_versions_undup = extract_service_versions(results)

        # deduplication
        service_versions = []
        for j in service_versions_undup:
            if j not in service_versions:
                service_versions.append(j)


        print("\n\nParsing results and cleaning the nmap output...")
        time.sleep(1.5)
        # service_versions = ['OpenSSH 8.2p1 Ubuntu 4ubuntu0.4', 'Samba smbd 4.6.2', 'Apache httpd 2.4.49', 'Samba smbd 4.6.2', 'Apache httpd 2.4.49']
        print(f"{LIGHT_GREEN}>>>> Summary of Nmap scan:{RESET}\n[*] Open ports detected: {portid_values}\n[*] Service protocols detected: {name_values}\n[*] Services detected: {service_versions}\nThese version values will be investigated further for potential vulnerabilities by the in-built LLM Agent if respective arguments are set.")

        filtered_version_values = version_number_checker(service_versions)
        

        if gobusterCheck:
            print(f"{LIGHT_GREEN}[*] Approval has been given to run gobuster dir enumeration on target. Initializing ...{RESET}")
            print(f"[*] Checking for suitability to run gobuster dir for directory enumeration ...")
            loading_bar(0.2)

            ######### Check for web service ports and run gobuster ##############
            web_ports = {80: 'http', 443: 'https'}

            # FUTURE WORK: To include more web ports
            # returns the port number that matches with the nmap output: 80 or 443
            matching_portid = int(find_matching_portid(results))

            # Pre-pend either http or https accordingly
            if matching_portid in web_ports:
                url = f"{web_ports[matching_portid]}://{target}:{matching_portid}"
                print(f"{LIGHT_GREEN}[*] Running Gobuster dir on target: "+ url + f" {RESET}")
                loading_bar(0.2)
                gobuster_output = asyncio.run(run_gobuster(url))
                print(gobuster_output)


## // LLM SEGMENT
        """
        Options:
        gpt-3.5-turbo/got-4-turbo 
        1. Run vulnerability enrichment with tool calling LLM agents
        2. Run 2nd round prompt to attempt exploit code extraction and exploit instructions
        """

        if "gpt" in gpt_model: #returns boolean, checks for model option 

            if vuln_promptCheck:  
                LLM_banner()
                print(f"""{LIGHT_GREEN}This built-in LLM has been customized to be highly interactive & verbose. Actions are chained using Langchain library. Responses are structured as follows:{RESET}
                {YELLOW}[*] Agent Executor Chain initiates{RESET}
                {YELLOW}[*] Action & Action_input:{RESET} LLM understands user input & selects appropriate tool for usage
                {YELLOW}[*] Observation:{RESET} LLM Agent observes results of its actions 
                {YELLOW}[*] Thought:{RESET} LLM Agent decides how to continue based on observation
                {YELLOW}[*] Finished chain:{RESET} Results 
                    
                    """)
                if user_confirmation("\nAre you ready to continue? Press Enter."):
                    for i in filtered_version_values:   # ['OpenSSH 8.4p1 Ubuntu 5ubuntu1.2', 'Apache 2.4.49']               
                        loading_bar(0.3)
                        print(vuln_prompter(i))
                        time.sleep(2)

            if full_promptCheck:
                LLM_banner()
                print(f"""{LIGHT_GREEN}This built-in LLM has been customized to be highly interactive & verbose. Actions are chained using Langchain library. Responses are structured as follows:{RESET}
                {YELLOW}[*] Agent Executor Chain initiates{RESET}
                {YELLOW}[*] Action & Action_input:{RESET} LLM understands user input & selects appropriate tool for usage
                {YELLOW}[*] Observation:{RESET} LLM Agent observes results of its actions 
                {YELLOW}[*] Thought:{RESET} LLM Agent decides how to continue based on observation
                {YELLOW}[*] Finished chain:{RESET} Results 
                    
                You have chosen full prompt option: 2nd round will attempt to extract instructions for exploit & exploit code!
                    """)
                if user_confirmation("\nAre you ready to continue?"):
                    for i in filtered_version_values:   # ['OpenSSH 8.4p1 Ubuntu 5ubuntu1.2', 'Apache 2.4.49']               
                        loading_bar(0.3)
                        print(vuln_prompter(i))
                        time.sleep(2)

                        if user_confirmation(f"{LIGHT_GREEN}[*] Advance with stage 2 LLM enrichment prompting?{RESET} Press Enter."):
                            print(f"\n{YELLOW}[*] Starting round 2 of prompting. \n[*] Retrieving exploit code, links and detailed instructions to the potential attackvector paths...{RESET}\n")
                            loading_bar(0.3)
                            print(enrich_prompter(i))
                            time.sleep(2)
                        else:
                            print("Moving on to next detected service...")
                            continue 

        
        

###   Local LLMs options
        if "lily" in gpt_model:
            if user_confirmation("\n[*] You have chosen the Lily-Mistral-7b model. \nAre you ready to continue? Press Enter."):
                list = [] # store the results of prompts
                counter = 0 # counter for for loop
                for i in filtered_version_values:
                    prompt = f"Summarize if the following service is vulnerable to exploit: {i}. If it is, provide a short title of the exploit and explanation in 3 lines. Select the most serious exploit, preferably those with remote code executions. Please keep your replies short. If you are unable to find an exploit, just say no exploit found."
                    list.append(send_prompt_lily(prompt))
                    counter = counter + 1
                    print(f"Iteration [{counter}]")

                return list


        if "llama" in gpt_model:
            if user_confirmation("\n[*] You have chosen the Llama3.1-8b model. \nAre you ready to continue? Press Enter."):
                list = [] # store the results of prompts
                counter = 0 # counter for for loop
                for i in filtered_version_values:
                    prompt = f"Summarize if the following service is vulnerable to exploit: {i}. If it is, provide a short title of the exploit and explanation in 3 lines."
                    list.append(send_prompt_llama3(prompt))
                    counter = counter + 1
                    print(f"Iteration [{counter}]")

                return list

        if "qwen" in gpt_model:
            if user_confirmation("\n[*] You have chosen the Qwen2-7b model. \nAre you ready to continue? Press Enter."):
                list = [] # store the results of prompts
                counter = 0 # counter for for loop
                for i in filtered_version_values:
                    prompt = f"Summarize if the following service is vulnerable to exploit: {i}. If it is, provide a short title of the exploit and explanation in 3 lines."
                    list.append(send_prompt_qwen2(prompt))
                    counter = counter + 1
                    print(f"Iteration [{counter}]")

                return list

        if edb:
            EDB_banner()
            for i in filtered_version_values:
                print(f"{LIGHT_GREEN}[*] Calling the exploitDB agent for final data enrichment & verification...{RESET}")
                loading_bar(0.1)
                exploit_search=searchEDB(content=f"{i}", nb_results=1)
                print(exploit_search)
                if user_confirmation(f"{LIGHT_GREEN}[*] Would you like to grab raw exploit code?"):
                    '''
                    Function to grab raw code from hXXps://www.exploit-db.com/raw/{id}
                    '''
                    id = re.search(r"id='(\d+)'", exploit_search).group(1)
                    raw_url = f"https://exploit-db.com/raw/{id}"
                    headers = {"User-Agent": "Mozilla/5.0 (Windows NT 10.0; WOW64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/109.0.0.0 Safari/537.36"}  # headers to bypass bot blocker
                    exploit_code = requests.get(raw_url, headers=headers)
                    if exploit_code.status_code == 200:
                        print(f"{YELLOW}Exploit code successfully retrieved:\n")
                        # add capability to write to text file
            
                        data = exploit_code.text
                        file = Path(f"{id}_exploit_code.txt")
                        file.write_text(f"""Exploit code Snippet
                                        ==================================== 
                                        Service: {exploit_search}\nLink to raw code: {raw_url}\n\n\n\n""" + data)
                        print(f"{LIGHT_GREEN}[*] Exploit code has been written into {id}_exploit_code.txt{RESET}\n")
                        if user_confirmation("Would you like a preview? Press Enter."):
                            print(f"{YELLOW}==================================== CODE ====================================\n{RESET}")
                            print(data)
                        

                    else:
                        print('Failed to retrieve the webpage. Status code:', exploit_code.status_code)
                else:
                    continue


        
        if wpscanCheck:
            """
            wpscan --url requires http://IP:port or https://IP:port if targetting IP address
            """
            # wpscan and bruteforce       
            print(f"{LIGHT_GREEN}[*] Running Wordpress wpscan enumeration against target url: {url}...")
            wpscan_output = run_wpscan(url)
            print("Wpscan Results: ")
            print(wpscan_output)

        if wpbruteCheck:
            # default wordlist="/usr/share/wordlists/rockyou.txt" without flag
            if user_confirmation("Run wpscan bruteforce against target? Press Enter."):
                print(f"{LIGHT_GREEN}[*] Running Wordpress wpscan bruteforce using password list against {url} ...")
                wpscan_brute_output=wpscan_bruteforce(url, wpscan_wordlist)
                print("Wpscan bruteforce Results: ")
                print(wpscan_brute_output)
            

    elif re.match(r'^https?://', target):  # Check if target is a URL
        if gobusterCheck:
            print(f"{LIGHT_GREEN}[*] Running Gobuster dir on target: "+ target + f" {RESET}")
            gobuster_output = run_gobuster(target)
            print("\nGobuster Results:")
            print(gobuster_output)

        if wpscanCheck:
            wpscan_output = run_wpscan(target)
            print(f"{LIGHT_GREEN}[*] Running wpscan against {target}...")
            print("Wpscan Results:")
            print(wpscan_output)

        if wpbruteCheck:
            if user_confirmation("Run wpscan bruteforce against target? Press Enter."):
                print(f"{LIGHT_GREEN}[*] Running wpscan bruteforce against {target}...")
                wpscan_brute_output=wpscan_bruteforce(target)
                print("Wpscan bruteforce Results:")
                print(wpscan_brute_output)

    # goes straight to sqli without intial nmap & processing
    if sqli: 
        sqli_target =  input(f"Confirm target and press Enter. Include the http/https prefix: ") 
        #event loop starts from main hence we must await the sqli
        await sqli_LLM_agent(sqli_target)

    else:
        print(f"{RED}\n\nERROR: \nInvalid target. Must be an IP address or a URL. \nIf using URL please include http/https.{RESET}")
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
    # raw the string using r"xx" - FONT: ANSI SHADOW from https://manytools.org/hacker-tools/ascii-banner/
    font=rf"""{LIGHT_BLUE}
 ██████╗██╗  ██╗ █████╗ ████████╗ ██████╗ ██████╗ ████████╗    ██████╗     ██╗  ██╗ █████╗  ██████╗██╗  ██╗███████╗██████╗ 
██╔════╝██║  ██║██╔══██╗╚══██╔══╝██╔════╝ ██╔══██╗╚══██╔══╝    ╚════██╗    ██║  ██║██╔══██╗██╔════╝██║ ██╔╝██╔════╝██╔══██╗
██║     ███████║███████║   ██║   ██║  ███╗██████╔╝   ██║        █████╔╝    ███████║███████║██║     █████╔╝ █████╗  ██████╔╝
██║     ██╔══██║██╔══██║   ██║   ██║   ██║██╔═══╝    ██║       ██╔═══╝     ██╔══██║██╔══██║██║     ██╔═██╗ ██╔══╝  ██╔══██╗
╚██████╗██║  ██║██║  ██║   ██║   ╚██████╔╝██║        ██║       ███████╗    ██║  ██║██║  ██║╚██████╗██║  ██╗███████╗██║  ██║
 ╚═════╝╚═╝  ╚═╝╚═╝  ╚═╝   ╚═╝    ╚═════╝ ╚═╝        ╚═╝       ╚══════╝    ╚═╝  ╚═╝╚═╝  ╚═╝ ╚═════╝╚═╝  ╚═╝╚══════╝╚═╝  ╚═╝
                                                                                                                            v3.0 2024
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
               \|_   | /  \      |       |      /   \|    |  \
                 \==-|     \     | Agent |     /     |----|~~/
                 |   |      |    |  LLM  |    |      |____/~/
                 |   |       \____\_____/____/      /    / /
                 |   |         [-----------]      _/____/ /
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

Current features of v3.0 includes:
Enumeration Tools
==================
{RESET}
[1] Nmap suite
    - Initial scan for ports, services, product names
[2] Gobuster (directory enumeration)
[3] Wpscan 
    - By default performs enumeration for user ID, vulnerable plugins, vulnerable themes, config backups 
    - Connected to wpscan API token for vulnerability enrichment

{LIGHT_GREEN}
Exploitation Tools (includes LLM Agents)
========================================
{RESET}
[1] Google Search agent 
    - works like a pentest helper assistant: researches vulnerable services found in your nmap scan 
    - Retrieves instructions to exploit vulnerability
    - Attempts to retrieve exploit code
[2] SQL Injection agent
    - Performs SQL Injection attempts on discovered login pages using LLM REACT Prompting
[3] Wpscan bruteforcer 
    - passwords bruteforcing using rockyou.txt by default  

{YELLOW}
Large Language Models (Options) 
========================================{RESET}
[1] Gpt-4-turbo (OpenAI)
[2] Gpt-3.5-turbo (OpenAI)
[3] Llama3.1-8b (Meta)
[4] Qwen2-7b (Alibaba)
[5] Lily - Cybersecurity tuned Mistral-7b (Mistral AI)

        """
    print(font)
    print(robot)
    time.sleep(0.7)
    print(f"{YELLOW}[*] Initializing sequence...")
    print(f"{RED}################ INTRODUCTION ################{RESET}")
    loading_bar(0.3)
    print(intro)
    

if __name__ == "__main__":     
    parser = argparse.ArgumentParser(prog='main.py', description='An all-in-one vulnerability scanning and pentest tool utilizing the power of LLMs.',usage="%(prog)s -t target")
    group = parser.add_mutually_exclusive_group()
    parser.add_argument("-t", "--target", required=True, help="specify single IP address or URL to enumerate. URL must include http/https")
    parser.add_argument("-g", "--gobuster", required=False, help="Run gobuster dir enumeration on the URL/host", action="store_true")

    # Retrieval-Augmentation Generation (RAG)
    parser.add_argument("-r", "--RAGE", required=False, help="Activate Retrieval-Augmentation Generation Engine (RAGE)", action="store_true")

    # Model options
    parser.add_argument("--model", dest="model", required=False, help="Select Models to use: gpt-3.5-turbo, gpt-4-turbo (default), llama3.1-8b, qwen2-7b, lily", default="gpt-4-turbo", type=str)

    # Prompt levels are mutually exclusive
    group.add_argument("-vp" , "--vuln-prompt", dest="vuln_prompt", required=False, help="Run only 1st LLM vulnerability discovery & enrichment on services found in nmap scan", action="store_true")
    group.add_argument("-fp", "--full-prompt",  dest="full_prompt", required=False, help="Run full 2-staged LLM vulnerability discovery & enrichment on services found in nmap scan", action="store_true")

    parser.add_argument("-e", "--exploitdb", required=False, help="Activates exploitdb module for searching exploits", action="store_true")
    parser.add_argument("-wps", "--wpscan", required=False, help="Run Wordpress wpscan enumeration on target", action="store_true")
    parser.add_argument("-wb", "--wpbrute", required=False, help="Authorize w pscan bruteforce on target using password list", action="store_true")
    parser.add_argument("-w", "--wordlist", required=False, help="Select wordlist for passwords bruteforcing wordpress using wpscan", default="/usr/share/wordlists/rockyou.txt", type=str)

    parser.add_argument("-s", "--sql-inject",  dest="sql_inject", required=False, help="Activates SQL Injection LLM Agent for autonomous web hacking", action="store_true")

    # Collate and append to output to specified file
    parser.add_argument("-oO", "--original-output",  dest="original_output", required=False, help="File to output pentest report results")

    # output to file and ask LLM to summarize
    parser.add_argument("-oX", "--sum-output", dest="sum_output", required=False, help="Enquires LLM to summarize pentest report results")

    args = parser.parse_args()

    target = args.target
    gobusterCheck = args.gobuster
    gpt_model = args.model.lower() # lowercase all
    vuln_promptCheck = args.vuln_prompt #True or false
    full_promptCheck = args.full_prompt #True or false
    edb = args.exploitdb #True or false
    sqli = args.sql_inject #True or false
    wpscanCheck = args.wpscan
    wpbruteCheck = args.wpbrute
    output_file = args.original_output
    sum_output_file = args.sum_output
    wpscan_wordlist = args.wordlist

    rag_check = args.RAGE


    if not args.target:
        print("Error: Must specify -t target")
        sys.exit(1)

    banner()
    if user_confirmation(f"{LIGHT_GREEN}[*] Are you ready to begin?{RESET}"):
        asyncio.run(main(target))
    else:
        sys.exit(1)


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
