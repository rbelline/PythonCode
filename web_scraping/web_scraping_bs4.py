from bs4 import BeautifulSoup
import html5lib
import requests
import pandas as pd

#get html text data
wikipedia_url = "https://web.archive.org/web/20200318083015/https://en.wikipedia.org/wiki/List_of_largest_banks"
response = requests.get(wikipedia_url)
html_data = response.text
print(html_data)

html_data[760:783]

#Replace the dots below
soup= BeautifulSoup(html_data, 'html.parser')

#create a empty data frame with this structure
data = pd.DataFrame(columns=["Name", "Market Cap (US$ Billion)"])
data_frames = []

for row in soup.find_all('tbody')[2].find_all('tr'):
    col = row.find_all('td')
    if col:
        bank_name = col[1].text.strip()
        Market_cap = col[2].text.strip()
        data_frames.append(pd.DataFrame({"Name":[bank_name], "Market Cap (US$ Billion)": [Market_cap]}))

#populate the data frame
data = pd.concat(data_frames, ignore_index=True)

print(data)

#Write your code here
data.head(n=5)

#Write your code here
json_data = data.to_json(orient='records')

json_file_path = 'bank_market_cap.json'

# Save the JSON data to a file
with open(json_file_path, 'w') as json_file:
    json_file.write(json_data)

print("DataFrame saved as JSON successfully.")

