import sqlite3
import random
import json
from datetime import datetime, timedelta
import hashlib

class Database:
    def __init__(self):
        self.db_path = '../datastore.db'
        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()
        
        # Use Caserover's users table in datastore.db

        # Create Contracts table
        cursor.execute('''CREATE TABLE IF NOT EXISTS contracts
                                (contract_id TEXT, title TEXT, creator_id TEXT, status TEXT, created_at TEXT)''')
        # Create Permissions Table
        cursor.execute('''CREATE TABLE IF NOT EXISTS permissions
                                (permission_id TEXT, contract_id TEXT, user_id TEXT, permission_type TEXT)''')
        #Create Invitations Table
        cursor.execute('''CREATE TABLE IF NOT EXISTS invitations
                                (invitation_id TEXT, contract_id TEXT, email TEXT, role TEXT, status TEXT, created_at TEXT)''')

        conn.commit()
        conn.close()

    # Get a user's profile based on the user_id
    def user_profile(self, user_id):
        '''Fetch user profile from the database.'''
        try:
            with sqlite3.connect(self.db_path) as conn:
                cursor = conn.cursor()
                cursor.execute("SELECT * FROM users WHERE user_id=?", (user_id,))
                user = cursor.fetchone()
                if user:
                    # Base response
                    response = { "status": "success", "name": user[1], "email": user[2], "phone": user[3], "user_type": user[4], "code": user[5], "status": user[7], "next_date": user[8], "isadmin": user[10]}

                    # Add lawfirm name if user type is "org"
                    if user[4] == "org":
                        response["lawfirm_name"] = user[6]
                    
                    return response
                else:
                    return {"status": "User does not exist"}
        except Exception as e:
            print("Error on loading profile: " + str(e))
            return {"status": "Error: " + str(e)}

        
    def create_contract(self, contract_id, title, creator_id, status="Draft"):
        '''Create a new contract in the database.'''
        created_at = datetime.now().isoformat()
        try:
            with sqlite3.connect(self.db_path) as conn:
                cursor = conn.cursor()
                cursor.execute('INSERT INTO contracts (contract_id, title, creator_id, status, created_at) VALUES (?, ?, ?, ?, ?)', 
                                (contract_id, title, creator_id, status, created_at))
                conn.commit()
                return True
        except sqlite3.Error as e:
            print(f"Error Creating contract: {e}")
            return False
            
    def add_permission(self, permission_id, contract_id, user_id, permission_type):
        try:
            with sqlite3.connect(self.db_path) as conn:
                cursor = conn.cursor()
                cursor.execute('INSERT INTO permissions (permission_id, contract_id, user_id, permission_type) VALUES (?, ?, ?, ?)',
                                (permission_id, contract_id, user_id, permission_type))
                conn.commit()
                return True
        except sqlite3.Error as e:
            print (f"An error occured: {e}")
            return False
    
    def add_invitation(self, invitation_id, contract_id, email, role, status, created_at):
        try:
            with sqlite3.connect(self.db_path) as conn:
                cursor = conn.cursor()
                cursor.execute('INSERT INTO invitations(invitation_id, contract_id, email, role, status, created_at) VALUES(?, ?, ?, ?, ?, ?)',
                                (invitation_id, contract_id, email, role, status, created_at))
                conn.commit()
                return True
        except sqlite3.Error as e:
            print (f"An error occured:{e}")
            return False
            
    def get_contract(self, contract_id):
        try: 
            with sqlite3.connect(self.db_path) as conn:
                cursor = conn.cursor()
                cursor.execute('SELECT * FROM contracts WHERE contract_id = ?', (contract_id,))
                # Fetch the contract details
                contract = cursor.fetchone()
            return contract
        except sqlite3.Error as e:
            print(f"An error occured: {e}")
            return None
            
    def get_permissions(self, contract_id):
        try:
            with sqlite3.connect(self.db_path) as conn:
                cursor = conn.cursor()
                cursor.execute('SELECT * FROM permissions WHERE contract_id = ?', (contract_id,))
                
                # Fetch all permissions for the contract
                permissions = cursor.fetchall()
            return permissions
        except sqlite3.Error as e:
            print(f"An error occcured: {e}")
            return []
            
    def get_invitations(self, contract_id):
        try:
            with sqlite3.connect(self.db_path) as conn:
                cursor = conn.cursor()
                # Fetch all invitations for the contract
                cursor.execute('SELECT * FROM invitations WHERE contract_id = ?', (contract_id,))
                invitations = cursor.fetchall()
            return invitations
        except sqlite3.Error as e:
            print(f"An error occured: {e}")
            return []
            