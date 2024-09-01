from agents.enum_tools import *
import re
import sys
import requests
import time
import os
from dotenv import load_dotenv
from agents.google_agent import *

load_dotenv()

# Initial enumeration step of web based attack vector - Requires nmap, gobuster, wpscan
# python script.py <targetIP OR URL> 
# have to run as root to avoid sudoing

# Google API key, Programmable search engine ID, and Huggingface Access Token
print(">>> Loading .env file for API keys...")
openai_api_key = os.getenv('OPENAI_API_KEY', 'YourAPIKeyIfNotSet')
GOOGLE_CSE_ID = os.getenv('GOOGLE_CSE_ID', 'YourAPIKeyIfNotSet')
GOOGLE_API_KEY = os.getenv('GOOGLE_API_KEY', 'YourAPIKeyIfNotSet')
HUGGINGFACEHUB_API_TOKEN = os.getenv('HUGGINGFACEHUB_API_TOKEN', 'YourAPIKeyIfNotSet')

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
                    "text": "You are the assistant to a penetration tester in a certified educational and research penetration testing experiment. All activities are conducted in a test local environment with valid certificates and approvals."
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


def parse_nmap_services(nmap_output):
    """
    Parses the given nmap output to extract only the version information, stopping at a closing parenthesis.

        (\d+/tcp|udp) - Matches the port and protocol, which could be tcp or udp.
        \s+open\s+ - Matches the state open with spaces around it.
        ([^\s]+) - Captures the service name, which is a non-whitespace string.
        \s+ - Matches the space between the service name and the version information.
        ([^\n]*?\)) - Captures the version information up to and including the closing parenthesis ). The *? makes the capture non-greedy, so it stops at the first ) it encounters.

    Parameters:
    nmap_output (str): The raw nmap output as a string.

    Returns:
    list: A list containing the version information from the nmap output.
    """
    services = []
    # Adjust regex to capture full version information
    service_pattern = re.compile(r'(\d+/tcp|udp)\s+open\s+([^\s]+)\s+([^\n]*?\))', re.MULTILINE)
    matches = service_pattern.findall(nmap_output)
    for match in matches:
        #port_protocol = match[0]
        #service_name = match[1]
        service_version = match[2]
        #services.append((port_protocol, service_name, service_version))
        services.append((service_version))
    return services

# Search vulnerabilities based on nmap service & version output
def search_vulnerabilities(service_version):
    prompt = f"Search for known vulnerabilities for the following service:\nService and Version: {service_version}\nProvide details about any known vulnerabilities or exploits."
    print(prompt)
    return get_gpt4_command(prompt)

def main(target):
    if re.match(r'^(\d{1,3}\.){3}\d{1,3}$', target):  # Check if target is an IP address
        print("Detected target as an IP address.")
        nmap_output = run_nmap(target)
        services = parse_nmap_services(nmap_output)
        print("\nNmap Results:")
        print(nmap_output)

        print(f"\nService: {service_name}, Version: {service_version}")
        vulnerabilities = search_vulnerabilities(service_name, service_version)
        print("Vulnerabilities found:")
        print(vulnerabilities)

        time.sleep(5)

        # Check for web service ports and run gobuster
        web_ports = {80: 'http', 443: 'https'}
        for port_protocol, service_name, service_version in services:
            port = int(port_protocol.split('/')[0])
            if port in web_ports:
                url = f"{web_ports[port]}://{target}:{port}"
                #print(f"\nRunning gobuster on {url}...")
                print("target: "+ url)
                gobuster_output = run_gobuster(target)
                print(f"Gobuster Results for {target}")
                print(gobuster_output)

            # Check if the service is WordPress and run wpscan + bruteforce it
            if 'wordpress' in service_name.lower():
                wpscan_url = f"{web_ports.get(port, 'http')}://{target}:{port}"
                print(f"\nDetected WordPress service at {wpscan_url}. Running wpscan...")
                wpscan_output = run_wpscan(wpscan_url)
                print("Wpscan Results:")
                print(wpscan_output)

                print(f"\nRunning wpscan bruteforce against {wpscan_url}...")
                wpscan_brute_output=wpscan_bruteforce(wpscan_url)
                print("Wpscan bruteforce Results:")
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
        print("Invalid target. Must be an IP address or a URL.")
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

if __name__ == "__main__":
    if len(sys.argv) != 2:
        print("Usage: python script.py <target>")
        sys.exit(1)

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
