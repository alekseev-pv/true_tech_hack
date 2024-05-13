#rag deps
import pandas as pd
from torch import cuda
from langchain.embeddings.huggingface import HuggingFaceEmbeddings
from langchain_community.document_loaders.csv_loader import CSVLoader
from langchain.text_splitter import RecursiveCharacterTextSplitter
from langchain.vectorstores import Chroma
from langchain_core.prompts import ChatPromptTemplate
from langchain.chains.combine_documents import create_stuff_documents_chain
from langchain.chains import create_retrieval_chain
from langchain_openai import OpenAI
from flask_cors import CORS, cross_origin
from flask import send_file


#llm deps
from typing import List
import enum
import openai
import json
from deep_translator import GoogleTranslator
import instructor
from pydantic import BaseModel


#tts deps
from runorm import RUNorm
from TeraTTS import TTS
from ruaccent import RUAccent
from torch import cuda
import tempfile

#asr deps
import requests

class ttsModel():
    def __init__(self, device = '', model_size = "small", omograph_model_size = 'turbo'):
        if device == '':
            device = f'cuda:{cuda.current_device()}' if cuda.is_available() else 'cpu'
        self.normalizer = RUNorm()
        self.normalizer.load(model_size=model_size, device=device)
        self.accentizer = RUAccent()
        self.accentizer.load(omograph_model_size=omograph_model_size, use_dictionary=True)
        self.tts = TTS("TeraTTS/natasha-g2p-vits", add_time_to_end=1.0, tokenizer_load_dict=False) # Вы можете настроить 'add_time_to_end' для продолжительности аудио, 'tokenizer_load_dict' можно отключить если используете RUAccent

    def call_tts(self, text):
        text = self.normalizer.norm(text)
        text = self.accentizer.process_all(text)
        audio = self.tts(text, play=False, lenght_scale=1.1)
        tmp = tempfile.NamedTemporaryFile()
        self.tts.save_wav(audio, tmp.name + '.wav')  # Сохранить аудио в файл
        return tmp.name + '.wav'


class RagQA:

    def __init__(self, fname='FINAL.csv', device=''):
        embed_model_id = 'intfloat/multilingual-e5-base'
        if device == '':
            device = f'cuda:{cuda.current_device()}' if cuda.is_available() else 'cpu'

        embed_model = HuggingFaceEmbeddings(
        model_name=embed_model_id,
        model_kwargs={'device': device},
        encode_kwargs={'device': device, 'batch_size': 32})
        loader = CSVLoader(file_path=fname, csv_args={
        'delimiter': ';',
        'fieldnames': ['url', 'name', 'content', 'product'],}, source_column="url")
        data = loader.load()
        text_splitter = RecursiveCharacterTextSplitter(chunk_size=1200, chunk_overlap=20)
        splits = text_splitter.split_documents(data)
        vectorstore = Chroma.from_documents(documents=splits, embedding=embed_model)
        retriever = vectorstore.as_retriever(search_type="mmr", search_kwargs={"k": 1})
        llm = OpenAI(
            api_key = "sk-xxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxx", # can be anything
            base_url = "http://localhost:8000/v1") # NOTE: Replace with IP address and port of your llama-cpp-python server)
        template = """
        Вы - помощник компании МТС и МТС Банка и вы помогаете людям отвечать на вопросы.
        Используйте только предоставленный контекст {context}, чтобы ответить на следующий вопрос:
        Вопрос: {input}
        Напишите ответ на русском языке. Напишите только ответ и ничего лишнего. Ответ должен быть не более чем в трех предложениях.
        """
        prompt = ChatPromptTemplate.from_template(template)
        doc_chain = create_stuff_documents_chain(llm, prompt)
        self.chain = create_retrieval_chain(retriever, doc_chain)

    def call_rag(self, user_query):
        response = self.chain.with_config(configurable={"llm_temperature": 0, "draft_model" : "LlamaPromptLookupDecoding(num_pred_tokens=10)", "stop" : '["Q:", "\n"]'}).invoke({"input": user_query})
        return response







# Define Enum class for multiple labels
class MultiLabelsQA(str, enum.Enum):
    QUESTION = 'QUESTION'
    REQUEST = 'user wants to make an operaion'
    #CONFIRM_OPERATION = 'user wants to confirm an operaion'
    #BACK = 'go back'

# Define the multi-class prediction model
class MultiClassPredictionQA(BaseModel):
    """
    Class for a multi-class label prediction.
    """

    class_labels: MultiLabelsQA


# Define Enum class for multiple labels
class MultiLabels(str, enum.Enum):
    PAYMENT = "User wants to pay for service or utilities"
    BALANCE = "User wants to check balance"
    TRANSFER = "User wants to transfer money to people"
    OTHER = "loans,investments,questions"


# Define the multi-class prediction model
class MultiClassPrediction(BaseModel):
    """
    Class for a multi-class label prediction.
    """

    class_labels: MultiLabels


class Transfer(BaseModel):
    recipient: str
    money_amount: int
    currency: str
    from_account: str
    #    to_account: str
    description: str
    mobile_number: str

class Balance(BaseModel):
    account_type: str

class Payment(BaseModel):
    service : str
    money_amount: int
    currency: str
    from_account: str

classes_d = {
    'PAYMENT' : Payment,
    'BALANCE' : Balance,
    'TRANSFER' : Transfer
}

class llmPredictor():

    def __init__(self,):

        self.client = openai.OpenAI(
        api_key = "sk-xxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxx", # can be anything
        base_url = "http://localhost:8000/v1" # NOTE: Replace with IP address and port of your llama-cpp-python server
        )
        self.client = instructor.patch(client=self.client)
        self.rag = RagQA()
    
    def translate_prompt(self, prompt):
        return GoogleTranslator(source='auto', target='en').translate(prompt)

    def classification_QA(self, prompt: str) -> MultiClassPredictionQA:
        return self.client.chat.completions.create(
            model="gpt-3.5-turbo",
            response_model=MultiClassPredictionQA,
            temperature = 0,
            messages=[
                {"role": "system", "content": f"Classify the following text: {prompt}"},
                {"role": "user", "content": prompt},
            ])
    
    def classification_request(self, prompt: str) -> MultiClassPrediction:
        return self.client.chat.completions.create(
            model="gpt-3.5-turbo",
            response_model=MultiClassPrediction,
            temperature = 0,
            messages=[
                {"role": "system", "content": f"Classify the following text: {prompt}"},
                {"role": "user", "content": prompt},
            ])

    def ner(self, prompt: str, res_classification_request):
        return self.client.chat.completions.create(
        model="gpt-3.5-turbo",
        response_model=instructor.Partial[classes_d[res_classification_request.class_labels.name]],
        messages=[
            {"role": "system", "content": "Format the user prompt to JSON file with following structure. If you couldn't find any field from structure in prompt, return -1 for this field. Answer with Russian language."},
            #{"role": "system", "content": "Форматируй запрос в формат JSON со следующей структурой. Если невозможно найти какое-то из полей, то выдай для этого поля пустое."},
            {"role": "user", "content": prompt},
        ],
        temperature=0,
    )
    

    def run_llm_endpoint(self, prompt):
        res_ner = ''
        rag_output = ''
        res_classification = ''
        res_classification_QA = ''
        translated_prompt = self.translate_prompt(prompt)
        res_classification_QA = self.classification_QA(translated_prompt)
        res_classification_request = self.classification_request(translated_prompt)
        if res_classification_QA.class_labels.name == "QUESTION" :
            res_rag = self.rag.call_rag(prompt)
            rag_output = {'answer' : res_rag['answer'], 'source' : res_rag['context'][0].metadata['source']}
        else:
            res_ner = self.ner(prompt, res_classification_request).dict()
        return {'res_QA': res_classification_QA.class_labels.name, 'res_class': res_classification_request.class_labels.name,  'res_ner' : res_ner, 'rag_output' : rag_output}


from flask import Flask, request, jsonify
app = Flask(__name__)
cors = CORS(app, expose_headers=['Access-Control-Allow-Origin'])
app.config['JSON_AS_ASCII'] = False
app.config['CORS_HEADERS'] = 'Content-Type'
app.json.ensure_ascii = False
llm_predictor = llmPredictor()
tts_model = ttsModel()

@app.route('/llm', methods=['POST'])
def llm():
    content = request.get_json()
    print(content)
    print(content["prompt"])
    return jsonify(llm_predictor.run_llm_endpoint(content["prompt"]))


@app.route('/asr', methods=['POST'])
@cross_origin()
def asr():
    print(request.files)
    if not request.files:
            # If the user didn't submit any files, return a 400 (Bad Request) error.
        abort(400)

        # For each file, let's store the results in a list of dictionaries.
    results = []

    # Loop over every file that the user submitted.
    for filename, handle in request.files.items():
        # Create a temporary file.
        # The location of the temporary file is available in `temp.name`.
        temp = tempfile.NamedTemporaryFile()
        # Write the user's uploaded file to the temporary file.
        # The file will get deleted when it drops out of scope.
        handle.save(temp)
        print(temp.name)
        files = {'file': open(temp.name, 'rb')}
        url = 'http://localhost:8080/inference'
        r = requests.post(url, files=files)
        return r.json()
        #dictToSend = {'file':temp}
        #res = requests.post('http://localhost:8080/inference', json=dictToSend)


from flask import send_file

@app.route('/tts', methods=['POST'])
@cross_origin()
def tts():
    content = request.json
    #content.encoding = "UTF-8"
    print(content)
    file_name = tts_model.call_tts(content['text'])
    path_to_file = file_name

    return send_file(
        file_name, 
        mimetype="audio/wav", 
        as_attachment=True)

@app.route('/asr_llm', methods=['POST'])
@cross_origin()
def asr_llm():
    print(request.files)
    if not request.files:
            # If the user didn't submit any files, return a 400 (Bad Request) error.
        abort(400)

        # For each file, let's store the results in a list of dictionaries.
    results = []

    # Loop over every file that the user submitted.
    for filename, handle in request.files.items():
        # Create a temporary file.
        # The location of the temporary file is available in `temp.name`.
        temp = tempfile.NamedTemporaryFile()
        # Write the user's uploaded file to the temporary file.
        # The file will get deleted when it drops out of scope.
        handle.save(temp)
        print(temp.name)
        files = {'file': open(temp.name, 'rb')}
        url = 'http://localhost:8080/inference'
        r = requests.post(url, files=files)
    return jsonify(llm_predictor.run_llm_endpoint(r.json()['text']))







if __name__ == '__main__':
    app.run(host= '0.0.0.0',debug=True)
