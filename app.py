from flask import Flask, request
from twilio.twiml.messaging_response import MessagingResponse
import configparser
import requests
import random
import boto3
from nltk.corpus import stopwords
from nltk.tokenize import word_tokenize
from PIL import ImageFont
from PIL import Image
from PIL import ImageDraw
import textwrap
import shutil
import bitly_api
from InstagramAPI import InstagramAPI
import time

app = Flask(__name__)

phone_number = "+15555555555"

class NewsBot(object):

    def __init__(self):
        config = configparser.ConfigParser()
        config.read('./config/config.ini')
        self.news_key = config['newsapi']['key']
        self.pixabay_key = config['pixabay']['key']
        # directory for photos
        self.temp_directory = 'temp-directory'
        self.bitly_user = config['bitly']['user']
        self.bitly_key = config['bitly']['key']
        self.insta_username = config['instagram']['username']
        self.insta_password = config['instagram']['password']
        self.font = config['default']['font']
        self.photo_key = config['pixabay']['key']

    def gather_data(self):
        try:
            response = requests.get(
                'https://newsapi.org/v2/everything?sources=crypto-coins-news&apiKey={}'.format(self.news_key))
            if response.ok:
                data = response.json()
                data_list = []
                for i in data['articles']:
                    news_dict = {}
                    news_dict["author"] = i["author"]
                    news_dict["title"] = i["title"]
                    news_dict["description"] = i["description"]
                    news_dict["url"] = i["url"]
                    data_list.append(news_dict)
                news_sample = random.choice(data_list)
            return news_sample
        except Exception as e:
            return {"Error": f"{e}"}

    def get_tags(self, text):
        key_words = []
        _text_words = []
        # ensure you have the correct access to sentiment analysis with aws comprehend
        _comprehend = boto3.client('comprehend', region_name='us-west-2')
        _response = _comprehend.detect_key_phrases(Text=text, LanguageCode='en')
        _cachedStopWords = set(stopwords.words("english"))
        for _ in _response['KeyPhrases']:
            if _['Score'] > .99:
                _text = _['Text']
                _word_tokens = word_tokenize(_text)
                _filtered_sentence = [w for w in _word_tokens if not w in _cachedStopWords]
                _keyword = ''.join(_filtered_sentence)
                key_words.append(_keyword)
        return key_words

    def random_photo(self):
        url_list = []
        url = f'https://pixabay.com/api/?key={self.photo_key}&q=cryptocurrency&image_type=' \
               f'photo&min_width=1080&min_height=1080'
        response = requests.get(url)
        if response.ok:
            images = response.json()
            for image in images['hits']:
                url_list.append(image['largeImageURL'])
            random_url = random.choice(url_list)
            return random_url


    def resize(self, photo):
        try:
            basewidth = 640
            picture = Image.open(photo)
            wpercent = (basewidth / float(picture.size[0]))
            hsize = int((float(picture.size[1]) * float(wpercent)))
            image = picture.resize((basewidth, hsize), Image.ANTIALIAS)
            image.save(photo)
            return photo
        except Exception as e:
                return str(e)

    def download_photo(self, photo_url):
        _response = requests.get(photo_url, stream=True)
        if _response.ok:
            try:
                _filename = _response.headers['Content-Disposition'].split('=')[1].replace('"', '')
                full_filename = (self.temp_directory + _filename)
                with open(full_filename, 'wb') as out_file:
                    shutil.copyfileobj(_response.raw, out_file)
                return full_filename
            except Exception as e:
                return {"Unable to Download Photo": f'{e}'}

    def title_photo(self, photo, text, author):
        try:
            font = ImageFont.truetype(self.font, 25)
            caption = f"\"{text}\" - {author} of Crypto Coins News."
            para = textwrap.wrap(caption, width=40)
            resized = self.resize(photo)
            picture = Image.open(resized)
            draw = ImageDraw.Draw(picture)
            current_h, pad = 250, 10
            for line in para:
                w, h = draw.textsize(line, font=font)
                draw.text(((600 - w) / 2, current_h), line, font=font)
                current_h += h + pad
            picture.save(photo)
            return {"image": photo}
        except Exception as e:
            return {"Unable to Title Photo": f'{e}'}

    def url_shortner(self, long_url):
        if url.startswith("http"):
            b = bitly_api.Connection(login=self.bitly_user, api_key=self.bitly_key)
            bitly_url = b.shorten(long_url)["url"]
            return bitly_url
        else:
            return "Invalid URI. Please ensure the url begins with {HTTP}."

    def upload_photo(self, photo, keywords):
        try:
            instagram = InstagramAPI(self.insta_username, self.insta_password)
            instagram.login()
            time.sleep(2)
            instagram.uploadPhoto(photo, caption=keywords)
            time.sleep(2)
            return {"status": "upload_success"}
        except Exception as e:
            return {"status": f"upload_failed - {e}"}


@app.route("/sms", methods=['GET', 'POST'])
def sms_reply():
    print(request.form['Body'])
    body = request.values.get('Body', None)
    resp = MessagingResponse()
    from_number = request.values.get('From')
    if from_number == f'{phone_number}':
        if body == "Begin":
            # don't look at these... just keep on scrolling..
            global photo, title, url, author, description, news_instance
            resp.message("News Bot Reporting.")
            news_instance = NewsBot()
            return str(resp)
        if body == "News":
            article = news_instance.gather_data()
            title = article['title']
            url = article['url']
            author = article['author']
            description = article['description']
            resp.message(title)
            return str(resp)
        if body == "Photo":
            photo = news_instance.random_photo()
            msg = resp.message("How do you like this view?")
            msg.media(photo)
            return str(resp)
        if body == "Caption":
            image = news_instance.download_photo(photo)
            news_instance.title_photo(image, title, author)
            insta_url = str(news_instance.url_shortner(url))
            keywords = news_instance.get_tags(description)
            clean_keywords = [''.join(e for e in string if e.isalnum()) for string in keywords]
            add_hashtags = ["#" + x for x in clean_keywords]
            str_hashtags = (' '.join(str(x) for x in add_hashtags))
            caption = str("Read more here: " + insta_url + " " + str_hashtags)
            news_instance.upload_photo(image, caption)
            resp.message("Captioned && Uploaded. Check it out.")
            return str(resp)
        else:
            resp.message("I'm not sure I understand...")
            return str(resp)


if __name__ == '__main__':
    app.run()