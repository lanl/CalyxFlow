#!/bin/bash

# Check if HF_TOKEN is unset or empty
if [ -z "$HF_TOKEN" ]; then
    echo "Error: HF_TOKEN environment variable is not set." >&2
    echo "You need the HF_TOKEN from huggingface to download the model." >&2
    exit 1
fi

cmd=$(cat << EOF
huggingface-cli login --token $HF_TOKEN --add-to-git-credential
huggingface-cli download $1
EOF
)
echo "$cmd" > temp
chmod +x temp
bash -c './temp'
rm temp

