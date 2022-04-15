import argparse
import requests
import pandas as pd
from io import StringIO
from IPython.display import Pretty
from IPython.core.magic import register_cell_magic

@register_cell_magic
def ck(line, cell):

    parser = getParser()
    inArgs = line.strip().split(' ')
    if inArgs == ['']:
        inArgs = []
    args = parser.parse_args(inArgs)
    url = args.url

    sio = StringIO(cell)
    query = sio.read()

    ret = queryClickHousePlayGround(query, url)
    if ret.shape[0] == 1 and ret.columns[0] == 'statement':
        ret = Pretty(ret.iloc[0, 0])
    return ret

def queryClickHousePlayGround(query: str, url: str):
    data = {
        'query':  query,
        'user': 'play',
        'password': '',
        'default_format': "JSON"
    }
    r = requests.get(url, params=data)
    df = None
    if r.ok:
        df = pd.DataFrame(r.json()['data'])
        print(f"Elapsed: {r.json()['statistics']['elapsed']} sec, read {r.json()['statistics']['rows_read']} rows, {r.json()['statistics']['bytes_read']} bytes.")
    else:
        print("Bad Request: {}".format(r.text))
    return df

def load_ipython_extension(ipython):
    ipython.register_magic_function(ck, 'cell')

def parseDataset(dataset: str) -> str:
    defaultUrl = "https://play.clickhouse.com:443"
    return {
        "ontime": "https://gh-api.clickhouse.com/play"
    }.get(dataset, defaultUrl)

def getParser():
    parser = argparse.ArgumentParser()
    parser.add_argument('--dataset', dest='url', type=parseDataset, default=parseDataset('default'))
    return parser