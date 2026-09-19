# -*- coding: utf-8 -*-
"""
Curated Regional Research Laboratories & Centers of Excellence Phase 2.
Expands research lab coverage across regional universities:
- University of Phayao (UP)
- Walailak University (WU)
- Maejo University (MJU)
- Mahasarakham University (MSU)
- Burapha University (BUU)
- Silpakorn University (SU)
- Mae Fah Luang University (MFU)
- Thaksin University (TSU)
- Ubon Ratchathani University (UBU)
- King Mongkut's University of Technology Thonburi (KMUTT FIBO & SIT)

Schema compliant with ResearchLabDB (AGENTS.md & PDPA).
"""

REGIONAL_RESEARCH_LABS_PHASE2 = [
    # =========================================================================
    # 1. UNIVERSITY OF PHAYAO (UP)
    # =========================================================================
    {
        "id": "up_smart_agriculture_food_center",
        "name_th": "ศูนย์วิจัยเกษตรอัจฉริยะและนวัตกรรมอาหารภาคเหนือ มหาวิทยาลัยพะเยา",
        "name_en": "Northern Smart Agriculture & Food Innovation Center (UP-SAFIC)",
        "university": "University of Phayao",
        "university_th": "มหาวิทยาลัยพะเยา",
        "faculty": "School of Agriculture and Natural Resources",
        "faculty_th": "คณะเกษตรศาสตร์และทรัพยากรธรรมชาติ",
        "department": "Department of Food Science and Technology",
        "department_th": "สาขาวิชาวิทยาศาสตร์และเทคโนโลยีการอาหาร",
        "lead_advisor_id": None,
        "member_faculty_ids": [],
        "description": "ศูนย์ความเป็นเลิศด้านการยกระดับผลผลิตการเกษตรภาคเหนือตอนบน มุ่งเน้นการวิจัยสมาร์ทฟาร์มมิ่ง การแปรรูปสารสกัดจากข้าวหอมมะลิพะเยา และการพัฒนาอาหารฟังก์ชันเพื่อสุขภาพ",
        "research_domains": [
            "Smart Precision Agriculture & IoT Sensor Networks",
            "Functional Food Formulation & Bioactive Peptides",
            "High-Value Agricultural Product Processing",
            "Soil Health Monitoring & Sustainable Farming"
        ],
        "flagship_equipment": [
            "Supercritical Fluid Extraction (SFE) System",
            "High-Performance Liquid Chromatography (HPLC-DAD)",
            "Precision Drone Multi-spectral Agricultural Mapping System",
            "Pilot-Scale Spray Dryer & Vacuum Freeze Dryer"
        ],
        "industry_partners": [
            "Phayao Provincial Agricultural Office",
            "Singha Corporation",
            "Charoen Pokphand Foods (CPF)",
            "Betagro Group"
        ],
        "open_positions": [
            "Master's RA: Functional Compounds from Phayao Rice (Full Tuition Scholarship)",
            "PhD Candidate: Precision Agro-Drone Autonomous Sensing"
        ],
        "website_url": "https://agri.up.ac.th",
        "image_url": "https://images.unsplash.com/photo-1574943320219-553eb213f72d?w=800&q=80"
    },
    {
        "id": "up_herbal_cosmeceuticals_center",
        "name_th": "ศูนย์วิจัยสมุนไพรและเครื่องสำอางธรรมชาตินวัตกรรม มหาวิทยาลัยพะเยา",
        "name_en": "Center of Excellence in Herbal Medicine and Natural Cosmeceuticals",
        "university": "University of Phayao",
        "university_th": "มหาวิทยาลัยพะเยา",
        "faculty": "School of Pharmaceutical Sciences",
        "faculty_th": "คณะเภสัชศาสตร์",
        "department": "Department of Pharmaceutical Technology",
        "department_th": "สาขาวิชาเทคโนโลยีเภสัชกรรม",
        "lead_advisor_id": None,
        "member_faculty_ids": [],
        "description": "ศูนย์วิจัยและพัฒนาสารสกัดสมุนไพรท้องถิ่นล้านนาเพื่อการแพทย์และเวชสำอาง มุ่งเน้นมาตรฐานความปลอดภัย การทดสอบฤทธิ์ทางชีวภาพ และการนำส่งยาผ่านอนุภาคนาโน",
        "research_domains": [
            "Herbal Active Ingredient Extraction & Standardization",
            "Liposomal & Nanoparticle Cosmetic Drug Delivery",
            "Antioxidant & Anti-Aging Cellular Assays",
            "Lanna Indigenous Medicinal Plant Phytochemistry"
        ],
        "flagship_equipment": [
            "Rotary Evaporator Battery & Industrial Sonicator",
            "Zeta Potential & Dynamic Light Scattering (DLS) Particle Analyzer",
            "Fluorescence Inverted Cell Culture Microscope",
            "Automated Microplate Spectrophotometer (ELISA Reader)"
        ],
        "industry_partners": [
            "Government Pharmaceutical Organization (GPO)",
            "Khao Kho Herb Co., Ltd.",
            "Twin Lotus Co., Ltd."
        ],
        "open_positions": [
            "Master's RA: Herbal Nanogel Formulation for Wound Healing",
            "Research Assistant: Cellular Cytotoxicity Screening"
        ],
        "website_url": "https://pharmacy.up.ac.th",
        "image_url": "https://images.unsplash.com/photo-1584308666744-24d5c474f2ae?w=800&q=80"
    },
    {
        "id": "up_ict_geoinformatics_disaster_lab",
        "name_th": "ห้องปฏิบัติการปัญญาประดิษฐ์และภูมิสารสนเทศเพื่อการเตือนภัยพิบัติ มหาวิทยาลัยพะเยา",
        "name_en": "AI & Geo-Informatics for Disaster Mitigation Laboratory",
        "university": "University of Phayao",
        "university_th": "มหาวิทยาลัยพะเยา",
        "faculty": "School of Information and Communication Technology",
        "faculty_th": "คณะเทคโนโลยีสารสนเทศและการสื่อสาร",
        "department": "Department of Computer Science & Geo-Informatics",
        "department_th": "สาขาวิชาวิทยาการคอมพิวเตอร์และภูมิสารสนเทศศาสตร์",
        "lead_advisor_id": None,
        "member_faculty_ids": [],
        "description": "ศูนย์วิจัยเชิงบูรณาการด้านการติดตามวิกฤตสิ่งแวดล้อม ไฟป่า หมอกควัน PM2.5 และดินถล่มในแถบภูเขาภาคเหนือ โดยประยุกต์ใช้ดาวเทียมภูมิสารสนเทศและการเรียนรู้ของเครื่อง (Machine Learning)",
        "research_domains": [
            "Satellite Remote Sensing & Forest Fire Early Warning",
            "Spatiotemporal Deep Learning for PM2.5 Forecasting",
            "Landslide & Mountain Flash Flood Risk Modeling",
            "GIS-based Smart City & Environmental Monitoring"
        ],
        "flagship_equipment": [
            "High-Performance GPU Deep Learning Cluster (4x NVIDIA RTX A6000)",
            "Direct Satellite Downlink Ground Receiver System",
            "Multi-sensor Ground Weather & Air Quality Real-time Stations"
        ],
        "industry_partners": [
            "Geo-Informatics and Space Technology Development Agency (GISTDA)",
            "Pollution Control Department (PCD)",
            "Department of Disaster Prevention and Mitigation (DDPM)"
        ],
        "open_positions": [
            "PhD Candidate: Deep Satellite Telemetry for Wildfire Detection",
            "Master's RA: Hydrological Landslide AI Prediction"
        ],
        "website_url": "https://ict.up.ac.th",
        "image_url": "https://images.unsplash.com/photo-1504384308090-c894fdcc538d?w=800&q=80"
    },

    # =========================================================================
    # 2. WALAILAK UNIVERSITY (WU)
    # =========================================================================
    {
        "id": "wu_wood_biomaterials_center",
        "name_th": "ศูนย์ความเป็นเลิศด้านไม้และวัสดุชีวภาพ มหาวิทยาลัยวลัยลักษณ์",
        "name_en": "Center of Excellence in Wood and Biomaterials (WU-CEWB)",
        "university": "Walailak University",
        "university_th": "มหาวิทยาลัยวลัยลักษณ์",
        "faculty": "School of Engineering and Technology",
        "faculty_th": "สำนักวิชาวิศวกรรมศาสตร์และเทคโนโลยี",
        "department": "Department of Materials Engineering",
        "department_th": "สาขาวิชาวิศวกรรมวัสดุและกระบวนการ",
        "lead_advisor_id": None,
        "member_faculty_ids": [],
        "description": "ศูนย์วิจัยชั้นนำด้านการแปรรูปไม้ยางพาราและชีวมวลภาคใต้ พัฒนาคอมโพสิตชีวภาพ สารเคลือบป้องกันไฟ และวัสดุก่อสร้างคาร์บอนต่ำเพื่อความยั่งยืน",
        "research_domains": [
            "Thermal & Chemical Wood Modification",
            "Bio-based Composites & Green Polyurethane",
            "Sustainable Palm Biomass Upcycling",
            "Nano-Cellulose Extraction & Functional Coatings"
        ],
        "flagship_equipment": [
            "High-Pressure Wood Thermal Modification Kiln",
            "Universal Testing Machine (UTM 100 kN)",
            "Scanning Electron Microscope (FE-SEM with EDS)",
            "Thermogravimetric Analyzer (TGA/DSC)"
        ],
        "industry_partners": [
            "Rubber Authority of Thailand (RAOT)",
            "Siam Cement Group (SCG Building Materials)",
            "Vanachai Group Public Company"
        ],
        "open_positions": [
            "Master's RA: Fire-Retardant Rubberwood Biocomposites",
            "PhD Fellow: Lignin-Derived High-Performance Adhesives"
        ],
        "website_url": "https://wood.wu.ac.th",
        "image_url": "https://images.unsplash.com/photo-1581092160607-ee22621dd758?w=800&q=80"
    },
    {
        "id": "wu_vector_borne_disease_center",
        "name_th": "ศูนย์ความเป็นเลิศด้านโรคติดเชื้อนำโดยแมลงและเวชศาสตร์เขตร้อน มหาวิทยาลัยวลัยลักษณ์",
        "name_en": "Center of Excellence in Vector-Borne Diseases & Tropical Medicine",
        "university": "Walailak University",
        "university_th": "มหาวิทยาลัยวลัยลักษณ์",
        "faculty": "School of Medicine",
        "faculty_th": "สำนักวิชาแพทยศาสตร์",
        "department": "Department of Tropical Medicine & Medical Microbiology",
        "department_th": "สาขาวิชาเวชศาสตร์เขตร้อนและจุลชีววิทยาทางการแพทย์",
        "lead_advisor_id": None,
        "member_faculty_ids": [],
        "description": "ศูนย์วิจัยระดับสากลที่ศึกษาการระบาด พันธุศาสตร์ และการพัฒนาภูมิคุ้มกันต่อไข้เลือดออก ชิคุนกุนยา และมาลาเรียในแถบคาบสมุทรภาคใต้",
        "research_domains": [
            "Dengue & Arbovirus Molecular Epidemiology",
            "Mosquito Vector Genetic Competence & Control",
            "Antigen-Antibody Rapid Diagnostic Assay Development",
            "Antimalarial Drug Resistance Surveillance"
        ],
        "flagship_equipment": [
            "Next-Generation Sequencer (Illumina MiniSeq)",
            "Biosafety Level 2+ (BSL-2+) High-Containment Research Suite",
            "Real-Time Quantitative PCR System (QuantStudio 5)",
            "Insectary Climate Chambers with Automated Photoperiod"
        ],
        "industry_partners": [
            "Department of Disease Control, Ministry of Public Health",
            "Armed Forces Research Institute of Medical Sciences (AFRIMS)",
            "World Health Organization (WHO SEARO)"
        ],
        "open_positions": [
            "PhD Researcher: Mosquito Microbiome Interactions in Dengue Transmission",
            "Master's RA: CRISPR-based Rapid Point-of-Care Diagnostics"
        ],
        "website_url": "https://medicine.wu.ac.th",
        "image_url": "https://images.unsplash.com/photo-1579154204601-01588f351e67?w=800&q=80"
    },

    # =========================================================================
    # 3. MAEJO UNIVERSITY (MJU)
    # =========================================================================
    {
        "id": "mju_organic_agriculture_biotech_center",
        "name_th": "ศูนย์วิจัยเกษตรอินทรีย์และเทคโนโลยีชีวภาพดินอัจฉริยะ มหาวิทยาลัยแม่โจ้",
        "name_en": "Organic Agriculture & Smart Soil Biotechnology Research Center",
        "university": "Maejo University",
        "university_th": "มหาวิทยาลัยแม่โจ้",
        "faculty": "Faculty of Agricultural Production",
        "faculty_th": "คณะผลิตกรรมการเกษตร",
        "department": "Department of Soil Science and Agronomy",
        "department_th": "สาขาวิชาปฐพีศาสตร์และพืชไร่",
        "lead_advisor_id": None,
        "member_faculty_ids": [],
        "description": "สถาบันวิจัยการเกษตรอินทรีย์ที่เก่าแก่และทรงอิทธิพลที่สุดในภาคเหนือ เชี่ยวชาญด้านจุลินทรีย์ปฏิปักษ์ การฟื้นฟูความอุดมสมบูรณ์ของดินด้วยถ่านไบโอชาร์ และเทคโนโลยีชีวภาพการเกษตรปลอดภัย",
        "research_domains": [
            "Soil Microbial Ecology & Beneficial Bio-inoculants",
            "Biochar Production & Carbon Sequestration",
            "Organic Certified Seed Breeding & Multiplication",
            "Natural Biological Pest Control Agents"
        ],
        "flagship_equipment": [
            "Automated Bioreactor Fermentation Train (50L & 200L)",
            "Total Organic Carbon Analyzer (Shimadzu TOC-L)",
            "Inductively Coupled Plasma Mass Spectrometry (ICP-MS)",
            "Microbial Colony Counter with AI Image Analysis"
        ],
        "industry_partners": [
            "National Innovation Agency (NIA)",
            "Mae Fah Luang Foundation",
            "Siam Kubota Corporation",
            "Northern Organic Agriculture Cooperative Network"
        ],
        "open_positions": [
            "Master's RA: Endophytic Microbes for Drought Resilience",
            "PhD Candidate: Biochar-Mineral Soil Amendments for Carbon Credits"
        ],
        "website_url": "https://ap.mju.ac.th",
        "image_url": "https://images.unsplash.com/photo-1592417817098-8f3d69106093?w=800&q=80"
    },
    {
        "id": "mju_postharvest_smart_automation_lab",
        "name_th": "ห้องปฏิบัติการวิจัยวิทยาการหลังการเก็บเกี่ยวและระบบอัตโนมัติทางการเกษตร มหาวิทยาลัยแม่โจ้",
        "name_en": "Precision Postharvest Technology and Agro-Automation Research Lab",
        "university": "Maejo University",
        "university_th": "มหาวิทยาลัยแม่โจ้",
        "faculty": "Faculty of Engineering and Agro-Industry",
        "faculty_th": "คณะวิศวกรรมและอุตสาหกรรมเกษตร",
        "department": "Department of Postharvest & Agro-Industrial Technology",
        "department_th": "สาขาวิชาวิศวกรรมเกษตรและเทคโนโลยีหลังการเก็บเกี่ยว",
        "lead_advisor_id": None,
        "member_faculty_ids": [],
        "description": "ห้องปฏิบัติการที่มุ่งพัฒนาเทคโนโลยีการลดความสูญเสียหลังการเก็บเกี่ยวของพืชผักและผลไม้เมืองหนาว การตรวจวัดคุณภาพแบบไม่ทำลายด้วย Hyperspectral Imaging และหุ่นยนต์คัดแยกผลผลิต",
        "research_domains": [
            "Non-Destructive Fruit Quality Evaluation (NIR & Hyperspectral)",
            "Modified Atmosphere Packaging (MAP) for Cold-Climate Crops",
            "Robotic Agro-Sorting & Vision-Based Grading",
            "Cold Chain IoT Logistics & Ethylene Scrubbing Technologies"
        ],
        "flagship_equipment": [
            "Benchtop VNIR Hyperspectral Imaging System (400-1000 nm)",
            "Gas Chromatography with Thermal Conductivity Detector (GC-TCD)",
            "6-Axis Industrial Robotic Sorting Cell",
            "Precision Cold Storage Chambers with Controlled Respiration"
        ],
        "industry_partners": [
            "The Royal Project Foundation (โครงการหลวง)",
            "Siam Makro Public Company",
            "Central Food Retail Group"
        ],
        "open_positions": [
            "Master's Fellowship: Hyperspectral Sweetness Sorting in Tropical Fruits",
            "PhD Candidate: Smart Cold Chain Shelf-Life Extension Systems"
        ],
        "website_url": "https://agro.mju.ac.th",
        "image_url": "https://images.unsplash.com/photo-1615811361523-6bd03d7748e7?w=800&q=80"
    },

    # =========================================================================
    # 4. MAHASARAKHAM UNIVERSITY (MSU)
    # =========================================================================
    {
        "id": "msu_paleontology_research_center",
        "name_th": "ศูนย์วิจัยและการศึกษาบรรพชีวินวิทยา มหาวิทยาลัยมหาสารคาม",
        "name_en": "Paleontological Research and Education Center (PRC-MSU)",
        "university": "Mahasarakham University",
        "university_th": "มหาวิทยาลัยมหาสารคาม",
        "faculty": "Faculty of Science",
        "faculty_th": "คณะวิทยาศาสตร์",
        "department": "Department of Biology & Geology",
        "department_th": "สาขาวิชาชีววิทยาและธรณีวิทยา",
        "lead_advisor_id": None,
        "member_faculty_ids": [],
        "description": "ศูนย์วิจัยบรรพชีวินวิทยาชั้นนำของเอเชียตะวันออกเฉียงใต้ มีบทบาทสำคัญในการค้นพบไดโนเสาร์และสัตว์ดึกดำบรรพ์ชนิดใหม่ของโลกในที่ราบสูงโคราช พร้อมห้องปฏิบัติการสกัดวิเคราะห์ฟอสซิล",
        "research_domains": [
            "Vertebrate Paleontology & Dinosaur Evolutionary Biology",
            "Khorat Plateau Mesozoic Stratigraphy & Paleoenvironment",
            "Micro-Computed Tomography (Micro-CT) Fossil Reconstruction",
            "Isotope Geochemistry for Paleoclimate Reconstruction"
        ],
        "flagship_equipment": [
            "High-Resolution Micro-CT Scanner for Geological Specimens",
            "Precision Ultrasonic Micro-Preparation Fossil Extraction Tools",
            "Stable Isotope Ratio Mass Spectrometer (IRMS)",
            "Petrographic Thin-Section Preparation Suite"
        ],
        "industry_partners": [
            "Department of Mineral Resources, Thailand",
            "Muséum National d'Histoire Naturelle (Paris, France)",
            "Fukui Prefectural Dinosaur Museum (Japan)"
        ],
        "open_positions": [
            "Master's RA: Mesozoic Reptilian Anatomy Analysis",
            "PhD Fellowship: Cretaceous Environmental Transition in Southeast Asia"
        ],
        "website_url": "https://prc.msu.ac.th",
        "image_url": "https://images.unsplash.com/photo-1518709268805-4e9042af9f23?w=800&q=80"
    },
    {
        "id": "msu_biodiversity_natural_products_lab",
        "name_th": "ศูนย์วิจัยความหลากหลายทางชีวภาพและผลิตภัณฑ์ธรรมชาติอีสาน มหาวิทยาลัยมหาสารคาม",
        "name_en": "Northeastern Biodiversity & Natural Bio-Products Research Center",
        "university": "Mahasarakham University",
        "university_th": "มหาวิทยาลัยมหาสารคาม",
        "faculty": "Faculty of Pharmacy",
        "faculty_th": "คณะเภสัชศาสตร์",
        "department": "Department of Pharmacognosy",
        "department_th": "สาขาวิชาเภสัชเวทและเภสัชเคมี",
        "lead_advisor_id": None,
        "member_faculty_ids": [],
        "description": "ศูนย์วิจัยที่มุ่งศึกษาคุณค่าทางยาของพืชและเห็ดพื้นบ้านอีสาน การคัดกรองสารยับยั้งมะเร็งและต้านอนุมูลอิสระ และการพัฒนาต่อยอดเป็นยาและผลิตภัณฑ์สุขภาพมูลค่าสูง",
        "research_domains": [
            "Isan Medicinal Flora Phytochemical Profiling",
            "Bioassay-Guided Anticancer Compound Fractionation",
            "Mushroom Metabolomics & Immunomodulatory Polysaccharides",
            "Standardized Extract Development for Herbal Medicine"
        ],
        "flagship_equipment": [
            "Preparative High-Performance Liquid Chromatography (Prep-HPLC)",
            "Gas Chromatography-Mass Spectrometry (GC-MS Triple Quad)",
            "Multi-Mode Microplate Reader with Cytotoxicity Screening",
            "Lyophilization Freezing Dryer Unit"
        ],
        "industry_partners": [
            "Thai Herbal Products Co., Ltd.",
            "Abhaibhubejhr Herbal Research Center",
            "Provincial Public Health Office Maha Sarakham"
        ],
        "open_positions": [
            "Master's RA: Isolation of Novel Terpenoids from Native Isan Flora",
            "PhD Candidate: Molecular Targets of Mushroom-Derived Immunostimulants"
        ],
        "website_url": "https://pharmacy.msu.ac.th",
        "image_url": "https://images.unsplash.com/photo-1532187863486-abf9dbad1b69?w=800&q=80"
    },

    # =========================================================================
    # 5. BURAPHA UNIVERSITY (BUU)
    # =========================================================================
    {
        "id": "buu_eec_green_hydrogen_energy_lab",
        "name_th": "ห้องปฏิบัติการวิจัยไฮโดรเจนสีเขียวและพลังงานสะอาด EEC มหาวิทยาลัยบูรพา",
        "name_en": "EEC Green Hydrogen & Clean Energy Technology Research Laboratory",
        "university": "Burapha University",
        "university_th": "มหาวิทยาลัยบูรพา",
        "faculty": "Faculty of Science",
        "faculty_th": "คณะวิทยาศาสตร์",
        "department": "Department of Chemistry & Renewable Energy",
        "department_th": "ภาควิชาเคมีและพลังงานทดแทน",
        "lead_advisor_id": None,
        "member_faculty_ids": [],
        "description": "ศูนย์วิจัยพลังงานอนาคตในระเบียงเศรษฐกิจภาคตะวันออก มุ่งเน้นการแยกน้ำด้วยไฟฟ้าเพื่อผลิตไฮโดรเจนสีเขียว (Water Electrolysis) และการพัฒนาเซลล์เชื้อเพลิงคาร์บอนเป็นศูนย์",
        "research_domains": [
            "Electrocatalyst Synthesis for Water Splitting",
            "Proton Exchange Membrane (PEM) Fuel Cells",
            "Solar-to-Hydrogen Photochemical Conversion",
            "Industrial Carbon Capture, Utilization, and Storage (CCUS)"
        ],
        "flagship_equipment": [
            "Potentiostat / Galvanostat with Electrochemical Impedance (EIS)",
            "Gas Chromatograph with Thermal Desorption for Hydrogen Purity",
            "PEM Electrolyzer Test Station with Mass Flow Controllers",
            "X-ray Diffraction (XRD) Powder Diffractometer"
        ],
        "industry_partners": [
            "PTT Public Company Limited",
            "Eastern Economic Corridor Office (EECO)",
            "SCG Clean Energy",
            "Global Power Synergy Public Company (GPSC)"
        ],
        "open_positions": [
            "Master's Fellowship: Non-Precious Metal Catalysts for Water Splitting",
            "PhD Candidate: High-Pressure Hydrogen Storage Materials"
        ],
        "website_url": "https://sci.buu.ac.th",
        "image_url": "https://images.unsplash.com/photo-1497435334941-8c899ee9e8e9?w=800&q=80"
    },

    # =========================================================================
    # 6. SILPAKORN UNIVERSITY (SU)
    # =========================================================================
    {
        "id": "su_digital_heritage_archaeology_lab",
        "name_th": "ห้องปฏิบัติการอนุรักษ์มรดกทางวัฒนธรรมและโบราณคดีดิจิทัล มหาวิทยาลัยศิลปากร",
        "name_en": "Digital Cultural Heritage & Archaeological Science Laboratory",
        "university": "Silpakorn University",
        "university_th": "มหาวิทยาลัยศิลปากร",
        "faculty": "Faculty of Archaeology",
        "faculty_th": "คณะโบราณคดี",
        "department": "Department of Archaeology and Heritage Sciences",
        "department_th": "ภาควิชาโบราณคดีและวิทยาศาสตร์มรดก",
        "lead_advisor_id": None,
        "member_faculty_ids": [],
        "description": "ศูนย์วิจัยโบราณคดีชั้นแนวหน้าของประเทศไทย ผสานวิทยาศาสตร์เคมีวิเคราะห์และเทคโนโลยีดิจิทัล 3 มิติ เพื่อการอนุรักษ์โบราณสถาน โบราณวัตถุ และการจำลองมรดกเสมือนจริง",
        "research_domains": [
            "Terrestrial 3D Laser Scanning & Photogrammetry",
            "Non-Destructive Material Characterization of Ancient Artifacts",
            "Archaeological Pigment & Ceramic Provenance Spectroscopy",
            "Virtual Reality (VR) Reconstruction of Historical Sites"
        ],
        "flagship_equipment": [
            "Portable X-ray Fluorescence Spectrometer (pXRF)",
            "LiDAR High-Accuracy Terrestrial 3D Laser Scanner",
            "FTIR Spectrometer with Attenuated Total Reflectance (ATR)",
            "Multi-view Stereophotogrammetry Drone Platform"
        ],
        "industry_partners": [
            "Fine Arts Department, Ministry of Culture",
            "UNESCO Bangkok Office",
            "SEAMEO SPAFA Regional Centre for Archaeology and Fine Arts"
        ],
        "open_positions": [
            "Master's RA: pXRF Chemical Profiling of Ancient Bronze Artifacts",
            "PhD Fellow: Immersive AR/VR Reconstruction of Dvaravati Monuments"
        ],
        "website_url": "https://archae.su.ac.th",
        "image_url": "https://images.unsplash.com/photo-1582555172866-f73bb12a2ab3?w=800&q=80"
    },
    {
        "id": "su_advanced_ceramics_materials_lab",
        "name_th": "ศูนย์วิจัยเซรามิกขั้นสูงและวัสดุนวัตกรรม มหาวิทยาลัยศิลปากร",
        "name_en": "Advanced Ceramics & Functional Materials Research Center",
        "university": "Silpakorn University",
        "university_th": "มหาวิทยาลัยศิลปากร",
        "faculty": "Faculty of Engineering and Industrial Technology",
        "faculty_th": "คณะวิศวกรรมศาสตร์และเทคโนโลยีอุตสาหกรรม",
        "department": "Department of Materials Science and Engineering",
        "department_th": "ภาควิชาวิทยาการและวิศวกรรมวัสดุ",
        "lead_advisor_id": None,
        "member_faculty_ids": [],
        "description": "ศูนย์วิจัยที่ผสานศิลปศาสตร์แห่งเซรามิกเข้ากับวิศวกรรมวัสดุขั้นสูง มุ่งพัฒนาเซรามิกทนความร้อนสูง ไบโอเซรามิกเพื่อการแพทย์ และวัสดุกรองสารพิษในน้ำเสียอุตสาหกรรม",
        "research_domains": [
            "High-Temperature Structural Ceramics & Refractories",
            "Biocompatible Hydroxyapatite Ceramics for Bone Implants",
            "Porous Ceramic Membranes for Industrial Wastewater Filtration",
            "Dielectric & Piezoelectric Functional Ceramics"
        ],
        "flagship_equipment": [
            "High-Temperature Sintering Furnace (Up to 1700°C)",
            "BET Surface Area and Pore Size Analyzer",
            "Vickers Micro-Hardness Tester",
            "Rotational Rheometer for Ceramic Slurries"
        ],
        "industry_partners": [
            "COTTO (SCG Ceramics Public Company)",
            "Royal Porcelain Public Company Limited",
            "Western Digital (Thailand)"
        ],
        "open_positions": [
            "Master's RA: Macroporous Ceramic Membranes for Heavy Metal Removal",
            "PhD Candidate: High-Entropy Oxide Ceramics for Thermal Barrier Coatings"
        ],
        "website_url": "https://eng.su.ac.th",
        "image_url": "https://images.unsplash.com/photo-1565193566173-7a0ee3dbe261?w=800&q=80"
    },

    # =========================================================================
    # 7. MAE FAH LUANG UNIVERSITY (MFU)
    # =========================================================================
    {
        "id": "mfu_tea_coffee_innovation_center",
        "name_th": "สถาบันชาและกาแฟแห่งมหาวิทยาลัยแม่ฟ้าหลวง",
        "name_en": "Tea and Coffee Institute of Mae Fah Luang University",
        "university": "Mae Fah Luang University",
        "university_th": "มหาวิทยาลัยแม่ฟ้าหลวง",
        "faculty": "School of Agro-Industry",
        "faculty_th": "สำนักวิชาอุตสาหกรรมเกษตร",
        "department": "Department of Food Technology and Innovation",
        "department_th": "สาขาวิชาเทคโนโลยีและนวัตกรรมอาหาร",
        "lead_advisor_id": None,
        "member_faculty_ids": [],
        "description": "สถาบันวิจัยชาและกาแฟระดับชาติในพื้นที่ภูเขาสูงภาคเหนือ เชี่ยวชาญการปรับปรุงพันธุ์ อัตลักษณ์กลิ่นรส (Sensory & Flavor Chemistry) และการสกัดสารคาเทชินและกรดคลอโรเจนิกมูลค่าสูง",
        "research_domains": [
            "Flavor Chemistry & Sensory Science of Specialty Coffee",
            "Tea Polyphenol Extraction & Functional Health Beverages",
            "Specialty Arabica Cultivar Genomics & Climate Adaptation",
            "Zero-Waste Coffee Pulp Biorefinery Upcycling"
        ],
        "flagship_equipment": [
            "Gas Chromatography-Olfactometry-Mass Spectrometry (GC-O-MS)",
            "Specialty Coffee Association (SCA) Standard Cupping Sensory Lab",
            "Industrial Precision Pilot Coffee Roaster with Telemetry Logging",
            "High-Speed Counter-Current Chromatograph (HSCCC)"
        ],
        "industry_partners": [
            "Doi Chaang Coffee Original Co., Ltd.",
            "Doi Tung Development Project",
            "CP All Public Company",
            "Specialty Coffee Association of Thailand"
        ],
        "open_positions": [
            "Master's RA: Volatile Compound Profiles of Fermented Arabica Coffee",
            "PhD Candidate: Green Tea Bioactives for Neuroprotective Health"
        ],
        "website_url": "https://teacoffee.mfu.ac.th",
        "image_url": "https://images.unsplash.com/photo-1514432324607-a09d9b4aefdd?w=800&q=80"
    },
    {
        "id": "mfu_pm25_air_quality_center",
        "name_th": "ศูนย์วิจัยมลพิษทางอากาศและหมอกควันข้ามแดน มหาวิทยาลัยแม่ฟ้าหลวง",
        "name_en": "Center of Excellence in Atmospheric & Transboundary Haze Pollution",
        "university": "Mae Fah Luang University",
        "university_th": "มหาวิทยาลัยแม่ฟ้าหลวง",
        "faculty": "School of Science",
        "faculty_th": "สำนักวิชาวิทยาศาสตร์",
        "department": "Department of Environmental Science & Chemistry",
        "department_th": "สาขาวิทยาศาสตร์สิ่งแวดล้อมและเคมี",
        "lead_advisor_id": None,
        "member_faculty_ids": [],
        "description": "ศูนย์วิจัยเชิงลึกด้านมลพิษฝุ่นละอองขนาดเล็ก (PM2.5) ในอนุภูมิภาคลุ่มน้ำโขง ตรวจวัดองค์ประกอบทางเคมี แหล่งกำเนิดไอโซโทป และผลกระทบต่อสุขภาพระบบทางเดินหายใจ",
        "research_domains": [
            "PM2.5 Chemical Speciation & Carbonaceous Aerosols",
            "Biomass Burning Source Apportionment (Positive Matrix Factorization)",
            "Transboundary Atmospheric Dispersion Modeling",
            "Respiratory Cytotoxicity of Ambient Fine Particulates"
        ],
        "flagship_equipment": [
            "High-Volume Air Sampler with Quartz Filter Gravimetric Room",
            "Organic Carbon / Elemental Carbon (OC/EC) Aerosol Analyzer",
            "Ion Chromatograph (IC) for Atmospheric Inorganic Ions",
            "Boundary-Layer Atmospheric Lidar Profiler"
        ],
        "industry_partners": [
            "Chiang Rai Provincial Public Health Office",
            "Pollution Control Department (PCD)",
            "Mekong River Commission (MRC)"
        ],
        "open_positions": [
            "Master's RA: Chemical Fingerprinting of Agricultural Biomass Smoke",
            "PhD Candidate: Atmospheric Trajectory Modeling of Transboundary Haze"
        ],
        "website_url": "https://science.mfu.ac.th",
        "image_url": "https://images.unsplash.com/photo-1534088568595-a066f410bcda?w=800&q=80"
    },

    # =========================================================================
    # 8. THAKSIN UNIVERSITY (TSU)
    # =========================================================================
    {
        "id": "tsu_songkhla_lake_basin_center",
        "name_th": "สถาบันวิจัยและฟื้นฟูระบบนิเวศลุ่มน้ำทะเลสาบสงขลา มหาวิทยาลัยทักษิณ",
        "name_en": "Songkhla Lake Basin Ecological & Wetland Conservation Center",
        "university": "Thaksin University",
        "university_th": "มหาวิทยาลัยทักษิณ",
        "faculty": "Faculty of Science",
        "faculty_th": "คณะวิทยาศาสตร์",
        "department": "Department of Environmental Science & Aquatic Biology",
        "department_th": "สาขาวิทยาศาสตร์สิ่งแวดล้อมและชีววิทยาสัตว์น้ำ",
        "lead_advisor_id": None,
        "member_faculty_ids": [],
        "description": "ศูนย์วิจัยหลักที่ดูแลระบบนิเวศทะเลสาบ 3 น้ำ (น้ำจืด น้ำกร่อย น้ำเค็ม) ที่ใหญ่ที่สุดในประเทศไทย วิจัยการฟื้นฟูประชากรสัตว์น้ำเศรษฐกิจ นกน้ำ และการจัดการน้ำเสียชุมชน",
        "research_domains": [
            "Lagoon Ecosystem Health & Water Quality Indexing",
            "Brackish-Water Fishery Resource Conservation",
            "Mangrove Wetland Restoration & Blue Carbon Storage",
            "Sediment Nutrient Dynamics and Eutrophication Mitigation"
        ],
        "flagship_equipment": [
            "Multiparameter Water Quality Sonde (YSI EXO2)",
            "Acoustic Doppler Current Profiler (ADCP) for Tidal Flow Analysis",
            "Automated Nutrients Auto-Analyzer (Nitrate, Phosphate, Silicate)",
            "Research Catamaran Sampling Vessel"
        ],
        "industry_partners": [
            "Department of Marine and Coastal Resources",
            "Songkhla Lake Basin Development Committee",
            "Petroleum Authority of Thailand Exploration and Production (PTTEP)"
        ],
        "open_positions": [
            "Master's RA: Eutrophication Dynamics in Upper Songkhla Lake",
            "PhD Candidate: Blue Carbon Valuation of Mangrove Wetlands"
        ],
        "website_url": "https://sci.tsu.ac.th",
        "image_url": "https://images.unsplash.com/photo-1507525428034-b723cf961d3e?w=800&q=80"
    },
    {
        "id": "tsu_southern_halal_food_lab",
        "name_th": "ศูนย์วิจัยและพัฒนาอาหารฮาลาลและนวัตกรรมเกษตรภาคใต้ มหาวิทยาลัยทักษิณ",
        "name_en": "Southern Halal Food Innovation & Agro-Biotech Research Lab",
        "university": "Thaksin University",
        "university_th": "มหาวิทยาลัยทักษิณ",
        "faculty": "Faculty of Technology and Community Development",
        "faculty_th": "คณะเทคโนโลยีและการพัฒนาชุมชน",
        "department": "Department of Food Technology and Nutrition",
        "department_th": "สาขาวิชาเทคโนโลยีอาหารและโภชนาการ",
        "lead_advisor_id": None,
        "member_faculty_ids": [],
        "description": "ศูนย์วิจัยที่เชื่อมโยงมาตรฐานอาหารฮาลาลสากลเข้ากับการแปรรูปผลผลิตเกษตรภาคใต้ (ส้มโอทับทิมสยาม ข้าวสังข์หยด ลองกอง) และการตรวจวิเคราะห์สิ่งปนเปื้อนตามหลักศาสนบัญญัติ",
        "research_domains": [
            "DNA-based Porcine Contamination Forensic Detection",
            "Sangyod Rice Nutrient Bioavailability & Glycemic Index",
            "Halal-Certified Functional Snack Formulation",
            "Sustainable Palm Oil Food Emulsion & Oleogel Technology"
        ],
        "flagship_equipment": [
            "Real-Time PCR Halal DNA Authentication Kit Platform",
            "Texture Analyzer with Multi-Sample Testing Fixtures",
            "Differential Scanning Calorimeter (DSC) for Fat Crystallization",
            "Sensory Tasting Lab Compliant with ISO Standards"
        ],
        "industry_partners": [
            "Central Islamic Committee of Thailand (CICOT)",
            "Southern Border Provinces Administrative Centre (SBPAC)",
            "Khao Sangyod Phatthalung GI Association"
        ],
        "open_positions": [
            "Master's RA: Low-GI Baked Goods from Sangyod Brown Rice",
            "PhD Fellowship: Rapid Biosensors for Halal Food Authentication"
        ],
        "website_url": "https://ftcd.tsu.ac.th",
        "image_url": "https://images.unsplash.com/photo-1498837167922-ddd27525d352?w=800&q=80"
    },

    # =========================================================================
    # 9. UBON RATCHATHANI UNIVERSITY (UBU)
    # =========================================================================
    {
        "id": "ubu_mekong_water_agro_hydrology_lab",
        "name_th": "ศูนย์วิจัยอุทกวิทยาเกษตรและการจัดการทรัพยากรน้ำลุ่มน้ำโขง-ชี-มูล มหาวิทยาลัยอุบลราชธานี",
        "name_en": "Mekong-Chi-Mun Agro-Hydrology & Water Management Research Center",
        "university": "Ubon Ratchathani University",
        "university_th": "มหาวิทยาลัยอุบลราชธานี",
        "faculty": "Faculty of Engineering",
        "faculty_th": "คณะวิศวกรรมศาสตร์",
        "department": "Department of Civil Engineering & Water Resources",
        "department_th": "ภาควิชาวิศวกรรมโยธาและทรัพยากรน้ำ",
        "lead_advisor_id": None,
        "member_faculty_ids": [],
        "description": "ศูนย์วิจัยด้านวิศวกรรมน้ำชั้นนำของภาคอีสานตอนล่าง มุ่งพัฒนาแบบจำลองคาดการณ์อุทกภัยแม่น้ำมูล-แม่น้ำโขง ระบบสูบน้ำพลังงานแสงอาทิตย์เพื่อการเกษตรฤดูแล้ง และการรับมือวิกฤตภูมิอากาศ",
        "research_domains": [
            "Basin-Scale Hydrological & Hydraulic River Modeling",
            "AI Flood Forecasting & Flash Flood Early Warning Systems",
            "Solar-Powered Distributed Agricultural Irrigation",
            "Transboundary Mekong Flow Alteration & Sediment Tracking"
        ],
        "flagship_equipment": [
            "High-Performance Computing Cluster for 2D Hydraulic Flood Modeling",
            "Autonomous Bathymetric Survey Boat with Dual-Frequency Sonar",
            "Groundwater Radar & Geophysical Resistivity Imaging Suite",
            "Automated Real-Time Telemetry Water Level Stations"
        ],
        "industry_partners": [
            "Royal Irrigation Department (RID Thailand)",
            "Office of the National Water Resources (ONWR)",
            "Mekong River Commission Secretariat"
        ],
        "open_positions": [
            "Master's RA: Hydrodynamic 2D Modeling of Mun River Inundation",
            "PhD Candidate: Climate Change Impact on Lower Mekong Agricultural Yields"
        ],
        "website_url": "https://eng.ubu.ac.th",
        "image_url": "https://images.unsplash.com/photo-1541888946425-d0fbb186c5f7?w=800&q=80"
    },
    {
        "id": "ubu_biomass_renewable_energy_lab",
        "name_th": "ศูนย์วิจัยพลังงานชีวมวลและวัสดุคาร์บอนชีวภาพอีสานใต้ มหาวิทยาลัยอุบลราชธานี",
        "name_en": "Lower Northeast Biomass & Bio-Carbon Renewable Energy Research Center",
        "university": "Ubon Ratchathani University",
        "university_th": "มหาวิทยาลัยอุบลราชธานี",
        "faculty": "Faculty of Science",
        "faculty_th": "คณะวิทยาศาสตร์",
        "department": "Department of Chemistry & Energy Materials",
        "department_th": "ภาควิชาเคมีและวัสดุพลังงาน",
        "lead_advisor_id": None,
        "member_faculty_ids": [],
        "description": "ศูนย์วิจัยพลังงานทดแทนที่แปรรูปวัสดุเหลือทิ้งทางการเกษตร (แกลบ ชานอ้อย ฟางข้าว และเหง้ามันสำปะหลัง) เป็นพลังงานเม็ดชีวมวลคุณภาพสูง แก๊สชีวมวล และถ่านกัมมันต์สำหรับแบตเตอรี่",
        "research_domains": [
            "Biomass Gasification & Pyrolysis Engineering",
            "Agricultural Residue Torrefaction & High-Density Pelletization",
            "Activated Carbon Synthesis for Supercapacitor Electrodes",
            "Biogas Upgrading & Microbial Anaerobic Digestion"
        ],
        "flagship_equipment": [
            "Continuous Dual-Stage Fluidized Bed Gasifier (10 kWth)",
            "Bomb Calorimeter for Gross Heat Value Determination",
            "Specific Surface Area (BET) and Micropore Gas Sorption Analyzer",
            "Thermal Conductive Exhaust Gas Chromatograph (GC-TCD/FID)"
        ],
        "industry_partners": [
            "Electricity Generating Authority of Thailand (EGAT)",
            "Ubon Bio Ethanol Public Company Limited (UBE)",
            "Provincial Electricity Authority (PEA)"
        ],
        "open_positions": [
            "Master's RA: Upgraded Bio-Pellets from Cassava Rhizome Waste",
            "PhD Fellowship: Activated Carbon from Biomass for Lithium-Ion Batteries"
        ],
        "website_url": "https://sci.ubu.ac.th",
        "image_url": "https://images.unsplash.com/photo-1473341304170-971dccb5ac1e?w=800&q=80"
    },

    # =========================================================================
    # 10. KMUTT FIBO & SIT (King Mongkut's University of Technology Thonburi)
    # =========================================================================
    {
        "id": "kmutt_fibo_industrial_robotics_lab",
        "name_th": "ห้องปฏิบัติการหุ่นยนต์อุตสาหกรรมและระบบการผลิตอัตโนมัติ (IRSAL) มจธ.",
        "name_en": "FIBO Industrial Robotics and Service Automation Laboratory (IRSAL)",
        "university": "King Mongkut's University of Technology Thonburi",
        "university_th": "มหาวิทยาลัยเทคโนโลยีพระจอมเกล้าธนบุรี",
        "faculty": "Institute of Field Robotics (FIBO)",
        "faculty_th": "สถาบันวิทยาการหุ่นยนต์ภาคสนาม (FIBO)",
        "department": "Department of Robotics and Automation Engineering",
        "department_th": "สาขาวิชาวิศวกรรมหุ่นยนต์และระบบอัตโนมัติ",
        "lead_advisor_id": None,
        "member_faculty_ids": [],
        "description": "ห้องปฏิบัติการวิจัยชั้นนำของประเทศไทยที่ก่อตั้งโดย FIBO มุ่งพัฒนาหุ่นยนต์แขนกลอุตสาหกรรม หุ่นยนต์ร่วมปฏิบัติงาน (Cobots) และระบบดิจิทัลทวิน (Digital Twin) สำหรับโรงงานอัจฉริยะ Industry 4.0",
        "research_domains": [
            "Collaborative Robotics (Cobots) Safety & Control",
            "Digital Twin & Physics-based Factory Simulation",
            "Automated Guided Vehicles (AGV/AMR) Fleet Coordination",
            "AI Vision-Guided High-Speed Assembly Pick-and-Place"
        ],
        "flagship_equipment": [
            "KUKA & Universal Robots (UR5/UR10) Industrial Cobot Arms",
            "Motion Capture OptiTrack Multi-Camera System",
            "NVIDIA Omniverse High-Fidelity Factory Simulation Workstation",
            "Industrial PLC Integration and Real-time EtherCAT Testbed"
        ],
        "industry_partners": [
            "Thai Robotics Society (TRS)",
            "DENSO (Thailand) Co., Ltd.",
            "Mitsubishi Electric Factory Automation",
            "Delta Electronics (Thailand)"
        ],
        "open_positions": [
            "Master's RA: Reinforcement Learning for Robotic Trajectory Planning",
            "PhD Candidate: Autonomous Mobile Robot Swarm Fleet Logistics"
        ],
        "website_url": "https://fibo.kmutt.ac.th",
        "image_url": "https://images.unsplash.com/photo-1485827404703-89b55fcc595e?w=800&q=80"
    },
    {
        "id": "kmutt_sit_ai_bigdata_innovation_center",
        "name_th": "ศูนย์วิจัยปัญญาประดิษฐ์และนวัตกรรมข้อมูลขนาดใหญ่ คณะเทคโนโลยีสารสนเทศ มจธ.",
        "name_en": "SIT Artificial Intelligence & Big Data Innovation Center (AIBIC)",
        "university": "King Mongkut's University of Technology Thonburi",
        "university_th": "มหาวิทยาลัยเทคโนโลยีพระจอมเกล้าธนบุรี",
        "faculty": "School of Information Technology",
        "faculty_th": "คณะเทคโนโลยีสารสนเทศ",
        "department": "Department of Information Technology & Data Science",
        "department_th": "สาขาวิชาเทคโนโลยีสารสนเทศและวิทยาการข้อมูล",
        "lead_advisor_id": None,
        "member_faculty_ids": [],
        "description": "ศูนย์นวัตกรรมด้าน AI และ Data Analytics ชั้นนำของ มจธ. เชี่ยวชาญการประมวลผลภาษาธรรมชาติภาษาไทย (Thai NLP) แบบจำลองภาษาขนาดใหญ่ (LLMs) และการวิเคราะห์ข้อมูลสุขภาพและการเงินระดับองค์กร",
        "research_domains": [
            "Large Language Models & Thai Natural Language Processing",
            "Federated Learning & Privacy-Preserving AI",
            "Healthcare Predictive Analytics & Medical Imaging AI",
            "Enterprise Big Data Architecture & Real-time Stream Analytics"
        ],
        "flagship_equipment": [
            "Enterprise AI Supercomputing Cluster (8x NVIDIA A100 80GB SXM4)",
            "Petabyte-scale High-Throughput NVMe Ceph Storage System",
            "Isolated Secure Data Enclave for Financial & Healthcare Research"
        ],
        "industry_partners": [
            "Kasikorn Business-Technology Group (KBTG)",
            "SCB TechX",
            "True Digital Group",
            "Siriraj Hospital Digital Health Tech Center"
        ],
        "open_positions": [
            "Master's RA: Domain-Adapted Thai Large Language Models",
            "PhD Fellow: Differential Privacy in Federated Healthcare Analytics"
        ],
        "website_url": "https://www.sit.kmutt.ac.th",
        "image_url": "https://images.unsplash.com/photo-1518770660439-4636190af475?w=800&q=80"
    },

    # =========================================================================
    # 11. REGIONAL FLAGSHIP CENTERS (NU, SUT, CMU, KKU, PSU, KU-SRC)
    # =========================================================================
    {
        "id": "nu_solar_energy_research_center",
        "name_th": "วิทยาลัยพลังงานทดแทนและสมาร์ตกริด (SERT) มหาวิทยาลัยนเรศวร",
        "name_en": "School of Renewable Energy and Smart Grid Technology (SERT-NU)",
        "university": "Naresuan University",
        "university_th": "มหาวิทยาลัยนเรศวร",
        "faculty": "School of Renewable Energy and Smart Grid Technology",
        "faculty_th": "วิทยาลัยพลังงานทดแทนและสมาร์ตกริด",
        "department": "Department of Smart Grid and Renewable Energy Systems",
        "department_th": "สาขาวิชาระบบโครงข่ายไฟฟ้าอัจฉริยะและพลังงานทดแทน",
        "lead_advisor_id": None,
        "member_faculty_ids": [],
        "description": "ศูนย์วิจัยพลังงานแสงอาทิตย์และสมาร์ตกริดชั้นนำของภาคเหนือตอนล่างและประเทศไทย เป็นศูนย์ทดสอบมาตรฐานเซลล์แสงอาทิตย์ระดับชาติ และวิจัยระบบไมโครกริดชุมชน",
        "research_domains": [
            "Solar PV Module Reliability & Degradation Testing",
            "Microgrid Energy Management Systems (EMS)",
            "Battery Energy Storage Integration for Grid Stability",
            "Floating Solar Photovoltaic Agro-Voltaic Synergy"
        ],
        "flagship_equipment": [
            "Class AAA Steady-State Solar Simulator",
            "Smart Grid Real-Time Digital Simulator (RTDS)",
            "Environmental Thermal-Cycling Walk-in Chambers (-40°C to +85°C)",
            "Electroluminescence (EL) Solar Cell Crack Imaging"
        ],
        "industry_partners": [
            "Provincial Electricity Authority (PEA)",
            "Energy Policy and Planning Office (EPPO)",
            "Bangchak Corporation Public Company",
            "B.Grimm Power"
        ],
        "open_positions": [
            "Master's RA: AI Optimal Scheduling for Solar-Battery Microgrids",
            "PhD Candidate: Perovskite-Silicon Tandem Photovoltaic Durability"
        ],
        "website_url": "https://sert.nu.ac.th",
        "image_url": "https://images.unsplash.com/photo-1509391365360-2e959784a276?w=800&q=80"
    },
    {
        "id": "sut_synchrotron_materials_center",
        "name_th": "ศูนย์วิจัยขั้นสูงด้านวัสดุศาสตร์และแสงซินโครตรอน มหาวิทยาลัยเทคโนโลยีสุรนารี",
        "name_en": "Center of Excellence in Advanced Functional Materials & Synchrotron Science",
        "university": "Suranaree University of Technology",
        "university_th": "มหาวิทยาลัยเทคโนโลยีสุรนารี",
        "faculty": "Institute of Science",
        "faculty_th": "สำนักวิชาวิทยาศาสตร์",
        "department": "School of Physics & Materials Science",
        "department_th": "สาขาวิชาฟิสิกส์และวิทยาศาสตร์วัสดุ",
        "lead_advisor_id": None,
        "member_faculty_ids": [],
        "description": "ศูนย์วิจัยที่ร่วมมือใกล้ชิดกับสถาบันวิจัยแสงซินโครตรอนแห่งชาติ (SLRI) ศึกษาโครงสร้างผลึกระดับอะตอม วัสดุกักเก็บพลังงาน และวัสดุแม่เหล็กไฟฟ้าขั้นสูง",
        "research_domains": [
            "Synchrotron X-ray Absorption Spectroscopy (XAS/XANES/EXAFS)",
            "Advanced Thermoelectric & Piezoelectric Crystals",
            "Solid-State Electrolyte Interface Dynamics",
            "High-Entropy Alloys for Extreme Environments"
        ],
        "flagship_equipment": [
            "Access to Synchrotron Beamlines (XAS, Photoemission, Infrared)",
            "Physical Property Measurement System (PPMS EverCool II)",
            "High-Resolution Transmission Electron Microscope (HR-TEM 200kV)",
            "Arc Melting Furnace for High-Purity Alloy Synthesis"
        ],
        "industry_partners": [
            "Synchrotron Light Research Institute (Public Organization)",
            "Western Digital Thailand",
            "PTT Global Chemical (GC)"
        ],
        "open_positions": [
            "PhD Fellow: In-situ Synchrotron Operando Battery Studies",
            "Master's RA: High-Entropy Thermoelectric Energy Harvesting"
        ],
        "website_url": "https://science.sut.ac.th",
        "image_url": "https://images.unsplash.com/photo-1507668077129-56e32842fceb?w=800&q=80"
    },
    {
        "id": "cmu_biomedical_engineering_center",
        "name_th": "สถาบันวิศวกรรมชีวการแพทย์ (BMEI) มหาวิทยาลัยเชียงใหม่",
        "name_en": "Biomedical Engineering Institute (BMEI-CMU)",
        "university": "Chiang Mai University",
        "university_th": "มหาวิทยาลัยเชียงใหม่",
        "faculty": "Biomedical Engineering Institute",
        "faculty_th": "สถาบันวิศวกรรมชีวการแพทย์",
        "department": "Department of Biomedical Engineering",
        "department_th": "สาขาวิชาวิศวกรรมชีวการแพทย์",
        "lead_advisor_id": None,
        "member_faculty_ids": [],
        "description": "สถาบันวิจัยชั้นแนวหน้าด้านวิศวกรรมชีวการแพทย์ มุ่งเน้นการพัฒนาข้อต่อเทียม 3 มิติเฉพาะบุคคล (Patient-Specific Implants) อุปกรณ์ฟื้นฟูผู้ป่วยหลอดเลือดสมอง และเซนเซอร์ชีวภาพ",
        "research_domains": [
            "Additive Manufacturing of Titanium Bone Implants",
            "Neuro-Rehabilitation Exoskeleton Robotics",
            "Electrochemical Biosensors for Point-of-Care Diagnostics",
            "AI-Assisted Diagnostic Ultrasound and CT Imaging"
        ],
        "flagship_equipment": [
            "Medical-Grade Selective Laser Melting (SLM) Titanium 3D Printer",
            "Dynamic Biomechanical Gait Analysis System with Force Plates",
            "Cleanroom Class 10,000 for Medical Device Packaging",
            "Micro-CT System for Bone Ingrowth Density Analysis"
        ],
        "industry_partners": [
            "Maharaj Nakorn Chiang Mai Hospital",
            "National Metal and Materials Technology Center (MTEC)",
            "Orthopeasia Co., Ltd."
        ],
        "open_positions": [
            "Master's RA: Porous Titanium Scaffold 3D Printing for Osteointegration",
            "PhD Candidate: EEG-Triggered Wearable Hand Rehabilitation Exoskeleton"
        ],
        "website_url": "https://bmei.cmu.ac.th",
        "image_url": "https://images.unsplash.com/photo-1516549655169-df83a0774514?w=800&q=80"
    },
    {
        "id": "kku_battery_energy_storage_center",
        "name_th": "โรงงานต้นแบบและศูนย์นวัตกรรมแบตเตอรี่ลิเธียมไอออน มหาวิทยาลัยขอนแก่น",
        "name_en": "Lithium-Ion Battery Pilot Plant & Energy Storage Center (KKU-BATT)",
        "university": "Khon Kaen University",
        "university_th": "มหาวิทยาลัยขอนแก่น",
        "faculty": "Faculty of Science & Faculty of Engineering",
        "faculty_th": "คณะวิทยาศาสตร์และคณะวิศวกรรมศาสตร์",
        "department": "Materials Science and Nanotechnology Program",
        "department_th": "สาขาวิชาวิทยาศาสตร์วัสดุและนาโนเทคโนโลยี",
        "lead_advisor_id": None,
        "member_faculty_ids": [],
        "description": "โรงงานแบตเตอรี่ลิเธียมไอออนแห่งแรกของสถาบันอุดมศึกษาไทย พัฒนาเซลล์แบตเตอรี่แบบถุง (Pouch Cells) จากซิลิกอนแกลบข้าวและขยะเกษตรอีสาน เพื่อรองรับยานยนต์ไฟฟ้า (EV) และระบบกักเก็บพลังงานแสงอาทิตย์",
        "research_domains": [
            "Bio-Silica Extraction from Rice Husk for High-Capacity Anodes",
            "Pouch-Cell Pilot Line Manufacturing and Safety Testing",
            "Sodium-Ion Battery Next-Generation Chemistry",
            "Battery Recycling and Critical Metal Hydrometallurgy"
        ],
        "flagship_equipment": [
            "Automated Pilot-Scale Pouch Cell Slurry Coating & Stacking Line",
            "Ultra-Dry Room (Dew Point < -50°C) for Battery Cell Assembly",
            "Multi-channel High-Current Battery Cycler (5V 100A per channel)",
            "Battery Nail Penetration & Thermal Abuse Safety Chamber"
        ],
        "industry_partners": [
            "Energy Absolute Public Company Limited (EA)",
            "Electricity Generating Authority of Thailand (EGAT)",
            "Bangchak Corporation"
        ],
        "open_positions": [
            "Master's RA: Rice Husk Nano-Silicon Anodes for 500 Wh/kg Cells",
            "PhD Candidate: Solid-State Electrolytes for Fire-Safe EV Batteries"
        ],
        "website_url": "https://battery.kku.ac.th",
        "image_url": "https://images.unsplash.com/photo-1558441719-8b489c63f77a?w=800&q=80"
    },
    {
        "id": "psu_marine_natural_products_center",
        "name_th": "ศูนย์ความเป็นเลิศด้านผลิตภัณฑ์ธรรมชาติและสารออกฤทธิ์ทางชีวภาพ มหาวิทยาลัยสงขลานครินทร์",
        "name_en": "Natural Products & Marine Bioactives Research Center of Excellence",
        "university": "Prince of Songkla University",
        "university_th": "มหาวิทยาลัยสงขลานครินทร์",
        "faculty": "Faculty of Science",
        "faculty_th": "คณะวิทยาศาสตร์",
        "department": "Department of Chemistry",
        "department_th": "สาขาวิทยาศาสตร์กายภาพ (เคมี)",
        "lead_advisor_id": None,
        "member_faculty_ids": [],
        "description": "ศูนย์วิจัยชั้นนำของภูมิภาคเอเชียตะวันออกเฉียงใต้ด้านเคมีผลิตภัณฑ์ธรรมชาติ สกัดและพิสูจน์โครงสร้างสารทุติยภูมิจากเชื้อราทะเล ดอกไม้ทะเล ฟองน้ำ และพืชสมุนไพรป่าชายเลนเพื่อพัฒนายาปฏิชีวนะและต้านมะเร็ง",
        "research_domains": [
            "Marine Sponge and Endophytic Fungi Bioactive Metabolites",
            "Structure Elucidation by 2D NMR and High-Resolution Mass Spectrometry",
            "Anti-MRSA Antibiotic and Cytotoxic Natural Molecule Screening",
            "Total Synthesis and Semi-Synthetic Drug Modification"
        ],
        "flagship_equipment": [
            "500 MHz Nuclear Magnetic Resonance (NMR) Spectrometer with CryoProbe",
            "High-Resolution Electrospray Ionization Time-of-Flight (ESI-HR-TOF-MS)",
            "Semi-Preparative and Analytical HPLC Chiral Separation Systems",
            "Cell Culture Bioassay Suite for Cytotoxicity & Antimicrobial Testing"
        ],
        "industry_partners": [
            "Government Pharmaceutical Organization (GPO)",
            "Mega Lifesciences Public Company Limited",
            "National Center for Genetic Engineering and Biotechnology (BIOTEC)"
        ],
        "open_positions": [
            "Master's Fellowship: Novel Alkaloids from Andaman Sea Sponges",
            "PhD Fellow: Anti-Biofilm Cyclic Peptides from Mangrove Fungi"
        ],
        "website_url": "https://natprod.psu.ac.th",
        "image_url": "https://images.unsplash.com/photo-1532187863486-abf9dbad1b69?w=800&q=80"
    },
    {
        "id": "ku_src_maritime_logistics_lab",
        "name_th": "ห้องปฏิบัติการวิจัยการจัดการโลจิสติกส์การเดินเรือและท่าเรืออัจฉริยะ มก. ศรีราชา",
        "name_en": "Maritime Logistics & Smart Port Operations Research Laboratory",
        "university": "Kasetsart University",
        "university_th": "มหาวิทยาลัยเกษตรศาสตร์",
        "faculty": "Faculty of International Maritime Studies",
        "faculty_th": "คณะพาณิชยนาวีนานาชาติ",
        "department": "Department of Nautical Science and Maritime Logistics",
        "department_th": "สาขาวิชาวิทยาการเดินเรือและการจัดการโลจิสติกส์ทางน้ำ",
        "lead_advisor_id": None,
        "member_faculty_ids": [],
        "description": "ห้องปฏิบัติการวิจัยโลจิสติกส์พาณิชยนาวีติดท่าเรือแหลมฉบัง เชี่ยวชาญการจำลองการเดินเรือด้วยแบบจำลอง 360 องศา การบริหารจัดการตู้สินค้าอัจฉริยะ และการลดการปล่อยก๊าซเรือนกระจกในอุตสาหกรรมท่าเรือ (Green Port)",
        "research_domains": [
            "Full-Mission Ship Handling Simulation & Navigational Safety",
            "Container Terminal Berth & Quay Crane Optimization Algorithms",
            "Cold Ironing & Port Carbon Footprint Decarbonization",
            "Autonomous Surface Vessels (ASV) Coastal Navigation Systems"
        ],
        "flagship_equipment": [
            "Transas Full-Mission 360-Degree Bridge Ship Simulator",
            "Smart Port Digital Twin Simulation Platform",
            "Engine Room Simulator (ERS) with Maritime Telemetry",
            "Vessel Traffic Service (VTS) Radar and AIS Tracking Station"
        ],
        "industry_partners": [
            "Port Authority of Thailand (Laem Chabang Port)",
            "Hutchison Ports Thailand",
            "Thai Shipowners' Association",
            "Eastern Economic Corridor (EEC) Office"
        ],
        "open_positions": [
            "Master's RA: AI Dynamic Berth Allocation for Mega-Container Ships",
            "PhD Candidate: Decarbonization Pathways for Gulf of Thailand Shipping"
        ],
        "website_url": "https://ims.src.ku.ac.th",
        "image_url": "https://images.unsplash.com/photo-1586528116311-ad8dd3c8310d?w=800&q=80"
    },
    {
        "id": "wu_coastal_aquaculture_biotech_center",
        "name_th": "ศูนย์ความเป็นเลิศด้านเพาะเลี้ยงสัตว์น้ำชายฝั่งและเทคโนโลยีชีวภาพ มหาวิทยาลัยวลัยลักษณ์",
        "name_en": "Center of Excellence in Coastal Aquaculture & Marine Biotechnology",
        "university": "Walailak University",
        "university_th": "มหาวิทยาลัยวลัยลักษณ์",
        "faculty": "School of Agricultural Technology and Food Industry",
        "faculty_th": "สำนักวิชาเทคโนโลยีการเกษตรและอุตสาหกรรมอาหาร",
        "department": "Department of Fishery Science and Aquaculture",
        "department_th": "สาขาวิชาวิทยาศาสตร์การประมงและการเพาะเลี้ยงสัตว์น้ำ",
        "lead_advisor_id": None,
        "member_faculty_ids": [],
        "description": "ศูนย์วิจัยการเพาะเลี้ยงสัตว์น้ำชายฝั่งอ่าวไทย มุ่งพัฒนาภูมิคุ้มกันโรคกุ้งขาวแวนนาไม การปรับปรุงพันธุ์ปูดำ และระบบน้ำหมุนเวียนแบบปิด (Recirculating Aquaculture Systems - RAS) ที่เป็นมิตรต่อสิ่งแวดล้อม",
        "research_domains": [
            "Shrimp Disease Prevention & Probiotic Feed Additives",
            "Recirculating Aquaculture Systems (RAS) Water Bio-Filtration",
            "Mud Crab (Scylla olivacea) Larviculture & Hatchery Biotechnology",
            "Marine Microalgae Culture for Astaxanthin and Omega-3 Lipids"
        ],
        "flagship_equipment": [
            "Indoor Industrial RAS System with Ozone Fractionation",
            "Molecular Pathology Inverted Phase-Contrast Microscope",
            "Gas Chromatography (GC-FID) for Fatty Acid Methyl Esters (FAME)",
            "Automated Water Quality Real-Time Sensor Array"
        ],
        "industry_partners": [
            "Charoen Pokphand Foods (CPF Aquaculture Division)",
            "Thai Union Group Public Company Limited",
            "Department of Fisheries, Ministry of Agriculture"
        ],
        "open_positions": [
            "Master's RA: Synbiotic Diets for Enhanced Shrimp Immune Resistance",
            "PhD Fellow: High-Density Mud Crab Indoor Farming Systems"
        ],
        "website_url": "https://agri.wu.ac.th",
        "image_url": "https://images.unsplash.com/photo-1544551763-46a013bb70d5?w=800&q=80"
    },
    {
        "id": "mfu_medicinal_cosmeceuticals_lab",
        "name_th": "ศูนย์นวัตกรรมเครื่องสำอางและเวชสำอางธรรมชาติแห่งล้านนา มหาวิทยาลัยแม่ฟ้าหลวง",
        "name_en": "Lanna Natural Cosmetics and Innovative Cosmeceuticals Center",
        "university": "Mae Fah Luang University",
        "university_th": "มหาวิทยาลัยแม่ฟ้าหลวง",
        "faculty": "School of Cosmetic Science",
        "faculty_th": "สำนักวิชาวิทยาศาสตร์เครื่องสำอาง",
        "department": "Department of Cosmetic Science and Technology",
        "department_th": "สาขาวิชาวิทยาศาสตร์เครื่องสำอางและเทคโนโลยี",
        "lead_advisor_id": None,
        "member_faculty_ids": [],
        "description": "ศูนย์วิจัยแห่งแรกและแห่งเดียวของไทยที่อุทิศให้กับวิทยาศาสตร์เครื่องสำอางอย่างครบวงจร วิจัยสารสกัดจากพืชพรรณเมืองหนาว ชา กาแฟ และสมุนไพรชาติพันธุ์เพื่อเวชสำอางชะลอวัย",
        "research_domains": [
            "Anti-Tyrosinase & Skin Whitening Phytochemical Screening",
            "Nano-Emulsion & Liposomal Encapsulation Stability",
            "Clinical Skin Efficacy Assessment (Transepidermal Water Loss)",
            "Microbiome-Friendly Clean Beauty Cosmeceutical Formulations"
        ],
        "flagship_equipment": [
            "Courage+Khazaka (C+K) Non-Invasive Skin Biophysical Testing Suite",
            "High-Pressure Homogenizer for Nano-Emulsion Synthesis (2000 bar)",
            "Laser Diffraction Particle Size Analyzer (Malvern Mastersizer)",
            "Sun Protection Factor (SPF) In-Vitro Transmittance Analyzer"
        ],
        "industry_partners": [
            "S&J International Enterprises Public Company Limited",
            "Mistine (Better Way Thailand Co., Ltd.)",
            "Giffarine Skyline Unity Co., Ltd.",
            "L'Oréal Thailand Research Collaborations"
        ],
        "open_positions": [
            "Master's RA: Coffee Oil Encapsulation in Solid Lipid Nanoparticles",
            "PhD Candidate: Northern Botanical Extracts for Skin Barrier Repair"
        ],
        "website_url": "https://cosmeticscience.mfu.ac.th",
        "image_url": "https://images.unsplash.com/photo-1522337360788-8b13dee7a37e?w=800&q=80"
    }
]
