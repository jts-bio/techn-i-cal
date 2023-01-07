import requests
import json


__title__  = 'YOUTUBE DOWNLOADER WITH API (RAPIDAPI)'



url = "https://t-one-youtube-converter.p.rapidapi.com/api/v1/createProcess"

querystring = {"url"                :  "https://www.youtube.com/watch?v=SsM25EBXN58&list=RDSsM25EBXN58&start_radio=1",
               "format"             :  "mp3",
               "responseFormat"     :  "json",
               "lang "              :  "en"}

headers = {
	"X-RapidAPI-Key": "ff7bbc6458msh2dec06298c7c57bp196a0djsn283e125eb894",
	"X-RapidAPI-Host": "t-one-youtube-converter.p.rapidapi.com"
}

response = requests.request("GET", url, headers=headers, params=querystring)

print(response.text)

import requests

url =  "https://www.youtube.com/watch?v=SsM25EBXN58&list=RDSsM25EBXN58&start_radio=1"

querystring = {"guid":"960616287c58ee55149626e3a84e6061","responseFormat":"json","lang":"en"}

headers = {
	"X-RapidAPI-Key": "ff7bbc6458msh2dec06298c7c57bp196a0djsn283e125eb894",
	"X-RapidAPI-Host": "t-one-youtube-converter.p.rapidapi.com"
}

response = requests.request("GET", url, headers=headers, params=querystring)

def _request(self, method, endpoint, body=None, query=None):
        url = '{}{}'.format(self._base_url, endpoint)
        response = requests.request(method, url, params=query, json=body)
        response.raise_for_status()
        return response.json()
    
with open('ex.html', 'w') as f:
    f.write(response.text)
    f.close()