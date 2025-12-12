# CalyxFlow
CalyxFlow is a lightweight agentic artificial intelligent workflow. This workflow demonstrates the use of AI LLMs to generate modeling and simulation inputs for a scientific simulation and manage execution and analysis of a suite of simulations. 

## Building

- Clone with `--recursive` to download LAMMPS if you don't already have a LAMMPS binary

- Install python dependencies using `uv`:
```
uv sync
```

We primarily use vLLM as our model server. If you want to use Ollama:
```
./setup_ollama.sh
```
This also downloads llama3.1:8b-instruct-fp16. Use `./run-scripts/download_ollama_model.sh` to download more models.

All scripts will start and kill the ollama server automatically.

## LAMMPS

- Build with the script `./build_lammps.sh`; This uses NVHPC to build LAMMMPS with the packages needed for the examples we've been testing with.
- Can pass in TAG to script: `TAG=<tag> ./build_lammps.sh` build dir is `build-lammps-${TAG}`, `build-lammps-grace` by default
- When building with NVHPC on Grace nodes, `mpirun` should be used instead of `srun`

## Running the LAMMPS workflow

In one window, serve your model:
```
. .venv/bin/activate
./run-scripts/run_vllm.sh <model> <model name> ["<extra vLLM args>"] [profile] [profile dir=./vllm_profiler]
```

In another, run the workflow:
```
. .venv/bin/activate
./run-scripts/run_lammps_workflow.sh <model name> <model server>=vllm <LAMMPS bindir> <LAMMPS inputs dir> [profile]
```
