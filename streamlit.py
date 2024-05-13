import streamlit as st
from audiorecorder import audiorecorder
import requests
import subprocess
import tempfile
#from streamlit_TTS import auto_play
#tts deps
#from runorm import RUNorm
#from TeraTTS import TTS
#from ruaccent import RUAccent
#from torch import cuda
import tempfile
#import time
import json
import urllib.request

#asr deps
import requests

def find_first_string_between_newlines(text):
    start_index = text.find('\n') + 1  # Find the index of the first newline and move one character forward
    end_index = text.find('\n', start_index)  # Find the index of the next newline after the start index
    while start_index != -1 and end_index != -1:
        substring = text[start_index:end_index].strip()
        if len(substring) >= 10:
            return substring
        else:
            start_index = end_index + 1
            end_index = text.find('\n', start_index)
    return text

def call_tts_endpoint(text):
    req = urllib.request.Request('https://8615-2a01-c22-7b5b-d500-233d-d48-3e3d-f2cf.ngrok-free.app/tts')
    req.add_header('Content-Type', 'application/json; charset=utf-8')
    jsondata = json.dumps({"text" : text})
    jsondataasbytes = jsondata.encode('utf-8')   # needs to be bytes
    req.add_header('Content-Length', len(jsondataasbytes))
    response = urllib.request.urlopen(req, jsondataasbytes)
    raw_data = response.read()
    encoding = response.info().get_content_charset('utf8')
    #content_tts = json.loads(raw_data.decode(encoding))
    #print(content_tts)
    fname = tempfile.NamedTemporaryFile().name + 'wav'
    f = open(fname,'wb')
    f.write(raw_data)
    f.close()
    return fname



transfer_dict = {
    "recipient": "получатель",
    "money_amount": "сумма",
    "currency": "валюта",
    "from_account": "откуда",
    #"to_account": "куда",
    "description": "описание",
    "mobile_number": "мобильный_номер"
}

balance_dict = {
    "account_type": "тип_счета"
}

payment_dict = {
    "service": "сервис",
    "money_amount": "сумма",
    "currency": "валюта",
    "from_account": "откуда"
}

def output_llm(data):
    print(data)
    if data["res_QA"]=="QUESTION":
        if '\n' in data["rag_output"]["answer"]:
            s = data["rag_output"]["answer"]
            str_replace = find_first_string_between_newlines(s)
            return str_replace + '\n Источник :'+str(data["rag_output"]["source"])
        return str(data["rag_output"]["answer"])+'\n Источник :'+str(data["rag_output"]["source"])
    if data['res_class'] == 'TRANSFER' and data["res_QA"]=="REQUEST":
        result_string = "Вот что получилось распознать. Вы хотите сделать перевод. "
        for key, value in transfer_dict.items():
            if '-1' not in str(data['res_ner'][key]):
                result_string+= value + ' - ' +str(data['res_ner'][key]) + '.\n'
        return result_string
    if data['res_class'] == 'BALANCE' and data["res_QA"]=="REQUEST":
        result_string = "Вот что получилось распознать. Вы хотите проверить баланс. "
        for key, value in balance_dict.items():
            if '-1' not in str(data['res_ner'][key]):
                result_string+= value + ' - ' +str(data['res_ner'][key]) + '.\n'
        return result_string
    if data['res_class'] == 'PAYMENT' and data["res_QA"]=="REQUEST":
        result_string = "Вот что получилось распознать. Вы хотите оплатить услуги. "
        for key, value in payment_dict.items():
            if '-1' not in str(data['res_ner'][key]):
                result_string+= value + ' - ' +str(data['res_ner'][key]) + '.\n'
        return result_string




bot_prompt = 'Привет! Я голосовой помощник компании МТС, который поможет тебе проверить баланс, перевести деньги или оплатить услуги. Просто скажи мне полную команду'

if "messages" not in st.session_state:
    st.session_state.messages = []
    st.session_state.messages.append({"role": "assistant", "content": bot_prompt})
    audio_tts = call_tts_endpoint(bot_prompt)
    print(audio_tts)
    with st.sidebar:
        pl = st.audio(audio_tts, autoplay = True)

    #audio_dict = {'bytes':audio_tts, 'sample_rate':22050, 'sample_width' : audio_tts.shape[0]}
    #print(auto_play(audio_dict))


if "audio" not in st.session_state:
    st.session_state.audio_status = 0

if st.session_state.audio_status != 1:
    st.session_state.audio_status = 0


with st.sidebar:
    #st.title("Audio Recorder")
    audio = audiorecorder("Click to record", "Click to stop recording")


for message in st.session_state.messages:
    with st.chat_message(message["role"]):
        st.markdown(message["content"])
if len(audio) > 1000 and st.session_state.audio_status == 0:
    print(len(audio))
    st.session_state.audio_status = 1
    # To play audio in frontend:
    #st.audio(audio.export().read())

    # To save audio to a file, use pydub export method:
    #audio = audio.set_channels(1)
    #audio = audio.set_frame_rate(16000).set_sample_width(2)
    print(audio.sample_width)
    tmp_name_in = tempfile.NamedTemporaryFile().name + '.wav'
    tmp_name_out = tempfile.NamedTemporaryFile().name + '.wav'
    audio.export(tmp_name_in, format="wav")
    subprocess.call('ffmpeg -y -i ' +tmp_name_in+ ' -ar 16000 -ac 1 -c:a pcm_s16le '+tmp_name_out, shell = True)
    url_asr = 'https://8615-2a01-c22-7b5b-d500-233d-d48-3e3d-f2cf.ngrok-free.app/asr'
    files =  {'file': open(tmp_name_out, 'rb')}
    r = requests.post(url_asr, files=files)
    prompt = r.json()["text"]
    st.chat_message("user").markdown(prompt)
    st.session_state.messages.append({"role": "user", "content": prompt})
    #r = requests.post("http://localhost:5000/llm", json=json.dumps({"prompt" : prompt}).encode("UTF-8"))
    #print(r.text)
    req = urllib.request.Request('http://localhost:5000/llm')
    req.add_header('Content-Type', 'application/json; charset=utf-8')
    jsondata = json.dumps({"prompt" : prompt})
    jsondataasbytes = jsondata.encode('utf-8')   # needs to be bytes
    req.add_header('Content-Length', len(jsondataasbytes))
    response = urllib.request.urlopen(req, jsondataasbytes)
    raw_data = response.read()
    encoding = response.info().get_content_charset('utf8')
    content_llm = output_llm(json.loads(raw_data.decode(encoding)))
    #print(content_llm)
    audio_tts = call_tts_endpoint(content_llm)
    #print(audio_tts)
    with st.sidebar:
        pl = st.audio(audio_tts, autoplay = True)

    # To get audio properties, use pydub AudioSegment properties:
    #st.write(f"Frame rate: {audio.frame_rate}, Frame width: {audio.frame_width}, Duration: {audio.duration_seconds} seconds")
    with st.chat_message("assistant"):
        st.markdown(content_llm)
    # Add assistant response to chat history
    st.session_state.messages.append({"role": "assistant", "content": content_llm})


if prompt := st.chat_input("Спросите у меня что-нибудь!") :
    st.chat_message("user").markdown(prompt)
    st.session_state.messages.append({"role": "user", "content": prompt})
    #r = requests.post("http://localhost:5000/llm", json=json.dumps({"prompt" : prompt}).encode("UTF-8"))
    #print(r.text)
    req = urllib.request.Request('https://8615-2a01-c22-7b5b-d500-233d-d48-3e3d-f2cf.ngrok-free.app/llm')
    req.add_header('Content-Type', 'application/json; charset=utf-8')
    jsondata = json.dumps({"prompt" : prompt})
    jsondataasbytes = jsondata.encode('utf-8')   # needs to be bytes
    req.add_header('Content-Length', len(jsondataasbytes))
    response = urllib.request.urlopen(req, jsondataasbytes)
    raw_data = response.read()
    encoding = response.info().get_content_charset('utf8')
    content_llm = output_llm(json.loads(raw_data.decode(encoding)))
    print(content_llm)
    audio_tts = call_tts_endpoint(content_llm)
    print(audio_tts)
    with st.sidebar:
        pl = st.audio(audio_tts, autoplay = True)

    # To get audio properties, use pydub AudioSegment properties:
    #st.write(f"Frame rate: {audio.frame_rate}, Frame width: {audio.frame_width}, Duration: {audio.duration_seconds} seconds")
    with st.chat_message("assistant"):
        st.markdown(content_llm)
    # Add assistant response to chat history
    st.session_state.messages.append({"role": "assistant", "content": content_llm})
