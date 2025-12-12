#!/bin/bash

arch=$(uname -m)
ollama_bin=""
version="0.12.6"

mkdir -p setup

cd setup

dlarch=""

if [ "$arch" = "aarch64" ]; then
    dlarch="arm64"
elif [ "$arch" = "x86_64" ]; then
    dlarch="amd64"
else
    echo "Unsupported arch: $arch"
    exit -1
fi

ollama_bin="./ollama-linux-${dlarch}/bin/ollama"

if [ -d "ollama-linux-${dlarch}" ]; then
    echo "Directory ollama-linux-${dlarch} exists, checking for ollama and ollama version."
    if [ -f "${ollama_bin}" ]; then
        # Matches version number this outputs
        [[ "$(${ollama_bin} --version)" =~ ([0-9\.]+) ]]
        echo "Have version ${BASH_REMATCH[1]}, want version $version"
        if [ ${BASH_REMATCH[1]} != $version ]; then
            echo "Downloading version $version"
            rm -rf ollama-linux-${dlarch}/*
            wget -qO- "https://github.com/ollama/ollama/releases/download/v${version}/ollama-linux-${dlarch}.tgz" | tar -xzf - -C ollama-linux-${dlarch}
        fi
    else
        echo "ollama binary doesn't exist, downloading version ${version}"
        rm -rf ollama-linux-${dlarch}/*
        wget -qO- "https://github.com/ollama/ollama/releases/download/v${version}/ollama-linux-${dlarch}.tgz" | tar -xzf - -C ollama-linux-${dlarch}
    fi
else
    mkdir -p ollama-linux-${dlarch}
    wget -qO- "https://github.com/ollama/ollama/releases/download/v${version}/ollama-linux-${dlarch}.tgz" | tar -xzf - -C ollama-linux-${dlarch}
fi

$ollama_bin serve &
ollamaPID=$!

sleep 2

eval "$ollama_bin pull llama3.1:8b-instruct-fp16"

kill $ollamaPID
