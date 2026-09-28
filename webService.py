import os
import json
import uuid
import random
import string
from copy import deepcopy
from pathlib import Path

SCRIPT_DIR = Path(__file__).resolve().parent
PROJECT_DIR = SCRIPT_DIR.parent

# =========================
# Générateurs
# =========================
def gen_uuid(file_name=None):
    if file_name:
        base_name = os.path.splitext(file_name)[0]  # TNR-020
        random_uuid = str(uuid.uuid4())             # 00defb96-ac71-4831-9f0a-ced10900bc82

        prefix = random_uuid[:27]                   # 00defb96-ac71-4831-9f0a-ced1090
        return f"{prefix}-{base_name}"              # 00defb96-ac71-4831-9f0a-ced1090-TNR-020

    return str(uuid.uuid4())

def gen_system_id():
    return "System" + ''.join(random.choices(string.ascii_letters + string.digits, k=30))

def gen_person_id():
    return "Person" + ''.join(random.choices(string.ascii_letters + string.digits, k=58))

def gen_contract_id():
    return ''.join(random.choices(string.ascii_lowercase, k=9))

def gen_address_id():
    return ''.join(random.choices('abcdef' + string.digits, k=8))  # type: 530f83a0

def gen_usage():
    return ''.join(random.choices(string.ascii_lowercase, k=10))

# =========================
# Enrichissement lié
# =========================
def enrich_linked_json(json_list, file_name=None):
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
        # lien entre events
        # =========================
        if data.get("payload", {}).get("customerReferences"):
            data["payload"]["customerReferences"]["sourceReference"]["systemId"] = shared_system_id
            data["payload"]["customerReferences"]["sourceReference"]["systemPersonId"] = shared_person_id

        if data.get("payload", {}).get("customerSourceReference"):
            data["payload"]["customerSourceReference"]["systemId"] = shared_system_id
            data["payload"]["customerSourceReference"]["systemPersonId"] = shared_person_id

        # =========================
        # contactMediums
        # =========================
        if data.get("payload", {}).get("contactMediums"):

            for cm in data["payload"]["contactMediums"]:

                # contract usages
                if cm.get("contactMediumContractsUsages"):
                    for usage in cm["contactMediumContractsUsages"]:

                        # contractId
                        if "contractId" in usage and not usage["contractId"]:
                            usage["contractId"] = gen_contract_id()

                        # contactMediumUsages
                        if "contactMediumUsages" in usage:
                            usage["contactMediumUsages"] = [
                                gen_usage() if not u else u
                                for u in usage["contactMediumUsages"]
                            ]

                # addresses
                for address_type in ["mainAddress", "fiscalAddress", "contactAddress"]:
                    if cm.get(address_type):
                        if "adressId" in cm[address_type] and not cm[address_type]["adressId"]:
                            cm[address_type]["adressId"] = gen_address_id()

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
        obj, idx = decoder.raw_decode(content, idx)
        objects.append(obj)

        while idx < len(content) and content[idx].isspace():
            idx += 1

    return objects

# =========================
# MAIN
# =========================
def process_folder(input_folder, output_json, output_ndjson):

    all_data = []

    for filename in sorted(os.listdir(input_folder)):
        if filename.endswith(".json"):
            path = os.path.join(input_folder, filename)

            with open(path, "r", encoding="utf-8") as f:
                content = f.read().strip()

            json_objects = read_multi_json(content)

            # filename = TNR-020.json
            enriched = enrich_linked_json(json_objects, file_name=filename)

            all_data.extend(enriched)

    # =========================
    # 1. JSON ARRAY OUTPUT
    # =========================
    with open(output_json, "w", encoding="utf-8") as f:
        json.dump(all_data, f, indent=4, ensure_ascii=False)

    # =========================
    # 2. NDJSON OUTPUT
    # =========================
    with open(output_ndjson, "w", encoding="utf-8") as f:
        for obj in all_data:
            f.write(json.dumps(obj, ensure_ascii=False) + "\n")

    print("JSON + NDJSON générés")

# =========================
# EXECUTION
# =========================
if __name__ == "__main__":
    process_folder(
        input_folder=PROJECT_DIR / "input_contactmedium",
        output_json=PROJECT_DIR / "json" / "output_jdd_contact.json",
        output_ndjson=PROJECT_DIR / "output" / "output_nd_contact.json"
    )
