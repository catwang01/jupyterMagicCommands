import os
from typing import Dict, List, Optional, TypedDict, Protocol

from IPython import get_ipython
from IPython.core.magic_arguments import argument, magic_arguments, parse_argstring

from jupyterMagicCommands.utils.jupyterNotebookRetriever import JupyterNotebookRetriever
from jupyterMagicCommands.utils.jupyter_client import JupyterClient
from jupyterMagicCommands.utils.log import getLogger
from jupyterMagicCommands.utils.parser import parse_logLevel

global_logger = getLogger(__name__)

class ConversationReturn(TypedDict):
    role: str
    content: str


history: List[ConversationReturn] = []

cachedBackend: Dict[str, 'Backend']  = {}


@magic_arguments()
@argument("--logLevel", type=parse_logLevel, default="ERROR")
@argument("--type", type=str, default=None, choices=["note"], help="Specify type of the cell")
def openai(line, cell):
    ipython = get_ipython()
    args = parse_argstring(openai, line)
    global_logger.setLevel(args.logLevel)
    user_input = cell.strip()
    backend_name = os.getenv("AI_BACKEND", "AzureOpenAI")
    if args.type not in cachedBackend:
        backend: Backend = BackendFactory().get_backend(backend_name)
        cachedBackend[args.type] = backend
    replace = False
    if args.type == "note":
        jupyter_client = JupyterClient(
            base_url=os.getenv("JMC_JUPYTER_BASE_URL"),
            # base_url="http://catwang.top/jupyter",
            password=os.getenv("JMC_JUPYTER_PASSWORD"),
            logger=global_logger,
        )
        jupyterNotebookRetriever = JupyterNotebookRetriever(jupyter_client, ipython, global_logger)
        cells = jupyterNotebookRetriever.get_current_notebook_json()
        i = jupyterNotebookRetriever.get_current_cell_index()
        cells_before_current_one = cells["cells"][:i]
        user_input = "\n\n".join(["\n".join(cell["source"]) for cell in cells_before_current_one])
        if cell:
            user_input += "\n\n" + cell
        replace = True
    output = cachedBackend[args.type].conversation(user_input)
    global_logger.debug(f"User input is {user_input}")
    ipython.set_next_input(output, replace=replace)

class Backend(Protocol):
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
    ipython.register_magic_function(openai, "line_cell")