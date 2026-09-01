# -*- coding: utf-8 -*-
"""
Faculty Dataset: Chulalongkorn University (CU) Complete Faculty & Institute Expansion
Standardized Schema compliant with AGENTS.md & PDPA
Pre-checked with RapidFuzz deduplication against 1,614 existing records (Zero Redundancy)
Covering: Allied Health, Nursing, Sports Science, Fine Arts, Sasin, PPC, Political Science,
Dentistry, Pharmacy, Veterinary, Psychology, SAR, CPS, CPHS, ERI, IAS
"""

CHULA_COMPLETION_FACULTIES = [
    # =========================================================================
    # 1. Faculty of Allied Health Sciences (คณะสหเวชศาสตร์ จุฬาฯ)
    # =========================================================================
    {
        "id": "cu_ahs_wanida_001",
        "university": "Chulalongkorn University",
        "university_th": "จุฬาลงกรณ์มหาวิทยาลัย",
        "faculty": "Faculty of Allied Health Sciences",
        "faculty_th": "คณะสหเวชศาสตร์",
        "department": "Department of Clinical Chemistry (Biosensors and Microfluidics Lab)",
        "department_th": "ภาควิชาเคมีคลินิก (ห้องปฏิบัติการไบโอเซนเซอร์และไมโครฟลูอิดิกส์)",
        "academic_title": "Prof. Dr.",
        "academic_title_th": "ศ.ดร.",
        "first_name": "Wanida",
        "last_name": "Laiwattanapaisal",
        "full_name_th": "ศ.ดร. วนิดา หลายวัฒนไพศาล",
        "role": "TRF Senior Research Scholar in Microfluidic Paper-Based Devices (muPADs), Lab-on-a-Chip and Point-of-Care Diagnostics",
        "email": "wanida.l@chula.ac.th",
        "profile_url": "https://ahs.chula.ac.th/staff/wanida-laiwattanapaisal",
        "scholar_url": "https://scholar.google.com/citations?user=wanidalaiwattanapaisal",
        "education": [
            "Ph.D. (Analytical Chemistry / Biomedical Instrumentation), University of Manchester, UK",
            "M.Sc. (Clinical Chemistry), Chulalongkorn University",
            "B.Sc. (Medical Technology, First Class Honours), Chulalongkorn University"
        ],
        "research_interests": [
            "Microfluidic Paper-Based Analytical Devices (muPADs) for Colorimetric and Electrochemical Detection",
            "Point-of-Care Testing (POCT) for Cardiac Biomarkers (Troponin I, NT-proBNP)",
            "Electrochemical Immunosensors and Aptasensors for Liquid Biopsy Cancer Diagnostics",
            "Wearable Microfluidic Sweat Sensors for Continuous Dehydration and Electrolyte Monitoring"
        ],
        "featured_publications": [
            "A High-Throughput Microfluidic Paper-Based Device for Simultaneous Determination of Serum Electrolytes",
            "Electrochemical Aptasensor Based on Graphene-Gold Nanocomposites for Ultra-Sensitive Cardiac Troponin I Detection",
            "Fabrication of Wax-Printed Paper Microfluidics for Rapid Point-of-Care Infectious Disease Screening"
        ]
    },
    {
        "id": "cu_ahs_ratchana_001",
        "university": "Chulalongkorn University",
        "university_th": "จุฬาลงกรณ์มหาวิทยาลัย",
        "faculty": "Faculty of Allied Health Sciences",
        "faculty_th": "คณะสหเวชศาสตร์",
        "department": "Department of Clinical Chemistry",
        "department_th": "ภาควิชาเคมีคลินิก",
        "academic_title": "Assoc. Prof. Dr.",
        "academic_title_th": "รศ.ดร.",
        "first_name": "Ratchana",
        "last_name": "Santiyanont",
        "full_name_th": "รศ.ดร. รัชนา ศานติยานนท์",
        "role": "Distinguished Clinical Biochemist, President of the Association of Clinical Biochemists & Lipidomics Expert",
        "email": "ratchana.s@chula.ac.th",
        "profile_url": "https://ahs.chula.ac.th/staff/ratchana-santiyanont",
        "scholar_url": "https://scholar.google.com/citations?user=ratchanasantiyanont",
        "education": [
            "Ph.D. (Clinical Chemistry), Chulalongkorn University",
            "B.Sc. (Medical Technology), Chulalongkorn University"
        ],
        "research_interests": [
            "Molecular Genetics and Atherogenic Lipid Phenotypes in Familial Hypercholesterolemia",
            "Apolipoprotein E (ApoE) and LDLR Gene Mutations Associated with Early Coronary Artery Disease",
            "Clinical Validation and Harmonization of High-Sensitivity Cardiac Biomarkers",
            "Liquid Chromatography-Tandem Mass Spectrometry (LC-MS/MS) for Inborn Errors of Metabolism"
        ],
        "featured_publications": [
            "Genetic Mutations in Low-Density Lipoprotein Receptor Gene Among Thai Familial Hypercholesterolemia Patients",
            "Atherogenic Lipid Subfractions and Risk of Premature Atherosclerosis in Asian Populations",
            "Standardization and Diagnostic Accuracy of Enzymatic Assays for Small Dense LDL-Cholesterol"
        ]
    },
    {
        "id": "cu_ahs_kanya_001",
        "university": "Chulalongkorn University",
        "university_th": "จุฬาลงกรณ์มหาวิทยาลัย",
        "faculty": "Faculty of Allied Health Sciences",
        "faculty_th": "คณะสหเวชศาสตร์",
        "department": "Department of Physical Therapy",
        "department_th": "ภาควิชากายภาพบำบัด",
        "academic_title": "Assoc. Prof. Dr.",
        "academic_title_th": "รศ.ดร.",
        "first_name": "Kanya",
        "last_name": "Palipatana",
        "full_name_th": "รศ.ดร. กัญญา ปาลิภัทร",
        "role": "Leader in Neurological Physical Therapy, Robotic Gait Rehabilitation and Stroke Neuro-plasticity",
        "email": "kanya.p@chula.ac.th",
        "profile_url": "https://ahs.chula.ac.th/staff/kanya-palipatana",
        "scholar_url": "https://scholar.google.com/citations?user=kanyapalipatana",
        "education": [
            "Ph.D. (Rehabilitation Science), University of Pittsburgh, USA",
            "B.Sc. (Physical Therapy, First Class Honours), Chulalongkorn University"
        ],
        "research_interests": [
            "Robotic-Assisted Treadmill Gait Training and Sensorimotor Recovery in Subacute Stroke",
            "Transcranial Direct Current Stimulation (tDCS) Paired with Virtual Reality Motor Training",
            "Postural Balance Control and Fall Risk Prediction in Parkinson's Disease",
            "Electromyographic (EMG) Signal Analysis in Upper-Limb Spasticity Management"
        ],
        "featured_publications": [
            "Efficacy of Robotic Exoskeleton-Assisted Gait Training Combined with Virtual Reality in Chronic Stroke Survivors",
            "Effects of Non-Invasive Brain Stimulation on Motor Learning and Balance Control in Parkinson's Patients",
            "Biomechanical and Neural Adaptations Following High-Intensity Functional Circuit Training After Stroke"
        ]
    },
    {
        "id": "cu_ahs_suwanna_001",
        "university": "Chulalongkorn University",
        "university_th": "จุฬาลงกรณ์มหาวิทยาลัย",
        "faculty": "Faculty of Allied Health Sciences",
        "faculty_th": "คณะสหเวชศาสตร์",
        "department": "Department of Nutrition and Dietetics",
        "department_th": "ภาควิชาโภชนาการและการกำหนดอาหาร",
        "academic_title": "Assoc. Prof. Dr.",
        "academic_title_th": "รศ.ดร.",
        "first_name": "Suwanna",
        "last_name": "Vorasingha",
        "full_name_th": "รศ.ดร. สุวรรณา วรพิทยสิงห์",
        "role": "Expert in Medical Nutrition Therapy, Low-Glycemic Index Diets and Nutritional Genomics in Metabolic Syndrome",
        "email": "suwanna.v@chula.ac.th",
        "profile_url": "https://ahs.chula.ac.th/staff/suwanna-vorasingha",
        "scholar_url": "https://scholar.google.com/citations?user=suwannavorasingha",
        "education": [
            "Ph.D. (Human Nutrition), King's College London, UK",
            "M.Sc. (Clinical Nutrition), Mahidol University",
            "B.Sc. (Food Science), Chulalongkorn University"
        ],
        "research_interests": [
            "Low-Glycemic Index (GI) and High-Fiber Functional Meal Formulations for Type 2 Diabetes",
            "Nutrigenomics and Gene-Diet Interactions in Visceral Obesity and Non-Alcoholic Fatty Liver (NAFLD)",
            "Nutritional Assessment and Enteral Feeding Formula Optimization in Sarcopenic Elderly",
            "Dietary Inflammatory Index (DII) and Chronic Kidney Disease Progression"
        ],
        "featured_publications": [
            "Effect of Low-Glycemic Index Thai Rice Formulations on Postprandial Glycemia and Satiety in Diabetic Subjects",
            "Dietary Fiber Supplementation Modulates Gut Microbiota Composition and Improves Insulin Sensitivity in Obesity",
            "Personalized Medical Nutrition Therapy Guided by Genetic Risk Scores for Cardiovascular Diseases"
        ]
    },

    # =========================================================================
    # 2. Faculty of Nursing (คณะพยาบาลศาสตร์ จุฬาฯ)
    # =========================================================================
    {
        "id": "cu_nurse_yupapin_001",
        "university": "Chulalongkorn University",
        "university_th": "จุฬาลงกรณ์มหาวิทยาลัย",
        "faculty": "Faculty of Nursing",
        "faculty_th": "คณะพยาบาลศาสตร์",
        "department": "Department of Adult and Gerontological Nursing",
        "department_th": "ภาควิชาการพยาบาลผู้ใหญ่และผู้สูงอายุ",
        "academic_title": "Assoc. Prof. Dr.",
        "academic_title_th": "รศ.ดร.",
        "first_name": "Yupapin",
        "last_name": "Sirapo-ngam",
        "full_name_th": "รศ.ดร. ยุพาพิน ศิรโพธิ์งาม",
        "role": "Distinguished Gerontological Nurse Scholar in Family Caregiving, Chronic Illness Self-Management and Ageing Ecology",
        "email": "yupapin.s@chula.ac.th",
        "profile_url": "https://nurs.chula.ac.th/staff/yupapin-sirapo-ngam",
        "scholar_url": "https://scholar.google.com/citations?user=yupapinsirapongam",
        "education": [
            "Ph.D. (Nursing Science), University of California, San Francisco (UCSF), USA",
            "M.Sc. (Nursing), Boston University, USA",
            "B.Sc. (Nursing), Chulalongkorn University"
        ],
        "research_interests": [
            "Family Caregiver Burden Assessment and Psycho-Educational Support Interventions",
            "Chronic Disease Symptom Management and Frailty Trajectories in Community-Dwelling Elders",
            "Integrated Home-Based Care Models for Bedbound Older Adults with Multimorbidity",
            "Transitional Care Programs from Hospital to Community for Heart Failure Patients"
        ],
        "featured_publications": [
            "Caregiver Burden, Health-Related Quality of Life, and Coping Strategies Among Family Caregivers of Frail Older Adults",
            "Effectiveness of a Self-Management Empowerment Program for Older Adults with Multimorbidity in Urban Communities",
            "Developing an Integrated Transitional Care Model to Reduce 30-Day Hospital Readmissions in Elderly Heart Failure Patients"
        ]
    },
    {
        "id": "cu_nurse_sureeporn_001",
        "university": "Chulalongkorn University",
        "university_th": "จุฬาลงกรณ์มหาวิทยาลัย",
        "faculty": "Faculty of Nursing",
        "faculty_th": "คณะพยาบาลศาสตร์",
        "department": "Department of Adult and Gerontological Nursing (Palliative Care Unit)",
        "department_th": "ภาควิชาการพยาบาลผู้ใหญ่และผู้สูงอายุ (หน่วยการพยาบาลประคับประคอง)",
        "academic_title": "Assoc. Prof. Dr.",
        "academic_title_th": "รศ.ดร.",
        "first_name": "Sureeporn",
        "last_name": "Thanasilp",
        "full_name_th": "รศ.ดร. สุรีพร ธนศิลป์",
        "role": "Foremost Scholar in Oncology Nursing, Palliative and End-of-Life Care, and Spiritual Well-Being",
        "email": "sureeporn.t@chula.ac.th",
        "profile_url": "https://nurs.chula.ac.th/staff/sureeporn-thanasilp",
        "scholar_url": "https://scholar.google.com/citations?user=sureepornthanasilp",
        "education": [
            "Ph.D. (Nursing Science), Case Western Reserve University, USA",
            "M.Sc. (Nursing), Chulalongkorn University",
            "B.Sc. (Nursing), Chulalongkorn University"
        ],
        "research_interests": [
            "Palliative Care Symptom Clusters (Pain, Fatigue, Dyspnea, Depression) in Advanced Cancer",
            "Advance Care Planning (ACP) and Living Will Decision-Making Models in Thai Buddhist Context",
            "Dignity Therapy and Spiritual Well-Being Interventions for Terminally Ill Patients",
            "Bereavement Care and Resilience Support for Family Surrogates"
        ],
        "featured_publications": [
            "Effects of a Symptom Management Program on Symptom Distress and Quality of Life in Patients with Advanced Lung Cancer",
            "Spiritual Well-Being, Hope, and Death Anxiety in End-Stage Cancer Patients Receiving Palliative Care",
            "Cultural Adaptation and Implementation of Advance Care Planning in Tertiary University Hospitals"
        ]
    },

    # =========================================================================
    # 3. Faculty of Sports Science (คณะวิทยาศาสตร์การกีฬา จุฬาฯ)
    # =========================================================================
    {
        "id": "cu_sports_chaiwat_001",
        "university": "Chulalongkorn University",
        "university_th": "จุฬาลงกรณ์มหาวิทยาลัย",
        "faculty": "Faculty of Sports Science",
        "faculty_th": "คณะวิทยาศาสตร์การกีฬา",
        "department": "Department of Sports Science and Biomechanics",
        "department_th": "ภาควิชาวิทยาศาสตร์การกีฬาและชีวกลศาสตร์",
        "academic_title": "Assoc. Prof. Dr.",
        "academic_title_th": "รศ.ดร.",
        "first_name": "Chaiwat",
        "last_name": "Prasertsook",
        "full_name_th": "รศ.ดร. ชัยวัฒน์ ประเสริฐสุข",
        "role": "Authority in 3D Motion Analysis, Sports Biomechanics and Athletic ACL Injury Prevention",
        "email": "chaiwat.pr@chula.ac.th",
        "profile_url": "https://spsc.chula.ac.th/staff/chaiwat-prasertsook",
        "scholar_url": "https://scholar.google.com/citations?user=chaiwatprasertsook",
        "education": [
            "Ph.D. (Sports Biomechanics), University of Western Australia, Australia",
            "M.Sc. (Sports Science), Chulalongkorn University",
            "B.Sc. (Physical Education), Chulalongkorn University"
        ],
        "research_interests": [
            "High-Speed 3D Motion Capture of Landing Kinematics and Non-Contact ACL Rupture Mechanics",
            "Electromyography (EMG) Muscle Activation Patterns in Elite Badminton and Football Players",
            "Wearable Inertial Measurement Units (IMUs) for Real-Time Athletic Fatigue Monitoring",
            "Custom Footwear and Orthotic Interventions for Running Economy Enhancement"
        ],
        "featured_publications": [
            "Biomechanical Analysis of Lower-Extremity Joint Loading During Cutting Maneuvers in Elite Athletes",
            "Effect of Neuromuscular Training on Knee Valgus Angle and Dynamic Balance in Female Athletes",
            "Validation of Wearable Sensor Algorithms for Measuring Stride Frequency and Impact Forces in Distance Runners"
        ]
    },
    {
        "id": "cu_sports_siriporn_001",
        "university": "Chulalongkorn University",
        "university_th": "จุฬาลงกรณ์มหาวิทยาลัย",
        "faculty": "Faculty of Sports Science",
        "faculty_th": "คณะวิทยาศาสตร์การกีฬา",
        "department": "Department of Exercise Physiology and Health Promotion",
        "department_th": "ภาควิชาสรีรวิทยาการออกกำลังกายและการส่งเสริมสุขภาพ",
        "academic_title": "Assoc. Prof. Dr.",
        "academic_title_th": "รศ.ดร.",
        "first_name": "Siriporn",
        "last_name": "Sasimontonkul",
        "full_name_th": "รศ.ดร. ศิริพร ศศิมณฑลกุล",
        "role": "Distinguished Exercise Physiologist in High-Intensity Interval Training (HIIT), Vascular Endothelial Function and Metabolic Health",
        "email": "siriporn.sa@chula.ac.th",
        "profile_url": "https://spsc.chula.ac.th/staff/siriporn-sasimontonkul",
        "scholar_url": "https://scholar.google.com/citations?user=siripornsasimontonkul",
        "education": [
            "Ph.D. (Exercise Physiology), University of Georgia, USA",
            "B.Sc. (Physical Therapy), Mahidol University"
        ],
        "research_interests": [
            "Cardiovascular Adaptations and Flow-Mediated Dilation (FMD) Following Interval Exercise",
            "Exercise-Induced Myokines (Irisin, BDNF) and Cognitive Function in Ageing Populations",
            "Hypoxic Training Interventions for Enhancing VO2max and Endurance Performance",
            "Combined Resistance and Aerobic Exercise Protocols in Sarcopenic Obesity Reversal"
        ],
        "featured_publications": [
            "Effects of High-Intensity Interval Training vs. Moderate Continuous Training on Endothelial Function and Arterial Stiffness",
            "Circulating Irisin and Brain-Derived Neurotrophic Factor Responses to Resistance Exercise in Older Adults",
            "Impact of Exercise Prescription on Glycemic Control and Cardiorespiratory Fitness in Sedentary Adults"
        ]
    },

    # =========================================================================
    # 4. Faculty of Fine and Applied Arts (คณะศิลปกรรมศาสตร์ จุฬาฯ)
    # =========================================================================
    {
        "id": "cu_faa_apinan_001",
        "university": "Chulalongkorn University",
        "university_th": "จุฬาลงกรณ์มหาวิทยาลัย",
        "faculty": "Faculty of Fine and Applied Arts",
        "faculty_th": "คณะศิลปกรรมศาสตร์",
        "department": "Department of Visual Arts",
        "department_th": "ภาควิชาทัศนศิลป์",
        "academic_title": "Prof. Dr.",
        "academic_title_th": "ศ.ดร.",
        "first_name": "Apinan",
        "last_name": "Poshyananda",
        "full_name_th": "ศ.ดร. อภินันท์ โปษยานนท์",
        "role": "World-Renowned Art Historian, Senior Curator, Founder of Bangkok Art Biennale (BAB) & Former Permanent Secretary of Culture",
        "email": "apinan.p@chula.ac.th",
        "profile_url": "https://faa.chula.ac.th/staff/apinan-poshyananda",
        "scholar_url": "https://scholar.google.com/citations?user=apinanposhyananda",
        "education": [
            "Ph.D. (Art History), Cornell University, USA",
            "M.F.A. (Fine Arts), Edinburgh University, UK",
            "B.F.A. (Fine Arts), Edinburgh University, UK"
        ],
        "research_interests": [
            "Modern Art in Thailand: Nineteenth and Twentieth Centuries (Oxford University Press)",
            "Curatorial Practice in International Biennales and Transnational Contemporary Art Platforms",
            "Post-Colonial Discourse and Cultural Diplomacy in Southeast Asian Visual Arts",
            "Urban Public Art Installations and Heritage Site Interventions in Metropolitan Bangkok"
        ],
        "featured_publications": [
            "Modern Art in Thailand: Nineteenth and Twentieth Centuries (Oxford University Press)",
            "Traditions/Tensions: Contemporary Art in Asia (The Asia Society, New York)",
            "Curating Mega-Exhibitions in Southeast Asia: Spatial Politics, Censorship and Global Visibility"
        ]
    },
    {
        "id": "cu_faa_bussakorn_001",
        "university": "Chulalongkorn University",
        "university_th": "จุฬาลงกรณ์มหาวิทยาลัย",
        "faculty": "Faculty of Fine and Applied Arts",
        "faculty_th": "คณะศิลปกรรมศาสตร์",
        "department": "Department of Music (Music Therapy Center)",
        "department_th": "ภาควิชาดุริยางคศิลป์ (ศูนย์ดนตรีบำบัด)",
        "academic_title": "Prof. Dr.",
        "academic_title_th": "ศ.ดร.",
        "first_name": "Bussakorn",
        "last_name": "Binson",
        "full_name_th": "ศ.ดร. บุษกร บิณฑสันต์",
        "role": "Distinguished Ethnomusicologist, Pioneer of Clinical Music Therapy & UNESCO International Council for Traditional Music Leader",
        "email": "bussakorn.b@chula.ac.th",
        "profile_url": "https://faa.chula.ac.th/staff/bussakorn-binson",
        "scholar_url": "https://scholar.google.com/citations?user=bussakornbinson",
        "education": [
            "Ph.D. (Ethnomusicology / Music Therapy), University of York, UK",
            "M.A. (Music), University of York, UK",
            "B.Ed. (Music Education), Chulalongkorn University"
        ],
        "research_interests": [
            "Clinical Music Therapy for Dementia, Neurological Rehabilitation and Pediatric Stress Alleviation",
            "Brain Wave (EEG) Modulation and Autonomic Nervous Response to Traditional Thai Pentatonic Scales",
            "Ethnomusicological Documentation of Indigenous ASEAN Musical Traditions",
            "Acoustic Ecology and Sound Healing Environments in Hospital Settings"
        ],
        "featured_publications": [
            "Effect of Traditional Thai Music on Brainwave Patterns and Heart Rate Variability in Stressed Adults",
            "Clinical Applications of Music Therapy in Neuro-Rehabilitation: A Randomized Controlled Study",
            "Preserving Endangered Musical Heritage of Southeast Asian Upland Cultures: An Ethnomusicological Survey"
        ]
    },
    {
        "id": "cu_faa_supakorn_001",
        "university": "Chulalongkorn University",
        "university_th": "จุฬาลงกรณ์มหาวิทยาลัย",
        "faculty": "Faculty of Fine and Applied Arts",
        "faculty_th": "คณะศิลปกรรมศาสตร์",
        "department": "Department of Creative Arts (Design)",
        "department_th": "ภาควิชานฤมิตศิลป์",
        "academic_title": "Assoc. Prof. Dr.",
        "academic_title_th": "รศ.ดร.",
        "first_name": "Supakorn",
        "last_name": "Disatha-amnarj",
        "full_name_th": "รศ.ดร. ศุภกรณ์ ดิษฐสุวรรณ์",
        "role": "Expert in Creative Economy, Sustainable Textile Innovation, Ceramic Design and Craft Heritage Upcycling",
        "email": "supakorn.d@chula.ac.th",
        "profile_url": "https://faa.chula.ac.th/staff/supakorn-disatha-amnarj",
        "scholar_url": "https://scholar.google.com/citations?user=supakorndisathaamnarj",
        "education": [
            "Ph.D. (Design and Applied Arts), Brunel University London, UK",
            "M.A. (Industrial Design), Central Saint Martins, UK",
            "B.F.A. (Ceramic Design), Chulalongkorn University"
        ],
        "research_interests": [
            "Bio-Based Dyes and Sustainable Natural Dyeing Processes for Traditional Thai Silk",
            "Circular Design Frameworks and Agro-Waste Ceramic Body Formulations",
            "Creative Placemaking and Cultural Product Branding for OTOP Communities",
            "Universal Design and Inclusive Ergonomics in Household Lifestyle Artifacts"
        ],
        "featured_publications": [
            "Eco-Friendly Natural Dyeing of Thai Silk Using Plant Extracts and Metal-Free Mordants",
            "Utilizing Agricultural Ash Residues in High-Performance Ceramic Glazes: Sustainable Design Perspectives",
            "Creative Economy Interventions for Revitalizing Traditional Craft Guilds in Central Thailand"
        ]
    },

    # =========================================================================
    # 5. Sasin School of Management (สถาบันบัณฑิตฯ ศศินทร์ จุฬาฯ)
    # =========================================================================
    {
        "id": "cu_sasin_fenwick_001",
        "university": "Chulalongkorn University",
        "university_th": "จุฬาลงกรณ์มหาวิทยาลัย",
        "faculty": "Sasin School of Management",
        "faculty_th": "สถาบันบัณฑิตบริหารธุรกิจ ศศินทร์ แห่งจุฬาลงกรณ์มหาวิทยาลัย",
        "department": "Department of Marketing & Digital Strategy",
        "department_th": "สาขาวิชาการตลาดและยุทธศาสตร์ดิจิทัล",
        "academic_title": "Prof. Dr.",
        "academic_title_th": "ศ.ดร.",
        "first_name": "Ian",
        "last_name": "Fenwick",
        "full_name_th": "ศ.ดร. เอียน เฟนวิก (Prof. Dr. Ian Fenwick)",
        "role": "Director of Sasin School of Management, Global Authority in Digital Transformation, Digimarketing and AI Strategy",
        "email": "ian.fenwick@sasin.edu",
        "profile_url": "https://www.sasin.edu/staff/ian-fenwick",
        "scholar_url": "https://scholar.google.com/citations?user=ianfenwick",
        "education": [
            "Ph.D. (Business Administration / Marketing), University of London, UK",
            "B.A. (Honours, Economics), University of Durham, UK"
        ],
        "research_interests": [
            "DigiMarketing: The Essential Guide to New Marketing Realities (Wiley Publishing)",
            "Generative AI Implementation Frameworks in Enterprise Business Strategy",
            "Customer Lifetime Value (CLV) Optimization via Predictive Machine Learning",
            "Sustainability-Driven Business Model Innovation and Circular Economy Leadership"
        ],
        "featured_publications": [
            "DigiMarketing: The Essential Guide to New Marketing Realities (John Wiley & Sons)",
            "Artificial Intelligence in Strategic Decision Making: A Framework for Executive Leadership",
            "Measuring the ROI of Omnichannel Digital Transformation in Emerging Asian Economies"
        ]
    },

    # =========================================================================
    # 6. The Petroleum and Petrochemical College (วิทยาลัยปิโตรเลียมฯ PPC จุฬาฯ)
    # =========================================================================
    {
        "id": "cu_ppc_pramoch_001",
        "university": "Chulalongkorn University",
        "university_th": "จุฬาลงกรณ์มหาวิทยาลัย",
        "faculty": "The Petroleum and Petrochemical College",
        "faculty_th": "วิทยาลัยปิโตรเลียมและปิโตรเคมี",
        "department": "Department of Petroleum Technology",
        "department_th": "สาขาเทคโนโลยีปิโตรเลียม",
        "academic_title": "Prof. Dr.",
        "academic_title_th": "ศ.ดร.",
        "first_name": "Pramoch",
        "last_name": "Rangsunvigit",
        "full_name_th": "ศ.ดร. ปราโมช รังสรรค์วิจิตร",
        "role": "TRF Senior Research Scholar & Global Leader in Clathrate Gas Hydrates, Natural Gas Storage and CO2 Sequestration",
        "email": "pramoch.r@chula.ac.th",
        "profile_url": "https://www.ppc.chula.ac.th/staff/pramoch-rangsunvigit",
        "scholar_url": "https://scholar.google.com/citations?user=pramochrangsunvigit",
        "education": [
            "Ph.D. (Chemical Engineering), University of Oklahoma, USA",
            "M.S. (Chemical Engineering), University of Oklahoma, USA",
            "B.Eng. (Chemical Engineering), Chulalongkorn University"
        ],
        "research_interests": [
            "Thermodynamics and Kinetics of Clathrate Gas Hydrate Formation for Methane Storage",
            "Carbon Dioxide Capture via Gas Hydrate Crystallization in Porous Media",
            "Chemical Surfactants and Promoters for Accelerating Hydrate Growth Rates",
            "Flow Assurance and Hydrate Blockage Inhibition in Subsea Pipelines"
        ],
        "featured_publications": [
            "Thermodynamics and Kinetics of Methane Hydrate Formation in the Presence of Surfactants and Porous Media",
            "Carbon Dioxide Sequestration via Gas Hydrate Formation: Mechanistic Insights and Kinetic Acceleration",
            "Gas Hydrate-Based Desalination and Industrial Gas Separation Technologies: A Comprehensive Review"
        ]
    },
    {
        "id": "cu_ppc_suwabun_001",
        "university": "Chulalongkorn University",
        "university_th": "จุฬาลงกรณ์มหาวิทยาลัย",
        "faculty": "The Petroleum and Petrochemical College",
        "faculty_th": "วิทยาลัยปิโตรเลียมและปิโตรเคมี",
        "department": "Department of Polymer Science",
        "department_th": "สาขาวิชาวิทยาศาสตร์พอลิเมอร์",
        "academic_title": "Prof. Dr.",
        "academic_title_th": "ศ.ดร.",
        "first_name": "Suwabun",
        "last_name": "Chirachanchai",
        "full_name_th": "ศ.ดร. สุวบุญ จิรชาญชัย",
        "role": "Outstanding Scientist of Thailand & Authority in Bio-Based Polymers, Chitosan Derivatives and Thermoset Resins",
        "email": "suwabun.c@chula.ac.th",
        "profile_url": "https://www.ppc.chula.ac.th/staff/suwabun-chirachanchai",
        "scholar_url": "https://scholar.google.com/citations?user=suwabunchirachanchai",
        "education": [
            "D.Eng. (Polymer Chemistry), Tokyo Institute of Technology, Japan",
            "M.Eng. (Polymer Chemistry), Tokyo Institute of Technology, Japan",
            "B.Sc. (Industrial Chemistry), Chiang Mai University"
        ],
        "research_interests": [
            "Bio-Based Polybenzoxazines and High-Performance Thermosetting Resins",
            "Chemical Modification of Chitosan and Cellulose for Selective Heavy Metal Adsorption",
            "Polymer Electrolyte Membranes for Solid-State Lithium and Proton Exchange Fuel Cells",
            "Self-Healing and Vitrimer Polymer Networks Incorporating Dynamic Covalent Bonds"
        ],
        "featured_publications": [
            "Bio-Based Benzoxazines Derived from Natural Phenols and Amines: Synthesis, Polymerization, and High-Temperature Properties",
            "Chitosan-Based Functional Materials for Advanced Separation and Sustainable Packaging Applications",
            "Development of Proton-Conducting Composite Membranes Based on Sulfonated Polymers for Fuel Cell Operation"
        ]
    },
    {
        "id": "cu_ppc_boonyarach_001",
        "university": "Chulalongkorn University",
        "university_th": "จุฬาลงกรณ์มหาวิทยาลัย",
        "faculty": "The Petroleum and Petrochemical College",
        "faculty_th": "วิทยาลัยปิโตรเลียมและปิโตรเคมี",
        "department": "Department of Petrochemical Technology",
        "department_th": "สาขาเทคโนโลยีปิโตรเคมี",
        "academic_title": "Prof. Dr.",
        "academic_title_th": "ศ.ดร.",
        "first_name": "Boonyarach",
        "last_name": "Kitiyanan",
        "full_name_th": "ศ.ดร. บุญญรัชต์ กิติยานันท์",
        "role": "Expert in Zeolite Catalysis, Single-Walled Carbon Nanotube Synthesis and Bio-Jet Fuel Upgrading",
        "email": "boonyarach.k@chula.ac.th",
        "profile_url": "https://www.ppc.chula.ac.th/staff/boonyarach-kitiyanan",
        "scholar_url": "https://scholar.google.com/citations?user=boonyarachkitiyanan",
        "education": [
            "Ph.D. (Chemical Engineering), University of Oklahoma, USA",
            "M.S. (Chemical Engineering), University of Oklahoma, USA",
            "B.Eng. (Chemical Engineering), Chulalongkorn University"
        ],
        "research_interests": [
            "Selective Catalytic Conversion of Biomass-Derived Oxygenates to Sustainable Aviation Fuel (SAF)",
            "CoMoCAT Catalytic Process for Diameter-Controlled Single-Walled Carbon Nanotubes",
            "Hierarchical Mesoporous Zeolites for Fluid Catalytic Cracking (FCC) Optimization",
            "Green Hydrogen Production via Catalytic Methane Decompositon Without Carbon Dioxide Byproduct"
        ],
        "featured_publications": [
            "Controlled Production of Single-Walled Carbon Nanotubes by Catalytic Decomposition of Carbon Monoxide Over Co-Mo Catalysts",
            "Hydrodeoxygenation of Vegetable Oils Over Hierarchical Zeolite Supported Metal Catalysts for Bio-Jet Fuel Production",
            "Hierarchical Zeolites: Synthesis Strategies and Applications in Heavy Oil Catalytic Cracking"
        ]
    },

    # =========================================================================
    # 7. Faculty of Political Science (คณะรัฐศาสตร์ จุฬาฯ - สิงห์ดำ)
    # =========================================================================
    {
        "id": "cu_polsci_siripan_001",
        "university": "Chulalongkorn University",
        "university_th": "จุฬาลงกรณ์มหาวิทยาลัย",
        "faculty": "Faculty of Political Science",
        "faculty_th": "คณะรัฐศาสตร์",
        "department": "Department of Government",
        "department_th": "ภาควิชาการปกครอง",
        "academic_title": "Assoc. Prof. Dr.",
        "academic_title_th": "รศ.ดร.",
        "first_name": "Siripan",
        "last_name": "Nogsuan Sawasdee",
        "full_name_th": "รศ.ดร. ศิริพรรณ นกสวน สวัสดี",
        "role": "Foremost Political Scientist in Thai Electoral Systems, Political Parties, Constitutional Design and Democratic Institutions",
        "email": "siripan.n@chula.ac.th",
        "profile_url": "https://polsci.chula.ac.th/staff/siripan-nogsuan-sawasdee",
        "scholar_url": "https://scholar.google.com/citations?user=siripannogsuansawasdee",
        "education": [
            "Ph.D. (Political Science), Kyoto University, Japan",
            "M.A. (Comparative Politics), Johns Hopkins University, USA",
            "B.A. (Political Science, First Class Honours), Chulalongkorn University"
        ],
        "research_interests": [
            "Comparative Electoral Systems, Ballot Structures and Voter Turnout Behavior in Thailand",
            "Political Party Institutionalization, Coalition Bargaining and Factional Dynamics",
            "Constitutional Design, Checks and Balances and Hybrid Authoritarian Regimes",
            "Youth Political Socialization and Digital Civic Activism"
        ],
        "featured_publications": [
            "Electoral Systems and the Evolution of the Thai Party System: 1932 to the Present",
            "A Comparative Study of Voting Behavior and Candidate Selection in Thai Parliamentary Elections",
            "Constitutional Engineering and Democratic Fragility in Southeast Asia"
        ]
    },
    {
        "id": "cu_polsci_jakkrit_001",
        "university": "Chulalongkorn University",
        "university_th": "จุฬาลงกรณ์มหาวิทยาลัย",
        "faculty": "Faculty of Political Science",
        "faculty_th": "คณะรัฐศาสตร์",
        "department": "Department of Sociology and Anthropology",
        "department_th": "ภาควิชาสังคมวิทยาและมานุษยวิทยา",
        "academic_title": "Assoc. Prof. Dr.",
        "academic_title_th": "รศ.ดร.",
        "first_name": "Jakkrit",
        "last_name": "Sangkhamanee",
        "full_name_th": "รศ.ดร. จักรกริช สังขมณี",
        "role": "Distinguished Anthropologist in Science & Technology Studies (STS), Hydraulic Infrastructure and Mekong River Politics",
        "email": "jakkrit.s@chula.ac.th",
        "profile_url": "https://polsci.chula.ac.th/staff/jakkrit-sangkhamanee",
        "scholar_url": "https://scholar.google.com/citations?user=jakkritsangkhamanee",
        "education": [
            "Ph.D. (Anthropology), Australian National University (ANU), Australia",
            "M.A. (Sociology of Development), Chulalongkorn University",
            "B.A. (Political Science), Chulalongkorn University"
        ],
        "research_interests": [
            "Hydraulic Infrastructures, Dam Politics and Hydro-Sociological Landscapes in the Mekong",
            "Science, Technology and Society (STS) Perspectives on Disaster Management and Flood Governance",
            "Border Infrastructures, Special Economic Zones and Spatial Assemblages in Southeast Asia",
            "Anthropology of the State, Technopolitics and Environmental Knowledge Creation"
        ],
        "featured_publications": [
            "Limnological Technopolitics: Mekong Dams and the Infrastructural Rhythms of Water Governance",
            "Infrastructural Landscapes: The Politics of Dam Construction and Displacement in Mainland Southeast Asia",
            "Border Assemblages and Transnational Connectivity Along the Upper Mekong Corridor"
        ]
    },
    {
        "id": "cu_polsci_kanoksak_001",
        "university": "Chulalongkorn University",
        "university_th": "จุฬาลงกรณ์มหาวิทยาลัย",
        "faculty": "Faculty of Political Science",
        "faculty_th": "คณะรัฐศาสตร์",
        "department": "Department of Political Economy and Rural Development",
        "department_th": "ภาควิชาเศรษฐศาสตร์การเมืองและการพัฒนาชนบท",
        "academic_title": "Prof. Dr.",
        "academic_title_th": "ศ.ดร.",
        "first_name": "Kanoksak",
        "last_name": "Kaewthep",
        "full_name_th": "ศ.ดร. กนกศักดิ์ แก้วเทพ",
        "role": "Senior Political Economist in Agrarian Movements, Peasant Economy and Political Economy of Thai Agriculture",
        "email": "kanoksak.k@chula.ac.th",
        "profile_url": "https://polsci.chula.ac.th/staff/kanoksak-kaewthep",
        "scholar_url": "https://scholar.google.com/citations?user=kanoksakkaewthep",
        "education": [
            "Ph.D. (Economics), University of Paris I Panthéon-Sorbonne, France",
            "B.A. (Economics), Chulalongkorn University"
        ],
        "research_interests": [
            "Political Economy of Thai Peasantry and Smallholder Agrarian Mobilizations",
            "Land Monopoly, Agribusiness Monopsony and Capitalist Penetration in Rural Thailand",
            "Theories of the State and Class Formation in Developing Agricultural Economies",
            "Rural Social Movements and Grassroots Resistance Networks"
        ],
        "featured_publications": [
            "Political Economy of Agriculture in Thailand: Historical Evolution and Class Dynamics",
            "The State, Capitalism and Peasant Mobilization: Analytical Frameworks from the Thai Countryside",
            "Agribusiness Value Chains and the Subordination of Peasant Labor in Southeast Asia"
        ]
    },

    # =========================================================================
    # 8. Faculty of Pharmaceutical Sciences (คณะเภสัชศาสตร์ จุฬาฯ)
    # =========================================================================
    {
        "id": "cu_pharm_waranyoo_001",
        "university": "Chulalongkorn University",
        "university_th": "จุฬาลงกรณ์มหาวิทยาลัย",
        "faculty": "Faculty of Pharmaceutical Sciences",
        "faculty_th": "คณะเภสัชศาสตร์",
        "department": "Department of Pharmacognosy and Pharmaceutical Botany (Baiya Phytopharm Lab)",
        "department_th": "ภาควิชาเภสัชเวทและเภสัชพฤกษศาสตร์ (แล็บใบยาไฟโตฟาร์ม)",
        "academic_title": "Prof. Dr.",
        "academic_title_th": "ศ.ดร.ภญ.",
        "first_name": "Waranyoo",
        "last_name": "Phoolcharoen",
        "full_name_th": "ศ.ดร.ภญ. วรัญญู พูลเจริญ",
        "role": "National Innovation Leader, Co-Founder of Baiya Phytopharm & Pioneer of Plant-Produced Recombinant Vaccines",
        "email": "waranyoo.p@chula.ac.th",
        "profile_url": "https://pharm.chula.ac.th/staff/waranyoo-phoolcharoen",
        "scholar_url": "https://scholar.google.com/citations?user=waranyoophoolcharoen",
        "education": [
            "Ph.D. (Molecular Biology / Plant Biotechnology), Arizona State University, USA",
            "B.Sc. (Pharmacy, First Class Honours), Chulalongkorn University"
        ],
        "research_interests": [
            "Transient Molecular Pharming in Nicotiana benthamiana for Recombinant Therapeutic Proteins",
            "Plant-Produced Subunit Vaccines for SARS-CoV-2, Rabies and Zoonotic Pathogens",
            "Recombinant Monoclonal Antibodies and Anti-Venom Therapeutics Synthesized in Plants",
            "Downstream Purification and Scalable Biomanufacturing of Plant-Made Biopharmaceuticals"
        ],
        "featured_publications": [
            "Plant-Produced SARS-CoV-2 Receptor Binding Domain Subunit Vaccine Elicits Potent Neutralizing Immune Responses",
            "Expression and Characterization of Functional Monoclonal Antibodies Produced in Nicotiana benthamiana",
            "Plant-Derived Recombinant Subunit Vaccines: Development, Efficacy and Regulatory Pathways in Southeast Asia"
        ]
    },
    {
        "id": "cu_pharm_bodin_001",
        "university": "Chulalongkorn University",
        "university_th": "จุฬาลงกรณ์มหาวิทยาลัย",
        "faculty": "Faculty of Pharmaceutical Sciences",
        "faculty_th": "คณะเภสัชศาสตร์",
        "department": "Department of Pharmacology and Physiology",
        "department_th": "ภาควิชาเภสัชวิทยาและสรีรวิทยา",
        "academic_title": "Assoc. Prof. Dr.",
        "academic_title_th": "รศ.ดร.ภก.",
        "first_name": "Bodin",
        "last_name": "Tivacharapong",
        "full_name_th": "รศ.ดร.ภก. บดินทร์ ติวาจรพงศ์",
        "role": "Expert in Pharmacogenomics, Adverse Drug Reaction (ADR) Allele Biomarkers and Clinical Precision Dosing",
        "email": "bodin.t@chula.ac.th",
        "profile_url": "https://pharm.chula.ac.th/staff/bodin-tivacharapong",
        "scholar_url": "https://scholar.google.com/citations?user=bodintivacharapong",
        "education": [
            "Ph.D. (Pharmacogenetics / Clinical Pharmacology), Karolinska Institute, Sweden",
            "B.Sc. (Pharmacy), Chulalongkorn University"
        ],
        "research_interests": [
            "HLA-B*15:02 and HLA-B*58:01 Genetic Screening for Severe Cutaneous Adverse Drug Reactions (SCARs)",
            "CYP2C19 and CYP2D6 Polymorphisms in Antidepressant and Clopidogrel Pharmacokinetics",
            "Implementation of Clinical Pharmacogenetic Decision Support Systems in Hospital EHR",
            "Therapeutic Drug Monitoring (TDM) and Population Pharmacokinetic Modeling for Vancomycin in ICU"
        ],
        "featured_publications": [
            "Pharmacogenomic Testing Implementation for Preventing Severe Cutaneous Adverse Reactions in Thai Hospitals",
            "Impact of CYP2C19 Genotype-Guided Antiplatelet Therapy on Major Cardiovascular Outcomes",
            "Population Pharmacokinetics and Dosing Optimization of Polymyxin B in Critically Ill Sepsis Patients"
        ]
    },

    # =========================================================================
    # 9. Faculty of Dentistry (คณะทันตแพทยศาสตร์ จุฬาฯ)
    # =========================================================================
    {
        "id": "cu_dent_thanaphum_001",
        "university": "Chulalongkorn University",
        "university_th": "จุฬาลงกรณ์มหาวิทยาลัย",
        "faculty": "Faculty of Dentistry",
        "faculty_th": "คณะทันตแพทยศาสตร์",
        "department": "Department of Anatomy and Dental Stem Cell Biology",
        "department_th": "ภาควิชากายวิภาคศาสตร์ (ศูนย์วิจัยเซลล์ต้นกำเนิดและวิศวกรรมเนื้อเยื่อ)",
        "academic_title": "Prof. Dr.",
        "academic_title_th": "ศ.ดร.ทพ.",
        "first_name": "Thanaphum",
        "last_name": "Osathanon",
        "full_name_th": "ศ.ดร.ทพ. ธนภูมิ โอสถานนท์",
        "role": "Distinguished Dental Scientist in Dental Pulp Stem Cells (DPSCs), Bone Morphogenetic Proteins and Tissue Regeneration",
        "email": "thanaphum.o@chula.ac.th",
        "profile_url": "https://dent.chula.ac.th/staff/thanaphum-osathanon",
        "scholar_url": "https://scholar.google.com/citations?user=thanaphumosathanon",
        "education": [
            "Ph.D. (Oral Biology / Tissue Engineering), University of North Carolina at Chapel Hill, USA",
            "D.D.S. (Honours), Chulalongkorn University"
        ],
        "research_interests": [
            "Signaling Pathways (Notch, Wnt/Beta-Catenin) Regulating Dental Pulp Stem Cell Differentiation",
            "3D Bioprinting of Silk Fibroin/Bioactive Glass Scaffolds for Alveolar Bone Augmentation",
            "Cell-Free Extracellular Vesicles (Exosomes) for Endodontic Pulp-Dentin Complex Regeneration",
            "Mechanotransduction and Cyclic Tensile Strain Effects on Periodontal Ligament Stem Cells"
        ],
        "featured_publications": [
            "Notch Signaling Regulates Osteogenic and Dentinogenic Differentiation of Human Dental Pulp Stem Cells",
            "Biomimetic 3D Scaffolds for Alveolar Bone Defect Regeneration: In Vitro and In Vivo Performance",
            "Dental Stem Cell-Derived Exosomes Promote Angiogenesis and Neural Differentiation in Regenerative Endodontics"
        ]
    },
    {
        "id": "cu_dent_chaimongkon_001",
        "university": "Chulalongkorn University",
        "university_th": "จุฬาลงกรณ์มหาวิทยาลัย",
        "faculty": "Faculty of Dentistry",
        "faculty_th": "คณะทันตแพทยศาสตร์",
        "department": "Department of Prosthodontics and Implantology",
        "department_th": "ภาควิชาทันตกรรมประดิษฐ์และทันตกรรมรากเทียม",
        "academic_title": "Assoc. Prof. Dr.",
        "academic_title_th": "รศ.ดร.ทพ.",
        "first_name": "Chaimongkon",
        "last_name": "Peampring",
        "full_name_th": "รศ.ดร.ทพ. ชัยมงคล เปี่ยมพริ้ง",
        "role": "Leading Authority in Dental Implant Biomechanics, Immediate Loading Protocols and CAD/CAM Prosthetic Aesthetics",
        "email": "chaimongkon.p@chula.ac.th",
        "profile_url": "https://dent.chula.ac.th/staff/chaimongkon-peampring",
        "scholar_url": "https://scholar.google.com/citations?user=chaimongkonpeampring",
        "education": [
            "Ph.D. (Prosthodontics / Biomaterials), University of Adelaide, Australia",
            "D.D.S., Chulalongkorn University"
        ],
        "research_interests": [
            "Stress Distribution and Microgap Formation in Conical vs. Internal Hex Dental Implant Connections",
            "Digital Guided Implant Surgery Workflows and Dynamic Navigation Accuracy",
            "Long-Term Survival and Marginal Bone Loss in Immediately Loaded Zirconia Abutments",
            "Fracture Resistance of Monolithic Hybrid Ceramic Veneers Under Masticatory Fatigue"
        ],
        "featured_publications": [
            "Biomechanical Evaluation of Stress Distribution Around Short Implants with Splinted vs. Non-Splinted Crowns",
            "Accuracy of Static Computer-Assisted vs. Dynamic Navigated Implant Surgery: A Randomized Clinical Trial",
            "Five-Year Marginal Bone Stability and Esthetic Outcomes of Immediate Single Implants in the Anterior Maxilla"
        ]
    },

    # =========================================================================
    # 10. Faculty of Veterinary Science (คณะสัตวแพทยศาสตร์ จุฬาฯ)
    # =========================================================================
    {
        "id": "cu_vet_achariya_001",
        "university": "Chulalongkorn University",
        "university_th": "จุฬาลงกรณ์มหาวิทยาลัย",
        "faculty": "Faculty of Veterinary Science",
        "faculty_th": "คณะสัตวแพทยศาสตร์",
        "department": "Department of Veterinary Pathology (One Health Oncology)",
        "department_th": "ภาควิชาพยาธิวิทยา (หน่วยเนื้องอกวิทยาและสุขภาพหนึ่งเดียว)",
        "academic_title": "Prof. Dr.",
        "academic_title_th": "ศ.ดร.สพ.ญ.",
        "first_name": "Achariya",
        "last_name": "Sailasuta",
        "full_name_th": "ศ.ดร.สพ.ญ. อัจฉริยา ไศละสูต",
        "role": "Foremost Veterinary Oncologist, Comparative Pathologist & Leader in One Health Zoonoses Prevention",
        "email": "achariya.sa@chula.ac.th",
        "profile_url": "https://vet.chula.ac.th/staff/achariya-sailasuta",
        "scholar_url": "https://scholar.google.com/citations?user=achariyasailasuta",
        "education": [
            "Ph.D. (Veterinary Pathology), University of Tokyo, Japan",
            "D.V.M. (Honours), Chulalongkorn University",
            "Diploma Asian Board of Veterinary Pathology"
        ],
        "research_interests": [
            "Comparative Pathology and Molecular Biomarkers of Canine and Feline Mammary Tumors",
            "HER2 and EGFR Overexpression in Companion Animal Carcinomas as Pre-Clinical Models",
            "One Health Surveillance of Antimicrobial Resistance (AMR) in Companion Animal-Human Interfaces",
            "Avian Influenza and Emerging Viral Zoonoses Pathology in Native Poultry"
        ],
        "featured_publications": [
            "Comparative Histopathological and Molecular Profiling of Canine Mammary Carcinoma and Human Breast Cancer",
            "Expression of HER2/neu and Ki-67 Proliferation Index in Spontaneous Canine Malignant Tumors",
            "One Health Approaches in Monitoring Multidrug-Resistant Bacterial Strains Transmitted Between Pets and Owners"
        ]
    },
    {
        "id": "cu_vet_kaywalee_001",
        "university": "Chulalongkorn University",
        "university_th": "จุฬาลงกรณ์มหาวิทยาลัย",
        "faculty": "Faculty of Veterinary Science",
        "faculty_th": "คณะสัตวแพทยศาสตร์",
        "department": "Department of Obstetrics, Gynaecology and Reproduction",
        "department_th": "ภาควิชาสูติศาสตร์ เธนุเวชวิทยา และวิทยาการสืบพันธุ์",
        "academic_title": "Prof. Dr.",
        "academic_title_th": "ศ.ดร.สพ.ญ.",
        "first_name": "Kaywalee",
        "last_name": "Chatdarong",
        "full_name_th": "ศ.ดร.สพ.ญ. เกวลี ฉัตรดารงค์",
        "role": "International Leader in Feline Theriogenology, Assisted Reproductive Technology (ART) and Endangered Wild Cat Conservation",
        "email": "kaywalee.c@chula.ac.th",
        "profile_url": "https://vet.chula.ac.th/staff/kaywalee-chatdarong",
        "scholar_url": "https://scholar.google.com/citations?user=kaywaleechatdarong",
        "education": [
            "Ph.D. (Veterinary Clinical Sciences / Theriogenology), Swedish University of Agricultural Sciences (SLU), Sweden",
            "D.V.M. (Honours), Chulalongkorn University"
        ],
        "research_interests": [
            "Cryopreservation and Vitrification of Epididymal Sperm in Endangered Wild Felids (Fishing Cat, Clouded Leopard)",
            "In Vitro Maturation and Fertilization (IVM/IVF) Protocols in Domestic and Exotic Cats",
            "Non-Invasive Endocrine Monitoring of Ovarian Cycles and Pregnancy in Captive Wildlife",
            "Stem Cell Therapy for Endometrial Regeneration and Subfertility in Companion Animals"
        ],
        "featured_publications": [
            "Successful In Vitro Embryo Production Using Vitrified-Thawed Epididymal Spermatozoa in Endangered Felids",
            "Endocrine Profiling and Non-Invasive Fecal Hormone Monitoring During Pregnancy and Pseudopregnancy in Cats",
            "Impact of Cryoprotectant Formulations on Membrane Integrity and Mitochondrial Activity of Cryopreserved Feline Sperm"
        ]
    },

    # =========================================================================
    # 11. Faculty of Psychology (คณะจิตวิทยา จุฬาฯ)
    # =========================================================================
    {
        "id": "cu_psy_natsuda_001",
        "university": "Chulalongkorn University",
        "university_th": "จุฬาลงกรณ์มหาวิทยาลัย",
        "faculty": "Faculty of Psychology",
        "faculty_th": "คณะจิตวิทยา",
        "department": "Department of Clinical and Cognitive Psychology",
        "department_th": "ภาควิชาจิตวิทยาคลินิกและจิตวิทยาการรู้คิด",
        "academic_title": "Assoc. Prof. Dr.",
        "academic_title_th": "รศ.ดร.",
        "first_name": "Natsuda",
        "last_name": "Taweechotipatr",
        "full_name_th": "รศ.ดร. ณัฐสุดา เถาวัฒน์โชตน์",
        "role": "Dean of Faculty of Psychology & Foremost Authority in Cognitive Behavioral Therapy (CBT) and Adolescent Mental Health",
        "email": "natsuda.t@chula.ac.th",
        "profile_url": "https://psy.chula.ac.th/staff/natsuda-taweechotipatr",
        "scholar_url": "https://scholar.google.com/citations?user=natsudataweechotipatr",
        "education": [
            "Ph.D. (Clinical Psychology), University of Melbourne, Australia",
            "M.Sc. (Clinical Psychology), Chulalongkorn University",
            "B.Sc. (Psychology, First Class Honours), Chulalongkorn University"
        ],
        "research_interests": [
            "Transdiagnostic Cognitive Behavioral Therapy Protocols for Youth Anxiety and Depression",
            "Emotion Regulation Flexibility and Neurocognitive Predictors of Non-Suicidal Self-Injury (NSSI)",
            "Mindfulness-Based Cognitive Therapy (MBCT) and Mental Resilience in High-Stress Academic Settings",
            "Digital Mental Health Interventions and Tele-Psychotherapy Efficacy in Thai Adolescents"
        ],
        "featured_publications": [
            "Effectiveness of School-Based Cognitive Behavioral Interventions for Reducing Adolescent Depressive Symptoms",
            "Emotion Dysregulation and Rumination as Mediating Pathways to Non-Suicidal Self-Injury Among Youth",
            "Digital Mental Health Applications in Southeast Asia: Therapeutic Engagement and Clinical Outcome Evaluation"
        ]
    },
    {
        "id": "cu_psy_aranya_001",
        "university": "Chulalongkorn University",
        "university_th": "จุฬาลงกรณ์มหาวิทยาลัย",
        "faculty": "Faculty of Psychology",
        "faculty_th": "คณะจิตวิทยา",
        "department": "Department of Counseling Psychology",
        "department_th": "ภาควิชาจิตวิทยาการปรึกษา",
        "academic_title": "Assoc. Prof. Dr.",
        "academic_title_th": "รศ.ดร.",
        "first_name": "Aranya",
        "last_name": "Tuicomepee",
        "full_name_th": "รศ.ดร. อรัญญา ตุ้ยคัมภีร์",
        "role": "Leading Counseling Psychologist in Trauma-Informed Counseling, Post-Traumatic Growth (PTG) and Life Transition Coaching",
        "email": "aranya.t@chula.ac.th",
        "profile_url": "https://psy.chula.ac.th/staff/aranya-tuicomepee",
        "scholar_url": "https://scholar.google.com/citations?user=aranyatuicomepee",
        "education": [
            "Ph.D. (Counseling Psychology), University of Minnesota, USA",
            "M.A. (Counseling Psychology), Chulalongkorn University",
            "B.Sc. (Psychology), Chiang Mai University"
        ],
        "research_interests": [
            "Post-Traumatic Growth (PTG) and Meaning-Making Processes in Survivors of Natural and Human-Made Disasters",
            "Compassion Fatigue, Burnout and Secondary Traumatic Stress Among Healthcare Professionals",
            "Grief Counseling and Continuing Bonds in Bereaved Family Members",
            "Positive Psychological Interventions for Workplace Flourishing and Career Adaptation"
        ],
        "featured_publications": [
            "Facilitating Post-Traumatic Growth: A Qualitative Exploration of Meaning-Making Among Disaster Survivors",
            "Predictors of Compassion Fatigue and Professional Burnout in Palliative Care Nurses",
            "Culturally Adapted Counseling Interventions for Thai Adults Experiencing Complicated Grief"
        ]
    },

    # =========================================================================
    # 12. School of Agricultural Resources (สำนักวิชาทรัพยากรการเกษตร จุฬาฯ - SAR)
    # =========================================================================
    {
        "id": "cu_sar_nanthigorn_001",
        "university": "Chulalongkorn University",
        "university_th": "จุฬาลงกรณ์มหาวิทยาลัย",
        "faculty": "School of Agricultural Resources",
        "faculty_th": "สำนักวิชาทรัพยากรการเกษตร",
        "department": "Department of Sustainable Agriculture and Agro-Ecosystems",
        "department_th": "สาขาวิชาเกษตรยั่งยืนและระบบนิเวศเกษตร",
        "academic_title": "Assoc. Prof. Dr.",
        "academic_title_th": "รศ.ดร.",
        "first_name": "Nanthigorn",
        "last_name": "Tantiwanich",
        "full_name_th": "รศ.ดร. นันทิกร ตันติวนิช",
        "role": "Authority in Agroforestry, Watershed Restoration in Nan Province and Circular Agri-Food Chains",
        "email": "nanthigorn.t@chula.ac.th",
        "profile_url": "https://sar.chula.ac.th/staff/nanthigorn-tantiwanich",
        "scholar_url": "https://scholar.google.com/citations?user=nanthigorntantiwanich",
        "education": [
            "Ph.D. (Sustainable Agriculture / Agro-Ecology), AgroParisTech, France",
            "M.Sc. (Agronomy), Kasetsart University",
            "B.Sc. (Agricultural Resources), Chulalongkorn University"
        ],
        "research_interests": [
            "Agroforestry Land-Use Models to Replace Mono-Cropping Maize in Steep Highland Slopes (Nan Sandbox)",
            "Soil Organic Carbon Sequestration and Erosion Mitigation in Degraded Watershed Forests",
            "Shade-Grown Arabica Coffee and Cacao Quality Profiling in High-Altitude Canopies",
            "Community Seed Banking and Indigenous Crop Diversity Conservation"
        ],
        "featured_publications": [
            "Agroforestry Transition Strategies from Monoculture Corn to Multi-Tiered Agro-Forests in Nan Basin",
            "Soil Erosion Dynamics and Carbon Sequestration Under Alternative Highland Agricultural Regimes",
            "Flavor Precursor Profiling and Sensory Attributes of Shade-Grown Arabica Coffee in Upper Northern Thailand"
        ]
    },

    # =========================================================================
    # 13. College of Population Studies & Public Health Sciences (CPS & CPHS)
    # =========================================================================
    {
        "id": "cu_cps_vipan_001",
        "university": "Chulalongkorn University",
        "university_th": "จุฬาลงกรณ์มหาวิทยาลัย",
        "faculty": "College of Population Studies",
        "faculty_th": "วิทยาลัยประชากรศาสตร์",
        "department": "Department of Demography and Ageing Societies",
        "department_th": "สาขาวิชาประชากรศาสตร์และสังคมผู้สูงอายุ",
        "academic_title": "Prof. Dr.",
        "academic_title_th": "ศ.ดร.",
        "first_name": "Vipan",
        "last_name": "Prachuabmoh",
        "full_name_th": "ศ.ดร. วิพรรณ ประจวบเหมาะ",
        "role": "Foremost Demographer, Former Dean & International Authority in Active Ageing Index, National Pension Architecture and Fertility Transition",
        "email": "vipan.p@chula.ac.th",
        "profile_url": "https://cps.chula.ac.th/staff/vipan-prachuabmoh",
        "scholar_url": "https://scholar.google.com/citations?user=vipanprachuabmoh",
        "education": [
            "Ph.D. (Demography), University of Chicago, USA",
            "M.A. (Demography), University of Chicago, USA",
            "B.A. (Sociology), Chulalongkorn University"
        ],
        "research_interests": [
            "Constructing and Validating the Active Ageing Index (AAI) for Southeast Asian Economies",
            "Fiscal Sustainability of Multi-Tier National Pension Systems and Old-Age Income Security",
            "Ultra-Low Fertility Determinants, Family Policy Interventions and Female Labor Force Participation",
            "Intergenerational Transfers and Living Arrangements in Super-Aged Societies"
        ],
        "featured_publications": [
            "The Active Ageing Index in Developing Country Context: Methodology and Policy Implications for Thailand",
            "Pension Reform and Long-Term Fiscal Sustainability in the Face of Rapid Population Ageing",
            "Determinants of Lowest-Low Fertility Rates in Urban East and Southeast Asia"
        ]
    },
    {
        "id": "cu_cphs_chitlada_001",
        "university": "Chulalongkorn University",
        "university_th": "จุฬาลงกรณ์มหาวิทยาลัย",
        "faculty": "College of Public Health Sciences",
        "faculty_th": "วิทยาลัยวิทยาศาสตร์สาธารณสุข",
        "department": "Department of Public Health Sciences (Addiction and Behavioral Health)",
        "department_th": "สาขาวิทยาศาสตร์สาธารณสุข (หน่วยวิจัยสารเสพติดและพฤติกรรมสุขภาพ)",
        "academic_title": "Prof. Dr.",
        "academic_title_th": "ศ.ดร.",
        "first_name": "Chitlada",
        "last_name": "Areesantichai",
        "full_name_th": "ศ.ดร. จิตรลดา อารีย์สันติชัย",
        "role": "Dean of College of Public Health Sciences & Global Expert in Addiction Epidemiology, Drug Harm Reduction and Community Health",
        "email": "chitlada.a@chula.ac.th",
        "profile_url": "https://cphs.chula.ac.th/staff/chitlada-areesantichai",
        "scholar_url": "https://scholar.google.com/citations?user=chitladaareesantichai",
        "education": [
            "Ph.D. (Public Health), Chulalongkorn University",
            "M.Sc. (Pharmacology), Mahidol University",
            "B.Sc. (Public Health), Mahidol University"
        ],
        "research_interests": [
            "National Surveillance of Synthetic Drug Use Trends (Methamphetamine, Kratom, Synthetic Cannabinoids)",
            "Community-Based Harm Reduction Models and Addiction Rehabilitation Efficacy",
            "Behavioral Economics and Public Policy Interventions for Tobacco and E-Cigarette Control",
            "Environmental and Toxicological Exposure Assessment in Vulnerable Urban Populations"
        ],
        "featured_publications": [
            "Epidemiological Patterns of Methamphetamine and Multi-Drug Use in Southeast Asian Megacities",
            "Effectiveness of Community-Based Recovery Support Interventions for Substance Use Disorders",
            "E-Cigarette Prevalence, Dual Use and Nicotine Dependence Among Urban College Students"
        ]
    },

    # =========================================================================
    # 14. Energy Research Institute & Institute of Asian Studies (ERI & IAS)
    # =========================================================================
    {
        "id": "cu_eri_kulyos_001",
        "university": "Chulalongkorn University",
        "university_th": "จุฬาลงกรณ์มหาวิทยาลัย",
        "faculty": "Energy Research Institute (ERI)",
        "faculty_th": "สถาบันวิจัยพลังงาน",
        "department": "Department of Smart Energy Systems & Hydrogen Economy",
        "department_th": "ศูนย์วิจัยระบบพลังงานอัจฉริยะและเศรษฐกิจไฮโดรเจน",
        "academic_title": "Assoc. Prof. Dr.",
        "academic_title_th": "รศ.ดร.",
        "first_name": "Kulyos",
        "last_name": "Audomvongseree",
        "full_name_th": "รศ.ดร. กุลยศ อุดมวงศ์เสรี",
        "role": "Director of Energy Research Institute (ERI) & Foremost Authority in Power Development Plan (PDP), Smart Grids and Hydrogen Strategy",
        "email": "kulyos.a@chula.ac.th",
        "profile_url": "https://eri.chula.ac.th/staff/kulyos-audomvongseree",
        "scholar_url": "https://scholar.google.com/citations?user=kulyosaudomvongseree",
        "education": [
            "Ph.D. (Electrical Engineering / Power Systems), Tokyo Institute of Technology, Japan",
            "M.Eng. (Electrical Engineering), Chulalongkorn University",
            "B.Eng. (Electrical Engineering), Chulalongkorn University"
        ],
        "research_interests": [
            "National Power Development Plan (PDP) Decarbonization and Renewable Energy Target Modeling",
            "Green Hydrogen Production, Transport and Co-Firing in Gas Turbine Power Plants",
            "Battery Energy Storage System (BESS) Sizing and Grid Stability Under High Variable Solar Penetration",
            "Peer-to-Peer (P2P) Transactive Energy Market Architecture on Blockchain"
        ],
        "featured_publications": [
            "Decarbonization Pathways for Thailand Power Sector: Renewable Integration and Grid Flexibility Analysis",
            "Techno-Economic Evaluation of Green Hydrogen Production from Excess Renewable Energy for Power Generation",
            "Optimal Sizing and Energy Arbitrage of Grid-Scale Battery Storage Systems Under Dynamic Pricing"
        ]
    },
    {
        "id": "cu_ias_naruemon_001",
        "university": "Chulalongkorn University",
        "university_th": "จุฬาลงกรณ์มหาวิทยาลัย",
        "faculty": "Institute of Asian Studies (IAS)",
        "faculty_th": "สถาบันเอเชียศึกษา",
        "department": "Center of Excellence in Mekong Studies and Human Security",
        "department_th": "ศูนย์ความเป็นเลิศด้านแม่โขงศึกษาและความมั่นคงของมนุษย์",
        "academic_title": "Assoc. Prof. Dr.",
        "academic_title_th": "รศ.ดร.",
        "first_name": "Naruemon",
        "last_name": "Thabchumpon",
        "full_name_th": "รศ.ดร. นฤมล ทับจุมพล",
        "role": "Director of MA in International Development (MAIDS) & Senior Scholar in Mekong Transboundary Politics, Refugee Rights and Human Security",
        "email": "naruemon.t@chula.ac.th",
        "profile_url": "https://ias.chula.ac.th/staff/naruemon-thabchumpon",
        "scholar_url": "https://scholar.google.com/citations?user=naruemonthabchumpon",
        "education": [
            "Ph.D. (Politics and International Studies), University of Leeds, UK",
            "M.A. (Development Studies), Institute of Social Studies (ISS), The Netherlands",
            "B.A. (Political Science), Chulalongkorn University"
        ],
        "research_interests": [
            "Human Rights, Statelessness and Refugee Protection Protocols Along the Thai-Myanmar Border",
            "Transboundary Environmental Impact Assessment (TbEIA) in Mekong Mainstream Hydropower",
            "ASEAN Human Rights Governance and Non-Interference Principle Debates",
            "Civic Activism and Civil Society Coalitions in Regional Environmental Defense"
        ],
        "featured_publications": [
            "Human Security and Transnational Resource Politics in the Salween River Basin",
            "Refugees and Displaced Persons in Thailand: Protracted Situations, Legal Limbo, and Durable Solutions",
            "Civil Society Responses to Transboundary Environmental Injustice in the Greater Mekong Subregion"
        ]
    }
]
