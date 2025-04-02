import bcrypt

def main():
    password = input("Enter a password to hash: ").encode('utf-8')
    hashed = bcrypt.hashpw(password, bcrypt.gensalt())
    print(f"Hashed password: {hashed.decode('utf-8')}")

if __name__ == "__main__":
    main()