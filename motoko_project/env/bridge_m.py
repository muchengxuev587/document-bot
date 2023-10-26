import os.path
import time
from typing import SupportsFloat, Any, Tuple, Dict
import os
import subprocess
import traceback
from motoko_project.env.env_logs import logger
# import env_logs
import requests
import json
from motoko_project.const import CKPT_DIR

class MotokoEnv():
    def __init__(self, log_path="./logs"):
        self.log_path = log_path
        self.has_reset = False
     
    @classmethod
    async def run_text(cls, code) -> Tuple[str, str]:
        try:
            # We will document_store the result in this dictionary
            namespace = {}
            exec(code, namespace)
            return namespace.get("result", ""), ""
        except Exception:
            # If there is an error in the code, return the error message
            return "", traceback.format_exc()

    @classmethod
    async def run_script(cls, working_directory, additional_python_paths=[], command=[]) -> Tuple[str, str]:
        working_directory = str(working_directory)
        additional_python_paths = [str(path) for path in additional_python_paths]

        # Copy the current environment variables
        env = os.environ.copy()

        # Modify the PYTHONPATH environment variable
        additional_python_paths = [working_directory] + additional_python_paths
        additional_python_paths = ":".join(additional_python_paths)
        env["PYTHONPATH"] = additional_python_paths + ":" + env.get("PYTHONPATH", "")

        # Start the subprocess
        process = subprocess.Popen(
            command, cwd=working_directory, stdout=subprocess.PIPE, stderr=subprocess.PIPE, env=env
        )

        try:
            # Wait for the process to complete, with a timeout
            stdout, stderr = process.communicate(timeout=10)
        except subprocess.TimeoutExpired:
            logger.info("The command did not complete within the given timeout.")
            process.kill()  # Kill the process if it times out
            stdout, stderr = process.communicate()
        return stdout.decode("utf-8"), stderr.decode("utf-8")
    
    # async def run(
    #     self, code, mode="script", code_file_name="", test_code="", test_file_name="", command=[], **kwargs
    # ) -> str:
    #     logger.info(f"Running {' '.join(command)}")
    #     if mode == "script":
    #         outs, errs = await self.run_script(command=command, **kwargs)
    #     elif mode == "text":
    #         outs, errs = await self.run_text(code=code)

    #     logger.info(f"{outs=}")
    #     logger.info(f"{errs=}")

    #     return outs, errs
    
    def render(self):
        raise NotImplementedError("render is not implemented")

    def reset(self) -> Tuple[Any, Dict[str, Any]]:
        self.has_reset = True
        # move back home & doing something
        returned_data = self.check_process()
        
        return returned_data

    def check_process(self):
        cmd = ['conda', 'info', '-e']
        conda_info, conda_err = self.run_script(cmd)
        cmd = ['pwd']
        work_dir, dir_err = self.run_script(cmd)
        
        return  {'conda_info': (conda_info, conda_err)}, {'pwd':(work_dir, dir_err)}
    
    def step(self, sys_msg) -> Tuple[Any, Dict[str, Any]]:
        if not self.has_reset:
            raise RuntimeError("Environment has not been reset yet")
        self.check_process()
        proj_dir = self.get_workspace()
        code = sys_msg[1]['code']
        code_file_name = sys_msg[1]['code_file_name']
        command =  ["python", f"{proj_dir}/{code_file_name}"]
        result_msg, err_msg =self.run_script(
        mode="script",
        command=command,
        working_directory=proj_dir,  # workspace/package_name, will run tests/test_xxx.py here
        # additional_python_paths=[development_code_dir] # workspace/package_name/package_name,
        # import statement inside package code needs this
        )
        returned_data =  {'conda_info': (result_msg, err_msg)}, {}
        return returned_data
