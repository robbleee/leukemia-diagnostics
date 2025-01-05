
# Full Nodes List
nodes = [
    # General logic steps
    {"id": "Start"},
    {"id": "Check Pediatric?"},
    {"id": "Check CD138? (Myeloma)"},
    {"id": "Check Blasts >= 20%?"},
    {"id": "Lineage=Myeloid"},
    {"id": "Lineage=Lymphoid"},
    {"id": "Lineage=Undetermined"},

    # Outcomes (acute)
    {"id": "Acute Myeloid Leukemia (AML)"},
    {"id": "Blastic Plasmacytoid Dendritic Cell Neoplasm (BPDCN)"},
    {"id": "Acute Erythroid Leukemia (AML-M6)"},
    {"id": "Acute Megakaryoblastic Leukemia (AML-M7)"},
    {"id": "Acute Promyelocytic Leukemia (APL)"},
    {"id": "AML with t(8;21)"},
    {"id": "AML with inv(16)"},
    {"id": "AML with FLT3"},
    {"id": "AML with NPM1"},

    {"id": "Acute Lymphoblastic Leukemia (ALL, Pediatric)"},
    {"id": "Acute Lymphoblastic Leukemia (ALL, Adult)"},
    {"id": "Acute Leukemia of Ambiguous Lineage"},

    # Outcomes (chronic)
    {"id": "Myeloproliferative Neoplasm (MPN)"},
    {"id": "MDS with Excess Blasts"},
    {"id": "MDS with Isolated del(5q)"},
    {"id": "Refractory Cytopenia with Multilineage Dysplasia (RCMD)"},
    {"id": "Refractory Anemia (MDS)"},
    {"id": "Chronic Myeloid Leukemia (CML)"},

    {"id": "Classical Hodgkin Lymphoma"},
    {"id": "Nodular Lymphocyte-Predominant HL"},
    {"id": "Hodgkin Lymphoma (Unspecified Subtype)"},

    {"id": "Mantle Cell Lymphoma"},
    {"id": "Marginal Zone Lymphoma"},
    {"id": "Primary CNS Lymphoma (DLBCL)"},
    {"id": "Burkitt's Lymphoma"},
    {"id": "Follicular Lymphoma (NHL)"},
    {"id": "Diffuse Large B-Cell Lymphoma (DLBCL)"},

    {"id": "Anaplastic Large Cell Lymphoma (ALCL, ALK+)"},
    {"id": "Anaplastic Large Cell Lymphoma (ALCL, ALK–)"},
    {"id": "Angioimmunoblastic T-Cell Lymphoma (AITL)"},
    {"id": "Cutaneous T-Cell Lymphoma (Mycosis Fungoides)"},
    {"id": "Peripheral T-Cell Lymphoma (PTCL)"},

    {"id": "Chronic Lymphocytic Leukemia (CLL)"},
    {"id": "Hairy Cell Leukemia"},

    # Other
    {"id": "Multiple Myeloma (Plasma Cell Neoplasm)"},
    {"id": "Other Chronic Hematologic Neoplasm"},
    {"id": "Unspecified Hematologic Neoplasm"},
]

# Full Links List
links = [
    # Start -> Pediatric check
    {"source": "Start", "target": "Check Pediatric?", "type": "logic"},

    # Pediatric modifies context, doesn't skip classification, so let's just store it as a step:
    {"source": "Check Pediatric?", "target": "Check CD138? (Myeloma)", "type": "adult/pediatric"},

    # Myeloma check
    {"source": "Check CD138? (Myeloma)", "target": "Multiple Myeloma (Plasma Cell Neoplasm)", "type": "yes"},
    {"source": "Check CD138? (Myeloma)", "target": "Check Blasts >= 20%?", "type": "no"},

    # Check blasts => 20%
    {"source": "Check Blasts >= 20%?", "target": "Lineage=Myeloid", "type": "yes (Acute)"},
    {"source": "Check Blasts >= 20%?", "target": "Chronic or Other", "type": "no"},

    # If acute + myeloid => AML logic
    {"source": "Lineage=Myeloid", "target": "Acute Myeloid Leukemia (AML)", "type": "blasts>=20%"},

    # AML sub-checks
    {"source": "Acute Myeloid Leukemia (AML)", "target": "Blastic Plasmacytoid Dendritic Cell Neoplasm (BPDCN)", "type": "CD123/CD4/CD56"},
    {"source": "Acute Myeloid Leukemia (AML)", "target": "Acute Erythroid Leukemia (AML-M6)", "type": "Erythroid/CD71"},
    {"source": "Acute Myeloid Leukemia (AML)", "target": "Acute Megakaryoblastic Leukemia (AML-M7)", "type": "Megakaryo/CD41/CD42b/CD61"},
    {"source": "Acute Myeloid Leukemia (AML)", "target": "Acute Promyelocytic Leukemia (APL)", "type": "t(15;17)"},
    {"source": "Acute Myeloid Leukemia (AML)", "target": "AML with t(8;21)", "type": "t(8;21)"},
    {"source": "Acute Myeloid Leukemia (AML)", "target": "AML with inv(16)", "type": "inv(16)/t(16;16)"},
    {"source": "Acute Myeloid Leukemia (AML)", "target": "AML with FLT3", "type": "FLT3"},
    {"source": "Acute Myeloid Leukemia (AML)", "target": "AML with NPM1", "type": "NPM1"},

    # If acute + lymphoid
    {"source": "Lineage=Lymphoid", "target": "Acute Lymphoblastic Leukemia (ALL, Pediatric)", "type": "pediatric"},
    {"source": "Lineage=Lymphoid", "target": "Acute Lymphoblastic Leukemia (ALL, Adult)", "type": "adult"},

    # If acute + undetermined
    {"source": "Lineage=Undetermined", "target": "Acute Leukemia of Ambiguous Lineage", "type": "blasts>=20%"},

    # If no B/T -> CLL
    {"source": "Chronic or Other", "target": "Chronic Lymphocytic Leukemia (CLL)", "type": "Default Lymphoid Chronic"},
    {"source": "Chronic Lymphocytic Leukemia (CLL)", "target": "Hairy Cell Leukemia", "type": "Hairy cells"},

    # If we do not match anything
    {"source": "Chronic or Other", "target": "Other Chronic Hematologic Neoplasm", "type": "rare fallback"},
    {"source": "Start", "target": "Unspecified Hematologic Neoplasm", "type": "fallback"}
]
