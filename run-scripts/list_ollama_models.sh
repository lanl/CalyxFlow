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

$ollama_bin serve &
ollamaPID=$!

sleep 2

eval "$ollama_bin list"

kill $ollamaPID
