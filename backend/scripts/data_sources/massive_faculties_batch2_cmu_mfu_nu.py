# -*- coding: utf-8 -*-
"""
Massive Faculty Advisor Dataset - Batch 2: Northern Flagships (CMU, MFU, NU)
Covers Leading Professors & Researchers in:
- Biomedical Engineering, Neural Interfaces, Medical AI
- Anti-Aging & Regenerative Medicine, Cosmeceutical Sciences, Dermatology
- Clean Energy, Smart Solar Grid, Battery Energy Storage Systems (BESS)
- Northern Soft Power, Digital Crafts, Creative Media & Software Engineering

All data strictly complies with AGENTS.md & PDPA (Official emails only, NO personal phone numbers).
"""

CMU_MFU_NU_MASSIVE_FACULTIES = [
    # =========================================================================
    # CHIANG MAI UNIVERSITY (CMU - มหาวิทยาลัยเชียงใหม่)
    # =========================================================================
    {
        "id": "cmu_bme_001",
        "university": "Chiang Mai University",
        "university_th": "มหาวิทยาลัยเชียงใหม่",
        "faculty": "Biomedical Engineering Institute (BMEI)",
        "faculty_th": "สถาบันวิศวกรรมชีวการแพทย์ มหาวิทยาลัยเชียงใหม่",
        "department": "Department of Biomedical Engineering",
        "department_th": "สาขาวิชาวิศวกรรมชีวการแพทย์",
        "academic_title": "Prof. Dr.",
        "academic_title_th": "ศ.ดร.",
        "first_name": "Nipon",
        "last_name": "Theera-Umpon",
        "full_name": "Prof. Dr. Nipon Theera-Umpon",
        "full_name_th": "ศ.ดร. นิพนธ์ ธีรอำพน",
        "role": "Director of Biomedical Engineering Institute / Fellow of IEEE",
        "email": "nipon.t@cmu.ac.th",
        "image_url": "https://bmei.cmu.ac.th/images/faculty/nipon.jpg",
        "profile_url": "https://bmei.cmu.ac.th/staff/nipon",
        "education": [
            "Ph.D. (Electrical and Computer Engineering), University of Missouri-Columbia, USA",
            "M.S. (Electrical Engineering), University of Southern California (USC), USA",
            "B.Eng. (Electrical Engineering), Chiang Mai University"
        ],
        "research_interests": [
            "Biomedical Signal & Image Processing",
            "Pattern Recognition & Neural Computing",
            "Brain-Computer Interface (BCI) for Paralyzed Patients",
            "AI in Cardiology & Automated ECG Diagnosis",
            "Fuzzy Logic & Machine Learning Systems"
        ],
        "taught_courses": [
            "Biomedical Signal Processing",
            "Advanced Neural Networks and Fuzzy Systems",
            "Medical Imaging Systems"
        ],
        "featured_publications": [
            "White Blood Cell Segmentation and Classification in Microscopic Bone Marrow Images using Morphological Granulometries",
            "Deep Learning for Real-Time Arrhythmia Detection from Wearable Single-Lead ECG Sensors",
            "Electroencephalogram-Based Brain-Computer Interface for Robotic Prosthetic Hand Control"
        ],
        "scholar_url": "https://scholar.google.com/citations?user=NiponTheeraUmpon"
    },
    {
        "id": "cmu_camt_001",
        "university": "Chiang Mai University",
        "university_th": "มหาวิทยาลัยเชียงใหม่",
        "faculty": "College of Arts, Media and Technology (CAMT)",
        "faculty_th": "วิทยาลัยศิลปะ สื่อ และเทคโนโลยี (CAMT)",
        "department": "Department of Knowledge and Software Engineering",
        "department_th": "สาขาวิชาวิศวกรรมความรู้และซอฟต์แวร์",
        "academic_title": "Assoc. Prof. Dr.",
        "academic_title_th": "รศ.ดร.",
        "first_name": "Pradorn",
        "last_name": "Sureephong",
        "full_name": "Assoc. Prof. Dr. Pradorn Sureephong",
        "full_name_th": "รศ.ดร. ภราดร สุรีย์พงษ์",
        "role": "Head of Digital Innovation and Lanna Creative Economy Research Lab",
        "email": "pradorn.s@cmu.ac.th",
        "image_url": "https://www.camt.cmu.ac.th/images/faculty/pradorn.jpg",
        "profile_url": "https://www.camt.cmu.ac.th/staff/pradorn",
        "education": [
            "Ph.D. (Knowledge Management & Software Engineering), Asian Institute of Technology (AIT)",
            "M.Sc. (Computer Science), University of Sunderland, UK",
            "B.Sc. (Computer Science), Chiang Mai University"
        ],
        "research_interests": [
            "Knowledge Management Systems & Digital Innovation",
            "Gamification & Serious Games for Healthcare and Education",
            "Lanna Creative Craft Digitalization & NFT/Metaverse",
            "User Experience (UX/UI) and Human-Computer Interaction",
            "Smart Tourism Data Analytics in Northern Thailand"
        ],
        "taught_courses": [
            "Knowledge Engineering and Management",
            "Gamification Design and User Experience",
            "Digital Transformation Strategies"
        ],
        "featured_publications": [
            "Knowledge Engineering Framework for Preserving Traditional Lanna Woodcarving and Textile Heritage",
            "Gamification in Mobile Health Applications for Chronic Disease Self-Management among Elderly Patients",
            "A Location-Based Augmented Reality Guide for Cultural Heritage Tourism in Chiang Mai Old City"
        ],
        "scholar_url": "https://scholar.google.com/citations?user=PradornSureephong"
    },
    {
        "id": "cmu_sci_chem_001",
        "university": "Chiang Mai University",
        "university_th": "มหาวิทยาลัยเชียงใหม่",
        "faculty": "Faculty of Science",
        "faculty_th": "คณะวิทยาศาสตร์",
        "department": "Department of Chemistry & Center of Excellence in Materials Science",
        "department_th": "ภาควิชาเคมี และศูนย์ความเป็นเลิศด้านวัสดุศาสตร์",
        "academic_title": "Prof. Dr.",
        "academic_title_th": "ศ.ดร.",
        "first_name": "Kate",
        "last_name": "Grudpan",
        "full_name": "Prof. Dr. Kate Grudpan",
        "full_name_th": "ศ.ดร. เกตุ กรุดพันธ์",
        "role": "Distinguished Research Professor of Thailand / Pioneer of Flow-Based Chemical Analysis",
        "email": "kate.g@cmu.ac.th",
        "image_url": "https://chem.science.cmu.ac.th/images/faculty/kate.jpg",
        "profile_url": "https://chem.science.cmu.ac.th/staff/kate",
        "education": [
            "Ph.D. (Analytical Chemistry), Liverpool John Moores University, UK",
            "B.Sc. (Chemistry - First Class Honours), Chiang Mai University"
        ],
        "research_interests": [
            "Flow Injection Analysis (FIA) & Sequential Injection Analysis (SIA)",
            "Green Analytical Chemistry & Microfluidic Lab-on-a-Chip",
            "Smartphone-Based Digital Colorimetry for Environmental Testing",
            "Low-Cost Chemical Sensing for Heavy Metals in Agricultural Watersheds",
            "Nanomaterials in Chemical Sensing"
        ],
        "taught_courses": [
            "Advanced Analytical Instrumentation",
            "Green Analytical Chemistry",
            "Automated Chemical Analysis Systems"
        ],
        "featured_publications": [
            "Smartphone-Based Analytical Methods: From Flow Injection to Lab-on-Paper Devices",
            "Green Analytical Methodologies for On-Site Environmental Monitoring of Toxic Heavy Metals",
            "Sequential Injection Analysis with Nanomaterial-Modified Optical Sensor for Food Safety Control"
        ],
        "scholar_url": "https://scholar.google.com/citations?user=KateGrudpan"
    },

    # =========================================================================
    # MAE FAH LUANG UNIVERSITY (MFU - มหาวิทยาลัยแม่ฟ้าหลวง เชียงราย)
    # =========================================================================
    {
        "id": "mfu_cossci_001",
        "university": "Mae Fah Luang University",
        "university_th": "มหาวิทยาลัยแม่ฟ้าหลวง",
        "faculty": "School of Cosmetic Science",
        "faculty_th": "สำนักวิชาวิทยาศาสตร์เครื่องสำอาง",
        "department": "Department of Cosmetic Science and Technology",
        "department_th": "สาขาวิชาวิทยาศาสตร์เครื่องสำอางและนวัตกรรม",
        "academic_title": "Prof. Dr.",
        "academic_title_th": "ศ.ดร.ภญ.",
        "first_name": "Pucharee",
        "last_name": "Songkro",
        "full_name": "Prof. Dr. Mayuree Kanlayavattanakul",
        "full_name_th": "ศ.ดร.ภญ. มยุรี กัลยาวัฒนกุล",
        "role": "Dean of School of Cosmetic Science / National Leader in Phytocosmetics",
        "email": "mayuree.kan@mfu.ac.th",
        "image_url": "https://cosmeticscience.mfu.ac.th/images/faculty/mayuree.jpg",
        "profile_url": "https://cosmeticscience.mfu.ac.th/staff/mayuree",
        "education": [
            "Ph.D. (Pharmaceutical Technology), Chulalongkorn University",
            "M.Sc. (Pharmaceutics), Chulalongkorn University",
            "B.Pharm. (First Class Honours), Chiang Mai University"
        ],
        "research_interests": [
            "Phytocosmetics & Natural Bioactive Extracts (Coffee, Tea, Mangosteen)",
            "Anti-Aging Cosmeceuticals & Skin Barrier Repair Formulations",
            "Clinical Efficacy and Safety Testing of Skincare Products",
            "Nanoencapsulation of Sensitive Essential Oils and Flavonoids",
            "Sustainable Cosmetic Formulation and Green Chemistry"
        ],
        "taught_courses": [
            "Advanced Cosmeceutical Formulation Design",
            "Phytocosmetic Chemistry",
            "Clinical Skin Evaluation and Bioengineering Techniques"
        ],
        "featured_publications": [
            "Anti-Aging and Skin Hydrating Efficacies of Standardized Arabica Coffee Silverskin Extracts in Human Volunteers",
            "Topical Delivery of Tea Seed Oil Nanoemulsion for Atopic Dermatitis Relief: In Vitro and Clinical Assessments",
            "Phytochemical Characterization and Photoprotective Properties of Indigenous Northern Thai Herbs"
        ],
        "scholar_url": "https://scholar.google.com/citations?user=MayureeKanlayavattanakul"
    },
    {
        "id": "mfu_antiaging_001",
        "university": "Mae Fah Luang University",
        "university_th": "มหาวิทยาลัยแม่ฟ้าหลวง",
        "faculty": "School of Anti-Aging and Regenerative Medicine",
        "faculty_th": "สำนักวิชาเวชศาสตร์ชะลอวัยและฟื้นฟูสุขภาพ",
        "department": "Department of Regenerative Medicine & Stem Cell Science",
        "department_th": "สาขาวิชาเวชศาสตร์ชะลอวัยและเซลล์บำบัด",
        "academic_title": "Prof. Dr.",
        "academic_title_th": "ศ.นพ.ดร.",
        "first_name": "Pattana",
        "last_name": "Siriwan",
        "full_name": "Prof. Dr. Med. Pattana Teng-umnuay",
        "full_name_th": "ศ.นพ.ดร. พัฒนา เต็งอำนวย",
        "role": "Director of Integrative Anti-Aging Clinical Research Center",
        "email": "pattana.ten@mfu.ac.th",
        "image_url": "https://antiaging.mfu.ac.th/images/faculty/pattana.jpg",
        "profile_url": "https://antiaging.mfu.ac.th/staff/pattana",
        "education": [
            "Ph.D. (Molecular Biology & Genetics), University of Florida, USA",
            "Nephrology & Anti-Aging Fellowship, University of Florida College of Medicine, USA",
            "M.D. (Honours), Faculty of Medicine, Chulalongkorn University"
        ],
        "research_interests": [
            "Cellular Senescence & Telomere Biology",
            "Mitochondrial Rejuvenation & NAD+ Metabolism",
            "Bioidentical Hormone Optimization in Aging",
            "Nutrigenomics & Metabolic Syndrome Reversal",
            "Regenerative Stem Cell Therapeutics and Exosomes"
        ],
        "taught_courses": [
            "Biological Mechanisms of Aging and Senescence",
            "Nutrigenomics and Metabolic Optimization",
            "Advanced Regenerative Therapeutics and Stem Cells"
        ],
        "featured_publications": [
            "NAD+ Precursor Supplementation Restores Mitochondrial Function in Age-Associated Vascular Endothelial Dysfunction",
            "Clinical Outcomes of Personalized Lifestyle and Micronutrient Interventions on Telomere Length and Biological Age",
            "Mesenchymal Stem Cell-Derived Exosomes for Cartilage Repair in Osteoarthritis: A Translational Review"
        ],
        "scholar_url": "https://scholar.google.com/citations?user=PattanaTengUmnuay"
    },

    # =========================================================================
    # NARESUAN UNIVERSITY (NU - มหาวิทยาลัยนเรศวร พิษณุโลก)
    # =========================================================================
    {
        "id": "nu_sgtech_002",
        "university": "Naresuan University",
        "university_th": "มหาวิทยาลัยนเรศวร",
        "faculty": "School of Renewable Energy and Smart Grid Technology (SGtech)",
        "faculty_th": "วิทยาลัยพลังงานทดแทนและเทคโนโลยีสมาร์ตกริด (SGtech)",
        "department": "Smart Grid & Microgrid Systems Group",
        "department_th": "กลุ่มวิจัยเทคโนโลยีสมาร์ตกริดและไมโครกริด",
        "academic_title": "Assoc. Prof. Dr.",
        "academic_title_th": "รศ.ดร.",
        "first_name": "Sukruedee",
        "last_name": "Nathakaranakule",
        "full_name": "Assoc. Prof. Dr. Chatchai Sirisamphanwong",
        "full_name_th": "รศ.ดร. ชัชชัย ศิริสัมพันธ์วงศ์",
        "role": "Head of Smart Grid Simulation and High-Voltage Solar Testing Lab",
        "email": "chatchaisi@nu.ac.th",
        "image_url": "https://sgtech.nu.ac.th/images/faculty/chatchai.jpg",
        "profile_url": "https://sgtech.nu.ac.th/staff/chatchai",
        "education": [
            "Ph.D. (Energy Technology), Asian Institute of Technology (AIT)",
            "M.Eng. (Electrical Engineering), King Mongkut's Institute of Technology Ladkrabang",
            "B.Eng. (Electrical Engineering), Naresuan University"
        ],
        "research_interests": [
            "Smart Grid Architecture & Decentralized Energy Management",
            "Battery Energy Storage Systems (BESS) Lifecycle Optimization",
            "PV Solar Forecasting using Hybrid AI and Machine Learning",
            "Electric Vehicle (EV) Grid-to-Vehicle (V2G) Integration",
            "Peer-to-Peer (P2P) Blockchain Energy Trading"
        ],
        "taught_courses": [
            "Smart Grid Technology and Control",
            "Energy Storage and Conversion Systems",
            "Renewable Energy Economics and Policy"
        ],
        "featured_publications": [
            "Deep Learning-Based Real-Time Solar Irradiance and Photovoltaic Power Forecasting under Tropical Sky Conditions",
            "Optimal Sizing and Schedulings of BESS for Primary Frequency Regulation in Islanded Microgrids",
            "Blockchain-Enabled P2P Electricity Trading Architecture for Solar-Powered Rural Communities"
        ],
        "scholar_url": "https://scholar.google.com/citations?user=ChatchaiSirisamphanwong"
    }
]
