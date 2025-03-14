from flask import Flask, request, jsonify, send_file
from flask_cors import CORS
from core import Core
from database import Database
import os

app = Flask(__name__)
CORS(app)

contract_manager = Core()
database=Database()

# Pinging the system
@app.route('/ping', methods=['GET'])
def ping():
    return {'status': 'running'}

@app.route('/create_contract', methods=['POST'])
def create_contract():
    data = request.get_json()
    # Input validation
    if not data:
        return jsonify({'error': 'No data provided'}), 400
    if 'user_id' not in data:
        return jsonify({'error': 'Missing user_id field'}), 400
    if 'title' not in data:
        return jsonify({'error': 'Missing title field'}), 400
    if 'description' not in data:
        return jsonify({'error' : 'Missing description field'}), 400
    
    # Get user profile
    profile = database.user_profile(data['user_id'])
    if 'name' not in profile:
        return jsonify({'error': 'Account does not exist'}), 401
    
    # Updated this for detailed error messages
    # if not data or 'user_id' not in data or 'title' not in data or 'description' not in data:
    #     return jsonify({'error': 'Missing required fields'}), 400

    contract_id = contract_manager.create_contract(
        creator_id=data['user_id'],
        creator_name=profile['name'],
        title=data['title'],
        description=data['description'],
    )
    # Store in databse and check result
    add=database.create_contract(contract_id, data['title'], data['user_id'])
    if not add:
        return jsonify({'error': 'Failed to create contract'}), 500
    
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

    # Check if user has permission to add clauses (creator or editor)
    contract = contract_manager.open_contract(contract_id)
    if not contract:
        return jsonify({'error': 'Contract not found'}), 404
    
    user_id = data['user_id']
    if contract['metadata']['creator_id'] != user_id:
        has_permission = False
        for collab in contract['metadata']['collaborators']:
            if collab["user_id"] == user_id and collab['role'] == 'Editor':
                has_permission = True
                break
        if not has_permission:
            return jsonify({'error': 'Permission denied. Only creator or editors can add clauses'}), 403
    
    clause = contract_manager.add_clause(
        contract_id=contract_id,
        short_title=data['short_title'],
        full_text=data['full_text'],
        publisher=data['user_id']
    )
    
    if clause:
        return jsonify({
            'message': 'Clause added',
            'clause_id': clause['clause_id'],
            'short_title': clause['short_title'],
            }), 201
    else:
        return jsonify({'error': 'Failed to add clause'}), 404

@app.route('/contracts/<contract_id>/clauses/<clause_id>', methods=['PUT'])
def update_clause(contract_id, clause_id):
    data = request.get_json()
    if not data or 'full_text' not in data or 'user_id' not in data:
        return jsonify({'error': 'Missing required fields'}), 400

    # Open contract
    contract = contract_manager.open_contract(contract_id)
    if not contract: 
        return jsonify ({'error': "Contract not found"}), 404
            
    user_id = data['user_id']
    
    # Check if user has permission to update clauses (creator or editor)
    if contract['metadata']['creator_id'] != user_id:
        has_permission = False
        for collab in contract['metadata']['collaborators']:
            if collab["user_id"] == user_id and collab['role'] == 'Editor':
                has_permission = True
                break
        if not has_permission:
            return jsonify({'error': 'Permission denied. Only creator or editors can update clauses'}), 403
    
    # Find publisher name from contract metadata
    publisher_name = "Unknown"
    if contract['metadata']['creator_id'] == user_id:
        publisher_name = contract['metadata']['creator_name']
    else:
        for collab in contract['metadata']['collaborators']:
            if collab["user_id"] == user_id:
                publisher_name = collab['name']
                break
    
    # Update Clause
    if contract_manager.update_clause(
        contract_id=contract_id,
        clause_id=clause_id,
        full_text=data['full_text'],
        publisher_id=data['user_id'],
        publisher_name= publisher_name,
        short_title=data.get('short_title') # For optional renaming
    ):
        return jsonify({
            'message': 'Clause updated successfully',
            'publisher_name': publisher_name}), 200
    else:
        return jsonify({'error': 'Contract or clause not found'}), 404
    
# Get all the clauses for a contract
@app.route('/contracts/<contract_id>/clauses', methods=['GET'])
def get_clauses(contract_id):
    clauses = contract_manager.get_clauses(contract_id)
    if not clauses:
        return jsonify({'error': 'Contract not found'}), 404
    return jsonify(clauses), 200

# Add collaborator using email
@app.route('/contracts/<contract_id>/collaborators', methods=['POST'])
def add_collaborator(contract_id):
    data = request.get_json()
    if not data or 'email' not in data or 'role' not in data or 'user_id' not in data:
        return jsonify({'error': 'Missing required fields'}), 400

    # Validate role
    valid_roles = ['Editor', 'Viewer', "Approver"]
    if data['role'] not in valid_roles:
        return jsonify({'error': 'Invalid role. Must be one of: ' + ', '.join(valid_roles)}), 400
    
    # Check if the email exists in the database
    if not database.email_exists(data['email']):
        return jsonify({'error': 'Email does not exist'}), 404
    
    # Get user profile by email
    collab_profile = database.get_user_by_email(data['email'])
    if 'user_id' not in collab_profile:
        return jsonify({'error': 'User not found'}), 500
    
    # Prepare collaborator data
    collaborator_data = {
        'user_id': collab_profile['user_id'],
        'name': collab_profile['name'],
        'email': data['email'],
        'role': data['role'],
        
    }
    
    success, message = contract_manager.add_collaborator(
        contract_id = contract_id,
        collaborator_data = collaborator_data,
        role = data['role'],
        added_by = data['user_id']
    )
    
    if success:
        db_success = database.add_role(collab_profile['user_id'], contract_id, data['role'])
        if not db_success:
            return jsonify({'error': 'Failed to add role in database'}), 500 
        
        return jsonify({'message': message, 'collaborator': collaborator_data}), 200
    else:
        return jsonify({'error': message}), 400

@app.route('/contracts/<contract_id>/collaborators/<collaborator_id>', methods=['DELETE'])
def remove_collaborator(contract_id, collaborator_id):
    data = request.get_json()
    if not data or 'user_id' not in data:
        return jsonify({'error': 'Missing user_id field'}), 400
        
    success, message = contract_manager.remove_collaborator(
        contract_id=contract_id,
        collaborator_id=collaborator_id,
        removed_by=data['user_id']
    )
    
    if success:
        db_success = database.delete_role(collaborator_id, contract_id)
        if not db_success:
            return jsonify({'error': 'Failed to remove role in database'}), 500
        
        return jsonify({'message': message}), 200
    else:
        return jsonify({'error': message}), 404
    
@app.route('/contracts/<contract_id>/collaborators/<collaborator_id>', methods=['PUT'])
def update_role(contract_id, collaborator_id):
    data = request.get_json()
    if not data or 'new_role' not in data or 'user_id' not in data:
        return jsonify({'error': 'Missing required fields'}), 400
    
    # Validate role
    valid_roles = ['Editor', 'Viewer', 'Approver']
    if data['new_role'] not in valid_roles:
        return jsonify({'error': 'Invalid role. Must be one of: ' + ', '.join(valid_roles)}), 400
    
    # Open the contract
    contract = contract_manager.open_contract(contract_id)
    if not contract:
        return jsonify({'error': 'Contract not found'}), 404
    
    # Update role
    success, message = contract_manager.update_role(contract_id, collaborator_id, data['new_role'], data['user_id'] )
    if not success:
        return jsonify({'error': message}), 400
    
    # Update role in databse
    db_success = database.update_role(collaborator_id, contract_id, data['new_role'])
    if not db_success:
        return jsonify({'error': 'Failed to update role in database'}), 500
    
    return jsonify({'message': 'Role updated successfully'}), 200
    
@app.route('/contracts/<contract_id>/clauses/<clause_id>/comments', methods=['POST'])
def add_comment(contract_id, clause_id):
    data = request.get_json()
    if not data or 'user_id' not in data or 'comment' not in data:
        return jsonify({'error': 'Missing required fields'}), 400
        
    # Get user profile for the name
    profile = database.user_profile(data['user_id'])
    if 'name' not in profile:
        return jsonify({'error': 'User not found'}), 404
        
    success, result = contract_manager.add_comment(
        contract_id=contract_id,
        clause_id=clause_id,
        user_id=data['user_id'],
        email= profile['email'],
        name=profile['name'],
        comment_text=data['comment']
    )
    
    if success:
        return jsonify({'message': 'Comment added', 'comment_id': result}), 201
    else:
        return jsonify({'error': result}), 400

@app.route('/contracts/<contract_id>/clauses/<clause_id>/comments', methods=['GET'])
def get_comments(contract_id, clause_id):
    comments = contract_manager.get_comments(contract_id, clause_id)
    
    if comments is None:
        return jsonify({'error': 'Contract or clause not found'}), 404
        
    return jsonify({'comments': comments}), 200

@app.route('/contracts/<contract_id>/clauses/<clause_id>/comments/<comment_id>', methods=['DELETE'])
def delete_comment(contract_id, clause_id, comment_id):
    data = request.get_json()
    if not data or 'user_id' not in data:
        return jsonify({'error': 'Missing user_id field'}), 400
        
    success, message = contract_manager.delete_comment(
        contract_id=contract_id,
        clause_id=clause_id,
        comment_id=comment_id,
        user_id=data['user_id']
    )
    
    if success:
        return jsonify({'message': message}), 200
    else:
        return jsonify({'error': message}), 400

@app.route('/contracts/<contract_id>/clauses/<clause_id>', methods=['DELETE'])
def delete_clause(contract_id, clause_id):
    if contract_manager.delete_clause(contract_id, clause_id):
        return jsonify({'message': 'Clause deleted'}), 200
    else:
        return jsonify({'error': 'Contract or clause not found'}), 404

@app.route('/contracts/<contract_id>', methods=['DELETE'])
def delete_contract(contract_id):
    data = request.get_json('contract_id')
    if not data or 'user_id' not in data:
        return jsonify({'error': 'Missing user_id field'}), 400
    
    # Open contract to get creator_id
    contract = contract_manager.open_contract(contract_id)
    if not contract:
        return jsonify({'error': 'Contract not found'}), 404
    
    creator_id = contract['metadata']['creator_id']
    if creator_id != data["user_id"]:
        return jsonify({'error': 'You are not authorized to delete this contract'}), 403
    
    success = contract_manager.delete_contract(contract_id)
    if success:
        # Remove from database
        db_success = database.delete_contract(contract_id)
        if not db_success:
            return jsonify({'error': 'Failed to delete contract from database'}), 500
        
        return jsonify({'message': 'Contract deleted successfully'}), 200
    else:
        return jsonify({'error': 'Contract not found'}), 404

@app.route('/contracts', methods=['GET'])
def list_contracts():
    user_id = request.args.get('user_id')
    collaborator_id = request.args.get('collaborator_id')
    contracts = contract_manager.list_contracts(user_id, collaborator_id)
    return jsonify(contracts)

@app.route('/users/<user_id>/contracts', methods=['GET'])
def get_user_contracts(user_id):
    '''List all contracts owned by a user'''
    contracts = database.get_user_contracts(user_id)
    return jsonify([
        {"contract_id": row[0], "title": row[1], "status": row[2]}
        for row in contracts
    ]), 200
    
@app.route('/users/<user_id>/collaborations', methods=['GET'])
def get_user_collaborations(user_id):
    '''List all contracts a user is collaborating on'''
    collaborations = database.get_user_collaborations(user_id)
    
    if not collaborations:
        return jsonify({'message': 'No collaborations found'}), 200
    
    return jsonify(collaborations), 200

@app.route('/contracts/<contract_id>/clauses/<clause_id>/reorder', methods=['PUT'])
def reorder_clauses(contract_id, clause_id):
    data = request.get_json()
    if not data or 'new_index' not in data or 'user_id' not in data:
        return jsonify({'error': 'Missing required fields'}), 400
    
    # Open contract
    contract = contract_manager.open_contract(contract_id)
    if not contract:
        return jsonify({'error': 'Contract not found'}), 404
    
    # Check if user has permission to reorder clauses (creator or editor)
    user_id = data['user_id']
    if contract ['metadata']['creator_id'] != user_id:
        has_permission = any(
            collab['user_id'] == user_id and collab['role'] == 'Editor'
            for collab in contract['metadata']['collaborators']
        )
        if not has_permission:
            return jsonify({'error': 'Permission denied. Only creator or editors can reorder clauses'}), 403
        
    # Update clause position
    success, message = contract_manager.move_clause(contract_id, clause_id, data['new_index'])
    if not success:
        return jsonify({'error': message}), 400
        
    return jsonify({'message': 'Clause moved successfully'}), 200

@app.route('/contracts/<contract_id>/approve', methods=['PUT'])
def approve_contract(contract_id):
    data = request.get_json()
    if not data or 'user_id' not in data:
        return jsonify({'error': 'Missing user_id field'}), 400
    
    success, message = contract_manager.approve_contract(contract_id, data["user_id"] )
    if not success:
        return jsonify({'error': message}), 403
    
    # Update db
    db_success= database.update_contract_status(contract_id, "Approved")
    if not db_success:
        return jsonify({'error': message}), 403
    
    return jsonify({'message': 'Contract approved successfully'}), 200

@app.route('/contracts/<contract_id>/export', methods =['GET'])
def export_contract(contract_id):
    '''Generate and download a DOCX version of a contract'''
    docx_path, message = contract_manager.convert_to_docx(contract_id)
    
    if not docx_path:
        return jsonify({'error': message}), 404
    
    return jsonify({'message': 'DOCX file generated successfully', 'file_path': docx_path}), 200
    
    # return send_file(docx_path, as_attachment=True)

if __name__ == '__main__':
    app.run(host='0.0.0.0',port='8081')