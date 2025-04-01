print("Fixing indentation...")
with open("app.py", "r") as f: lines = f.readlines()
lines[287] = "        if login_button.button(\"Sign In\", key=\"login_button\"):\\n"
lines[288] = "            if authenticate_user(username, password):\\n"
with open("app.py", "w") as f: f.writelines(lines)
