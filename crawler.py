import requests
import urllib.parse
from bs4 import BeautifulSoup
import json
import re

class Crawler999:
    base_catalog_url = ""
    urls = []
    start_page, max_pages = 0, 0

    def __init__(self, url, start, max):
        self.base_catalog_url = url
        self.start_page, self.max_pages = start, max
        self.urls.clear()
    
    def normalize_chars(self, input_string, space_rep):
        translation_table = str.maketrans("ăĂțȚșȘîÎâÂ", "aAtTsSiIaA")

        normalized_string = input_string.strip()
        normalized_string = normalized_string.replace(" ", space_rep)   
        normalized_string = normalized_string.replace("   ", " ")
        normalized_string = normalized_string.replace("  ", " ")
        normalized_string = normalized_string.translate(translation_table)
        normalized_string = re.sub(r'\u00b3', '3', normalized_string)
        normalized_string = re.sub(r'\u20ac', 'e', normalized_string)
        normalized_string = normalized_string.lower()

        return normalized_string

    def scrap_urls(self, url):
        page = requests.get(url)
        soup = BeautifulSoup(page.content, "html.parser")

        # Collect all the links to the ads on the page

        items = soup.find(class_='items__list')
    
        for item in items.find_all(class_='ads-list-photo-item'):
            try:
                link = item.find('a')['href']
            except:
                continue
            
            if link.startswith('/booster'):
                continue
            else:
                self.urls.append(urllib.parse.urljoin(url, link))
    
        # Find the url of the next page

        paginator = soup.find(class_='paginator')
        ul = paginator.find('ul')
    
        current = int(ul.find(class_='current').text)
        
        next = 0
        for li in ul.find_all('li'):
            if int(li.find('a').text) > current:
                next = int(li.find('a').text)
                break
            
        self.max_pages -= 1
    
        if next != 0 and self.max_pages > 0:
            self.scrap_urls(self.base_catalog_url+"?page="+str(next))
        else:
            return
    
    def scrap_parameters(self, url):
        print(url)

        car = {}
        page = requests.get(url)
        soup = BeautifulSoup(page.content, "html.parser")

        # Save id

        id_str = ""
        for i in reversed(range(0, len(url)-1)):
            if url[i] == '/':
                id_str = url[i+1:]
                break

        car['offer_id'] = id_str

        # Save price

        car['price'] = self.normalize_chars(soup.find(class_='adPage__content__price-feature__prices__price__value').text, ' ')

        currency = ""

        try:
            currency = self.normalize_chars(soup.find(class_='adPage__content__price-feature__prices__price__currency').text, ' ')
        except:
            pass

        car['price'] += currency

        # Save region

        car['region'] = ""

        region_elements = soup.find(class_='adPage__content__region')
        for dd in region_elements.find_all('dd'):
            car['region'] += dd.text

        car['region'] = self.normalize_chars(car['region'], ' ')

        # Save features per groups

        features = soup.find(class_='adPage__content__features')

        for col in features.find_all(class_='adPage__content__features__col'):
            uls = col.find_all('ul')
            h2s = col.find_all('h2')

            for i in range(len(uls)):
                # Value - array
                if self.normalize_chars(h2s[i].text, "") in ["securitate", "confort"]:
                    properties = []

                    for li in uls[i].find_all('li'):
                        span_element = li.find('span')
                        properties.append(self.normalize_chars(span_element.text, " "))

                    car[self.normalize_chars(h2s[i].text, "_")] = properties
                # Value - dictionary
                else:
                    properties = {}

                    for li in uls[i].find_all('li'):
                        span_elements = li.find_all('span')

                        value = ""
                        try:
                            value = span_elements[1].find('a').text
                        except:
                            value = span_elements[1].text
                    
                        key = span_elements[0].text

                        properties[self.normalize_chars(key, '_')] = self.normalize_chars(value, ' ')

                    car[self.normalize_chars(h2s[i].text, "_")] = properties

        return car
    
    def scrap_all_ads(self):
        cars = []

        for url in self.urls:
            cars.append(self.scrap_parameters(url))

        dict_field_format = {}
        dict_field_format['cars'] = cars

        return dict_field_format


crawler = Crawler999("https://999.md/ro/list/transport/cars", 2, 1)
crawler.scrap_urls(crawler.base_catalog_url+"?page="+str(crawler.start_page))

with open("cars.json", "w") as json_file:
    json.dump(crawler.scrap_all_ads(), json_file, indent=4)
