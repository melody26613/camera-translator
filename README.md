# Camera Translator
Capture video frames from the OBS virtual camera, extract text using [PaddleOCR](https://github.com/PaddlePaddle/PaddleOCR), and translate it with the [Ollama](https://ollama.com/download/linux) LLM model.


![demo 1](https://github.com/melody26613/camera-translator/blob/main/pic/2025-08-24_10-01-41.gif)

![demo 2](https://github.com/melody26613/camera-translator/blob/main/pic/2025-08-24_10-03-11.gif)

* flow

OBS virtual camera → capture image → PaddleOCR REST API → Ollama translate → Output translated image

## Preparation
1. install nvidia driver
2. install nvidia toolkit for docker container
3. install docker

* run the docker container from my repo [paddle-ocr-restapi](https://github.com/melody26613/paddle-ocr-restapi)

4. install ollama

* ollama model
```bash
ollama pull gemma2:2b
```

* ollama config

example service configuration:
```
[Service]
Environment="OLLAMA_HOST=0.0.0.0:11434"
Environment="OLLAMA_MODELS=/mnt/d/workspace/ollama_models"
Environment="OLLAMA_DEBUG=1"
Environment="OLLAMA_KEEP_ALIVE=-1"
```

5. OBS
6. python

## Python Setting
```bash
python -m venv venv
        
source venv/bin/activate # activate virtual environment
        
pip install --upgrade pip
pip install -r requirements.txt

# deactivate
```

## OBS Setting
1. output the game screen via the OBS virtual camera
2. execute `python utils/list_all_camera.py` to get the device id of the OBS virtual camera
3. execute `python capture_camera.py`
4. add the output image `pic/translated_text_overlay.png` as a source in OBS