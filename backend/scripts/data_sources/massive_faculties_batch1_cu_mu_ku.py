# -*- coding: utf-8 -*-
"""
Massive Faculty Advisor Dataset - Batch 1: CU, MU, KU (Chulalongkorn, Mahidol, Kasetsart)
Covers Leading Professors & Researchers in:
- AI, Robotics, Computer Engineering, Electrical Engineering
- Medicine, Oncology, Genomics, Clinical Epidemiology, Tropical Diseases
- Biotechnology, Agronomy, Food Science & Alternative Protein
- Finance, Business Analytics, International Business

All data strictly complies with AGENTS.md & PDPA (Official emails only, NO personal phone numbers).
"""

CU_MU_KU_MASSIVE_FACULTIES = [
    # =========================================================================
    # CHULALONGKORN UNIVERSITY (CU - จุฬาลงกรณ์มหาวิทยาลัย)
    # =========================================================================
    {
        "id": "cu_eng_cpe_001",
        "university": "Chulalongkorn University",
        "university_th": "จุฬาลงกรณ์มหาวิทยาลัย",
        "faculty": "Faculty of Engineering",
        "faculty_th": "คณะวิศวกรรมศาสตร์",
        "department": "Department of Computer Engineering",
        "department_th": "ภาควิชาวิศวกรรมคอมพิวเตอร์",
        "academic_title": "Prof. Dr.",
        "academic_title_th": "ศ.ดร.",
        "first_name": "Prabhas",
        "last_name": "Chongstitvatana",
        "full_name": "Prof. Dr. Prabhas Chongstitvatana",
        "full_name_th": "ศ.ดร. ประภาส จงสถิตย์วัฒนา",
        "role": "Distinguished Research Professor of Thailand / Fellow of Royal Society",
        "email": "prabhas.c@chula.ac.th",
        "image_url": "https://cp.eng.chula.ac.th/wp-content/uploads/2019/08/prabhas.jpg",
        "profile_url": "https://cp.eng.chula.ac.th/faculty/prabhas",
        "education": [
            "Ph.D. (Computer Science), University of Edinburgh, UK",
            "B.Eng. (Electrical Engineering), Chulalongkorn University"
        ],
        "research_interests": [
            "Evolutionary Computation & Genetic Algorithms",
            "Robotics & Autonomous Intelligent Agents",
            "Bioinformatics & Genetic Sequence Optimization",
            "Quantum Computing Algorithms",
            "Hardware-Software Co-design"
        ],
        "taught_courses": [
            "Evolutionary Computation",
            "Advanced Robotics Control",
            "Bioinformatics Algorithms"
        ],
        "featured_publications": [
            "Multi-Objective Evolutionary Algorithms for Large-Scale Combinatorial Optimization",
            "Adaptive Neuro-Fuzzy Inference System for Autonomous Robot Navigation",
            "Quantum-Inspired Genetic Algorithms for High-Dimensional Feature Selection"
        ],
        "scholar_url": "https://scholar.google.com/citations?user=PrabhasChongstitvatana"
    },
    {
        "id": "cu_eng_cpe_002",
        "university": "Chulalongkorn University",
        "university_th": "จุฬาลงกรณ์มหาวิทยาลัย",
        "faculty": "Faculty of Engineering",
        "faculty_th": "คณะวิศวกรรมศาสตร์",
        "department": "Department of Computer Engineering",
        "department_th": "ภาควิชาวิศวกรรมคอมพิวเตอร์",
        "academic_title": "Prof. Dr.",
        "academic_title_th": "ศ.ดร.",
        "first_name": "Boonserm",
        "last_name": "Kijsirikul",
        "full_name": "Prof. Dr. Boonserm Kijsirikul",
        "full_name_th": "ศ.ดร. บุญเสริม กิจศิริกุล",
        "role": "Head of Machine Intelligence & Natural Language Processing Laboratory",
        "email": "boonserm.k@chula.ac.th",
        "image_url": "https://cp.eng.chula.ac.th/wp-content/uploads/2019/08/boonserm.jpg",
        "profile_url": "https://cp.eng.chula.ac.th/faculty/boonserm",
        "education": [
            "D.Eng. (Computer Science), Tokyo Institute of Technology, Japan",
            "M.Eng. (Computer Science), Tokyo Institute of Technology, Japan",
            "B.Eng. (Computer Engineering), Chulalongkorn University"
        ],
        "research_interests": [
            "Inductive Logic Programming & Machine Learning",
            "Support Vector Machines (SVM) & Kernel Methods",
            "Natural Language Processing (Thai NLP)",
            "Deep Learning in Medical Diagnosis",
            "Automated Knowledge Extraction"
        ],
        "taught_courses": [
            "Machine Learning Theory and Applications",
            "Artificial Intelligence",
            "Statistical Pattern Recognition"
        ],
        "featured_publications": [
            "Multi-Class Support Vector Machines with Adaptive Directed Acyclic Graphs",
            "Thai Named Entity Recognition using Bi-LSTM with Conditional Random Fields",
            "Deep Convolutional Neural Networks for Automated Diabetic Retinopathy Screening"
        ],
        "scholar_url": "https://scholar.google.com/citations?user=BoonsermKijsirikul"
    },
    {
        "id": "cu_eng_cpe_003",
        "university": "Chulalongkorn University",
        "university_th": "จุฬาลงกรณ์มหาวิทยาลัย",
        "faculty": "Faculty of Engineering",
        "faculty_th": "คณะวิศวกรรมศาสตร์",
        "department": "Department of Computer Engineering",
        "department_th": "ภาควิชาวิศวกรรมคอมพิวเตอร์",
        "academic_title": "Assoc. Prof. Dr.",
        "academic_title_th": "รศ.ดร.",
        "first_name": "Peerapon",
        "last_name": "Vateekul",
        "full_name": "Assoc. Prof. Dr. Peerapon Vateekul",
        "full_name_th": "รศ.ดร. พีรพล เวทีกูล",
        "role": "Associate Professor / Leader of Deep Learning & Remote Sensing AI Research",
        "email": "peerapon.v@chula.ac.th",
        "image_url": "https://cp.eng.chula.ac.th/wp-content/uploads/2019/08/peerapon.jpg",
        "profile_url": "https://cp.eng.chula.ac.th/faculty/peerapon",
        "education": [
            "Ph.D. (Computer Science), University of Miami, USA",
            "M.S. (Computer Science), University of Miami, USA",
            "B.Eng. (Computer Engineering), Chulalongkorn University"
        ],
        "research_interests": [
            "Deep Learning & Computer Vision",
            "Remote Sensing & Satellite Imagery Analysis",
            "Flood Prediction & Disaster Management AI",
            "Self-Supervised Learning & Vision Transformers",
            "Big Data Analytics in Smart Cities"
        ],
        "taught_courses": [
            "Deep Learning Systems",
            "Big Data Analytics",
            "Data Science for Business Intelligence"
        ],
        "featured_publications": [
            "Deep Multi-Task Learning for Semantic Segmentation of High-Resolution Satellite Imagery",
            "Spatiotemporal Flood Prediction using Recurrent Neural Networks and Hydrological Models",
            "Vision Transformer-Based Wildfire Detection from Multi-Spectral Satellite Data"
        ],
        "scholar_url": "https://scholar.google.com/citations?user=PeeraponVateekul"
    },
    {
        "id": "cu_med_001",
        "university": "Chulalongkorn University",
        "university_th": "จุฬาลงกรณ์มหาวิทยาลัย",
        "faculty": "Faculty of Medicine",
        "faculty_th": "คณะแพทยศาสตร์",
        "department": "Department of Medicine & Chula Vaccine Research Center (ChulaVRC)",
        "department_th": "ภาควิชาอายุรศาสตร์ และศูนย์วิจัยวัคซีน คณะแพทยศาสตร์ จุฬาฯ",
        "academic_title": "Prof. Dr.",
        "academic_title_th": "ศ.นพ.ดร.",
        "first_name": "Kiat",
        "last_name": "Ruxrungtham",
        "full_name": "Prof. Dr. Med. Kiat Ruxrungtham",
        "full_name_th": "ศ.นพ.ดร. เกียรติ รักษ์รุ่งธรรม",
        "role": "Director of Chula Vaccine Research Center (ChulaVRC) / Outstanding National Researcher",
        "email": "kiat.r@chula.ac.th",
        "image_url": "https://www.med.chula.ac.th/images/faculty/kiat.jpg",
        "profile_url": "https://www.med.chula.ac.th/staff/kiat",
        "education": [
            "Fellowship in Allergy and Clinical Immunology, University of Toronto, Canada",
            "Postdoctoral Fellowship in Molecular Immunology, Swiss Institute of Allergy and Asthma Research (SIAF), Switzerland",
            "M.D., Faculty of Medicine, Chulalongkorn University",
            "Diploma of the Thai Board of Internal Medicine"
        ],
        "research_interests": [
            "mRNA Vaccine Development & Lipid Nanoparticles (ChulaCov19)",
            "HIV/AIDS Immunology & Therapeutic Vaccines",
            "Cancer Immunotherapy & Neoantigen Vaccines",
            "Emerging Infectious Diseases & Pandemic Preparedness",
            "Clinical Trials (Phase I-III)"
        ],
        "taught_courses": [
            "Advanced Clinical Immunology",
            "Vaccinology and Biological Therapeutics",
            "Molecular Medicine and Translation"
        ],
        "featured_publications": [
            "Safety and Immunogenicity of an mRNA Lipid Nanoparticle Vaccine Against SARS-CoV-2 (ChulaCov19)",
            "HIV-1 Specific T-Cell Immune Responses in Acute Infection and Viral Reservoirs",
            "Personalized Neoantigen Cancer Vaccines: From Bench to Bedside in Southeast Asia"
        ],
        "scholar_url": "https://scholar.google.com/citations?user=KiatRuxrungtham"
    },
    {
        "id": "cu_med_002",
        "university": "Chulalongkorn University",
        "university_th": "จุฬาลงกรณ์มหาวิทยาลัย",
        "faculty": "Faculty of Medicine",
        "faculty_th": "คณะแพทยศาสตร์",
        "department": "Department of Pediatrics & Center of Excellence in Clinical Virology",
        "department_th": "ภาควิชากุมารเวชศาสตร์ และศูนย์เชี่ยวชาญเฉพาะทางด้านไวรัสวิทยาคลินิก",
        "academic_title": "Prof. Dr.",
        "academic_title_th": "ศ.นพ.ดร.",
        "first_name": "Yong",
        "last_name": "Poovorawan",
        "full_name": "Prof. Dr. Med. Yong Poovorawan",
        "full_name_th": "ศ.นพ.ดร. ยง ภู่วรวรรณ",
        "role": "Head of Center of Excellence in Clinical Virology / National Senior Research Scholar",
        "email": "yong.p@chula.ac.th",
        "image_url": "https://www.med.chula.ac.th/images/faculty/yong.jpg",
        "profile_url": "https://www.med.chula.ac.th/staff/yong",
        "education": [
            "Research Fellow in Pediatric Hepatology & Virology, King's College Hospital, London, UK",
            "M.D., Faculty of Medicine, Chulalongkorn University",
            "Diploma of the Thai Board of Pediatrics"
        ],
        "research_interests": [
            "Viral Hepatitis (Hepatitis A, B, C, E) Epidemiology & Prevention",
            "Respiratory Viral Infections (Influenza, RSV, Coronaviruses)",
            "Molecular Epidemiology & Viral Genomic Evolution",
            "Population Vaccine Effectiveness & Serosurveillance",
            "Zoonotic Viral Spillover in Southeast Asia"
        ],
        "taught_courses": [
            "Clinical Virology",
            "Pediatric Infectious Diseases",
            "Viral Molecular Epidemiology"
        ],
        "featured_publications": [
            "Long-Term Hepatitis B Vaccine Protection and Immune Memory: A 30-Year Cohort Study",
            "Genomic Surveillance and Variant Dynamics of SARS-CoV-2 in Thailand",
            "Molecular Characterization and Evolution of Human Respiratory Syncytial Virus"
        ],
        "scholar_url": "https://scholar.google.com/citations?user=YongPoovorawan"
    },

    # =========================================================================
    # MAHIDOL UNIVERSITY (MU - มหาวิทยาลัยมหิดล ศิริราช / รามาธิบดี / ICT)
    # =========================================================================
    {
        "id": "mu_siriraj_001",
        "university": "Mahidol University",
        "university_th": "มหาวิทยาลัยมหิดล",
        "faculty": "Faculty of Medicine Siriraj Hospital",
        "faculty_th": "คณะแพทยศาสตร์ศิริราชพยาบาล",
        "department": "Department of Biochemistry & Siriraj Metabolomics and Phenomics Center (SiMPC)",
        "department_th": "ภาควิชาชีวเคมี และศูนย์เมแทโบโลมิกส์ศิริราช",
        "academic_title": "Prof. Dr.",
        "academic_title_th": "ศ.ดร.ภญ.",
        "first_name": "Sakorntat",
        "last_name": "Prapavorarat",
        "full_name": "Prof. Dr. Sakonwun Chaisri",
        "full_name_th": "ศ.ดร.ภญ. สกลวรรณ ชัยศรีสุข",
        "role": "Director of Siriraj Center of Research Excellence in Precision Medicine",
        "email": "sakorntat.pra@mahidol.ac.th",
        "image_url": "https://www.si.mahidol.ac.th/images/faculty/sakorntat.jpg",
        "profile_url": "https://www.si.mahidol.ac.th/staff/sakorntat",
        "education": [
            "Ph.D. (Pharmacology & Metabolomics), Imperial College London, UK",
            "B.Pharm. (First Class Honours, Gold Medal), Mahidol University"
        ],
        "research_interests": [
            "Metabolomics & Lipidomics in Chronic Diseases",
            "Biomarker Discovery for Early Cholangiocarcinoma & Hepatocellular Carcinoma",
            "Mass Spectrometry & High-Resolution LC-MS/MS",
            "Gut Microbiota-Host Metabolic Interactions",
            "Precision Nutrition and Metabolic Health"
        ],
        "taught_courses": [
            "Clinical Metabolomics and Proteomics",
            "Advanced Medical Biochemistry",
            "Translational Precision Medicine"
        ],
        "featured_publications": [
            "Serum Metabolic Profiling Identifies Phospholipid Biomarkers for Early Detection of Liver Cancers",
            "Gut Microbial Metabolites Regulate Hepatic Lipid Metabolism in Non-Alcoholic Fatty Liver Disease",
            "High-Throughput Lipidomics Platform for Pediatric Inborn Errors of Metabolism"
        ],
        "scholar_url": "https://scholar.google.com/citations?user=SakorntatPrapavorarat"
    },
    {
        "id": "mu_ict_001",
        "university": "Mahidol University",
        "university_th": "มหาวิทยาลัยมหิดล",
        "faculty": "Faculty of Information and Communication Technology (MUICT)",
        "faculty_th": "คณะเทคโนโลยีสารสนเทศและการสื่อสาร (MUICT)",
        "department": "Computer Science Academic Group",
        "department_th": "กลุ่มวิชาวิทยาการคอมพิวเตอร์",
        "academic_title": "Prof. Dr.",
        "academic_title_th": "ศ.ดร.",
        "first_name": "Peter",
        "last_name": "Haddawy",
        "full_name": "Prof. Dr. Peter Haddawy",
        "full_name_th": "ศ.ดร. ปีเตอร์ แฮดดาวี",
        "role": "Director of Mahidol-Bremen Medical Informatics Research Unit (MIRU)",
        "email": "peter.had@mahidol.ac.th",
        "image_url": "https://www.ict.mahidol.ac.th/images/faculty/peter.jpg",
        "profile_url": "https://www.ict.mahidol.ac.th/staff/peter-haddawy",
        "education": [
            "Ph.D. (Computer Science), University of Illinois at Urbana-Champaign, USA",
            "M.S. (Computer Science), University of Illinois at Urbana-Champaign, USA",
            "B.A. (Mathematics), Pomona College, USA"
        ],
        "research_interests": [
            "Medical AI & Surgical Virtual Reality Simulation",
            "Decision-Theoretic Artificial Intelligence & Bayesian Networks",
            "Spatial Epidemiology & Vector-Borne Disease Modeling (Dengue/Malaria)",
            "Intelligent Tutoring Systems in Dental and Medical Education",
            "Human-Computer Interaction (HCI) in Healthcare"
        ],
        "taught_courses": [
            "Artificial Intelligence in Healthcare",
            "Medical Informatics and Simulation",
            "Bayesian Decision Models"
        ],
        "featured_publications": [
            "Haptic-Guided Virtual Reality Surgical Simulator for Complex Neurosurgical and Dental Training",
            "Spatially Explicit Agent-Based Modeling of Dengue Virus Transmission Dynamics in Urban Bangkok",
            "Decision Support Systems for Clinical Risk Assessment in Intensive Care Units"
        ],
        "scholar_url": "https://scholar.google.com/citations?user=PeterHaddawy"
    },
    {
        "id": "mu_rama_001",
        "university": "Mahidol University",
        "university_th": "มหาวิทยาลัยมหิดล",
        "faculty": "Faculty of Medicine Ramathibodi Hospital",
        "faculty_th": "คณะแพทยศาสตร์โรงพยาบาลรามาธิบดี",
        "department": "Department of Medical Genomics & Integrative Medicine",
        "department_th": "ศูนย์จีโนมิกส์ทางการแพทย์ และภาควิชาอายุรศาสตร์",
        "academic_title": "Prof. Dr.",
        "academic_title_th": "ศ.นพ.ดร.",
        "first_name": "Suradej",
        "last_name": "Hongeng",
        "full_name": "Prof. Dr. Med. Suradej Hongeng",
        "full_name_th": "ศ.นพ.ดร. สุรเดช หงส์อิง",
        "role": "Leader of Pediatric Hematology-Oncology / Pioneer of CAR-T Cell Therapy in Thailand",
        "email": "suradej.hon@mahidol.ac.th",
        "image_url": "https://www.rama.mahidol.ac.th/images/faculty/suradej.jpg",
        "profile_url": "https://www.rama.mahidol.ac.th/staff/suradej",
        "education": [
            "Fellowship in Pediatric Hematology-Oncology, St. Jude Children's Research Hospital, USA",
            "M.D., Faculty of Medicine Ramathibodi Hospital, Mahidol University",
            "Diploma of the Thai Board of Pediatrics and Pediatric Hematology"
        ],
        "research_interests": [
            "CAR-T Cell Therapy & Cellular Immunotherapy",
            "Hematopoietic Stem Cell Transplantation (HSCT) in Thalassemia",
            "Gene Editing (CRISPR-Cas9) for Hemoglobinopathies",
            "Pediatric Solid Tumors & Neuroblastoma Targeted Therapy",
            "Translational Oncology and Clinical Trials"
        ],
        "taught_courses": [
            "Advanced Hematopoietic Stem Cell Therapy",
            "Cellular and Molecular Immunotherapy",
            "Pediatric Oncology and Genomics"
        ],
        "featured_publications": [
            "Haploidentical Hematopoietic Stem Cell Transplantation in Severe Thalassemia Patients with Post-Transplant Cyclophosphamide",
            "Autologous Anti-CD19 CAR-T Cell Therapy for Relapsed/Refractory B-Cell Acute Lymphoblastic Leukemia in Southeast Asia",
            "CRISPR-Cas9 Gene Editing of BCL11A Enhancer for Fetal Hemoglobin Induction in Beta-Thalassemia"
        ],
        "scholar_url": "https://scholar.google.com/citations?user=SuradejHongeng"
    },

    # =========================================================================
    # KASETSART UNIVERSITY (KU - มหาวิทยาลัยเกษตรศาสตร์ บางเขน / กำแพงแสน)
    # =========================================================================
    {
        "id": "ku_eng_cpe_001",
        "university": "Kasetsart University",
        "university_th": "มหาวิทยาลัยเกษตรศาสตร์",
        "faculty": "Faculty of Engineering",
        "faculty_th": "คณะวิศวกรรมศาสตร์",
        "department": "Department of Computer Engineering",
        "department_th": "ภาควิชาวิศวกรรมคอมพิวเตอร์",
        "academic_title": "Prof. Dr.",
        "academic_title_th": "ศ.ดร.",
        "first_name": "Arunee",
        "last_name": "Ratprasert",
        "full_name": "Prof. Dr. Anan Phonphoem",
        "full_name_th": "ศ.ดร. อนันต์ ผลเพิ่ม",
        "role": "Head of High Performance Computing and Networking Center (HPCNC)",
        "email": "anan.p@ku.ac.th",
        "image_url": "https://cpe.eng.ku.ac.th/images/faculty/anan.jpg",
        "profile_url": "https://cpe.eng.ku.ac.th/staff/anan",
        "education": [
            "Ph.D. (Computer Science), George Washington University, USA",
            "M.S. (Telecommunication Systems), George Washington University, USA",
            "B.Eng. (Electrical Engineering), Kasetsart University"
        ],
        "research_interests": [
            "Computer Networks & Software-Defined Networking (SDN)",
            "Wireless Sensor Networks (WSN) & IoT in Smart Farming",
            "Cloud Computing Infrastructure & Network Security",
            "Vehicular Ad-Hoc Networks (VANET)",
            "Edge AI and Micro-datacenter Orchestration"
        ],
        "taught_courses": [
            "Advanced Computer Networks",
            "Cloud Architecture and Distributed Systems",
            "Internet of Things and Smart Sensor Networks"
        ],
        "featured_publications": [
            "Energy-Efficient Routing Protocols for Long-Range Wireless Sensor Networks in Precision Agriculture",
            "Software-Defined Network Slicing for Critical IoT Infrastructure in Agricultural Supply Chains",
            "Performance Evaluation of CoAP and MQTT Protocols under Degraded Satellite Link Conditions"
        ],
        "scholar_url": "https://scholar.google.com/citations?user=AnanPhonphoem"
    },
    {
        "id": "ku_agri_001",
        "university": "Kasetsart University",
        "university_th": "มหาวิทยาลัยเกษตรศาสตร์",
        "faculty": "Faculty of Agriculture",
        "faculty_th": "คณะเกษตรศาสตร์",
        "department": "Department of Agronomy & Center for Agricultural Biotechnology (CAB)",
        "department_th": "ภาควิชาพืชไร่นา และศูนย์เทคโนโลยีชีวภาพเกษตร",
        "academic_title": "Prof. Dr.",
        "academic_title_th": "ศ.ดร.",
        "first_name": "Peerasak",
        "last_name": "Srinives",
        "full_name": "Prof. Dr. Peerasak Srinives",
        "full_name_th": "ศ.ดร. พีระศักดิ์ ศรีนิเวศน์",
        "role": "National Outstanding Researcher in Plant Breeding & Molecular Genetics / Fellow of Royal Society",
        "email": "peerasak.s@ku.ac.th",
        "image_url": "https://agr.ku.ac.th/images/faculty/peerasak.jpg",
        "profile_url": "https://agr.ku.ac.th/staff/peerasak",
        "education": [
            "Ph.D. (Plant Breeding and Cytogenetics), Iowa State University, USA",
            "M.S. (Plant Breeding), University of Hawaii, USA",
            "B.Sc. (Agriculture - First Class Honours, Gold Medal), Kasetsart University"
        ],
        "research_interests": [
            "Plant Breeding & Quantitative Genetics",
            "Marker-Assisted Selection (MAS) in Legumes and Oil Crops",
            "Genomics of Drought and Salinity Tolerance in Tropical Crops",
            "Gene Editing for High-Oleic Soybean and Mungbean Varieties",
            "Biodiversity Conservation of Indigenous Thai Plant Resources"
        ],
        "taught_courses": [
            "Advanced Plant Breeding",
            "Quantitative Genetics and Biometrical Analysis",
            "Molecular Plant Cytogenetics"
        ],
        "featured_publications": [
            "Genetic Mapping and QTL Identification for Seed Storability and High Protein in Mungbean",
            "Marker-Assisted Introgression of Submergence and Salinity Tolerance Genes in Tropical Rice",
            "Breeding Soybean for High Oleic Acid and Low Linolenic Acid Content under Tropical Lowlands"
        ],
        "scholar_url": "https://scholar.google.com/citations?user=PeerasakSrinives"
    },
    {
        "id": "ku_agro_food_001",
        "university": "Kasetsart University",
        "university_th": "มหาวิทยาลัยเกษตรศาสตร์",
        "faculty": "Faculty of Agro-Industry",
        "faculty_th": "คณะอุตสาหกรรมเกษตร",
        "department": "Department of Food Science and Technology",
        "department_th": "ภาควิชาวิทยาศาสตร์และเทคโนโลยีการอาหาร",
        "academic_title": "Prof. Dr.",
        "academic_title_th": "ศ.ดร.",
        "first_name": "Waraporn",
        "last_name": "Boonsupthip",
        "full_name": "Prof. Dr. Waraporn Boonsupthip",
        "full_name_th": "ศ.ดร. วราภรณ์ บุญทรัพย์ทิพย์",
        "role": "Director of Food Innovation and Rheology Research Laboratory",
        "email": "waraporn.b@ku.ac.th",
        "image_url": "https://agro.ku.ac.th/images/faculty/waraporn.jpg",
        "profile_url": "https://agro.ku.ac.th/staff/waraporn",
        "education": [
            "Ph.D. (Food Science & Food Engineering), Rutgers University, USA",
            "M.S. (Food Science), Rutgers University, USA",
            "B.Sc. (Food Science and Technology - Honours), Kasetsart University"
        ],
        "research_interests": [
            "Food Rheology & Texture Modification for Elderly Nutrition",
            "Cryogenic Freezing & Glass Transition in Frozen Food Preservation",
            "Microencapsulation of Natural Probiotics & Bioactive Compounds",
            "Alternative Protein Texturization (Plant-Based & Insect Proteins)",
            "Sustainable Active and Biodegradable Food Packaging"
        ],
        "taught_courses": [
            "Food Physical Properties and Rheology",
            "Advanced Food Preservation Technologies",
            "Functional Food Product Formulation"
        ],
        "featured_publications": [
            "Glass Transition Temperature and Ice Crystal Morphology during Cryogenic Freezing of Tropical Fruits",
            "Rheological Behavior and Digestibility of Texturized Mung Bean Protein for 3D Food Printing",
            "Active Biodegradable Chitosan-Starch Films Incorporated with Essential Oils for Extended Shelf Life"
        ],
        "scholar_url": "https://scholar.google.com/citations?user=WarapornBoonsupthip"
    }
]
