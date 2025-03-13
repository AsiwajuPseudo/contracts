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
        # # Create Permissions Table
        cursor.execute('''CREATE TABLE IF NOT EXISTS permissions
                                (contract_id TEXT, user_id TEXT, role TEXT)''')
        #Create Invitations Table
        '''Invitations to be implemented in later versions, for now we are just adding collaborators with their role or priviledge'''
        # cursor.execute('''CREATE TABLE IF NOT EXISTS invitations
        #                         (invitation_id TEXT, contract_id TEXT, email TEXT, role TEXT, status TEXT, created_at TEXT)''')

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
                    response = { "status": "success", "name": user[1], "email": user[2], "phone": user[3], "user_type": user[4], "code": user[5], "account_status": user[7], "next_date": user[8], "isadmin": user[10]}

                    # Add lawfirm name if user type is "org"
                    if user[4] == "org":
                        response["lawfirm_name"] = user[6]
                    
                    return response
                else:
                    return {"status": "User does not exist"}
        except Exception as e:
            print("Error on loading profile: " + str(e))
            return {"status": "Error: " + str(e)}
        
            # Get a user's profile based on email
    def get_user_by_email(self, email):
        '''Fetch user profile from the database using email address.'''
        try:
            with sqlite3.connect(self.db_path) as conn:
                cursor = conn.cursor()
                cursor.execute('SELECT * FROM users WHERE email=?', (email,))
                user = cursor.fetchone()
                if user:
                    # Return user info
                    response = {
                        "status": "success",
                        "user_id": user[0],
                        "name": user[1],
                        "email": user[2],
                        "phone": user[3],
                        "user_type": user[4],
                        "code": user[5],
                        "account_status": user[7],
                        "next_date": user[8],
                        "isadmin": user[10]
                    }
                    
                    # Add lawfirm name if user type is "org"
                    if user[4] == "org":
                        response["lawfirm_name"] = user[6]
                    return response
                else:
                    return {"status": "User does not exist"}
        except Exception as e:
            print("Error on loading profile by email: " + str(e))
            return {"status": "Error: " + str(e)}
        
    # Check if a user exists in the database by user_id
    def user_exists(self, user_id):
        try:
            with sqlite3.connect(self.db_path) as conn:
                cursor = conn.cursor()
                cursor.execute('SELECT user_id FROM users WHERE user_id=?', (user_id,))
                user = cursor.fetchone()
                return user is not None
        except Exception as e:
            print("Error checking user existence:" + str(e))
            return False
    
    # Check if a user exists in the database by email
    def email_exists(self, email):
        try:
            with sqlite3.connect(self.db_path) as conn:
                cursor = conn.cursor()
                cursor.execute('SELECT user_id FROM users WHERE email=?', (email,))
                user = cursor.fetchone()
                return user is not None
        except Exception as e:
            print("Error checking email existence:" + str(e))
            return False

        
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
        
    # Add a role (when adding a collaborator)
    def add_role(self, user_id, contract_id, role):
        try:
            with sqlite3.connect(self.db_path) as conn:
                cursor = conn.cursor()
                cursor.execute('INSERT INTO permissions (contract_id, user_id, role) VALUES (?, ?, ?)', (contract_id, user_id, role))  
                conn.commit()
                return True
        except sqlite3.Error as e:
            print(f"Error adding role: {e}")
            return False
            
    # Update a user's role for a contract
    def update_role(self, user_id, contract_id, new_role):
        try:
            with sqlite3.connect(self.db_path) as conn:
                cursor = conn.cursor()
                cursor.execute('UPDATE permissions SET role = ? WHERE user_id = ? AND contract_id = ?', (new_role, user_id, contract_id))
                conn.commit()
                return True
        except sqlite3.Error as e:
            print(f"Error updating role: {e}")
            return False
    
    # Delete a role (when removing a collaborator)
    def delete_role(self, user_id, contract_id):
        try:
            with sqlite3.connect(self.db_path) as conn:
                cursor = conn.cursor()
                cursor.execute('DELETE FROM permissions WHERE user_id = ? AND contract_id = ?', (user_id, contract_id))
                conn.commit()
                return True
        except sqlite3.Error as e:
            print(f"Error deleting role: {e}")
            return False
        
    # Delete a contract
    def delete_contract(self, contract_id):
        try:
            with sqlite3.connect(self.db_path) as conn:
                cursor = conn.cursor()
                
                # Delete contract from contracts table
                cursor.execute('DELETE FROM contracts WHERE contract_id = ?', (contract_id,))
                
                # Delete associated permissions
                cursor.execute('DELETE FROM permissions WHERE contract_id = ?', (contract_id,)) 
                
                conn.commit()
                return True
        except sqlite3.Error as e:
            print(f"Error deleting contract: {e}")
            return False
        
   # Get all contracts a user owns
    def get_user_contracts(self, user_id):
        with sqlite3.connect(self.db_path) as conn:
            cursor = conn.cursor()
            cursor.execute('''
            SELECT contract_id, title, status FROM contracts WHERE creator_id = ?
            ''', (user_id,))
            return cursor.fetchall()
            
    # Get all contracts a user is a collaborator on, along with their role
    def get_user_collaborations(self, user_id):
        try:
            with sqlite3.connect(self.db_path) as conn:
                cursor = conn.cursor()
                cursor.execute('''
                SELECT p.contract_id, c.title, p.role
                FROM permissions p
                JOIN contracts c ON p.contract_id = c.contract_id
                WHERE p.user_id = ?
                ''', (user_id,))
                collaborations = [{"contract_id": row[0], "title": row[1], "role": row[2]} for row in cursor.fetchall()]
                
                print(f"Collaborations found: {collaborations}")
                return collaborations
        except sqlite3.Error as e:
            print(f"Database error in get_user_collaborations: {e}")
            return []