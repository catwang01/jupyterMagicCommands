import functools
import logging
import os
from typing import Optional
from urllib.parse import quote

from requests import Session
from retrying import retry

LOGGER = logging.getLogger(__name__)

class JupyterClient:

    base_url: str
    _sess: Optional[Session]
    password: str
    logger: logging.Logger

    def __init__(self, base_url: str, password: str, logger: Optional[logging.Logger]=None) -> None:
        self.base_url = base_url
        self.password = password
        self._sess = None
        self.logger = logger or LOGGER

    @property
    def sess(self):
        if self._sess is None:
            self._sess = self._login_jupyter_server(self.password)
        return self._sess

    def _login_jupyter_server(self, password: str) -> Session:
        sess = Session()
        sess.request = functools.partial(sess.request, timeout=10)
        login_url = f"{self.base_url.rstrip('/')}/login"
        resp = sess.get(login_url)
        assert resp.status_code == 200, f"Authentication failed with status_code {resp.status_code}"
        xsrf_cookie = resp.cookies['_xsrf']
        params = { '_xsrf': xsrf_cookie,
            'password': password
        }
        r = sess.post(login_url, data=params)
        assert r.status_code == 200, f"Authentication failed with status_code {r.status_code}"
        sess.headers["X-XSRFToken"] = xsrf_cookie
        return sess

    def create_notebook(self, notebook_path: str, content: Optional[str]=None, file_path: Optional[str]=None) -> None:
        if content is None and file_path is None:
            raise Exception("You need to")
        elif content is not None and file_path is not None:
            raise Exception("You need to")
        elif file_path is not None:
            with open(file_path, 'r', encoding='utf8') as f:
                content = f.read()
        data = {
            'type': 'file',
            'format': 'text',
            'content': content
        }
        url = f"{self.base_url.rstrip('/')}/api/contents/{quote(notebook_path)}"
        r = self.sess.put(url, json=data)
        if not r.ok:
            raise Exception(f"Request faile with {r.status_code}. Error message {r.text}")

    def download_notebook(self, notebook_path: str, output_folder: str='.') -> None:
        params = {"type": "file", "content": 1}
        url = f"{self.base_url.rstrip('/')}/api/contents/{quote(notebook_path)}"
        r = self.sess.get(url, params=params)
        if not r.ok:
            raise Exception(f"Request failed with {r.status_code}. Error message {r.text}")

        save_path = os.path.join(output_folder, notebook_path)
        save_dir = os.path.dirname(save_path)
        if not os.path.exists(save_dir):
            os.makedirs(save_dir)

        with open(save_path, 'w', encoding='utf8') as f:
            f.write(r.json()['content'])

    def create_directory(self, directory_path: str) -> None:
        data = {"type": "directory"}
        url = f"{self.base_url.rstrip('/')}/api/contents/{quote(directory_path.strip('/'))}"
        r = self.sess.put(url, json=data)
        if not r.ok:
            raise Exception(f"Request failed with {r.status_code}. Error message {r.text}")

    def create_directory_recursive(self, directory_path: str) -> None:
        parts = directory_path.strip('/').split('/')
        create_path_retried_version = retry(stop_max_attempt_number=3)(self.create_directory)
        for i in range(len(parts)):
            current_path = "/".join(parts[:i+1])
            create_path_retried_version(current_path)

    def get_notebook_content(self, path: str, include_content: bool=False) -> dict:
        url = f"{self.base_url.rstrip('/')}/api/contents/{quote(path.strip('/'))}"
        queryParams = {
            'content': int(include_content)
        }
        # append queryParams
        r = self.sess.get(url, params=queryParams)
        if not r.ok:
            raise Exception(f"Request failed with {r.status_code}. Error message {r.text}")
        notebook_json = r.json()
        return notebook_json.get('content', {})

    def get_session(self, session_id: str) -> dict:
        url = f"{self.base_url.rstrip('/')}/api/sessions/{session_id}"
        r = self.sess.get(url)
        if not r.ok:
            raise Exception(f"Request failed with {r.status_code}. Error message {r.text}")
        return r.json()

    def get_sessions(self) -> dict:
        url = f"{self.base_url.rstrip('/')}/api/sessions"
        r = self.sess.get(url)
        if not r.ok:
            raise Exception(f"Request failed with {r.status_code}. Error message {r.text}")
        return r.json()