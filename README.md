# ChatGPT 2 Hacker (Automated Pentesting with GPT and other AI models)
Shield: [![CC BY-NC 4.0][cc-by-nc-shield]][cc-by-nc]

All in one vulnerability scanning and pentesting tool empowered with autonomous LLM agents - ChatGPT. Created to empower the pentesting process using ChatGPT.
Currently uses ChatGPT models gpt-4-turbo, gpt-3.5-turbo, other models pending.

- [ChatGPT 2 Hacker](#chatgpt-2-hacker)
  - [Getting Started](#getting-started)
  - [Features](#features)
    - [Integration of LLM Agents - 2 Main Usecases](#integration-of-llm-agents---2-main-usecases)
      - [1. Vulnerability Enrichment LLM Agent module](#1-vulnerability-enrichment-llm-agent-module)
      - [2. Autonomous SQL Injection Agent](#2-autonomous-sql-injection-agent)
  - [Retrieval-Augmentation Generation Engine (RAGE)](#retrieval-augmentation-generation-engine-rage)
    - [RAGE in ChatGPT2Hacker](#rage-in-chatgpt2hacker)
  - [Usage](#usage)
  - [Demonstration](#demonstration)
    - [Usecase 1 - Vulnerability Enrichment LLM Agent Module](#usecase-1---vulnerability-enrichment-llm-agent-module)
    - [Usecase 2 - Autonomous SQL Injection Agent](#usecase-2---autonomous-sql-injection-agent)
    - [Demonstration of how the LLM adapts to multiple failed SQLi attempts:](#demonstration-of-how-the-llm-adapts-to-multiple-failed-sqli-attempts)
  - [Disclaimer](#disclaimer)

**PREVIEW :**

Intro:
![alt text](/img/intro.png)

Explanatory in-built wiki:
![alt text](/img/wiki.png)


## Getting Started
ChatGPT 2 Hacker is an vulnerability scanning and enumeration tool that incorporates the use of LLM models (Large Language models like ChatGPT, Mistral, Llama) for pentesting purposes.

1. **ChatGPT 2 Hacker** is a pentesting tool powered by **ChatGPT**. It is highly flexible and allow the use of local LLM model suites as well. Simply specify desired model types in parameters when running.
2. It is designed to enhance and empower the pentesting process. At the base level, it has **built-in enumeration tools** like nmap, gobuster and wpscan.

## Features
### Integration of LLM Agents - 2 Main Usecases

#### 1. Vulnerability Enrichment LLM Agent module
On top of host and domain enumeration, users have the option to enrich scan results.
   
  In-built LLM agents will initiate prompt chains to extract exploit information, detailed instructions and exploit links.
   
   * To counteract the known limitations of LLM models being trained on datasets with cut-off training date (i.e. GPT-4-Turbo: April 2023), **ChatGPT 2 Hacker** uses LLM Agents empowered with search capabilities instead.
   * This vastly expands the available knowledge base leveraged by the LLM.
   * Functions such as Google Search API are provided to the LLM Agent which uses it in a multi-round process:

      * LLM Agent recieves user input 
      * Agent decides how to use tool and generates search query
      * Agent observed results of tool output and generates thought/future actions
      * Agent repeats attempts for desired result 
  

**Example ReAct Prompt**
```json
{                                             
    "action": "Google Search",                                                                                                                                                       "action_input": "Apache HTTP Server 2.4.49 exploit site:exploit-db.com"  
     }       

Observation: Oct 6, 2021 ... Apache HTTP Server 2.4.49 - Path Traversal & Remote Code Execution (RCE). CVE-2021-41773 . webapps exploit for Multiple platform. Nov 11, 2021 ... ... Exploit Author: Valentin Lobstein # Vendor Homepage: https://apache.org/ # Version: Apache 2.4.49/2.4.50 (CGI enabled) # Tested on: Debian ... A flaw was found in a change made to path normalization in Apache HTTP Server 2.4.49. An attacker could use a path traversal attack to map URLs to files ... Oct 13, 2021 ... Exploit: Apache HTTP Server 2.4.50 - Path Traversal & Remote Code Execution (RCE) Date: 10/05/2021 Exploit Author: Lucas Souza Oct 25, 2021 ... Apache HTTP Server 2.4.50 - Remote Code Execution (RCE) (2). CVE-2021-42013 . webapps exploit for Multiple platform. Search Exploit Database for Exploits, Papers, and Shellcode. You can ... 2021-10-06, Apache HTTP Server 2.4.49 - Path Traversal & Remote Code Execution (RCE) ... Apr 8, 2019 ... 1. Upload exploit to Apache HTTP server 2. Send request to page 3. Await 6:25AM for logrotate to restart Apache 4. python3.5 is now suid 0 Oct 6, 2014 ... ... exploit on : "+page if proxyhost != "": c = httplib.HTTPConnection(proxyhost,proxyport) c.request("GET","http://"+rhost+page,headers=headers) ... Mar 23, 2021 ... Exploit Title: Codiad 2.8.4 - Remote Code Execution (Authenticated) # Discovery by: WangYihang # Vendor Homepage: http://codiad.com/ ... Apr 4, 2003 ... Apache mod_ssl < 2.8.7 OpenSSL - 'OpenFuckV2.c' Remote Buffer Overflow (1). CVE-2002-0082CVE-857 . remote exploit for Unix platform.                                                                                                             
Thought: json
{                                                                                                                                                                                                                                           
    "action": "Final Answer",                                                                                                                                                                                                               
    "action_input": "Title: Apache HTTP Server 2.4.49 - Path Traversal & Remote Code Execution (RCE) CVE-2021-41773\nDescription: A flaw was found in the path normalization process in Apache HTTP Server 2.4.49 that allows an attacker to perform a path traversal attack, potentially leading to remote code execution.\nLink: https://www.exploit-db.com/exploits/50239"                                                                                                           
}    

```

#### 2. Autonomous SQL Injection Agent

SQL Injection Agent hunts for login forms, input fields and embed links from a user specified target and performs iterative SQLi on it. Currently only supports GPT-4-Turbo model. Testing was successful on simple login forms with static HTML, under development to include more complex web pages.

*Note: After empirical evaluation, we find that GPT-4 performs better than GPT-3.5 and other LLMs in terms of penetration testing reasoning. In fact, GPT-3.5 leads to failed test in simple tasks.*

* The agent utilizes the Playwright library to interact with the browser elements and parses HTML content of target sites
* LLM Agent injects SQL payloads into discovered login forms and determines if injection was successful from the response content.


*Further uses cases such as Linux Priv Escalation are under development, stay tuned!*


## Retrieval-Augmentation Generation Engine (RAGE)

LLM2 Hacker has an in-built retrieval augmentation generation engine that greatly strengthens the generative capabilities of LLM models.

**Improvements:**
1. LLM's pretrained data is enhanced with domain focused knowledge database 
2. Reduced hallucinations; factual grounding
3. Domain contextual relevance

RAG operates by first retrieving relevant information from a database using a query generated by the LLM. This retrieved information is then integrated into the LLM's query input, enabling it to generate more accurate and contextually relevant text. RAG leverages vector databases, which store data in a way that facilitates efficient search and retrieval.

Comprehensive Guide: https://blogs.nvidia.com/blog/what-is-retrieval-augmented-generation/

### RAGE in ChatGPT2Hacker
In ChatGPT 2 Hacker, the LLM model is supplemented with an index generated from SQL injection manuals and cheatsheets. Current the resources are hardcoded. Development works are ongoing to source for more relevant data sources.


## Usage
ChatGPT 2 Hacker is tested under `Python 3.10.` Other Python3 versions should work but are not tested.
1. To start:
   
   * (Recommended) `python3 main.py -t <target IP or URL>` or `python3 main.py --target <target IP or URL>`
2. LLM Agents
   * Specify LLM Model to use (Default gpt-4-turbo) `--model gpt-3.5-turbo`
   * Authorize vulnerability enrichment using LLM Agent `-vp` or `--vuln-prompt`
   * Authorize full multi-staged LLM Agent vulnerability discovery & enrichment on target `-fp` or `--full-prompt`
   
3. Additional features:
   * Run gobuster directory enumeration `-g` or `--gobuster`. Default wordlist used is `/usr/share/wordlists/dirb/common.txt`
   * Run wpscan for enumerating wordpress sites `-wps` or `--wpscan`.  Default mode includes scans for vulnerable plugins, vulnerable themes, user IDs range 1-10 , config backups, db exports. Wpscan API token can be loaded for vulnerability database check.
   * Activate exploitdb module for extraction of CVE Link and CVE exploit code (if available) `-e` or `--exploitdb`
4. Exploitation
   
   * Run wpscan bruteforce using password wordlist (Default wordlist: `/usr/share/wordlists/rockyou.txt`) `-wb` or `--wpbrute`. Select wordlist using `-w` or `--wordlist`
   * Authorize input fields, login page hunt and GPT4-Empowered SQLi Agent injections `-s` or `--sql-inject`
5. Retrieval Augmentation Generation (RAG) Engine
   
   * Activate Retrieval-Augmentation Generation Engine (RAGE) `-r` or `--RAGE`



## Demonstration 
### Usecase 1 - Vulnerability Enrichment LLM Agent Module
Running ChatGPT 2 Hacker on sample IP address target with `-fp` fullprompt enabled on `gpt-4-turbo`:

FULL GIF DEMO:
![alt text](/img/LLM_Vuln_agent.gif)

**The steps**
Initial nmap scan:
![alt text](/img/vuln_prompt1.png)

Sample output for vulnerability enrichment on OpenSSH 8.2p1
![alt text](/img/ssh.png)

Sample output for vulnerability enrichment on Apache 2.4.49
![alt text](/img/apache2449.png)

Verifying this by navigating to the link provided by the LLM, indeed the exploit code is readily available:
![alt text](/img/calfcrusher.png)
ChatGPT 2 Hacker successfully extracts relevant vulnerability information, steps for exploit and link to exploit code!

### Usecase 2 - Autonomous SQL Injection Agent
Using a sample sandbox locally hosted website: *localhost:3456*
We instruct ChatGPT 2 Hacker to perform successful SQL injections on the target:
![alt text](/img/finalSQL1.gif)

![alt text](/img/sql1.png)

On the DB logs we can see the attempted SQL payloads used by the LLM:
![alt text](/img/db_logs.png)

### Demonstration of how the LLM adapts to multiple failed SQLi attempts:
In this test we utilized offsec's SQL injection lab in 10.2.3
![alt text](/img/offsec_sqli.png)

## Disclaimer
This tool is for educational and testing purposes only. Do not use it to exploit the vulnerability on any system that you do not own or have permission to test. The authors of this script are not responsible for any misuse or damage caused by its use.

Shield: [![CC BY-NC 4.0][cc-by-nc-shield]][cc-by-nc]
This work is licensed under a
[Creative Commons Attribution-NonCommercial 4.0 International License][cc-by-nc].

[![CC BY-NC 4.0][cc-by-nc-image]][cc-by-nc]

[cc-by-nc]: https://creativecommons.org/licenses/by-nc/4.0/
[cc-by-nc-image]: https://licensebuttons.net/l/by-nc/4.0/88x31.png
[cc-by-nc-shield]: https://img.shields.io/badge/License-CC%20BY--NC%204.0-lightgrey.svg


