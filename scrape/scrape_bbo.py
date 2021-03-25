import time
from pprint import pprint

from seleniumrequests import Chrome
from selenium.webdriver.chrome.options import Options

chrome_options = Options()
chrome_options.add_experimental_option("detach", True)

target_suffix = "/myhands/hands.php?tourney=54173-1611629131-&username=granola357"
bbo_password = open('../bbo_password.txt', 'r').read()
print(bbo_password)

login_data = {
    't': target_suffix,
    'count': '1',
    'username': 'Forrest_',
    'password': bbo_password,
    'submit': 'Login',
    'keep': 'on'
}

#driver_options = Options()
#driver_options.add_argument()
driver = Chrome()
response = driver.request('POST',
                          'https://www.bridgebase.com/myhands/myhands_login.php?t=%2Fmyhands%2Fhands.php%3Ftourney%3D54173-1611629131-%26username%3Dgranola357',
                          data=login_data)
print(response.status_code)
pprint(response.content)
print(response.cookies)
print(driver.get_cookies())

#tournament_response = driver.request('GET', 'http://www.google.com')

tournament_response = driver.request('GET', 'https://www.bridgebase.com/myhands/hands.php?tourney=54173-1611629131-&username=granola357&from_login=1')
pprint(tournament_response.content)

time.sleep(20)

'''
with requests.session() as session:
    login_response = session.post('https://www.bridgebase.com/myhands/myhands_login.php?t=%2Fmyhands%2Fhands.php%3Ftourney%3D54173-1611629131-%26username%3Dgranola357', data=login_data)
    print(login_response.status_code)
    print(login_response.content)
    print(session.cookies)
    tournament_response = session.get('https://www.bridgebase.com/myhands/hands.php?tourney=54173-1611629131-&username=granola357&from_login=1')
    pprint(tournament_response.content)
    
target_url = "https://www.bridgebase.com/myhands/hands.php?tourney=54173-1611629131-&username=granola357&from_login=0"

cookies = {"myhands_token": "forrest_|f99043d980d4afcfdea5cd72cf5a6641dbc6662c",
           "bbo_major_version": "3",
           "PHPSESSID": "o25u6hu0ucht2ol6c5hu0m2j3m",
           "session_id": "e32be3eb3df3ff20215f2dcda8e4b188",
           "itemMarking_forums_items": "eJwtyLENXDAgCATAXagpfAg8uJpxd030ylvi0VkyEc1iV6RKEr_ilrNVCsPsVYJm2AdnPQwq",
           "GIBRESTSRV": "gibrestwv3"

           }

response = requests.get(target_url, cookies=cookies)
pprint(response.content)
'''
