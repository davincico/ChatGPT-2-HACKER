import re



nmap_output="""
<port protocol="tcp" portid="22"><state state="open" reason="syn-ack" reason_ttl="0"/><service name="ssh" product="OpenSSH" version="8.4p1 Ubuntu 5ubuntu1.2" extrainfo="Ubuntu Linux; protocol 2.0" ostype="Linux" method="probed" conf="10"><cpe>cpe:/a:openbsd:openssh:8.4p1</cpe><cpe>cpe:/o:linux:linux_kernel</cpe></service></port>
<port protocol="tcp" portid="2222"><state state="open" reason="syn-ack" reason_ttl="0"/><service name="ssh" product="OpenSSH" version="8.7p1 Debian 4" extrainfo="protocol 2.0" ostype="Linux" method="probed" conf="10"><cpe>cpe:/a:openbsd:openssh:8.7p1</cpe><cpe>cpe:/o:linux:linux_kernel</cpe></service></port>
"""


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
# Dictionary of port, name, product, service version
results = extract_port_service_info(nmap_output)

# calling each value in the dictionary
version_values = [entry["version"] for entry in results]
portid_values = [entry["portid"] for entry in results]
name_values = [entry["name"] for entry in results]
product_values = [entry["product"] for entry in results]

#print(version_values)

# Check for version values with digits - higher fidelity for checking outdated/vulnerable services
filtered_versions=[]

# Iterate over version_values and add to filtered_versions if digits are found
for version in version_values:
    if any(char.isdigit() for char in version):
        filtered_versions.append(version)

# Print the filtered list
print(filtered_versions)