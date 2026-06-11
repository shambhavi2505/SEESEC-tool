import requests

url = "https://idfyblogs.idfy.com/api/posts?page=1&limit=12&where[_status][equals]=published&sort=-publishedAt"

response = requests.get(url)

data = response.json()

first_article = data["docs"][0]

print(first_article["title"])
print(first_article["slug"])
print(first_article["publishedAt"])
print(first_article["content"].keys())
print(type(first_article["content"]["root"]))