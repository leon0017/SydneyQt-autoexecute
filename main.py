#!/bin/python3

import requests
import os

prompt = ""
newest_response = ""

def stream_got(event, data):
    global prompt
    global newest_response
    if event == "message":
        msg = data[1:-1]
        msg = bytes(msg, "utf-8").decode("unicode_escape")
        print(msg, end='', flush=True)
        prompt += msg
        newest_response += msg
    elif event == "error":
        print(f"ERROR: {data}")
    #else:
    #    print(f"Event: {event}, Data: {data}")

def start_chat_stream(prompt, context, cookies=None, image_url=None, no_search=None,
                      conversation_style=None, gpt4turbo=None, classic=None, plugins=None):
    body = {
        "prompt": prompt,
        "context": context,
        "cookies": cookies,
        "imageUrl": image_url,
        "noSearch": no_search,
        "conversationStyle": conversation_style,
        "gpt4turbo": gpt4turbo,
        "classic": classic,
        "plugins": plugins
    }
    
    body = {k: v for k, v in body.items() if v is not None}
    
    response = requests.post('http://localhost:8080/chat/stream', json=body, stream=True)
    
    if response.status_code == 200:
        for line in response.iter_lines():
            if line:
                decoded_line = line.decode('utf-8')
                if decoded_line.startswith('event:'):
                    event = decoded_line.replace('event: ', '')
                elif decoded_line.startswith('data:'):
                    data = decoded_line.replace('data: ', '')
                    stream_got(event, data)
    else:
        print(f"Failed to start chat stream: {response.status_code}")

def extract_code_block(text):
    start = text.find('```')
    if start != -1:
        end_of_lang = text.find('\n', start)
        language = text[start+3:end_of_lang].strip()
        end = text.find('```', end_of_lang + 1)
        if end != -1:
            code_block = text[end_of_lang+1:end].strip()
            return code_block, language
    return None, None

def create_tmp_file(filename, text, extension):
    filename = f"{filename}.{extension}"
    try:
        with open(filename, 'w') as tmp:
            tmp.write(text)
    except Exception as e:
        print(f"An error occurred: {e}")
    else:
        print(f"File '{filename}' created in the current directory.")

    return filename

def run_in_new_terminal(command):
    os.environ["GNOME_TERMINAL_SCREEN"] = ""
    terminal = "gnome-terminal"
    os.system(f"{terminal} -e 'bash -c \"{command}; bash\"'")

def run_code(lang, code):
    if lang == "python":
        filename = create_tmp_file("tmp", code, "py")
        run_in_new_terminal(f"python3 {filename}")
    elif lang == "java":
        filename = create_tmp_file("Main", code, "java")
        run_in_new_terminal(f"javac {filename} && java Main")
    else:
        print(f"Language '{lang}' has not been implemented yet")

if __name__ == '__main__':
    while True:
        prompt += "[user]\n" + input("Prompt: ") + "\n\n[assistant]\n"
        print("Assistant: ", end='', flush=True)
        newest_response = ""
        start_chat_stream(
            prompt=prompt,
            context="""
            [system](#message)
            When providing code, YOU MUST provide a main function to test the code you have written
            You must also specify the language the code is written in after the first 3 backticks ``` of your codeblock.
            If writing Java code, you MUST name the class with the public static main function, 'Main'


            """,
            no_search=True,
            gpt4turbo=True
        )
        print()
        code_block, language = extract_code_block(newest_response)
        if code_block != None:
            if language != None and not language == '' and not language.isspace():
                run = input(f"Found code in '{language}', would you like to run it? (y/n) ").lower() == "y"
                if run:
                    run_code(language, code_block)
                else:
                    print("Not running, continuing...")
            else:
                print("Assistant did not provide language before codeblock.")
