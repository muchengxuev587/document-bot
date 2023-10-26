from motoko_project import Motoko


# You can also use mc_port instead of azure_login, but azure_login is highly recommended
openai_api_key = "sk-lAmlRoBhqOiU7Zz82aBeAc84969d4e3cB338326cD5A0855c"
openai_base = "https://api.openai.com/v1"
motoko = Motoko(
    openai_api_key=openai_api_key,
    openai_base = openai_base
)

# start lifelong learning
motoko.learn()