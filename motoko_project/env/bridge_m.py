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
from motoko_project.const import CKPT_DIR, PROJECT_ROOT, WORKSPACE_ROOT

class MotokoEnv():
    def __init__(self, log_path="./logs"):
        self.log_path = log_path
        self.has_reset = True
        self.events = []
        
        # print('ckptdir:', CKPT_DIR)
        os.makedirs(f"{CKPT_DIR}/curriculum/vectordb", exist_ok=True)
        os.makedirs(f"{CKPT_DIR}/action", exist_ok=True)
        os.makedirs(f"{CKPT_DIR}/skill/code", exist_ok=True)
        os.makedirs(f"{CKPT_DIR}/skill/description", exist_ok=True)
        os.makedirs(f"{CKPT_DIR}/skill/vectordb", exist_ok=True)
        
        
    @classmethod
    def run_text(cls, code) -> Tuple[str, str]:
        try:
            # We will document_store the result in this dictionary
            namespace = {}
            exec(code, namespace)
            return namespace.get("result", ""), ""
        except Exception:
            # If there is an error in the code, return the error message
            return "", traceback.format_exc()

    @classmethod
    def run_script(cls, working_directory, additional_python_paths=[], command=[]) -> Tuple[str, str]:
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
    
    @classmethod
    def run(
        self, code, mode="script", code_file_name="", command=[], **kwargs
    ) -> str:
        if mode == "script":
            outs, errs = self.run_script(command=command, **kwargs)
            logger.info(f"Running script:\n{' '.join(command)}")
        elif mode == "text":
            outs, errs = self.run_text(code=code)
            logger.info(f"Running code: \n{code}")

        return outs,errs
    
    def render(self):
        raise NotImplementedError("render is not implemented")

    def reset(self) -> Tuple[Any, Dict[str, Any]]:
        self.has_reset = True
        # move back home & doing something
        returned_data = self.check_process()
        self.events = []
        return returned_data

    def check_process(self):
        cmd = ['conda', 'info', '-e']
        conda_info, conda_err = self.run_script(working_directory=PROJECT_ROOT,command=cmd)
        cmd = ['pwd']
        current_dir, dir_err = self.run_script(working_directory=PROJECT_ROOT,command=cmd)
        cmd = ['ls', f"{CKPT_DIR}"]
        state_dir, dirinfo_err = self.run_script(working_directory=PROJECT_ROOT,command=cmd)
        info = {'conda_info': (conda_info, conda_err), 
                'ckpt_dirs': (state_dir, dirinfo_err),
                'position':(current_dir, dir_err), 
                }
        return 'observe', info
    
    def step(self, sys_msg) -> Tuple[Any, Dict[str, Any]]:
        # logger.info(f"Running python code from message: {sys_msg}")
        if not self.has_reset:
            raise RuntimeError("Environment has not been reset yet")
        # self.check_process()
        mode = sys_msg[1]['mode']
        code_file_name = sys_msg[1]['code_file_name']
        command =  ["python", f"{WORKSPACE_ROOT}/{code_file_name}"]
        result_msg, err_msg =self.run(
        mode = mode,
        command=command,
        working_directory=WORKSPACE_ROOT,  # workspace/package_name, will run tests/test_xxx.py here
        code = sys_msg[1]['code']
        )
        
        cmd = ['pwd']
        current_dir, dir_err = self.run_script(working_directory=PROJECT_ROOT,command=cmd)
        
        info = {'result': (result_msg, err_msg), 
                'health': 20,
                'position':(current_dir, dir_err), 
                # 'completed_tasks': [],
                # 'failed_tasks':[]
                }
        event = ['observe', info]
        if err_msg:
            event[0] = 'onError'
            
        # print('event_by_step:', event)
        self.events.append(event)
        return self.events
