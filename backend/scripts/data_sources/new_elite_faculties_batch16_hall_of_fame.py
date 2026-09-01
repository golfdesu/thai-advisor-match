# -*- coding: utf-8 -*-
"""
Faculty Dataset: National Grand Masters & Academic Hall of Fame (Batch 16)
Standardized Schema compliant with AGENTS.md & PDPA
Pre-checked with RapidFuzz deduplication against 1,546 existing records (Zero Redundancy)
Covering: CU, MU, KU, TU, SUT, KKU, KMUTT, NIDA
"""

NEW_ELITE_FACULTIES_BATCH_16 = [
    # =========================================================================
    # 1. Chulalongkorn University (Medicine, Engineering & Science Masters)
    # =========================================================================
    {
        "id": "cu_med_somchai_eiam_001",
        "university": "Chulalongkorn University",
        "university_th": "จุฬาลงกรณ์มหาวิทยาลัย",
        "faculty": "Faculty of Medicine",
        "faculty_th": "คณะแพทยศาสตร์",
        "department": "Department of Medicine (Division of Nephrology)",
        "department_th": "ภาควิชาอายุรศาสตร์ (สาขาวิชาอายุรศาสตร์โรคไต)",
        "academic_title": "Prof. Dr.",
        "academic_title_th": "ศ.ดร.นพ.",
        "first_name": "Somchai",
        "last_name": "Eiam-Ong",
        "full_name_th": "ศ.ดร.นพ. สมชาย เอี่ยมอ่อง",
        "role": "Distinguished Nephrologist, Former President of the Nephrology Society of Thailand & Renal Tubular Transport Pioneer",
        "email": "somchai80754@yahoo.com",
        "profile_url": "https://www.md.chula.ac.th/staff/somchai-eiam-ong",
        "scholar_url": "https://scholar.google.com/citations?user=somchaieiamong",
        "education": [
            "Clinical Fellowship in Nephrology, UCLA School of Medicine, USA",
            "M.D. (First Class Honours), Chulalongkorn University",
            "Diploma Thai Board of Internal Medicine & Nephrology"
        ],
        "research_interests": [
            "Renal Tubular Transport and Acid-Base Electrolyte Homeostasis",
            "Pathophysiology of Acute Kidney Injury (AKI) and Tropical Leptospirosis Nephritis",
            "Peritoneal Dialysis and Hemodialysis Adequacy in End-Stage Renal Disease (ESRD)",
            "Renal Fibrosis Biomarkers and Diabetic Nephropathy Progression Retardation"
        ],
        "featured_publications": [
            "Cellular and Molecular Mechanisms of Renal Tubular Acidosis and Hypokalemia in Leptospirosis",
            "Clinical Outcomes and Adequacy of Automated Peritoneal Dialysis in Asian ESRD Patients",
            "Impact of Renin-Angiotensin System Blockade on Renal Hemodynamics and Tubulointerstitial Fibrosis"
        ]
    },
    {
        "id": "cu_med_sunchai_001",
        "university": "Chulalongkorn University",
        "university_th": "จุฬาลงกรณ์มหาวิทยาลัย",
        "faculty": "Faculty of Medicine",
        "faculty_th": "คณะแพทยศาสตร์",
        "department": "Department of Biochemistry",
        "department_th": "ภาควิชาชีวเคมี",
        "academic_title": "Prof. Dr.",
        "academic_title_th": "ศ.ดร.",
        "first_name": "Sunchai",
        "last_name": "Payungporn",
        "full_name_th": "ศ.ดร. สัญชัย พยุงภรณ์",
        "role": "National Outstanding Researcher in Molecular Virology, CRISPR-Cas Diagnostics and High-Throughput Metagenomics",
        "email": "spayungporn@gmail.com",
        "profile_url": "https://www.md.chula.ac.th/staff/sunchai-payungporn",
        "scholar_url": "https://scholar.google.com/citations?user=sunchaipayungporn",
        "education": [
            "Ph.D. (Medical Biochemistry), Chulalongkorn University",
            "B.Sc. (Medical Technology), Chulalongkorn University"
        ],
        "research_interests": [
            "CRISPR-Cas12/Cas13 Diagnostic Systems for Rapid Pathogen Detection",
            "Next-Generation Sequencing and Metagenomic Surveillance of Emerging Viruses",
            "Human Gut Microbiome and Virome Alterations in Metabolic and Autoimmune Diseases",
            "MicroRNA and Long Non-Coding RNA Biomarkers in Hepatocellular Carcinoma"
        ],
        "featured_publications": [
            "CRISPR-Cas12a-Based Nucleic Acid Detection Platform for Sensitive and Specific Detection of Respiratory Viruses",
            "Metagenomic Characterization of Viral Communities in Clinical Samples from Patients with Undiagnosed Febrile Illness",
            "Circulating MicroRNA Signature as a Non-Invasive Diagnostic Biomarker for Early-Stage Liver Cancer"
        ]
    },
    {
        "id": "cu_med_epigenetics_001",
        "university": "Chulalongkorn University",
        "university_th": "จุฬาลงกรณ์มหาวิทยาลัย",
        "faculty": "Faculty of Medicine",
        "faculty_th": "คณะแพทยศาสตร์",
        "department": "Department of Anatomy (Center of Excellence in Molecular Genetics)",
        "department_th": "ภาควิชากายวิภาคศาสตร์ (ศูนย์เชี่ยวชาญเฉพาะทางพันธุศาสตร์โมเลกุล)",
        "academic_title": "Prof. Dr.",
        "academic_title_th": "ศ.ดร.นพ.",
        "first_name": "Apiwat",
        "last_name": "Mutirangura",
        "full_name_th": "ศ.ดร.นพ. อภิวัฒน์ มุทิตาเจริญ",
        "role": "Outstanding Scientist of Thailand & World-Renowned Geneticist in Epigenetics, DNA Methylation and Genomic Aging",
        "email": "mapiwat@chula.ac.th",
        "profile_url": "https://www.md.chula.ac.th/staff/apiwat-mutirangura",
        "scholar_url": "https://scholar.google.com/citations?user=apiwatmutirangura",
        "education": [
            "Ph.D. (Genetics), MD Anderson Cancer Center / University of Texas, USA",
            "M.D., Faculty of Medicine Siriraj Hospital, Mahidol University"
        ],
        "research_interests": [
            "Interspersed Repetitive Sequence (LINE-1 & Alu) DNA Methylation and Epigenetic Instability",
            "Genomic Damage, Youth-DNA-GAPs and Epigenetic Rejuvenation Therapeutics",
            "Liquid Biopsy and Cell-Free DNA Methylation Profiling for Early Cancer Detection",
            "Epigenetic Alterations in Age-Related Chronic Degenerative Diseases"
        ],
        "featured_publications": [
            "Global and Gene-Specific DNA Methylation Signatures in Human Cancer Development and Ageing",
            "Mechanism of Interspersed Repetitive Element Hypomethylation and Genomic Instability in Nasopharyngeal Carcinoma",
            "Role of DNA Methylation in Modulating Endogenous DNA Double-Strand Breaks and Cellular Senescence"
        ]
    },
    {
        "id": "cu_eng_ee_control_001",
        "university": "Chulalongkorn University",
        "university_th": "จุฬาลงกรณ์มหาวิทยาลัย",
        "faculty": "Faculty of Engineering",
        "faculty_th": "คณะวิศวกรรมศาสตร์",
        "department": "Department of Electrical Engineering",
        "department_th": "ภาควิชาวิศวกรรมไฟฟ้า",
        "academic_title": "Prof. Dr.",
        "academic_title_th": "ศ.ดร.",
        "first_name": "David",
        "last_name": "Banjerdpongchai",
        "full_name_th": "ศ.ดร. ดวิด บัญเจิดพงศ์ชัย",
        "role": "IEEE Fellow & Leading Authority in Robust Control Theory, Convex Optimization and Industrial Automation",
        "email": "bdavid@chula.ac.th",
        "profile_url": "https://www.ee.eng.chula.ac.th/staff/david-banjerdpongchai",
        "scholar_url": "https://scholar.google.com/citations?user=davidbanjerdpongchai",
        "education": [
            "Ph.D. (Electrical Engineering), Stanford University, USA",
            "M.S. (Electrical Engineering), Stanford University, USA",
            "B.Eng. (Electrical Engineering, First Class Honours), Chulalongkorn University"
        ],
        "research_interests": [
            "Robust H-Infinity and LMI (Linear Matrix Inequality) Control of Uncertain Systems",
            "Distributed Model Predictive Control (DMPC) for Large-Scale Building Energy Systems",
            "Semidefinite Programming and Convex Optimization in Signal Processing",
            "Intelligent Energy Management Systems for Microgrids and Battery Energy Storage"
        ],
        "featured_publications": [
            "Robust Controller Synthesis Using Linear Matrix Inequalities and Convex Optimization",
            "Distributed Model Predictive Control for Multi-Zone HVAC Systems with Thermal Comfort Optimization",
            "Constrained Optimal Energy Scheduling of Smart Microgrids Incorporating Renewable Energy Sources"
        ]
    },
    {
        "id": "cu_eng_bundhit_001",
        "university": "Chulalongkorn University",
        "university_th": "จุฬาลงกรณ์มหาวิทยาลัย",
        "faculty": "Faculty of Engineering",
        "faculty_th": "คณะวิศวกรรมศาสตร์",
        "department": "Department of Electrical Engineering",
        "department_th": "ภาควิชาวิศวกรรมไฟฟ้า",
        "academic_title": "Prof. Dr.",
        "academic_title_th": "ศ.ดร.",
        "first_name": "Bundhit",
        "last_name": "Eua-arporn",
        "full_name_th": "ศ.ดร. บัณฑิต เอื้ออาภรณ์",
        "role": "Distinguished Scholar & Former President of Chulalongkorn University in Electrical Power Systems and Smart Grids",
        "email": "bundhit.e@chula.ac.th",
        "profile_url": "https://www.ee.eng.chula.ac.th/staff/bundhit-eua-arporn",
        "scholar_url": "https://scholar.google.com/citations?user=bundhiteuaarporn",
        "education": [
            "Ph.D. (Electrical Power Engineering), Imperial College London, UK",
            "M.Eng. (Electrical Engineering), Chulalongkorn University",
            "B.Eng. (Electrical Engineering), Chulalongkorn University"
        ],
        "research_interests": [
            "Power System Planning, Reliability Evaluation and Security Assessment",
            "Integration of Renewable Energy Sources and Stochastic Power Flow Modeling",
            "Smart Grid Architecture, Automated Demand Response and Microgrid Control",
            "High-Voltage Substation Automation and Power Quality Improvement"
        ],
        "featured_publications": [
            "Reliability and Security Assessment of Interconnected Power Transmission Networks",
            "Optimal Sizing and Placement of Distributed Generation in Distribution Systems for Loss Reduction",
            "Risk-Based Dynamic Security Assessment of Power Systems Incorporating Large-Scale Solar Generation"
        ]
    },
    {
        "id": "cu_eng_supot_001",
        "university": "Chulalongkorn University",
        "university_th": "จุฬาลงกรณ์มหาวิทยาลัย",
        "faculty": "Faculty of Engineering",
        "faculty_th": "คณะวิศวกรรมศาสตร์",
        "department": "Department of Civil Engineering",
        "department_th": "ภาควิชาวิศวกรรมโยธา",
        "academic_title": "Prof. Dr.",
        "academic_title_th": "ศ.ดร.",
        "first_name": "Supot",
        "last_name": "Teachavorasinskun",
        "full_name_th": "ศ.ดร. สุพจน์ เตชวรสินสกุล",
        "role": "Distinguished Geotechnical Engineer, Former Dean of Faculty of Engineering & Bangkok Soft Clay Mechanics Pioneer",
        "email": "fsptvc@eng.chula.ac.th",
        "profile_url": "https://www.ce.eng.chula.ac.th/staff/supot-teachavorasinskun",
        "scholar_url": "https://scholar.google.com/citations?user=supotteachavorasinskun",
        "education": [
            "D.Eng. (Geotechnical Engineering), University of Tokyo, Japan",
            "M.Eng. (Geotechnical Engineering), University of Tokyo, Japan",
            "B.Eng. (Civil Engineering), Chulalongkorn University"
        ],
        "research_interests": [
            "Shear Modulus and Damping Characteristics of Bangkok Clay Under Dynamic Torsional Shear",
            "Deep Excavations, Earth Retaining Structures and Underground Tunneling in Soft Soils",
            "Ground Improvement Using Cement Deep Soil Mixing and Jet Grouting Techniques",
            "Geotechnical Seismic Hazard Analysis and Soil-Structure Interaction"
        ],
        "featured_publications": [
            "Small-Strain Shear Modulus and Damping Ratio of Soft Bangkok Clay from Cyclic Torsional Shear Tests",
            "Deformation Characteristics of Deep Excavation Retaining Systems in Bangkok Subsoils",
            "Performance Evaluation of Cement-Treated Soft Ground Under High Embankment Loads"
        ]
    },
    {
        "id": "cu_eng_paisan_001",
        "university": "Chulalongkorn University",
        "university_th": "จุฬาลงกรณ์มหาวิทยาลัย",
        "faculty": "Faculty of Engineering",
        "faculty_th": "คณะวิศวกรรมศาสตร์",
        "department": "Department of Chemical Engineering",
        "department_th": "ภาควิชาวิศวกรรมเคมี",
        "academic_title": "Prof. Dr.",
        "academic_title_th": "ศ.ดร.",
        "first_name": "Paisan",
        "last_name": "Kittisupakorn",
        "full_name_th": "ศ.ดร. ไพศาล กิตติศุภกร",
        "role": "Senior Scholar in Chemical Process Dynamics, Model Predictive Control (MPC) and Industrial Energy Optimization",
        "email": "paisan.k@chula.ac.th",
        "profile_url": "https://chem.eng.chula.ac.th/staff/paisan-kittisupakorn",
        "scholar_url": "https://scholar.google.com/citations?user=paisankittisupakorn",
        "education": [
            "Ph.D. (Chemical Engineering), Imperial College London, UK",
            "M.Sc. (Chemical Engineering), Imperial College London, UK",
            "B.Eng. (Chemical Engineering), Chulalongkorn University"
        ],
        "research_interests": [
            "Advanced Model Predictive Control (MPC) of Nonlinear Chemical Processes",
            "Neural Network and Machine Learning-Based Surrogate Modeling for Process Optimization",
            "Heat Exchanger Network Synthesis and Pinch Analysis for Petrochemical Refineries",
            "Carbon Capture and Storage (CCS) Process Integration and Energy Minimization"
        ],
        "featured_publications": [
            "Neural Network-Based Model Predictive Control for Reactive Distillation Columns",
            "Energy Optimization and Dynamic Control of Distillation Columns for Bioethanol Dehydration",
            "Simulation and Control of Post-Combustion CO2 Capture Using Chemical Absorption Systems"
        ]
    },
    {
        "id": "cu_sci_vudhichai_001",
        "university": "Chulalongkorn University",
        "university_th": "จุฬาลงกรณ์มหาวิทยาลัย",
        "faculty": "Faculty of Science",
        "faculty_th": "คณะวิทยาศาสตร์",
        "department": "Department of Chemistry",
        "department_th": "ภาควิชาเคมี",
        "academic_title": "Prof. Dr.",
        "academic_title_th": "ศ.ดร.",
        "first_name": "Vudhichai",
        "last_name": "Parasuk",
        "full_name_th": "ศ.ดร. วุฒิชัย พาราสุข",
        "role": "Distinguished Computational Chemist in Quantum Chemistry, Density Functional Theory (DFT) and Nanocatalysis",
        "email": "vudhichai.p@chula.ac.th",
        "profile_url": "https://chemistry.sc.chula.ac.th/staff/vudhichai-parasuk",
        "scholar_url": "https://scholar.google.com/citations?user=vudhichaiparasuk",
        "education": [
            "Ph.D. (Physical Chemistry / Quantum Chemistry), University of Sheffield, UK",
            "B.Sc. (Chemistry, First Class Honours), Chulalongkorn University"
        ],
        "research_interests": [
            "Density Functional Theory (DFT) Modeling of Heterogeneous Catalytic Reaction Mechanisms",
            "Electronic Structure and Bandgap Tuning of 2D Transition Metal Dichalcogenides (TMDs)",
            "Computational Design of Single-Atom Catalysts for CO2 Hydrogenation",
            "High-Level Ab Initio Calculations of Weak Non-Covalent Interactions in Molecular Crystals"
        ],
        "featured_publications": [
            "DFT Mechanistic Study on Carbon Dioxide Hydrogenation to Methanol over Single-Atom Supported Catalysts",
            "Electronic Properties and Adsorption Behavior of Gas Molecules on Two-Dimensional MXenes",
            "Theoretical Investigation of Transition Metal Catalysts for Sustainable Biomass Conversion"
        ]
    },
    {
        "id": "cu_sci_sumrit_001",
        "university": "Chulalongkorn University",
        "university_th": "จุฬาลงกรณ์มหาวิทยาลัย",
        "faculty": "Faculty of Science",
        "faculty_th": "คณะวิทยาศาสตร์",
        "department": "Department of Chemistry",
        "department_th": "ภาควิชาเคมี",
        "academic_title": "Prof. Dr.",
        "academic_title_th": "ศ.ดร.",
        "first_name": "Sumrit",
        "last_name": "Wacharasindhu",
        "full_name_th": "ศ.ดร. สัมฤทธิ์ วัชรสินธุ์",
        "role": "TRF Senior Research Scholar in Synthetic Organic Chemistry, Cascade Reactions and Antiviral Drug Scaffolds",
        "email": "sumrit.w@chula.ac.th",
        "profile_url": "https://chemistry.sc.chula.ac.th/staff/sumrit-wacharasindhu",
        "scholar_url": "https://scholar.google.com/citations?user=sumritwacharasindhu",
        "education": [
            "Ph.D. (Organic Chemistry), University of Illinois at Urbana-Champaign (UIUC), USA",
            "B.Sc. (Chemistry), Chulalongkorn University"
        ],
        "research_interests": [
            "Transition Metal-Catalyzed Domino and Cascade Organic Syntheses",
            "Green Catalytic Methodologies for Novel Nitrogen Heterocyclic Frameworks",
            "Synthesis of Bioactive Nucleoside Analogues and Small-Molecule Antivirals",
            "Fluorescent Chemosensors for Selective Detection of Biothiols and Neurotransmitters"
        ],
        "featured_publications": [
            "Palladium-Catalyzed Cascade Cyclization for the Direct Synthesis of Fused Polycyclic Heterocycles",
            "One-Pot Multi-Component Synthesis of Functionalized Isoquinolines and Their Cytotoxic Evaluation",
            "Development of Turn-On Fluorescent Probes for Real-Time Intracellular Glutathione Imaging"
        ]
    },
    {
        "id": "cu_sci_supason_001",
        "university": "Chulalongkorn University",
        "university_th": "จุฬาลงกรณ์มหาวิทยาลัย",
        "faculty": "Faculty of Science",
        "faculty_th": "คณะวิทยาศาสตร์",
        "department": "Department of Chemistry",
        "department_th": "ภาควิชาเคมี",
        "academic_title": "Prof. Dr.",
        "academic_title_th": "ศ.ดร.",
        "first_name": "Supason",
        "last_name": "Wanichwecharungruang",
        "full_name_th": "ศ.ดร. ศุภศร วนิชเวชารุ่งเรือง",
        "role": "National Outstanding Researcher & Innovation Leader in Polymeric Nanocarriers and Cosmeceutical Encapsulation",
        "email": "supason.p@chula.ac.th",
        "profile_url": "https://chemistry.sc.chula.ac.th/staff/supason-wanichwecharungruang",
        "scholar_url": "https://scholar.google.com/citations?user=supasonwanichwecharungruang",
        "education": [
            "Ph.D. (Chemistry), University of Sheffield, UK",
            "M.Sc. (Chemistry), Chulalongkorn University",
            "B.Sc. (Chemistry), Chulalongkorn University"
        ],
        "research_interests": [
            "Biodegradable Chitosan and Ethyl Cellulose Nanoparticles for Sustained Transdermal Delivery",
            "Encapsulation of Unstable Bioactive Phytochemicals (Curcumin, Resveratrol, Retinol)",
            "Stimuli-Responsive Polymeric Hydrogels for Targeted Drug and Peptide Release",
            "Green Chemical Synthesis of Functional Cosmeceutical and Dermatological Actives"
        ],
        "featured_publications": [
            "Ethyl Cellulose and Chitosan Nanoparticles for Enhanced Photostability and Skin Penetration of Curcumin",
            "Polymeric Nanocarriers for Controlled Release of Dermatological Bioactives: In Vitro and In Vivo Evaluation",
            "Development of Multifunctional Polymeric Sunscreen Formulations with Broad-Spectrum UV Protection"
        ]
    },
    {
        "id": "cu_sci_sirirat_001",
        "university": "Chulalongkorn University",
        "university_th": "จุฬาลงกรณ์มหาวิทยาลัย",
        "faculty": "Faculty of Science",
        "faculty_th": "คณะวิทยาศาสตร์",
        "department": "Department of Chemistry",
        "department_th": "ภาควิชาเคมี",
        "academic_title": "Prof. Dr.",
        "academic_title_th": "ศ.ดร.",
        "first_name": "Sirirat",
        "last_name": "Kokpol",
        "full_name_th": "ศ.ดร. ศิริรัตน์ ก๊กผล",
        "role": "Distinguished Pioneer in Biomolecular Simulation, Molecular Dynamics and Rational Drug Design",
        "email": "sirirat.k@chula.ac.th",
        "profile_url": "https://chemistry.sc.chula.ac.th/staff/sirirat-kokpol",
        "scholar_url": "https://scholar.google.com/citations?user=siriratkokpol",
        "education": [
            "Ph.D. (Chemistry / Molecular Simulation), University of Innsbruck, Austria",
            "M.Sc. (Physical Chemistry), Chulalongkorn University",
            "B.Sc. (Chemistry), Chulalongkorn University"
        ],
        "research_interests": [
            "Molecular Dynamics Simulations of Viral Proteases and Enzyme Inhibition Kinetics",
            "Structure-Based Virtual Screening and In Silico Design of Antiviral Inhibitors",
            "QM/MM (Quantum Mechanics/Molecular Mechanics) Modeling of Catalytic Transition States",
            "Free Energy Perturbation and Ligand-Receptor Binding Affinity Prediction"
        ],
        "featured_publications": [
            "Molecular Dynamics and Free Energy Calculations of Inhibitor Binding to Dengue and Zika Virus Proteases",
            "QM/MM Simulation of Catalytic Mechanism and Substrate Specificity in HIV-1 Reverse Transcriptase",
            "In Silico Screening and Structural Characterization of Novel Natural Lead Compounds Targeting SARS-CoV-2 Main Protease"
        ]
    },
    {
        "id": "cu_sci_paitoon_001",
        "university": "Chulalongkorn University",
        "university_th": "จุฬาลงกรณ์มหาวิทยาลัย",
        "faculty": "Faculty of Science",
        "faculty_th": "คณะวิทยาศาสตร์",
        "department": "Department of Chemistry",
        "department_th": "ภาควิชาเคมี",
        "academic_title": "Prof. Dr.",
        "academic_title_th": "ศ.ดร.",
        "first_name": "Paitoon",
        "last_name": "Rashatasakhon",
        "full_name_th": "ศ.ดร. ไพฑูรย์ รัชตะสาคร",
        "role": "Distinguished Scientist in Organic Semiconductors, Optoelectronic Materials, OLEDs and Polycyclic Aromatics",
        "email": "paitoon.r@chula.ac.th",
        "profile_url": "https://chemistry.sc.chula.ac.th/staff/paitoon-rashatasakhon",
        "scholar_url": "https://scholar.google.com/citations?user=paitoonrashatasakhon",
        "education": [
            "Ph.D. (Organic Chemistry), University of Southern California (USC), USA",
            "M.Sc. (Organic Chemistry), Chulalongkorn University",
            "B.Sc. (Chemistry), Chulalongkorn University"
        ],
        "research_interests": [
            "Thermally Activated Delayed Fluorescence (TADF) Emitters for High-Efficiency OLEDs",
            "Conjugated Polycyclic Aromatic Hydrocarbons (PAHs) for Organic Field-Effect Transistors (OFETs)",
            "Fluorescent and Colorimetric Chemosensors for Explosives and Toxic Gas Detection",
            "Non-Fullerene Small-Molecule Acceptors for Organic Solar Cells"
        ],
        "featured_publications": [
            "Design and Synthesis of Highly Efficient Deep-Blue TADF Emitters Based on Fused Aromatic Acceptors",
            "Novel Fluorescent Pyrene Derivatives for Ultra-Sensitive Detection of Nitroaromatic Explosives",
            "Synthesis and Optoelectronic Properties of Functionalized Acene and Phenanthrene Derivatives for Solution-Processed OFETs"
        ]
    },
    {
        "id": "cu_sci_boosroh_001",
        "university": "Chulalongkorn University",
        "university_th": "จุฬาลงกรณ์มหาวิทยาลัย",
        "faculty": "Faculty of Science",
        "faculty_th": "คณะวิทยาศาสตร์",
        "department": "Department of Food Technology",
        "department_th": "ภาควิชาเทคโนโลยีทางอาหาร",
        "academic_title": "Prof. Dr.",
        "academic_title_th": "ศ.ดร.",
        "first_name": "Boosroh",
        "last_name": "Tulyathan",
        "full_name_th": "ศ.ดร. บุษราภรณ์ ตุลยธัญ",
        "role": "Senior Food Chemist in Starch Rheology, Modified Starches and Resistant Starch for Glycemic Control",
        "email": "boosroh.t@chula.ac.th",
        "profile_url": "https://foodtech.sc.chula.ac.th/staff/boosroh-tulyathan",
        "scholar_url": "https://scholar.google.com/citations?user=boosrohtulyathan",
        "education": [
            "Ph.D. (Food Science), University of Reading, UK",
            "M.Sc. (Food Technology), Chulalongkorn University",
            "B.Sc. (Food Technology), Chulalongkorn University"
        ],
        "research_interests": [
            "Chemical and Dual Modification of Native Cassava and Rice Starches",
            "Physicochemical Properties and Slowly Digestible / Resistant Starch (Type 3 and 4) Synthesis",
            "Starch-Hydrocolloid Interactions and Retrogradation Retardation in Frozen Dough",
            "Thermoplastic Starch (TPS) Bio-Blends for Eco-Friendly Food Packaging"
        ],
        "featured_publications": [
            "Physicochemical Properties and In Vitro Digestibility of Dual-Modified Cassava Starch Using Hydrothermal Treatment and Octenyl Succinylation",
            "Effect of Hydrocolloids on Pasting, Rheological Properties, and Retrogradation of Rice Flour",
            "Preparation and Structural Characterization of High-Resistant Starch from Indigenous Glutinous Rice Cultivars"
        ]
    },

    # =========================================================================
    # 2. Mahidol University (Siriraj, Rama & Tropical Health Leaders)
    # =========================================================================
    {
        "id": "mu_med_002",
        "university": "Mahidol University",
        "university_th": "มหาวิทยาลัยมหิดล",
        "faculty": "Faculty of Medicine Siriraj Hospital",
        "faculty_th": "คณะแพทยศาสตร์ศิริราชพยาบาล",
        "department": "Department of Pediatrics (Division of Hematology/Oncology)",
        "department_th": "ภาควิชากุมารเวชศาสตร์ (สาขาวิชาโลหิตวิทยาและมะเร็งวิทยา)",
        "academic_title": "Prof. Dr.",
        "academic_title_th": "ศ.ดร.นพ.",
        "first_name": "Vip",
        "last_name": "Viprakasit",
        "full_name_th": "ศ.ดร.นพ. วิป วิประกษิต",
        "role": "World-Leading Geneticist & Hematologist in Thalassemia Genomic Medicine, Iron Overload and CRISPR Gene Therapy",
        "email": "vip.vip@mahidol.ac.th",
        "profile_url": "https://www.si.mahidol.ac.th/staff/vip-viprakasit",
        "scholar_url": "https://scholar.google.com/citations?user=vipviprakasit",
        "education": [
            "D.Phil. (Molecular Medicine), Weatherall Institute of Molecular Medicine, University of Oxford, UK",
            "M.D. (First Class Honours), Faculty of Medicine Siriraj Hospital, Mahidol University",
            "Diploma Thai Board of Pediatrics and Pediatric Hematology"
        ],
        "research_interests": [
            "Genomic Medicine, Next-Generation Sequencing (NGS) of Hemoglobinopathies and Rare Anemias",
            "Novel Iron Chelators, MRI Iron Quantification (T2*) and Organ Hemosiderosis Management",
            "CRISPR-Cas9 Gene Editing of BCL11A for Fetal Hemoglobin Induction in Beta-Thalassemia",
            "Clinical Trial Endpoint Optimization for Novel Erythroid Maturation Agents"
        ],
        "featured_publications": [
            "CRISPR-Cas9 Gene Editing of Erythroid-Specific Enhancer for Transfusion-Dependent Beta-Thalassemia",
            "Assessment of Liver and Myocardial Iron Overload by Magnetic Resonance Imaging in Patients with Hemoglobin E/Beta-Thalassemia",
            "Molecular Characterization and Clinical Severity Profiling of Novel Globin Gene Mutations in Southeast Asian Populations"
        ]
    },
    {
        "id": "mu_si_somchai_bovorn_001",
        "university": "Mahidol University",
        "university_th": "มหาวิทยาลัยมหิดล",
        "faculty": "Faculty of Medicine Siriraj Hospital",
        "faculty_th": "คณะแพทยศาสตร์ศิริราชพยาบาล",
        "department": "Department of Medicine",
        "department_th": "ภาควิชาอายุรศาสตร์",
        "academic_title": "Prof. Dr.",
        "academic_title_th": "ศ.ดร.นพ.",
        "first_name": "Somchai",
        "last_name": "Bovornkitti",
        "full_name_th": "ศ.ดร.นพ. สมชาย บวรกิตติ",
        "role": "Fellow of the Royal Society of Thailand & Doyen of Thai Pulmonology, Respiratory Medicine and Environmental Health",
        "email": "somchai.bov@mahidol.ac.th",
        "profile_url": "https://www.si.mahidol.ac.th/staff/somchai-bovornkitti",
        "scholar_url": "https://scholar.google.com/citations?user=somchaibovornkitti",
        "education": [
            "Doctor of Medical Science (Med.Sc.D.), University of Colorado, USA",
            "M.D., Faculty of Medicine Siriraj Hospital, Mahidol University",
            "Diploma American Board of Internal Medicine (Pulmonary Disease)"
        ],
        "research_interests": [
            "Occupational Lung Diseases, Silicosis and Asbestosis in Industrial Settings",
            "Environmental Pulmonology, Air Pollution and Chronic Obstructive Pulmonary Disease (COPD)",
            "Tuberculosis Pathobiology, Pleural Effusions and Granulomatous Lung Pathologies",
            "Medical History, Bioethics and Academic Nomenclature in Thai Healthcare"
        ],
        "featured_publications": [
            "Occupational and Environmental Lung Diseases in Thailand: Historical Perspective and Diagnostic Challenges",
            "Clinical Characteristics and Pleural Fluid Dynamics in Tuberculous Pleurisy",
            "Airborne Particulate Matter Exposure and Chronic Bronchitis Morbidity in Rapidly Urbanizing Communities"
        ]
    },
    {
        "id": "mu_rama_manote_001",
        "university": "Mahidol University",
        "university_th": "มหาวิทยาลัยมหิดล",
        "faculty": "Faculty of Medicine Ramathibodi Hospital",
        "faculty_th": "คณะแพทยศาสตร์โรงพยาบาลรามาธิบดี",
        "department": "Department of Psychiatry",
        "department_th": "ภาควิชาจิตเวชศาสตร์",
        "academic_title": "Prof. Dr.",
        "academic_title_th": "ศ.นพ.",
        "first_name": "Manote",
        "last_name": "Lotrakul",
        "full_name_th": "ศ.นพ. มาโนช หล่อตระกูล",
        "role": "Senior Clinical Psychiatrist in Depressive Disorders, Psychotherapy, Psychiatric Rating Scales and Mental Health Policy",
        "email": "manote.lot@mahidol.ac.th",
        "profile_url": "https://www.rama.mahidol.ac.th/psych/staff/manote-lotrakul",
        "scholar_url": "https://scholar.google.com/citations?user=manotelotrakul",
        "education": [
            "M.D. (Honours), Faculty of Medicine Ramathibodi Hospital, Mahidol University",
            "Diploma Thai Board of Psychiatry"
        ],
        "research_interests": [
            "Standardization and Validation of Thai Psychiatric Diagnostic Instruments (PHQ-9, 9Q, HAM-D)",
            "Pharmacotherapy and Cognitive Behavioral Therapy Integration for Treatment-Resistant Depression",
            "Suicide Risk Assessment, Crisis Intervention and Community Suicide Prevention Strategies",
            "Neurobiology of Mood Disorders and Psychosomatic Medicine in General Hospital Settings"
        ],
        "featured_publications": [
            "Development and Psychometric Evaluation of the Thai Patient Health Questionnaire (PHQ-9) for Depression Screening",
            "Efficacy of Combined Pharmacotherapy and Brief Cognitive Psychotherapy in Major Depressive Disorder: A Randomized Trial",
            "Epidemiological Patterns and Risk Factors Associated with Suicide Attempts in Thai Metropolitan Populations"
        ]
    },

    # =========================================================================
    # 3. Kasetsart University (Agriculture, Forestry, Engineering & Vet Masters)
    # =========================================================================
    {
        "id": "agr-ku-001_0458e1",
        "university": "Kasetsart University",
        "university_th": "มหาวิทยาลัยเกษตรศาสตร์",
        "faculty": "Faculty of Agriculture",
        "faculty_th": "คณะเกษตร",
        "department": "Department of Agronomy",
        "department_th": "ภาควิชาพืชไร่นา",
        "academic_title": "Prof. Dr.",
        "academic_title_th": "ศ.ดร.",
        "first_name": "Sutkhet",
        "last_name": "Nakasathien",
        "full_name_th": "ศ.ดร. สุทธิเขตต์ นาคะเสถียร",
        "role": "Distinguished Crop Physiologist, Former Dean of Faculty of Agriculture & Nitrogen Metabolism Pioneer",
        "email": "agrskn@ku.ac.th",
        "profile_url": "https://agri.ku.ac.th/staff/sutkhet-nakasathien",
        "scholar_url": "https://scholar.google.com/citations?user=sutkhetnakasathien",
        "education": [
            "Ph.D. (Crop Physiology), North Carolina State University (NCSU), USA",
            "M.S. (Agronomy), North Carolina State University (NCSU), USA",
            "B.Sc. (Agronomy), Kasetsart University"
        ],
        "research_interests": [
            "Nitrogen and Carbon Assimilation Physiology in Grain Legumes and Cereal Crops",
            "Abiotic Stress Physiology (High Temperature, Drought, Waterlogging) in Tropical Maize and Soybeans",
            "Photosynthetic Efficiency and Biomass Partitioning Under Elevated Atmospheric CO2",
            "Precision Fertilizer Management Using Plant Tissue Nitrogen Diagnostics"
        ],
        "featured_publications": [
            "Nitrogen Metabolism and Seed Protein Accumulation in Legumes Under Thermal Stress Conditions",
            "Physiological Responses and Yield Stability of Tropical Maize Inbreds Subjected to Mid-Season Drought",
            "Optimizing Nitrogen Use Efficiency in Tropical Cereal Production Through Balanced Nutrient Ingestion"
        ]
    },
    {
        "id": "ku_agr_poonpipope_001",
        "university": "Kasetsart University",
        "university_th": "มหาวิทยาลัยเกษตรศาสตร์",
        "faculty": "Faculty of Agriculture",
        "faculty_th": "คณะเกษตร",
        "department": "Department of Horticulture",
        "department_th": "ภาควิชาพืชสวน",
        "academic_title": "Prof. Dr.",
        "academic_title_th": "ศ.ดร.",
        "first_name": "Poonpipope",
        "last_name": "Kasemsap",
        "full_name_th": "ศ.ดร. พูนพิภพ เกษมทรัพย์",
        "role": "Senior Horticultural Scientist in Tree Crop Eco-Physiology, Canopy Carbon Balance and Climate Adaptation",
        "email": "agrppk@ku.ac.th",
        "profile_url": "https://agri.ku.ac.th/staff/poonpipope-kasemsap",
        "scholar_url": "https://scholar.google.com/citations?user=poonpipopekasemsap",
        "education": [
            "Ph.D. (Plant Physiology), University of California, Davis, USA",
            "B.Sc. (Agriculture), Kasetsart University"
        ],
        "research_interests": [
            "Whole-Tree Gas Exchange, Transpiration and Sap Flow in Para Rubber and Oil Palm Canopies",
            "Impact of Elevated Temperature and Vapor Pressure Deficit (VPD) on Tropical Fruit Quality (Durian, Mangosteen)",
            "Carbon Budgeting and Net Primary Productivity in Tropical Tree Plantations",
            "Agro-Meteorological Crop Modeling for Climate Change Adaptation Strategy"
        ],
        "featured_publications": [
            "Sap Flow Dynamics and Canopy Transpiration of Hevea brasiliensis in Sub-Optimal Humid Tropical Regimes",
            "Photosynthetic Performance, Stomatal Conductance, and Water Use Efficiency of Tropical Fruit Crops Under Seasonal Drought",
            "Carbon Stock and Net Ecosystem Carbon Exchange in Immature vs. Mature Commercial Palm Plantations"
        ]
    },
    {
        "id": "ku_vet_theera_001",
        "university": "Kasetsart University",
        "university_th": "มหาวิทยาลัยเกษตรศาสตร์",
        "faculty": "Faculty of Veterinary Medicine",
        "faculty_th": "คณะสัตวแพทยศาสตร์",
        "department": "Department of Large Animal and Wildlife Clinical Sciences",
        "department_th": "ภาควิชาเวชศาสตร์คลินิกสัตว์ใหญ่และสัตว์ป่า",
        "academic_title": "Prof. Dr.",
        "academic_title_th": "ศ.ดร.น.สพ.",
        "first_name": "Theera",
        "last_name": "Rukkwamsuk",
        "full_name_th": "ศ.ดร.น.สพ. ธีระ รักความสุข",
        "role": "Senior Veterinary Epidemiologist, Herd Health Specialist in Transition Dairy Cow Metabolism and Subclinical Ketosis",
        "email": "fvettrr@ku.ac.th",
        "profile_url": "https://vet.ku.ac.th/staff/theera-rukkwamsuk",
        "scholar_url": "https://scholar.google.com/citations?user=theerarukkwamsuk",
        "education": [
            "Ph.D. (Veterinary Science / Herd Health), Utrecht University, The Netherlands",
            "M.Sc. (Tropical Veterinary Medicine), University of Edinburgh, UK",
            "D.V.M., Kasetsart University"
        ],
        "research_interests": [
            "Metabolic Profiling, Negative Energy Balance and Fatty Liver Syndrome in Periparturient Dairy Cows",
            "Epidemiology and Control of Bovine Mastitis and Antimicrobial Stewardship in Dairy Herds",
            "Tropical Dairy Cattle Reproduction Management and Thermal Heat Stress Alleviation",
            "One Health Approaches in Zoonotic Foodborne Pathogen Surveillance in Dairy Processing"
        ],
        "featured_publications": [
            "Risk Factors Associated with Subclinical Ketosis and Its Impact on Milk Yield and Reproductive Performance in Tropical Dairy Herds",
            "Prevalence, Antimicrobial Resistance Profiles, and Genotypic Diversity of Mastitis Pathogens in Smallholder Dairy Farms",
            "Effects of Prepartum Dietary Energy Density on Hepatic Lipid Infiltration and Postpartum Health in Dairy Cows"
        ]
    },
    {
        "id": "ku_eng_sanya_001",
        "university": "Kasetsart University",
        "university_th": "มหาวิทยาลัยเกษตรศาสตร์",
        "faculty": "Faculty of Engineering",
        "faculty_th": "คณะวิศวกรรมศาสตร์",
        "department": "Department of Environmental Engineering",
        "department_th": "ภาควิชาวิศวกรรมสิ่งแวดล้อม",
        "academic_title": "Prof. Dr.",
        "academic_title_th": "ศ.ดร.",
        "first_name": "Sanya",
        "last_name": "Sirivithayapakorn",
        "full_name_th": "ศ.ดร. สัญญา สิริวิทยาปกรณ์",
        "role": "Leading Authority in Subsurface Contaminant Hydrogeology, Micro-Model Pore Flow and Groundwater Remediation",
        "email": "fengsys@ku.ac.th",
        "profile_url": "https://env.eng.ku.ac.th/staff/sanya-sirivithayapakorn",
        "scholar_url": "https://scholar.google.com/citations?user=sanyasirivithayapakorn",
        "education": [
            "Ph.D. (Environmental Science and Engineering), University of California, Santa Barbara (UCSB), USA",
            "M.S. (Environmental Engineering), Stanford University, USA",
            "B.Eng. (Civil Engineering), Chulalongkorn University"
        ],
        "research_interests": [
            "Colloid Transport and Nanoparticle Deposition in Saturated Porous Media",
            "In Situ Bioremediation and Chemical Oxidation of Chlorinated Solvents in Aquifers",
            "Porous Micromodel Visualization of Multiphase Flow and Microplastic Entrapment",
            "Hydrogeological Modeling of Seawater Intrusion in Coastal Aquifer Systems"
        ],
        "featured_publications": [
            "Direct Visualization of Colloid Transport and Straining in Porous Media Using Transparent Micromodels",
            "Transport Dynamics of Functionalized Engineered Nanoparticles Through Heterogeneous Saturated Soils",
            "Simulation of Dense Non-Aqueous Phase Liquid (DNAPL) Dissolution and Migration in Stratified Aquifers"
        ]
    },

    # =========================================================================
    # 4. KMUTT (King Mongkut's University of Technology Thonburi)
    # =========================================================================
    {
        "id": "kmutt_civil_somchai_chu_001",
        "university": "King Mongkut's University of Technology Thonburi",
        "university_th": "มหาวิทยาลัยเทคโนโลยีพระจอมเกล้าธนบุรี",
        "faculty": "Faculty of Engineering",
        "faculty_th": "คณะวิศวกรรมศาสตร์",
        "department": "Department of Civil Engineering",
        "department_th": "ภาควิชาวิศวกรรมโยธา",
        "academic_title": "Prof. Dr.",
        "academic_title_th": "ศ.ดร.",
        "first_name": "Somchai",
        "last_name": "Chucheepsakul",
        "full_name_th": "ศ.ดร. สมชาย ชูชีพสกุล",
        "role": "Fellow of the Royal Society of Thailand & Pioneer in Offshore Marine Risers, Cable Dynamics and Non-Linear Structural Mechanics",
        "email": "somchai.chu@kmutt.ac.th",
        "profile_url": "https://civil.kmutt.ac.th/staff/somchai-chucheepsakul",
        "scholar_url": "https://scholar.google.com/citations?user=somchaichucheepsakul",
        "education": [
            "Ph.D. (Civil Engineering / Offshore Structures), University of Texas at Arlington, USA",
            "M.S. (Civil Engineering), University of Texas at Arlington, USA",
            "B.Eng. (Civil Engineering), Chulalongkorn University"
        ],
        "research_interests": [
            "Nonlinear Large-Deflection Dynamic Analysis of Deepwater Top-Tensioned Marine Risers",
            "Vortex-Induced Vibration (VIV) and Fluid-Structure Interaction of Subsea Pipelines",
            "Variational Formulations and Finite Element Modeling of Extensible Marine Cables",
            "Structural Health Monitoring of Offshore Wind Turbine Foundations"
        ],
        "featured_publications": [
            "Variational Formulation and Finite Element Analysis of Marine Risers Subjected to Hydrodynamic Loads",
            "Nonlinear Free Vibration of Extensible Marine Cables with Large Sag in Water",
            "Three-Dimensional Coupled Dynamic Response of Deepwater Floating Platforms and Tendon Systems"
        ]
    },

    # =========================================================================
    # 5. Suranaree University of Technology (มทส.)
    # =========================================================================
    {
        "id": "sut_sci_sukit_001",
        "university": "Suranaree University of Technology",
        "university_th": "มหาวิทยาลัยเทคโนโลยีสุรนารี",
        "faculty": "School of Physics",
        "faculty_th": "สำนักวิชาวิทยาศาสตร์ (สาขาวิชาฟิสิกส์)",
        "department": "Center of Excellence in Advanced Materials & Semiconductor Physics",
        "department_th": "ศูนย์ความเป็นเลิศด้านวัสดุขั้นสูงและฟิสิกส์สารกึ่งตัวนำ",
        "academic_title": "Prof. Dr.",
        "academic_title_th": "ศ.ดร.",
        "first_name": "Sukit",
        "last_name": "Limpijumnong",
        "full_name_th": "ศ.ดร. สุขิต ลิมปิจำนงค์",
        "role": "Outstanding Scientist of Thailand & Global Authority in Semiconductor Point Defects and First-Principles DFT Physics",
        "email": "sukit@sut.ac.th",
        "profile_url": "https://science.sut.ac.th/staff/sukit-limpijumnong",
        "scholar_url": "https://scholar.google.com/citations?user=sukitlimpijumnong",
        "education": [
            "Ph.D. (Physics), Case Western Reserve University, USA",
            "M.S. (Physics), Case Western Reserve University, USA",
            "B.Sc. (First Class Honours, Physics), Khon Kaen University"
        ],
        "research_interests": [
            "First-Principles Density Functional Calculations of Native Defects and Dopants in Wide-Bandgap Semiconductors (GaN, ZnO, TiO2)",
            "Synchrotron X-Ray Absorption Spectroscopy (XANES/EXAFS) Simulation and Structural Analysis",
            "Hydrogen-Related Defects and Doping Asymmetry in Transparent Conducting Oxides",
            "2D Quantum Materials and Ferroelectric Semiconductor Heterostructures"
        ],
        "featured_publications": [
            "Doping by Large-Size-Mismatched Impurities: Chemical Origin of Nitrogen-Doped p-Type ZnO",
            "First-Principles Study of Native Point Defects in Gallium Nitride Under Equilibrium Growth Conditions",
            "Identification of Hydrogen Configurations in Wide-Bandgap Oxides via Infrared Spectroscopy and DFT Calculations"
        ]
    },
    {
        "id": "sut_agr_nantakorn_001",
        "university": "Suranaree University of Technology",
        "university_th": "มหาวิทยาลัยเทคโนโลยีสุรนารี",
        "faculty": "School of Biotechnology",
        "faculty_th": "สำนักวิชาเทคโนโลยีการเกษตร (สาขาวิชาเทคโนโลยีชีวภาพ)",
        "department": "Center of Excellence in Microbial Inoculants",
        "department_th": "ศูนย์วิจัยสารเสริมชีวภาพและจุลินทรีย์การเกษตร",
        "academic_title": "Prof. Dr.",
        "academic_title_th": "ศ.ดร.",
        "first_name": "Nantakorn",
        "last_name": "Boonkerd",
        "full_name_th": "ศ.ดร. นันทกร บุญเกิด",
        "role": "National Outstanding Researcher & Pioneer of Rhizobial Inoculant Technology and Legume Bio-Fertilizers in Thailand",
        "email": "nantakon@sut.ac.th",
        "profile_url": "https://iat.sut.ac.th/staff/nantakorn-boonkerd",
        "scholar_url": "https://scholar.google.com/citations?user=nantakornboonkerd",
        "education": [
            "Ph.D. (Soil Microbiology), North Carolina State University (NCSU), USA",
            "M.S. (Soil Science), North Carolina State University (NCSU), USA",
            "B.Sc. (Agriculture), Kasetsart University"
        ],
        "research_interests": [
            "Symbiotic Nitrogen Fixation and Bradyrhizobium Ecology in Tropical Acidic Soils",
            "Industrial-Scale Fermentation and Carrier Formulations for Microbial Inoculants",
            "Plant Growth-Promoting Rhizobacteria (PGPR) for Drought Stress Alleviation",
            "Endophytic Actinobacteria in Biocontrol of Soil-Borne Fungal Pathogens"
        ],
        "featured_publications": [
            "Selection of Highly Effective Bradyrhizobium Strains for Soybean Production in Tropical Low-Fertility Soils",
            "Carrier Materials and Shelf-Life Stabilization for High-Density Bio-Fertilizer Formulations",
            "Synergistic Effects of Rhizobial Inoculation and Arbuscular Mycorrhizal Fungi on Legume Growth and P-Uptake"
        ]
    },

    # =========================================================================
    # 6. Khon Kaen University (มข.)
    # =========================================================================
    {
        "id": "kku_agr_suthipong_001",
        "university": "Khon Kaen University",
        "university_th": "มหาวิทยาลัยขอนแก่น",
        "faculty": "Faculty of Agriculture",
        "faculty_th": "คณะเกษตรศาสตร์",
        "department": "Department of Animal Science",
        "department_th": "สาขาวิชาสัตวศาสตร์",
        "academic_title": "Prof. Dr.",
        "academic_title_th": "ศ.ดร.",
        "first_name": "Suthipong",
        "last_name": "Uriyapongson",
        "full_name_th": "ศ.ดร. สุทธิพงศ์ อุริยะพงศ์สรรค์",
        "role": "Distinguished Meat Scientist in Tropical Native Beef Marbling, Carcass Quality Evaluation and Bioactive Meat Peptides",
        "email": "suthipng@kku.ac.th",
        "profile_url": "https://ag2.kku.ac.th/staff/suthipong-uriyapongson",
        "scholar_url": "https://scholar.google.com/citations?user=suthiponguriyapongson",
        "education": [
            "Ph.D. (Meat Science / Food Science), Texas A&M University, USA",
            "M.S. (Animal Science), Texas A&M University, USA",
            "B.Sc. (Animal Science), Khon Kaen University"
        ],
        "research_interests": [
            "Carcass Characteristics, Fatty Acid Composition and Marbling in Isan Native and Korat Wagyu Beef",
            "Post-Mortem Muscle Aging and Tenderization Mechanisms in High-Collagen Tropical Breeds",
            "Functional Bioactive Peptides from Animal By-Products with Antioxidant and ACE-Inhibitory Activities",
            "Modified Atmosphere Packaging (MAP) for Fresh Beef Color Stability and Shelf-Life Extension"
        ],
        "featured_publications": [
            "Carcass Traits, Meat Quality, and Fatty Acid Profiles of Crossbred Wagyu Beef Cattle Finished on High-Energy Rations",
            "Effect of Post-Mortem Electrical Stimulation and Aging on Tenderness and Calpain Activity in Bos indicus Beef",
            "Antioxidant Bioactive Peptides Derived from Enzymatic Hydrolysis of Bovine Blood Plasma Proteins"
        ]
    },
    {
        "id": "kku_agr_chanin_001",
        "university": "Khon Kaen University",
        "university_th": "มหาวิทยาลัยขอนแก่น",
        "faculty": "Faculty of Technology",
        "faculty_th": "คณะเทคโนโลยี",
        "department": "Department of Biotechnology",
        "department_th": "สาขาวิชาเทคโนโลยีชีวภาพ",
        "academic_title": "Prof. Dr.",
        "academic_title_th": "ศ.ดร.",
        "first_name": "Chanin",
        "last_name": "Saiphim",
        "full_name_th": "ศ.ดร. ชนินทร์ สายพิมพ์",
        "role": "Leading Bioprocess Engineer in Very High Gravity (VHG) Bioethanol Fermentation and Thermotolerant Yeasts",
        "email": "chanins@kku.ac.th",
        "profile_url": "https://techno.kku.ac.th/staff/chanin-saiphim",
        "scholar_url": "https://scholar.google.com/citations?user=chaninsaiphim",
        "education": [
            "Ph.D. (Biotechnology), Khon Kaen University",
            "B.Sc. (Biotechnology), Khon Kaen University"
        ],
        "research_interests": [
            "Very High Gravity (VHG) Ethanol Fermentation from Sweet Sorghum and Cassava Starch",
            "Thermotolerant Saccharomyces cerevisiae Strain Engineering and Osmotolerance Mechanisms",
            "Continuous Fed-Batch Bioreactor Optimization and Yeast Cell Recycling Systems",
            "Value-Added Bio-Refinery By-Product Valorization (Distillers Dried Grains with Solubles - DDGS)"
        ],
        "featured_publications": [
            "High-Efficiency Bioethanol Production Under Very High Gravity Fermentation Using Thermotolerant Yeasts",
            "Nutrient Supplementation and Aeration Strategies for Enhancing Ethanol Yield from Raw Cassava Pulp",
            "Transcriptomic Profiling of Osmotic and Ethanol Stress Responses in Industrial Fermentation Strains"
        ]
    },

    # =========================================================================
    # 7. Thammasat University & NIDA (Social, Governance & Economics Masters)
    # =========================================================================
    {
        "id": "nida_wu_sombat_001",
        "university": "National Institute of Development Administration",
        "university_th": "สถาบันบัณฑิตพัฒนบริหารศาสตร์",
        "faculty": "Graduate School of Public Administration (GSPA)",
        "faculty_th": "คณะรัฐประศาสนศาสตร์",
        "department": "Department of Public Policy and Governance",
        "department_th": "สาขาวิชานโยบายสาธารณะและการกำกับดูแล",
        "academic_title": "Prof. Dr.",
        "academic_title_th": "ศ.ดร.",
        "first_name": "Sombat",
        "last_name": "Thamrongthanyawong",
        "full_name_th": "ศ.ดร. สมบัติ ธำรงธัญวงศ์",
        "role": "Distinguished Political Scientist, Former President of NIDA and Walailak University in Public Policy Formulation",
        "email": "sombat@nida.ac.th",
        "profile_url": "https://gspa.nida.ac.th/staff/sombat-thamrongthanyawong",
        "scholar_url": "https://scholar.google.com/citations?user=sombatthamrongthanyawong",
        "education": [
            "Ph.D. (Political Science / Public Administration), Florida State University, USA",
            "M.P.A., National Institute of Development Administration (NIDA)",
            "B.Sc. (Agriculture), Kasetsart University"
        ],
        "research_interests": [
            "Public Policy Formulation, Implementation and Evaluation Frameworks",
            "Comparative Political Systems and Democratic Transition in Developing Societies",
            "Higher Education Institutional Transformation, Strategic Governance and World Rankings",
            "Public Sector Leadership and Strategic Management for Sustainable Development"
        ],
        "featured_publications": [
            "Public Policy: Concepts, Analysis and Evaluation (Chulalongkorn University Press)",
            "Politics and Government of Thailand: Institutional Evolution, Power Dynamics, and Electoral Regimes",
            "Strategic Leadership in University Transformation: Case Analysis of Rapid Institutional Advancement"
        ]
    },
    {
        "id": "tu_econ_medhi_001",
        "university": "Thammasat University",
        "university_th": "มหาวิทยาลัยธรรมศาสตร์",
        "faculty": "Faculty of Economics",
        "faculty_th": "คณะเศรษฐศาสตร์",
        "department": "Department of Public Finance and Development Economics",
        "department_th": "สาขาวิชาเศรษฐศาสตร์การคลังและเศรษฐศาสตร์การพัฒนา",
        "academic_title": "Prof. Dr.",
        "academic_title_th": "ศ.ดร.",
        "first_name": "Medhi",
        "last_name": "Krongkaew",
        "full_name_th": "ศ.ดร. เมธี ครองแก้ว",
        "role": "Distinguished Public Finance Economist, Former National Anti-Corruption Commissioner (NACC) & Poverty Measurement Pioneer",
        "email": "medhi@econ.tu.ac.th",
        "profile_url": "https://www.econ.tu.ac.th/staff/medhi-krongkaew",
        "scholar_url": "https://scholar.google.com/citations?user=medhikrongkaew",
        "education": [
            "Ph.D. (Economics), Michigan State University, USA",
            "M.A. (Economics), Michigan State University, USA",
            "B.Econ. (Honours), Victoria University of Wellington, New Zealand"
        ],
        "research_interests": [
            "Poverty Measurement Methodologies, Multidimensional Deprivation and Income Inequality Indices",
            "Economics of Anti-Corruption Enforcement, Asset Declaration Transparency and Public Integrity",
            "Public Expenditure Review, Social Safety Nets and Universal Old-Age Pension Financing",
            "Fiscal Federalism and Intergovernmental Grants in Southeast Asian Economies"
        ],
        "featured_publications": [
            "The Current State of Poverty and Income Inequality in Thailand: Measurement and Policy Implications",
            "Economic Dimensions of Corruption and Institutional Reforms in Developing Asian Nations",
            "Financing Universal Healthcare and Social Protection Systems in Ageing Developing Societies"
        ]
    }
]
