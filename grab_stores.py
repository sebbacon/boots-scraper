import requests

cookies = {
    "_ga": "GA1.1.453840848.1707040973",
    "_ga_D849FHQPDQ": "GS1.1.1707219294.2.1.1707219394.0.0.0",
}

headers = {
    "authority": "pharmacystockchecker.com",
    "accept": "*/*",
    "accept-language": "en-GB,en-US;q=0.9,en;q=0.8",
    # Already added when you pass json=
    # 'content-type': 'application/json',
    # 'cookie': '_ga=GA1.1.453840848.1707040973; _ga_D849FHQPDQ=GS1.1.1707219294.2.1.1707219394.0.0.0',
    "origin": "https://pharmacystockchecker.com",
    "referer": "https://pharmacystockchecker.com/",
    "sec-ch-ua": '"Not_A Brand";v="8", "Chromium";v="120"',
    "sec-ch-ua-mobile": "?0",
    "sec-ch-ua-platform": '"Linux"',
    "sec-fetch-dest": "empty",
    "sec-fetch-mode": "cors",
    "sec-fetch-site": "same-origin",
    "user-agent": "Mozilla/5.0 (X11; Linux x86_64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36",
}

json_data = "26"

response = requests.post(
    "https://pharmacystockchecker.com/GetAllStockForItem",
    cookies=cookies,
    headers=headers,
    json=json_data,
)

with open("outputs/stores.json", "w") as f:
    f.write(response.text)
