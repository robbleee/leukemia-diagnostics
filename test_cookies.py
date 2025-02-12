import streamlit as st
import bcrypt
import jwt
import datetime
from streamlit_cookies_manager import EncryptedCookieManager

##################################
# Configuration & Constants
##################################
SECRET_KEY = "your_secret_key"  # Replace with your secure key!
ALGORITHM = "HS256"
COOKIE_NAME = "auth_token"

# Initialize the cookie manager.
cookies = EncryptedCookieManager(prefix=COOKIE_NAME, password=SECRET_KEY)

##################################
# AUTH FUNCTIONS
##################################
def verify_password(stored_password: str, provided_password: str) -> bool:
    return bcrypt.checkpw(provided_password.encode('utf-8'), stored_password.encode('utf-8'))

def authenticate_user(username: str, password: str) -> bool:
    # Retrieve user data from st.secrets (or your user database)
    users = st.secrets["auth"]["users"]
    for user in users:
        if user["username"] == username:
            return verify_password(user["hashed_password"], password)
    return False

def create_token(username: str) -> str:
    # Token will be valid for 30 days.
    expiration = datetime.datetime.utcnow() + datetime.timedelta(days=30)
    token = jwt.encode({"sub": username, "exp": expiration}, SECRET_KEY, algorithm=ALGORITHM)
    return token

def verify_token(token: str) -> str:
    try:
        payload = jwt.decode(token, SECRET_KEY, algorithms=[ALGORITHM])
        return payload.get("sub")
    except jwt.ExpiredSignatureError:
        return None
    except jwt.InvalidTokenError:
        return None

##################################
# LOGIN PAGE
##################################
def show_login_page():
    st.title("Diagnosis Support Tool - Login")
    username = st.text_input("Username")
    password = st.text_input("Password", type="password")
    
    if st.button("Login"):
        if authenticate_user(username, password):
            # Create a persistent token and save it in a cookie.
            token = create_token(username)
            cookies[COOKIE_NAME] = token
            cookies.save()  # Write cookie to the browser.
            
            st.session_state["authenticated"] = True
            st.session_state["username"] = username
            st.success("Logged in successfully!")
            st.rerun()
        else:
            st.error("Invalid username or password!")

##################################
# MAIN APPLICATION PAGE
##################################
def show_main_app():
    st.title("Main Application")
    st.write(f"Welcome, {st.session_state.get('username', 'User')}!")
    
    # Your application code goes here.
    st.write("This is your main application content.")
    
    if st.button("Logout"):
        st.session_state["authenticated"] = False
        cookies.delete(COOKIE_NAME)
        cookies.save()
        st.experimental_rerun()

##################################
# PERSISTENT LOGIN CHECK
##################################
def check_persistent_login():
    # If a token exists in the cookies, validate it.
    token = cookies.get(COOKIE_NAME)
    if token:
        username = verify_token(token)
        if username:
            st.session_state["authenticated"] = True
            st.session_state["username"] = username

##################################
# Main Execution
##################################
if __name__ == "__main__":
    # The cookie manager might need to load cookies asynchronously.
    if not cookies.ready():
        st.stop()  # Wait until the cookies are ready before proceeding.
    
    # Initialize the authenticated flag if not already set.
    if "authenticated" not in st.session_state:
        st.session_state["authenticated"] = False

    # Check for an existing persistent login (if the user left and came back).
    if not st.session_state["authenticated"]:
        check_persistent_login()

    if st.session_state["authenticated"]:
        show_main_app()
    else:
        show_login_page()
