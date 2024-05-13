from gtts import gTTS

txt = "Отвечаю на ваш запрос. Как можно сменить номер, если у вашего кота 8 лапок."

tts = gTTS(text=txt, lang='ru', slow=False)
tts.speed = 5;
tts.save("test.mp3")

print(tts.write_to_fp())