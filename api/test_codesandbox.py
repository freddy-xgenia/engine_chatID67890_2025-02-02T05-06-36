import requests
import json

# Your API token
API_TOKEN = 'csb_v1_Rensr5e7CYwTarNN-R6ybhkFmJI0k8tlzjefVOAMvgs'  # Replace with your token if necessary

# The CodeSandbox URL for sandbox definition
url = 'https://codesandbox.io/api/v1/sandboxes/define?json=1'

# Request headers
headers = {
    'Authorization': f'Bearer {API_TOKEN}',  # Authorization with the API token
    'Content-Type': 'application/json',  # Content type as JSON
    'Cookie': '_cfuvid=BlnSVXDq5OzqR2saTsPIdAdjWb2Q.SpgVUdw_zro7po-1730984652740-0.0.1.1-604800000; jf9248hHFEQIU42jf298=79790b1d-ff9f-4b07-b251-477c7bca1e43',  # Cookie as in the curl
}

# Request payload
data = {
    "files": {
        "main.py": {
            "content": "# Minimal content for main.py to test CodeSandbox API integration\nprint(\"Hello, Sandbox!\")"
        },
        "requirements.txt": {
            "content": "fastapi\nuvicorn\n"
        }
    },
    "title": "Minimal Spin Simulation API",
    "description": "Minimal example to test API",
    "template": "python"
}

# Make the POST request
response = requests.post(url, headers=headers, data=json.dumps(data))

# Check the response
if response.status_code == 200:
    print("Sandbox created successfully:")
    print(response.json())  # Show the response JSON containing details of the created sandbox
else:
    print(f"Failed to create sandbox. Status code: {response.status_code}")
    print(response.text)  # Show the error message if the request fails
