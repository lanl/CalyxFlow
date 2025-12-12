#!/bin/bash
# ./run-scripts/run_vllm.sh $HOME/.cache/huggingface/hub/models--mistralai--Magistral-Small-2506/snapshots/e4b9e3089b5727e266a430bc062cacc40631b8a5 magistral --tokenizer-mode=mistral

# MODEL_CHECKPOINT=$HOME/.cache/huggingface/hub/models--mistralai--Devstral-Small-2505/snapshots/a6e97eaf3bfe308cb5396675a716147b2ced37c8
# MODEL_NAME=devstral
MODEL_CHECKPOINT=$1
MODEL_NAME=$2
# for mistral-type models:
# --tokenizer-mode=mistral \
EXTRA_ARGS=$3
echo $EXTRA_ARGS
PROFILE=${4:-noprofile}
profileDir=${5:-"./vllm_profiler"}

#export VLLM_ATTENTION_BACKEND=FLASH_ATTN
#export VLLM_USE_V1=0
export VLLM_NO_USAGE_STATS=1
export VLLM_RPC_GET_DATA_TIMEOUT_MS=1800000
export VLLM_RPC_TIMEOUT=1000000
export VLLM_HTTP_TIMEOUT_KEEP_ALIVE=60
export VLLM_TORCH_PROFILER_RECORD_SHAPES=1
export VLLM_TORCH_PROFILER_WITH_FLOPS=1
export VLLM_TORCH_PROFILER_WITH_PROFILE_MEMORY=1
if [[ "$PROFILE" == "profile" ]]; then
    export VLLM_TORCH_PROFILER_DIR=${profileDir}
fi
python3 -m vllm.entrypoints.openai.api_server \
    --model $MODEL_CHECKPOINT \
    --uvicorn-log-level debug \
    --seed 10 \
    --disable-log-stats --max-log-len=0 \
    --served-model-name $MODEL_NAME $EXTRA_ARGS

