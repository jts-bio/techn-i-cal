
import requests
import json



def get_database (database_id: str) -> dict:
    
    url = "https://api.notion.com/v1/databases/" + database_id 
    headers = dict(
        accept=         "application/json",
        notionVersion=  "2022-06-28"
    )
    response = requests.get(url, headers=headers)
    
    return json.loads(response.content)