from io import StringIO
from IPython.core.magic import register_cell_magic
import requests
import pandas as pd

@register_cell_magic
def ck(line, cell):

    sio = StringIO(cell)
    query = sio.read()

    def queryClickHousePlayGround(query):
        query = query + "FORMAT JSON\n"
        data = {
            'query':  query,
            'user': 'explorer',
            'password': '',
        }
        r = requests.get("https://play.clickhouse.com:443", params=data)
        df = None
        if r.ok:
            df = pd.DataFrame(r.json()['data'])
        else:
            print("Bad Request: {}".format(r.text))
        return df
    return queryClickHousePlayGround(query)

def load_ipython_extension(ipython):
    ipython.register_magic_function(ck, 'cell')