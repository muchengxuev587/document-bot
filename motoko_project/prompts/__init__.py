import pkg_resources
import motoko_project.utils as U


def load_prompt(prompt):
    package_path = pkg_resources.resource_filename("motoko_project", "")
    return U.load_text(f"{package_path}/prompts/{prompt}.txt")
