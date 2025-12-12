#!/bin/bash

arch=$(uname -m)
ollama_bin=""

if [ "$arch" = "aarch64" ]; then
    ollama_bin="./setup/ollama-linux-arm64/bin/ollama"
elif [ "$arch" = "x86_64" ]; then
    ollama_bin="./setup/ollama-linux-amd64/bin/ollama"
else
    echo "Unsupported arch: $arch"
    exit -1
fi

model=${1:-"Llama3.3"}
model_server=${2:-vllm}
lammpsBin=$3
inDir=$4
do_profile=${5:-noprofile}


port="0"
if [[ "$model_server" == "ollama" ]]; then
    port="11434"
elif [[ "$model_server" == "vllm" ]]; then
    port="8000"
else
    echo "Unsupported model server. Supported servers: 'vllm', 'ollama' (default)"
    exit -1
fi

if [[ "$model_server" == "ollama" ]]; then
    ollama_bin serve &
    ollamaPID=$!
    sleep 5
fi

if [[ "$model_server" == "vllm" && "$do_profile" == "profile" ]]; then
    set -e
    curl -X POST http://127.0.0.1:8000/start_profile
    set +e
fi

python3 -m src.llamaindextest ${model} \
    --inputFileDir="${inDir}" \
    --lammps="${lammpsBin}" \
    --port=$port

if [[ "$model_server" == "vllm" && "$do_profile" == "profile" ]]; then
    curl -X POST http://127.0.0.1:8000/stop_profile
fi

if [[ "$model_server" == "ollama" ]]; then
    kill $ollamaPID
fi
