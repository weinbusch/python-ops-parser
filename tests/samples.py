import os

import epo_ops
from python_ops_client_wrapper import ops_client


SAMPLE_DIR = "tests/samples"

SAMPLES = [
    "00102678",
    "99203729",
    "register_search",
]


def register_search(client, cql):
    response = client.register_search(cql)
    return response.text


def register(client, application_number):
    response = client.register(
        reference_type="application",
        input=epo_ops.models.Epodoc(number=f"EP{application_number}"),
        constituents=["biblio", "events", "procedural-steps"],
    )
    return response.text


def save_data(filename, data):
    path = os.path.join(SAMPLE_DIR, filename)
    with open(path, "w", encoding="utf-8") as f:
        f.write(data)


def download():
    client = ops_client()

    if not os.path.isdir(SAMPLE_DIR):
        os.makedirs(SAMPLE_DIR)

    for name in SAMPLES:
        if name == "register_search":
            data = register_search(client, "pa=bosch and pd=2015")
        else:
            data = register(client, name)
        save_data(f"{name}.xml", data)
        print(f"downloaded {name}")


if __name__ == "__main__":
    print("Downloading sample data from EPO OPS ...")
    download()
