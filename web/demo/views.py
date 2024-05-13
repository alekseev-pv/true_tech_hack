from django.shortcuts import render

from django.http import HttpResponse

from django.views.decorators.csrf import csrf_exempt

from bs4 import BeautifulSoup

import base64
from datetime import datetime
import os


import json
import requests

import pyttsx3

# some voice inits

tts = pyttsx3.init()
# Задать голос по умолчанию
tts.setProperty('voice', 'ru') 
tts.setProperty('rate', 300) 





def index(request):
    context = {"inn" : None, "areas" : None, "minjust" : None, "grants" : None}
    return render(request, "index.html", context)

def send(request):
    recipient = ""
    amount = ""
    currency = ""
    from_account = ""

    if request.GET.get('recipient') is not None:
        recipient = request.GET.get('recipient')

    if request.GET.get('amount') is not None:
        amount = request.GET.get('amount')

    if request.GET.get('currency') is not None:
        currency = request.GET.get('currency')

    if request.GET.get('from_account') is not None:
        from_account = request.GET.get('from_account')


    context = {"recipient" : recipient, "amount" : amount, "currency" : currency, "from_account" : from_account}

    return render(request, "send.html", context)

def help(request):
    context = {}
    return render(request, "help.html", context)

@csrf_exempt
def voice(request):

    answer = '{"result" : "err", "state" : 0}';


    if request.method == 'POST':

        #### get wav file from base64

        data = dict(request.POST.items())
        # print(data)

        c = datetime.now().strftime("%m.%d.%Y.%H.%M.%S")

        # encode_string = base64.b64encode(data['voice'])
        
        file_name = "audio"+ c +".wav"

        wav_file = open('media/'+file_name, "wb")

        file_full_name = os.path.abspath(wav_file.name)

        print(file_full_name)
        
        decode_string = base64.b64decode(data['voice'].encode("utf-8"))
        
        wav_file.write(decode_string)
        wav_file.close()

        ############################
        # now we have saved wav & his name

        ### go to LLM

        base_url = "https://8615-2a01-c22-7b5b-d500-233d-d48-3e3d-f2cf.ngrok-free.app"

        url_asr = base_url +"/asr"
        url_llm = base_url +"/llm"
        url_tts = base_url +"/tts"

        url_asr_llm = base_url +"/asr_llm"

        url_load = "127.0.0.1:8080/load"
        
        

        # load

        ### PATH TO MODEL?
        # post_data = {'model': 'path'}

        # try:
        #     result = requests.post(url_load, data = post_data, headers = headers)
        #     print(result.text)

        # except Exception as err:
        #     print("Model loading error ", err)

        #inference

        # ASR - inference

        files = {'file': (file_name, open(file_full_name, 'rb'), 'audio/wav')}

        post_data = {'temperature': '0.0',
                     'temperature_inc':'0.2',
                     'response_format':'json'}
        
        # dont use it!
        headers = {"Content-Type" : "multipart/form-data"}
        
        print("asr!")

        try:
            result = requests.post(url_asr, files=files, data = post_data)
            print(result.text)
            text_request = result.text
        except Exception as err:
            print("Model inference error: ", err)



        # LLM - inference

        llm_answer = ""
        

        post_data = {'prompt': text_request}
        
        headers = {"Content-Type" : "application/json"}
        
        print("LLM")

        try:
            result = requests.post(url_llm, json = post_data, headers=headers)
            llm_answer = result.json()
            print(llm_answer)
            print(llm_answer.keys())
        except Exception as err:
            print("Model inference error: ", err)        
        
        #################################################################################################################


        # tts.save_to_file('Отвечаю на ваш запрос. Как можно сменить номер, если у вашего кота 8 лапок.', 'media/test.mp3')
        
        clean_txt_answer = ""

        if len(llm_answer['rag_output']) > 0:
            print(type(llm_answer['rag_output']['answer']))
            print(llm_answer['rag_output']['answer'])

            t = llm_answer['rag_output']['answer'] 

            clean_txt_answer = t[0:t.find('\n\n', 0)]
            
            print(t)
            
            print("!")

            print(clean_txt_answer)

            print("!")

            print(len(clean_txt_answer))
            print(type(clean_txt_answer))


        if (len(clean_txt_answer) > 0):
            tts.save_to_file(clean_txt_answer, 'media/test.mp3')
            print("!!!")
        else:
            tts.save_to_file('Повторите запрос', 'media/test.mp3')  
        
        # Wait until above command is not finished.
        tts.runAndWait()

        enc = base64.b64encode(open("media/test.mp3", "rb").read())

        # print(enc)

        answer = '{"result" : "play_voice", "text_request": "запрос", "text_response": "ответ", "state" : "submit", "voice" : "'+ enc.decode("utf-8") +'"}'

    return HttpResponse(answer)