import PyPDF2
from PyPDF2 import PdfFileReader
import ast

def extract_function_names(code):
    tree = ast.parse(code)
    function_names = []

    for node in ast.walk(tree):
        if isinstance(node, ast.FunctionDef):
            function_names.append(node.name)

    return function_names



def check_page_num(filepath):
# Creating a pdf file object.
    pdf = open(filepath, "rb")
    
    # Creating pdf reader object.
    pdf_reader = PyPDF2.PdfFileReader(pdf)
    
    # Checking total number of pages in a pdf file.
    print("Total number of Pages:", pdf_reader.numPages)
    
    # Return the number of pages to the caller
    return pdf_reader.numPages 

#choose a file from local folder to check the result
file_path = "/home/bsz/data/chatglm/document_agent/ckpt/pdf_files/202303181737070649.pdf"
check_page_num(file_path)

code = '''
def foo():
    pass

def bar():
    pass
'''

function_names = extract_function_names(code)
print(function_names)

