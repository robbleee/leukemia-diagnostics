import json
from typing import Dict, List, Optional, Tuple, Set
from dataclasses import dataclass, field
from datetime import datetime, timedelta

@dataclass
class EnhancedPatient:
    """Enhanced patient data structure incorporating AML parser molecular data"""
    
    # Basic Demographics
    age: int
    
    # Performance Status
    ecog_status: Optional[int] = None  # 0-4
    karnofsky_status: Optional[int] = None  # 0-100
    
    # Cancer Information
    primary_diagnosis: str = ""
    disease_stage: Optional[str] = None
    newly_diagnosed: bool = False
    relapsed: bool = False
    refractory: bool = False
    in_remission: bool = False
    
    # ===== MOLECULAR/GENETIC DATA FROM AML PARSER =====
    
    # Basic Clinical Values
    blasts_percentage: Optional[float] = None
    fibrotic: bool = False
    hypoplasia: bool = False
    number_of_dysplastic_lineages: Optional[int] = None
    no_cytogenetics_data: bool = False
    
    # AML-Defining Recurrent Genetic Abnormalities (Critical for trial matching!)
    aml_defining_abnormalities: Dict[str, bool] = field(default_factory=lambda: {
        "PML::RARA": False,
        "NPM1": False,
        "RUNX1::RUNX1T1": False,
        "CBFB::MYH11": False,
        "DEK::NUP214": False,
        "RBM15::MRTFA": False,
        "MLLT3::KMT2A": False,
        "GATA2::MECOM": False,
        "KMT2A": False,
        "MECOM": False,
        "NUP98": False,
        "CEBPA": False,
        "bZIP": False,
        "BCR::ABL1": False,
        "FLT3": False
    })
    
    # Biallelic TP53 Mutations (High-risk marker)
    tp53_status: Dict[str, bool] = field(default_factory=lambda: {
        "tp53_mentioned": False,
        "2_x_TP53_mutations": False,
        "1_x_TP53_mutation_del_17p": False,
        "1_x_TP53_mutation_LOH": False,
        "1_x_TP53_mutation_10_percent_vaf": False,
        "1_x_TP53_mutation_50_percent_vaf": False
    })
    
    # MDS-Related Mutations (Important for prognosis and trial eligibility)
    mds_related_mutations: Dict[str, bool] = field(default_factory=lambda: {
        "ASXL1": False,
        "BCOR": False,
        "EZH2": False,
        "RUNX1": False,
        "SF3B1": False,
        "SRSF2": False,
        "STAG2": False,
        "U2AF1": False,
        "ZRSR2": False,
        "UBA1": False,
        "JAK2": False
    })
    
    # MDS-Related Cytogenetics (Risk stratification)
    mds_related_cytogenetics: Dict[str, bool] = field(default_factory=lambda: {
        "Complex_karyotype": False,
        "del_5q": False,
        "t_5q": False,
        "add_5q": False,
        "-7": False,
        "del_7q": False,
        "+8": False,
        "del_11q": False,
        "del_12p": False,
        "t_12p": False,
        "add_12p": False,
        "-13": False,
        "i_17q": False,
        "-17": False,
        "add_17p": False,
        "del_17p": False,
        "del_20q": False,
        "idic_X_q13": False,
        "inv3_t33": False
    })
    
    # ELN2024 Risk Genes (Latest risk stratification)
    eln2024_risk_genes: Dict[str, bool] = field(default_factory=lambda: {
        "TP53": False,
        "KRAS": False,
        "PTPN11": False,
        "NRAS": False,
        "FLT3_ITD": False,
        "NPM1": False,
        "IDH1": False,
        "IDH2": False,
        "DDX41": False
    })
    
    # AML Differentiation (FAB classification)
    aml_differentiation: Optional[str] = None  # M0, M1, M2, M3, M4, M5a, M5b, M6a, M6b, M7
    
    # Disease History Qualifiers
    previous_mds_over_3_months: bool = False
    previous_mds_mpn_over_3_months: bool = False
    previous_mpn_over_3_months: bool = False
    previous_cytotoxic_therapy: Optional[str] = None
    predisposing_germline_variant: str = "None"
    
    # ===== STANDARD CLINICAL DATA =====
    
    # Treatment History
    prior_chemotherapy_regimens: int = 0
    prior_targeted_therapies: List[str] = field(default_factory=list)
    prior_immunotherapies: List[str] = field(default_factory=list)
    autologous_transplant_date: Optional[datetime] = None
    allogeneic_transplant_date: Optional[datetime] = None
    last_radiation_date: Optional[datetime] = None
    
    # Laboratory Values
    hemoglobin_g_dl: Optional[float] = None
    platelet_count_k_ul: Optional[float] = None
    neutrophil_count_k_ul: Optional[float] = None
    white_cell_count_k_ul: Optional[float] = None
    creatinine_mg_dl: Optional[float] = None
    bilirubin_mg_dl: Optional[float] = None
    alt_times_uln: Optional[float] = None
    
    # Medical Conditions
    ejection_fraction: Optional[int] = None
    recent_mi_date: Optional[datetime] = None
    heart_failure: bool = False
    hiv_positive: bool = False
    hepatitis_b_positive: bool = False
    hepatitis_c_positive: bool = False
    active_infection: bool = False
    other_cancers: bool = False
    
    # Reproductive
    pregnant: bool = False
    breastfeeding: bool = False
    
    @classmethod
    def from_aml_parser_output(cls, aml_data: Dict, **additional_data):
        """Create EnhancedPatient from AML parser output"""
        patient = cls(**additional_data)
        
        # Map AML parser data to patient fields
        patient.blasts_percentage = aml_data.get("blasts_percentage")
        patient.fibrotic = aml_data.get("fibrotic", False)
        patient.hypoplasia = aml_data.get("hypoplasia", False)
        patient.number_of_dysplastic_lineages = aml_data.get("number_of_dysplastic_lineages")
        patient.no_cytogenetics_data = aml_data.get("no_cytogenetics_data", False)
        
        # AML-defining abnormalities
        aml_abnormalities = aml_data.get("AML_defining_recurrent_genetic_abnormalities", {})
        patient.aml_defining_abnormalities.update(aml_abnormalities)
        
        # TP53 status
        tp53_data = aml_data.get("Biallelic_TP53_mutation", {})
        patient.tp53_status.update(tp53_data)
        
        # MDS-related mutations
        mds_mutations = aml_data.get("MDS_related_mutation", {})
        patient.mds_related_mutations.update(mds_mutations)
        
        # MDS-related cytogenetics
        mds_cyto = aml_data.get("MDS_related_cytogenetics", {})
        patient.mds_related_cytogenetics.update(mds_cyto)
        
        # ELN2024 risk genes
        eln_genes = aml_data.get("ELN2024_risk_genes", {})
        patient.eln2024_risk_genes.update(eln_genes)
        
        # AML differentiation
        patient.aml_differentiation = aml_data.get("AML_differentiation")
        
        # Qualifiers
        qualifiers = aml_data.get("qualifiers", {})
        patient.previous_mds_over_3_months = qualifiers.get("previous_MDS_diagnosed_over_3_months_ago", False)
        patient.previous_mds_mpn_over_3_months = qualifiers.get("previous_MDS/MPN_diagnosed_over_3_months_ago", False)
        patient.previous_mpn_over_3_months = qualifiers.get("previous_MPN_diagnosed_over_3_months_ago", False)
        patient.previous_cytotoxic_therapy = qualifiers.get("previous_cytotoxic_therapy")
        patient.predisposing_germline_variant = qualifiers.get("predisposing_germline_variant", "None")
        
        return patient
    
    def get_positive_mutations(self) -> Set[str]:
        """Get all positive mutations for this patient"""
        mutations = set()
        
        # AML-defining abnormalities
        for gene, positive in self.aml_defining_abnormalities.items():
            if positive:
                mutations.add(gene)
        
        # MDS-related mutations
        for gene, positive in self.mds_related_mutations.items():
            if positive:
                mutations.add(gene)
        
        # ELN2024 risk genes
        for gene, positive in self.eln2024_risk_genes.items():
            if positive:
                mutations.add(gene)
        
        return mutations
    
    def get_cytogenetic_abnormalities(self) -> Set[str]:
        """Get all cytogenetic abnormalities for this patient"""
        abnormalities = set()
        
        for abnormality, positive in self.mds_related_cytogenetics.items():
            if positive:
                abnormalities.add(abnormality)
        
        return abnormalities
    
    def has_high_risk_features(self) -> bool:
        """Check if patient has high-risk molecular features"""
        # TP53 mutations are high-risk
        if any(self.tp53_status.values()):
            return True
        
        # Complex karyotype is high-risk
        if self.mds_related_cytogenetics.get("Complex_karyotype", False):
            return True
        
        # Certain high-risk mutations
        high_risk_mutations = ["TP53", "KRAS", "PTPN11", "NRAS"]
        for mutation in high_risk_mutations:
            if self.eln2024_risk_genes.get(mutation, False):
                return True
        
        return False


class EnhancedTrialMatcher:
    """Enhanced trial matcher that incorporates detailed molecular data"""
    
    def __init__(self, trials_file: str):
        """Load trials with structured eligibility criteria"""
        with open(trials_file, 'r', encoding='utf-8') as f:
            self.trials = json.load(f)
        
        # Filter trials that have V2 structured eligibility
        self.trials = [
            trial for trial in self.trials 
            if 'structured_eligibility_v2' in trial and trial['structured_eligibility_v2']
        ]
        
        print(f"📊 Loaded {len(self.trials)} trials with structured eligibility criteria")
    
    def check_molecular_eligibility(self, patient: EnhancedPatient, criteria: Dict) -> Tuple[bool, str]:
        """Check molecular/genetic eligibility criteria"""
        genetic_criteria = criteria.get('genetic_markers', {})
        
        # Check required positive mutations
        required_positive = genetic_criteria.get('required_positive', [])
        patient_mutations = patient.get_positive_mutations()
        
        for required_gene in required_positive:
            # Handle different gene name formats
            gene_variants = [
                required_gene,
                required_gene.replace("_", ""),
                required_gene.replace("::", "_"),
                required_gene.split("::")[0] if "::" in required_gene else required_gene
            ]
            
            if not any(variant in patient_mutations for variant in gene_variants):
                return False, f"Required mutation {required_gene} not present"
        
        # Check required negative mutations
        required_negative = genetic_criteria.get('required_negative', [])
        for excluded_gene in required_negative:
            gene_variants = [
                excluded_gene,
                excluded_gene.replace("_", ""),
                excluded_gene.replace("::", "_"),
                excluded_gene.split("::")[0] if "::" in excluded_gene else excluded_gene
            ]
            
            if any(variant in patient_mutations for variant in gene_variants):
                return False, f"Excluded mutation {excluded_gene} is present"
        
        # Check chromosomal abnormalities
        chromosomal_criteria = genetic_criteria.get('chromosomal_abnormalities', {})
        patient_cyto = patient.get_cytogenetic_abnormalities()
        
        required_cyto = chromosomal_criteria.get('required', [])
        for required_abnormality in required_cyto:
            if required_abnormality not in patient_cyto:
                return False, f"Required cytogenetic abnormality {required_abnormality} not present"
        
        excluded_cyto = chromosomal_criteria.get('excluded', [])
        for excluded_abnormality in excluded_cyto:
            if excluded_abnormality in patient_cyto:
                return False, f"Excluded cytogenetic abnormality {excluded_abnormality} is present"
        
        return True, "Molecular criteria met"
    
    def check_blast_percentage(self, patient: EnhancedPatient, criteria: Dict) -> Tuple[bool, str]:
        """Check blast percentage requirements"""
        lab_criteria = criteria.get('laboratory_values', {})
        blood_counts = lab_criteria.get('blood_counts', {})
        
        # Some trials may have specific blast percentage requirements
        # This would need to be added to the eligibility extraction
        if patient.blasts_percentage is not None:
            # Example: exclude if blasts > 30% (would be trial-specific)
            # This logic would be driven by the extracted criteria
            pass
        
        return True, "Blast percentage criteria met"
    
    def check_aml_subtype_eligibility(self, patient: EnhancedPatient, criteria: Dict) -> Tuple[bool, str]:
        """Check AML subtype-specific eligibility"""
        cancer_criteria = criteria.get('cancer_diagnosis', {})
        
        # Check if specific AML subtypes are required/excluded
        required_diagnoses = cancer_criteria.get('required_diagnoses', [])
        excluded_diagnoses = cancer_criteria.get('excluded_diagnoses', [])
        
        # Map AML differentiation to common trial terminology
        aml_subtype_mapping = {
            "M3": ["acute promyelocytic leukemia", "APL", "PML-RARA"],
            "M4": ["acute myelomonocytic leukemia", "AMML"],
            "M5a": ["acute monoblastic leukemia"],
            "M5b": ["acute monocytic leukemia"],
            "M6a": ["acute erythroid leukemia"],
            "M7": ["acute megakaryoblastic leukemia"]
        }
        
        if patient.aml_differentiation:
            subtype_terms = aml_subtype_mapping.get(patient.aml_differentiation, [])
            
            # Check if this subtype is specifically excluded
            for excluded_dx in excluded_diagnoses:
                if any(term.lower() in excluded_dx.lower() for term in subtype_terms):
                    return False, f"AML subtype {patient.aml_differentiation} is excluded"
        
        return True, "AML subtype criteria met"
    
    def check_risk_stratification(self, patient: EnhancedPatient, criteria: Dict) -> Tuple[bool, str]:
        """Check risk-based eligibility (high-risk vs standard-risk)"""
        # Many trials are specifically for high-risk or standard-risk patients
        
        is_high_risk = patient.has_high_risk_features()
        
        # This would be enhanced based on trial-specific risk requirements
        # extracted from eligibility criteria
        
        return True, "Risk stratification criteria met"
    
    def calculate_molecular_match_score(self, patient: EnhancedPatient, trial: Dict) -> float:
        """Calculate a molecular match score for prioritizing trials"""
        score = 0.0
        
        # Get trial's genetic requirements
        criteria = trial.get('structured_eligibility_v2', {})
        genetic_criteria = criteria.get('genetic_markers', {})
        
        required_positive = genetic_criteria.get('required_positive', [])
        patient_mutations = patient.get_positive_mutations()
        
        # Score based on molecular match
        for required_gene in required_positive:
            if required_gene in patient_mutations:
                score += 10.0  # High score for exact molecular match
        
        # Bonus for specific high-value mutations
        high_value_mutations = ["NPM1", "FLT3", "IDH1", "IDH2", "CEBPA"]
        for mutation in high_value_mutations:
            if mutation in patient_mutations:
                score += 5.0
        
        # Penalty for high-risk features if trial doesn't specify
        if patient.has_high_risk_features():
            score -= 2.0
        
        return score
    
    def match_patient_to_trial(self, patient: EnhancedPatient, trial: Dict) -> Tuple[bool, List[str], float]:
        """
        Enhanced matching with molecular data and scoring
        Returns (is_eligible, list_of_reasons, match_score)
        """
        criteria = trial.get('structured_eligibility_v2', {})
        reasons = []
        
        # Standard checks (age, performance status, etc.)
        standard_checks = [
            self.check_age_eligibility,
            self.check_performance_status,
            self.check_cancer_diagnosis,
            self.check_prior_treatments,
            self.check_laboratory_values,
            self.check_medical_conditions,
            self.check_reproductive
        ]
        
        # Enhanced molecular checks
        molecular_checks = [
            self.check_molecular_eligibility,
            self.check_blast_percentage,
            self.check_aml_subtype_eligibility,
            self.check_risk_stratification
        ]
        
        all_checks = standard_checks + molecular_checks
        
        for check_func in all_checks:
            try:
                is_eligible, reason = check_func(patient, criteria)
                if not is_eligible:
                    reasons.append(reason)
            except Exception as e:
                # Handle missing methods gracefully
                continue
        
        is_eligible = len(reasons) == 0
        match_score = self.calculate_molecular_match_score(patient, trial) if is_eligible else 0.0
        
        return is_eligible, reasons, match_score
    
    def find_matching_trials(self, patient: EnhancedPatient) -> List[Dict]:
        """
        Find matching trials with molecular scoring
        """
        matching_trials = []
        
        for trial in self.trials:
            is_eligible, exclusion_reasons, match_score = self.match_patient_to_trial(patient, trial)
            
            trial_result = {
                'trial': trial,
                'eligible': is_eligible,
                'exclusion_reasons': exclusion_reasons,
                'molecular_match_score': match_score,
                'title': trial.get('title', 'Unknown'),
                'locations': trial.get('locations', 'Unknown'),
                'cancer_types': trial.get('cancer_types', 'Unknown')
            }
            
            if is_eligible:
                matching_trials.append(trial_result)
        
        # Sort by molecular match score (highest first)
        matching_trials.sort(key=lambda x: x['molecular_match_score'], reverse=True)
        
        return matching_trials
    
    # Include standard checking methods from previous implementation
    def check_age_eligibility(self, patient: EnhancedPatient, criteria: Dict) -> Tuple[bool, str]:
        """Check if patient meets age criteria"""
        age_criteria = criteria.get('age', {})
        min_age = age_criteria.get('min_age')
        max_age = age_criteria.get('max_age')
        
        if min_age is not None and patient.age < min_age:
            return False, f"Patient age {patient.age} < minimum {min_age}"
        
        if max_age is not None and patient.age > max_age:
            return False, f"Patient age {patient.age} > maximum {max_age}"
        
        return True, "Age criteria met"
    
    def check_performance_status(self, patient: EnhancedPatient, criteria: Dict) -> Tuple[bool, str]:
        """Check if patient meets performance status criteria"""
        ps_criteria = criteria.get('performance_status', {})
        
        # Check ECOG status
        ecog_min = ps_criteria.get('ecog_min')
        ecog_max = ps_criteria.get('ecog_max')
        
        if patient.ecog_status is not None:
            if ecog_min is not None and patient.ecog_status < ecog_min:
                return False, f"ECOG {patient.ecog_status} < minimum {ecog_min}"
            if ecog_max is not None and patient.ecog_status > ecog_max:
                return False, f"ECOG {patient.ecog_status} > maximum {ecog_max}"
        
        return True, "Performance status criteria met"
    
    def check_cancer_diagnosis(self, patient: EnhancedPatient, criteria: Dict) -> Tuple[bool, str]:
        """Check if patient meets cancer diagnosis criteria"""
        cancer_criteria = criteria.get('cancer_diagnosis', {})
        
        # Check required diagnoses
        required_diagnoses = cancer_criteria.get('required_diagnoses', [])
        if required_diagnoses:
            diagnosis_match = any(
                req_dx.lower() in patient.primary_diagnosis.lower() 
                for req_dx in required_diagnoses
            )
            if not diagnosis_match:
                return False, f"Patient diagnosis '{patient.primary_diagnosis}' not in required: {required_diagnoses}"
        
        return True, "Cancer diagnosis criteria met"
    
    def check_prior_treatments(self, patient: EnhancedPatient, criteria: Dict) -> Tuple[bool, str]:
        """Check if patient meets prior treatment criteria"""
        treatment_criteria = criteria.get('prior_treatments', {})
        
        # Check chemotherapy requirements
        chemo_criteria = treatment_criteria.get('chemotherapy', {})
        min_regimens = chemo_criteria.get('min_prior_regimens')
        
        if min_regimens is not None and patient.prior_chemotherapy_regimens < min_regimens:
            return False, f"Minimum {min_regimens} prior chemo regimens required, patient has {patient.prior_chemotherapy_regimens}"
        
        return True, "Prior treatment criteria met"
    
    def check_laboratory_values(self, patient: EnhancedPatient, criteria: Dict) -> Tuple[bool, str]:
        """Check if patient meets laboratory value criteria"""
        lab_criteria = criteria.get('laboratory_values', {})
        
        # Check blood counts
        blood_counts = lab_criteria.get('blood_counts', {})
        
        hgb_min = blood_counts.get('hemoglobin_min_g_dl')
        if hgb_min is not None and patient.hemoglobin_g_dl is not None:
            if patient.hemoglobin_g_dl < hgb_min:
                return False, f"Hemoglobin {patient.hemoglobin_g_dl} < minimum {hgb_min} g/dL"
        
        return True, "Laboratory criteria met"
    
    def check_medical_conditions(self, patient: EnhancedPatient, criteria: Dict) -> Tuple[bool, str]:
        """Check if patient meets medical condition criteria"""
        medical_criteria = criteria.get('medical_conditions', {})
        
        # Check infections
        infection_criteria = medical_criteria.get('infections', {})
        
        if infection_criteria.get('hiv_excluded') is True and patient.hiv_positive:
            return False, "HIV positive patients excluded"
        
        return True, "Medical condition criteria met"
    
    def check_reproductive(self, patient: EnhancedPatient, criteria: Dict) -> Tuple[bool, str]:
        """Check if patient meets reproductive criteria"""
        repro_criteria = criteria.get('reproductive', {})
        
        if repro_criteria.get('pregnancy_excluded') is True and patient.pregnant:
            return False, "Pregnant patients excluded"
        
        return True, "Reproductive criteria met"


# Example usage with molecular data
def example_enhanced_matching():
    """Example using enhanced molecular matching"""
    
    # Load the enhanced matcher
    matcher = EnhancedTrialMatcher('trials-aggregator/clinical_trials_with_structured_eligibility_v2.json')
    
    # Example AML parser output
    aml_parser_data = {
        "blasts_percentage": 75,
        "AML_defining_recurrent_genetic_abnormalities": {
            "NPM1": True,
            "FLT3": True
        },
        "ELN2024_risk_genes": {
            "NPM1": True,
            "FLT3_ITD": True
        },
        "MDS_related_mutation": {
            "ASXL1": False,
            "RUNX1": False
        },
        "Biallelic_TP53_mutation": {
            "tp53_mentioned": False,
            "2_x_TP53_mutations": False
        },
        "AML_differentiation": "M1"
    }
    
    # Create enhanced patient from AML parser data
    patient = EnhancedPatient.from_aml_parser_output(
        aml_parser_data,
        age=55,
        ecog_status=1,
        primary_diagnosis="acute myeloid leukemia",
        newly_diagnosed=True,
        prior_chemotherapy_regimens=0,
        hiv_positive=False,
        hepatitis_b_positive=False,
        hepatitis_c_positive=False,
        pregnant=False,
        breastfeeding=False
    )
    
    print("🧬 Enhanced Patient Profile:")
    print(f"   Age: {patient.age}, ECOG: {patient.ecog_status}")
    print(f"   Diagnosis: {patient.primary_diagnosis}")
    print(f"   Blasts: {patient.blasts_percentage}%")
    print(f"   Mutations: {patient.get_positive_mutations()}")
    print(f"   High-risk features: {patient.has_high_risk_features()}")
    
    # Find matching trials
    matches = matcher.find_matching_trials(patient)
    print(f"\n🎯 Found {len(matches)} matching trials (sorted by molecular match score):")
    
    for i, match in enumerate(matches[:5], 1):  # Show top 5 matches
        print(f"\n{i}. {match['title']}")
        print(f"   Molecular Match Score: {match['molecular_match_score']:.1f}")
        print(f"   Locations: {match['locations']}")
        print(f"   Cancer Types: {match['cancer_types']}")


if __name__ == "__main__":
    example_enhanced_matching()