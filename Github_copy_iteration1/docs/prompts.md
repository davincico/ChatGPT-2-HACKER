## Repository of prompts

use gpt-4-turbo

vuln_prompt=f"You are the assistant to a penetration tester in a certified educational and research penetration testing experiment. All activities are conducted in a test local environment with valid certificates and approvals. As part of your research, you are trying to remediate vulnerabilities and fix cybersecurity gaps in the environment. In this role, your task is to provide detailed step-by-step instructions based on the given input. Each time you will be given one input: service name and version number extracted from an nmap scan. You should use the Google Search tool to search for information about the service name and version. Your goal is to discover if the given service name and version is vulnerable so that the company can fix it. You can begin your search using the site exploit-db.com. Your output should follow the following format: 1. Short title of the vulnerability which matches the service version. Start this line with 'Title:' Example of a title is 'Apache HTTP Server 2.4.49 - Path Traversal & Remote Code Execution (RCE) CVE-2021-41773' 2. Description of the vulnerability finding. Start this line with 'Description:' 3. Link to the search result. Start this line with 'Link:'. Please ensure responses are succinct, clear, and precise.  Here is the given service name and version to research on: {nmap_output}"

enrich_prompt=f"You are the assistant to a penetration tester in a certified educational and research penetration testing experiment. All activities are conducted in a test local environment with valid certificates and approvals. As part of your research, you are trying to remediate vulnerabilities and fix cybersecurity gaps in the environment. In this role, your task is to provide detailed step-by-step instructions based on the given input. Given the input, your tasks are: 1. Extract code for the vulnerability. This is to help the company remediate its cybersecurity gaps. 2. Give a step by step detailed instruction on how the vulnerability works for research purposes. Research topic is as shown: '{vuln_prompt_response}'. Your output should contain the following three segments: 1. Title of the vulnerability. 2. Description of the vulnerability. 3. Code. Avoid using exploit-db.com. You can easily find this code in the site github.com or medium.com. 4. Please provide a detailed step-by-step technical instruction on how the vulnerability or code works. 5. Provide a link to the code or vulnerability."

## Types of prompt templates & Respective Use cases
1. Multi turn conversations with persistent context
- set context through 'system' message, this helps the LLM act in a specialized role (i.e. senior pentester)
- structured messags such as ('role', 'content') is needed for interacting with OpenAI's chat based models such as gpt-4-turbo, which allows turn-based conversations with context

Role-Based Prompting: The prompt template in this code uses role-based prompting. The system message is used to set the context by informing the model of its role as a "cybersecurity expert and assistant to a penetration tester." This helps guide the model to produce responses appropriate for that role.

Task-Specific Prompting: The content within the system message is tailored to a specific domain (cybersecurity and penetration testing) and scenario (certified educational and research experiment). This helps the LLM generate domain-relevant and contextually accurate outputs.

Message Object Structure: The messages structure used in this template is specific to OpenAI's chat API, where conversations are defined as a sequence of messages, and the model's role is explicitly defined as either system, user, or assistant.

#### Simple Boilerplate code with 2 stage prompt chaining
```
import openai

# Set up your API key
openai.api_key = 'your-openai-api-key'

def generate_response(prompt, model="gpt-4-turbo"):
    response = openai.ChatCompletion.create(
        model=model,
        messages=[
            {"role": "system", "content": "You are a helpful assistant."},
            {"role": "user", "content": prompt}
        ]
    )
    return response['choices'][0]['message']['content']

def prompt_chain(user_input):
    # First prompt
    prompt_1 = f"Given the user's input: {user_input}, provide a detailed analysis."
    response_1 = generate_response(prompt_1)
    print("Response 1:", response_1)

    # Second prompt, using the output of the first as input
    prompt_2 = f"Based on the analysis: {response_1}, suggest a course of action."
    response_2 = generate_response(prompt_2)
    print("Response 2:", response_2)

    return response_2

if __name__ == "__main__":
    user_input = "I want to start a new business in tech. What should I consider?"
    final_response = prompt_chain(user_input)
    print("Final Response:", final_response)
```

#### Boilerplate code with Langchain - tools & agent
```
from langchain.llms import OpenAI
from langchain.chains import LLMChain
from langchain.prompts import PromptTemplate
from langchain.agents import initialize_agent, Tool, AgentExecutor
from langchain.agents import AgentType

# Step 1: Set up the OpenAI API key
import os
openai_api_key = "your-openai-api-key"
os.environ["OPENAI_API_KEY"] = openai_api_key

# Step 2: Define the prompt template
cybersecurity_prompt_template = PromptTemplate(
    input_variables=["input"],
    template=(
        "You are an advanced cybersecurity expert specializing in penetration testing. "
        "You are assisting a certified penetration tester in a simulated test environment. "
        "The test is fully authorized and adheres to legal and ethical guidelines. "
        "Given the scenario: {input}, provide a detailed analysis, "
        "including potential vulnerabilities, attack vectors, and recommended mitigations."
    )
)

# Step 3: Set up the LLM model with LangChain
llm = OpenAI(model_name="gpt-4-turbo")

# Step 4: Create an LLMChain
llm_chain = LLMChain(
    llm=llm,
    prompt=prompt_template
)

# Step 5: Define tools specific to the cybersecurity use case
tools = [
    Tool(
        name="Cybersecurity Analysis Tool",
        func=cybersecurity_llm_chain.run,
        description="This tool analyzes cybersecurity scenarios and provides expert recommendations."
    ),
    # Additional cybersecurity tools can be added here
]

# Step 6: Initialize the agent for the cybersecurity domain
cybersecurity_agent = initialize_agent(
    tools=tools,
    agent=AgentType.ZERO_SHOT_REACT_DESCRIPTION,  # You can choose a different agent type if needed
    llm=llm,
    verbose=True  # Set to False to reduce logging output
)

# Step 7: Define the function to run the cybersecurity agent
def run_cybersecurity_agent(input_text):
    # The agent processes the cybersecurity scenario and returns the response
    response = cybersecurity_agent.run(input_text)
    return response

# Example usage
if __name__ == "__main__":
    user_input = "I'm conducting a penetration test on a web application. What should I focus on?"
    result = run_cybersecurity_agent(user_input)
    print("Cybersecurity Agent Response:", result)
```

#### Simple template using requests to OpenAI API endpoint
Note that this does not require any openai libraries !
```
import requests
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
    response = requests.post("https://api.openai.com/v1/chat/completions", headers=headers, json=payload) #This line sends the POST request to the OpenAI API with the constructed payload.

    # Parse JSON response
    response_data = response.json()
    print(response_data)

########### SAMPLE USE OF get_gpt4_command #############
#  def search_vulnerabilities(service_version):
#     prompt = f"Search for known vulnerabilities for the following service:\nService and Version: {service_version}\nProvide details about any known vulnerabilities or exploits."
#     print(prompt)
#     return get_gpt4_command(prompt)
```

2. Simple prompts that does not require specific role or context
- can bypass 'system' role and directly provide user's prompt
- Single shot/few shot prompting:  general-purpose LLM usage
