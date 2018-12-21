import json
import os
import re
import urllib.request
from random import *

from bs4 import BeautifulSoup
from slackclient import SlackClient
from flask import Flask, request, make_response, render_template

app = Flask(__name__)

slack_token = ""
slack_client_id = ""
slack_client_secret = ""
slack_verification = ""
sc = SlackClient(slack_token)

words = []
dic = {}
latest = ''


def first():
    # URL 데이터를 가져올 사이트 url 입력
    # url = "http://terms.tta.or.kr/dictionary/dictionarySisaList.do"
    prot = "https://terms.naver.com/list.nhn?cid=59277&categoryId=59283&page="
    home = "https://terms.naver.com"
    # URL 주소에 있는 HTML 코드를 soup에 저장합니다.
    global words
    words = []
    global dic
    dic = {}

    for n in range(1, 5):
        url = prot + str(n)
        url.replace('\n', '')
        soup = BeautifulSoup(urllib.request.urlopen(url).read(), "html.parser")
        for i in soup.find_all("ul", class_="content_list"):
            for j in i.find_all("strong", class_="title"):
                words.append(j.find("a").get_text())
                (key, value) = j.find("a").get_text(), (home + j.find("a")["href"])
                dic[key] = value

def setLatest(url):
    global latest
    latest = url

def getLatest():
    global latest
    return latest


# 크롤링 함수 구현하기
def _crawl_naver_keywords(text):
    l = text.split()
    st = u''.join(l[1:])
    answer = []
    exp =''
    if '퇴근' in st:
        return '집에 갑니다ㅠㅠㅠㅠㅠㅠ'
    elif '자세히' in st:
        soup2 = BeautifulSoup(urllib.request.urlopen(getLatest()).read(), "html.parser")
        exp = soup2.find_all("p", class_="txt")
        string =''
        for i in exp:
            string += (i.get_text())
        return string
    elif 'mydic' in st:
        string ="저는 "
        for word in words:
            string +=word+", "

        string += "알아요 ㅋㅋ"
        return string
    elif '추천' in st:
        random = randrange(0, len(words))
        url2 = dic[words[random]]
        exp = words[random] + '\n'
        soup2 = BeautifulSoup(urllib.request.urlopen(url2).read(), "html.parser")
        exp += soup2.find("dl", class_="summary_area").get_text().replace('요약', '').strip() + '\n'
        setLatest(url2)
        return exp
    for word in words:
        if st in word:
            answer.append(word)

    for a in answer:
        url2 = dic[a]
        exp += a + '\n'
        soup2 = BeautifulSoup(urllib.request.urlopen(url2).read(), "html.parser")
        exp += soup2.find("dl", class_="summary_area").get_text().replace('요약', '').strip() +'\n'
        setLatest(url2)
        # latest = url2

    if len(answer) == 0:
        return '공부 열심히 할께요ㅠㅠ'

    return exp

    # return url


#     if  "best" in text:

#         url = "http://www.11st.co.kr/html/bestSellerMain.html"
#         sourcecode = urllib.request.urlopen(url).read()
#         soup = BeautifulSoup(sourcecode, "html.parser")
#         keyword = []
#         keyword = soup.find_all("div",class_="pup_title")


#         keywords = []
#         keywords.append("11번가 best 10 ")
#         for i in range(0,10):
#             keywords.append(keyword[i].get_text())


#         return u'\n'.join(keywords)

# 한글 지원을 위해 앞에 unicode u를 붙힙니다.
# 한글 지원을 위해 앞에 unicode u를 붙혀준다.


# 이벤트 핸들하는 함수
def _event_handler(event_type, slack_event):
    print(slack_event["event"])

    if event_type == "app_mention":
        channel = slack_event["event"]["channel"]
        text = slack_event["event"]["text"]

        keywords = _crawl_naver_keywords(text)
        sc.api_call(
            "chat.postMessage",
            channel=channel,
            text=keywords
        )

        return make_response("App mention message has been sent", 200, )

    # ============= Event Type Not Found! ============= #
    # If the event_type does not have a handler
    message = "You have not added an event handler for the %s" % event_type
    # Return a helpful error message
    return make_response(message, 200, {"X-Slack-No-Retry": 1})


@app.route("/listening", methods=["GET", "POST"])
def hears():
    first()
    slack_event = json.loads(request.data)

    if "challenge" in slack_event:
        return make_response(slack_event["challenge"], 200, {"content_type":
                                                                 "application/json"
                                                             })

    if slack_verification != slack_event.get("token"):
        message = "Invalid Slack verification token: %s" % (slack_event["token"])
        make_response(message, 403, {"X-Slack-No-Retry": 1})

    if "event" in slack_event:
        event_type = slack_event["event"]["type"]
        return _event_handler(event_type, slack_event)

    # If our bot hears things that are not events we've subscribed to,
    # send a quirky but helpful error response
    return make_response("[NO EVENT IN SLACK REQUEST] These are not the droids\
                         you're looking for.", 404, {"X-Slack-No-Retry": 1})


@app.route("/", methods=["GET"])
def index():

    return "<h1>Server is ready.</h1>"


if __name__ == '__main__':
    app.run('0.0.0.0', port=5000)

