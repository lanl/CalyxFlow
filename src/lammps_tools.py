import os
import uuid
import json
import subprocess

from typing import Annotated
from llama_index.core.tools import FunctionTool

def _unique_output_directory(dirname: str = "dirname"):
    """
    Useful for making  a unique output directory.

    :param dirname: The directory name to be made unique
    :returns: A unique directory path
    """

    if not hasattr(_unique_output_directory, "outdir"):
        p = os.path.join("output", f"{dirname}-{uuid.uuid4().hex}")
        while os.path.isdir(p):
            p = os.path.join("output", f"{dirname}-{uuid.uuid4().hex}")
        os.makedirs(p)
        _unique_output_directory.outdir = p
        return p
    else:
        return _unique_output_directory.outdir

unique_output_dir_tool = FunctionTool.from_defaults(
    fn=_unique_output_directory,
    description="Creates a unique output directory. input 1 is 'dirname' and is the base directory name that will be turned into a unique output directory by the tool.",
    return_direct=True)

def _write_file(text: str = "", fname: str = "dummy_fname", dname: str = "dummy_dname"):
    """
    Tool to write to a file

    :param text: Text to write to the file
    :param fname: Unique file basename that text will go into
    :param dname: Directory that the file will be created in
    :returns: Dictionary containing success status and error message if not successful
    """

    fpath = os.path.join(dname, fname)

    try:
        with open(fpath, 'x') as file:
            file.write(text)
        return {"success": True}
    except FileExistsError:
        return {"success": False, "error": "File already exists"}
    except OSError as e:
        return {"success": False, "error": f"{type(e).__name__}"}

write_file_tool = FunctionTool.from_defaults(
    fn=_write_file,
    description="Writes a file to disk. Input 1 is 'text' and is the file text, input 2 is 'fname' and is the file name, input 3 is 'dname' and is the file directory",
    return_direct=True)

def _read_file(fpath: Annotated[str, "A relative filepath"] = "dummy_fpath"):
    """
    Tool to read a file as text

    :param fpath: Path to file to read
    :returns: Dictionary containing success status and file content as a string or error message
    """

    try:
        with open(fpath, 'r') as file:
            file_content = file.read()

        return {"success": True, "result": file_content}

    except OSError as e:
        return {"success": False, "error": f"{type(e).__name__}"}

read_file_tool = FunctionTool.from_defaults(
    fn=_read_file,
    description="Reads a file from disk. Input parameter is called 'fpath' and is a relative file path.")


def _run_lammps(command: str, cwd: str):
    """
    Tool to run a command in bash
    """
    return subprocess.run(command, shell=True, cwd=cwd)

run_command_tool = FunctionTool.from_defaults(
    fn=_run_lammps,
    description="Runs a bash lammps command using subprocess. cwd is the working directory of the input file. Returns the CompletedProcess instance from the subprocess run."
)
