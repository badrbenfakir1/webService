import os
import json
import uuid
import random
import string
from pathlib import Path


# =========================
# Chemins du projet
# =========================

SCRIPT_DIR = Path(__file__).resolve().parent
PROJECT_DIR = SCRIPT_DIR.parent


# =========================
# Générateurs
# =========================

def gen_uuid(file_name=None):
    if file_name:
        base_name = os.path.splitext(file_name)[0]
        random_uuid = str(uuid.uuid4())

        prefix = random_uuid[:27]

        return f"{prefix}-{base_name}"

    return str(uuid.uuid4())


def gen_system_id():
    return "System" + ''.join(
        random.choices(
            string.ascii_letters + string.digits,
            k=30
        )
    )


def gen_person_id():
    return "Person" + ''.join(
        random.choices(
            string.ascii_letters + string.digits,
            k=58
        )
    )


def gen_contract_id():
    return ''.join(
        random.choices(
            string.ascii_lowercase,
            k=9
        )
    )


# =========================
# Enrichissement lié
# =========================

def enrich_linked_json(json_list, file_name=None):

    # Un seul systemId et un seul systemPersonId
    # pour tous les événements du même TNR.

    shared_system_id = gen_system_id()
    shared_person_id = gen_person_id()

    enriched_list = []

    for data in json_list:

        # =========================
        # metadata
        # =========================

        if data.get("metadata"):
            data["metadata"]["id"] = gen_uuid(file_name)

        # =========================
        # customerReferences
        # =========================

        if data.get("payload", {}).get("customerReferences"):

            source_reference = data["payload"][
                "customerReferences"
            ].get("sourceReference")

            if source_reference:

                source_reference["systemId"] = shared_system_id
                source_reference["systemPersonId"] = shared_person_id

        # =========================
        # customerSourceReference
        # =========================

        if data.get("payload", {}).get(
            "customerSourceReference"
        ):

            customer_source_reference = data["payload"][
                "customerSourceReference"
            ]

            customer_source_reference["systemId"] = shared_system_id
            customer_source_reference["systemPersonId"] = shared_person_id

        # =========================
        # contractRoles
        # =========================

        if data.get("payload", {}).get("contractRoles"):

            for role in data["payload"]["contractRoles"]:

                # Si contractId existe et est vide,
                # on génère un contractId.

                if "contractId" in role and not role["contractId"]:

                    role["contractId"] = gen_contract_id()

        enriched_list.append(data)

    return enriched_list


# =========================
# Lecture JSON multiple objets
# =========================

def read_multi_json(content):

    decoder = json.JSONDecoder()
    idx = 0
    objects = []

    while idx < len(content):

        obj, idx = decoder.raw_decode(
            content,
            idx
        )

        objects.append(obj)

        while idx < len(content) and content[idx].isspace():
            idx += 1

    return objects


# =========================
# MAIN
# =========================

def process_folder(
    input_folder,
    output_json,
    output_ndjson
):

    all_data = []

    for filename in sorted(os.listdir(input_folder)):

        if filename.endswith(".json"):

            path = os.path.join(
                input_folder,
                filename
            )

            print(f"Traitement : {filename}")

            with open(
                path,
                "r",
                encoding="utf-8"
            ) as f:

                content = f.read().strip()

            # Lecture des différents objets JSON
            # présents dans le TNR.

            json_objects = read_multi_json(content)

            # Enrichissement des données
            # avec les règles contractRoles.

            enriched = enrich_linked_json(
                json_objects,
                file_name=filename
            )

            # Ajouter les événements du TNR
            # à la liste globale.

            all_data.extend(enriched)

    # =========================
    # 1. JSON ARRAY OUTPUT
    # =========================

    with open(
        output_json,
        "w",
        encoding="utf-8"
    ) as f:

        json.dump(
            all_data,
            f,
            indent=4,
            ensure_ascii=False
        )

    # =========================
    # 2. NDJSON OUTPUT
    # =========================

    with open(
        output_ndjson,
        "w",
        encoding="utf-8"
    ) as f:

        for obj in all_data:

            f.write(
                json.dumps(
                    obj,
                    ensure_ascii=False
                ) + "\n"
            )

    print("JSON + NDJSON générés")


# =========================
# EXECUTION
# =========================

if __name__ == "__main__":

    process_folder(
        input_folder=PROJECT_DIR / "inputcontractrole.added",

        output_json=PROJECT_DIR
        / "json"
        / "output_jdd_contractrole.json",

        output_ndjson=PROJECT_DIR
        / "output"
        / "output_nd_contractrole.json"
    )
