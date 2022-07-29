import datetime
import re
import requests

def handle_scrape():
    path = 'coolcats/scrapes/'
    now = datetime.datetime.now()

    # grab the most recent state of the CC scripts
    response = requests.get("https://www.coolcatsnft.com/static/js/main.addc33d3.js")

    current_grab = f'{path}coolcats_script_{now.strftime("%m.%d.%y.%H.%M")}.txt'

    # discord active file
    f = open(current_grab, 'w')
    f.write(response.text)
    f.close()

    # return regex
    required_item_instances = [x.group() for x in re.finditer(
        r'\"requiredItems\":\[.*?]', 
        response.text
    )]

    required_item_instances = [item.replace('"requiredItems":', "").replace("[", "").replace("]", "").split(",") for item in required_item_instances]
    required_item_instances = [int(item) for sublist in required_item_instances for item in sublist]

    return [*set(required_item_instances)]