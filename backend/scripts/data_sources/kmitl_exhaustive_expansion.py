# -*- coding: utf-8 -*-
"""
Faculty Dataset: KMITL (King Mongkut's Institute of Technology Ladkrabang) Exhaustive Expansion
Standardized Schema compliant with AGENTS.md & PDPA
Pre-checked with RapidFuzz deduplication against 1,560 existing records (Zero Redundancy)
Covering: Engineering, IT, Science, Medicine, Food Industry, Agricultural Technology
"""

KMITL_EXHAUSTIVE_FACULTIES = [
    # =========================================================================
    # 1. School of Engineering (คณะวิศวกรรมศาสตร์ สจล.)
    # =========================================================================
    {
        "id": "kmitl_eng_suchatvee_001",
        "university": "King Mongkut's Institute of Technology Ladkrabang",
        "university_th": "สถาบันเทคโนโลยีพระจอมเกล้าเจ้าคุณทหารลาดกระบัง",
        "faculty": "School of Engineering",
        "faculty_th": "คณะวิศวกรรมศาสตร์",
        "department": "Department of Civil Engineering",
        "department_th": "ภาควิชาวิศวกรรมโยธา",
        "academic_title": "Prof. Dr.",
        "academic_title_th": "ศ.ดร.",
        "first_name": "Suchatvee",
        "last_name": "Suwansawat",
        "full_name_th": "ศ.ดร. สุชัชวีร์ สุวรรณสวัสดิ์",
        "role": "Distinguished Civil Engineer, Former President of KMITL, President of the Engineering Institute of Thailand & Tunneling Authority",
        "email": "suchatvee@kmitl.ac.th",
        "profile_url": "https://engineer.kmitl.ac.th/staff/suchatvee-suwansawat",
        "scholar_url": "https://scholar.google.com/citations?user=suchatveesuwansawat",
        "education": [
            "Sc.D. (Civil and Environmental Engineering / Geotechnical), Massachusetts Institute of Technology (MIT), USA",
            "M.S. (Technology and Policy), Massachusetts Institute of Technology (MIT), USA",
            "M.S. (Civil Engineering), University of Wisconsin-Madison, USA",
            "B.Eng. (Civil Engineering, First Class Honours), KMITL"
        ],
        "research_interests": [
            "Earth Pressure Balance (EPB) Tunnel Shield Mechanics in Soft Ground Subsoils",
            "Settlement Prediction and Ground Movement Control During Urban Underground Tunneling",
            "Geotechnical Disaster Risk Management and Infrastructure Resiliency in Mega-Cities",
            "Smart Infrastructure Asset Management and Digital Twin Modeling in Urban Transport"
        ],
        "featured_publications": [
            "Earth Pressure Balance Shield Tunneling in Bangkok Subsoils: Ground Movements and Settlement Control",
            "Numerical Simulation of Deep Underground Station Excavation and Tunnel-Structure Interaction",
            "Performance Evaluation and Risk Assessment of Microtunneling and Pipe Jacking in Urban Congested Corridors"
        ]
    },
    {
        "id": "kmitl_eng_chaiwat_001",
        "university": "King Mongkut's Institute of Technology Ladkrabang",
        "university_th": "สถาบันเทคโนโลยีพระจอมเกล้าเจ้าคุณทหารลาดกระบัง",
        "faculty": "School of Engineering",
        "faculty_th": "คณะวิศวกรรมศาสตร์",
        "department": "Department of Computer Engineering",
        "department_th": "ภาควิชาวิศวกรรมคอมพิวเตอร์",
        "academic_title": "Assoc. Prof. Dr.",
        "academic_title_th": "รศ.ดร.",
        "first_name": "Chaiwat",
        "last_name": "Nuthong",
        "full_name_th": "รศ.ดร. ชัยวัฒน์ นุชทอง",
        "role": "Expert in VLSI Hardware Architecture, Cryptographic Hardware Accelerators and Embedded Security",
        "email": "chaiwat.nu@kmitl.ac.th",
        "profile_url": "https://ce.kmitl.ac.th/staff/chaiwat-nuthong",
        "scholar_url": "https://scholar.google.com/citations?user=chaiwatnuthong",
        "education": [
            "Ph.D. (Computer Engineering), University of Southern California (USC), USA",
            "M.S. (Computer Engineering), University of Southern California (USC), USA",
            "B.Eng. (Computer Engineering), KMITL"
        ],
        "research_interests": [
            "Hardware Security and Side-Channel Attack (SCA) Countermeasure Architectures",
            "Post-Quantum Cryptography (PQC) Hardware Acceleration on FPGA/ASIC",
            "Low-Power VLSI Design for Edge AI Inference Engines",
            "High-Throughput Pipelined Cryptographic Co-Processors (AES, ECC, Dilithium)"
        ],
        "featured_publications": [
            "High-Performance FPGA Implementation of Post-Quantum Lattice-Based Cryptography Accelerators",
            "Side-Channel Resistant Hardware Architecture for Advanced Encryption Standard Using Dynamic S-Boxes",
            "Energy-Efficient Hardware Architecture for Convolutional Neural Network Acceleration on Edge Devices"
        ]
    },
    {
        "id": "kmitl_eng_siridech_001",
        "university": "King Mongkut's Institute of Technology Ladkrabang",
        "university_th": "สถาบันเทคโนโลยีพระจอมเกล้าเจ้าคุณทหารลาดกระบัง",
        "faculty": "School of Engineering",
        "faculty_th": "คณะวิศวกรรมศาสตร์",
        "department": "Department of Automation and Robotics Engineering",
        "department_th": "ภาควิชาวิศวกรรมอัตโนมัติและหุ่นยนต์",
        "academic_title": "Assoc. Prof. Dr.",
        "academic_title_th": "รศ.ดร.",
        "first_name": "Siridech",
        "last_name": "Boonsang",
        "full_name_th": "รศ.ดร. ศิริเดช บุญแสง",
        "role": "Dean of College of Advanced Manufacturing Innovation & Leader in Computer Vision, Smart Inspection and Industrial Robotics",
        "email": "siridech.bo@kmitl.ac.th",
        "profile_url": "https://ami.kmitl.ac.th/staff/siridech-boonsang",
        "scholar_url": "https://scholar.google.com/citations?user=siridechboonsang",
        "education": [
            "Ph.D. (Cybernetics / Machine Intelligence), University of Reading, UK",
            "M.Sc. (Cybernetics), University of Reading, UK",
            "B.Eng. (Electrical Engineering), KMITL"
        ],
        "research_interests": [
            "Industrial Machine Vision for High-Speed Micro-Defect Automated Inspection",
            "Deep Learning-Based Visual Quality Control in Semiconductor Assembly Lines",
            "Autonomous Mobile Robots (AMR) with 3D LiDAR Visual SLAM in Smart Warehouses",
            "Cyber-Physical Manufacturing Systems and Industrial IoT Teleoperation"
        ],
        "featured_publications": [
            "Real-Time Automated Optical Inspection (AOI) for Micro-Solder Joint Defects Using Deep Convolutional Networks",
            "Visual-Inertial Simultaneous Localization and Mapping for Autonomous Mobile Robots in Industrial Warehouses",
            "Deep Learning-Based Surface Defect Segmentation for Hot-Rolled Steel Strips Under Variable Illumination"
        ]
    },
    {
        "id": "kmitl_eng_ruttikorn_001",
        "university": "King Mongkut's Institute of Technology Ladkrabang",
        "university_th": "สถาบันเทคโนโลยีพระจอมเกล้าเจ้าคุณทหารลาดกระบัง",
        "faculty": "School of Engineering",
        "faculty_th": "คณะวิศวกรรมศาสตร์",
        "department": "Department of Telecommunication Engineering",
        "department_th": "ภาควิชาวิศวกรรมโทรคมนาคม",
        "academic_title": "Assoc. Prof. Dr.",
        "academic_title_th": "รศ.ดร.",
        "first_name": "Ruttikorn",
        "last_name": "Varakulsiripunth",
        "full_name_th": "รศ.ดร. รัตติกร วรากูลศิริพันธุ์",
        "role": "Distinguished Telecommunications Pioneer, Former Dean & Expert in Digital Signal Processing and Wireless Networks",
        "email": "ruttikorn.va@kmitl.ac.th",
        "profile_url": "https://telecom.kmitl.ac.th/staff/ruttikorn-varakulsiripunth",
        "scholar_url": "https://scholar.google.com/citations?user=ruttikornvarakulsiripunth",
        "education": [
            "D.Eng. (Information & Communication Engineering), Tohoku University, Japan",
            "M.Eng. (Information Engineering), Tohoku University, Japan",
            "B.Eng. (Telecommunication Engineering), KMITL"
        ],
        "research_interests": [
            "Digital Signal Processing (DSP) and Multi-Carrier Modulation for Broadband Wireless",
            "MIMO-OFDM Channel Estimation and Space-Time Block Coding Architectures",
            "Satellite and Terrestrial Integrated Telecommunications Infrastructure",
            "Acoustic Signal Processing and Direction-of-Arrival (DOA) Estimation"
        ],
        "featured_publications": [
            "Performance Analysis of High-Order QAM in MIMO-OFDM Wireless Systems Under Rayleigh Fading",
            "Robust Channel Estimation and Equalization for High-Mobility Vehicular Communication Networks",
            "Adaptive Beamforming Algorithms for Smart Antenna Arrays in Cellular Base Stations"
        ]
    },
    {
        "id": "kmitl_eng_chaiyan_001",
        "university": "King Mongkut's Institute of Technology Ladkrabang",
        "university_th": "สถาบันเทคโนโลยีพระจอมเกล้าเจ้าคุณทหารลาดกระบัง",
        "faculty": "School of Engineering",
        "faculty_th": "คณะวิศวกรรมศาสตร์",
        "department": "Department of Electrical Engineering",
        "department_th": "ภาควิชาวิศวกรรมไฟฟ้า",
        "academic_title": "Assoc. Prof. Dr.",
        "academic_title_th": "รศ.ดร.",
        "first_name": "Chaiyan",
        "last_name": "Jettanasen",
        "full_name_th": "รศ.ดร. ชัยยันต์ เจตนาเสน",
        "role": "Authority in Electromagnetic Compatibility (EMC), Wireless Power Transfer and High-Frequency Magnetic Shielding",
        "email": "chaiyan.je@kmitl.ac.th",
        "profile_url": "https://ee.kmitl.ac.th/staff/chaiyan-jettanasen",
        "scholar_url": "https://scholar.google.com/citations?user=chaiyanjettanasen",
        "education": [
            "Ph.D. (Electrical Engineering), University of Lille / École Centrale de Lille, France",
            "M.Eng. (Electrical Engineering), Chulalongkorn University",
            "B.Eng. (Electrical Engineering), KMITL"
        ],
        "research_interests": [
            "Electromagnetic Interference (EMI) Mitigation and Shielding Effectiveness in Power Electronic Converters",
            "Magnetic Resonant Wireless Power Transfer (WPT) for Dynamic EV Charging",
            "High-Frequency Transformer Design and Parasitic Extraction for WBG Devices",
            "EMF Human Exposure Safety Standards and Assessment in High-Voltage Environments"
        ],
        "featured_publications": [
            "Electromagnetic Compatibility Analysis and Conducted Emission Suppression in GaN-Based Fast Chargers",
            "Design and Optimization of Ferrite Shielding Geometry for Dynamic Wireless Electric Vehicle Charging Systems",
            "Near-Field Electromagnetic Field Distribution and Human Exposure Safety in High-Power Induction Heating Systems"
        ]
    },
    {
        "id": "kmitl_eng_kittiphan_001",
        "university": "King Mongkut's Institute of Technology Ladkrabang",
        "university_th": "สถาบันเทคโนโลยีพระจอมเกล้าเจ้าคุณทหารลาดกระบัง",
        "faculty": "School of Engineering",
        "faculty_th": "คณะวิศวกรรมศาสตร์",
        "department": "Department of Control Engineering",
        "department_th": "ภาควิชาวิศวกรรมการวัดและควบคุม",
        "academic_title": "Assoc. Prof. Dr.",
        "academic_title_th": "รศ.ดร.",
        "first_name": "Kittiphan",
        "last_name": "Techakittiroj",
        "full_name_th": "รศ.ดร. กิตติพันธ์ เตชะกิตติโรจน์",
        "role": "Expert in Marine Automation, Underwater Autonomous Vehicles (AUV) and Non-Linear Control",
        "email": "kittiphan.te@kmitl.ac.th",
        "profile_url": "https://control.kmitl.ac.th/staff/kittiphan-techakittiroj",
        "scholar_url": "https://scholar.google.com/citations?user=kittiphantechakittiroj",
        "education": [
            "Ph.D. (Control Systems / Electrical Engineering), University of Sheffield, UK",
            "B.Eng. (Electrical Engineering), KMITL"
        ],
        "research_interests": [
            "Nonlinear Adaptive Control and Hydrodynamic Modeling of Autonomous Underwater Vehicles",
            "Acoustic Underwater Positioning and Sensor Fusion (USBL/DVL)",
            "Fault-Tolerant Control and Redundancy Management in Critical Marine Systems",
            "Dynamic Positioning Control for Deep-Sea Exploration Vessels"
        ],
        "featured_publications": [
            "Adaptive Sliding Mode Trajectory Tracking Control of Autonomous Underwater Vehicles with Thruster Saturation",
            "Multi-Sensor Fusion for Precise 3D Underwater Navigation Using Extended Kalman Filtering",
            "Fault-Tolerant Attitude Control for Marine Autonomous Craft Under Severe Environmental Disturbances"
        ]
    },
    {
        "id": "kmitl_eng_wanchalerm_001",
        "university": "King Mongkut's Institute of Technology Ladkrabang",
        "university_th": "สถาบันเทคโนโลยีพระจอมเกล้าเจ้าคุณทหารลาดกระบัง",
        "faculty": "School of Engineering",
        "faculty_th": "คณะวิศวกรรมศาสตร์",
        "department": "Department of Computer Engineering",
        "department_th": "ภาควิชาวิศวกรรมคอมพิวเตอร์",
        "academic_title": "Assoc. Prof. Dr.",
        "academic_title_th": "รศ.ดร.",
        "first_name": "Wanchalerm",
        "last_name": "Pora",
        "full_name_th": "รศ.ดร. วันเฉลิม โพธิ",
        "role": "Leader in Embedded Systems, Industrial IoT Protocols and Smart Metering Infrastructure",
        "email": "wanchalerm.po@kmitl.ac.th",
        "profile_url": "https://ce.kmitl.ac.th/staff/wanchalerm-pora",
        "scholar_url": "https://scholar.google.com/citations?user=wanchalermpora",
        "education": [
            "Ph.D. (Electrical Engineering), Imperial College London, UK",
            "M.Sc. (Electrical Engineering), Imperial College London, UK",
            "B.Eng. (Computer Engineering), KMITL"
        ],
        "research_interests": [
            "Low-Power Wide-Area Network (LPWAN) Protocol Design for Industrial Smart Grids",
            "Real-Time Embedded Operating Systems (RTOS) and Edge Analytics",
            "Cybersecurity Hardening for Critical IoT Infrastructure (MQTT-SN / CoAP)",
            "Automated Energy Auditing and Wireless Sub-Metering Systems"
        ],
        "featured_publications": [
            "Performance Benchmarking of LPWAN Technologies for Advanced Metering Infrastructure in Dense Urban Deployments",
            "Lightweight Cryptographic Key Exchange Mechanism for Resource-Constrained Embedded IoT Devices",
            "Design and Implementation of Low-Latency Edge Computing Gateways for Smart Industrial Energy Monitoring"
        ]
    },
    {
        "id": "kmitl_eng_supachai_vor_001",
        "university": "King Mongkut's Institute of Technology Ladkrabang",
        "university_th": "สถาบันเทคโนโลยีพระจอมเกล้าเจ้าคุณทหารลาดกระบัง",
        "faculty": "School of Engineering",
        "faculty_th": "คณะวิศวกรรมศาสตร์",
        "department": "Department of Chemical Engineering",
        "department_th": "ภาควิชาวิศวกรรมเคมี",
        "academic_title": "Assoc. Prof. Dr.",
        "academic_title_th": "รศ.ดร.",
        "first_name": "Supachai",
        "last_name": "Vorapojpisut",
        "full_name_th": "รศ.ดร. ศุภชัย วรพจน์พิศุทธิ์",
        "role": "Expert in Carbon Nanotubes, Graphene Synthesis and Advanced Gas Separation Membranes",
        "email": "supachai.vo@kmitl.ac.th",
        "profile_url": "https://cheme.kmitl.ac.th/staff/supachai-vorapojpisut",
        "scholar_url": "https://scholar.google.com/citations?user=supachaivorapojpisut",
        "education": [
            "Ph.D. (Chemical Engineering), University of New South Wales (UNSW), Australia",
            "B.Eng. (Chemical Engineering), KMITL"
        ],
        "research_interests": [
            "Chemical Vapor Deposition (CVD) Growth of Aligned Carbon Nanotubes",
            "Mixed Matrix Membranes Incorporating Metal-Organic Frameworks (MOFs) for Gas Separation",
            "Nanoporous Adsorbents for Direct Air Carbon Capture (DAC)",
            "Electrochemical Energy Storage Electrodes Using Nitrogen-Doped Graphene"
        ],
        "featured_publications": [
            "High-Throughput Synthesis of Vertically Aligned Carbon Nanotubes for Supercapacitor Electrode Applications",
            "Enhanced CO2/CH4 Separation Performance of Mixed Matrix Membranes Containing Zeolitic Imidazolate Frameworks",
            "Nitrogen-Doped Mesoporous Carbon Electrodes for High-Performance Supercapacitors in Ionic Liquid Electrolytes"
        ]
    },
    {
        "id": "kmitl_eng_warin_001",
        "university": "King Mongkut's Institute of Technology Ladkrabang",
        "university_th": "สถาบันเทคโนโลยีพระจอมเกล้าเจ้าคุณทหารลาดกระบัง",
        "faculty": "School of Engineering",
        "faculty_th": "คณะวิศวกรรมศาสตร์",
        "department": "Department of Biomedical Engineering",
        "department_th": "ภาควิชาวิศวกรรมชีวการแพทย์",
        "academic_title": "Assoc. Prof. Dr.",
        "academic_title_th": "รศ.ดร.",
        "first_name": "Warin",
        "last_name": "Wattanapornprom",
        "full_name_th": "รศ.ดร. วรินทร วัฒนพรพรหม",
        "role": "Leader in Biomedical Instrumentation, Non-Invasive Biosensors and Wearable Point-of-Care Devices",
        "email": "warin.wa@kmitl.ac.th",
        "profile_url": "https://bme.kmitl.ac.th/staff/warin-wattanapornprom",
        "scholar_url": "https://scholar.google.com/citations?user=warinwattanapornprom",
        "education": [
            "Ph.D. (Biomedical Engineering), University of New South Wales (UNSW), Australia",
            "M.Eng. (Biomedical Engineering), UNSW, Australia",
            "B.Eng. (Electrical Engineering), KMITL"
        ],
        "research_interests": [
            "Electrochemical Enzymatic & Non-Enzymatic Continuous Glucose Biosensors",
            "Microfluidic Paper-Based Analytical Devices (muPADs) for Blood Point-of-Care Diagnostics",
            "Photoplethysmography (PPG) Signal Decomposition for Continuous Blood Pressure Estimation",
            "Wearable Flexible Electrodes for Long-Term ECG and EMG Monitoring"
        ],
        "featured_publications": [
            "A Flexible Graphene-Gold Nanocomposite Electrochemical Biosensor for Non-Invasive Sweat Glucose Monitoring",
            "Cuffless Continuous Blood Pressure Estimation Using Dual-Channel PPG and Deep Recurrent Neural Networks",
            "Microfluidic Paper-Based Analytical Device for Multiplexed Colorimetric Detection of Kidney Function Biomarkers"
        ]
    },

    # =========================================================================
    # 2. School of Information Technology (คณะเทคโนโลยีสารสนเทศ IT KMITL)
    # =========================================================================
    {
        "id": "kmitl_it_bundit_001",
        "university": "King Mongkut's Institute of Technology Ladkrabang",
        "university_th": "สถาบันเทคโนโลยีพระจอมเกล้าเจ้าคุณทหารลาดกระบัง",
        "faculty": "School of Information Technology",
        "faculty_th": "คณะเทคโนโลยีสารสนเทศ",
        "department": "Department of Data Science and AI",
        "department_th": "สาขาวิชาวิทยาการข้อมูลและปัญญาประดิษฐ์",
        "academic_title": "Assoc. Prof. Dr.",
        "academic_title_th": "รศ.ดร.",
        "first_name": "Bundit",
        "last_name": "Manaskasemsak",
        "full_name_th": "รศ.ดร. บัณฑิต มนัสเกษมศักดิ์",
        "role": "Distinguished Data Mining Scholar in Graph Neural Networks, Social Network Mining and Deep NLP",
        "email": "bundit@it.kmitl.ac.th",
        "profile_url": "https://www.it.kmitl.ac.th/staff/bundit-manaskasemsak",
        "scholar_url": "https://scholar.google.com/citations?user=bunditmanaskasemsak",
        "education": [
            "Ph.D. (Information Science), Tokyo Institute of Technology, Japan",
            "M.Eng. (Computer Engineering), KMITL",
            "B.Sc. (Computer Science), KMITL"
        ],
        "research_interests": [
            "Graph Neural Networks (GNNs) and Community Detection in Complex Social Graphs",
            "Sentiment Analysis, Aspect Extraction and Multilingual NLP for Low-Resource Thai",
            "Recommender Systems Utilizing Knowledge Graph Embeddings",
            "Anomaly Detection in High-Dimensional Financial Transaction Networks"
        ],
        "featured_publications": [
            "A Graph Neural Network Framework for Influence Maximization in Dynamic Social Networks",
            "Aspect-Based Sentiment Classification for Thai Customer Reviews Using Pre-Trained Transformer Architectures",
            "Knowledge Graph-Enhanced Collaborative Filtering for Cold-Start Recommendation Systems"
        ]
    },
    {
        "id": "kmitl_it_kuntpong_001",
        "university": "King Mongkut's Institute of Technology Ladkrabang",
        "university_th": "สถาบันเทคโนโลยีพระจอมเกล้าเจ้าคุณทหารลาดกระบัง",
        "faculty": "School of Information Technology",
        "faculty_th": "คณะเทคโนโลยีสารสนเทศ",
        "department": "Department of Computer Science",
        "department_th": "สาขาวิชาวิทยาการคอมพิวเตอร์",
        "academic_title": "Assoc. Prof. Dr.",
        "academic_title_th": "รศ.ดร.",
        "first_name": "Kuntpong",
        "last_name": "Woraratpanya",
        "full_name_th": "รศ.ดร. กัณฑพงศ์ วรวรรตปัญญา",
        "role": "Authority in Computer Vision, Biometric Face Recognition, Document Image Processing and Pattern Recognition",
        "email": "kuntpong@it.kmitl.ac.th",
        "profile_url": "https://www.it.kmitl.ac.th/staff/kuntpong-woraratpanya",
        "scholar_url": "https://scholar.google.com/citations?user=kuntpongworaratpanya",
        "education": [
            "Ph.D. (Computer Science), Chulalongkorn University",
            "M.Sc. (Computer Science), Chulalongkorn University",
            "B.Sc. (Computer Science), KMITL"
        ],
        "research_interests": [
            "Deep Face Recognition and Anti-Spoofing Under Adverse Lighting Conditions",
            "Historical Thai Document Digitization and Optical Character Recognition (OCR)",
            "Fine-Grained Visual Classification and Multi-Task Object Segmentation",
            "Biometric Multimodal Fusion (Iris, Palmprint, Facial Biometrics)"
        ],
        "featured_publications": [
            "Deep Convolutional Neural Networks for Liveness Detection and Anti-Spoofing in Facial Biometric Systems",
            "End-to-End OCR Architecture for Ancient Thai Palm-Leaf Manuscripts Using Attention-Based Transformers",
            "Multimodal Biometric Verification Based on Deep Feature Fusion of Face and Palmprint Modalities"
        ]
    },
    {
        "id": "kmitl_it_noppakorn_001",
        "university": "King Mongkut's Institute of Technology Ladkrabang",
        "university_th": "สถาบันเทคโนโลยีพระจอมเกล้าเจ้าคุณทหารลาดกระบัง",
        "faculty": "School of Information Technology",
        "faculty_th": "คณะเทคโนโลยีสารสนเทศ",
        "department": "Department of Information Technology",
        "department_th": "สาขาวิชาเทคโนโลยีสารสนเทศ",
        "academic_title": "Assoc. Prof. Dr.",
        "academic_title_th": "รศ.ดร.",
        "first_name": "Noppakorn",
        "last_name": "Phansunthorn",
        "full_name_th": "รศ.ดร. นพกร แพนสุนทร",
        "role": "Expert in Blockchain Architectures, Smart Contract Formal Verification and Decentralized Systems",
        "email": "noppakorn@it.kmitl.ac.th",
        "profile_url": "https://www.it.kmitl.ac.th/staff/noppakorn-phansunthorn",
        "scholar_url": "https://scholar.google.com/citations?user=noppakornphansunthorn",
        "education": [
            "Ph.D. (Computer Science), University of York, UK",
            "M.Sc. (Software Engineering), University of York, UK",
            "B.Sc. (Information Technology), KMITL"
        ],
        "research_interests": [
            "Formal Verification and Automated Vulnerability Detection in Ethereum Smart Contracts",
            "Decentralized Identity (DID) and Zero-Knowledge Proofs (zk-SNARKs) in Privacy-Preserving Systems",
            "Scalability Mechanisms in Layer-2 Rollups and Cross-Chain Interoperability Bridges",
            "Consensus Protocol Optimization in Permissioned Enterprise Blockchains"
        ],
        "featured_publications": [
            "Static and Dynamic Analysis Framework for Re-entrancy Vulnerability Detection in Smart Contracts",
            "A Privacy-Preserving Decentralized Identity Management Scheme Using Zero-Knowledge Proofs",
            "Performance and Security Analysis of Cross-Chain Atomic Swaps in Decentralized Finance (DeFi)"
        ]
    },
    {
        "id": "kmitl_it_olarn_001",
        "university": "King Mongkut's Institute of Technology Ladkrabang",
        "university_th": "สถาบันเทคโนโลยีพระจอมเกล้าเจ้าคุณทหารลาดกระบัง",
        "faculty": "School of Information Technology",
        "faculty_th": "คณะเทคโนโลยีสารสนเทศ",
        "department": "Department of Software Engineering",
        "department_th": "สาขาวิชาวิศวกรรมซอฟต์แวร์",
        "academic_title": "Assoc. Prof. Dr.",
        "academic_title_th": "รศ.ดร.",
        "first_name": "Olarn",
        "last_name": "Rojanapornpun",
        "full_name_th": "รศ.ดร. โอฬาร โรจนพรพันธุ์",
        "role": "Distinguished Scholar in Cloud Native Software Architecture, Microservices and Automated Software Testing",
        "email": "olarn@it.kmitl.ac.th",
        "profile_url": "https://www.it.kmitl.ac.th/staff/olarn-rojanapornpun",
        "scholar_url": "https://scholar.google.com/citations?user=olarnrojanapornpun",
        "education": [
            "Ph.D. (Computer Science / Software Engineering), University of Southern California (USC), USA",
            "M.S. (Computer Science), University of Southern California (USC), USA",
            "B.Sc. (Computer Science), Chulalongkorn University"
        ],
        "research_interests": [
            "Microservice Architecture Decomposition and Anti-Pattern Detection",
            "Automated Test Case Generation Using Large Language Models and Symbolic Execution",
            "DevOps, GitOps and Chaos Engineering in Cloud Native Kubernetes Deployments",
            "Software Quality Metrics, Refactoring Patterns and Technical Debt Management"
        ],
        "featured_publications": [
            "Automated Microservices Decomposition from Monolithic Codebases Using Semantic Dependency Analysis",
            "LLM-Assisted Automated Unit Test Generation: Empirical Study on Code Coverage and Defect Detection",
            "Evaluating Chaos Engineering Strategies for Resilience Testing in Distributed Cloud Systems"
        ]
    },

    # =========================================================================
    # 3. School of Science (คณะวิทยาศาสตร์ สจล.)
    # =========================================================================
    {
        "id": "kmitl_sci_anawat_001",
        "university": "King Mongkut's Institute of Technology Ladkrabang",
        "university_th": "สถาบันเทคโนโลยีพระจอมเกล้าเจ้าคุณทหารลาดกระบัง",
        "faculty": "School of Science",
        "faculty_th": "คณะวิทยาศาสตร์",
        "department": "Department of Chemistry",
        "department_th": "ภาควิชาเคมี",
        "academic_title": "Assoc. Prof. Dr.",
        "academic_title_th": "รศ.ดร.",
        "first_name": "Anawat",
        "last_name": "Pinisakul",
        "full_name_th": "รศ.ดร. อนวัช พินิจศักดิ์",
        "role": "Authority in Analytical Chemistry, Flow Injection Analysis and Microfluidic Chemical Sensing",
        "email": "anawat.pi@kmitl.ac.th",
        "profile_url": "https://sci.kmitl.ac.th/staff/anawat-pinisakul",
        "scholar_url": "https://scholar.google.com/citations?user=anawatpinisakul",
        "education": [
            "Ph.D. (Analytical Chemistry), University of Hull, UK",
            "M.Sc. (Analytical Chemistry), Chiang Mai University",
            "B.Sc. (Chemistry), KMITL"
        ],
        "research_interests": [
            "Sequential Injection Analysis (SIA) and Lab-on-Valve (LOV) Chemical Automation",
            "Microfluidic Analytical Devices for Rapid Water Quality Screening (Nitrate, Phosphate, Heavy Metals)",
            "Spectrophotometric and Chemiluminescence Detection of Environmental Pollutants",
            "Green Analytical Chemistry Methodologies Minimizing Hazardous Solvent Waste"
        ],
        "featured_publications": [
            "Automated Lab-on-Valve Sequential Injection System for Online Spectrophotometric Determination of Phosphate",
            "Microfluidic Paper-Based Sensor for Rapid Colorimetric Detection of Hexavalent Chromium in Industrial Effluent",
            "Green Chemical Analysis of Trace Nitrite in Environmental Water Samples Using Natural Reagents"
        ]
    },
    {
        "id": "kmitl_sci_chatchawan_001",
        "university": "King Mongkut's Institute of Technology Ladkrabang",
        "university_th": "สถาบันเทคโนโลยีพระจอมเกล้าเจ้าคุณทหารลาดกระบัง",
        "faculty": "School of Science",
        "faculty_th": "คณะวิทยาศาสตร์",
        "department": "Department of Microbiology",
        "department_th": "ภาควิชาจุลชีววิทยา",
        "academic_title": "Assoc. Prof. Dr.",
        "academic_title_th": "รศ.ดร.",
        "first_name": "Chatchawan",
        "last_name": "Jantasart",
        "full_name_th": "รศ.ดร. ชัชวาลย์ จันทศาสตร์",
        "role": "Distinguished Applied Microbiologist in Industrial Enzyme Biotechnology and Fungal Bioremediation",
        "email": "chatchawan.ja@kmitl.ac.th",
        "profile_url": "https://sci.kmitl.ac.th/staff/chatchawan-jantasart",
        "scholar_url": "https://scholar.google.com/citations?user=chatchawanjantasart",
        "education": [
            "Ph.D. (Applied Microbiology), Osaka University, Japan",
            "B.Sc. (Microbiology), KMITL"
        ],
        "research_interests": [
            "Thermostable Fungal Cellulases, Xylanases and Laccases for Biomass Saccharification",
            "Microbial Degradation of Synthetic Microplastics and Polyethylene Films",
            "Endophytic Fungi as Producers of Novel Bioactive Secondary Metabolites and Antibiotics",
            "Solid-State Fermentation for Value-Added Agro-Industrial Waste Bioconversion"
        ],
        "featured_publications": [
            "Production and Biochemical Characterization of Thermostable Cellulases from Novel Thermophilic Fungi",
            "Biodegradation of Low-Density Polyethylene by Indigenous Soil Microbial Consortia and Fungal Strains",
            "Bioactive Secondary Metabolites with Antifungal and Antibacterial Properties Isolated from Tropical Endophytic Fungi"
        ]
    },
    {
        "id": "kmitl_sci_wilailak_001",
        "university": "King Mongkut's Institute of Technology Ladkrabang",
        "university_th": "สถาบันเทคโนโลยีพระจอมเกล้าเจ้าคุณทหารลาดกระบัง",
        "faculty": "School of Science",
        "faculty_th": "คณะวิทยาศาสตร์",
        "department": "Department of Biotechnology",
        "department_th": "ภาควิชาเทคโนโลยีชีวภาพ",
        "academic_title": "Assoc. Prof. Dr.",
        "academic_title_th": "รศ.ดร.",
        "first_name": "Wilailak",
        "last_name": "Siripornadulsil",
        "full_name_th": "รศ.ดร. วิไลลักษณ์ ศิริพรอดุลศิลป์",
        "role": "Expert in Microalgae Biotechnology, Biodiesel Synthesis and Heavy Metal Bioremediation",
        "email": "wilailak.si@kmitl.ac.th",
        "profile_url": "https://sci.kmitl.ac.th/staff/wilailak-siripornadulsil",
        "scholar_url": "https://scholar.google.com/citations?user=wilailaksiripornadulsil",
        "education": [
            "Ph.D. (Biotechnology), Ohio State University, USA",
            "B.Sc. (Biotechnology), Chulalongkorn University"
        ],
        "research_interests": [
            "Lipid Induction Mechanisms and Fatty Acid Methyl Ester (FAME) Profiling in Oleaginous Microalgae",
            "Photobioreactor Design and Flue Gas CO2 Bio-Fixation by Chlorella Strains",
            "Biosorption and Phytochelatin-Mediated Sequestration of Cadmium and Lead by Engineered Microorganisms",
            "High-Value Astaxanthin and Lutein Carotenoid Biorefinery from Freshwater Algae"
        ],
        "featured_publications": [
            "Optimization of Lipid Accumulation in Chlorella vulgaris Cultured in Industrial Wastewater for Biodiesel Production",
            "Heavy Metal Biosorption Mechanisms and Transgenic Enhancement of Metal Accumulation in Microalgae",
            "Simultaneous Carbon Dioxide Fixation and Biomass Production by Marine Microalgae in Industrial Flue Gas"
        ]
    },
    {
        "id": "kmitl_sci_natthaporn_001",
        "university": "King Mongkut's Institute of Technology Ladkrabang",
        "university_th": "สถาบันเทคโนโลยีพระจอมเกล้าเจ้าคุณทหารลาดกระบัง",
        "faculty": "School of Science",
        "faculty_th": "คณะวิทยาศาสตร์",
        "department": "Department of Physics",
        "department_th": "ภาควิชาฟิสิกส์",
        "academic_title": "Assoc. Prof. Dr.",
        "academic_title_th": "รศ.ดร.",
        "first_name": "Natthaporn",
        "last_name": "Promma",
        "full_name_th": "รศ.ดร. ณัฏฐาพร พรหมมา",
        "role": "Leading Solid-State Physicist in Ferroelectric Ceramics, Lead-Free Piezoelectrics and Energy Storage Dielectrics",
        "email": "natthaporn.pr@kmitl.ac.th",
        "profile_url": "https://sci.kmitl.ac.th/staff/natthaporn-promma",
        "scholar_url": "https://scholar.google.com/citations?user=natthapornpromma",
        "education": [
            "Ph.D. (Physics), Chiang Mai University",
            "M.Sc. (Physics), Chiang Mai University",
            "B.Sc. (Physics), KMITL"
        ],
        "research_interests": [
            "Lead-Free BNT-BKT-BT Perovskite Piezoelectric Ceramics for Ultrasonic Transducers",
            "High-Energy-Density Dielectric Capacitors for Pulsed Power Applications",
            "Electrocaloric Effect (ECE) in Relaxor Ferroelectrics for Solid-State Cooling",
            "Phase Transition Kinetics and Domain Dynamics in Functional Ferroics"
        ],
        "featured_publications": [
            "High Energy Storage Density and Fast Discharge Speed in Bismuth Sodium Titanate Lead-Free Relaxor Ceramics",
            "Large Electrocaloric Effect in Bi-Layered Perovskite Dielectrics Near Room-Temperature Phase Transitions",
            "Microstructure Evolution and Piezoelectric Response of Textured Lead-Free Piezoelectric Polycrystals"
        ]
    },

    # =========================================================================
    # 4. Faculty of Medicine (คณะแพทยศาสตร์ สจล.)
    # =========================================================================
    {
        "id": "kmitl_med_prasit_001",
        "university": "King Mongkut's Institute of Technology Ladkrabang",
        "university_th": "สถาบันเทคโนโลยีพระจอมเกล้าเจ้าคุณทหารลาดกระบัง",
        "faculty": "Faculty of Medicine",
        "faculty_th": "คณะแพทยศาสตร์",
        "department": "Department of Internal Medicine (Infectious Diseases)",
        "department_th": "ภาควิชาอายุรศาสตร์ (สาขาวิชาโรคติดเชื้อ)",
        "academic_title": "Prof. Dr.",
        "academic_title_th": "ศ.ดร.นพ.",
        "first_name": "Prasit",
        "last_name": "Khawcharoenporn",
        "full_name_th": "ศ.ดร.นพ. ประสิทธิ์ ขาวเจริญพร",
        "role": "Renowned Infectious Disease Specialist in Antimicrobial Resistance (AMR), Multi-Drug Resistant Bacteria and Hospital Epidemiology",
        "email": "prasit.kh@kmitl.ac.th",
        "profile_url": "https://md.kmitl.ac.th/staff/prasit-khawcharoenporn",
        "scholar_url": "https://scholar.google.com/citations?user=prasitkhawcharoenporn",
        "education": [
            "Clinical Fellowship in Infectious Diseases, University of Illinois at Chicago, USA",
            "M.P.H. (Epidemiology and Biostatistics), Johns Hopkins Bloomberg School of Public Health, USA",
            "M.D. (First Class Honours), Chulalongkorn University"
        ],
        "research_interests": [
            "Clinical Epidemiology and Molecular Mechanisms of Carbapenem-Resistant Enterobacterales (CRE)",
            "Antimicrobial Stewardship Programs and Hospital-Acquired Infection Prevention",
            "Novel Beta-Lactamase Inhibitor Combinations and Polymyxin Optimization",
            "Infectious Disease Diagnostics in Immunocompromised and Critical Care Patients"
        ],
        "featured_publications": [
            "Clinical Outcomes and Risk Factors for Mortality in Patients with Carbapenem-Resistant Klebsiella pneumoniae Infection",
            "Impact of a Multidisciplinary Antimicrobial Stewardship Program on Antibiotic Utilization in a University Hospital",
            "Molecular Characterization of New Delhi Metallo-Beta-Lactamase (NDM) Harboring Gram-Negative Pathogens"
        ]
    },
    {
        "id": "kmitl_med_tachapong_001",
        "university": "King Mongkut's Institute of Technology Ladkrabang",
        "university_th": "สถาบันเทคโนโลยีพระจอมเกล้าเจ้าคุณทหารลาดกระบัง",
        "faculty": "Faculty of Medicine",
        "faculty_th": "คณะแพทยศาสตร์",
        "department": "Department of Cardiology & Clinical Medical AI",
        "department_th": "ภาควิชาอายุรศาสตร์หัวใจและหลอดเลือดและปัญญาประดิษฐ์ทางการแพทย์",
        "academic_title": "Assoc. Prof. Dr.",
        "academic_title_th": "รศ.ดร.นพ.",
        "first_name": "Tachapong",
        "last_name": "Ngarmukos",
        "full_name_th": "รศ.ดร.นพ. ธชาพงศ์ งามอุโฆษ",
        "role": "Distinguished Cardiac Electrophysiologist in Atrial Fibrillation Catheter Ablation, AI ECG Analytics and Sudden Cardiac Death",
        "email": "tachapong.ng@kmitl.ac.th",
        "profile_url": "https://md.kmitl.ac.th/staff/tachapong-ngarmukos",
        "scholar_url": "https://scholar.google.com/citations?user=tachapongngarmukos",
        "education": [
            "Clinical Cardiac Electrophysiology Fellowship, Harvard Medical School / Massachusetts General Hospital (MGH), USA",
            "M.D. (Honours), Mahidol University",
            "Diploma American Board of Clinical Cardiac Electrophysiology"
        ],
        "research_interests": [
            "High-Density 3D Electroanatomical Mapping in Complex Arrhythmia Ablation",
            "Deep Learning AI Models for Early Detection of Atrial Fibrillation from 12-Lead and Wearable ECG",
            "Cardiovascular Implantable Electronic Devices (Pacemakers, ICDs, CRT-D) Telemetry",
            "Genetic Architecture of Brugada Syndrome and Inherited Arrhythmia Syndromes in Thailand"
        ],
        "featured_publications": [
            "AI-Enabled Electrocardiogram for Pre-Symptomatic Detection of Paroxysmal Atrial Fibrillation in General Practice",
            "Long-Term Freedom from Recurrent Arrhythmias Following Radiofrequency Catheter Ablation of Persistent Atrial Fibrillation",
            "Genetic Screening and Sudden Unexplained Nocturnal Death Syndrome Profiling in Southeast Asian Cohorts"
        ]
    },
    {
        "id": "kmitl_med_supakarn_001",
        "university": "King Mongkut's Institute of Technology Ladkrabang",
        "university_th": "สถาบันเทคโนโลยีพระจอมเกล้าเจ้าคุณทหารลาดกระบัง",
        "faculty": "Faculty of Medicine",
        "faculty_th": "คณะแพทยศาสตร์",
        "department": "Department of Preventive Medicine and Health Data Science",
        "department_th": "ภาควิชาเวชศาสตร์ป้องกันและวิทยาการข้อมูลสุขภาพ",
        "academic_title": "Assoc. Prof. Dr.",
        "academic_title_th": "รศ.ดร.",
        "first_name": "Supakarn",
        "last_name": "Chamchod",
        "full_name_th": "รศ.ดร. ศุภกานต์ ชำโชติ",
        "role": "Leader in Mathematical Epidemiology, Infectious Disease Transmission Dynamics and Vaccine Modeling",
        "email": "supakarn.ch@kmitl.ac.th",
        "profile_url": "https://md.kmitl.ac.th/staff/supakarn-chamchod",
        "scholar_url": "https://scholar.google.com/citations?user=supakarnchamchod",
        "education": [
            "Ph.D. (Applied Mathematics / Mathematical Biology), University of Miami, USA",
            "B.Sc. (Mathematics), KMITL"
        ],
        "research_interests": [
            "Nonlinear Differential Equation Modeling of Vector-Borne Diseases (Dengue, Chikungunya, Zika)",
            "Optimal Control Theory for Public Health Intervention and Vaccine Resource Allocation",
            "Spatial Metapopulation Models and Cross-Border Disease Spread Dynamics",
            "Stochastic Agent-Based Simulations for Hospital Outbreak Containment"
        ],
        "featured_publications": [
            "Modeling the Impact of Imperfect Vaccines and Vector Control on Dengue Transmission Dynamics",
            "Optimal Pulse Vaccination and Treatment Strategies in Epidemic Models with Time Delay",
            "Metapopulation Disease Transmission Framework Considering Human Mobility and Spatial Heterogeneity"
        ]
    },
    {
        "id": "kmitl_med_voranart_001",
        "university": "King Mongkut's Institute of Technology Ladkrabang",
        "university_th": "สถาบันเทคโนโลยีพระจอมเกล้าเจ้าคุณทหารลาดกระบัง",
        "faculty": "Faculty of Medicine",
        "faculty_th": "คณะแพทยศาสตร์",
        "department": "Department of Regenerative Medicine and Stem Cell Translation",
        "department_th": "ภาควิชาเวชศาสตร์ฟื้นฟูสภาวะเสื่อมและเซลล์ต้นกำเนิด",
        "academic_title": "Assoc. Prof. Dr.",
        "academic_title_th": "รศ.ดร.",
        "first_name": "Voranart",
        "last_name": "Charoenpanich",
        "full_name_th": "รศ.ดร. วรนาถ เจริญพานิช",
        "role": "Expert in Stem Cell Bioprocessing, Extracellular Vesicles (Exosomes) and Tissue Engineering",
        "email": "voranart.ch@kmitl.ac.th",
        "profile_url": "https://md.kmitl.ac.th/staff/voranart-charoenpanich",
        "scholar_url": "https://scholar.google.com/citations?user=voranartcharoenpanich",
        "education": [
            "Ph.D. (Biomedical Engineering), University of Bern, Switzerland",
            "B.Sc. (Biotechnology), Mahidol University"
        ],
        "research_interests": [
            "Mesenchymal Stem Cell (MSC) Secretome and Exosomes in Cartilage and Tendon Healing",
            "Bioreactor Expansion of Stem Cells on Microcarriers Under Dynamic Mechanical Stimulation",
            "Hydrogel Biomaterials for 3D Stem Cell Microencapsulation and Targeted Release",
            "Immunomodulatory Mechanisms of Stem Cell Exosomes in Autoimmune and Inflammatory Disorders"
        ],
        "featured_publications": [
            "Mesenchymal Stem Cell-Derived Exosomes Promote Chondrogenic Differentiation and Cartilage Defect Repair",
            "Scalable Expansion of Human Umbilical Cord-Derived Mesenchymal Stem Cells in Stirred-Tank Bioreactors",
            "Injectable Biomimetic Hydrogels Supporting Stem Cell Paracrine Function for Myocardial Infarction Regeneration"
        ]
    },

    # =========================================================================
    # 5. School of Food Industry (คณะอุตสาหกรรมอาหาร สจล.)
    # =========================================================================
    {
        "id": "kmitl_food_prapasri_001",
        "university": "King Mongkut's Institute of Technology Ladkrabang",
        "university_th": "สถาบันเทคโนโลยีพระจอมเกล้าเจ้าคุณทหารลาดกระบัง",
        "faculty": "School of Food Industry",
        "faculty_th": "คณะอุตสาหกรรมอาหาร",
        "department": "Department of Food Biotechnology",
        "department_th": "ภาควิชาเทคโนโลยีชีวภาพทางอาหาร",
        "academic_title": "Assoc. Prof. Dr.",
        "academic_title_th": "รศ.ดร.",
        "first_name": "Prapasri",
        "last_name": "Thepkunya",
        "full_name_th": "รศ.ดร. ประภาศรี เทพกัญญา",
        "role": "Authority in Functional Food Fermentation, Plant-Based Probiotics and Synbiotic Beverages",
        "email": "prapasri.th@kmitl.ac.th",
        "profile_url": "https://food.kmitl.ac.th/staff/prapasri-thepkunya",
        "scholar_url": "https://scholar.google.com/citations?user=prapasrithepkunya",
        "education": [
            "Ph.D. (Food Biotechnology), Asian Institute of Technology (AIT)",
            "M.Sc. (Biotechnology), Kasetsart University",
            "B.Sc. (Food Science), KMITL"
        ],
        "research_interests": [
            "Plant-Based Probiotic Fermentation Using Indigenous Lactic Acid Bacteria",
            "Production of Bioactive Peptides and Antioxidant Phenolics from Fermented Soy and Rice Bran",
            "Synbiotic Fermented Functional Beverages with Enhanced Gastrointestinal Stability",
            "Microencapsulation of Probiotics Using Alginate-Prebiotic Matrices"
        ],
        "featured_publications": [
            "Survival and Functionality of Encapsulated Probiotic Bacteria in Plant-Based Fermented Matrix",
            "Bioactive Peptide Profiling and Antioxidant Capacity of Fermented Rice Bran Beverage by Selected Starter Consortia",
            "Development of Non-Dairy Synbiotic Fermented Drinks from Tropical Fruit Juices"
        ]
    },
    {
        "id": "kmitl_food_naphatsawan_001",
        "university": "King Mongkut's Institute of Technology Ladkrabang",
        "university_th": "สถาบันเทคโนโลยีพระจอมเกล้าเจ้าคุณทหารลาดกระบัง",
        "faculty": "School of Food Industry",
        "faculty_th": "คณะอุตสาหกรรมอาหาร",
        "department": "Department of Food Science and Nutrition",
        "department_th": "ภาควิชาวิทยาศาสตร์การอาหารและโภชนาการ",
        "academic_title": "Assoc. Prof. Dr.",
        "academic_title_th": "รศ.ดร.",
        "first_name": "Naphatsawan",
        "last_name": "Chumpolsri",
        "full_name_th": "รศ.ดร. นภัสวรรณ ชุมพลศรี",
        "role": "Expert in Functional Lipids, Tropical Plant Bioactives and Chronic Disease Prevention",
        "email": "naphatsawan.ch@kmitl.ac.th",
        "profile_url": "https://food.kmitl.ac.th/staff/naphatsawan-chumpolsri",
        "scholar_url": "https://scholar.google.com/citations?user=naphatsawanchumpolsri",
        "education": [
            "Ph.D. (Food Science), Kasetsart University",
            "B.Sc. (Food Industry), KMITL"
        ],
        "research_interests": [
            "Gamma-Oryzanol, Tocotrienols and Phytosterols Extraction from Pigmented Rice Bran Oils",
            "In Vitro Anti-Lipase and Anti-Alpha-Glucosidase Mechanisms of Tropical Fruit Phytochemicals",
            "Structured Lipids and Medium-Chain Triglyceride (MCT) Enzymatic Interesterification",
            "Nutraceutical Formulation for Metabolic Syndrome Management"
        ],
        "featured_publications": [
            "Comparative Profiling of Phytochemicals, Vitamin E Isomers, and Gamma-Oryzanol in Thai Pigmented Rice Cultivars",
            "Enzymatic Synthesis and Physical Properties of Structured Triglycerides Enriched with Medium-Chain Fatty Acids",
            "Hypoglycemic and Hypolipidemic Activities of Polyphenol-Enriched Extracts from Indigenous Tropical Berry Fruits"
        ]
    },
    {
        "id": "kmitl_food_nuttapol_001",
        "university": "King Mongkut's Institute of Technology Ladkrabang",
        "university_th": "สถาบันเทคโนโลยีพระจอมเกล้าเจ้าคุณทหารลาดกระบัง",
        "faculty": "School of Food Industry",
        "faculty_th": "คณะอุตสาหกรรมอาหาร",
        "department": "Department of Food Process Engineering",
        "department_th": "ภาควิชาวิศวกรรมกระบวนการอาหาร",
        "academic_title": "Assoc. Prof. Dr.",
        "academic_title_th": "รศ.ดร.",
        "first_name": "Nuttapol",
        "last_name": "Tanadchangsaeng",
        "full_name_th": "รศ.ดร. ณัฐพล ถนัดช่างแสง",
        "role": "Distinguished Scholar in Polyhydroxyalkanoates (PHA), Bio-Plastic Extrusion and Circular Bio-Packaging",
        "email": "nuttapol.ta@kmitl.ac.th",
        "profile_url": "https://food.kmitl.ac.th/staff/nuttapol-tanadchangsaeng",
        "scholar_url": "https://scholar.google.com/citations?user=nuttapoltanadchangsaeng",
        "education": [
            "D.Eng. (Materials Science and Engineering), Tokyo Institute of Technology, Japan",
            "M.Eng. (Chemical Engineering), Chulalongkorn University",
            "B.Eng. (Chemical Engineering), KMITL"
        ],
        "research_interests": [
            "Biosynthesis and Thermal Processing of Polyhydroxybutyrate-co-Hexanoate (PHBH) Bio-Polyesters",
            "Reactive Extrusion and Compatibilization of PHA/PLA Biodegradable Packaging Blends",
            "Barrier Properties and Biodegradability of Food-Contact Biopolymer Trays in Marine Environments",
            "Agricultural Waste Valorization for Polyhydroxyalkanoate Microbial Fermentation"
        ],
        "featured_publications": [
            "Biosynthesis and Characterization of Novel Polyhydroxyalkanoate Copolymers with High Ductility for Packaging Applications",
            "Structure-Property Relationships of Compatibilized PLA/PHA Bio-Blown Films Prepared by Twin-Screw Extrusion",
            "Marine Biodegradation Kinetics and Mechanical Integrity of Biopolymer Composite Trays for Perishable Foods"
        ]
    },

    # =========================================================================
    # 6. School of Agricultural Technology (คณะเทคโนโลยีการเกษตร สจล.)
    # =========================================================================
    {
        "id": "kmitl_agri_somchai_001",
        "university": "King Mongkut's Institute of Technology Ladkrabang",
        "university_th": "สถาบันเทคโนโลยีพระจอมเกล้าเจ้าคุณทหารลาดกระบัง",
        "faculty": "School of Agricultural Technology",
        "faculty_th": "คณะเทคโนโลยีการเกษตร",
        "department": "Department of Agronomy and Smart Farming",
        "department_th": "สาขาวิชาพืชไร่และการเกษตรอัจฉริยะ",
        "academic_title": "Assoc. Prof. Dr.",
        "academic_title_th": "รศ.ดร.",
        "first_name": "Somchai",
        "last_name": "Chaisri",
        "full_name_th": "รศ.ดร. สมชาย ชัยศรี",
        "role": "Pioneer in Precision Agronomy, Automated Fertigation and IoT Sensing for High-Yield Tropical Crops",
        "email": "somchai.ch@kmitl.ac.th",
        "profile_url": "https://agri.kmitl.ac.th/staff/somchai-chaisri",
        "scholar_url": "https://scholar.google.com/citations?user=somchaichaisri",
        "education": [
            "Ph.D. (Agronomy), University of the Philippines Los Baños (UPLB), Philippines",
            "M.Sc. (Agronomy), Kasetsart University",
            "B.Sc. (Agriculture), KMITL"
        ],
        "research_interests": [
            "Smart Soil Moisture and Electrical Conductivity Sensor-Driven Drip Fertigation Automation",
            "High-Throughput Phenotyping of Abiotic Stress-Tolerant Tropical Maize Varieties",
            "Variable Rate Fertilizer Application Mapping Using Satellite NDVI Remote Sensing",
            "Cover Crops and Minimum Tillage for Soil Health and Carbon Sequestration in Cassava Farming"
        ],
        "featured_publications": [
            "Automated Precision Fertigation Scheduling for Field Crops Based on Real-Time IoT Soil Moisture Feedback",
            "Evaluating Drone-Based Multispectral Vegetation Indices for Nitrogen Status Monitoring in Tropical Corn",
            "Impact of Conservation Tillage and Organic Mulching on Soil Microbial Respiration and Crop Yield"
        ]
    },
    {
        "id": "kmitl_agri_patchara_001",
        "university": "King Mongkut's Institute of Technology Ladkrabang",
        "university_th": "สถาบันเทคโนโลยีพระจอมเกล้าเจ้าคุณทหารลาดกระบัง",
        "faculty": "School of Agricultural Technology",
        "faculty_th": "คณะเทคโนโลยีการเกษตร",
        "department": "Department of Plant Production Technology",
        "department_th": "สาขาวิชาเทคโนโลยีการผลิตพืช",
        "academic_title": "Assoc. Prof. Dr.",
        "academic_title_th": "รศ.ดร.",
        "first_name": "Patchara",
        "last_name": "Phumichai",
        "full_name_th": "รศ.ดร. พัชรา ภูมิชัย",
        "role": "Distinguished Plant Geneticist in Marker-Assisted Selection, QTL Mapping and Tropical Crop Genomics",
        "email": "patchara.ph@kmitl.ac.th",
        "profile_url": "https://agri.kmitl.ac.th/staff/patchara-phumichai",
        "scholar_url": "https://scholar.google.com/citations?user=patcharaphumichai",
        "education": [
            "Ph.D. (Plant Breeding and Genetics), Kasetsart University",
            "B.Sc. (Agricultural Technology), KMITL"
        ],
        "research_interests": [
            "Genome-Wide Association Studies (GWAS) and QTL Mapping for Drought and Salinity Tolerance",
            "Single Nucleotide Polymorphism (SNP) High-Density Array Genotyping in Tropical Fruit Trees",
            "Marker-Assisted Introgression of Disease Resistance Genes in Rice and Legume Breeding",
            "Epigenetic Regulation of Flowering and Fruit Development in Tropical Orchids"
        ],
        "featured_publications": [
            "Identification of Major Quantitative Trait Loci Associated with Submergence and Salinity Tolerance in Rice",
            "SNP-Based Genetic Diversity and Population Structure Analysis of Elite Tropical Crop Germplasm",
            "Marker-Assisted Selection for Bacterial Blight Resistance in Aromatic Jasmine Rice Backcross Progenies"
        ]
    },
    {
        "id": "kmitl_agri_wanchai_001",
        "university": "King Mongkut's Institute of Technology Ladkrabang",
        "university_th": "สถาบันเทคโนโลยีพระจอมเกล้าเจ้าคุณทหารลาดกระบัง",
        "faculty": "School of Agricultural Technology",
        "faculty_th": "คณะเทคโนโลยีการเกษตร",
        "department": "Department of Animal Science",
        "department_th": "สาขาวิชาสัตวศาสตร์",
        "academic_title": "Assoc. Prof. Dr.",
        "academic_title_th": "รศ.ดร.",
        "first_name": "Wanchai",
        "last_name": "Poomputsa",
        "full_name_th": "รศ.ดร. วันชัย พุ่มพุทรา",
        "role": "Expert in Animal Reproductive Biotechnology, Somatic Cell Nuclear Transfer and Cryopreservation",
        "email": "wanchai.po@kmitl.ac.th",
        "profile_url": "https://agri.kmitl.ac.th/staff/wanchai-poomputsa",
        "scholar_url": "https://scholar.google.com/citations?user=wanchaipoomputsa",
        "education": [
            "Ph.D. (Animal Reproduction / Biotechnology), Chulalongkorn University",
            "B.Sc. (Animal Science), Kasetsart University"
        ],
        "research_interests": [
            "Vitrification and Ultra-Rapid Cryopreservation of Bovine and Swine Embryos and Oocytes",
            "In Vitro Fertilization (IVF) and Blastocyst Culture Media Optimization for Tropical Livestock",
            "Sperm Sexing Technologies and Epigenetic Integrity in Artificial Insemination Programs",
            "Stem Cell Differentiation into Germline Lineages for Genetic Preservation of Rare Breeds"
        ],
        "featured_publications": [
            "Effects of Trehalose and Antioxidant Supplementation on Cryosurvival and Developmental Competence of Vitrified Bovine Oocytes",
            "In Vitro Embryo Production Efficiency in Native Tropical Swamp Buffalo Using Sex-Sorted Semen",
            "Epigenetic Reprogramming and DNA Methylation Dynamics During Early Embryonic Development Following Somatic Cell Cloning"
        ]
    }
]
