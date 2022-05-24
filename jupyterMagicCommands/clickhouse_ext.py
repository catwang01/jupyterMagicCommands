import argparse
from pprint import pprint
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

    ret = queryClickHousePlayGround(query, url, args)
    if not isinstance(ret, pd.DataFrame):
        ret = Pretty(ret)
    return ret

def queryClickHousePlayGround(query: str, url: str, args: argparse.Namespace):
    data = {
        'query':  query,
        'user': 'play',
        'password': '',
        'default_format': "JSON"
    }
    try: 
        r = requests.get(url, params=data)
    except Exception as e:
        print(e)
    if r.ok:
        ret = pd.DataFrame(r.json()['data'])
        if args.plain:
            if ret.shape != (1, 1):
                print("--plain only supports results shape = (1, 1). current shape: {}".format(ret.shape))
                sys.exit(1)
            ret = str(ret.iloc[0,0])
        print(f"Elapsed: {r.json()['statistics']['elapsed']} sec, read {r.json()['statistics']['rows_read']} rows, {r.json()['statistics']['bytes_read']} bytes.")
    else:
        print("Bad Request: {}".format(r.text))
    for k, v in r.headers.items():
        print("{}: {}".format(k, v))
    return ret

def load_ipython_extension(ipython):
    ipython.register_magic_function(ck, 'cell')

def parseDataset(dataset: str) -> str:
    defaultUrl = "https://play.clickhouse.com:443"
    return {"ontime": "https://gh-api.clickhouse.com/play"}.get(dataset, defaultUrl)

def getParser():
    parser = argparse.ArgumentParser()
    parser.add_argument('--dataset', dest='url', type=parseDataset, default=parseDataset('default'))
    parser.add_argument('--plain', action='store_true', default=False)
    return parser

load_ipython_extension(get_ipython())