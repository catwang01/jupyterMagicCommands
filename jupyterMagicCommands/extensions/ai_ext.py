from IPython.core.magic import register_cell_magic
from IPython import get_ipython 
import os

def openai_magic(line, cell):
    import openai

    openai.api_key = os.getenv("OPENAI_API_KEY")
    if openai.api_key is None:
        print("Using maigc ai requires to provide openai api key by setting environment varaible OPENAI_API_KEY")
        return
    
    prompt = cell.strip()
  
    model = "gpt-3.5-turbo"
    response = openai.ChatCompletion.create(
        model=model,
        messages=[{ "role": "system", "content": prompt }],
        max_tokens=1024,
        n=1,
        stop=None,
        temperature=0,
    )
    output = response.choices[0].message.content
    get_ipython().set_next_input(output)

def load_ipython_extension(ipython):
    ipython.register_magic_function(openai_magic, 'cell')