#!/usr/bin/env python
# coding: utf-8

from gae_http_client import RequestsHttpClient
from google.appengine.api import taskqueue

from flask import Flask, request, abort

from linebot import (
    LineBotApi, WebhookHandler
)
from linebot.exceptions import (
    InvalidSignatureError
)

from linebot.models import (
    MessageEvent, TextMessage, TextSendMessage,
)

import config
import xml.etree.ElementTree as ET
import urllib2
jaran_api_key = config.JARAN_API_KEY

app = Flask(__name__)
line_bot_api = LineBotApi(config.CHANNEL_ACCESS_TOKEN, http_client=RequestsHttpClient)
handler = WebhookHandler(config.CHANNEL_ACCESS_TOKEN)

# エリアコード取得関数
def get_area_codes(area_name):
    # xml読み込み
    tree = ET.parse('area.xml')
    root = tree.getroot()
    # 都道府県検索対象エリア情報取得
    areas = list(filter(lambda x:x.attrib['name'].find(area_name) > -1, root.iter('Prefecture')))
    # 市区町村検索対象エリア情報取得
    for prefecture in root.iter('Prefecture'):
        areas.extend(list(filter(lambda x:x.attrib['name'].find(area_name) > -1, prefecture.iter('LargeArea'))))
        areas.extend(list(filter(lambda x:x.attrib['name'].find(area_name) > -1, prefecture.iter('SmallArea'))))
    return list(map(lambda x:x.attrib['cd'], areas))

#s_areaタグを取得
def is_small_area(area_codes):
    #xml取得
    tree = ET.parse('area.xml')
    root = tree.getroot()
    area_tag = ''
    for child in root.iter('Prefecture'):
        for small in child:
            for little in small:
                if little.attrib['cd'] in area_codes:
                    area_tag = 's_area'
    return area_tag

#l_areaタグを取得
def is_large_area(area_codes):
    #xml取得
    tree = ET.parse('area.xml')
    root = tree.getroot()
    area_tag= ''
    for child in root.iter('Prefecture'):
        for small in child:
            if small.attrib['cd'] in area_codes:
                area_tag ='l_area'
    return area_tag

#エリアコード検索
def get_onsen_data(area_codes,area_tag):
    area_codes = str(area_codes[0])
    area_tag = str(area_tag)
    data = {"api_key":jaran_api_key,"query":area_codes,"area_tag":area_tag}
    url = 'http://hogehoge.com/common/api/key=?'%data['api_key'],'&%s'%data['area_tag'],'=%s'%data['query'],'&count=1&xml_ptn=1'
    url = url[0]+url[1]+url[2]+url[3]
    response = urllib2.urlopen(url)
    onsen_data = response.read()
    return onsen_data

#温泉データから温泉情報への変換
def get_onsen_info(onsen_data):
    onsen_info = ''
    root = ET.fromstring(onsen_data)
    for child in root:
        for node in child:
            if node.text is not None:
                onsen_info = onsen_info + node.text + ','
    return onsen_info

#メッセージテキストの整形
def make_onsen_message(onsen_info,area_name):
    if onsen_info is None: return
    onsen_info = onsen_info.split(',')
    top_message = area_name+"周辺の温泉を探してみたぴよ！"
    message = ''
    for i in range(len(onsen_info)):
        message += onsen_info[i]
    end_message = 'また何かあれば教えてぴよ！！'
    onsen_message = top_message + message + end_message
    return onsen_message


@app.route("/callback", methods=['POST'])
def callback():
    # get X-Line-Signature header value
    signature = request.headers['X-Line-Signature']
    # get request body as text
    body = request.get_data(as_text=True)
    app.logger.info("Request body: " + body)
    # Task Queue Add
    taskqueue.add(url='/worker',
                  params={'body': body,
                          'signature': signature},
                  method="POST")
    return 'OK'

@app.route("/worker", methods=['POST'])
def worker():
    body = request.form.get('body')
    signature = request.form.get('signature')
    # handle webhook body
    try:
        handler.handle(body, signature)
    except InvalidSignatureError:
        abort(400)

    return 'OK'

@handler.add(MessageEvent, message=TextMessage)
def handle_message(event):
    text_message = event.message.text
    area_codes = get_area_codes(text_message)
    area_tag = is_large_area(area_codes)
    if area_tag is None:
        arae_tag = is_small_area(area_codes)
    
    onsen_data = get_onsen_data(area_codes,area_tag)
    if onsen_data is None:
        LineBotApi.reply_message(
        event.reply_token,
        TextSendMessage(text='温泉が見つからないぴよ！！'))
    
    onsen_info = get_onsen_info(onsenData)
    if onsen_info is None:
        LineBotApi.reply_message(
        event.reply_token,
        TextSendMessage(text='温泉が見つからないぴよ！！'))
    
    onsenMessage = makeOnsenMessage(onsen_info,testMessage)
    if onsen is None:
        LineBotApi.reply_message(
        event.reply_token,
        TextSendMessage(text='温泉が見つからないぴよ！！'))
    
    line_bot_api.reply_message(
        event.reply_token,
        TextSendMessage(text=onsen_info))

if __name__ == "__main__":
    app.run()
