import ast
import re
import os
import time

import motoko_project.utils as U
from langchain.chat_models import ChatOpenAI
from langchain.prompts import SystemMessagePromptTemplate
from langchain.schema import AIMessage, HumanMessage, SystemMessage

from motoko_project.prompts import load_prompt
from motoko_project.control_primitives_context import load_control_primitives_context
from motoko_project.const import CKPT_DIR, PROJECT_ROOT, WORKSPACE_ROOT

class ActionAgent:
    def __init__(
        self,
        model_name="gpt-3.5-turbo",
        temperature=0,
        request_timout=120,
        ckpt_dir="ckpt",
        resume=False,
        chat_log=True,
        execution_error=True,
    ):
        self.ckpt_dir = ckpt_dir
        self.chat_log = chat_log
        self.execution_error = execution_error
        # U.f_mkdir(f"{ckpt_dir}/action")
        if resume:
            print(f"\033[32mLoading Action Agent from {ckpt_dir}/action\033[0m")

        self.llm = ChatOpenAI(
            model_name=model_name,
            temperature=temperature,
            request_timeout=request_timout,
            openai_api_key= os.environ["OPENAI_API_KEY"],
            openai_api_base= os.environ["OPENAI_API_BASE"]
            
        )

    def render_system_message(self, skills=[]):
        system_template = load_prompt("dbot_action_template")
        # FIXME: Hardcoded control_primitives
        base_skills = [
            # open pdf file with pdfplumber 
        ]

        programs = "\n\n".join(load_control_primitives_context(base_skills) + skills)
        response_format = load_prompt("action_response_format")
        system_message_prompt = SystemMessagePromptTemplate.from_template(
            system_template
        )
        system_message = system_message_prompt.format(
            programs=programs, response_format=response_format
        )
        assert isinstance(system_message, SystemMessage)
        return system_message

    def render_human_message(
        self, *, events, code="", task="", context="", critique=""
    ):
        error_messages = []
        result_messages = []
        
        for i, (event_type, event) in enumerate(events):

            if event_type == "onError":
                error_messages.append(event["onError"])
            elif event_type == "observe":
                health = event["health"]
                position = event["position"]
                result = event['result'][0]
                result_messages.append(result)
              
        observation = ""

        if code:
            observation += f"Code from the last round:\n{code}\n"
        else:
            observation += f"Code from the last round: No code in the first round\n\n"

        if self.execution_error:
            if error_messages:
                error = "\n".join(error_messages)
                observation += f"Execution error:\n{error}\n"
            else:
                observation += f"Execution error: No error\n"

        
        if result:
            observation += f"Result from the last round::\n{result}\n"
        else:
            observation += f"Result from the last round:: No error\n"
                
        observation += f"Position: {position}\n"

        observation += f"Task: {task}\n"

        if context:
            observation += f"Context: {context}\n"
        else:
            observation += f"Context: None\n"

        if critique:
            observation += f"Critique: {critique}\n"
        else:
            observation += f"Critique: None\n"

        return HumanMessage(content=observation)

    def find_test_file(self, file_type=('pdf')) -> str:
        search_folder = WORKSPACE_ROOT
        path_list = []
    
        for root, dirs, files in os.walk(search_folder):
            for file in files:
               if file.endswith(file_type):
                   path_list.append(os.path.join(root, file))

        return path_list
    
    def process_ai_message(self, message, lang: str=""):
        assert isinstance(message, AIMessage)

        retry = 3
        error = None
        while retry > 0:
            try:
                code_pattern = rf"```{lang}.*?\s+(.*?)```"
                match = re.search(code_pattern, message.content, re.DOTALL)
                if match:
                    code = match.group(1)
                else:
                    print(f"{code_pattern} not match following text:")
                    print(message)
                
                # raise Exception            
                parsed = code
                tree = ast.parse(code)
                function_names = []
                for node in ast.walk(tree):
                    if isinstance(node, ast.FunctionDef):
                        function_names.append(node.name)
                main_function = function_names[-1]
                
                file_path_list = self.find_test_file(file_type=('pdf'))
                if len(file_path_list) > 0 :
                    file_path = file_path_list[0]
                    exec_code = f"""{main_function}(file_path="{str(file_path)}")"""
                else:
                    print(f"can't find text file in {WORKSPACE_ROOT}:")
                return { "program_code": parsed, 
                         "program_name": main_function,
                         "test_file": file_path, 
                         "exec_code": exec_code,}
            
            except Exception as e:
                retry -= 1
                error = e
                time.sleep(1)
                
        return f"Error parsing action response (before program execution): {error}"

    def summarize_chatlog(self, events):
        # a function of receiving information from env can be arranged here
        return None
    
                        
