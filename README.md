# WHO Hematologic Classification Tool

![Streamlit App](https://github.com/yourusername/hematologic-classification-tool/blob/main/assets/app_screenshot.png)

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
14. Blastic Plasmacytoid Dendritic Cell Neoplasm (BPDCN)
15. Burkitt's Lymphoma (High-Grade B-Cell NHL)
16. Chronic Lymphocytic Leukemia (CLL)
17. Chronic Myeloid Leukemia (CML)
18. Cutaneous T-Cell Lymphoma (Mycosis Fungoides)
19. Diffuse Large B-Cell Lymphoma (DLBCL)
20. Follicular Lymphoma (Non-Hodgkin)
21. Hairy Cell Leukemia (Rare B-Cell Neoplasm)
22. Histiocytic/Dendritic Cell Neoplasm
23. Hodgkin Lymphoma (Unspecified Subtype)
24. Mantle Cell Lymphoma
25. Marginal Zone Lymphoma
26. Mastocytosis
27. Myelodysplastic Syndromes (MDS)
28. Myeloproliferative Neoplasm (MPN)
29. Peripheral T-Cell Lymphoma (PTCL)
30. Refractory Anemia (MDS)
31. Refractory Cytopenia with Multilineage Dysplasia (RCMD)
32. Primary CNS Lymphoma (DLBCL)
33. Undetermined Hematologic Neoplasm

## 🛠️ Installation

### 📋 Prerequisites

- **Python 3.8 or higher**
- **Git**

### 🔧 Clone the Repository

```bash
git clone https://github.com/yourusername/hematologic-classification-tool.git
cd hematologic-classification-tool
```
🐍 Create a Virtual Environment
It's recommended to use a virtual environment to manage dependencies.


bash
Copy code
python -m venv venv
Activate the virtual environment:

Windows:

bash
Copy code
venv\Scripts\activate
macOS/Linux:

bash
Copy code
source venv/bin/activate
📦 Install Dependencies
Ensure you have pip updated:

bash
Copy code
pip install --upgrade pip
Install the required packages:

bash
Copy code
pip install -r requirements.txt
If requirements.txt is not provided, you can install the necessary packages manually:

bash
Copy code
pip install streamlit
pip install openai  # If AI features are integrated
🗂️ Project Structure
plaintext
Copy code
hematologic-classification-tool/
├── app.py
├── helpers.py
├── requirements.txt
├── README.md
└── assets/
    └── app_screenshot.png
🚀 Running the Application
Activate your virtual environment if not already active:

Windows:

bash
Copy code
venv\Scripts\activate
macOS/Linux:

bash
Copy code
source venv/bin/activate
Start the Streamlit app:

bash
Copy code
streamlit run app.py
This command will launch the application in your default web browser. If it doesn't open automatically, navigate to the URL provided in the terminal (typically http://localhost:8501).

🖥️ Usage
Data Input Panel: Enter all relevant patient data, including Complete Blood Count (CBC), Bone Marrow Blasts percentage, Morphological Details, Lineage, Immunophenotyping Markers, Cytogenetic Abnormalities, Molecular Mutations, and any Special Entities.
Classify: Click the "Classify" button to process the inputs.
Results Panel: View the classification result, detailed derivation, AI-generated clinical recommendations (if authenticated), and an interactive classification flowchart.
Explanation & Help: Access detailed explanations of the classification logic through the "Show Explanation" button in the sidebar.
🎓 Explanation & Help
Access the detailed Explanation & Help section by clicking the "Show Explanation" button in the sidebar. This section provides an in-depth overview of the classification logic, key decision factors, step-by-step explanations, and a comprehensive list of classifiable hematologic malignancies.

🔒 Authentication (Optional)
For users to access AI-powered reviews and clinical recommendations, authentication is required. Implement your preferred authentication method to manage user access. Ensure that sensitive data and AI recommendations are securely handled.

📈 Future Improvements
Expand Classifiable Entities: Incorporate additional rare hematologic malignancies.
Machine Learning Integration: Utilize ML models for enhanced classification accuracy.
User Management: Implement role-based access control for different user types.
Multi-Language Support: Make the tool accessible to non-English-speaking users.
Enhanced Visualizations: Add more interactive elements like detailed flowcharts and real-time data validation.
🤝 Contributing
Contributions are welcome! Please follow these steps to contribute:

Fork the Repository

Create a Feature Branch

bash
Copy code
git checkout -b feature/YourFeatureName
Commit Your Changes

bash
Copy code
git commit -m "Add some feature"
Push to the Branch

bash
Copy code
git push origin feature/YourFeatureName
Open a Pull Request

📄 License
This project is licensed under the MIT License.

📞 Contact
For any questions, suggestions, or feedback, please contact your.email@example.com.

