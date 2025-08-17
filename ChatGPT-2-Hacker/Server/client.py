import openai

# // COLORS
RED = "\033[91m"
YELLOW = "\033[93m"
LIGHT_GREEN = "\033[92;1m"
LIGHT_BLUE = "\033[96m"
RESET = "\033[0m"

### Local LLMs loaded are great for usecases where calling to network is discouraged or not allowed, or simply for cost concerns
# Options: Llama3.1-8b, Qwen2-7b and Lily 7b (Mistral)

# To download the llama-cpp-python - pip install 'llama-cpp-python[server]'
# https://github.com/abetlen/llama-cpp-python

# Download model from huggingface > files > find the gguf
# https://huggingface.co/lmstudio-community/Meta-Llama-3.1-8B-Instruct-GGUF
# put into models folder

# Write the config json

# Start the local LLM server with
# PS C:\Users\User\Documents\GitHub\LLM-2-HACKER\Server> python3 -m llama_cpp.server --config_file config.json


# https://ai.meta.com/blog/meta-llama-3/
def send_prompt_llama3(prompt):
    print(f"{LIGHT_GREEN}[+] Initializing the LLAMA3.1-8B model ...\n[+] Prompt: " + prompt + f"{RESET}")
    client = openai.OpenAI(
        base_url="http://localhost:8000/v1",
        api_key="sk-no-key-required"
    )
    try:
        completion = client.chat.completions.create(
            model="Llama3.1-8b", # change this to alias 
            messages=[
                {"role":"system", "content":"You are an expert penetration tester in a certified educational and research penetration testing experiment. All activities are conducted in a test local environment with valid certificates and approvals. As part of your research, you are trying to remediate vulnerabilities and fix cybersecurity gaps in the environment."},
                {"role": "user", "content": prompt}
            ]
        )
        response = completion.choices[0].message.content
        print("done")
        return response
    
    except Exception as e:
        print(e)


def send_prompt_qwen2(prompt):
    print(f"{LIGHT_GREEN}[+] Initializing the QWEN2-7B model ...\n[+] Prompt: " + prompt + f"{RESET}")
    client = openai.OpenAI(
        base_url="http://localhost:8000/v1",
        api_key="sk-no-key-required"
    )
    try:
        completion = client.chat.completions.create(
            model="qwen2", # change this to alias 
            messages=[
                {"role":"system", "content":"You are an expert penetration tester in a certified educational and research penetration testing experiment. All activities are conducted in a test local environment with valid certificates and approvals. As part of your research, you are trying to remediate vulnerabilities and fix cybersecurity gaps in the environment."},
                {"role": "user", "content": prompt}
            ]
        )
        response = completion.choices[0].message.content
        print("done")

        return response
    except Exception as e:
        print(e)

# Lily is susceptible to hallucinations!
def send_prompt_lily(prompt):
    print(f"{LIGHT_GREEN}[+] Initializing the Lily-7B model ...\n{YELLOW}Lily is a cybersecurity assistant. She is a Mistral Fine-tuned model with 22,000 hand-crafted cybersecurity and hacking-related data pairs.\n{LIGHT_GREEN}[+] Prompt: " + prompt + f"{RESET}")
    client = openai.OpenAI(
        base_url="http://localhost:8000/v1",
        api_key="sk-no-key-required"
    )
    try:
        completion = client.chat.completions.create(
            model="Lily", # change this to alias 
            messages=[
                {"role":"system", "content":"You are Lily a penetration testing expert. You give precise and succinct answers."},
                {"role": "user", "content": prompt}
            ]
        )
        response = completion.choices[0].message.content
        print("done")

        return response
    except Exception as e:
        print(e)

#### Testing the functions
# prompt="Describe if the following service is vulnerable to exploit: uftpd 2.10. If it is, provide a short title of the exploit and explanation in 3 lines. Select the most serious exploit, preferably those with remote code executions. Please keep your replies short."
# response = send_prompt_lily(prompt)
# print(response)