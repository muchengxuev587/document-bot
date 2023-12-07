from motoko_project import Motoko


# You can also use mc_port instead of azure_login, but azure_login is highly recommended
openai_api_key = ""
openai_base = "https://api.ezchat.top/v1"
motoko = Motoko(
    openai_api_key=openai_api_key,
    openai_base = openai_base
)

# start lifelong learning
motoko.learn()
