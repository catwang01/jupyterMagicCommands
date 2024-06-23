import os
from typing import List, Optional, TypedDict

from IPython import get_ipython
from IPython.core.magic_arguments import argument, magic_arguments, parse_argstring

from jupyterMagicCommands.utils.log import getLogger
from jupyterMagicCommands.utils.parser import parse_logLevel

global_logger = getLogger(__name__)

class ConversationReturn(TypedDict):
    role: str
    content: str


history: List[ConversationReturn] = []

@magic_arguments()
@argument("--logLevel", type=parse_logLevel, default="ERROR")
def openai(line, cell):
    args = parse_argstring(openai, line)
    global_logger.setLevel(args.logLevel)
    user_input = cell.strip()
    backend_name = os.getenv("AI_BACKEND", "AzureOpenAI")
    backend: Backend = BackendFactory().get_backend(backend_name)
    output = backend.conversation(user_input)
    get_ipython().set_next_input(output)

class Backend:
    def conversation(self, user_input: str) -> str: ...


def retrieve_required_environment_variable(
    env_var_name: str, default_value: Optional[str] = None
) -> str:
    env_var = os.getenv(env_var_name)
    if env_var is None:
        if default_value is None:
            raise Exception(f"Environment variable {env_var_name} is not set")
        else:
            return default_value
    return env_var


class BackendFactory:

    def get_backend(self, backend_name: str) -> Backend:
        if backend_name == "OpenAI":
            openai_key = retrieve_required_environment_variable("OPENAI_API_KEY")
            model = "gpt-3.5-turbo"
            return OpenAIBackend(openai_key, model)
        elif backend_name == "AzureOpenAI":
            endpoint = retrieve_required_environment_variable("AZURE_OPENAI_ENDPOINT")
            azure_openai_key = retrieve_required_environment_variable(
                "AZURE_OPENAI_API_KEY"
            )
            deployment_name = retrieve_required_environment_variable(
                "AZURE_OPENAI_DEPLOYMENT_NAME"
            )
            return AzureOpenAIBackend(endpoint, azure_openai_key, deployment_name)
        else:
            raise Exception("Invalid backend name")


class OpenAIBackend(Backend):
    def __init__(self, openai_key: str, model: str):
        from openai import OpenAI
        self.openai_key = openai_key
        self.model = model
        self.client = OpenAI()

    def conversation(self, user_input: str) -> str:
        history.append({"role": "system", "content": user_input})
        response = self.client.chat.completions.create(
            model=self.model,
            messages=history,
            max_tokens=1024,
            n=1,
            stop=None,
            temperature=0,
        )
        output = response.choices[0].message.content
        history.append({"role": "bot", "content": output})
        return output


class AzureOpenAIBackend(Backend):

    def __init__(
        self,
        endpoint: str,
        azure_openai_key: str,
        deployment_name: str,
        api_version: str = "2024-02-01",
    ):
        from openai import AzureOpenAI
        self.deployment_name = deployment_name
        self.client = AzureOpenAI(
            api_version=api_version,
            api_key=azure_openai_key,
            azure_endpoint=endpoint
        )

    def conversation(self, user_input: str) -> str:
        history.append({"role": "system", "content": user_input})
        global_logger.info(f"Adding one user message to the history, the current history len is {len(history)}")
        try:
            response = self.client.chat.completions.create(
                model=self.deployment_name,
                messages=history,
                max_tokens=1024,
                n=1,
                stop=None,
                temperature=0,
            )
            output = response.choices[0].message.content
        except Exception as e:
            # remove the last system message if the request fails
            history.pop()
            return str(e)
        else:
            history.append({"role": "assistant", "content": output})
            global_logger.info(f"Adding one assistant message to the history, the current history len is {len(history)}")
        return output

def load_ipython_extension(ipython):
    ipython.register_magic_function(openai, "cell")