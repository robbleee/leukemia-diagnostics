# WHO Hematologic Classification Tool

![Streamlit App](https://blood-cancer-classifier.streamlit.app/)

## 📚 Overview

The **WHO Hematologic Classification Tool** is a web-based application designed to assist clinicians, researchers, and students in classifying hematologic malignancies based on user-provided data. Leveraging the World Health Organization (WHO) classification guidelines, this tool offers a streamlined and intuitive interface for determining cancer types, providing detailed derivations, and suggesting clinical next steps.

**Disclaimer**: This tool is intended for **educational purposes only** and should **not** be used as a substitute for professional medical advice or diagnosis.

## 🚀 Features

- **Comprehensive Classification**: Identifies a wide range of hematologic malignancies, including rare and aggressive subtypes.
- **User-Friendly Interface**: Organized input panels with clear sections for easy data entry.
- **Detailed Derivation**: Provides step-by-step explanations of the classification logic.
- **AI-Powered Recommendations**: (For authenticated users) Generates AI-driven reviews and clinical next steps.
- **Interactive Flowcharts**: Visual representation of the classification pathway.
- **Multi-Language Support**: Future updates to include multiple languages.
- **Secure Authentication**: Ensures that sensitive recommendations are accessible only to authorized users.

## 🛠️ Installation

Follow the steps below to install and run the application locally:

### Prerequisites

Ensure you have the following installed on your system:
- Python 3.8 or higher
- pip (Python package manager)

### Steps

1. **Clone the repository and navigate to the project directory**:

    ```bash
    git clone https://github.com/robbleee/blood-cancer-classifier.git
    cd hematologic-classification-tool
    ```

2. **Create and activate a virtual environment**:

    ```bash
    python -m venv venv
    source venv/bin/activate  # On Windows: venv\Scripts\activate
    ```

3. **Install the required dependencies**:

    ```bash
    pip install -r requirements.txt
    ```

4. **Hash your password using the provided script**:
   - Run the `hash_password.py` script included in the repository to generate a bcrypt-hashed password.
   
     ```bash
     python hash_password.py
     ```

   - Enter your desired password when prompted. Copy the hashed password from the output.

5. **Set up your environment variables**:
   - Create a `.streamlit/secrets.toml` file in the project directory.
   - Add the following contents to `secrets.toml`:
     
     ```toml
     [auth]
     users = [
       {username = "admin", hashed_password = "<paste-your-hashed-password-here>"}
     ]

     [openai]
     api_key = "<your-openai-api-key>"
     ```

   - **Adding New Credentials**:
     - To add additional users, append new entries to the `users` array in `secrets.toml`:
       
       ```toml
       [auth]
       users = [
         {username = "admin", hashed_password = "<paste-your-hashed-password-here>"},
         {username = "user1", hashed_password = "<hashed-password-user1>"},
         {username = "user2", hashed_password = "<hashed-password-user2>"}
       ]

       [openai]
       api_key = "<your-openai-api-key>"
       ```

     - **Note**: Use the `hash_password.py` script to generate hashed passwords for new users.

6. **Run the application**:

    ```bash
    streamlit run app.py
    ```

7. **Open your browser and navigate to** `http://localhost:8501`.

## 🗂️ `hash_password.py`

Here’s the `hash_password.py` script included in the repository:

```python
import bcrypt

def main():
    password = input("Enter a password to hash: ").encode('utf-8')
    hashed = bcrypt.hashpw(password, bcrypt.gensalt())
    print(f"Hashed password: {hashed.decode('utf-8')}")

if __name__ == "__main__":
    main()
```

### **How to Use `hash_password.py` Script**

1. **Run the Script**:
   
    ```bash
    python hash_password.py
    ```

2. **Input Your Password**:
   
   - When prompted, enter the password you wish to hash. For example:
     
     ```
     Enter a password to hash: your_secure_password
     ```

3. **Copy the Hashed Password**:
   
   - After entering your password, the script will output the hashed version. It will look something like this:
     
     ```
     Hashed password: $2b$12$KIXQ2tVt6Y8u0U9N1Q0pP.Je8fKcE9EwM.Uu1u7bqk3nJ0uT8Q4h6
     ```

4. **Update `secrets.toml`**:
   
   - Replace `<paste-your-hashed-password-here>` in the `secrets.toml` file with the hashed password you copied.
   - For example:
     
     ```toml
     [auth]
     users = [
       {username = "admin", hashed_password = "$2b$12$KIXQ2tVt6Y8u0U9N1Q0pP.Je8fKcE9EwM.Uu1u7bqk3nJ0uT8Q4h6"}
     ]

     [openai]
     api_key = "<your-openai-api-key>"
     ```

## 📋 Classifiable Hematologic Malignancies

1. Acute Erythroid Leukemia (AML-M6)
2. Acute Lymphoblastic Leukemia (ALL, Pediatric)
3. Acute Lymphoblastic Leukemia (ALL, Adult)
4. Acute Megakaryoblastic Leukemia (AML-M7)
5. Acute Myeloid Leukemia (AML)
6. Acute Promyelocytic Leukemia (APL)
7. AML with FLT3 Mutation
8. AML with NPM1 Mutation
9. AML with t(8;21)
10. AML with inv(16)/t(16;16)
11. Angioimmunoblastic T-Cell Lymphoma (AITL)
12. Anaplastic Large Cell Lymphoma (ALCL, ALK+)
13. Anaplastic Large Cell Lymphoma (ALCL, ALK–)
14. Burkitt's Lymphoma (High-Grade B-Cell NHL)
15. Chronic Lymphocytic Leukemia (CLL)
16. Cutaneous T-Cell Lymphoma (Mycosis Fungoides)
17. Diffuse Large B-Cell Lymphoma (DLBCL)
18. Follicular Lymphoma (Non-Hodgkin)
19. Hairy Cell Leukemia (Rare B-Cell Neoplasm)
20. Mantle Cell Lymphoma
21. Marginal Zone Lymphoma
22. Myeloproliferative Neoplasm (MPN)
23. Nodular Lymphocyte-Predominant Hodgkin Lymphoma (NLPHL)
24. Primary CNS Lymphoma (DLBCL)
25. Refractory Anemia (MDS)
26. Refractory Cytopenia with Multilineage Dysplasia (RCMD)

## 🤝 Contribution

Contributions, issues, and feature requests are welcome! Feel free to open an issue or submit a pull request.

## 📜 License

This project is licensed under the MIT License. See the [LICENSE](LICENSE) file for details.
