## Profit - Backend
Решение запускалось на RTX4090

0.pip install -r requirements.txt

1. Whisper + CUDA
https://github.com/ggerganov/whisper.cpp

model from:
https://huggingface.co/Ftfyhh/whisper-ggml-q4_0-models/tree/main
model name: whisper-ggml-large-v3-q4_0.bin
use command:
./server -m ./whisper-ggml-large-v3-q4_0.bin -l ru -bo 7

2. llama.cpp + CUDA
install: CMAKE_ARGS="-DLLAMA_CUDA=on" FORCE_CMAKE=1 pip install 'llama-cpp-python[server]'
model: https://huggingface.co/TheBloke/CapybaraHermes-2.5-Mistral-7B-GGUF/blob/main/capybarahermes-2.5-mistral-7b.Q8_0.gguf
use command:
python3 -m llama_cpp.server --model capybarahermes-2.5-mistral-7b.Q8_0.gguf  --n_gpu_layers 32 


3. python backend.py


P.S gpt-3.5-turbo в вызовах llm - локальная CapybaraHermes-2.5-Mistral-7B, а не платный функционал от OpenAI :)