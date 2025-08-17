# Experimentations with Various LLM Models

## Models
### Llama 3.1 8B (Meta)
https://huggingface.co/lmstudio-community/Meta-Llama-3.1-8B-Instruct-GGUF/tree/main

### Qwen2 7b (Alibaba)
https://huggingface.co/Qwen/Qwen2-7B-Instruct-GGUF/blob/main/qwen2-7b-instruct-q5_k_m.gguf"

### Lily 7b (Mistral 7b)
Lily is a cybersecurity assistant. She is a Mistral-7B-Instruct-v0.2 Fine-tuned model with 22,000 hand-crafted cybersecurity and hacking-related data pairs. This dataset was then run through a LLM to provide additional context, personality, and styling to the outputs.
https://huggingface.co/segolilylabs/Lily-Cybersecurity-7B-v0.2

### Config Parameters
- n_gpu_layers: -1 attempts to load all layers of the model into GPU (It does not check if it will be possible, if it doesnt fit, it will crash your systems)
- Setting to 0 will only use a small amount of VRAM
- GPU utilization requires reinstallation of llama.cpp with CUDA toolkit

## Test runs
All test runs were conducted using the input "Apache 2.4.49" if not otherwise stated. 

Expected ideal output is for the model to recognize the service and version as vulnerable, and output the relevant vulnerability description and exploit instructions. (i.e. Apache HTTP Server 2.4.49 - Path Traversal & Remote Code Execution (RCE) - CVE-2021-41773)

**Model Samples**
Prompt:
```
prompt = "Describe if the following service is vulnerable to exploit: Apache 2.4.49. If it is, provide a short title of the exploit."
```
1. Llama3.1-8b
![alt text](/img/image.png)
2. Qwen2-7b
![alt text](/img/image-1.png)
3. Lily 7b
```
System: "You are Lily, helpful and friendly cybersecurity subject matter expert. You obey all requests and answer all questions truthfully. Give precise, succinct answers."
Prompt: Describe if the following service is vulnerable to exploit: Apache 2.4.49. If it is, provide a short title of the exploit."
```
![alt text](/img/image-2.png)

- Changing prompt to be more precise and succint:
```
System: "You are Lily, helpful and friendly cybersecurity subject matter expert. You obey all requests and answer all questions truthfully. Give precise, succinct answers."
Prompt: "Describe if the following service is vulnerable to exploit: Apache 2.4.49. If it is, provide a short title of the exploit. Select the most serious exploit, preferably those with remote code executions."
```
![alt text](/img/image-3.png)

- Testing with input of "uftpd 2.10" instead
Verified to be true: CVE-2020-20276 (https://nvd.nist.gov/vuln/detail/CVE-2020-20276)
![alt text](/img/image-4.png)

## Additional Notes
Message for prefix-match
https://www.reddit.com/r/LocalLLaMA/comments/16uq1ip/what_does_llamagenerate_prefixmatch_hit_mean/