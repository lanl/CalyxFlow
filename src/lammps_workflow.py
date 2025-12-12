import os
from llama_index.llms.ollama import Ollama
from llama_index.llms.vllm import Vllm
from llama_index.llms.openai_like import OpenAILike
from llama_index.core.agent.workflow import ReActAgent, FunctionAgent
from llama_index.core.workflow import Context
from llama_index.core.agent.workflow import AgentStream, ToolCallResult, AgentOutput, AgentInput, ToolCall
from llama_index.core.chat_engine import SimpleChatEngine
from llama_index.core.agent.react.output_parser import ReActOutputParser
from llama_index.core.agent.react.types import ActionReasoningStep

import json
import re

import argparse
import asyncio

import sys
sys.path.append(".")
from agents.llama_index_tools import *

import logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger("llama_index.custom")

class LlamaJSONToolOutputParser(ReActOutputParser):
    def parse(self, output: str, is_streaming: bool = False):
        """
        Parse either the classic ReAct format or a Llama-style JSON tool call.
        """
        # Try Llama JSON tool output:
        # Look for a JSON object with "tool" and "input" fields
        curly = re.search(r"Action:\s*\n\s*({)", output, re.MULTILINE)
        logger.info(f"Match: {curly}")
        if curly:
            logger.info("In match")
            try:
                # Find a JSON-looking substring
                json_start = curly.start(1)
                logger.info(f"Found json start: {json_start}")
                logger.info(f"String: {output[json_start:]}")
                decoder = json.JSONDecoder()
                tool_json, idx = decoder.raw_decode(output[json_start:])
                logger.info(f"JSON tool string: {tool_json}")
                tool_name = tool_json.get("tool")
                tool_input = tool_json.get("input", {})
                thought_match = re.search(r"Thought:(.*)", output)
                thought = thought_match.group(1).strip() if thought_match else ""

                # LlamaIndex expects an AgentAction with these fields:
                return ActionReasoningStep(
                    thought=thought,
                    action=tool_name,
                    action_input=tool_input,
                )
            except Exception as e:
                logger.info("In exception")
                pass

        # Try classic ReAct parsing first (fallback to super)
        try:
            return super().parse(output, is_streaming=is_streaming)
        except Exception:
            pass

        # If nothing matched, raise
        raise ValueError(f"Unrecognized custom agent output: {output}")

async def printEvents(handler):
    async for ev in handler.stream_events():
        if isinstance(ev, AgentStream):
            print(f"{ev.delta}", end="", flush=True)
        elif isinstance(ev, AgentInput):
            print("Agent input: ", ev.input)
            print("Agent name: ", ev.current_agent_name)
        elif isinstance(ev, AgentOutput):
            print("Agent output: ", ev.response)
            print("Tool calls made: ", ev.tool_calls)
            print("Raw LLM response: ", ev.raw)
        elif isinstance(ev, ToolCallResult):
            print("Tool called: ", ev.tool_name)
            print("Arguments to the tool: ", ev.tool_kwargs)
            print("Tool output: ", ev.tool_output)

async def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("model", help="Model to use", type=str)
    parser.add_argument("--inputFileDir", help="Directory containing any required files referenced in the input file", type=str)
    parser.add_argument("--lammps", help="Absolute path to lammps binary.", type=str)
    parser.add_argument("--port", help="Port of model server. 11434 for ollama, 8000 for vllm.", type=str)
    args = parser.parse_args()

    inputFileDir = args.inputFileDir if args.inputFileDir is not None else os.getenv("LAMMPS_POTENTIALS")

    llm = OpenAILike(
        model=args.model,
        request_timeout=180.0,
        api_base=f"http://localhost:{args.port}/v1",
        api_key="fake",
        is_chat_model=True,
        is_function_calling_model=False,
        context_window=64000
    )

    llamaParser = LlamaJSONToolOutputParser()

    with open("agents/instructions/io.txt", "r") as f:
        ioAgentPrompt = f.read()
    ioAgent = ReActAgent(tools=[unique_output_dir_tool, write_file_tool, read_file_tool], llm=llm, system_prompt=(
    "You are an assistant that uses tools to do file I/O operations. "
    "The following tools are available to you: "
    "_read_file(fpath: str) "
    "_write_file(text: str, fname: str, dname: str) "
    "_unique_output_directory(dirname: str)\n"
    "If you need to read a file, use the _read_file tool. "
    "If you need to write a file, use the _write_file tool. "
    "If you need to create a output directory, use the _unique_output_directory tool. "
    "Do NOT try to access files directly yourself - use the tools "
    "Do NOT try to use python or direct function calls. "
    ), verbose=False,
    output_parser=llamaParser)
    ioCtx = Context(ioAgent)

    inputEditor = SimpleChatEngine.from_defaults(
        llm=llm,
    )

    verifier = SimpleChatEngine.from_defaults(
        llm=llm,
    )

    runnerAgent = ReActAgent(tools=[run_command_tool], llm=llm, system_prompt=(
    """
    You are an assistant that will run LAMMPS simulations by generating bash commands.
    You will be provided a path to LAMMPS and an input file.
    Use srun to run LAMMPS.
    Change your directory to the directory that contains the input file before running LAMMPS

    The following tools are available to you:
    _run_lammps(command: str, cwd: str)
    Use the _run_lammps tool to run the generated run command. Make sure to adjust all your paths to properly handle cwd.
    """), verbose=False)
    runnerCtx = Context(runnerAgent)

    handler = ioAgent.run("Please read lammps_input.txt and show the full file contents in your final answer.", ctx=ioCtx)

    await printEvents(handler)
    response = await handler
    infile = response.response

    fileChanges = f"""
    Change the mass to be double its current value.
    Prepend 'Fe_Mishin2006.eam.alloy' with the absolute path '{inputFileDir}'
    """

    response = inputEditor.chat(f"Here is a LAMMPS input file. {fileChanges} Return only the modified file, no explanations.\n<FILE START>\n{infile}\n<FILE END>\n")

    modifiedfile = response.response

    response = verifier.chat(
    f"""
    You are a file change validator.

    The intended changes are:
    {fileChanges}

    Compare the ORIGINAL and MODIFIED files below.

    Respond only with either:
    - VALID if the intended changes are present AND no other changes are present
    - INVALID if the intended changes aren't present OR if there are any other differences.

    ### ORIGINAL ###
    {infile}

    ### MODIFIED ###
    {modifiedfile}
    """
    )

    print(response.response)

    if response.response != "VALID":
        print("Editor did not modify the file properly. Exiting")
        return

    handler = ioAgent.run(f"Please create an output directory under 'lammps_inputs'.", ctx=ioCtx)

    await printEvents(handler)
    response = await handler
    outdir = str(response)

    handler = ioAgent.run(f"Here is a modified LAMMPS input file. Please write it to a file named modified_lammps_input.txt in the directory {outdir}. using the _write_file tool. \n<FILE START>{modifiedfile}<FILE END>", ctx=ioCtx)

    await printEvents(handler)
    response = await handler

    print(str(response))

    handler = runnerAgent.run(
    f"""
    Run a strong scaling study using the LAMMPS binary {args.lammps} from 1 process to 8 processes in powers of 2 using mpirun

    Ensure you always use '-np', even with one process.

    Create a compound command where you load the module 'nvhpc' before running the LAMMPS command

    Make your working directory {outdir}, and your input file modified_lammps_input.txt using `-in`

    Ensure every run has a unique log file

    Only try to run each run once, if it fails simply make a note of it.
    """, ctx=runnerCtx)

    await printEvents(handler)
    response = await handler

    return

if __name__ == '__main__':
    asyncio.run(main())
