# dash_app.py
import dash
from dash import html
import dash_cytoscape as cyto

# Define Nodes with Simplified IDs and Descriptive Labels
nodes = [
    # General Logic Steps
    {"id": "start", "label": "Start"},
    {"id": "check_pediatric", "label": "Check Pediatric?"},
    {"id": "check_cd138_myeloma", "label": "Check CD138? (Myeloma)"},
    {"id": "check_blasts_20", "label": "Check Blasts >= 20%?"},
    {"id": "lineage_myeloid", "label": "Lineage=Myeloid"},
    {"id": "lineage_lymphoid", "label": "Lineage=Lymphoid"},
    {"id": "lineage_undetermined", "label": "Lineage=Undetermined"},

    # Acute Outcomes
    {"id": "aml", "label": "Acute Myeloid Leukemia (AML)"},
    {"id": "bpdcn", "label": "Blastic Plasmacytoid Dendritic Cell Neoplasm (BPDCN)"},
    {"id": "aml_m6", "label": "Acute Erythroid Leukemia (AML-M6)"},
    {"id": "aml_m7", "label": "Acute Megakaryoblastic Leukemia (AML-M7)"},
    {"id": "apl", "label": "Acute Promyelocytic Leukemia (APL)"},
    {"id": "aml_t821", "label": "AML with t(8;21)"},
    {"id": "aml_inv16", "label": "AML with inv(16)/t(16;16)"},
    {"id": "aml_flt3", "label": "AML with FLT3"},
    {"id": "aml_npm1", "label": "AML with NPM1"},

    {"id": "all_pediatric", "label": "Acute Lymphoblastic Leukemia (ALL, Pediatric)"},
    {"id": "all_adult", "label": "Acute Lymphoblastic Leukemia (ALL, Adult)"},
    {"id": "acute_ambiguous", "label": "Acute Leukemia of Ambiguous Lineage"},

    # Chronic Outcomes
    {"id": "mpn", "label": "Myeloproliferative Neoplasm (MPN)"},
    {"id": "mds_excess_blasts", "label": "MDS with Excess Blasts"},
    {"id": "mds_del5q", "label": "MDS with Isolated del(5q)"},
    {"id": "rcmd", "label": "Refractory Cytopenia with Multilineage Dysplasia (RCMD)"},
    {"id": "refractory_anemia", "label": "Refractory Anemia (MDS)"},
    {"id": "cml", "label": "Chronic Myeloid Leukemia (CML)"},

    # Hodgkin Lymphoma
    {"id": "classical_hodgkin", "label": "Classical Hodgkin Lymphoma"},
    {"id": "nodular_lp_hl", "label": "Nodular Lymphocyte-Predominant HL"},
    {"id": "hodgkin_unspecified", "label": "Hodgkin Lymphoma (Unspecified Subtype)"},

    # Non-Hodgkin Lymphoma (B-cell)
    {"id": "mantle_cell", "label": "Mantle Cell Lymphoma"},
    {"id": "marginal_zone", "label": "Marginal Zone Lymphoma"},
    {"id": "primary_cns_dlbcl", "label": "Primary CNS Lymphoma (DLBCL)"},
    {"id": "burkitts_lymphoma", "label": "Burkitt's Lymphoma"},
    {"id": "follicular_nhl", "label": "Follicular Lymphoma (NHL)"},
    {"id": "dlbcl", "label": "Diffuse Large B-Cell Lymphoma (DLBCL)"},

    # Non-Hodgkin Lymphoma (T-cell)
    {"id": "alcl_alkp", "label": "Anaplastic Large Cell Lymphoma (ALCL, ALK+)"},
    {"id": "alcl_alkm", "label": "Anaplastic Large Cell Lymphoma (ALCL, ALK–)"},
    {"id": "aitl", "label": "Angioimmunoblastic T-Cell Lymphoma (AITL)"},
    {"id": "mycosis_fungoides", "label": "Cutaneous T-Cell Lymphoma (Mycosis Fungoides)"},
    {"id": "ptcl", "label": "Peripheral T-Cell Lymphoma (PTCL)"},

    {"id": "cll", "label": "Chronic Lymphocytic Leukemia (CLL)"},
    {"id": "hairy_cell", "label": "Hairy Cell Leukemia"},

    # Other Entities
    {"id": "multiple_myeloma", "label": "Multiple Myeloma (Plasma Cell Neoplasm)"},
    {"id": "other_chronic", "label": "Other Chronic Hematologic Neoplasm"},
    {"id": "unspecified_neoplasm", "label": "Unspecified Hematologic Neoplasm"},
]

# Define Links with Simplified Source and Target IDs
links = [
    # Start -> Pediatric check
    {"source": "start", "target": "check_pediatric", "type": "logic"},

    # Pediatric modifies context, doesn't skip classification
    {"source": "check_pediatric", "target": "check_cd138_myeloma", "type": "adult/pediatric"},

    # Myeloma check
    {"source": "check_cd138_myeloma", "target": "multiple_myeloma", "type": "yes"},
    {"source": "check_cd138_myeloma", "target": "check_blasts_20", "type": "no"},

    # Check blasts >= 20%
    {"source": "check_blasts_20", "target": "lineage_myeloid", "type": "yes (Acute)"},
    {"source": "check_blasts_20", "target": "other_chronic", "type": "no"},

    # Acute Myeloid Leukemia (AML) logic
    {"source": "lineage_myeloid", "target": "aml", "type": "blasts>=20%"},

    # AML sub-checks
    {"source": "aml", "target": "bpdcn", "type": "CD123/CD4/CD56"},
    {"source": "aml", "target": "aml_m6", "type": "Erythroid/CD71"},
    {"source": "aml", "target": "aml_m7", "type": "Megakaryo/CD41/CD42b/CD61"},
    {"source": "aml", "target": "apl", "type": "t(15;17)"},
    {"source": "aml", "target": "aml_t821", "type": "t(8;21)"},
    {"source": "aml", "target": "aml_inv16", "type": "inv(16)/t(16;16)"},
    {"source": "aml", "target": "aml_flt3", "type": "FLT3"},
    {"source": "aml", "target": "aml_npm1", "type": "NPM1"},

    # Acute Lymphoblastic Leukemia (ALL)
    {"source": "lineage_lymphoid", "target": "all_pediatric", "type": "pediatric"},
    {"source": "lineage_lymphoid", "target": "all_adult", "type": "adult"},

    # Acute Leukemia of Ambiguous Lineage
    {"source": "lineage_undetermined", "target": "acute_ambiguous", "type": "blasts>=20%"},

    

    

    

    
    {"source": "cll", "target": "hairy_cell", "type": "Hairy cells"},

    
    {"source": "start", "target": "unspecified_neoplasm", "type": "fallback"},
]

# Verification Step
node_ids = set(node["id"] for node in nodes)
link_targets = set(link["target"] for link in links)
missing_targets = link_targets - node_ids

if missing_targets:
    print("Missing nodes for targets:", missing_targets)
    raise ValueError(f"Missing nodes for targets: {missing_targets}")
else:
    print("All target nodes are present.")

# Convert to Cytoscape Elements
cy_nodes = [
    {
        "data": {
            "id": node["id"],
            "label": node["label"]
        }
    }
    for node in nodes
]

cy_edges = [
    {
        "data": {
            "source": link["source"],
            "target": link["target"],
            "label": link["type"]
        }
    }
    for link in links
]

cy_elements = cy_nodes + cy_edges

# Initialize Dash App
app = dash.Dash(__name__)

app.layout = html.Div([
    html.H1("Hematologic Classification Flowchart", style={'textAlign': 'center'}),

    cyto.Cytoscape(
        id="cytoscape",
        elements=cy_elements,
        layout={"name": "breadthfirst"},
        style={"width": "100%", "height": "1200px"},
        stylesheet=[
            # Node Styling
            {
                "selector": "node",
                "style": {
                    "content": "data(label)",
                    "text-valign": "center",
                    "text-halign": "center",
                    "color": "#fff",
                    "background-color": "#0074D9",
                    "width": "200px",
                    "height": "60px",
                    "font-size": "8px",
                    "shape": "rectangle",
                    "border-width": "2px",
                    "border-color": "#fff",
                    "text-wrap": "wrap",
                    "text-max-width": "180px",
                },
            },
            # Edge Styling
            {
                "selector": "edge",
                "style": {
                    "curve-style": "bezier",
                    "target-arrow-shape": "triangle",
                    "label": "data(label)",
                    "line-color": "#0074D9",
                    "target-arrow-color": "#0074D9",
                    "width": 1.5,
                    "font-size": "7px",
                    "text-rotation": "autorotate",
                    "text-margin-y": "-10px",
                    "color": "#000",
                    "text-background-color": "#fff",
                    "text-background-opacity": 1,
                    "text-background-padding": "3px",
                    "text-background-shape": "roundrectangle",
                },
            },
            # Highlight Selected Node
            {
                "selector": "node:selected",
                "style": {
                    "background-color": "#FF4136",
                    "line-color": "#FF4136",
                    "target-arrow-color": "#FF4136",
                    "source-arrow-color": "#FF4136",
                }
            },
            # Highlight Selected Edge
            {
                "selector": "edge:selected",
                "style": {
                    "line-color": "#FF4136",
                    "target-arrow-color": "#FF4136",
                }
            },
        ],
    ),

    # Optional: Add a legend or additional UI components here
])

if __name__ == "__main__":
    app.run_server(debug=True)
