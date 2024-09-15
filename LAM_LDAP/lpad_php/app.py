from flask import Flask, request, render_template, send_file
import pandas as pd
from ldap3 import Server, Connection, ALL
import random
import string
import os

app = Flask(__name__)

LDAP_SERVER = 'ldap://openldap:389'
LDAP_USER = 'cn=admin,dc=alibnr,dc=com'
LDAP_PASSWORD = 'admin_pass'

def generate_password(length=8):
    characters = string.ascii_letters + string.digits + string.punctuation
    return ''.join(random.choice(characters) for i in range(length))

def check_and_create_ou(conn, ou_dn):
    if not conn.search(ou_dn, '(objectClass=organizationalUnit)'):
        print(f"Creating organizational unit {ou_dn}")
        ou_attrs = {
            'objectClass': ['organizationalUnit'],
            'ou': ou_dn.split(',')[0].split('=')[1]
        }
        if not conn.add(ou_dn, attributes=ou_attrs):
            print(f"Error creating OU {ou_dn}: {conn.result}")
        else:
            print(f"Organizational unit {ou_dn} created successfully")
    else:
        print(f"Organizational unit {ou_dn} already exists")

def create_user(conn, username, password, group):
    gid_map = {
        'ИКТК-11': 1001,
        'ИКТК-12': 1002,
        'ИКТК-03': 1003,
    }
    gid_number = gid_map.get(group, 1000)
    uid_number = random.randint(10000, 99999)
    home_directory = f"/home/{username}"

    dn = f"cn={username},ou=users,dc=alibnr,dc=com"
    attrs = {
        'objectClass': ['inetOrgPerson', 'posixAccount', 'top'],
        'cn': username,
        'sn': username,
        'uid': username,
        'userPassword': password,
        'gidNumber': gid_number,
        'uidNumber': uid_number,
        'homeDirectory': home_directory
    }
    if conn.search('ou=users,dc=alibnr,dc=com', f'(cn={username})'):
        print(f"User {username} already exists")
        return
    
    if not conn.add(dn, attributes=attrs):
        print(f"Error adding user {username}: {conn.result}")
    else:
        print(f"User {username} added successfully")
        if not os.path.exists(home_directory):
            os.makedirs(home_directory)

@app.route('/')
def index():
    return render_template('upload.html')

@app.route('/upload', methods=['POST'])
def upload():
    if 'file' not in request.files:
        return 'No file part'
    file = request.files['file']
    if file.filename == '':
        return 'No selected file'
    if file and file.filename.endswith('.csv'):
        try:
            df = pd.read_csv(file)

            required_columns = ['ФИО', 'номер зачетки', 'группа']
            if not all(column in df.columns for column in required_columns):
                return 'CSV file is missing required columns'

            server = Server(LDAP_SERVER, get_info=ALL)
            conn = Connection(server, user=LDAP_USER, password=LDAP_PASSWORD, auto_bind=True)

            check_and_create_ou(conn, 'ou=users,dc=alibnr,dc=com')

            output = []

            for index, row in df.iterrows():
                username = row['номер зачетки']
                password = generate_password()
                group = row['группа']
                create_user(conn, username, password, group)
                output.append({'username': username, 'password': password})

            output_df = pd.DataFrame(output)
            output_file = 'output.csv'
            output_df.to_csv(output_file, index=False)

            conn.unbind()

            return send_file(output_file, as_attachment=True)

        except Exception as e:
            return f'An error occurred: {e}'

    return 'Invalid file type'

if __name__ == '__main__':
    app.run(host='0.0.0.0', port=5010, debug=True)
