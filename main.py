from flask import Flask, request, jsonify
from flask_cors import CORS


from core import Core
from database import Database

app = Flask(__name__)
CORS(app)

contract_manager = Core()
database=Database()

@app.route('/create_contract', methods=['POST'])
def create_contract():
    data = request.get_json()
    #get user profile
    profile = database.user_profile(data['user_id'])
    if 'name' not in profile:
        return jsonify({'error': 'Account does not exist'}), 401
    if not data or 'user_id' not in data or 'title' not in data or 'description' not in data:
        return jsonify({'error': 'Missing required fields'}), 400

    contract_id = contract_manager.create_contract(
        creator_id=data['user_id'],
        creator_name=profile['name'],
        title=data['title'],
        description=data['description'],
    )
    add=database.create_contract(contract_id, data['title'], data['user_id'])
    return jsonify({'contract_id': contract_id}), 201

@app.route('/contracts/<contract_id>', methods=['GET'])
def get_contract(contract_id):
    contract = contract_manager.open_contract(contract_id)
    if not contract:
        return jsonify({'error': 'Contract not found'}), 404
    return jsonify(contract)

@app.route('/contracts/<contract_id>/clauses', methods=['POST'])
def add_clause(contract_id):
    data = request.get_json()
    if not data or 'short_title' not in data or 'full_text' not in data or 'user_id' not in data:
        return jsonify({'error': 'Missing required fields'}), 400

    if contract_manager.add_clause(
        contract_id=contract_id,
        short_title=data['short_title'],
        full_text=data['full_text'],
        publisher=data['user_id']
    ):
        return jsonify({'message': 'Clause added'}), 201
    else:
        return jsonify({'error': 'Contract not found'}), 404

@app.route('/contracts/<contract_id>/clauses/<clause_id>', methods=['PUT'])
def update_clause(contract_id, clause_id):
    data = request.get_json()
    if not data or 'full_text' not in data or 'user_id' not in data:
        return jsonify({'error': 'Missing required fields'}), 400

    if contract_manager.update_clause(
        contract_id=contract_id,
        clause_id=clause_id,
        full_text=data['full_text'],
        publisher=data['user_id']
    ):
        return jsonify({'message': 'Clause updated'}), 200
    else:
        return jsonify({'error': 'Contract or clause not found'}), 404

@app.route('/contracts/<contract_id>/collaborators', methods=['POST'])
def add_collaborator(contract_id):
    data = request.get_json()
    if not data or 'collaborator_id' not in data:
        return jsonify({'error': 'Missing collaborator_id'}), 400

    if contract_manager.add_collaborator(contract_id, data['collaborator_id']):
        return jsonify({'message': 'Collaborator added'}), 200
    else:
        return jsonify({'error': 'Contract not found or collaborator already exists'}), 404

@app.route('/contracts/<contract_id>/collaborators/<collaborator_id>', methods=['DELETE'])
def remove_collaborator(contract_id, collaborator_id):
    if contract_manager.remove_collaborator(contract_id, collaborator_id):
        return jsonify({'message': 'Collaborator removed'}), 200
    else:
        return jsonify({'error': 'Contract or collaborator not found'}), 404

@app.route('/contracts/<contract_id>/clauses/<clause_id>', methods=['DELETE'])
def delete_clause(contract_id, clause_id):
    if contract_manager.delete_clause(contract_id, clause_id):
        return jsonify({'message': 'Clause deleted'}), 200
    else:
        return jsonify({'error': 'Contract or clause not found'}), 404

@app.route('/contracts/<contract_id>', methods=['DELETE'])
def delete_contract(contract_id):
    if contract_manager.delete_contract(contract_id):
        return jsonify({'message': 'Contract deleted'}), 200
    else:
        return jsonify({'error': 'Contract not found'}), 404

@app.route('/contracts', methods=['GET'])
def list_contracts():
    creator_id = request.args.get('creator_id')
    collaborator_id = request.args.get('collaborator_id')
    contracts = contract_manager.list_contracts(creator_id, collaborator_id)
    return jsonify(contracts)

if __name__ == '__main__':
    app.run(host='0.0.0.0',port='8081')