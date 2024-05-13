import requests
import base64

post_data = {"prompt" : "перейди назад"}
post_data = {"prompt" : "сколько сейчас времени и денег?"}
post_data = {"prompt" : "какой тариф лучше"}
post_data = {"prompt" : "назад"}

post_data = {"text" : "перевести сестре 4000 рублей"}


# dont use it!
headers = {"Content-Type" : "application/json"}

url_llm = "https://53b800bf198196.lhr.life/tts"

try:
    result = requests.post(url_llm, json = post_data, headers=headers)
    #print(result.content)
    #print(result.json())
    

    wav_file = open('ww.wav', "wb")

    decode_string = base64.b64decode(result.text.encode("utf-8"))
        
    wav_file.write(result.content)
    wav_file.close()



except Exception as err:
    print("Model inference error: ", err)
