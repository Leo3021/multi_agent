import requests

def chatgpt_response(text, model='gpt-4o-2024-08-06'):
    ###
    api_key = "sk-ej4gQvkMNQJ1hZH99619B0FfF6E1448eBe558e3c1b2c82Eb"
    proxy_api_url = "https://api.holdai.top/v1/chat/completions"
    headers = {
        'Content-Type': 'application/json',
        'Authorization': f'Bearer {api_key}',
    }
    data = {
        'model': model,
        'messages': [{
            'role': 'system',
            'content': ''},
            {
                'role': 'user',
                'content': text
            }]
    }
    try:
        response = requests.post(proxy_api_url, headers=headers, json=data).json()
        return response['choices'][0]['message']['content']
    except requests.exceptions.RequestException as e:
        # 捕获任何网络请求中的错误
        print(f"Request failed: {e}")
        return "Error: Request failed due to a network issue."

if __name__ == "__main__":
    print(chatgpt_response("hello"))