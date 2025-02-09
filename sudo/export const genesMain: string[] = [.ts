export const genesMain: string[] = [
  'SF3B1',
  'ASXL1',
  'SRSF2',
  'DNMT3A',
  'RUNX1',
  'U2AF1',
  'EZH2',
  'CBL',
  'NRAS',
  'IDH2',
  'KRAS',
  'ETV6',
  'NPM1',
]

export const genesRes: string[] = [
  'BCOR',
  'STAG2',
  'NF1',
  'CEBPA',
  'SETBP1',
  'PTPN11',
  'GATA2',
  'PRPF8',
  'BCORL1',
  'ETNK1',
  'PPM1D',
  'PHF6',
  'WT1',
  'IDH1',
  'GNB1',
]


const fieldsDefinitions: {[key: string]: FieldDefinition} = {
  // Clinical
  'BM_BLAST': {
    label: 'Bone Marrow Blasts',
    category: 'clinical',
    type: 'number',
    required: true,
    varName: 'BM_BLAST',
    units: '%',
    min: 0,
    max: 30,
  },
  'HB': {
    label: 'Hemoglobin',
    category: 'clinical',
    type: 'number',
    required: true,
    varName: 'HB',
    units: ' g/dl',
    min: 4,
    max: 20,
    notes:
      'Useful conversion for Hb values: 10 g/dL= 6.2 mmol/L, 8 g/dL= 5.0 mmol/L',
  },
  'PLT': {
    label: 'Platelet Count',
    category: 'clinical',
    type: 'number',
    required: true,
    varName: 'PLT',
    units: ' 1e9/l',
    min: 0,
    max: 2000,
  },
  'ANC': {
    label: 'Absolute Neutrophil Count',
    category: 'clinical',
    type: 'number',
    required: true,
    varName: 'ANC',
    min: 0,
    max: 15,
    units: ' 1e9/l',
    notes: 'Only needed to calculate IPSS-R',
  },
  'AGE': {
    label: 'Age',
    category: 'clinical',
    type: 'number',
    required: false,
    varName: 'AGE',
    units: ' years',
    min: 18,
    max: 120,
    notes: 'Only needed to calculate age-adjusted IPSS-R',
    allowNull: true,
  },
  // Cytogenetics
  'CYTO_IPSSR': {
    label: 'Cytogenetics Category',
    category: 'cytogenetics',
    type: 'string',
    required: true,
    varName: 'CYTO_IPSSR',
    values: [
      'Very Good',
      'Good',
      'Intermediate',
      'Poor',
      'Very Poor',
    ]
  },
  // Molecular Data
  'TP53mut': {
    label: `Number of TP53 mutations`,
    category: 'molecular',
    type: 'string',
    required: false,
    default: '0',
    varName: 'TP53mut',
    values: [    
      '0',
      '1',
      '2 or more'
    ]
  },
  'TP53maxvaf': {
    label: `Maximum VAF of TP53 mutation(s)`,
    category: 'molecular',
    type: 'number',
    required: false,
    default: 0,
    varName: 'TP53maxvaf',
    units: '%',
    min: 0,
    max: 100,
  },
  'TP53loh': {
    label: `Loss of heterozygosity at TP53 locus`,
    category: 'molecular',
    type: 'string',
    required: false,
    default: 0,
    varName: 'TP53loh',
    values: [    
      0,
      1,
      'NA',
    ]
  },
  'MLL_PTD': {
    label: `MLL <or KMT2A> PTD`,
    category: 'molecular',
    type: 'string',
    required: false,
    default: 0,
    varName: 'MLL_PTD',
    values: [    
      0,
      1,
      'NA',
    ]
  },
  'FLT3': {
    label: `FLT3 ITD or TKD`,
    category: 'molecular',
    type: 'string',
    required: false,
    default: 0,
    varName: 'FLT3',
    values: [    
      0,
      1,
      'NA',
    ]
  },
}

// Cytogenetic Data
const cytogenetics: string[] = [
  'del5q',
  'del7_7q',
  'del17_17p',
  'complex',
]

cytogenetics.forEach((value) => {
  fieldsDefinitions[value] = {
    label: `Presence of ${value}`,
    category: 'molecular',
    type: 'string',
    required: false,
    default: 0,
    varName: value,
    values: [    
      0,
      1,
    ],
  }
})

const genesMain: string[] = [
  'ASXL1',
  'CBL',
  'DNMT3A',
  'ETV6',
  'EZH2',
  'IDH2',
  'KRAS',
  'NPM1',
  'NRAS',
  'RUNX1',
  'SF3B1',
  'SRSF2',
  'U2AF1',
]

const genesResidual: string[] = [
  'BCOR',
  'BCORL1',
  'CEBPA',
  'ETNK1',
  'GATA2',
  'GNB1',
  'IDH1',
  'NF1',
  'PHF6',
  'PPM1D',
  'PRPF8',
  'PTPN11',
  'SETBP1',
  'STAG2',
  'WT1',
]

const genes: string[] = [
  ...genesMain,
  ...genesResidual,
]

genes.forEach((gene) => {
  fieldsDefinitions[gene] = {
    label: gene,
    category: 'molecular',
    type: 'string',
    required: false,
    default: 0,
    varName: gene,
    values: [    
      0,
      1,
      'NA',
    ],
  }
})

// Field Definitions for IPSS-M and IPSS-R
export const ipssmFields: FieldDefinition[] = [
  // Clinical Fields
  fieldsDefinitions['BM_BLAST'],
  fieldsDefinitions['HB'],
  fieldsDefinitions['PLT'],
  // Cytogenetic Fields
  fieldsDefinitions['del5q'],
  fieldsDefinitions['del7_7q'],
  fieldsDefinitions['del17_17p'],
  fieldsDefinitions['complex'],
  fieldsDefinitions['CYTO_IPSSR'],
  // Molecular Fields
  fieldsDefinitions['TP53mut'],
  fieldsDefinitions['TP53maxvaf'],
  fieldsDefinitions['TP53loh'],
  fieldsDefinitions['MLL_PTD'],
  fieldsDefinitions['FLT3'],
  fieldsDefinitions['ASXL1'],
  fieldsDefinitions['CBL'],
  fieldsDefinitions['DNMT3A'],
  fieldsDefinitions['ETV6'],
  fieldsDefinitions['EZH2'],
  fieldsDefinitions['IDH2'],
  fieldsDefinitions['KRAS'],
  fieldsDefinitions['NPM1'],
  fieldsDefinitions['NRAS'],
  fieldsDefinitions['RUNX1'],
  fieldsDefinitions['SF3B1'],
  fieldsDefinitions['SRSF2'],
  fieldsDefinitions['U2AF1'],
  fieldsDefinitions['BCOR'],
  fieldsDefinitions['BCORL1'],
  fieldsDefinitions['CEBPA'],
  fieldsDefinitions['ETNK1'],
  fieldsDefinitions['GATA2'],
  fieldsDefinitions['GNB1'],
  fieldsDefinitions['IDH1'],
  fieldsDefinitions['NF1'],
  fieldsDefinitions['PHF6'],
  fieldsDefinitions['PPM1D'],
  fieldsDefinitions['PRPF8'],
  fieldsDefinitions['PTPN11'],
  fieldsDefinitions['SETBP1'],
  fieldsDefinitions['STAG2'],
  fieldsDefinitions['WT1'],
]

export const ipssrFields: FieldDefinition[] = [
  fieldsDefinitions['BM_BLAST'],
  fieldsDefinitions['HB'],
  fieldsDefinitions['PLT'],
  fieldsDefinitions['ANC'],
  fieldsDefinitions['CYTO_IPSSR'],
  fieldsDefinitions['AGE'],
]

const betas: BetaRiskScore[] = [
  { name: 'CYTOVEC', coeff: 0.287, means: 1.39, worst: 4, best: 0 },
  { name: 'BLAST5', coeff: 0.352, means: 0.922, worst: 4, best: 0 },
  { name: 'TRANSF_PLT100', coeff: -0.222, means: 1.41, worst: 0, best: 2.5 },
  { name: 'HB1', coeff: -0.171, means: 9.87, worst: 2, best: 20 },
  { name: 'SF3B1_alpha', coeff: -0.0794, means: 0.186, worst: 0, best: 1 },
  { name: 'SF3B1_5q', coeff: 0.504, means: 0.0166, worst: 1, best: 0 },
  { name: 'ASXL1', coeff: 0.213, means: 0.252, worst: 1, best: 0 },
  { name: 'SRSF2', coeff: 0.239, means: 0.158, worst: 1, best: 0 },
  { name: 'DNMT3A', coeff: 0.221, means: 0.161, worst: 1, best: 0 },
  { name: 'RUNX1', coeff: 0.423, means: 0.126, worst: 1, best: 0 },
  { name: 'U2AF1', coeff: 0.247, means: 0.0866, worst: 1, best: 0 },
  { name: 'EZH2', coeff: 0.27, means: 0.0588, worst: 1, best: 0 },
  { name: 'CBL', coeff: 0.295, means: 0.0473, worst: 1, best: 0 },
  { name: 'NRAS', coeff: 0.417, means: 0.0362, worst: 1, best: 0 },
  { name: 'IDH2', coeff: 0.379, means: 0.0429, worst: 1, best: 0 },
  { name: 'KRAS', coeff: 0.202, means: 0.0271, worst: 1, best: 0 },
  { name: 'MLL_PTD', coeff: 0.798, means: 0.0247, worst: 1, best: 0 },
  { name: 'ETV6', coeff: 0.391, means: 0.0216, worst: 1, best: 0 },
  { name: 'NPM1', coeff: 0.43, means: 0.0112, worst: 1, best: 0 },
  { name: 'TP53multi', coeff: 1.18, means: 0.071, worst: 1, best: 0 },
  { name: 'FLT3', coeff: 0.798, means: 0.0108, worst: 1, best: 0 },
  { name: 'Nres2', coeff: 0.231, means: 0.388, worst: 2, best: 0 },
]

export default betas

/*
  Define export interfaces for patient data and IPSS scores
*/

export interface PatientInput {
  // Clinical Data
  BM_BLAST: number;
  HB: number;
  PLT: number;
  ANC?: number;
  AGE?: number;
  // Cytogenetic Data
  del5q: string;
  del7_7q: string;
  del17_17p: string;
  complex: string;
  CYTO_IPSSR: string;
  // Molecular Data
  TP53mut?: string;
  TP53maxvaf?: number;
  TP53loh?: string;
  MLL_PTD?: string;
  FLT3?: string;
  ASXL1?: string;
  CBL?: string;
  DNMT3A?: string;
  ETV6?: string;
  EZH2?: string;
  IDH2?: string;
  KRAS?: string;
  NPM1?: string;
  NRAS?: string;
  RUNX1?: string;
  SF3B1?: string;
  SRSF2?: string;
  U2AF1?: string;
  BCOR?: string;
  BCORL1?: string;
  CEBPA?: string;
  ETNK1?: string;
  GATA2?: string;
  GNB1?: string;
  IDH1?: string;
  NF1?: string;
  PHF6?: string;
  PPM1D?: string;
  PRPF8?: string;
  PTPN11?: string;
  SETBP1?: string;
  STAG2?: string;
  WT1?: string;
  // Intermediate Variables
  Nres2: {[key: string]: number};
  SF3B1_5q?: string;
  SF3B1_alpha?: string;
  TP53multi?: string;
  HB1?: number;
  TRANSF_PLT100?: number;
  BLAST5?: number;
  CYTOVEC?: number;
}

/*
  IPSS-R types
*/

interface PatientForIpssrWithCytoNumber {
  // Clinical Data needed to compute Ippsr (Age is optional)
  bmblast: number;
  hb: number;
  plt: number;
  anc: number;
  age?: number;
  cytovec: number;
  cytoIpssr?: string;
}
interface PatientForIpssrWithCytoString {
  // Clinical Data needed to compute Ippsr (Age is optional)
  bmblast: number;
  hb: number;
  plt: number;
  anc: number;
  age?: number;
  cytovec?: number;
  cytoIpssr: string;
}

export type PatientForIpssr = PatientForIpssrWithCytoNumber | PatientForIpssrWithCytoString;

/*
  IPSS-M types
*/

interface IpssmScore {
  riskScore: number;
  riskCat: string;
  contributions: {[key: string]: number};
}

export interface IpssmScores {
  means: IpssmScore;
  best: IpssmScore;
  worst: IpssmScore;
}

/*
  Output  of Annotated Patient Types
*/

export interface PatientWithIpssr {
  // IPSS-R Risk Score
  IPSSR_SCORE?: number;
  IPSSR_CAT?: string;
  // IPSS-RA Risk Score Age-Adjusted (Optional)
  IPSSRA_SCORE?: number | null;
  IPSSRA_CAT?: string | null;
}

export interface PatientWithIpssm {
  // IPSS-M Risk Score: Mean, Best, Worst
  IPSSM_SCORE: number;
  IPSSM_CAT: string;
  IPSSM_SCORE_BEST: number;
  IPSSM_CAT_BEST: string;
  IPSSM_SCORE_WORST: number;
  IPSSM_CAT_WORST: string;
}

export interface PatientOutput extends PatientInput, PatientWithIpssr, PatientWithIpssm {}

/*
  Other types
*/

export interface BetaRiskScore {
  name: string;
  coeff: number;
  means: number;
  worst: number;
  best: number;
}

export interface CsvData {
  [key: string]: number | string
}

export interface FieldDefinition {
  label: string;
  category: string;
  type: string;
  required: boolean;
  default?: number | string;
  varName:string;
  units?: string;
  min?: number;
  max?: number;
  values?: any[];
  notes?: string;
  allowNull?: boolean;
}



const ipssrCat: string[] = [
  'Very Low',
  'Low',
  'Int',
  'High',
  'Very High',
]
const ipssmCat: string[] = [
  'Very Low',
  'Low', 
  'Moderate Low', 
  'Moderate High', 
  'High', 
  'Very High', 
]

// Utility to find value between intervals, and map interval number to value
const cutBreak = (
  value: number, 
  breaks: number[], 
  mapping: (number | string)[], 
  right: boolean = true,
): number | string => {
  for (let i = 1; i < breaks.length; i++) {
    if (right) {
      // Intervals are closed to the right, and open to the left
      if (value > breaks[i - 1] && value <= breaks[i]) {
        return mapping ? mapping[i - 1] : i - 1
      }
    } else {
      // Intervals are open to the right, and closed to the left
      if (value >= breaks[i - 1] && value < breaks[i]) {
        return mapping ? mapping[i - 1] : i - 1
      }
    }
  }
  return NaN // default value
}

/**
 * Compute IPSS-R risk score and risk categories
 * @param {number} bmblast - bone marrow blasts, in %
 * @param {number} hb - hemoglobin, in gram per deciliter
 * @param {number} plt - platelet, in giga per liter
 * @param {number} anc - absolute neutrophile count, in giga per liter
 * @param {number} cytovec - cytogenetic category in numerical form
 * @param {number} cytoIpssr - cytogenetic category in categorical form
 * @param {number} [age] - Age, in years
 *
 * @return {Object} dictionary of ipssr and ipssr-age adjusted, score and category.
 */
const computeIpssr = (
  { bmblast, hb, plt, anc, cytovec, cytoIpssr, age }: PatientForIpssr,
  rounding: boolean = true,
  roundingDigits: number = 4
) : PatientWithIpssr => {
  // Get proper Cytogenetic category
  const cytovecMap: { [key: string]: number } = {'Very Good': 0, 'Good': 1, 'Intermediate': 2, 'Poor': 3, 'Very Poor': 4}
  if (!cytovec && cytoIpssr) {
    cytovec = cytovecMap[cytoIpssr]
  }
  if (cytovec === undefined || cytovec === null || cytovec < 0 || cytovec > 4) {
    throw new Error('Cytogenetic category is not valid.')
  }

  // Get Variable Ranges, defining each category breaks and value mapping
  const bmblastBreak = [-Infinity, 2, 4.99, 10, Infinity]
  const hbBreak = [-Infinity, 8, 10, Infinity]
  const pltBreak = [-Infinity, 50, 100, Infinity]
  const ancBreak = [-Infinity, 0.8, Infinity]
  const ipssrgBreaks = [-Infinity, 1.5, 3, 4.5, 6, Infinity]

  const bmblastMap = [0, 1, 2, 3] //{ 0: 0, 1: 1, 2: 2, 3: 3 }
  const hbMap = [1.5, 1, 0] //{ 0: 1.5, 1: 1, 2: 0 }
  const pltMap = [1, 0.5, 0] //{ 0: 1, 1: 0.5, 2: 0 }
  const ancMap = [0.5, 0] //{ 0: 0.5, 1: 0 }
  
  const bmblastri = Number(cutBreak(bmblast, bmblastBreak, bmblastMap, true))
  const hbri = Number(cutBreak(hb, hbBreak, hbMap, false))
  const pltri = Number(cutBreak(plt, pltBreak, pltMap, false))
  const ancri = Number(cutBreak(anc, ancBreak, ancMap, false))

  // Build IPSS-R raw score 
  let ipssr: string | null = null
  let ipssrRaw: number | null = null

  ipssrRaw = bmblastri + hbri + pltri + ancri + cytovec
  if (rounding) {
    ipssrRaw = round(ipssrRaw, roundingDigits)
  }
  ipssr = cutBreak(ipssrRaw, ipssrgBreaks, ipssrCat).toString()

  // Build IPSS-RA Age-Adjusted if available
  let ipssra: string | null = null
  let ipssraRaw: number | null = null

  if (age !== null && age !== undefined) {
    const ageAdjust = (Number(age) - 70) * (0.05 - ipssrRaw * 0.005)
    ipssraRaw = ipssrRaw + ageAdjust
    if (rounding) {
      ipssraRaw = round(ipssraRaw, roundingDigits)
    }
    ipssra = cutBreak(ipssraRaw, ipssrgBreaks, ipssrCat).toString()
  }
  return {
    IPSSR_SCORE: ipssrRaw,
    IPSSR_CAT: ipssr,
    IPSSRA_SCORE: ipssraRaw,
    IPSSRA_CAT: ipssra,
  }
}

/**
 * Compute IPSS-M risk score and risk categories
 * @param {Array.<number>} patientValues - list of observed values for one individual
 * @param {boolean} [rounding] - flag if rounding should be applied
 * @param {number} [roundingDigits] - decimal digits to round
 * @param {Array.<number>} [cutpoints] - list of cutoff values of group categories
 *
 * @return {Object} dictionary of ipssm: score, category and contribution of each var.
 */

const computeIpssm = (
  patientValues: PatientInput,
  rounding: boolean = true,
  roundingDigits: number = 2,
  cutpoints: number[] = [-1.5, -0.5, 0, 0.5, 1.5]
) : IpssmScores => {
  // relative risk contribution of each variable. log2 is just a scaling factor
  const scores: IpssmScores = {
    means: {
      riskScore: 0,
      riskCat: '',
      contributions: {},
    },
    worst: {
      riskScore: 0,
      riskCat: '',
      contributions: {},
    },
    best: {
      riskScore: 0,
      riskCat: '',
      contributions: {},
    },
  }

  Object.keys(scores).forEach((scenario) => {
    const contributions: {[key: string]: number} = {}

    betas.forEach((beta) => {
      let value = patientValues[beta.name as keyof PatientInput]

      // Impute if missing variable
      if (value === 'NA' || value === null) {
        value = beta[scenario as keyof BetaRiskScore]
      }
      if (beta.name === 'Nres2') {
        value = patientValues.Nres2[scenario]
      }

      // Contribution Normalization
      contributions[beta.name] =
        ((Number(value) - beta.means) * beta.coeff) / Math.log(2)
    })

    // risk score
    let riskScore = Object.values(contributions).reduce((sum: number, x) => sum + x, 0)
    if (rounding) {
      riskScore = round(riskScore, roundingDigits)
    }

    // risk categories
    const riskCat = cutBreak(
      riskScore,
      [-Infinity, ...cutpoints, Infinity],
      ipssmCat
    ).toString()

    scores[scenario as keyof IpssmScores] = {
      riskScore: riskScore,
      riskCat: riskCat,
      contributions: contributions,
    }
  })
  return scores
}

export { computeIpssr, computeIpssm }
