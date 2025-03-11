import json
import os
from datetime import datetime
import uuid
import threading

class Core:
    def __init__(self, contract_directory="../store"):
        self.contract_directory = contract_directory
        self.lock = threading.Lock() # lock for thread safety
        if not os.path.exists(self.contract_directory):
            os.makedirs(self.contract_directory)

    def _generate_id(self):
        return str(uuid.uuid4())

    def _get_contract_path(self, contract_id):
        return f"{self.contract_directory}/{contract_id}.json"

    def create_contract(self, creator_id, creator_name, title, description, collaborators=None):
        contract_id = self._generate_id()
        creation_date = datetime.now().isoformat()
        
        contract = {
            "metadata": {
                "contract_id": contract_id,
                "creator_id": creator_id,
                "creator_name": creator_name,
                "title": title,
                "description": description,
                "creation_date": creation_date,
                "collaborators": collaborators if collaborators else []
            },
            "clauses": []
        }
        
        self.save_contract(contract)
        return contract_id

    def open_contract(self, contract_id):
        contract_path = self._get_contract_path(contract_id)
        if not os.path.exists(contract_path):
            return None
        
        try:
            with open(contract_path, "r") as f:
                return json.load(f)
        except (json.JSONDecodeError, FileNotFoundError):
            return None

    def save_contract(self, contract):
        contract_path = self._get_contract_path(contract["metadata"]["contract_id"])
        with self.lock:
            with open(contract_path, "w") as f:
                json.dump(contract, f, indent=4)

    def add_clause(self, contract_id, short_title, full_text, publisher):
        contract = self.open_contract(contract_id)
        if not contract:
            return False

        clause_id = self._generate_id()
        new_clause = {
            "clause_id": clause_id,
            "short_title": short_title,
            "versions": [{
                "date": datetime.now().isoformat(),
                "full_text": full_text,
                "publisher": publisher
            }]
        }
        contract["clauses"].append(new_clause)
        self.save_contract(contract)
        return True

    def update_clause(self, contract_id, clause_id, full_text, publisher):
        contract = self.open_contract(contract_id)
        if not contract:
            return False

        for clause in contract["clauses"]:
            if clause["clause_id"] == clause_id:
                clause["versions"].insert(0, {
                    "date": datetime.now().isoformat(),
                    "full_text": full_text,
                    "publisher": publisher
                })
                self.save_contract(contract)
                return True
        return False

    def add_collaborator(self, contract_id, collaborator_id):
        contract = self.open_contract(contract_id)
        if not contract:
            return False

        if collaborator_id not in contract["metadata"]["collaborators"]:
            contract["metadata"]["collaborators"].append(collaborator_id)
            self.save_contract(contract)
            return True
        return False

    def remove_collaborator(self, contract_id, collaborator_id):
        contract = self.open_contract(contract_id)
        if not contract:
            return False

        if collaborator_id in contract["metadata"]["collaborators"]:
            contract["metadata"]["collaborators"].remove(collaborator_id)
            self.save_contract(contract)
            return True
        return False

    def delete_clause(self, contract_id, clause_id):
        contract = self.open_contract(contract_id)
        if not contract:
            return False
        
        contract["clauses"] = [clause for clause in contract["clauses"] if clause["clause_id"] != clause_id]
        self.save_contract(contract)
        return True

    def delete_contract(self, contract_id):
        contract_path = self._get_contract_path(contract_id)
        if os.path.exists(contract_path):
            os.remove(contract_path)
            return True
        return False

    def list_contracts(self, creator_id=None, collaborator_id=None):
        contracts = []
        for filename in os.listdir(self.contract_directory):
            if filename.endswith(".json"):
                contract_id = filename[:-5]
                contract = self.open_contract(contract_id)
                if contract:
                    if creator_id and contract["metadata"]["creator_id"] != creator_id:
                        continue
                    if collaborator_id and collaborator_id not in contract["metadata"]["collaborators"]:
                        continue
                    contracts.append(contract["metadata"])
        return contracts