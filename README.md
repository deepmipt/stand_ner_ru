# Demo stand. Model: NER (Russian)

## Installation and start
1. Clone the repo and `cd` to project root:
    ```
    git clone https://github.com/deepmipt/stand_ner_ru.git
    cd stand_ner_ru
    ```
2. Run script to download and unpack model components:
    ```
    ./download_components.sh
    ```   
3. Create a virtual environment with `Python 3.6`:
    ```
    virtualenv env -p python3.6
    ```
4. Activate the environment:
    ```
    source ./env/bin/activate
    ```
5. Install requirements:
    ```
    pip install -r requirements.txt
    ```
6. Specify model endpoint host (`api_host`) and port (`api_port`) in `ner_agent_config.json`
7. Specify virtual environment path (if necessary) in `run_ru_ner.sh`
8. Run model:
    ```
    ./run_ru_ner.sh
    ```
## Building and running with Docker:
1. If necessary, build Base Docker image from:

   https://github.com/deepmipt/stand_docker_cuda
  
2. Clone the repo and `cd` to project root:
    ```
    git clone https://github.com/deepmipt/stand_ner_ru.git
    cd stand_ner_ru
    ```
3. Build Docker image:
   ```
   sudo docker build -t stand/ner_ru .
   ```
4. Run Docker image:
   ```
   sudo docker run -p <host_port>:6004 -v /path/to/host/vol/map/dir:/vol stand/ner_ru
   ```