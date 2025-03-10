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
        # cursor.execute('''CREATE TABLE IF NOT EXSTS users 
        #                         (user_id TEXT, name TEXT, email TEXT)''' )
        # Create Contracts table
        cursor.execute('''CREATE TABLE IF NOT EXISTS contracts
                                (contract_id TEXT, title TEXT, owner_id TEXT, status TEXT, created_at TEXT)''')
        # Create Permissions Table
        cursor.execute('''CREATE TABLE IF NOT EXISTS permissions
                                (permission_id TEXT, contract_id TEXT, user_id TEXT, permission_type TEXT)''')
        #Create Invitations Table
        cursor.execute('''CREATE TABLE IF NOT EXISTS invitations
                                (invitation_id TEXT, contract_id TEXT, email TEXT, role TEXT, status TEXT, created_at TEXT)''')

        conn.commit()

        
    def create_contract(self, contract_id, title, owner_id, status, created_at):
        
        # Generate a random contract ID
        contract_id = "contract" + str(random.randint(1000, 9999))
        title = "Untiled Contract"
        current_datetime = datetime.now()
        created_at = str(current_datetime.date)
        try:
            self.cursor.execute('INSERT INTO contracts (contract_id, title, owner_id, status, created_at) VALUES (?, ?, ?, ?, ?)', 
                                (contract_id, title, owner_id, status, created_at))
            self.conn.commit()
        except sqlite3.Error as e:
            print(f"Error Creating contract: {e}")
            
    def add_permission(self, permission_id, contract_id, user_id, permission_type):
        try:
            self.cursor.execute('INSERT INTO permissions (permission_id, contract_id, user_id, permission_type) VALUES (?, ?, ?, ?)',
                                (permission_id, contract_id, user_id, permission_type))
            self.conn.commit()
        except sqlite3.Error as e:
            print (f"An error occured: {e}")
    
    def add_invitation(self, invitation_id, contract_id, email, role, status, created_at):
        try:
            self.cursor.execute('INSERT INTO invitaions(invitation_id, contract_id, email, role, status, created_at) VALUES(?, ?, ?, ?, ?, ?)',
                                (invitation_id, contract_id, email, role, status, created_at))
            self.conn.commit()
        except sqlite3.Error as e:
            print (f"An error occured:{e}")
            
    def get_contract(self, contract_id):
        try: 
            self.cursor.execute('SELECT * FROM contracts WHERE contract_id = ?', (contract_id))
            contract = self.cursor.fetchone()
            return contract
        except sqlite3.Error as e:
            print(f"An error occured: {e}")
            
    def get_permissions(self, contract_id):
        try:
            self.cursor.execute('SELECT * FROM permissions WHERE contract_id = ?', (contract_id))
            permissions = self.cursor.fetchall()
            return permissions
        except sqlite3.Error as e:
            print(f"An error occcured: {e}")
            
    def get_invitations(self, contract_id):
        try:
            self.cursor.execute('SELECT * FROM invitations WHERE contract_id = ?', (contract_id,))
            invitations = self.cursor.fetchall()
            return invitations
        except sqlite3.Error as e:
            print(f"An error occured: {e}")
            