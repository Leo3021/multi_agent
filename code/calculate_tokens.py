import tiktoken

def calculate_tokens(text, model="gpt-4o"):
    # enc = tiktoken.get_encoding("o200k_base")
    # assert enc.decode(enc.encode("hello world")) == "hello world"

    # To get the tokeniser corresponding to a specific model in the OpenAI API:
    enc = tiktoken.encoding_for_model(model)
    
    tokens = enc.encode(text)
    token_count = len(tokens)

    return token_count

if __name__ == "__main__":
    input_text = "Hello, how are you?"
    result = calculate_tokens(input_text)

    print(f"输入的 token 数量: {result}")

