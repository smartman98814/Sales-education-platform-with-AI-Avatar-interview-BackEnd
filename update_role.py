import sqlite3
import os

db_path = 'users.db'
if not os.path.exists(db_path):
    print(f'❌ Database file not found: {db_path}')
    exit(1)

conn = sqlite3.connect(db_path)
cursor = conn.cursor()

# Add role column if needed
try:
    cursor.execute('ALTER TABLE users ADD COLUMN role VARCHAR DEFAULT "user"')
    conn.commit()
    print('✅ Role column added')
except Exception as e:
    if 'duplicate column' not in str(e).lower():
        print(f'Note: {e}')

# Check if user exists first
cursor.execute('SELECT email, username, role FROM users WHERE email = ?', ('softrdev0715@gmail.com',))
user = cursor.fetchone()

if not user:
    print('❌ User softrdev0715@gmail.com not found!')
    print('Please sign up through the UI first, then run this script again.')
    conn.close()
    exit(1)

print(f'Found user: {user[0]} (current role: {user[2]})')

# Update user to admin
cursor.execute('UPDATE users SET role = "admin" WHERE email = ?', ('softrdev0715@gmail.com',))
conn.commit()

# Verify
cursor.execute('SELECT email, username, role FROM users WHERE email = ?', ('softrdev0715@gmail.com',))
user = cursor.fetchone()

if user:
    print(f'✅ User updated to admin!')
    print(f'   Email: {user[0]}')
    print(f'   Username: {user[1]}')
    print(f'   Role: {user[2]}')
    print(f'\n📝 You can now sign in and access the Admin Panel!')
else:
    print('❌ Error updating user!')

conn.close()

