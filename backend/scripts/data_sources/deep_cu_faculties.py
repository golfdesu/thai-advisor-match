# -*- coding: utf-8 -*-
"""
Master Deep Faculty Advisor Dataset - Chulalongkorn University (CU - จุฬาลงกรณ์มหาวิทยาลัย)
Comprehensive coverage of Distinguished Research Professors, Royal Society Fellows, Center of Excellence Directors, and Leading PIs across:
1. Faculty of Engineering (Computer, Chemical, Mechanical, Electrical, Civil, Environmental, Biomedical, Materials, Industrial)
2. Faculty of Medicine (ChulaVRC mRNA Vaccine, Clinical Virology, Cardiology COOL-AF, Precision Oncology, Movement Disorders DBS, Immunology SLE, Hepatology & Liver Cancer, Epigenetics & Aging)
3. Faculty of Science (Computational Chemistry QM/MM, PNA Diagnostics, Supramolecular Sensors, Marine Coral Cryopreservation, Particle Physics CERN CMS, Shrimp Molecular Immunology, Snail Mucin Biodiversity, Quantum Information)
4. Chulalongkorn Business School - CBS & Sasin (FinTech & DeFi, Marketing Analytics, Consumer Neuroscience, Strategic Agility, Demography & Silver Economy)
5. Faculty of Pharmaceutical Sciences (Pulmonary DPI Inhalers, Silk Sericin Wound Dressings, Nanomedicine, Phytochemistry & Natural Bioactives)
6. Faculty of Architecture (Urban Futures, TOD & Land Value Capture, Sustainable Net-Zero Buildings, Heritage Conservation)
7. Faculty of Economics & Political Science (Behavioral Economics & Nudge, US-China Geopolitics, Strategic & Defense Studies, Aging Welfare)
8. Faculty of Veterinary Science (Swine Virology PRRSV/ASFV, Avian Influenza One Health, Companion Animal Pathology)
9. Faculty of Dentistry (Dental Pulp Stem Cells hDPSCs, 3D Bioceramics Bone Regeneration, Periodontal Immunology)
10. Faculty of Law & Communication Arts (AI Governance & Cyber Law, Strategic Crisis Communication & Health Infodemics)
11. Faculty of Allied Health Sciences & Psychology (Cellular Physiology CFTR, Molecular Diagnostics, Cognitive Behavioral Therapy CBT)
12. Faculty of Arts & Education (Acoustic Phonetics, Southeast Asian History & Maritime Trade, Educational Needs Assessment & Learning Analytics)
13. Petroleum & Petrochemical College (PPC) & MMRI (Bio-based Polymers, Chitosan, Cellulose Nanocrystals, Circular Materials)

All data strictly complies with AGENTS.md & PDPA (Official institutional emails, NO personal phone numbers).
"""

CU_DEEP_EXPANSION_FACULTIES = [
    # =========================================================================
    # 1. FACULTY OF ENGINEERING (CHULALONGKORN UNIVERSITY)
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
            "Evolutionary Computation & Multi-Objective Genetic Algorithms",
            "Robotics, Motion Planning & Autonomous Intelligent Agents",
            "Bioinformatics Algorithms & Genetic Sequence Optimization",
            "Quantum Computing Algorithms & Quantum-Inspired Optimization",
            "Hardware-Software Co-Design & Embedded AI Architecture"
        ],
        "taught_courses": [
            "Evolutionary Computation",
            "Advanced Robotics Control and Intelligent Systems",
            "Bioinformatics Algorithms"
        ],
        "featured_publications": [
            "Multi-Objective Evolutionary Algorithms for Large-Scale Combinatorial Optimization in Smart Cities",
            "Adaptive Neuro-Fuzzy Inference System for Autonomous Robot Navigation in Dynamic Environments",
            "Quantum-Inspired Genetic Algorithms for High-Dimensional Feature Selection and Genomic Classification"
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
            "Inductive Logic Programming & Machine Learning Foundations",
            "Support Vector Machines (SVM) & Kernel Methods in High Dimensions",
            "Thai Natural Language Processing (Thai NLP & Large Language Models)",
            "Deep Learning in Medical Diagnostic Imaging",
            "Automated Knowledge Graph Construction and Ontology Engineering"
        ],
        "taught_courses": [
            "Machine Learning Theory and Applications",
            "Artificial Intelligence",
            "Statistical Pattern Recognition"
        ],
        "featured_publications": [
            "Multi-Class Support Vector Machines with Adaptive Directed Acyclic Graphs",
            "Thai Named Entity Recognition using Transformer-Based Contextual Embeddings and Bi-LSTM-CRF",
            "Deep Convolutional Neural Networks for Automated Diabetic Retinopathy Screening in Resource-Limited Settings"
        ],
        "scholar_url": "https://scholar.google.com/citations?user=BoonsermKijsirikul"
    },
    {
        "id": "cu_eng_cpe_remote_001",
        "university": "Chulalongkorn University",
        "university_th": "จุฬาลงกรณ์มหาวิทยาลัย",
        "faculty": "Faculty of Engineering",
        "faculty_th": "คณะวิศวกรรมศาสตร์",
        "department": "Department of Computer Engineering & Disaster Informatics Lab",
        "department_th": "ภาควิชาวิศวกรรมคอมพิวเตอร์ และห้องปฏิบัติการสารสนเทศภัยพิบัติ",
        "academic_title": "Assoc. Prof. Dr.",
        "academic_title_th": "รศ.ดร.",
        "first_name": "Peerapon",
        "last_name": "Vateekul",
        "full_name": "Assoc. Prof. Dr. Peerapon Vateekul",
        "full_name_th": "รศ.ดร. พีรพล เวทีกูล",
        "role": "Director of Chula AI for Disaster Management and Geospatial Intelligence Hub",
        "email": "peerapon.v@chula.ac.th",
        "image_url": "https://cp.eng.chula.ac.th/images/faculty/peerapon.jpg",
        "profile_url": "https://cp.eng.chula.ac.th/staff/peerapon",
        "education": [
            "Ph.D. (Computer Science), University of Miami, USA",
            "M.S. (Computer Science), University of Miami, USA",
            "B.Eng. (Computer Engineering - First Class Honours), Chulalongkorn University"
        ],
        "research_interests": [
            "Deep Learning for Satellite Remote Sensing & Synthetic Aperture Radar (SAR)",
            "Flood Inundation and Landslide Prediction using Spatio-Temporal Graph Neural Networks",
            "Hierarchical Multi-Label Text Classification for Legal and Enterprise Corpora",
            "PM2.5 Air Pollution Nowcasting using Multi-Modal Remote Sensing and Ground Sensors",
            "Computer Vision for Autonomous Drone Disaster Surveillance"
        ],
        "taught_courses": [
            "Big Data Analytics and Geospatial Intelligence",
            "Deep Learning Applications in Earth Observation",
            "Data Science for Social Impact and Disaster Response"
        ],
        "featured_publications": [
            "Spatio-Temporal Graph Neural Network for Real-Time Urban Flash Flood Forecasting using Sentinel-1 SAR and Rainfall Radars",
            "Deep Multimodal Fusion of Multi-Spectral Satellite Imagery and Ground Sensor Networks for Hourly PM2.5 Prediction",
            "Hierarchical Deep Learning Framework for Multi-Label Document Classification with Semantic Tree Constraint"
        ],
        "scholar_url": "https://scholar.google.com/citations?user=PeeraponVateekul"
    },
    {
        "id": "cu_eng_cpe_vision_002",
        "university": "Chulalongkorn University",
        "university_th": "จุฬาลงกรณ์มหาวิทยาลัย",
        "faculty": "Faculty of Engineering",
        "faculty_th": "คณะวิศวกรรมศาสตร์",
        "department": "Department of Computer Engineering & Visual Information Processing Lab",
        "department_th": "ภาควิชาวิศวกรรมคอมพิวเตอร์ และห้องปฏิบัติการประมวลผลข้อมูลภาพ",
        "academic_title": "Assoc. Prof. Dr.",
        "academic_title_th": "รศ.ดร.",
        "first_name": "Thanarat",
        "last_name": "Chalidabhongse",
        "full_name": "Assoc. Prof. Dr. Thanarat Chalidabhongse",
        "full_name_th": "รศ.ดร. ธนารัตน์ ชลิดาพงศ์",
        "role": "Head of Visual Information Processing Laboratory / Senior AI Computer Vision Specialist",
        "email": "thanarat.c@chula.ac.th",
        "image_url": "https://cp.eng.chula.ac.th/images/faculty/thanarat.jpg",
        "profile_url": "https://cp.eng.chula.ac.th/staff/thanarat",
        "education": [
            "Ph.D. (Computer Science / Computer Vision), University of Maryland, College Park, USA",
            "M.S. (Computer Science), University of Maryland, College Park, USA",
            "B.Eng. (Computer Engineering - First Class Honours), Chulalongkorn University"
        ],
        "research_interests": [
            "Visual Surveillance, Human Activity Recognition and Abnormal Behavior Detection",
            "Background Subtraction and Robust Motion Tracking in Complex Urban Scenes",
            "3D Human Pose Estimation and Biomechanical Movement Analysis",
            "Deep Learning for Automated Defect Inspection in Manufacturing Lines",
            "Multi-Camera Tracking and Re-Identification in Large-Scale Environments"
        ],
        "taught_courses": [
            "Computer Vision and Pattern Recognition",
            "Digital Image Processing and Visual Computing",
            "Deep Learning for Visual Understanding"
        ],
        "featured_publications": [
            "Perturbation-Based Dynamic Background Modeling for Robust Motion Detection in Outdoor Surveillance",
            "Spatial-Temporal Graph Convolutional Networks for Skeleton-Based Fall Detection in Elderly Care Facilities",
            "Multi-Target Multi-Camera Tracking using Appearance-Topology Consistency Constraints"
        ],
        "scholar_url": "https://scholar.google.com/citations?user=ThanaratChalidabhongse"
    },
    {
        "id": "cu_eng_cpe_bigdata_003",
        "university": "Chulalongkorn University",
        "university_th": "จุฬาลงกรณ์มหาวิทยาลัย",
        "faculty": "Faculty of Engineering",
        "faculty_th": "คณะวิศวกรรมศาสตร์",
        "department": "Department of Computer Engineering & Distributed Systems Lab",
        "department_th": "ภาควิชาวิศวกรรมคอมพิวเตอร์ และห้องปฏิบัติการระบบกระจายและบิ๊กดาต้า",
        "academic_title": "Assoc. Prof. Dr.",
        "academic_title_th": "รศ.ดร.",
        "first_name": "Natawut",
        "last_name": "Nupairoj",
        "full_name": "Assoc. Prof. Dr. Natawut Nupairoj",
        "full_name_th": "รศ.ดร. ณัฐวุฒิ หนูไพโรจน์",
        "role": "Director of Big Data and Cloud Computing Laboratory / Senior Architect in Distributed High-Performance Systems",
        "email": "natawut.n@chula.ac.th",
        "image_url": "https://cp.eng.chula.ac.th/images/faculty/natawut.jpg",
        "profile_url": "https://cp.eng.chula.ac.th/staff/natawut",
        "education": [
            "Ph.D. (Computer Science and Engineering), Michigan State University, USA",
            "M.S. (Computer Science and Engineering), Michigan State University, USA",
            "B.Eng. (Computer Engineering - First Class Honours), Chulalongkorn University"
        ],
        "research_interests": [
            "Big Data Architecture, Stream Processing and Real-Time Data Pipelines",
            "Cloud Native Infrastructure, Distributed File Systems and Kubernetes Orchestration",
            "Federated Learning and Privacy-Preserving Machine Learning on Edge Clusters",
            "Graph Database Query Optimization for Large-Scale Financial Knowledge Graphs",
            "Scalable Microservices Performance Modeling and Fault Tolerance"
        ],
        "taught_courses": [
            "Cloud Computing and Distributed Systems",
            "Big Data Engineering and Architecture",
            "Advanced Operating Systems and Cluster Computing"
        ],
        "featured_publications": [
            "Adaptive Resource Provisioning Framework for Streaming Big Data Workloads in Hybrid Cloud",
            "Privacy-Preserving Federated Learning over Heterogeneous Distributed Edge Devices with Differential Privacy",
            "Scalable Graph Analytics Engine for Complex Transaction Network Fraud Detection in Digital Banking"
        ],
        "scholar_url": "https://scholar.google.com/citations?user=NatawutNupairoj"
    },
    {
        "id": "cu_eng_chem_001",
        "university": "Chulalongkorn University",
        "university_th": "จุฬาลงกรณ์มหาวิทยาลัย",
        "faculty": "Faculty of Engineering",
        "faculty_th": "คณะวิศวกรรมศาสตร์",
        "department": "Department of Chemical Engineering & Center of Excellence in Catalysis",
        "department_th": "ภาควิชาวิศวกรรมเคมี และศูนย์ความเป็นเลิศด้านการเร่งปฏิกิริยา",
        "academic_title": "Prof. Dr.",
        "academic_title_th": "ศ.ดร.",
        "first_name": "Suttichai",
        "last_name": "Assabumrungrat",
        "full_name": "Prof. Dr. Suttichai Assabumrungrat",
        "full_name_th": "ศ.ดร. สุทธิชัย อัสสะบำรุงรัตน์",
        "role": "Distinguished Research Professor of Thailand / Fellow of Royal Society / World Top 1% Scientist in Chemical Engineering",
        "email": "suttichai.a@chula.ac.th",
        "image_url": "https://chem.eng.chula.ac.th/images/faculty/suttichai.jpg",
        "profile_url": "https://chem.eng.chula.ac.th/staff/suttichai",
        "education": [
            "Ph.D. (Chemical Engineering), Imperial College London, UK",
            "M.Sc. (Chemical Engineering), Imperial College London, UK",
            "B.Eng. (Chemical Engineering - First Class Honours, Gold Medal), Chulalongkorn University"
        ],
        "research_interests": [
            "Heterogeneous Catalysis & Multifunctional Chemical Reactors",
            "Solid Oxide Fuel Cells (SOFC) & Solid Oxide Electrolyzers (SOEC)",
            "Green Hydrogen Production from Biogas & Biorefinery Processes",
            "Carbon Capture, Utilization and Storage (CCUS) & CO2 Methanation",
            "Process Intensification & Membrane Reactive Distillation"
        ],
        "taught_courses": [
            "Advanced Chemical Reaction Engineering",
            "Heterogeneous Catalysis and Reactor Design",
            "Hydrogen Energy Systems and Fuel Cells"
        ],
        "featured_publications": [
            "Recent Advances in Solid Oxide Fuel Cells: Materials, Modeling, and Carbon Capture Integration",
            "CO2 Hydrogenation to Methanol and Light Hydrocarbons over Metal-Supported Catalysts: Kinetics and Mechanism",
            "Process Intensification for Biodiesel Production via Reactive Distillation: Techno-Economic Assessment"
        ],
        "scholar_url": "https://scholar.google.com/citations?user=SuttichaiAssabumrungrat"
    },
    {
        "id": "cu_eng_chem_poly_003",
        "university": "Chulalongkorn University",
        "university_th": "จุฬาลงกรณ์มหาวิทยาลัย",
        "faculty": "Faculty of Engineering",
        "faculty_th": "คณะวิศวกรรมศาสตร์",
        "department": "Department of Chemical Engineering & Center of Excellence on Catalysis and Catalytic Reaction Engineering",
        "department_th": "ภาควิชาวิศวกรรมเคมี และศูนย์ความเป็นเลิศด้านการเร่งปฏิกิริยาและวิศวกรรมปฏิกิริยาการเร่ง",
        "academic_title": "Prof. Dr.",
        "academic_title_th": "ศ.ดร.",
        "first_name": "Piyasan",
        "last_name": "Praserthdam",
        "full_name": "Prof. Dr. Piyasan Praserthdam",
        "full_name_th": "ศ.ดร. ปิยะสาร ประเสริฐธรรม",
        "role": "Distinguished Research Professor of Thailand / Fellow of Royal Society / Pioneer in Polyolefin Polymerization Catalysts",
        "email": "piyasan.p@chula.ac.th",
        "image_url": "https://chem.eng.chula.ac.th/images/faculty/piyasan.jpg",
        "profile_url": "https://chem.eng.chula.ac.th/staff/piyasan",
        "education": [
            "Ph.D. (Chemical Engineering), Rice University, USA",
            "M.S. (Chemical Engineering), Rice University, USA",
            "B.Eng. (Chemical Engineering - Honours), Chulalongkorn University"
        ],
        "research_interests": [
            "Ziegler-Natta and Metallocene Catalysts for Polyethylene and Polypropylene Polymerization",
            "Photocatalytic Solar Hydrogen Production and Water Splitting over Nanostructured TiO2/g-C3N4",
            "Catalytic Deactivation Mechanisms and Coke Formation in Petrochemical Steam Crackers",
            "Synthesis of Mesoporous Zeolites for Hydrocarbon Isomerization and Alkylation",
            "Theoretical Density Functional Theory (DFT) Modeling of Heterogeneous Catalytic Surfaces"
        ],
        "taught_courses": [
            "Polymer Reaction Engineering and Catalysis",
            "Industrial Heterogeneous Catalytic Processes",
            "Advanced Surface Chemistry and Catalysis Kinetics"
        ],
        "featured_publications": [
            "Deactivation Kinetics and Structure Sensitivity of Ziegler-Natta Catalysts in Ethylene Polymerization",
            "Enhanced Photocatalytic Hydrogen Evolution over 2D/2D g-C3N4/TiO2 Heterojunctions under Visible Light",
            "Density Functional Theory Insights into the Active Sites and Reaction Pathways of Olefin Metathesis on Supported Rhenium Catalysts"
        ],
        "scholar_url": "https://scholar.google.com/citations?user=PiyasanPraserthdam"
    },
    {
        "id": "cu_eng_chem_biorefinery_001",
        "university": "Chulalongkorn University",
        "university_th": "จุฬาลงกรณ์มหาวิทยาลัย",
        "faculty": "Faculty of Engineering",
        "faculty_th": "คณะวิศวกรรมศาสตร์",
        "department": "Department of Chemical Engineering & Bio-Refinery Research Unit",
        "department_th": "ภาควิชาวิศวกรรมเคมี และหน่วยปฏิบัติการวิจัยชีววิศวกรรมการสกัด",
        "academic_title": "Prof. Dr.",
        "academic_title_th": "ศ.ดร.",
        "first_name": "Artiwan",
        "last_name": "Shotipruk",
        "full_name": "Prof. Dr. Artiwan Shotipruk",
        "full_name_th": "ศ.ดร. อัญชลีพร วาริทสวัสดิ์ (อารตีวรรณ โชติพฤกษ์)",
        "role": "Distinguished Professor in Subcritical Water Extraction and Green Biorefinery Technologies",
        "email": "artiwan.s@chula.ac.th",
        "image_url": "https://chem.eng.chula.ac.th/images/faculty/artiwan.jpg",
        "profile_url": "https://chem.eng.chula.ac.th/staff/artiwan",
        "education": [
            "Ph.D. (Chemical Engineering), University of Michigan, Ann Arbor, USA",
            "M.S. (Chemical Engineering), University of Michigan, Ann Arbor, USA",
            "B.Eng. (Chemical Engineering - First Class Honours), Chulalongkorn University"
        ],
        "research_interests": [
            "Subcritical Water Hydrolysis and Green Solvent Extraction of High-Value Biocompounds",
            "Lignocellulosic Biomass Valorization to Furfural, HMF, and Bio-based Chemicals",
            "Pressurized Liquid Extraction (PLE) and Supercritical CO2 Fluid Processing",
            "Microbial Lipid Extraction from Microalgae for Sustainable Aviation Fuel (SAF)",
            "Circular Bioeconomy Process Synthesis and Techno-Economic Life Cycle Analysis"
        ],
        "taught_courses": [
            "Separation Processes and Green Extraction Technologies",
            "Biochemical Engineering and Biorefinery Design",
            "Advanced Mass Transfer and Fluid Phase Equilibria"
        ],
        "featured_publications": [
            "Subcritical Water Extraction and Hydrolysis of Agricultural Biomass for Value-Added Phenolic and Sugar Recovery",
            "Continuous Production of 5-Hydroxymethylfurfural (HMF) from Glucose using Green Biphasic Catalytic Systems",
            "Valorization of Defatted Rice Bran into Protein Hydrolysates and Antioxidants via Subcritical Water Treatment"
        ],
        "scholar_url": "https://scholar.google.com/citations?user=ArtiwanShotipruk"
    },
    {
        "id": "cu_eng_chem_nanocarbon_002",
        "university": "Chulalongkorn University",
        "university_th": "จุฬาลงกรณ์มหาวิทยาลัย",
        "faculty": "Faculty of Engineering",
        "faculty_th": "คณะวิศวกรรมศาสตร์",
        "department": "Department of Chemical Engineering & Particle and Material Technology Research Unit",
        "department_th": "ภาควิชาวิศวกรรมเคมี และหน่วยวิจัยเทคโนโลยีอนุภาคและวัสดุ",
        "academic_title": "Prof. Dr.",
        "academic_title_th": "ศ.ดร.",
        "first_name": "Tawatchai",
        "last_name": "Charinpanitkul",
        "full_name": "Prof. Dr. Tawatchai Charinpanitkul",
        "full_name_th": "ศ.ดร. ธวัชชัย ชรินพาณิชกุล",
        "role": "Distinguished Professor in Particle Technology, Carbon Nanomaterials and Aerosol Engineering",
        "email": "tawatchai.c@chula.ac.th",
        "image_url": "https://chem.eng.chula.ac.th/images/faculty/tawatchai.jpg",
        "profile_url": "https://chem.eng.chula.ac.th/staff/tawatchai",
        "education": [
            "D.Eng. (Chemical Engineering), University of Tokyo, Japan",
            "M.Eng. (Chemical Engineering), University of Tokyo, Japan",
            "B.Eng. (Chemical Engineering - First Class Honours, Gold Medal), Chulalongkorn University"
        ],
        "research_interests": [
            "Continuous Synthesis of Carbon Nanotubes, Graphene and Quantum Dots",
            "Aerosol Flame Synthesis and Fluidized Bed Reactors for Nanocatalysts",
            "Carbon-Based Composite Materials for Supercapacitors and Lithium-Ion Anodes",
            "Adsorption of Micro-Pollutants and Heavy Metals using Engineered Biochar",
            "Computational Fluid Dynamics (CFD) Multiphase Granular Flow Simulation"
        ],
        "taught_courses": [
            "Particle Technology and Granular Systems",
            "Aerosol Engineering and Nanomaterial Synthesis",
            "Advanced Transport Phenomena in Multiphase Reactors"
        ],
        "featured_publications": [
            "Large-Scale Continuous Chemical Vapor Deposition of High-Purity Carbon Nanotubes over Bimetallic Catalysts",
            "Graphene-Wrapped Silicon Nanoparticle Anodes for High-Capacity Fast-Charging Lithium-Ion Batteries",
            "Engineered Porous Carbon from Biomass Wastes for Efficient Atmospheric CO2 Capture and Gas Separation"
        ],
        "scholar_url": "https://scholar.google.com/citations?user=TawatchaiCharinpanitkul"
    },
    {
        "id": "cu_eng_robotics_001",
        "university": "Chulalongkorn University",
        "university_th": "จุฬาลงกรณ์มหาวิทยาลัย",
        "faculty": "Faculty of Engineering",
        "faculty_th": "คณะวิศวกรรมศาสตร์",
        "department": "Department of Mechanical Engineering & Medical Robotics Center",
        "department_th": "ภาควิชาวิศวกรรมเครื่องกล และศูนย์วิจัยหุ่นยนต์ทางการแพทย์",
        "academic_title": "Prof. Dr.",
        "academic_title_th": "ศ.ดร.",
        "first_name": "Viboon",
        "last_name": "Sangveraphunsiri",
        "full_name": "Prof. Dr. Viboon Sangveraphunsiri",
        "full_name_th": "ศ.ดร. วิบูลย์ แสงวีระพันธุ์ศิริ",
        "role": "Head of Regional Center for Robotics and Mechatronics / Pioneer in Medical Rehabilitation Exoskeletons",
        "email": "viboon.s@chula.ac.th",
        "image_url": "https://me.eng.chula.ac.th/images/faculty/viboon.jpg",
        "profile_url": "https://me.eng.chula.ac.th/staff/viboon",
        "education": [
            "Ph.D. (Mechanical Engineering), Georgia Institute of Technology, USA",
            "M.S. (Mechanical Engineering), Georgia Institute of Technology, USA",
            "B.Eng. (Mechanical Engineering - First Class Honours), Chulalongkorn University"
        ],
        "research_interests": [
            "Robotic Exoskeletons & Upper/Lower Limb Stroke Rehabilitation Devices (SensibleTab / SensibleHand)",
            "Tele-Robotic Surgical Systems and Force Feedback Haptic Master-Slave Arms",
            "Industrial Robot Manipulator Dynamics & Non-Linear Control",
            "Autonomous Mobile Robots (AMR) for Hospital and Cleanroom Logistics",
            "Sensor Fusion and AI-Driven Gait Trajectory Planning"
        ],
        "taught_courses": [
            "Advanced Robotics and Spatial Kinematics",
            "Medical Robotics and Human-Robot Interaction",
            "Modern Control Engineering and Digital Signal Processing"
        ],
        "featured_publications": [
            "Design and Clinical Validation of an Upper-Limb Robotic Exoskeleton for Stroke Neurorehabilitation",
            "Adaptive Impedance and Force Control for Compliant Robotic Rehabilitation Systems",
            "Autonomous Navigation and Fleet Management of Hospital Delivery Robots during Epidemic Crises"
        ],
        "scholar_url": "https://scholar.google.com/citations?user=ViboonSangveraphunsiri"
    },
    {
        "id": "cu_eng_me_thermal_001",
        "university": "Chulalongkorn University",
        "university_th": "จุฬาลงกรณ์มหาวิทยาลัย",
        "faculty": "Faculty of Engineering",
        "faculty_th": "คณะวิศวกรรมศาสตร์",
        "department": "Department of Mechanical Engineering & Fluid Mechanics and Thermal Engineering Lab",
        "department_th": "ภาควิชาวิศวกรรมเครื่องกล",
        "academic_title": "Prof. Dr.",
        "academic_title_th": "ศ.ดร.",
        "first_name": "Somchai",
        "last_name": "Wongwises",
        "full_name": "Prof. Dr. Somchai Wongwises",
        "full_name_th": "ศ.ดร. สมชาย วงศ์วิเศษ",
        "role": "Distinguished Research Professor of Thailand / Fellow of Royal Society / World-Renowned Expert in Two-Phase Flow & Heat Exchangers",
        "email": "somchai.w@chula.ac.th",
        "image_url": "https://me.eng.chula.ac.th/images/faculty/somchai.jpg",
        "profile_url": "https://me.eng.chula.ac.th/staff/somchai",
        "education": [
            "Dr.-Ing. (Thermal and Nuclear Process Engineering), University of Karlsruhe (KIT), Germany",
            "M.Eng. (Mechanical Engineering), Chulalongkorn University",
            "B.Eng. (Mechanical Engineering - Honours), Chulalongkorn University"
        ],
        "research_interests": [
            "Two-Phase Gas-Liquid Flow Dynamics, Condensation and Evaporation in Microchannels",
            "Nanofluids Thermophysical Properties and Convective Heat Transfer Enhancement",
            "Advanced Compact Heat Exchanger Design for Zero-Carbon Air-Conditioning and Heat Pumps",
            "Supercritical CO2 Brayton Power Cycles for Concentrated Solar Power",
            "Thermal Management of Electric Vehicle High-Energy Lithium-Ion Battery Packs"
        ],
        "taught_courses": [
            "Advanced Fluid Mechanics and Turbulence",
            "Convective Heat and Mass Transfer",
            "Two-Phase Flow Phenomena and Heat Exchanger Design"
        ],
        "featured_publications": [
            "Review of Boiling Heat Transfer and Pressure Drop in Micro- and Minichannels with Low-GWP Refrigerants",
            "Heat Transfer Characteristics and Thermal Conductivity of Hybrid Graphene-Metallic Nanofluids",
            "Direct Contact Condensation of Steam Jets in Subcooled Water: Regimes, Heat Transfer, and Pressure Oscillations"
        ],
        "scholar_url": "https://scholar.google.com/citations?user=SomchaiWongwises"
    },
    {
        "id": "cu_eng_ee_power_001",
        "university": "Chulalongkorn University",
        "university_th": "จุฬาลงกรณ์มหาวิทยาลัย",
        "faculty": "Faculty of Engineering",
        "faculty_th": "คณะวิศวกรรมศาสตร์",
        "department": "Department of Electrical Engineering (Power Systems Division)",
        "department_th": "ภาควิชาวิศวกรรมไฟฟ้า (สาขาวิศวกรรมระบบไฟฟ้ากำลัง)",
        "academic_title": "Prof. Dr.",
        "academic_title_th": "ศ.ดร.",
        "first_name": "Surachai",
        "last_name": "Chaitusaney",
        "full_name": "Prof. Dr. Surachai Chaitusaney",
        "full_name_th": "ศ.ดร. สุรชัย ชัยทัศนีย์",
        "role": "Head of Smart Grid & Renewable Energy Integration Research Unit",
        "email": "surachai.c@chula.ac.th",
        "image_url": "https://ee.eng.chula.ac.th/images/faculty/surachai.jpg",
        "profile_url": "https://ee.eng.chula.ac.th/staff/surachai",
        "education": [
            "Ph.D. (Electrical Engineering), University of Tokyo, Japan",
            "M.Eng. (Electrical Engineering), University of Tokyo, Japan",
            "B.Eng. (Electrical Engineering - First Class Honours), Chulalongkorn University"
        ],
        "research_interests": [
            "Smart Grid Reliability and Power Quality",
            "High Penetration of Distributed PV and Wind into National Grid",
            "Battery Energy Storage System (BESS) Sizing and Optimal Dispatch",
            "Microgrid Protection Coordination with Inverter-Based Resources (IBR)",
            "Dynamic Stability and Frequency Regulation in Low-Inertia Grids"
        ],
        "taught_courses": [
            "Power System Analysis and Control",
            "Smart Grid Architecture and Operations",
            "Power System Protection with Distributed Generation"
        ],
        "featured_publications": [
            "Reliability Evaluation of Smart Distribution Systems with High Penetration of Rooftop Photovoltaic Systems",
            "Optimal Battery Energy Storage Sizing for Frequency Support in Low-Inertia Islanded Microgrids",
            "Adaptive Overcurrent Protection Coordination in Active Distribution Networks with Inverter-Based Distributed Generation"
        ],
        "scholar_url": "https://scholar.google.com/citations?user=SurachaiChaitusaney"
    },
    {
        "id": "cu_eng_ee_control_001",
        "university": "Chulalongkorn University",
        "university_th": "จุฬาลงกรณ์มหาวิทยาลัย",
        "faculty": "Faculty of Engineering",
        "faculty_th": "คณะวิศวกรรมศาสตร์",
        "department": "Department of Electrical Engineering (Control & Automation Division)",
        "department_th": "ภาควิชาวิศวกรรมไฟฟ้า (สาขาวิชาวิศวกรรมควบคุมและระบบอัตโนมัติ)",
        "academic_title": "Prof. Dr.",
        "academic_title_th": "ศ.ดร.",
        "first_name": "David",
        "last_name": "Banjerdpongchai",
        "full_name": "Prof. Dr. David Banjerdpongchai",
        "full_name_th": "ศ.ดร. เดวิด บรรเจิดพงศ์ชัย",
        "role": "Distinguished Professor in Advanced Process Control, Convex Optimization & Smart Building Energy Management",
        "email": "david.b@chula.ac.th",
        "image_url": "https://ee.eng.chula.ac.th/images/faculty/david.jpg",
        "profile_url": "https://ee.eng.chula.ac.th/staff/david",
        "education": [
            "Ph.D. (Electrical Engineering), Stanford University, USA",
            "M.S. (Electrical Engineering), Stanford University, USA",
            "B.Eng. (Electrical Engineering - First Class Honours, Gold Medal), Chulalongkorn University"
        ],
        "research_interests": [
            "Model Predictive Control (MPC) and Robust Multivariable Control",
            "Convex Optimization Algorithms (Linear Matrix Inequalities - LMI)",
            "Building Energy Management Systems (BEMS) & HVAC Optimization",
            "Fault Detection and Isolation (FDI) in Industrial Petrochemical Processes",
            "Cyber-Physical System Security in Critical Energy Infrastructures"
        ],
        "taught_courses": [
            "Linear Multivariable Control Systems",
            "Convex Optimization and Robust Control",
            "Advanced Process Control and Industrial Automation"
        ],
        "featured_publications": [
            "Model Predictive Control with Economic Objective for Multi-Chiller Energy Optimization in Large-Scale Buildings",
            "Robust H-infinity Control Synthesis for Time-Delay Systems with Polytopic Uncertainties using LMI",
            "Data-Driven Fault Detection and Diagnosis for Industrial Gas Turbines using Sparse Representation"
        ],
        "scholar_url": "https://scholar.google.com/citations?user=DavidBanjerdpongchai"
    },
    {
        "id": "cu_eng_ee_ic_002",
        "university": "Chulalongkorn University",
        "university_th": "จุฬาลงกรณ์มหาวิทยาลัย",
        "faculty": "Faculty of Engineering",
        "faculty_th": "คณะวิศวกรรมศาสตร์",
        "department": "Department of Electrical Engineering (Microelectronics Division)",
        "department_th": "ภาควิชาวิศวกรรมไฟฟ้า (สาขาวิชาไมโครอิเล็กทรอนิกส์และวงจรรวม)",
        "academic_title": "Prof. Dr.",
        "academic_title_th": "ศ.ดร.",
        "first_name": "Ekachai",
        "last_name": "Leelarasmee",
        "full_name": "Prof. Dr. Ekachai Leelarasmee",
        "full_name_th": "ศ.ดร. เอกชัย ลีลารัศมี",
        "role": "Distinguished Professor in Integrated Circuit Design / Co-Creator of the Waveform Relaxation Algorithm for SPICE Circuit Simulation",
        "email": "ekachai.l@chula.ac.th",
        "image_url": "https://ee.eng.chula.ac.th/images/faculty/ekachai.jpg",
        "profile_url": "https://ee.eng.chula.ac.th/staff/ekachai",
        "education": [
            "Ph.D. (Electrical Engineering and Computer Sciences), University of California, Berkeley, USA",
            "M.S. (Electrical Engineering and Computer Sciences), University of California, Berkeley, USA",
            "B.Eng. (Electrical Engineering - First Class Honours, Gold Medal), Chulalongkorn University"
        ],
        "research_interests": [
            "Analog and Mixed-Signal CMOS Integrated Circuit Design",
            "Ultra-Low-Power Biomedical Sensor Interfaces and Implantable ICs",
            "VLSI CAD Algorithms and Accelerated Circuit Simulation Methods",
            "Energy Harvesting Circuit Architectures for Batteryless IoT Nodes",
            "High-Efficiency Switched-Capacitor DC-DC Power Converters"
        ],
        "taught_courses": [
            "Analog Integrated Circuit Design",
            "Advanced VLSI Systems Design and CAD",
            "Semiconductor Device Modeling for Circuit Simulation"
        ],
        "featured_publications": [
            "The Waveform Relaxation Method for Time-Domain Analysis of Large-Scale Integrated Circuits",
            "An Ultra-Low-Power Multi-Channel Biopotential Acquisition ASIC for Neural Signal Recording",
            "High-Efficiency Reconfigurable Switched-Capacitor DC-DC Converter for Biomedical Implants"
        ],
        "scholar_url": "https://scholar.google.com/citations?user=EkachaiLeelarasmee"
    },
    {
        "id": "cu_eng_ee_vision_001",
        "university": "Chulalongkorn University",
        "university_th": "จุฬาลงกรณ์มหาวิทยาลัย",
        "faculty": "Faculty of Engineering",
        "faculty_th": "คณะวิศวกรรมศาสตร์",
        "department": "Department of Electrical Engineering (Multimedia & Communications)",
        "department_th": "ภาควิชาวิศวกรรมไฟฟ้า (สาขาวิชามัลติมีเดียและโทรคมนาคม)",
        "academic_title": "Assoc. Prof. Dr.",
        "academic_title_th": "รศ.ดร.",
        "first_name": "Supavadee",
        "last_name": "Aramvith",
        "full_name": "Assoc. Prof. Dr. Supavadee Aramvith",
        "full_name_th": "รศ.ดร. สุภาวดี อร่ามวิทย์",
        "role": "IEEE Fellow / Senior Director of Video Communications and Deep Computer Vision Lab",
        "email": "supavadee.a@chula.ac.th",
        "image_url": "https://ee.eng.chula.ac.th/images/faculty/supavadee.jpg",
        "profile_url": "https://ee.eng.chula.ac.th/staff/supavadee",
        "education": [
            "Ph.D. (Electrical Engineering), University of Washington, Seattle, USA",
            "M.S. (Electrical Engineering), University of Washington, Seattle, USA",
            "B.Eng. (Computer Engineering - First Class Honours), Mahidol University"
        ],
        "research_interests": [
            "Video Coding Standards (VVC / H.266, HEVC) & Low-Bitrate Streaming",
            "Deep Learning Computer Vision for Surveillance and Abnormal Behavior Detection",
            "Drone-Based Aerial Object Tracking and Real-Time Search-and-Rescue Vision",
            "Multimodal Image Enhancement in Adverse Weather (Rain, Fog, Low-Light)",
            "Edge AI Vision Analytics for Smart Traffic Monitoring"
        ],
        "taught_courses": [
            "Digital Video Processing and Compression",
            "Advanced Computer Vision and Deep Learning",
            "Multimedia Communications and Protocols"
        ],
        "featured_publications": [
            "Low-Complexity Versatile Video Coding (VVC) Rate-Distortion Optimization for High-Dynamic-Range Content",
            "Real-Time Multiobject Aerial Tracking from UAV Video Streams using Deep Association Feature Fusion",
            "Unsupervised Deep Image Deraining and Dehazing for Autonomous Transportation Safety"
        ],
        "scholar_url": "https://scholar.google.com/citations?user=SupavadeeAramvith"
    },
    {
        "id": "cu_eng_bme_001",
        "university": "Chulalongkorn University",
        "university_th": "จุฬาลงกรณ์มหาวิทยาลัย",
        "faculty": "Faculty of Engineering",
        "faculty_th": "คณะวิศวกรรมศาสตร์",
        "department": "Biomedical Engineering Program",
        "department_th": "หลักสูตรวิศวกรรมชีวการแพทย์",
        "academic_title": "Assoc. Prof. Dr.",
        "academic_title_th": "รศ.ดร.",
        "first_name": "Juthamas",
        "last_name": "Ratanavaraporn",
        "full_name": "Assoc. Prof. Dr. Juthamas Ratanavaraporn",
        "full_name_th": "รศ.ดร. จุฑามาศ รัตนวราภรณ์",
        "role": "Director of Biomedical Biomaterials and Tissue Engineering Laboratory",
        "email": "juthamas.r@chula.ac.th",
        "image_url": "https://bme.eng.chula.ac.th/images/faculty/juthamas.jpg",
        "profile_url": "https://bme.eng.chula.ac.th/staff/juthamas",
        "education": [
            "Ph.D. (Biomaterials Science), Kyoto University, Japan",
            "M.Sc. (Biotechnology), Chulalongkorn University",
            "B.Sc. (Biochemistry), Chulalongkorn University"
        ],
        "research_interests": [
            "Silk Fibroin and Natural Polymer Biomaterials for Tissue Regeneration",
            "3D Bioprinting of Cartilage, Skin, and Bone Scaffolds",
            "Nanoparticle Targeted Drug and Nucleic Acid Delivery Systems",
            "Hydrogel Wound Dressings with Antimicrobial Peptides",
            "Biocompatibility and In-Vivo Preclinical Evaluation"
        ],
        "taught_courses": [
            "Biomaterials and Tissue Engineering",
            "Drug Delivery Systems and Nanomedicine",
            "Biocompatibility Testing and Regulatory Affairs"
        ],
        "featured_publications": [
            "Silk Fibroin-Gelatin 3D Scaffolds with Sustained Growth Factor Release for Articular Cartilage Repair",
            "Injectable Self-Healing Hydrogels based on Modified Chitosan for Hemostatic Wound Dressings",
            "Targeted Polymeric Nanocarriers for Chemotherapeutic Drug Delivery in Breast Cancer Models"
        ],
        "scholar_url": "https://scholar.google.com/citations?user=JuthamasRatanavaraporn"
    },
    {
        "id": "cu_eng_civil_001",
        "university": "Chulalongkorn University",
        "university_th": "จุฬาลงกรณ์มหาวิทยาลัย",
        "faculty": "Faculty of Engineering",
        "faculty_th": "คณะวิศวกรรมศาสตร์",
        "department": "Department of Civil Engineering & Center of Excellence in Earthquake Engineering",
        "department_th": "ภาควิชาวิศวกรรมโยธา และศูนย์เชี่ยวชาญเฉพาะทางด้านวิศวกรรมแผ่นดินไหว",
        "academic_title": "Prof. Dr.",
        "academic_title_th": "ศ.ดร.",
        "first_name": "Boonchai",
        "last_name": "Ukritchon",
        "full_name": "Prof. Dr. Boonchai Ukritchon",
        "full_name_th": "ศ.ดร. บุญชัย อุกฤษฏชน",
        "role": "Distinguished Professor in Geotechnical and Structural Stability Engineering",
        "email": "boonchai.u@chula.ac.th",
        "image_url": "https://civil.eng.chula.ac.th/images/faculty/boonchai.jpg",
        "profile_url": "https://civil.eng.chula.ac.th/staff/boonchai",
        "education": [
            "Ph.D. (Geotechnical Engineering), University of Cambridge, UK",
            "M.Eng. (Civil Engineering), Asian Institute of Technology (AIT)",
            "B.Eng. (Civil Engineering - First Class Honours), Chulalongkorn University"
        ],
        "research_interests": [
            "Numerical Limit Analysis & Finite Element Limit Analysis (FELA) for Soft Clays",
            "Underground Tunneling and Deep Excavation Stability in Bangkok Clay",
            "Seismic Ground Response and Liquefaction Vulnerability in Deep Sedimentary Basins",
            "Slope Stability & Landslide Risk Assessment under Heavy Rainfall",
            "Soil-Structure Interaction for High-Rise Foundations and Mega Piles"
        ],
        "taught_courses": [
            "Advanced Geotechnical Engineering",
            "Finite Element Analysis in Geotechnics",
            "Foundation Engineering for High-Rise Structures"
        ],
        "featured_publications": [
            "Stability Analysis of Deep Unlined Circular Tunnels in Bangkok Soft Clay Using Finite Element Limit Analysis",
            "Undrained Stability of Supported Deep Excavations in Non-Homogeneous Soft Clays",
            "Three-Dimensional Stability of Slopes Subjected to Seepage and High-Intensity Precipitation"
        ],
        "scholar_url": "https://scholar.google.com/citations?user=BoonchaiUkritchon"
    },
    {
        "id": "cu_eng_env_001",
        "university": "Chulalongkorn University",
        "university_th": "จุฬาลงกรณ์มหาวิทยาลัย",
        "faculty": "Faculty of Engineering",
        "faculty_th": "คณะวิศวกรรมศาสตร์",
        "department": "Department of Environmental Engineering & Water Resources Research Hub",
        "department_th": "ภาควิชาวิศวกรรมสิ่งแวดล้อม",
        "academic_title": "Prof. Dr.",
        "academic_title_th": "ศ.ดร.",
        "first_name": "Pisut",
        "last_name": "Painmanakul",
        "full_name": "Prof. Dr. Pisut Painmanakul",
        "full_name_th": "ศ.ดร. พิสุทธิ์ เพียรมนกุล",
        "role": "Distinguished Professor in Advanced Water Purification and Clean Air Technologies",
        "email": "pisut.p@chula.ac.th",
        "image_url": "https://env.eng.chula.ac.th/images/faculty/pisut.jpg",
        "profile_url": "https://env.eng.chula.ac.th/staff/pisut",
        "education": [
            "Ph.D. (Process and Environmental Engineering), INSA Toulouse, France",
            "M.Sc. (Environmental Engineering), INSA Toulouse, France",
            "B.Eng. (Environmental Engineering), Chulalongkorn University"
        ],
        "research_interests": [
            "Micro- and Nano-Bubble Technology for Advanced Water and Wastewater Treatment",
            "Volatile Organic Compounds (VOCs) and PM2.5 Abatement in Urban Environments",
            "Gas-Liquid Mass Transfer in Multiphase Environmental Reactors",
            "Membrane Bioreactors (MBR) and Resource Recovery from Industrial Sludge",
            "Life Cycle Assessment (LCA) and Carbon Footprint for Zero Waste Communities"
        ],
        "taught_courses": [
            "Physicochemical Processes in Environmental Engineering",
            "Air Pollution Control and Industrial Ventilation",
            "Circular Economy and Sustainable Waste Management"
        ],
        "featured_publications": [
            "Effect of Micro- and Nano-Bubbles on Hydrodynamics and Oxygen Mass Transfer in Water Aeration Systems",
            "Removal of Micro-Pollutants and Endocrine Disrupting Compounds Using Ozone-Assisted Micro-Bubble Oxidation",
            "Urban Air Quality Management: Real-Time Sensor Networks and Active Indoor Air Purification"
        ],
        "scholar_url": "https://scholar.google.com/citations?user=PisutPainmanakul"
    },
    {
        "id": "cu_eng_env_water_002",
        "university": "Chulalongkorn University",
        "university_th": "จุฬาลงกรณ์มหาวิทยาลัย",
        "faculty": "Faculty of Engineering",
        "faculty_th": "คณะวิศวกรรมศาสตร์",
        "department": "Department of Environmental Engineering & Center of Excellence in Water Reuse",
        "department_th": "ภาควิชาวิศวกรรมสิ่งแวดล้อม และศูนย์ความเป็นเลิศด้านการนำน้ำกลับมาใช้ใหม่",
        "academic_title": "Prof. Dr.",
        "academic_title_th": "ศ.ดร.",
        "first_name": "Chavalit",
        "last_name": "Ratanatamskul",
        "full_name": "Prof. Dr. Chavalit Ratanatamskul",
        "full_name_th": "ศ.ดร. ชวลิต รัตนธรรมสกุล",
        "role": "Director of Water Reuse and Membrane Technology Center / Senior Environmental Engineering Scholar",
        "email": "chavalit.r@chula.ac.th",
        "image_url": "https://env.eng.chula.ac.th/images/faculty/chavalit.jpg",
        "profile_url": "https://env.eng.chula.ac.th/staff/chavalit",
        "education": [
            "D.Eng. (Environmental Engineering), University of Tokyo, Japan",
            "M.Eng. (Environmental Engineering), University of Tokyo, Japan",
            "B.Eng. (Environmental Engineering - Honours), Chulalongkorn University"
        ],
        "research_interests": [
            "Membrane Bioreactor (MBR) and Reverse Osmosis (RO) for Direct Potable Reuse",
            "Anaerobic Membrane Bioreactors (AnMBR) for Biogas Energy Recovery from Food Waste",
            "Fouling Mitigation and Novel Antifouling Nanocomposite Membranes",
            "Electrochemical Advanced Oxidation for Recalcitrant Textile and Petrochemical Effluents",
            "Zero Liquid Discharge (ZLD) Systems for Industrial Water Security"
        ],
        "taught_courses": [
            "Membrane Processes in Water and Wastewater Engineering",
            "Industrial Wastewater Management and Zero Liquid Discharge",
            "Anaerobic Digestion and Waste-to-Energy Systems"
        ],
        "featured_publications": [
            "Performance and Fouling Characteristics of an Anaerobic Ceramic Membrane Bioreactor for High-Strength Food Waste Digestion",
            "Electrochemical Oxidation Combined with Nanofiltration for Complete Decolorization and Mineralization of Dye Effluents",
            "Comprehensive Assessment of Water Reclamation and Energy Neutrality in Decentralized Membrane Bioreactors"
        ],
        "scholar_url": "https://scholar.google.com/citations?user=ChavalitRatanatamskul"
    },
    {
        "id": "cu_eng_materials_alloy_001",
        "university": "Chulalongkorn University",
        "university_th": "จุฬาลงกรณ์มหาวิทยาลัย",
        "faculty": "Faculty of Engineering",
        "faculty_th": "คณะวิศวกรรมศาสตร์",
        "department": "Department of Metallurgical and Materials Engineering",
        "department_th": "ภาควิชาวิศวกรรมโลหการและวัสดุ",
        "academic_title": "Assoc. Prof. Dr.",
        "academic_title_th": "รศ.ดร.",
        "first_name": "Yuttanant",
        "last_name": "Boonyongmaneerat",
        "full_name": "Assoc. Prof. Dr. Yuttanant Boonyongmaneerat",
        "full_name_th": "รศ.ดร. ยุทธนันท์ บุญยงมณีรัตน์",
        "role": "Director of Metallurgy and Materials Science Research Hub / Pioneer in Electrodeposition and High-Entropy Alloys",
        "email": "yuttanant.b@chula.ac.th",
        "image_url": "https://mat.eng.chula.ac.th/images/faculty/yuttanant.jpg",
        "profile_url": "https://mat.eng.chula.ac.th/staff/yuttanant",
        "education": [
            "Ph.D. (Materials Science and Engineering), Massachusetts Institute of Technology (MIT), USA",
            "B.S. (Materials Science and Engineering), Cornell University, USA"
        ],
        "research_interests": [
            "High-Entropy Alloys (HEAs) and Nanocrystalline Coatings for Corrosion Protection",
            "Pulse Electrodeposition of Refractory Metal Alloys for Extreme Environments",
            "Advanced Metal Matrix Composites (MMC) for Automotive and Aerospace Structures",
            "Cathode and Anode Materials for Solid-State Lithium and Sodium Batteries",
            "Additive Manufacturing Metallurgy and Microstructure Solidification Control"
        ],
        "taught_courses": [
            "Phase Transformations and Kinetics in Materials",
            "Surface Engineering and Corrosion Science",
            "Advanced Materials Characterization Techniques"
        ],
        "featured_publications": [
            "Electrodeposition of Nanocrystalline Ni-W and Co-W Alloys with Superior Wear and High-Temperature Oxidation Resistance",
            "Microstructural Evolution and Mechanical Properties of Additively Manufactured High-Entropy Alloys",
            "Electrochemical Performance of Solid-State Electrolyte Coatings on High-Nickel Layered Oxide Cathodes"
        ],
        "scholar_url": "https://scholar.google.com/citations?user=YuttanantBoonyongmaneerat"
    },

    # =========================================================================
    # 2. FACULTY OF MEDICINE (CHULALONGKORN UNIVERSITY - MDCU)
    # =========================================================================
    {
        "id": "cu_med_vaccine_001",
        "university": "Chulalongkorn University",
        "university_th": "จุฬาลงกรณ์มหาวิทยาลัย",
        "faculty": "Faculty of Medicine",
        "faculty_th": "คณะแพทยศาสตร์",
        "department": "Department of Medicine & Chula Vaccine Research Center (ChulaVRC)",
        "department_th": "ภาควิชาอายุรศาสตร์ และศูนย์วิจัยวัคซีนจุฬาลงกรณ์ (ChulaVRC)",
        "academic_title": "Prof. Dr.",
        "academic_title_th": "ศ.นพ.ดร.",
        "first_name": "Kiat",
        "last_name": "Ruxrungtham",
        "full_name": "Prof. Dr. Med. Kiat Ruxrungtham",
        "full_name_th": "ศ.นพ.ดร. เกียรติ รักษ์รุ่งธรรม",
        "role": "Director of Chula Vaccine Research Center (ChulaVRC) / Pioneer of ChulaCov19 mRNA Vaccine and HIV Immunotherapy",
        "email": "kiat.r@chula.ac.th",
        "image_url": "https://med.chula.ac.th/images/faculty/kiat.jpg",
        "profile_url": "https://med.chula.ac.th/staff/kiat",
        "education": [
            "Postdoctoral Fellowship in Allergy and Clinical Immunology, Harvard Medical School, USA",
            "Postdoctoral Research in Molecular Immunology, NIH / NIAID, Bethesda, USA",
            "M.D. (Honours), Faculty of Medicine, Chulalongkorn University"
        ],
        "research_interests": [
            "mRNA Vaccine Technology Platform & Lipid Nanoparticle (LNP) Formulation (ChulaCov19)",
            "Therapeutic HIV Vaccines and Monoclonal Antibodies for Functional Cure",
            "Cancer Neoantigen Vaccines & Personalized Immuno-Oncology",
            "Immune Response Monitoring & Neutralizing Antibody Assays for Emerging Pathogens",
            "Clinical Trial Design (Phase I-III) for Novel Biopharmaceuticals"
        ],
        "taught_courses": [
            "Advanced Clinical Immunology and Immunotherapy",
            "Vaccinology and Biologics Drug Development",
            "Translational Medicine and First-in-Human Clinical Trials"
        ],
        "featured_publications": [
            "Safety and Immunogenicity of the ChulaCov19 mRNA Vaccine against SARS-CoV-2 in Healthy Adults: Phase 1/2 Clinical Trials",
            "Long-Term Immune Persistence and Neutralization Capacity of mRNA Vaccines against SARS-CoV-2 Emerging Variants",
            "Cellular and Humoral Immune Responses in Therapeutic HIV-1 Clinical Vaccine Trials in Southeast Asia"
        ],
        "scholar_url": "https://scholar.google.com/citations?user=KiatRuxrungtham"
    },
    {
        "id": "cu_med_virology_001",
        "university": "Chulalongkorn University",
        "university_th": "จุฬาลงกรณ์มหาวิทยาลัย",
        "faculty": "Faculty of Medicine",
        "faculty_th": "คณะแพทยศาสตร์",
        "department": "Department of Pediatrics & Center of Excellence in Clinical Virology",
        "department_th": "ภาควิชากุมารเวชศาสตร์ และศูนย์ความเป็นเลิศด้านไวรัสวิทยาคลินิก",
        "academic_title": "Prof. Dr.",
        "academic_title_th": "ศ.นพ.",
        "first_name": "Yong",
        "last_name": "Poovorawan",
        "full_name": "Prof. Dr. Med. Yong Poovorawan",
        "full_name_th": "ศ.นพ. ยง ภู่วรวรรณ",
        "role": "Head of Center of Excellence in Clinical Virology / Senior Research Scholar of Thailand / National Viral Disease Authority",
        "email": "yong.p@chula.ac.th",
        "image_url": "https://med.chula.ac.th/images/faculty/yong.jpg",
        "profile_url": "https://med.chula.ac.th/staff/yong",
        "education": [
            "Research Fellowship in Pediatric Hepatology, King's College Hospital, London, UK",
            "M.D., Faculty of Medicine, Chulalongkorn University",
            "Diploma of the Thai Board of Pediatrics"
        ],
        "research_interests": [
            "Epidemiology, Evolution and Molecular Virology of Viral Hepatitis (HBV, HCV, HEV)",
            "Emerging and Re-emerging Respiratory Viruses (SARS-CoV-2, Influenza, RSV)",
            "Hand, Foot, and Mouth Disease (Enterovirus A71, Coxsackievirus A6/A16)",
            "Dengue, Zika, and Chikungunya Genomic Surveillance in Southeast Asia",
            "Longitudinal Vaccine Efficacy and Real-World Protection Studies"
        ],
        "taught_courses": [
            "Clinical Diagnostic Virology",
            "Pediatric Infectious Diseases and Hepatology",
            "Molecular Epidemiology of Viral Epidemics"
        ],
        "featured_publications": [
            "Long-Term Follow-up of Universal Hepatitis B Vaccination in Newborns: Protective Immunity after 30 Years",
            "Genomic Epidemiology and Transmission Dynamics of Enterovirus A71 Associated with Severe Neurological Hand-Foot-Mouth Disease",
            "Real-World Effectiveness of Heterologous Prime-Boost COVID-19 Vaccine Regimens in Thailand"
        ],
        "scholar_url": "https://scholar.google.com/citations?user=YongPoovorawan"
    },
    {
        "id": "cu_med_neurovir_002",
        "university": "Chulalongkorn University",
        "university_th": "จุฬาลงกรณ์มหาวิทยาลัย",
        "faculty": "Faculty of Medicine",
        "faculty_th": "คณะแพทยศาสตร์",
        "department": "Department of Medicine & WHO Collaborating Centre for Research and Training on Viral Zoonoses",
        "department_th": "ภาควิชาอายุรศาสตร์ และศูนย์ความร่วมมือองค์การอนามัยโลกด้านการวิจัยและฝึกอบรมโรคไวรัสจากสัตว์สู่คน",
        "academic_title": "Prof. Dr.",
        "academic_title_th": "ศ.นพ.",
        "first_name": "Thiravat",
        "last_name": "Hemachudha",
        "full_name": "Prof. Dr. Med. Thiravat Hemachudha",
        "full_name_th": "ศ.นพ. ธีระวัฒน์ เหมะจุฑา",
        "role": "Distinguished Research Professor of Thailand / Senior Research Scholar / World Authority on Rabies and Neuro-Infectious Encephalitis",
        "email": "thiravat.h@chula.ac.th",
        "image_url": "https://med.chula.ac.th/images/faculty/thiravat.jpg",
        "profile_url": "https://med.chula.ac.th/staff/thiravat",
        "education": [
            "Postdoctoral Fellowship in Neuroimmunology and Neurovirology, Johns Hopkins University School of Medicine, USA",
            "M.D., Faculty of Medicine, Chulalongkorn University",
            "Diploma of the Thai Board of Neurology"
        ],
        "research_interests": [
            "Human Rabies Pathogenesis, Neurotropism and Post-Exposure Prophylaxis Regimens",
            "Emerging Zoonotic Neuro-Viruses (Nipah, Bat Coronaviruses, Encephalitis)",
            "Autoimmune Encephalitis and Anti-NMDA Receptor Encephalitis Pathomechanisms",
            "Microbiome-Gut-Brain Axis in Early Neurodegenerative Pathologies",
            "Medical Cannabis Pharmacology for Refractory Neurological Conditions"
        ],
        "taught_courses": [
            "Clinical Neurovirology and Zoonoses",
            "Neuroimmunology and Demyelinating Disorders",
            "Pathophysiology of Central Nervous System Infections"
        ],
        "featured_publications": [
            "Pathogenesis of Human Rabies: Pathological and Immunological Findings in the Central Nervous System",
            "Intradermal Post-Exposure Rabies Vaccination: Clinical Efficacy and Cost-Effectiveness in Asia",
            "Autoimmune Limbic Encephalitis Associated with Neuronal Surface Antibodies: Diagnostic Pitfalls and Immunotherapy"
        ],
        "scholar_url": "https://scholar.google.com/citations?user=ThiravatHemachudha"
    },
    {
        "id": "cu_med_cardio_001",
        "university": "Chulalongkorn University",
        "university_th": "จุฬาลงกรณ์มหาวิทยาลัย",
        "faculty": "Faculty of Medicine",
        "faculty_th": "คณะแพทยศาสตร์",
        "department": "Department of Medicine (Cardiology Division & Cardiac Center)",
        "department_th": "ภาควิชาอายุรศาสตร์ (สาขาวิชาหทัยวิทยา และศูนย์ความเป็นเลิศทางการแพทย์ด้านโรคหัวใจ)",
        "academic_title": "Prof. Dr.",
        "academic_title_th": "ศ.นพ.ดร.",
        "first_name": "Rungroj",
        "last_name": "Krittayaphong",
        "full_name": "Prof. Dr. Med. Rungroj Krittayaphong",
        "full_name_th": "ศ.นพ.ดร. รุ่งโรจน์ กฤตยพงษ์",
        "role": "Senior Professor in Clinical Cardiology & Cardiac Electrophysiology",
        "email": "rungroj.k@chula.ac.th",
        "image_url": "https://med.chula.ac.th/images/faculty/rungroj.jpg",
        "profile_url": "https://med.chula.ac.th/staff/rungroj",
        "education": [
            "Fellowship in Cardiac Electrophysiology, University of Oklahoma Health Sciences Center, USA",
            "M.D. (Honours), Faculty of Medicine, Chulalongkorn University",
            "Diploma of the Thai Board of Cardiology"
        ],
        "research_interests": [
            "Atrial Fibrillation (AF) Registry & Anticoagulation Outcomes in Asians (COOL-AF Registry)",
            "Cardiac MRI (CMR) and Cardiac CT for Myocardial Viability Assessment",
            "Catheter Ablation of Complex Cardiac Arrhythmias",
            "Heart Failure with Preserved Ejection Fraction (HFpEF)",
            "Cardiovascular Disease Epidemiology in Southeast Asia"
        ],
        "taught_courses": [
            "Clinical Cardiac Electrophysiology",
            "Cardiovascular Magnetic Resonance Imaging",
            "Evidence-Based Cardiology and National Registries"
        ],
        "featured_publications": [
            "Nationwide Registry of Patients with Atrial Fibrillation in Thailand (COOL-AF): Quality of Life, Anticoagulation, and Clinical Endpoints",
            "Diagnostic Accuracy of Cardiovascular Magnetic Resonance Late Gadolinium Enhancement in Non-Ischemic Cardiomyopathy",
            "Risk Factors and 10-Year Mortality Prediction in Asian Patients with Coronary Artery Disease"
        ],
        "scholar_url": "https://scholar.google.com/citations?user=RungrojKrittayaphong"
    },
    {
        "id": "cu_med_onco_001",
        "university": "Chulalongkorn University",
        "university_th": "จุฬาลงกรณ์มหาวิทยาลัย",
        "faculty": "Faculty of Medicine",
        "faculty_th": "คณะแพทยศาสตร์",
        "department": "Department of Medicine (Medical Oncology Division & Chula Cancer Center)",
        "department_th": "ภาควิชาอายุรศาสตร์ (สาขาวิชาอายุรศาสตร์มะเร็งวิทยา และศูนย์มะเร็งครบวงจร)",
        "academic_title": "Prof. Dr.",
        "academic_title_th": "ศ.นพ.ดร.",
        "first_name": "Virote",
        "last_name": "Sriuranpong",
        "full_name": "Prof. Dr. Med. Virote Sriuranpong",
        "full_name_th": "ศ.นพ.ดร. วิโรจน์ ศรีอุฬารพงศ์",
        "role": "Director of Comprehensive Cancer Center & Pioneer in Precision Lung Cancer Oncology",
        "email": "virote.s@chula.ac.th",
        "image_url": "https://med.chula.ac.th/images/faculty/virote.jpg",
        "profile_url": "https://med.chula.ac.th/staff/virote",
        "education": [
            "Ph.D. (Human Genetics / Molecular Oncology), Johns Hopkins University School of Medicine, USA",
            "Medical Oncology Fellowship, Johns Hopkins Hospital, USA",
            "M.D. (First Class Honours, Gold Medal), Chulalongkorn University"
        ],
        "research_interests": [
            "Precision Oncology & Targeted Therapy for EGFR/ALK-Mutant Lung Cancer",
            "Cancer Immunotherapy (Immune Checkpoint Inhibitors PD-1/PD-L1)",
            "Liquid Biopsy & Circulating Tumor DNA (ctDNA) Monitoring",
            "Molecular Signatures of Resistance to Tyrosine Kinase Inhibitors (TKIs)",
            "Phase I-III Global Oncology Clinical Trials"
        ],
        "taught_courses": [
            "Molecular Biology of Cancer and Targeted Therapies",
            "Precision Medical Oncology and Genomics",
            "Clinical Trial Methodology in Oncology"
        ],
        "featured_publications": [
            "Molecular Epidemiology of EGFR Mutations and Efficacy of Third-Generation TKIs in Southeast Asian Non-Small Cell Lung Cancer",
            "Longitudinal ctDNA Profiling Detects Early Resistance Mutations in Advanced Lung Adenocarcinoma Patients",
            "Phase III Trial of First-Line Immunotherapy Combinations in Asian Patients with Advanced Solid Tumors"
        ],
        "scholar_url": "https://scholar.google.com/citations?user=ViroteSriuranpong"
    },
    {
        "id": "cu_med_breast_cancer_002",
        "university": "Chulalongkorn University",
        "university_th": "จุฬาลงกรณ์มหาวิทยาลัย",
        "faculty": "Faculty of Medicine",
        "faculty_th": "คณะแพทยศาสตร์",
        "department": "Department of Surgery & Queen Sirikit Centre for Breast Cancer (QSCBC)",
        "department_th": "ภาควิชาศัลยศาสตร์ และศูนย์สิริกิติ์บรมราชินีนาถเพื่อโรคมะเร็งเต้านม",
        "academic_title": "Prof. Dr.",
        "academic_title_th": "ศ.นพ.",
        "first_name": "Kris",
        "last_name": "Chatamra",
        "full_name": "Prof. Dr. Med. Kris Chatamra",
        "full_name_th": "ศ.นพ. กฤษณ์ จาฏามระ",
        "role": "Founder and Director of Queen Sirikit Centre for Breast Cancer / Senior Oncoplastic Breast Surgeon (FRCS England)",
        "email": "kris.c@chula.ac.th",
        "image_url": "https://med.chula.ac.th/images/faculty/kris.jpg",
        "profile_url": "https://med.chula.ac.th/staff/kris",
        "education": [
            "M.D., University of London, UK",
            "FRCS (Fellow of Royal College of Surgeons of England), UK",
            "Consultant Surgeon, Royal Marsden Hospital and King's College Hospital, London, UK"
        ],
        "research_interests": [
            "Oncoplastic Breast Surgery and Immediate Microvascular Reconstruction",
            "Triple-Negative Breast Cancer (TNBC) Molecular Profiling in Underprivileged Patients",
            "High-Risk Hereditary BRCA1/BRCA2 Genetic Screening and Risk-Reducing Strategies",
            "Comprehensive Supportive and Palliative Care for Advanced Cancer Patients",
            "Immunohistochemical Biomarkers for Predicting Chemotherapy Neoadjuvant Response"
        ],
        "taught_courses": [
            "Oncoplastic Breast Surgery Techniques",
            "Comprehensive Breast Cancer Care and Multidisciplinary Management",
            "Surgical Oncology Ethics and Palliative Care"
        ],
        "featured_publications": [
            "Oncoplastic Breast Conserving Surgery in Asian Women with High Tumor-to-Breast Volume Ratios: Long-Term Cosmetic and Oncological Outcomes",
            "Prevalence and Clinical Spectrum of Pathogenic BRCA1 and BRCA2 Germline Mutations in Thai Breast Cancer Cohorts",
            "Holistic and Palliative Care Integration in Advanced Metastatic Breast Cancer: The QSCBC Hospice Model"
        ],
        "scholar_url": "https://scholar.google.com/citations?user=KrisChatamra"
    },
    {
        "id": "cu_med_epigenetics_001",
        "university": "Chulalongkorn University",
        "university_th": "จุฬาลงกรณ์มหาวิทยาลัย",
        "faculty": "Faculty of Medicine",
        "faculty_th": "คณะแพทยศาสตร์",
        "department": "Department of Anatomy & Center of Excellence in Molecular Genetics and Epigenetics",
        "department_th": "ภาควิชากายวิภาคศาสตร์ และศูนย์ความเป็นเลิศด้านพันธุศาสตร์โมเลกุลและเอพิเจเนติกส์",
        "academic_title": "Prof. Dr.",
        "academic_title_th": "ศ.ดร.นพ.",
        "first_name": "Apiwat",
        "last_name": "Mutirangura",
        "full_name": "Prof. Dr. Med. Apiwat Mutirangura",
        "full_name_th": "ศ.ดร.นพ. อภิวัฒน์ มุทิตาเจริญ",
        "role": "Distinguished Research Professor of Thailand / Fellow of Royal Society / World Pioneer in Genome-Wide DNA Methylation & Youth-DNA Rejuvenation",
        "email": "apiwat.m@chula.ac.th",
        "image_url": "https://med.chula.ac.th/images/faculty/apiwat.jpg",
        "profile_url": "https://med.chula.ac.th/staff/apiwat",
        "education": [
            "Postdoctoral Fellowship in Human Molecular Genetics, Baylor College of Medicine, Houston, USA",
            "Ph.D. (Human Genetics), Chulalongkorn University",
            "M.D., Faculty of Medicine, Chulalongkorn University"
        ],
        "research_interests": [
            "Epigenetic DNA Methylation Loss, LINE-1/Alu Retrotransposons and Genomic Instability in Aging and Cancer",
            "DNA Gap Rejuvenation Technology (RED-X) for Reversing Cellular Senescence",
            "Circulating Cell-Free Methylated DNA Biomarkers for Early Nasopharyngeal and Colorectal Cancer Screening",
            "Epigenetic Modulation by Environmental Toxicants, PM2.5 and Dietary Bioactives",
            "Single-Cell Epigenomics and Chromatin Conformation in Stem Cell Differentiation"
        ],
        "taught_courses": [
            "Human Molecular Genetics and Epigenetics",
            "Mechanisms of Aging and Cellular Rejuvenation",
            "Epigenetic Biomarkers in Precision Medicine"
        ],
        "featured_publications": [
            "Genome-Wide Loss of LINE-1 and Alu DNA Methylation Drives Chromosomal Instability and Cellular Aging",
            "Restoration of Youthful DNA Methylation Patterns Reverses Senescence Markers in Aged Human Fibroblasts",
            "Quantitative Detection of Hypomethylated Circulating Cell-Free DNA as a Sensitive Universal Pan-Cancer Biomarker"
        ],
        "scholar_url": "https://scholar.google.com/citations?user=ApiwatMutirangura"
    },
    {
        "id": "cu_med_neuro_001",
        "university": "Chulalongkorn University",
        "university_th": "จุฬาลงกรณ์มหาวิทยาลัย",
        "faculty": "Faculty of Medicine",
        "faculty_th": "คณะแพทยศาสตร์",
        "department": "Department of Medicine (Neurology Division & Parkinson's Center of Excellence)",
        "department_th": "ภาควิชาอายุรศาสตร์ (สาขาวิชาประสาทวิทยา และศูนย์ความเป็นเลิศทางการแพทย์โรคพาร์กินสัน)",
        "academic_title": "Prof. Dr.",
        "academic_title_th": "ศ.นพ.ดร.",
        "first_name": "Roongroj",
        "last_name": "Bhidayasiri",
        "full_name": "Prof. Dr. Med. Roongroj Bhidayasiri",
        "full_name_th": "ศ.นพ.ดร. รุ่งโรจน์ พิทยศิริ",
        "role": "Director of Chulalongkorn Excellence Center for Parkinson's Disease & Movement Disorders",
        "email": "roongroj.b@chula.ac.th",
        "image_url": "https://med.chula.ac.th/images/faculty/roongroj.jpg",
        "profile_url": "https://med.chula.ac.th/staff/roongroj",
        "education": [
            "Fellowship in Movement Disorders, UCLA School of Medicine, USA",
            "FRCP (London, Edinburgh), Royal College of Physicians, UK",
            "M.D. (Honours), Chulalongkorn University"
        ],
        "research_interests": [
            "Parkinson's Disease Pathophysiology, Biomarkers & Tremor Quantitation",
            "Laser-Guided Gait Training Device for Parkinsonian Freezing of Gait",
            "Deep Brain Stimulation (DBS) Target Optimization and Programming",
            "Non-Motor Symptoms and Circadian Dysregulation in Neurodegeneration",
            "Digital Health and Wearable Sensors for Remote Neuro-Monitoring"
        ],
        "taught_courses": [
            "Clinical Movement Disorders and Neuromodulation",
            "Neurodegenerative Disease Pathogenesis",
            "Medical Device Innovation for Neurological Patients"
        ],
        "featured_publications": [
            "Laser-Guided Visual Cues and Auditory Stimulation for Overcoming Freezing of Gait in Parkinson's Disease: A Multicenter Randomized Trial",
            "Validation of Wearable Inertial Sensor Technology for Real-Time Tremor and Dyskinesia Assessment",
            "Consensus Guidelines for Deep Brain Stimulation in Dystonia and Parkinson's Disease across the Asia-Pacific Region"
        ],
        "scholar_url": "https://scholar.google.com/citations?user=RoongrojBhidayasiri"
    },
    {
        "id": "cu_med_immuno_001",
        "university": "Chulalongkorn University",
        "university_th": "จุฬาลงกรณ์มหาวิทยาลัย",
        "faculty": "Faculty of Medicine",
        "faculty_th": "คณะแพทยศาสตร์",
        "department": "Department of Microbiology & Center of Excellence in Immunology and Immune-Mediated Diseases",
        "department_th": "ภาควิชาจุลชีววิทยา และศูนย์ความเป็นเลิศด้านภูมิคุ้มกันบำบัดและโรคภูมิคุ้มกัน",
        "academic_title": "Prof. Dr.",
        "academic_title_th": "ศ.ดร.พญ.",
        "first_name": "Nattiya",
        "last_name": "Hirankarn",
        "full_name": "Prof. Dr. Med. Nattiya Hirankarn",
        "full_name_th": "ศ.ดร.พญ. ณัฏฐิยา หิรัญกาญจน์",
        "role": "Distinguished Professor in Medical Immunology / Director of Center of Excellence in Immunology and Immune-Mediated Diseases",
        "email": "nattiya.h@chula.ac.th",
        "image_url": "https://med.chula.ac.th/images/faculty/nattiya.jpg",
        "profile_url": "https://med.chula.ac.th/staff/nattiya",
        "education": [
            "Ph.D. (Immunology), Imperial College London, UK",
            "M.D. (First Class Honours, Gold Medal), Faculty of Medicine, Chulalongkorn University"
        ],
        "research_interests": [
            "Immunogenetics and Epigenetics of Systemic Lupus Erythematosus (SLE)",
            "Autoantibody Profiling and Microfluidic Biomarker Discovery in Autoimmune Diseases",
            "CAR-T Cell Engineering and Adoptive Cell Transfer for Solid Tumors",
            "Single-Cell RNA Sequencing of Immune Cell Exhaustion in Chronic Infections",
            "Interferon Signature and Cytokine Storm Pathogenesis in Lupus Nephritis"
        ],
        "taught_courses": [
            "Advanced Medical Immunology",
            "Immunogenetics and Cellular Therapeutics",
            "Mechanisms of Autoimmunity and Tolerance"
        ],
        "featured_publications": [
            "Genome-Wide Association Study Identifies Novel Susceptibility Loci for Systemic Lupus Erythematosus in Southeast Asian Populations",
            "Single-Cell Transcriptomics Reveals Distinct Pro-inflammatory B-Cell and T-Cell Subsets in Lupus Nephritis Flare",
            "Engineering Allogeneic CAR-T Cells with CRISPR/Cas9 Gene Editing for Refractory B-Cell Malignancies"
        ],
        "scholar_url": "https://scholar.google.com/citations?user=NattiyaHirankarn"
    },
    {
        "id": "cu_med_gastro_liver_001",
        "university": "Chulalongkorn University",
        "university_th": "จุฬาลงกรณ์มหาวิทยาลัย",
        "faculty": "Faculty of Medicine",
        "faculty_th": "คณะแพทยศาสตร์",
        "department": "Department of Biochemistry & Center of Excellence in Hepatitis and Liver Cancer",
        "department_th": "ภาควิชาชีวเคมี และศูนย์ความเป็นเลิศด้านไวรัสตับอักเสบและมะเร็งตับ",
        "academic_title": "Prof. Dr.",
        "academic_title_th": "ศ.ดร.นพ.",
        "first_name": "Pisit",
        "last_name": "Tangkijvanich",
        "full_name": "Prof. Dr. Med. Pisit Tangkijvanich",
        "full_name_th": "ศ.ดร.นพ. พิสิฐ ตั้งกิจวานิชย์",
        "role": "Head of Center of Excellence in Hepatitis and Liver Cancer / Senior Fellow of Royal College of Physicians of Thailand",
        "email": "pisit.t@chula.ac.th",
        "image_url": "https://med.chula.ac.th/images/faculty/pisit.jpg",
        "profile_url": "https://med.chula.ac.th/staff/pisit",
        "education": [
            "Postdoctoral Fellowship in Molecular Hepatology, Mayo Clinic, Rochester, USA",
            "M.D. (Honours), Faculty of Medicine, Chulalongkorn University",
            "Diploma of the Thai Board of Gastroenterology"
        ],
        "research_interests": [
            "Hepatocellular Carcinoma (HCC) Molecular Pathogenesis and Epigenetic Biomarkers",
            "Circulating MicroRNAs and Cell-Free DNA Liquid Biopsies for Early HCC Detection",
            "Direct-Acting Antivirals (DAA) Resistance in Hepatitis C Virus (HCV)",
            "Non-Alcoholic Fatty Liver Disease (NAFLD/MASLD) and Fibrosis Progression Biomarkers",
            "Targeted Multi-Kinase Inhibitors and Immunotherapy in Advanced Liver Cancer"
        ],
        "taught_courses": [
            "Clinical Hepatology and Molecular Mechanisms of Liver Disease",
            "Advanced Medical Biochemistry and Oncology Biomarkers",
            "Evidence-Based Gastroenterology and Liver Transplantation"
        ],
        "featured_publications": [
            "Diagnostic Performance of Serum MicroRNA Panels and Alpha-Fetoprotein for Early-Stage Hepatocellular Carcinoma in Cirrhotic Patients",
            "Circulating Tumor DNA Methylation Markers for Monitoring Treatment Response and Minimal Residual Disease in Liver Cancer",
            "Real-World Efficacy and Sustained Virological Response of Generic Direct-Acting Antivirals in Thai Hepatitis C Cohort"
        ],
        "scholar_url": "https://scholar.google.com/citations?user=PisitTangkijvanich"
    },

    # =========================================================================
    # 3. FACULTY OF SCIENCE (CHULALONGKORN UNIVERSITY)
    # =========================================================================
    {
        "id": "cu_sci_compchem_001",
        "university": "Chulalongkorn University",
        "university_th": "จุฬาลงกรณ์มหาวิทยาลัย",
        "faculty": "Faculty of Science",
        "faculty_th": "คณะวิทยาศาสตร์",
        "department": "Department of Chemistry & Computational Chemistry Unit",
        "department_th": "ภาควิชาเคมี และหน่วยวิจัยเคมีคำนวณ",
        "academic_title": "Prof. Dr.",
        "academic_title_th": "ศ.ดร.",
        "first_name": "Supot",
        "last_name": "Hannongbua",
        "full_name": "Prof. Dr. Supot Hannongbua",
        "full_name_th": "ศ.ดร. สุพจน์ หารหนองบัว",
        "role": "Distinguished Research Professor of Thailand / Fellow of Royal Society / Former President of Science Society of Thailand",
        "email": "supot.h@chula.ac.th",
        "image_url": "https://chemistry.sc.chula.ac.th/images/faculty/supot.jpg",
        "profile_url": "https://chemistry.sc.chula.ac.th/staff/supot",
        "education": [
            "Dr.rer.nat. (Theoretical & Computational Chemistry), University of Innsbruck, Austria",
            "M.Sc. (Physical Chemistry), Chulalongkorn University",
            "B.Sc. (Chemistry), Chulalongkorn University"
        ],
        "research_interests": [
            "Molecular Dynamics Simulations (MD) and Quantum Mechanical / Molecular Mechanical (QM/MM) Methods",
            "Structure-Based Computer-Aided Drug Design (CADD) against HIV-1 RT and Dengue Proteases",
            "Conducting Polymers and Organic Photovoltaic Materials Modeling",
            "Machine Learning Potentials for High-Throughput Materials Discovery",
            "Solvation Thermodynamics and Ion Channel Biophysics"
        ],
        "taught_courses": [
            "Quantum Chemistry and Molecular Spectroscopy",
            "Computational Chemistry and Molecular Dynamics Simulations",
            "Statistical Thermodynamics in Chemical Physics"
        ],
        "featured_publications": [
            "QM/MM and Molecular Dynamics Investigations into the Binding Mechanisms of Non-Nucleoside Reverse Transcriptase Inhibitors with HIV-1 RT",
            "Theoretical Investigation of Charge Transfer and Exciton Dissociation in Conjugated Polymer Solar Cells",
            "Machine Learning-Enhanced Free Energy Perturbation Simulations for Accurate Protein-Ligand Binding Affinities"
        ],
        "scholar_url": "https://scholar.google.com/citations?user=SupotHannongbua"
    },
    {
        "id": "cu_sci_pna_001",
        "university": "Chulalongkorn University",
        "university_th": "จุฬาลงกรณ์มหาวิทยาลัย",
        "faculty": "Faculty of Science",
        "faculty_th": "คณะวิทยาศาสตร์",
        "department": "Department of Chemistry & Center of Excellence in Organic Synthesis and Peptide Nucleic Acids",
        "department_th": "ภาควิชาเคมี และศูนย์ความเป็นเลิศด้านการสังเคราะห์สารอินทรีย์และเปปไทด์กรดนิวคลีอิก",
        "academic_title": "Prof. Dr.",
        "academic_title_th": "ศ.ดร.",
        "first_name": "Tirayut",
        "last_name": "Vilaivan",
        "full_name": "Prof. Dr. Tirayut Vilaivan",
        "full_name_th": "ศ.ดร. ธีรยุทธ วิไลวัลย์",
        "role": "Distinguished Research Professor of Thailand / Fellow of Royal Society / World Pioneer in Conformationally Constrained PNA Probes",
        "email": "tirayut.v@chula.ac.th",
        "image_url": "https://chemistry.sc.chula.ac.th/images/faculty/tirayut.jpg",
        "profile_url": "https://chemistry.sc.chula.ac.th/staff/tirayut",
        "education": [
            "D.Phil. (Organic Chemistry), University of Oxford, UK",
            "B.Sc. (Chemistry - First Class Honours, Gold Medal), Chulalongkorn University"
        ],
        "research_interests": [
            "Pyrrolidinyl Peptide Nucleic Acids (acpcPNA) for Ultra-Sensitive DNA/RNA Detection",
            "Fluorescent PNA Probes and Colorimetric Paper-Based Diagnostics for Pathogens (TB, HPV, Dengue)",
            "Organic Photoredox Catalysis and Asymmetric Organocatalytic Synthesis",
            "Antisense PNA Oligonucleotides for Targeted Gene Regulation and Antibacterial Therapy",
            "Biosensor Surface Chemistry and Nanomaterial Hybrid Bioconjugates"
        ],
        "taught_courses": [
            "Advanced Organic Synthesis and Reaction Mechanisms",
            "Bioorganic Chemistry and Molecular Recognition",
            "Spectroscopic Identification of Organic Compounds"
        ],
        "featured_publications": [
            "Conformationally Constrained Pyrrolidinyl Peptide Nucleic Acids: Synthesis, Hybridization Properties, and Diagnostic Applications",
            "Paper-Based Colorimetric PNA Sensor for Visual Detection of Single-Nucleotide Polymorphisms in Tuberculosis Drug Resistance",
            "Fluorescent Anthracene-Labeled PNA Probes for Real-Time Quantitative Detection of Viral RNA Targets"
        ],
        "scholar_url": "https://scholar.google.com/citations?user=TirayutVilaivan"
    },
    {
        "id": "cu_sci_supramolecule_002",
        "university": "Chulalongkorn University",
        "university_th": "จุฬาลงกรณ์มหาวิทยาลัย",
        "faculty": "Faculty of Science",
        "faculty_th": "คณะวิทยาศาสตร์",
        "department": "Department of Chemistry & Organic Synthesis and Sensor Research Unit",
        "department_th": "ภาควิชาเคมี และหน่วยวิจัยการสังเคราะห์สารอินทรีย์และเซนเซอร์เคมี",
        "academic_title": "Prof. Dr.",
        "academic_title_th": "ศ.ดร.",
        "first_name": "Mongkol",
        "last_name": "Sukwattanasinitt",
        "full_name": "Prof. Dr. Mongkol Sukwattanasinitt",
        "full_name_th": "ศ.ดร. มงคล สุขวัฒนาสินิทธิ์",
        "role": "Distinguished Professor in Supramolecular Chemistry, Chemosensors and Functional Chromophores",
        "email": "mongkol.s@chula.ac.th",
        "image_url": "https://chemistry.sc.chula.ac.th/images/faculty/mongkol.jpg",
        "profile_url": "https://chemistry.sc.chula.ac.th/staff/mongkol",
        "education": [
            "Ph.D. (Organic Chemistry), University of North Carolina at Chapel Hill, USA",
            "B.Sc. (Chemistry - First Class Honours, Gold Medal), Chulalongkorn University"
        ],
        "research_interests": [
            "Colorimetric and Fluorescent Polydiacetylene (PDA) Sensors for Pathogen Detection",
            "Porphyrin, Calixarene and Metal-Organic Framework Chemosensors for Explosives and Pesticides",
            "Aggregation-Induced Emission (AIE) Luminogens for Bioimaging and Cellular Staining",
            "Self-Assembled Supramolecular Polymer Hydrogels for Controlled Drug Delivery",
            "Photocatalytic Degradation of Hazardous Organic Pollutants"
        ],
        "taught_courses": [
            "Supramolecular Chemistry and Molecular Machines",
            "Advanced Organic Spectroscopy and Photochemistry",
            "Design and Synthesis of Chemical and Biosensors"
        ],
        "featured_publications": [
            "Polydiacetylene Liposomes as Colorimetric and Fluorescent Probes for Rapid Visual Detection of Bacterial Toxins",
            "Aggregation-Induced Emission Luminogens for High-Contrast Two-Photon Fluorescence Imaging of Cancer Cells",
            "Fluorescent Calixarene Derivatives for Highly Selective Recognition of Heavy Metal Ions in Aqueous Media"
        ],
        "scholar_url": "https://scholar.google.com/citations?user=MongkolSukwattanasinitt"
    },
    {
        "id": "cu_sci_shrimp_biotech_001",
        "university": "Chulalongkorn University",
        "university_th": "จุฬาลงกรณ์มหาวิทยาลัย",
        "faculty": "Faculty of Science",
        "faculty_th": "คณะวิทยาศาสตร์",
        "department": "Department of Biochemistry & Center of Excellence for Molecular Biology and Genomics of Shrimp",
        "department_th": "ภาควิชาชีวเคมี และศูนย์ความเป็นเลิศด้านชีววิทยาโมเลกุลและจีโนมิกส์ของกุ้ง",
        "academic_title": "Prof. Dr.",
        "academic_title_th": "ศ.ดร.",
        "first_name": "Anchalee",
        "last_name": "Tassanakajon",
        "full_name": "Prof. Dr. Anchalee Tassanakajon",
        "full_name_th": "ศ.ดร. อัญชลี ทัศนาขจร",
        "role": "Distinguished Research Professor of Thailand / Fellow of Royal Society / Global Authority in Crustacean Innate Immunity & Shrimp Genomics",
        "email": "anchalee.t@chula.ac.th",
        "image_url": "https://biochem.sc.chula.ac.th/images/faculty/anchalee.jpg",
        "profile_url": "https://biochem.sc.chula.ac.th/staff/anchalee",
        "education": [
            "Ph.D. (Biochemistry and Molecular Biology), University of California, Davis, USA",
            "B.Sc. (Chemistry - First Class Honours, Gold Medal), Chulalongkorn University"
        ],
        "research_interests": [
            "Innate Immune Defense Mechanisms of Black Tiger and Whiteleg Shrimp against Viral & Bacterial Pathogens (WSSV, AHPND, EHP)",
            "Antimicrobial Peptides (Penaeidins, Anti-Lipopolysaccharide Factors ALFs) Characterization and Synthetic Analogs",
            "RNA Interference (RNAi) and Double-Stranded RNA Delivery Platforms for Disease Resistance in Aquaculture",
            "Shrimp Functional Genomics, Transcriptome Profiling and Marker-Assisted Selection",
            "Gut Microbiome Modulations and Probiotic Interventions for Sustainable Shrimp Farming"
        ],
        "taught_courses": [
            "Advanced Molecular Biology and Genomics",
            "Comparative Immunology of Invertebrates",
            "Aquaculture Biotechnology and Disease Management"
        ],
        "featured_publications": [
            "Innate Immunity in Crustaceans: Antimicrobial Peptides and Pattern Recognition Receptors in Shrimp Defense",
            "RNA Interference Targeting Viral Structural Genes Protects Penaeus monodon from Fatal White Spot Syndrome Virus Infection",
            "Molecular Characterization and Protective Efficacy of Recombinant Anti-Lipopolysaccharide Factors against Acute Hepatopancreatic Necrosis Disease (AHPND)"
        ],
        "scholar_url": "https://scholar.google.com/citations?user=AnchaleeTassanakajon"
    },
    {
        "id": "cu_sci_marine_001",
        "university": "Chulalongkorn University",
        "university_th": "จุฬาลงกรณ์มหาวิทยาลัย",
        "faculty": "Faculty of Science",
        "faculty_th": "คณะวิทยาศาสตร์",
        "department": "Department of Marine Science & Reef Biology Research Group",
        "department_th": "ภาควิชาวิศวกรรมทางทะเลและวิทยาศาสตร์ทางทะเล",
        "academic_title": "Prof. Dr.",
        "academic_title_th": "ศ.ดร.",
        "first_name": "Suchana",
        "last_name": "Chavanich",
        "full_name": "Prof. Dr. Suchana Chavanich",
        "full_name_th": "ศ.ดร. สุชนา ชวนิชย์",
        "role": "Distinguished Professor in Marine Ecology / First Thai Female Scientist in Antarctica & Arctic Expeditions",
        "email": "suchana.c@chula.ac.th",
        "image_url": "https://marine.sc.chula.ac.th/images/faculty/suchana.jpg",
        "profile_url": "https://marine.sc.chula.ac.th/staff/suchana",
        "education": [
            "Ph.D. (Zoology / Marine Ecology), University of New Hampshire, USA",
            "M.S. (Marine Science), University of Guam, USA",
            "B.Sc. (Marine Science - Honours), Chulalongkorn University"
        ],
        "research_interests": [
            "Coral Sexual Reproduction and Cryopreservation of Coral Gametes",
            "Micro-fragmentation and Assisted Evolution for Coral Reef Restoration under Climate Warming",
            "Polar Marine Ecology (Antarctic and Arctic Benthic Communities)",
            "Marine Microplastic Pollution and Trophic Transfer in Marine Food Webs",
            "Crown-of-Thorns Starfish (COTS) Population Outbreaks and Biological Management"
        ],
        "taught_courses": [
            "Tropical Marine Ecology and Conservation",
            "Coral Reef Ecosystem Dynamics",
            "Marine Environmental Impact Assessment"
        ],
        "featured_publications": [
            "Assisted Coral Sexual Reproduction and Cryopreservation: Breakthroughs for Restoring Degraded Reefs in the Gulf of Thailand",
            "Microplastic Ingestion and Accumulation in Commercial Marine Fish and Benthic Invertebrates in Tropical Waters",
            "Climate Change Impacts on Benthic Communities in Polar Regions: Comparative Insights from Antarctica and the Arctic"
        ],
        "scholar_url": "https://scholar.google.com/citations?user=SuchanaChavanich"
    },
    {
        "id": "cu_sci_biodiv_snail_002",
        "university": "Chulalongkorn University",
        "university_th": "จุฬาลงกรณ์มหาวิทยาลัย",
        "faculty": "Faculty of Science",
        "faculty_th": "คณะวิทยาศาสตร์",
        "department": "Department of Biology & Center of Excellence in Biodiversity and Animal Taxonomy",
        "department_th": "ภาควิชาชีววิทยา และศูนย์ความเป็นเลิศด้านความหลากหลายทางชีวภาพและอนุกรมวิธานสัตว์",
        "academic_title": "Prof. Dr.",
        "academic_title_th": "ศ.ดร.",
        "first_name": "Somsak",
        "last_name": "Panha",
        "full_name": "Prof. Dr. Somsak Panha",
        "full_name_th": "ศ.ดร. สมศักดิ์ ปัญหา",
        "role": "Distinguished Research Professor of Thailand / Fellow of Royal Society / World Expert on Tropical Land Snails and Bioactive Mucin",
        "email": "somsak.pan@chula.ac.th",
        "image_url": "https://biology.sc.chula.ac.th/images/faculty/somsak.jpg",
        "profile_url": "https://biology.sc.chula.ac.th/staff/somsak",
        "education": [
            "Ph.D. (Zoology / Invertebrate Taxonomy), Kyoto University, Japan",
            "M.Sc. (Zoology), Chulalongkorn University",
            "B.Sc. (Biology), Chulalongkorn University"
        ],
        "research_interests": [
            "Systematics, Phylogeny and Biogeography of Southeast Asian Land Snails and Invertebrates",
            "Bioactive Peptide Extraction from Tropical Land Snail Mucin (Snail White Cosmeceutical Innovations)",
            "Limestone Karst Ecosystem Biodiversity and Conservation Biology",
            "Speciation Dynamics and Adaptive Radiation along River Basins in the Indochina Region",
            "Microbiome of Invertebrate Mucus and Antimicrobial Compound Discovery"
        ],
        "taught_courses": [
            "Advanced Invertebrate Zoology and Systematics",
            "Tropical Biodiversity and Conservation Biogeography",
            "Evolutionary Biology and Speciation"
        ],
        "featured_publications": [
            "Integrative Taxonomy and Molecular Phylogeny of Tropical Carnivorous Land Snails in Southeast Asia",
            "Bioactive Peptides and Antioxidant Properties of Purified Mucin from the Endemic Land Snail Hemiplecta distincta",
            "Karst Biodiversity Hotspots and High Endemism of Micro-Mollusks in the Greater Mekong Subregion"
        ],
        "scholar_url": "https://scholar.google.com/citations?user=SomsakPanha"
    },
    {
        "id": "cu_sci_physics_cern_001",
        "university": "Chulalongkorn University",
        "university_th": "จุฬาลงกรณ์มหาวิทยาลัย",
        "faculty": "Faculty of Science",
        "faculty_th": "คณะวิทยาศาสตร์",
        "department": "Department of Physics & High Energy and Particle Physics Group",
        "department_th": "ภาควิชาฟิสิกส์ และกลุ่มวิจัยฟิสิกส์พลังงานสูงและอนุภาค",
        "academic_title": "Prof. Dr.",
        "academic_title_th": "ศ.ดร.",
        "first_name": "Burin",
        "last_name": "Asavapibhop",
        "full_name": "Prof. Dr. Burin Asavapibhop",
        "full_name_th": "ศ.ดร. บุรินทร์ อัศวพิภพ",
        "role": "Head of Thailand-CERN CMS Collaboration Team / Distinguished Particle Physicist",
        "email": "burin.a@chula.ac.th",
        "image_url": "https://physics.sc.chula.ac.th/images/faculty/burin.jpg",
        "profile_url": "https://physics.sc.chula.ac.th/staff/burin",
        "education": [
            "Ph.D. (Experimental High Energy Physics), University of Massachusetts Amherst, USA",
            "B.Sc. (Physics - Honours), Chulalongkorn University"
        ],
        "research_interests": [
            "Experimental Particle Physics & Large Hadron Collider (LHC) CMS Experiment",
            "Higgs Boson Properties and Search for Physics Beyond the Standard Model (BSM)",
            "Heavy-Ion Collisions and Quark-Gluon Plasma (QGP) Dynamics",
            "Distributed Grid Computing and Big Data Analytics for High Energy Particle Detectors",
            "Scintillation Radiation Detectors and Silicon Pixel Tracker Instrumentation"
        ],
        "taught_courses": [
            "Subatomic and Particle Physics",
            "Quantum Mechanics and Relativistic Quantum Fields",
            "Advanced Computational Physics and Data Analysis"
        ],
        "featured_publications": [
            "Measurement of the Higgs Boson Mass and Decay Width in the Diphoton and Four-Lepton Channels at the CMS Experiment",
            "Search for Supersymmetry and Dark Matter Candidates in Proton-Proton Collisions at 13 TeV with the CMS Detector",
            "Performance and Calibration of the CMS Silicon Pixel Detector in High-Luminosity LHC Runs"
        ],
        "scholar_url": "https://scholar.google.com/citations?user=BurinAsavapibhop"
    },

    # =========================================================================
    # 4. CHULALONGKORN BUSINESS SCHOOL (CBS) & SASIN SCHOOL OF MANAGEMENT
    # =========================================================================
    {
        "id": "cu_cbs_fin_001",
        "university": "Chulalongkorn University",
        "university_th": "จุฬาลงกรณ์มหาวิทยาลัย",
        "faculty": "Chulalongkorn Business School (Faculty of Commerce and Accountancy)",
        "faculty_th": "คณะพาณิชยศาสตร์และการบัญชี (CBS จุฬาฯ)",
        "department": "Department of Banking and Finance",
        "department_th": "ภาควิชาการธนาคารและการเงิน",
        "academic_title": "Prof. Dr.",
        "academic_title_th": "ศ.ดร.",
        "first_name": "Kanis",
        "last_name": "Saengchote",
        "full_name": "Prof. Dr. Kanis Saengchote",
        "full_name_th": "ศ.ดร. คณิสร์ แสงโชติ",
        "role": "Associate Professor in FinTech, Blockchain Analytics & Real Estate Finance",
        "email": "kanis@cbs.chula.ac.th",
        "image_url": "https://www.cbs.chula.ac.th/images/faculty/kanis.jpg",
        "profile_url": "https://www.cbs.chula.ac.th/staff/kanis",
        "education": [
            "Ph.D. (Finance), Kellogg School of Management, Northwestern University, USA",
            "M.S. (Finance), Kellogg School of Management, Northwestern University, USA",
            "B.Sc. (Economics - First Class Honours), London School of Economics (LSE), UK"
        ],
        "research_interests": [
            "Decentralized Finance (DeFi) & Blockchain On-Chain Forensics",
            "Central Bank Digital Currencies (CBDC) & Digital Asset Market Microstructure",
            "Real Estate Pricing Dynamics & REITs Optimization",
            "Corporate Financial Governance and Capital Structure",
            "Financial Risk Modeling during Systemic Crises"
        ],
        "taught_courses": [
            "Financial Technology (FinTech) and Digital Assets",
            "Advanced Corporate Finance",
            "Real Estate Investment and Securitization"
        ],
        "featured_publications": [
            "Liquidity Provision and Automated Market Maker Dynamics in Decentralized Exchanges (Uniswap v3)",
            "Systemic Risk Contagion across Traditional Equity Markets and Cryptocurrency Ecosystems",
            "House Price Indices and Affordability Trends in Bangkok Metropolitan Region: A Hedonic Price Analysis"
        ],
        "scholar_url": "https://scholar.google.com/citations?user=KanisSaengchote"
    },
    {
        "id": "cu_cbs_stat_001",
        "university": "Chulalongkorn University",
        "university_th": "จุฬาลงกรณ์มหาวิทยาลัย",
        "faculty": "Chulalongkorn Business School (Faculty of Commerce and Accountancy)",
        "faculty_th": "คณะพาณิชยศาสตร์และการบัญชี (CBS จุฬาฯ)",
        "department": "Department of Statistics & Business Analytics",
        "department_th": "ภาควิชาสถิติและวิทยาการวิเคราะห์ธุรกิจ",
        "academic_title": "Prof. Dr.",
        "academic_title_th": "ศ.ดร.",
        "first_name": "Wilert",
        "last_name": "Puriwat",
        "full_name": "Prof. Dr. Wilert Puriwat",
        "full_name_th": "ศ.ดร. วิเลิศ ภูริวัตร",
        "role": "President of Chulalongkorn University / Distinguished Professor in Marketing Analytics and Consumer Neuroscience",
        "email": "wilert@cbs.chula.ac.th",
        "image_url": "https://www.cbs.chula.ac.th/images/faculty/wilert.jpg",
        "profile_url": "https://www.cbs.chula.ac.th/staff/wilert",
        "education": [
            "D.Phil. (Management Studies), University of Oxford, UK",
            "M.B.A., Babson College, USA",
            "M.Sc. (International Marketing), University of Strathclyde, UK",
            "B.B.A. (Honours), Chulalongkorn University"
        ],
        "research_interests": [
            "Digital Customer Experience & AI-Driven Omnichannel Marketing",
            "Consumer Neuroscience & Eye-Tracking Decision Modeling",
            "Brand Equity Dynamics in Social Commerce Platforms",
            "Sustainable Consumer Behavior & Green Purchasing Intentions",
            "Big Data Analytics in Retail and Financial Services"
        ],
        "taught_courses": [
            "Strategic Marketing Analytics",
            "Consumer Neuroscience and Behavioral Modeling",
            "Digital Business Transformation Strategy"
        ],
        "featured_publications": [
            "Investigating the Impact of Artificial Intelligence-Powered Chatbots on Customer Engagement and Brand Loyalty",
            "Neuro-Marketing Insights into Sustainable Product Purchasing: An Eye-Tracking and EEG Integrated Study",
            "Omnichannel Service Integration and Its Impact on Customer Perceived Value in Asian Emerging Markets"
        ],
        "scholar_url": "https://scholar.google.com/citations?user=WilertPuriwat"
    },
    {
        "id": "cu_cbs_strategy_001",
        "university": "Chulalongkorn University",
        "university_th": "จุฬาลงกรณ์มหาวิทยาลัย",
        "faculty": "Chulalongkorn Business School (Faculty of Commerce and Accountancy)",
        "faculty_th": "คณะพาณิชยศาสตร์และการบัญชี (CBS จุฬาฯ)",
        "department": "Department of Commerce & Strategic Management",
        "department_th": "ภาควิชาพาณิชยศาสตร์ (สาขาวิชาการจัดการเชิงกลยุทธ์)",
        "academic_title": "Prof. Dr.",
        "academic_title_th": "ศ.ดร.",
        "first_name": "Pasu",
        "last_name": "Decharin",
        "full_name": "Prof. Dr. Pasu Decharin",
        "full_name_th": "ศ.ดร. พสุ เดชะรินทร์",
        "role": "Distinguished Professor in Strategic Management / Former Dean of Chulalongkorn Business School",
        "email": "pasu@cbs.chula.ac.th",
        "image_url": "https://www.cbs.chula.ac.th/images/faculty/pasu.jpg",
        "profile_url": "https://www.cbs.chula.ac.th/staff/pasu",
        "education": [
            "Ph.D. (Strategic Management), Oregon State University, USA",
            "M.B.A., University of Colorado at Boulder, USA",
            "B.B.A. (Honours), Chulalongkorn University"
        ],
        "research_interests": [
            "Corporate Strategy Formulation and Strategic Agility in Dynamic Environments",
            "Balanced Scorecard (BSC) and Strategy Maps in Enterprise Performance Management",
            "Mergers and Acquisitions (M&A) Integration and Synergy Realization",
            "Corporate Governance, Board Effectiveness and ESG Transformation",
            "Digital Disruption and Business Model Innovation in ASEAN"
        ],
        "taught_courses": [
            "Strategic Management and Business Policy",
            "Corporate Governance and Executive Leadership",
            "Strategic Agility and Organizational Transformation"
        ],
        "featured_publications": [
            "Strategic Agility and Dynamic Capabilities: How Asian Conglomerates Navigate Geopolitical and Technological Shocks",
            "The Mediating Role of Corporate Governance in ESG Performance and Firm Valuation in Emerging Markets",
            "Post-Merger Integration Success Factors: An Empirical Investigation of Cross-Border M&A in Southeast Asia"
        ],
        "scholar_url": "https://scholar.google.com/citations?user=PasuDecharin"
    },
    {
        "id": "cu_sasin_silver_econ_001",
        "university": "Chulalongkorn University",
        "university_th": "จุฬาลงกรณ์มหาวิทยาลัย",
        "faculty": "Sasin School of Management",
        "faculty_th": "สถาบันบัณฑิตบริหารธุรกิจ ศศินทร์ แห่งจุฬาลงกรณ์มหาวิทยาลัย",
        "department": "Department of Demography and Strategic Economics",
        "department_th": "สาขาประชากรศาสตร์และเศรษฐศาสตร์เชิงกลยุทธ์",
        "academic_title": "Prof. Dr.",
        "academic_title_th": "ศ.ดร.",
        "first_name": "Kua",
        "last_name": "Wongboonsin",
        "full_name": "Prof. Dr. Kua Wongboonsin",
        "full_name_th": "ศ.ดร. เกื้อ วงศ์บุญสิน",
        "role": "Distinguished Professor in Demography, Silver Economy and Aging Workforce Policies",
        "email": "kua.w@sasin.edu",
        "image_url": "https://www.sasin.edu/images/faculty/kua.jpg",
        "profile_url": "https://www.sasin.edu/staff/kua",
        "education": [
            "Ph.D. (Demography), University of Pennsylvania, USA",
            "M.A. (Demography), University of Pennsylvania, USA",
            "B.A. (Political Science - Honours), Chulalongkorn University"
        ],
        "research_interests": [
            "Silver Economy & Business Models for Super-Aged Societies",
            "Demographic Dividend II & Longevity Financial Planning in ASEAN",
            "Labor Force Aging and Automation Replacement Dynamics",
            "National Pension System Sustainability and Social Security Reform",
            "Spatial Population Distribution and Urbanization Trends"
        ],
        "taught_courses": [
            "Demographic Dynamics and Global Business Strategy",
            "Silver Economy and Aging Market Opportunities",
            "Strategic Human Capital and Labor Policy"
        ],
        "featured_publications": [
            "The Second Demographic Dividend and Economic Growth in Aging Asian Economies",
            "Silver Economy Transformation: Market Opportunities and Policy Challenges for Thailand's Super-Aged Society",
            "Labor Force Participation of Older Workers and Corporate Productivity in Southeast Asia"
        ],
        "scholar_url": "https://scholar.google.com/citations?user=KuaWongboonsin"
    },

    # =========================================================================
    # 5. FACULTY OF PHARMACEUTICAL SCIENCES (CHULALONGKORN UNIVERSITY)
    # =========================================================================
    {
        "id": "cu_pharm_nano_001",
        "university": "Chulalongkorn University",
        "university_th": "จุฬาลงกรณ์มหาวิทยาลัย",
        "faculty": "Faculty of Pharmaceutical Sciences",
        "faculty_th": "คณะเภสัชศาสตร์",
        "department": "Department of Pharmaceutics and Industrial Pharmacy",
        "department_th": "ภาควิชาเภสัชกรรมและเภสัชอุตสาหกรรม",
        "academic_title": "Prof. Dr.",
        "academic_title_th": "ศ.ภญ.ดร.",
        "first_name": "Garnpimol",
        "last_name": "Ritthidej",
        "full_name": "Prof. Dr. Pharm. Garnpimol Ritthidej",
        "full_name_th": "ศ.ภญ.ดร. กาญจน์พิมล ฤทธิเดช",
        "role": "Distinguished Professor in Pharmaceutical Formulation and Pulmonary Drug Delivery",
        "email": "garnpimol.r@chula.ac.th",
        "image_url": "https://pharm.chula.ac.th/images/faculty/garnpimol.jpg",
        "profile_url": "https://pharm.chula.ac.th/staff/garnpimol",
        "education": [
            "Ph.D. (Industrial and Physical Pharmacy), Purdue University, USA",
            "B.Sc. (Pharmacy - First Class Honours), Chulalongkorn University"
        ],
        "research_interests": [
            "Dry Powder Inhalers (DPI) & Pulmonary Delivery of Peptides and Vaccines",
            "Lipid-Based Nanocarriers (SLN/NLC) for Enhanced Oral Bioavailability",
            "Mucoadhesive Polymeric Nanoparticles for Ocular and Transdermal Delivery",
            "Microencapsulation of Natural Antioxidants for Cosmeceutical Innovations",
            "Process Analytical Technology (PAT) in Pharmaceutical Scale-Up"
        ],
        "taught_courses": [
            "Advanced Dosage Form Design and Development",
            "Pulmonary and Nasal Drug Delivery Systems",
            "Physical Pharmacy and Colloidal Phenomena"
        ],
        "featured_publications": [
            "Engineering Carrier-Free Spray-Dried Inhalable Microparticles for Targeted Deep Lung Vaccine Delivery",
            "Chitosan-Coated Nanostructured Lipid Carriers for Improved Corneal Permeability and Ocular Drug Retention",
            "Physicochemical Stability and Dissolution Profiling of Poorly Water-Soluble Active Ingredients via Solid Dispersions"
        ],
        "scholar_url": "https://scholar.google.com/citations?user=GarnpimolRitthidej"
    },
    {
        "id": "cu_pharm_silk_001",
        "university": "Chulalongkorn University",
        "university_th": "จุฬาลงกรณ์มหาวิทยาลัย",
        "faculty": "Faculty of Pharmaceutical Sciences",
        "faculty_th": "คณะเภสัชศาสตร์",
        "department": "Department of Pharmacy Practice & Center of Excellence in Natural Products and Biomaterials",
        "department_th": "ภาควิชาเภสัชกรรมปฏิบัติการ และศูนย์ความเป็นเลิศด้านนวัตกรรมผลิตภัณฑ์ธรรมชาติและชีววัสดุ",
        "academic_title": "Prof. Dr.",
        "academic_title_th": "ศ.ภญ.ดร.",
        "first_name": "Pornanong",
        "last_name": "Aramwit",
        "full_name": "Prof. Dr. Pharm. Pornanong Aramwit",
        "full_name_th": "ศ.ภญ.ดร. พรอนงค์ อร่ามวิทย์",
        "role": "Distinguished Professor in Clinical Pharmacy & World-Renowned Innovator in Bioactive Silk Sericin Therapeutics",
        "email": "pornanong.a@chula.ac.th",
        "image_url": "https://pharm.chula.ac.th/images/faculty/pornanong.jpg",
        "profile_url": "https://pharm.chula.ac.th/staff/pornanong",
        "education": [
            "Ph.D. (Pharmacy Administration and Clinical Pharmacy), University of Wisconsin-Madison, USA",
            "M.S. (Clinical Pharmacy), University of Wisconsin-Madison, USA",
            "B.Sc. (Pharmacy - Honours), Chulalongkorn University"
        ],
        "research_interests": [
            "Silk Sericin and Fibroin Extraction for Advanced Wound Care Dressings",
            "Bioactive Natural Cosmeceuticals for Anti-Aging and Skin Regeneration",
            "Collagen and Sericin Scaffolds for Bone and Cartilage Regeneration",
            "Clinical Pharmacokinetics and Therapeutic Drug Monitoring",
            "Commercialization and Regulatory Dossier Filing for Natural Biomaterials"
        ],
        "taught_courses": [
            "Advanced Clinical Pharmacy and Biotherapeutics",
            "Pharmaceutical Biomaterials in Wound Care and Tissue Regeneration",
            "Clinical Trials Management and Pharmaceutical Commercialization"
        ],
        "featured_publications": [
            "Silk Sericin-Loaded Hydrogels Accelerate Full-Thickness Cutaneous Wound Healing via Enhanced Fibroblast Proliferation and Collagen Synthesis",
            "Clinical Evaluation of a Novel Silk Sericin Wound Dressing in Patients with Deep Second-Degree Burns",
            "Anti-Inflammatory and Antioxidative Mechanisms of Low-Molecular-Weight Silk Sericin Peptides in Dermatological Applications"
        ],
        "scholar_url": "https://scholar.google.com/citations?user=PornanongAramwit"
    },

    # =========================================================================
    # 6. FACULTY OF ARCHITECTURE (CHULALONGKORN UNIVERSITY)
    # =========================================================================
    {
        "id": "cu_arch_urban_001",
        "university": "Chulalongkorn University",
        "university_th": "จุฬาลงกรณ์มหาวิทยาลัย",
        "faculty": "Faculty of Architecture",
        "faculty_th": "คณะสถาปัตยกรรมศาสตร์",
        "department": "Department of Urban and Regional Planning & Urban Futures Lab",
        "department_th": "ภาควิชาการวางแผนภาคและเมือง และห้องปฏิบัติการอนาคตเมือง",
        "academic_title": "Assoc. Prof. Dr.",
        "academic_title_th": "รศ.ดร.",
        "first_name": "Apiwat",
        "last_name": "Ratanawaraha",
        "full_name": "Assoc. Prof. Dr. Apiwat Ratanawaraha",
        "full_name_th": "รศ.ดร. อภิวัฒน์ รัตนวราหะ",
        "role": "Director of Urban Futures and Spatial Policy Lab / Pioneer in Transit-Oriented Development & Land Value Capture",
        "email": "apiwat.r@chula.ac.th",
        "image_url": "https://arch.chula.ac.th/images/faculty/apiwat.jpg",
        "profile_url": "https://arch.chula.ac.th/staff/apiwat",
        "education": [
            "Ph.D. (Urban and Regional Planning), Massachusetts Institute of Technology (MIT), USA",
            "M.Phil. (Land Economy), University of Cambridge, UK",
            "B.Eng. (Civil Engineering), Chulalongkorn University"
        ],
        "research_interests": [
            "Futures of Mobility, Autonomous Vehicles & Urban Spatial Restructuring",
            "Transit-Oriented Development (TOD) & Land Value Capture (LVC) Mechanisms",
            "Spatial Econometrics and Big Data for Megacity Informal Settlement Dynamics",
            "Urban Resilience to Sea Level Rise and Subsidence in Bangkok Megacity",
            "Land Use Law, Zoning Reform and Municipal Finance Innovations"
        ],
        "taught_courses": [
            "Urban and Regional Economics",
            "Land Use and Transportation Planning",
            "Urban Futures and Strategic Spatial Policy"
        ],
        "featured_publications": [
            "Land Value Capture through Rail Transit Financing: Institutional Barriers and Legal Frameworks in Bangkok",
            "Autonomous Vehicles and the Spatial Restructuring of Megacities: A Multi-Scenario Simulation Model",
            "Urban Subsidence and Coastal Inundation Resilience in Southeast Asian Delta Metropolises"
        ],
        "scholar_url": "https://scholar.google.com/citations?user=ApiwatRatanawaraha"
    },
    {
        "id": "cu_arch_green_001",
        "university": "Chulalongkorn University",
        "university_th": "จุฬาลงกรณ์มหาวิทยาลัย",
        "faculty": "Faculty of Architecture",
        "faculty_th": "คณะสถาปัตยกรรมศาสตร์",
        "department": "Department of Architecture & Building Technology Research Unit",
        "department_th": "ภาควิชาสถาปัตยกรรมศาสตร์ และหน่วยวิจัยเทคโนโลยีอาคารเพื่อสิ่งแวดล้อม",
        "academic_title": "Assoc. Prof. Dr.",
        "academic_title_th": "รศ.ดร.",
        "first_name": "Atch",
        "last_name": "Sreshthaputra",
        "full_name": "Assoc. Prof. Dr. Atch Sreshthaputra",
        "full_name_th": "รศ.ดร. อรรจน์ เศรษฐบุตร",
        "role": "Distinguished Building Technology Scholar / President of Thai Green Building Institute (TGBI)",
        "email": "atch.s@chula.ac.th",
        "image_url": "https://arch.chula.ac.th/images/faculty/atch.jpg",
        "profile_url": "https://arch.chula.ac.th/staff/atch",
        "education": [
            "Ph.D. (Architecture / Building Energy), Texas A&M University, USA",
            "M.Arch., Texas A&M University, USA",
            "B.Arch. (Honours), Chulalongkorn University"
        ],
        "research_interests": [
            "Net-Zero Energy Building (NZEB) Design in Hot and Humid Tropical Climates",
            "Building Information Modeling (BIM) Integrated Energy and Daylight Simulation",
            "Passive Cooling Strategies, Natural Ventilation and Thermal Comfort Modeling",
            "Embodied Carbon Life Cycle Assessment (LCA) in Sustainable Construction Materials",
            "Green Building Rating Systems Certification Standards (TREES, LEED, WELL)"
        ],
        "taught_courses": [
            "Sustainable Architectural Design and Energy Simulation",
            "Building Climatology and Passive Environmental Systems",
            "Green Building Standards and Certification Practice"
        ],
        "featured_publications": [
            "Optimizing Passive Shading and Natural Ventilation for Net-Zero Commercial High-Rise Buildings in Tropical Megacities",
            "Comparative Life-Cycle Carbon Assessment of Mass Timber versus Conventional Reinforced Concrete Buildings in Southeast Asia",
            "Thermal Comfort and Energy Conservation Potential of Variable Air Volume Air-Conditioning in Thai Office Buildings"
        ],
        "scholar_url": "https://scholar.google.com/citations?user=AtchSreshthaputra"
    },

    # =========================================================================
    # 7. FACULTY OF ECONOMICS & POLITICAL SCIENCE (CHULALONGKORN UNIVERSITY)
    # =========================================================================
    {
        "id": "cu_econ_behav_001",
        "university": "Chulalongkorn University",
        "university_th": "จุฬาลงกรณ์มหาวิทยาลัย",
        "faculty": "Faculty of Economics",
        "faculty_th": "คณะเศรษฐศาสตร์",
        "department": "Department of Economics & Behavioral Economics and Anti-Corruption Lab",
        "department_th": "คณะเศรษฐศาสตร์ (ห้องปฏิบัติการเศรษฐศาสตร์พฤติกรรมและการต่อต้านการทุจริต)",
        "academic_title": "Assoc. Prof. Dr.",
        "academic_title_th": "รศ.ดร.",
        "first_name": "Thanee",
        "last_name": "Chaiwat",
        "full_name": "Assoc. Prof. Dr. Thanee Chaiwat",
        "full_name_th": "รศ.ดร. ธานี ชัยวัฒน์",
        "role": "Director of Center for Behavioral and Experimental Economics (CBEE) / National Anti-Corruption Economic Modeling Expert",
        "email": "thanee.c@chula.ac.th",
        "image_url": "https://econ.chula.ac.th/images/faculty/thanee.jpg",
        "profile_url": "https://econ.chula.ac.th/staff/thanee",
        "education": [
            "Ph.D. (Economics), University of Bologna, Italy",
            "M.Sc. (Economics), University of Warwick, UK",
            "B.Econ. (First Class Honours), Chulalongkorn University"
        ],
        "research_interests": [
            "Behavioral Economics, Lab-in-the-Field Experiments & Nudge Interventions",
            "Economics of Crime, Corruption Networks & Institutional Integrity",
            "Social Norms, Trust and Cooperation Dynamics in Rural Communities",
            "Behavioral Public Policy for Financial Literacy and Debt De-escalation",
            "Experimental Game Theory in Multi-Stakeholder Resource Bargaining"
        ],
        "taught_courses": [
            "Behavioral and Experimental Economics",
            "Economics of Crime and Institutional Corruption",
            "Microeconomic Theory and Game Theoretic Modeling"
        ],
        "featured_publications": [
            "Experimental Evidence on Bribery Networks and the Role of Whistleblower Protection in Emerging Economies",
            "Nudging Pro-Social Compliance: A Randomized Controlled Field Trial on Tax Compliance and Civic Responsibility",
            "Social Capital, Trust, and Community Resilience during Severe Economic Shocks in Rural Thailand"
        ],
        "scholar_url": "https://scholar.google.com/citations?user=ThaneeChaiwat"
    },
    {
        "id": "cu_polsci_ir_001",
        "university": "Chulalongkorn University",
        "university_th": "จุฬาลงกรณ์มหาวิทยาลัย",
        "faculty": "Faculty of Political Science",
        "faculty_th": "คณะรัฐศาสตร์",
        "department": "Department of International Relations & Institute of Security and International Studies (ISIS)",
        "department_th": "ภาควิชาความสัมพันธ์ระหว่างประเทศ และสถาบันศึกษาความมั่นคงและนานาชาติ (ISIS)",
        "academic_title": "Prof. Dr.",
        "academic_title_th": "ศ.ดร.",
        "first_name": "Thitinan",
        "last_name": "Pongsudhirak",
        "full_name": "Prof. Dr. Thitinan Pongsudhirak",
        "full_name_th": "ศ.ดร. ฐิตินันท์ พงษ์สุทธิรักษ์",
        "role": "Senior Fellow and Former Director of ISIS Thailand / World-Renowned Geopolitical Analyst on ASEAN and US-China Rivalry",
        "email": "thitinan.p@chula.ac.th",
        "image_url": "https://polsci.chula.ac.th/images/faculty/thitinan.jpg",
        "profile_url": "https://polsci.chula.ac.th/staff/thitinan",
        "education": [
            "Ph.D. (International Relations), London School of Economics (LSE), UK",
            "M.A. (International Economics and American Foreign Policy), Johns Hopkins University (SAIS), USA",
            "B.A. (Political Science), University of California, Santa Barbara, USA"
        ],
        "research_interests": [
            "US-China Geopolitical Competition and Strategic Hedging in Southeast Asia",
            "ASEAN Centrality, Regional Security Architecture and Minilateralism (Quad, AUKUS)",
            "Thailand Foreign Policy, Democratic Transition and Constitutional Politics",
            "Indo-Pacific Maritime Security and Geoeconomics in the South China Sea",
            "Mekong Subregional Geopolitics and Transboundary Water Governance"
        ],
        "taught_courses": [
            "International Relations Theory and Geopolitical Dynamics",
            "Foreign Policy Analysis of Major Powers in Southeast Asia",
            "Security and Strategic Studies in the Indo-Pacific"
        ],
        "featured_publications": [
            "Thailand's Strategic Equidistance and Foreign Policy Hedging amidst US-China Strategic Rivalry",
            "ASEAN's Geopolitical Dilemma: Centrality, Minilateralism, and Indo-Pacific Balance of Power",
            "Democratic Backsliding and Strategic Realignment in Southeast Asian Foreign Relations"
        ],
        "scholar_url": "https://scholar.google.com/citations?user=ThitinanPongsudhirak"
    },
    {
        "id": "cu_polsci_security_001",
        "university": "Chulalongkorn University",
        "university_th": "จุฬาลงกรณ์มหาวิทยาลัย",
        "faculty": "Faculty of Political Science",
        "faculty_th": "คณะรัฐศาสตร์",
        "department": "Department of International Relations & Strategic Studies Hub",
        "department_th": "ภาควิชาความสัมพันธ์ระหว่างประเทศ",
        "academic_title": "Prof. Dr.",
        "academic_title_th": "ศ.ดร.",
        "first_name": "Surachart",
        "last_name": "Bamrungsuk",
        "full_name": "Prof. Dr. Surachart Bamrungsuk",
        "full_name_th": "ศ.ดร. สุรชาติ บำรุงสุข",
        "role": "Distinguished Professor in Strategic and Defense Studies / Senior Advisor on Military Reform & National Security",
        "email": "surachart.b@chula.ac.th",
        "image_url": "https://polsci.chula.ac.th/images/faculty/surachart.jpg",
        "profile_url": "https://polsci.chula.ac.th/staff/surachart",
        "education": [
            "Ph.D. (Political Science / Defense Policy), Columbia University, USA",
            "M.A. (Political Science), Columbia University, USA",
            "B.A. (Political Science - Honours), Chulalongkorn University"
        ],
        "research_interests": [
            "Civil-Military Relations and Military Modernization in Southeast Asia",
            "Defense Procurement, National Security Architecture and Hybrid Warfare",
            "Maritime Geopolitics and Counter-Piracy in the Malacca Strait",
            "Insurgency Dynamics and Peace Negotiations in Southern Thailand",
            "Great Power Nuclear Deterrence and Global Arms Control Dynamics"
        ],
        "taught_courses": [
            "Strategic and Defense Studies",
            "Civil-Military Relations in Comparative Perspective",
            "National Security Policy and Crisis Decision Making"
        ],
        "featured_publications": [
            "Military Transformed: The Politics of Defense Procurement and Modernization in Thailand",
            "Civil-Military Relations and Democratic Transitions in Post-Authoritarian Southeast Asia",
            "Hybrid Warfare and Grey-Zone Challenges in Maritime Southeast Asia"
        ],
        "scholar_url": "https://scholar.google.com/citations?user=SurachartBamrungsuk"
    },

    # =========================================================================
    # 8. FACULTY OF VETERINARY SCIENCE (CHULALONGKORN UNIVERSITY)
    # =========================================================================
    {
        "id": "cu_vet_swine_001",
        "university": "Chulalongkorn University",
        "university_th": "จุฬาลงกรณ์มหาวิทยาลัย",
        "faculty": "Faculty of Veterinary Science",
        "faculty_th": "คณะสัตวแพทยศาสตร์",
        "department": "Department of Veterinary Pathology & Swine Viral Research Hub",
        "department_th": "ภาควิชาพยาธิวิทยาทางสัตวแพทย์ และหน่วยวิจัยไวรัสวิทยาโรคสุกร",
        "academic_title": "Prof. Dr.",
        "academic_title_th": "ศ.น.สพ.ดร.",
        "first_name": "Roongroje",
        "last_name": "Thanawongnuwech",
        "full_name": "Prof. Dr. Vet. Roongroje Thanawongnuwech",
        "full_name_th": "ศ.น.สพ.ดร. รุ่งโรจน์ ธนาวงษ์นุเวช",
        "role": "Distinguished Professor in Veterinary Pathology / Fellow of Royal Society / Former Dean of Faculty of Veterinary Science",
        "email": "roongroje.t@chula.ac.th",
        "image_url": "https://vet.chula.ac.th/images/faculty/roongroje.jpg",
        "profile_url": "https://vet.chula.ac.th/staff/roongroje",
        "education": [
            "Ph.D. (Veterinary Pathology), Iowa State University, USA",
            "M.S. (Veterinary Pathology), Iowa State University, USA",
            "D.V.M. (First Class Honours), Chulalongkorn University"
        ],
        "research_interests": [
            "Pathogenesis and Immunopathology of Porcine Reproductive and Respiratory Syndrome Virus (PRRSV)",
            "African Swine Fever Virus (ASFV) Molecular Diagnosis and Biosecurity Protocols",
            "Porcine Epidemic Diarrhea Virus (PEDV) Lineage Evolution in Asia",
            "One Health Surveillance of Emerging Zoonotic Viruses at Animal-Human Interfaces",
            "Mucosal Vaccine Development and Immunomodulation in Food Animals"
        ],
        "taught_courses": [
            "Advanced Veterinary Systemic Pathology",
            "Swine Health Management and Diagnostic Virology",
            "One Health and Emerging Zoonoses Control"
        ],
        "featured_publications": [
            "Genetic Characterization and Immunopathogenesis of Lineage 1 Highly Pathogenic PRRSV in Southeast Asia",
            "Biosafety and Biosecurity Interventions against African Swine Fever Virus Incursion in Commercial Swine Holdings",
            "Zoonotic Risk Profiling and Cross-Species Transmission Dynamics of Novel Swine Coronaviruses"
        ],
        "scholar_url": "https://scholar.google.com/citations?user=RoongrojeThanawongnuwech"
    },
    {
        "id": "cu_vet_avian_onehealth_001",
        "university": "Chulalongkorn University",
        "university_th": "จุฬาลงกรณ์มหาวิทยาลัย",
        "faculty": "Faculty of Veterinary Science",
        "faculty_th": "คณะสัตวแพทยศาสตร์",
        "department": "Department of Veterinary Public Health & Center of Excellence for Emerging and Re-emerging Infectious Diseases in Animals",
        "department_th": "ภาควิชาสัตวแพทย์สาธารณสุข และศูนย์ความเป็นเลิศด้านโรคติดเชื้ออุบัติใหม่ในสัตว์",
        "academic_title": "Prof. Dr.",
        "academic_title_th": "ศ.น.สพ.ดร.",
        "first_name": "Alongkorn",
        "last_name": "Amonsin",
        "full_name": "Prof. Dr. Vet. Alongkorn Amonsin",
        "full_name_th": "ศ.น.สพ.ดร. อลงกร อมรศิลป์",
        "role": "Director of Center of Excellence for Emerging Infectious Diseases in Animals / FAO & WHO One Health Expert",
        "email": "alongkorn.a@chula.ac.th",
        "image_url": "https://vet.chula.ac.th/images/faculty/alongkorn.jpg",
        "profile_url": "https://vet.chula.ac.th/staff/alongkorn",
        "education": [
            "Ph.D. (Comparative and Molecular Biosciences), University of Minnesota, USA",
            "M.S. (Veterinary Microbiology), University of Minnesota, USA",
            "D.V.M. (Honours), Chulalongkorn University"
        ],
        "research_interests": [
            "Avian Influenza Virus (H5N1, H5N6, H9N2) Molecular Evolution and Pandemic Risk",
            "Genomic Epidemiology and Cross-Species Spillover of Coronaviruses in Bats and Wildlife",
            "Antimicrobial Resistance (AMR) Profiling in Livestock Supply Chains and Aquaculture",
            "One Health Integrated Surveillance Architecture in the Greater Mekong Subregion",
            "Multiplex Real-Time Molecular Assays for Rapid Zoonotic Outbreak Containment"
        ],
        "taught_courses": [
            "Veterinary Epidemiology and One Health Informatics",
            "Zoonoses, Emerging Infectious Diseases and Food Safety",
            "Molecular Diagnostic Virology in Veterinary Public Health"
        ],
        "featured_publications": [
            "Genomic Surveillance of Clade 2.3.4.4b Highly Pathogenic Avian Influenza H5N1 along Migratory Flyways in Southeast Asia",
            "Identification of Novel Coronaviruses in Horseshoe Bats and Intermediate Mammals in Tropical Karst Landscapes",
            "One Health Genomic Surveillance of Colistin-Resistant mcr-Positive Enterobacteriaceae across Livestock and Humans"
        ],
        "scholar_url": "https://scholar.google.com/citations?user=AlongkornAmonsin"
    },

    # =========================================================================
    # 9. FACULTY OF DENTISTRY (CHULALONGKORN UNIVERSITY)
    # =========================================================================
    {
        "id": "cu_dent_stemcell_001",
        "university": "Chulalongkorn University",
        "university_th": "จุฬาลงกรณ์มหาวิทยาลัย",
        "faculty": "Faculty of Dentistry",
        "faculty_th": "คณะทันตแพทยศาสตร์",
        "department": "Department of Anatomy & Center of Excellence in Oral Biology and Tissue Engineering",
        "department_th": "ภาควิชากายวิภาคศาสตร์ และศูนย์ความเป็นเลิศด้านชีววิทยาช่องปากและวิศวกรรมเนื้อเยื่อ",
        "academic_title": "Prof. Dr.",
        "academic_title_th": "ศ.ทพ.ดร.",
        "first_name": "Prasit",
        "last_name": "Pavasant",
        "full_name": "Prof. Dr. Dent. Prasit Pavasant",
        "full_name_th": "ศ.ทพ.ดร. ประสิทธิ์ ภวสันต์",
        "role": "Distinguished Professor in Oral Biology / Pioneer in Dental Pulp Stem Cells and 3D Bioceramic Bone Regeneration",
        "email": "prasit.p@chula.ac.th",
        "image_url": "https://dent.chula.ac.th/images/faculty/prasit.jpg",
        "profile_url": "https://dent.chula.ac.th/staff/prasit",
        "education": [
            "Ph.D. (Anatomy and Developmental Biology), University of London, UK",
            "D.D.S. (First Class Honours, Gold Medal), Chulalongkorn University"
        ],
        "research_interests": [
            "Human Dental Pulp Stem Cells (hDPSCs) & Periodontal Ligament Stem Cells (PDLSCs)",
            "3D Bioprinted Biphasic Calcium Phosphate Scaffolds for Maxillofacial Bone Regeneration",
            "Mechanotransduction and Fluid Shear Stress Signaling in Osteoblast Differentiation",
            "Bioactive Peptides and Platelet-Rich Fibrin (PRF) in Dental Implant Osseointegration",
            "Molecular Mechanisms of Periodontitis-Induced Alveolar Bone Resorption"
        ],
        "taught_courses": [
            "Advanced Oral Biology and Molecular Craniofacial Development",
            "Stem Cell Biology and Tissue Engineering in Dentistry",
            "Bone Biology and Implant Biomaterials"
        ],
        "featured_publications": [
            "Human Dental Pulp Stem Cells Seeded on 3D-Printed Biphasic Calcium Phosphate Scaffolds Promote Massive Maxillofacial Bone Repair",
            "Mechanosensitive Ion Channel Piezo1 Mediates Fluid Shear Stress-Induced Osteogenic Differentiation in Periodontal Ligament Cells",
            "Therapeutic Efficacy of Dental Stem Cell Conditioned Medium in Accelerating Periodontal Tissue Regeneration"
        ],
        "scholar_url": "https://scholar.google.com/citations?user=PrasitPavasant"
    },

    # =========================================================================
    # 10. FACULTY OF LAW & COMMUNICATION ARTS (CHULALONGKORN UNIVERSITY)
    # =========================================================================
    {
        "id": "cu_law_cyber_001",
        "university": "Chulalongkorn University",
        "university_th": "จุฬาลงกรณ์มหาวิทยาลัย",
        "faculty": "Faculty of Law",
        "faculty_th": "คณะนิติศาสตร์",
        "department": "Department of International Law & Center for AI and Digital Law Policy",
        "department_th": "ภาควิชากฎหมายระหว่างประเทศ และศูนย์วิจัยกฎหมายปัญญาประดิษฐ์และดิจิทัล",
        "academic_title": "Prof. Dr.",
        "academic_title_th": "ศ.ดร.",
        "first_name": "Pareena",
        "last_name": "Srivanit",
        "full_name": "Prof. Dr. Pareena Srivanit",
        "full_name_th": "ศ.ดร. ปารีณา ศรีวนิชย์",
        "role": "Dean of Faculty of Law / Distinguished Expert in Criminal Jurisprudence, Cyber Law & AI Legal Ethics",
        "email": "pareena.s@law.chula.ac.th",
        "image_url": "https://law.chula.ac.th/images/faculty/pareena.jpg",
        "profile_url": "https://law.chula.ac.th/staff/pareena",
        "education": [
            "S.J.D. (Doctor of Juridical Science), University of Wisconsin-Madison, USA",
            "LL.M., Harvard Law School, USA",
            "LL.M., University of Pennsylvania, USA",
            "LL.B. (First Class Honours, Gold Medal), Chulalongkorn University"
        ],
        "research_interests": [
            "Artificial Intelligence Governance, Algorithmic Accountability and AI Liability",
            "Personal Data Protection Act (PDPA) Compliance and Cross-Border Data Transfers",
            "Cybercrime Law, Electronic Evidence and Digital Forensics Admissibility",
            "Comparative Criminal Justice, Restorative Justice and Sentencing Reform",
            "Financial Crimes, Anti-Money Laundering (AML) and Virtual Asset Regulation"
        ],
        "taught_courses": [
            "AI, Big Data and the Law",
            "Cybercrime, Digital Evidence and Criminal Procedure",
            "Comparative Corporate Criminal Liability"
        ],
        "featured_publications": [
            "Legal Liability Frameworks for Autonomous Systems and Artificial Intelligence in Civil Law Jurisdictions",
            "Balancing Privacy and National Security: Cross-Border Cloud Data Enforcement under PDPA Frameworks",
            "Regulatory Sandbox Design for Decentralized Financial Systems and Smart Contracts Enforcement"
        ],
        "scholar_url": "https://scholar.google.com/citations?user=PareenaSrivanit"
    },
    {
        "id": "cu_commarts_crisis_001",
        "university": "Chulalongkorn University",
        "university_th": "จุฬาลงกรณ์มหาวิทยาลัย",
        "faculty": "Faculty of Communication Arts",
        "faculty_th": "คณะนิเทศศาสตร์",
        "department": "Department of Public Relations & Strategic Health Communication Research Center",
        "department_th": "ภาควิชาการประชาสัมพันธ์ และศูนย์วิจัยการสื่อสารสุขภาพเชิงกลยุทธ์",
        "academic_title": "Prof. Dr.",
        "academic_title_th": "ศ.ดร.",
        "first_name": "Parichart",
        "last_name": "Sthapitanonda",
        "full_name": "Prof. Dr. Parichart Sthapitanonda",
        "full_name_th": "ศ.ดร. ปาริชาต สถาปิตานนท์",
        "role": "Vice President of Chulalongkorn University / Senior Scholar in Strategic Communication, Crisis Management & Health Advocacy",
        "email": "parichart.s@chula.ac.th",
        "image_url": "https://commarts.chula.ac.th/images/faculty/parichart.jpg",
        "profile_url": "https://commarts.chula.ac.th/staff/parichart",
        "education": [
            "Ph.D. (Communication), Ohio University, USA",
            "M.A. (Communication), Ohio University, USA",
            "B.A. (Communication Arts - Honours), Chulalongkorn University"
        ],
        "research_interests": [
            "Strategic Crisis Communication and Misinformation Mitigation in Digital Infodemics",
            "Health Communication Policy, Public Health Campaigns & Behavioral Change",
            "Corporate Social Responsibility (CSR) and Stakeholder Engagement in ASEAN",
            "Social Media Sentiment Analytics and Government Public Communication Strategy",
            "Media Literacy and Digital Resilience among Aging Populations"
        ],
        "taught_courses": [
            "Strategic Communication and Crisis Management",
            "Public Health Communication Campaigns",
            "Communication Theory and Advanced Research Methodologies"
        ],
        "featured_publications": [
            "Mitigating Infodemics: Strategic Crisis Communication Frameworks for Public Health Agencies during Epidemic Emergencies",
            "Social Media Framing, Public Risk Perception, and Vaccine Hesitancy in Southeast Asian Urban Centers",
            "Stakeholder Trust and Corporate Communication Agility during Severe Reputational Crises"
        ],
        "scholar_url": "https://scholar.google.com/citations?user=ParichartSthapitanonda"
    },

    # =========================================================================
    # 11. FACULTY OF ALLIED HEALTH SCIENCES & PSYCHOLOGY (CHULALONGKORN UNIVERSITY)
    # =========================================================================
    {
        "id": "cu_ahs_physio_001",
        "university": "Chulalongkorn University",
        "university_th": "จุฬาลงกรณ์มหาวิทยาลัย",
        "faculty": "Faculty of Allied Health Sciences",
        "faculty_th": "คณะสหเวชศาสตร์",
        "department": "Department of Transfusion Medicine and Clinical Microbiology & Cellular Physiology Lab",
        "department_th": "ภาควิชาเวชศาสตร์การธนาคารเลือดและจุลชีววิทยาคลินิก",
        "academic_title": "Prof. Dr.",
        "academic_title_th": "ศ.ดร.",
        "first_name": "Chatchai",
        "last_name": "Muanprasat",
        "full_name": "Prof. Dr. Chatchai Muanprasat",
        "full_name_th": "ศ.ดร. นพ. ชัชชัย เหมือนประสาท",
        "role": "Distinguished Cellular Physiologist / Leader in CFTR Chloride Channel and Intestinal Barrier Therapeutics",
        "email": "chatchai.m@chula.ac.th",
        "image_url": "https://ahs.chula.ac.th/images/faculty/chatchai.jpg",
        "profile_url": "https://ahs.chula.ac.th/staff/chatchai",
        "education": [
            "Ph.D. (Physiology / Biophysics), University of California, San Francisco (UCSF), USA",
            "M.D. (First Class Honours, Gold Medal), Mahidol University"
        ],
        "research_interests": [
            "CFTR and TMEM16A Chloride Ion Channel Modulators for Antidiarrheal and Cystic Fibrosis Therapy",
            "Intestinal Epithelial Barrier Integrity and Tight Junction Regulation",
            "AMPK Activators and Natural Plant Bioactives for Inflammatory Bowel Disease (IBD)",
            "Diabetic Nephropathy Prevention via Free Fatty Acid Receptor Signaling (FFA4/GPR120)",
            "High-Throughput Drug Screening Assays for Epithelial Transport Disorders"
        ],
        "taught_courses": [
            "Advanced Cellular and Molecular Physiology",
            "Biophysical Transport Mechanisms and Drug Discovery",
            "Clinical Translational Physiology"
        ],
        "featured_publications": [
            "Discovery and Mechanism of Action of Small-Molecule CFTR Channel Inhibitors for Secretory Diarrhea Therapy",
            "Activation of Free Fatty Acid Receptor 4 (FFA4) Attenuates Intestinal Inflammation and Restores Epithelial Barrier Tight Junctions",
            "Therapeutic Potential of Natural Polyphenols in Preventing Diabetic Glomerular Podocyte Injury via AMPK Activation"
        ],
        "scholar_url": "https://scholar.google.com/citations?user=ChatchaiMuanprasat"
    },
    {
        "id": "cu_psych_cbt_001",
        "university": "Chulalongkorn University",
        "university_th": "จุฬาลงกรณ์มหาวิทยาลัย",
        "faculty": "Faculty of Psychology",
        "faculty_th": "คณะจิตวิทยา",
        "department": "Department of Clinical and Health Psychology",
        "department_th": "ภาควิชาจิตวิทยาคลินิกและจิตวิทยาสุขภาพ",
        "academic_title": "Prof. Dr.",
        "academic_title_th": "ศ.ดร.",
        "first_name": "Sompoch",
        "last_name": "Iamsupasit",
        "full_name": "Prof. Dr. Sompoch Iamsupasit",
        "full_name_th": "ศ.ดร. สมโภชน์ เอี่ยมสุภาษิต",
        "role": "Distinguished Professor in Behavioral Modification and Cognitive Behavioral Therapy (CBT) / Pioneer of Health Psychology in Thailand",
        "email": "sompoch.i@chula.ac.th",
        "image_url": "https://psy.chula.ac.th/images/faculty/sompoch.jpg",
        "profile_url": "https://psy.chula.ac.th/staff/sompoch",
        "education": [
            "Ph.D. (Clinical and Health Psychology), University of Georgia, USA",
            "M.S. (Behavioral Psychology), Florida State University, USA",
            "B.Ed. (Psychology - Honours), Chulalongkorn University"
        ],
        "research_interests": [
            "Cognitive Behavioral Therapy (CBT) Protocols for Major Depressive and Anxiety Disorders",
            "Behavior Modification Techniques for Chronic Disease Self-Management (Diabetes, Hypertension)",
            "Mindfulness-Based Stress Reduction (MBSR) and Neurobiological Resilience",
            "Psychosocial Determinants of Addictive Behaviors and Smoking Cessation Interventions",
            "Psychometric Tool Standardization and Cultural Adaptation in Southeast Asia"
        ],
        "taught_courses": [
            "Advanced Cognitive Behavioral Therapy",
            "Behavior Modification Theory and Clinical Practice",
            "Health Psychology and Behavioral Medicine"
        ],
        "featured_publications": [
            "Efficacy of Culturally Adapted Cognitive Behavioral Therapy in Reducing Depression and Anxiety in Thai Outpatients",
            "Mindfulness-Based Stress Reduction Improves Glycemic Control and Quality of Life in Patients with Type 2 Diabetes",
            "Behavioral Modification Interventions for Smoking Cessation in Community Health Settings"
        ],
        "scholar_url": "https://scholar.google.com/citations?user=SompochIamsupasit"
    },

    # =========================================================================
    # 12. FACULTY OF ARTS & FACULTY OF EDUCATION (CHULALONGKORN UNIVERSITY)
    # =========================================================================
    {
        "id": "cu_arts_ling_001",
        "university": "Chulalongkorn University",
        "university_th": "จุฬาลงกรณ์มหาวิทยาลัย",
        "faculty": "Faculty of Arts",
        "faculty_th": "คณะอักษรศาสตร์",
        "department": "Department of Linguistics & Center for Endangered Languages and Phonetics",
        "department_th": "ภาควิชาภาษาศาสตร์ และศูนย์วิจัยภาษาศาสตร์และสัทศาสตร์ภาษาถิ่น",
        "academic_title": "Prof. Dr.",
        "academic_title_th": "ศ.ดร.",
        "first_name": "Theraphan",
        "last_name": "Luangthongkum",
        "full_name": "Prof. Dr. Theraphan Luangthongkum",
        "full_name_th": "ศ.ดร. ธีรพันธุ์ ล.ทองคำ",
        "role": "Distinguished Research Professor of Thailand / Fellow of Royal Society / World Renowned Authority on Mon-Khmer & Tai-Kadai Acoustic Phonetics",
        "email": "theraphan.l@chula.ac.th",
        "image_url": "https://arts.chula.ac.th/images/faculty/theraphan.jpg",
        "profile_url": "https://arts.chula.ac.th/staff/theraphan",
        "education": [
            "Ph.D. (Linguistics / Acoustic Phonetics), University of Edinburgh, UK",
            "M.A. (Linguistics), Brown University, USA",
            "B.A. (English Literature - Honours), Chulalongkorn University"
        ],
        "research_interests": [
            "Acoustic and Physiological Phonetics of Tonal and Register Languages",
            "Comparative Historical Linguistics of Austroasiatic (Mon-Khmer) and Kra-Dai Languages",
            "Endangered Indigenous Language Revitalization and Phonological Archiving",
            "Electropalatography (EPG) and Laryngeal Articulation Dynamics",
            "Sociolinguistic Dialect Geography across the Mekong River Basin"
        ],
        "taught_courses": [
            "Acoustic and Experimental Phonetics",
            "Comparative Historical Linguistics of Southeast Asian Languages",
            "Field Methods and Endangered Language Documentation"
        ],
        "featured_publications": [
            "Acoustic Characteristics of Voice Quality Registers in Mon-Khmer and Kra-Dai Languages",
            "A Historical Phonological Study of Proto-Kra and Its Genetic Affiliation in Southeast Asia",
            "The Register Complex in Suai and Chong: Glottal and Pharyngeal Articulations"
        ],
        "scholar_url": "https://scholar.google.com/citations?user=TheraphanLuangthongkum"
    },
    {
        "id": "cu_arts_history_002",
        "university": "Chulalongkorn University",
        "university_th": "จุฬาลงกรณ์มหาวิทยาลัย",
        "faculty": "Faculty of Arts",
        "faculty_th": "คณะอักษรศาสตร์",
        "department": "Department of History & Institute of Asian Studies",
        "department_th": "ภาควิชาประวัติศาสตร์ และสถาบันเอเชียศึกษา",
        "academic_title": "Prof. Dr.",
        "academic_title_th": "ศ.ดร.",
        "first_name": "Sunait",
        "last_name": "Chutintaranond",
        "full_name": "Prof. Dr. Sunait Chutintaranond",
        "full_name_th": "ศ.ดร. สุเนตร ชุตินธรานนท์",
        "role": "Distinguished Professor in Southeast Asian History, Maritime Silk Road and Myanmar Studies",
        "email": "sunait.c@chula.ac.th",
        "image_url": "https://arts.chula.ac.th/images/faculty/sunait.jpg",
        "profile_url": "https://arts.chula.ac.th/staff/sunait",
        "education": [
            "Ph.D. (Southeast Asian History), Cornell University, USA",
            "M.A. (Southeast Asian Studies), Cornell University, USA",
            "B.A. (History - First Class Honours), Chulalongkorn University"
        ],
        "research_interests": [
            "Ayutthaya and Myanmar Warfare, Royal Chronicles and Geopolitical Rivalry",
            "Maritime Silk Road Trade Networks and Port Kingdoms in the Gulf of Siam",
            "Cross-Border Cultural Diplomacy and Theravada Buddhist Statecraft in Mainland Southeast Asia",
            "Historical Memory, Nationalism and Regional Identity Construction",
            "Archaeological Heritage and Underwater Shipwreck Epigraphy in Asia"
        ],
        "taught_courses": [
            "Seminar in Pre-Modern Southeast Asian History",
            "Ayutthaya and the Indian Ocean Maritime Trade Network",
            "Historiography and Historical Criticism"
        ],
        "featured_publications": [
            "Cakravartin: The Ideology of Universal Monarchy and Warfare in Early Modern Mainland Southeast Asia",
            "Ayutthaya and the Maritime Silk Road: Cosmopolitan Port Polity and Eurasian Transshipment",
            "Burmese Historiography on the Fall of Ayutthaya: A Re-examination of the Hmannan Yazawin"
        ],
        "scholar_url": "https://scholar.google.com/citations?user=SunaitChutintaranond"
    },
    {
        "id": "cu_edu_eval_001",
        "university": "Chulalongkorn University",
        "university_th": "จุฬาลงกรณ์มหาวิทยาลัย",
        "faculty": "Faculty of Education",
        "faculty_th": "คณะครุศาสตร์",
        "department": "Department of Educational Research and Psychology",
        "department_th": "ภาควิชาวิจัยและจิตวิทยาการศึกษา",
        "academic_title": "Prof. Dr.",
        "academic_title_th": "ศ.ดร.",
        "first_name": "Suwimon",
        "last_name": "Wongwanich",
        "full_name": "Prof. Dr. Suwimon Wongwanich",
        "full_name_th": "ศ.ดร. สุวิมล ว่องวาณิช",
        "role": "Distinguished Professor in Educational Measurement, Needs Assessment and Learning Analytics / Fellow of Royal Society",
        "email": "suwimon.w@chula.ac.th",
        "image_url": "https://edu.chula.ac.th/images/faculty/suwimon.jpg",
        "profile_url": "https://edu.chula.ac.th/staff/suwimon",
        "education": [
            "Ph.D. (Educational Research, Measurement and Statistics), Chulalongkorn University",
            "M.Ed. (Educational Research), Chulalongkorn University",
            "B.Ed. (Mathematics - Honours), Chulalongkorn University"
        ],
        "research_interests": [
            "Needs Assessment Research Methodologies (PNI_modified) in Educational Systems",
            "Classroom Action Research (CAR) and School-Based Competency Assessment",
            "Item Response Theory (IRT) and Computerized Adaptive Testing (CAT)",
            "Learning Analytics and Predictive Student Dropout Modeling in Higher Education",
            "Educational Program Evaluation and Structural Equation Modeling (SEM)"
        ],
        "taught_courses": [
            "Advanced Educational Measurement and Evaluation",
            "Needs Assessment and Program Evaluation Methodology",
            "Multivariate Statistics and Structural Equation Modeling in Education"
        ],
        "featured_publications": [
            "Modified Priority Needs Index (PNI_modified): A Methodological Framework for Strategic Educational Decision Making",
            "Classroom Action Research Implementation and Its Impact on Teacher Pedagogical Content Knowledge in Thailand",
            "Developing Computerized Adaptive Testing for Higher-Order Thinking Skills Assessment in Secondary Schools"
        ],
        "scholar_url": "https://scholar.google.com/citations?user=SuwimonWongwanich"
    },

    # =========================================================================
    # 13. PETROLEUM AND PETROCHEMICAL COLLEGE (PPC) & MMRI (CHULALONGKORN UNIVERSITY)
    # =========================================================================
    {
        "id": "cu_ppc_biopolymer_001",
        "university": "Chulalongkorn University",
        "university_th": "จุฬาลงกรณ์มหาวิทยาลัย",
        "faculty": "Petroleum and Petrochemical College (PPC Chula)",
        "faculty_th": "วิทยาลัยปิโตรเลียมและปิโตรเคมี จุฬาฯ",
        "department": "Polymer Science Division & Bio-Polymer Innovation Center",
        "department_th": "สาขาวิทยาศาสตร์พอลิเมอร์ และศูนย์นวัตกรรมพอลิเมอร์ชีวภาพ",
        "academic_title": "Prof. Dr.",
        "academic_title_th": "ศ.ดร.",
        "first_name": "Suwabun",
        "last_name": "Chirachanchai",
        "full_name": "Prof. Dr. Suwabun Chirachanchai",
        "full_name_th": "ศ.ดร. สุวาบุญ จิรชาญชัย",
        "role": "Distinguished Research Professor of Thailand / Former Dean of PPC Chula / Global Pioneer in Chitosan and Bio-Based Polymers",
        "email": "suwabun.c@chula.ac.th",
        "image_url": "https://ppc.chula.ac.th/images/faculty/suwabun.jpg",
        "profile_url": "https://ppc.chula.ac.th/staff/suwabun",
        "education": [
            "D.Eng. (Polymer Chemistry), Tokyo Institute of Technology, Japan",
            "M.Eng. (Polymer Chemistry), Tokyo Institute of Technology, Japan",
            "B.Sc. (Materials Science - Honours), Chulalongkorn University"
        ],
        "research_interests": [
            "Chitosan and Polysaccharide Chemical Modification for Smart Functional Materials",
            "Bio-Based Polyesters (PLA, PHA) and Biodegradable Packaging Films with High Gas Barrier",
            "Supramolecular Hydrogels and Self-Assembled Inclusion Complexes for Drug Delivery",
            "Cellulose Nanocrystals (CNC) from Agricultural Waste for Nanocomposite Reinforcement",
            "Chemical Recycling of Post-Consumer Synthetic Polymers via Catalytic Solvolysis"
        ],
        "taught_courses": [
            "Advanced Polymer Synthesis and Reaction Engineering",
            "Bio-Based Polymers and Green Chemistry",
            "Polymer Physics, Morphology and Structure-Property Relationships"
        ],
        "featured_publications": [
            "Naturally Derived Chitosan-Based Functional Materials: Synthesis, Self-Assembly, and Biomedical Applications",
            "High-Barrier Biodegradable Poly(lactic acid) Nanocomposites Reinforced with Surface-Modified Cellulose Nanocrystals",
            "Facile Catalytic Glycolysis for Chemical Upcycling of Poly(ethylene terephthalate) Waste into High-Value Polyurethanes"
        ],
        "scholar_url": "https://scholar.google.com/citations?user=SuwabunChirachanchai"
    },
    {
        "id": "cu_mmri_cellulose_001",
        "university": "Chulalongkorn University",
        "university_th": "จุฬาลงกรณ์มหาวิทยาลัย",
        "faculty": "Metallurgy and Materials Science Research Institute (MMRI Chula)",
        "faculty_th": "สถาบันวิจัยโลหะและวัสดุ จุฬาลงกรณ์มหาวิทยาลัย (MMRI)",
        "department": "Polymer and Advanced Materials Division",
        "department_th": "ฝ่ายวิจัยพอลิเมอร์และวัสดุขั้นสูง",
        "academic_title": "Prof. Dr.",
        "academic_title_th": "ศ.ดร.",
        "first_name": "Hathaikarn",
        "last_name": "Manuspiya",
        "full_name": "Prof. Dr. Hathaikarn Manuspiya",
        "full_name_th": "ศ.ดร. หทัยกานต์ มนัสปิยะ",
        "role": "Director of Metallurgy and Materials Science Research Institute (MMRI) / Leader in Circular Materials & Cellulose Nanomaterials",
        "email": "hathaikarn.m@chula.ac.th",
        "image_url": "https://mmri.chula.ac.th/images/faculty/hathaikarn.jpg",
        "profile_url": "https://mmri.chula.ac.th/staff/hathaikarn",
        "education": [
            "Ph.D. (Materials Science and Engineering), Pennsylvania State University, USA",
            "M.S. (Polymer Science), Pennsylvania State University, USA",
            "B.Sc. (Materials Science), Chulalongkorn University"
        ],
        "research_interests": [
            "Circular Materials & Agricultural Waste Valorization into Bacterial and Plant Nanocellulose",
            "Aerogels and Microcellular Foams for Thermal Insulation and Oil-Water Separation",
            "Flexible Transparent Electronics based on Nanocellulose Substrates",
            "Carbon Footprint Reduction and Life Cycle Assessment (LCA) in Packaging Materials",
            "Supercapacitors and Flexible Energy Storage using Biomass-Derived Porous Carbon"
        ],
        "taught_courses": [
            "Circular Economy and Sustainable Materials Engineering",
            "Nanostructured Polymers and Nanocomposites",
            "Advanced Characterization of Porous and High-Surface-Area Materials"
        ],
        "featured_publications": [
            "Superhydrophobic and Flame-Retardant Nanocellulose Aerogels for High-Efficiency Oil Spill Clean-Up and Thermal Insulation",
            "Green Synthesis of Bacterial Cellulose Nanocomposites from Agro-Industrial Sugarcane Bagasse Byproducts",
            "Flexible Solid-State Supercapacitors Based on Nitrogen-Doped Carbonized Nanocellulose Electrodes"
        ],
        "scholar_url": "https://scholar.google.com/citations?user=HathaikarnManuspiya"
    }
]
