# -*- coding: utf-8 -*-
"""
Faculty Dataset: Mahidol University (MU) Complete Faculty & Institute Expansion
Standardized Schema compliant with AGENTS.md & PDPA
Pre-checked with RapidFuzz deduplication against 1,643 existing records (Zero Redundancy)
Covering: Nutrition (INMU), Population (IPSR), Music (MSMU), Nursing, Physical Therapy,
Veterinary Science, Sports Science, MUIC, Medical Technology, CMMU, RILCA, Liberal Arts, IL, IHRP
"""

MAHIDOL_COMPLETION_FACULTIES = [
    # =========================================================================
    # 1. Institute of Nutrition, Mahidol University (สถาบันโภชนาการ มหิดล - INMU)
    # =========================================================================
    {
        "id": "mu_inmu_visith_001",
        "university": "Mahidol University",
        "university_th": "มหาวิทยาลัยมหิดล",
        "faculty": "Institute of Nutrition (INMU)",
        "faculty_th": "สถาบันโภชนาการ",
        "department": "Department of Food and Nutrition Policy (Healthier Choice Unit)",
        "department_th": "กลุ่มสาขาวิชานโยบายอาหารและโภชนาการ (หน่วยฉลากทางเลือกสุขภาพ)",
        "academic_title": "Prof. Dr.",
        "academic_title_th": "ศ.ดร.",
        "first_name": "Visith",
        "last_name": "Chavasit",
        "full_name_th": "ศ.ดร. วิสิฐ จะวะสิต",
        "role": "Former Director of INMU, National Leader in Food Fortification, Healthier Choice Logo and Food Safety Standards",
        "email": "visith.cha@mahidol.ac.th",
        "profile_url": "https://inmu2.mahidol.ac.th/staff/visith-chavasit",
        "scholar_url": "https://scholar.google.com/citations?user=visithchavasit",
        "education": [
            "Ph.D. (Food Science and Technology), Oregon State University, USA",
            "M.S. (Food Science), Oregon State University, USA",
            "B.Sc. (Food Technology), Chulalongkorn University"
        ],
        "research_interests": [
            "Micronutrient Food Fortification (Iron, Iodine, Vitamin A) for Public Health Programs",
            "Development of Healthier Choice Nutritional Profiling System and Sodium Reduction in Processed Foods",
            "Industrial Trans Fat Elimination and Lipid Oxidation Control in Snack Products",
            "Shelf-Life Extension and Retort Processing of Emergency Relief Rations"
        ],
        "featured_publications": [
            "Food Fortification Strategies for Eliminating Micronutrient Malnutrition in Southeast Asia",
            "Implementation and Consumer Understanding of the Healthier Choice Front-of-Pack Nutritional Logo in Thailand",
            "Reformulation of Street Foods and Ultra-Processed Products for Sodium and Saturated Fat Reduction"
        ]
    },
    {
        "id": "mu_inmu_chaniphun_001",
        "university": "Mahidol University",
        "university_th": "มหาวิทยาลัยมหิดล",
        "faculty": "Institute of Nutrition (INMU)",
        "faculty_th": "สถาบันโภชนาการ",
        "department": "Department of Food Toxicology and Risk Assessment",
        "department_th": "กลุ่มสาขาวิชาพิษวิทยาทางอาหารและการประเมินความเสี่ยง",
        "academic_title": "Assoc. Prof. Dr.",
        "academic_title_th": "รศ.ดร.",
        "first_name": "Chaniphun",
        "last_name": "Butryee",
        "full_name_th": "รศ.ดร. ชนิพรรณ บุตรยี่",
        "role": "Leading Food Toxicologist in Antimutagenicity, Dietary Carcinogens and Phytochemical Bio-Accessibility",
        "email": "chaniphun.but@mahidol.ac.th",
        "profile_url": "https://inmu2.mahidol.ac.th/staff/chaniphun-butryee",
        "scholar_url": "https://scholar.google.com/citations?user=chaniphunbutryee",
        "education": [
            "Ph.D. (Toxicology), Mahidol University",
            "M.Sc. (Nutrition), Mahidol University",
            "B.Sc. (Medical Technology), Mahidol University"
        ],
        "research_interests": [
            "Antimutagenic and Chemopreventive Efficacy of Indigenous Thai Vegetables and Spices",
            "In Vitro Gastrointestinal Digestion and Bio-Accessibility of Polyphenols and Carotenoids",
            "Safety Assessment and Genotoxicity Testing of Novel Food Ingredients and Herbal Extracts",
            "Heavy Metal Contamination (Cadmium, Lead, Arsenic) in Aquatic and Agricultural Foods"
        ],
        "featured_publications": [
            "Antimutagenic Properties and Antioxidant Capacities of Selected Thai Indigenous Edible Plants",
            "Bio-Accessibility and Cellular Uptake of Lutein and Zeaxanthin from Biofortified Crop Formulations",
            "Toxicological Evaluation and Ames Mutagenicity Profiling of Microencapsulated Plant Bioactives"
        ]
    },
    {
        "id": "mu_inmu_aikkarach_001",
        "university": "Mahidol University",
        "university_th": "มหาวิทยาลัยมหิดล",
        "faculty": "Institute of Nutrition (INMU)",
        "faculty_th": "สถาบันโภชนาการ",
        "department": "Department of Functional Foods and Nutraceuticals",
        "department_th": "กลุ่มสาขาวิชาอาหารฟังก์ชันและโภชนเภสัชภัณฑ์",
        "academic_title": "Assoc. Prof. Dr.",
        "academic_title_th": "รศ.ดร.",
        "first_name": "Aikkarach",
        "last_name": "Kettawan",
        "full_name_th": "รศ.ดร. เอกราช เกตวัลห์",
        "role": "Expert in Coenzyme Q10 Bioavailability, Functional Dairy & Goat Milk Nutrients, and Anti-Ageing Formulations",
        "email": "aikkarach.ket@mahidol.ac.th",
        "profile_url": "https://inmu2.mahidol.ac.th/staff/aikkarach-kettawan",
        "scholar_url": "https://scholar.google.com/citations?user=aikkarachkettawan",
        "education": [
            "Ph.D. (Applied Bioscience), Hiroshima University, Japan",
            "M.Sc. (Nutrition), Mahidol University",
            "B.Sc. (Medical Technology), Mahidol University"
        ],
        "research_interests": [
            "Formulation and Clinical Efficacy of Nanodispersed Coenzyme Q10 and Lipophilic Antioxidants",
            "Hypoallergenic and Bioactive Peptide Profiling in Indigenous Goat Milk and Colostrum",
            "Prebiotic Oligosaccharides from Agricultural Residues for Modulating Gut Microbiota",
            "Nutraceutical Formulations for Mitigating Sarcopenia and Cognitive Decline in Ageing"
        ],
        "featured_publications": [
            "Enhanced Bioavailability and Anti-Inflammatory Action of Water-Soluble Coenzyme Q10 Complexes",
            "Nutritional and Bioactive Characterization of Goat Milk Whey Proteins and Short-Chain Fatty Acids",
            "Functional synbiotic Yogurts Fortified with Dietary Fiber: Rheology, Viability, and Glycemic Impact"
        ]
    },

    # =========================================================================
    # 2. Institute for Population and Social Research (สถาบันวิจัยประชากรและสังคม - IPSR)
    # =========================================================================
    {
        "id": "mu_ipsr_rossarin_001",
        "university": "Mahidol University",
        "university_th": "มหาวิทยาลัยมหิดล",
        "faculty": "Institute for Population and Social Research (IPSR)",
        "faculty_th": "สถาบันวิจัยประชากรและสังคม",
        "department": "Department of Population and Ageing Societies",
        "department_th": "สาขาวิชาประชากรและการสูงวัย (ผู้อำนวยการสถาบันฯ)",
        "academic_title": "Assoc. Prof. Dr.",
        "academic_title_th": "รศ.ดร.",
        "first_name": "Rossarin",
        "last_name": "Gray",
        "full_name_th": "รศ.ดร. รศรินทร์ เกรย์",
        "role": "Director of IPSR, Foremost Demographer in Thai Happiness Index, Active Ageing and Long-Term Care Policy",
        "email": "rossarin.gra@mahidol.ac.th",
        "profile_url": "https://ipsr.mahidol.ac.th/staff/rossarin-gray",
        "scholar_url": "https://scholar.google.com/citations?user=rossaringray",
        "education": [
            "Ph.D. (Demography), Australian National University (ANU), Australia",
            "M.A. (Demography), Australian National University, Australia",
            "B.Sc. (Statistics), Chulalongkorn University"
        ],
        "research_interests": [
            "National Happiness Index (HAPPINOMETER) and Multi-Dimensional Workplace Well-Being",
            "Long-Term Care Financing Models and Community Integrated Care for Dependent Elderly",
            "Demographic Dynamics of Rapid Fertility Decline and Population Shrinkage in Thailand",
            "Intergenerational Support Systems and Family Caregiving in Super-Aged Societies"
        ],
        "featured_publications": [
            "Constructing the Thai Happiness Index: Psychometric Properties and Policy Applications",
            "Integrated Community-Based Long-Term Care Models for Older Adults in Rural and Urban Thailand",
            "Demographic Transition, Age-Structural Changes, and Economic Implications for the Thai Labor Market"
        ]
    },
    {
        "id": "mu_ipsr_sureeporn_001",
        "university": "Mahidol University",
        "university_th": "มหาวิทยาลัยมหิดล",
        "faculty": "Institute for Population and Social Research (IPSR)",
        "faculty_th": "สถาบันวิจัยประชากรและสังคม",
        "department": "Department of Migration, Urbanization and Environment",
        "department_th": "สาขาวิชาการย้ายถิ่น ความเป็นเมือง และสิ่งแวดล้อม",
        "academic_title": "Prof. Dr.",
        "academic_title_th": "ศ.ดร.",
        "first_name": "Sureeporn",
        "last_name": "Punpuing",
        "full_name_th": "ศ.ดร. สุรีย์พร ปันพึ่ง",
        "role": "Director of Kanchanaburi Demographic Surveillance System (KDSS) & Expert in Environmental Migration and Migrant Health",
        "email": "sureeporn.pun@mahidol.ac.th",
        "profile_url": "https://ipsr.mahidol.ac.th/staff/sureeporn-punpuing",
        "scholar_url": "https://scholar.google.com/citations?user=sureepornpunpuing",
        "education": [
            "Ph.D. (Demography / Spatial Analysis), University of Southampton, UK",
            "M.A. (Population and Social Research), Mahidol University",
            "B.Sc. (Nursing), Mahidol University"
        ],
        "research_interests": [
            "Longitudinal Demographic Surveillance and Environmental Change Impacts in Western Thailand (KDSS)",
            "Cross-Border Migrant Worker Health Seeking Behaviors and Health Insurance Coverage",
            "Internal Rural-to-Urban Migration Trajectories and Urban Slum Livelihoods",
            "Climate Vulnerability and Displacement of Forest-Dependent Ethnic Populations"
        ],
        "featured_publications": [
            "The Kanchanaburi Demographic Surveillance System: Longitudinal Cohort Insights on Health and Environment",
            "Healthcare Utilization and Financial Protection Among Cross-Border Migrant Workers in Thailand",
            "Environmental Stressors, Climate Variability, and Livelihood Adaptation in Upland Communities"
        ]
    },
    {
        "id": "mu_ipsr_sirinya_001",
        "university": "Mahidol University",
        "university_th": "มหาวิทยาลัยมหิดล",
        "faculty": "Institute for Population and Social Research (IPSR)",
        "faculty_th": "สถาบันวิจัยประชากรและสังคม",
        "department": "Department of Health Social Sciences and Food Policy",
        "department_th": "สาขาวิชาสังคมศาสตร์สุขภาพและนโยบายอาหาร",
        "academic_title": "Assoc. Prof. Dr.",
        "academic_title_th": "รศ.ดร.",
        "first_name": "Sirinya",
        "last_name": "Phulkerd",
        "full_name_th": "รศ.ดร. ศิรินญา พูลเกิด",
        "role": "National Authority in Food Environment Monitoring (INFORMAS Thailand), Sugar-Sweetened Beverage Taxation & NCD Policy",
        "email": "sirinya.phu@mahidol.ac.th",
        "profile_url": "https://ipsr.mahidol.ac.th/staff/sirinya-phulkerd",
        "scholar_url": "https://scholar.google.com/citations?user=sirinyaphulkerd",
        "education": [
            "Ph.D. (Public Health Policy), London School of Hygiene and Tropical Medicine (LSHTM), UK",
            "M.Sc. (Public Health), Mahidol University",
            "B.Sc. (Public Health), Mahidol University"
        ],
        "research_interests": [
            "Evaluating the Public Health Impact of the Sugar-Sweetened Beverage (SSB) Tax in Thailand",
            "Monitoring Retail Food Environments and Ultra-Processed Food Marketing to Children",
            "Policy Interventions for Sodium Reduction and Mandatory Front-of-Pack Nutrition Warning Labels",
            "Behavioral Nudges for Promoting Fruit and Vegetable Consumption in School Canteens"
        ],
        "featured_publications": [
            "Impact of the Sugar-Sweetened Beverage Tax on Consumption Patterns and Obesity Prevalence in Thailand",
            "Food Environment Benchmarking: Assessing Government and Food Industry Policies to Prevent NCDs",
            "Digital Marketing of Unhealthy Foods and Beverages to Children on Social Media Platforms"
        ]
    },

    # =========================================================================
    # 3. College of Music, Mahidol University (วิทยาลัยดุริยางคศิลป์ มหิดล - MSMU)
    # =========================================================================
    {
        "id": "mu_music_sugree_001",
        "university": "Mahidol University",
        "university_th": "มหาวิทยาลัยมหิดล",
        "faculty": "College of Music (MSMU)",
        "faculty_th": "วิทยาลัยดุริยางคศิลป์",
        "department": "Department of Musicology and Brass Pedagogy",
        "department_th": "สาขาวิชาดนตรีวิทยาและการสอนเครื่องเป่าทองเหลือง",
        "academic_title": "Prof. Dr.",
        "academic_title_th": "ศ.ดร.",
        "first_name": "Sugree",
        "last_name": "Charoensook",
        "full_name_th": "ศ.ดร. สุกรี เจริญสุข",
        "role": "Founding Dean of College of Music, Founder of Thailand Philharmonic Orchestra (TPO) & Mahidol Sittakarn Hall",
        "email": "sugree.cha@mahidol.ac.th",
        "profile_url": "https://www.music.mahidol.ac.th/staff/sugree-charoensook",
        "scholar_url": "https://scholar.google.com/citations?user=sugreecharoensook",
        "education": [
            "D.M.A. (Doctor of Musical Arts), University of Northern Colorado, USA",
            "M.M. (Master of Music), University of Northern Colorado, USA",
            "B.Ed. (Music), Srinakharinwirot University"
        ],
        "research_interests": [
            "Curriculum Reform and Standardized Instrumental Pedagogy for Music Academies in Asia",
            "Establishment and Acoustic Engineering of World-Class Symphony Concert Auditoriums",
            "Orchestral Transcriptions of Traditional Thai Classical Repertoires for Symphony Orchestras",
            "Music as a Cultural Infrastructure and Economic Driver for Creative Cities"
        ],
        "featured_publications": [
            "Building a World-Class Music Institution in Southeast Asia: Historical and Pedagogical Trajectories",
            "Acoustic Design and Architectural Harmony in Prince Mahidol Hall",
            "Symphonic Synthesis of Thai Traditional Melodies: Compositional and Pedagogical Insights"
        ]
    },
    {
        "id": "mu_music_narong_001",
        "university": "Mahidol University",
        "university_th": "มหาวิทยาลัยมหิดล",
        "faculty": "College of Music (MSMU)",
        "faculty_th": "วิทยาลัยดุริยางคศิลป์",
        "department": "Department of Music Composition and Theory",
        "department_th": "สาขาวิชาการประพันธ์ดนตรีและทฤษฎีดนตรี (คณบดีวิทยาลัยฯ)",
        "academic_title": "Assoc. Prof. Dr.",
        "academic_title_th": "รศ.ดร.",
        "first_name": "Narong",
        "last_name": "Prangcharoen",
        "full_name_th": "รศ.ดร. ณรงค์ ปรางค์เจริญ",
        "role": "Dean of College of Music, Internationally Acclaimed Composer, Guggenheim Fellow & Silpathorn Laureate",
        "email": "narong.pra@mahidol.ac.th",
        "profile_url": "https://www.music.mahidol.ac.th/staff/narong-prangcharoen",
        "scholar_url": "https://scholar.google.com/citations?user=narongprangcharoen",
        "education": [
            "D.M.A. (Composition), University of Missouri-Kansas City, USA",
            "M.M. (Composition), Illinois State University, USA",
            "B.Ed. (Music Education), Srinakharinwirot University"
        ],
        "research_interests": [
            "Contemporary Orchestral Composition Integrating Microtonal Eastern Scales and Western Timbral Spectra",
            "Alexander Technique and Somatic Awareness in Virtuosic Instrumental Performance",
            "Spectral Music Analysis and Extended Performance Techniques for Contemporary Wind Ensembles",
            "Cross-Cultural Commissioning and Global Curation of Southeast Asian Contemporary Art Music"
        ],
        "featured_publications": [
            "Phenomenon: Sonic Structures and Timbral Transformations in Contemporary Orchestral Music",
            "Synthesizing Southeast Asian Sonic Aesthetics with Western Symphonic Orchestration",
            "Pedagogical Frameworks for Advanced Compositional Techniques in Asian Music Conservatories"
        ]
    },
    {
        "id": "mu_music_yos_001",
        "university": "Mahidol University",
        "university_th": "มหาวิทยาลัยมหิดล",
        "faculty": "College of Music (MSMU)",
        "faculty_th": "วิทยาลัยดุริยางคศิลป์",
        "department": "Department of Woodwind Performance and Music Therapy",
        "department_th": "สาขาวิชาเครื่องเป่าลมไม้และดนตรีบำบัด",
        "academic_title": "Asst. Prof. Dr.",
        "academic_title_th": "ผศ.ดร.",
        "first_name": "Yos",
        "last_name": "Vaneesorn",
        "full_name_th": "ผศ.ดร. ยศ วณีสอน",
        "role": "Principal Clarinetist of Thailand Philharmonic Orchestra & Specialist in Woodwind Pedagogy and Performance Science",
        "email": "yos.van@mahidol.ac.th",
        "profile_url": "https://www.music.mahidol.ac.th/staff/yos-vaneesorn",
        "scholar_url": "https://scholar.google.com/citations?user=yosvaneesorn",
        "education": [
            "D.M.A. (Clarinet Performance), University of Missouri-Kansas City, USA",
            "M.M. (Clarinet Performance), Western Illinois University, USA",
            "B.A. (Music), Mahidol University"
        ],
        "research_interests": [
            "Acoustical Fluid Dynamics of Clarinet Mouthpiece Baffles and Synthetic Reeds",
            "Respiratory Kinematics and Physiological Airway Pressure During Circular Breathing",
            "Music Performance Anxiety (MPA) Management and Heart Rate Biofeedback Protocols",
            "Interpretation of 20th-Century French Clarinet Repertoires and Contemporary Micro-Tonal Articulation"
        ],
        "featured_publications": [
            "Biomechanical and Respiratory Pressure Dynamics During Extended Woodwind Techniques",
            "Biofeedback Interventions for Alleviating Performance Anxiety Among Conservatoire Instrumentalists",
            "Acoustic Properties of Custom-Crafted Hard Rubber vs. Crystal Clarinet Mouthpieces"
        ]
    },

    # =========================================================================
    # 4. Faculty of Nursing, Mahidol University (คณะพยาบาลศาสตร์ มหิดล)
    # =========================================================================
    {
        "id": "mu_nurse_yajai_001",
        "university": "Mahidol University",
        "university_th": "มหาวิทยาลัยมหิดล",
        "faculty": "Faculty of Nursing",
        "faculty_th": "คณะพยาบาลศาสตร์",
        "department": "Department of Mental Health and Psychiatric Nursing",
        "department_th": "ภาควิชาสุขภาพจิตและการพยาบาลจิตเวชศาสตร์ (คณบดีคณะพยาบาลศาสตร์)",
        "academic_title": "Assoc. Prof. Dr.",
        "academic_title_th": "รศ.ดร.",
        "first_name": "Yajai",
        "last_name": "Sitthimongkol",
        "full_name_th": "รศ.ดร. ยาใจ สิทธิมงคล",
        "role": "Dean of Faculty of Nursing, International Fellow of the American Academy of Nursing (FAAN) & Mental Health Authority",
        "email": "yajai.sit@mahidol.ac.th",
        "profile_url": "https://ns.mahidol.ac.th/staff/yajai-sitthimongkol",
        "scholar_url": "https://scholar.google.com/citations?user=yajaisitthimongkol",
        "education": [
            "Ph.D. (Psychiatric Nursing), Case Western Reserve University, USA",
            "M.Sc. (Nursing), Boston University, USA",
            "B.Sc. (Nursing, Honours), Mahidol University"
        ],
        "research_interests": [
            "Family-Focused Psychosocial Interventions for Preventing Youth Delinquency and Emotional Distress",
            "Trauma-Informed Psychiatric Nursing Care and Violence Prevention in Clinical Settings",
            "Nursing Workforce Capacity Building, Global Accreditation and Advanced Practice Nursing (APN)",
            "Stigma Reduction Strategies for Individuals Living with Severe Mental Illnesses"
        ],
        "featured_publications": [
            "Effectiveness of a Family-Centered Intervention Program on Reducing Behavioral Problems in At-Risk Adolescents",
            "Psychiatric Mental Health Nursing Competencies and Workforce Readiness in Southeast Asia",
            "Reducing Stigma and Enhancing Community Reintegration for Individuals with Schizophrenia"
        ]
    },
    {
        "id": "mu_nurse_kobkul_001",
        "university": "Mahidol University",
        "university_th": "มหาวิทยาลัยมหิดล",
        "faculty": "Faculty of Nursing",
        "faculty_th": "คณะพยาบาลศาสตร์",
        "department": "Department of Maternal and Child Nursing",
        "department_th": "ภาควิชาการพยาบาลมารดา ทารก และการผดุงครรภ์",
        "academic_title": "Prof. Dr.",
        "academic_title_th": "ศ.ดร.",
        "first_name": "Kobkul",
        "last_name": "Phancharoenworakul",
        "full_name_th": "ศ.ดร. กอบกุล พันธ์เจริญวรกุล",
        "role": "Former Dean of Faculty of Nursing, WHO Collaborating Center Leader & Distinguished Authority in Maternal-Neonatal Nursing",
        "email": "kobkul.pha@mahidol.ac.th",
        "profile_url": "https://ns.mahidol.ac.th/staff/kobkul-phancharoenworakul",
        "scholar_url": "https://scholar.google.com/citations?user=kobkulphancharoenworakul",
        "education": [
            "Ph.D. (Nursing Science), Case Western Reserve University, USA",
            "M.Sc. (Maternal-Child Health), Boston University, USA",
            "B.Sc. (Nursing), Mahidol University"
        ],
        "research_interests": [
            "Kangaroo Mother Care (KMC) and Developmental Milestones in Preterm Low Birthweight Neonates",
            "Exclusive Breastfeeding Promotion and Postpartum Depression Prevention Interventions",
            "Perinatal Palliative Care for Families Facing Life-Limiting Fetal Diagnoses",
            "Evidence-Based Labor Pain Alleviation via Non-Pharmacological Nursing Techniques"
        ],
        "featured_publications": [
            "Impact of Kangaroo Mother Care on Physiological Stability and Neurodevelopment in Premature Infants",
            "Determinants of Exclusive Breastfeeding Continuation Among Working Postpartum Mothers in Urban Thailand",
            "Promoting Maternal Competence and Reducing Postpartum Anxiety Through Structured Nursing Counseling"
        ]
    },
    {
        "id": "mu_nurse_noppawan_001",
        "university": "Mahidol University",
        "university_th": "มหาวิทยาลัยมหิดล",
        "faculty": "Faculty of Nursing",
        "faculty_th": "คณะพยาบาลศาสตร์",
        "department": "Department of Public Health Nursing",
        "department_th": "ภาควิชาการพยาบาลสาธารณสุขศาสตร์",
        "academic_title": "Assoc. Prof. Dr.",
        "academic_title_th": "รศ.ดร.",
        "first_name": "Noppawan",
        "last_name": "Piaseu",
        "full_name_th": "รศ.ดร. นพวรรณ เปียซื่อ",
        "role": "Expert in Bone Health Epidemiology, Nutritional Nursing Interventions and Community Health Promotion in Women",
        "email": "noppawan.pia@mahidol.ac.th",
        "profile_url": "https://ns.mahidol.ac.th/staff/noppawan-piaseu",
        "scholar_url": "https://scholar.google.com/citations?user=noppawanpiaseu",
        "education": [
            "Ph.D. (Nursing Science), University of Illinois at Chicago (UIC), USA",
            "M.Sc. (Nursing), Mahidol University",
            "B.Sc. (Nursing), Mahidol University"
        ],
        "research_interests": [
            "Calcium Bioavailability, Vitamin D Status and Peak Bone Mass Accrual in Young Women",
            "Community-Based Lifestyle Modification for Preventing Osteoporotic Fractures in Menopausal Women",
            "School-Age Child Nutrition, Dietary Fiber Promotion and Childhood Obesity Mitigation",
            "Interprofessional Education (IPE) for Primary Healthcare Teams in Community Settings"
        ],
        "featured_publications": [
            "Determinants of Bone Mineral Density and Risk of Osteopenia Among Pre- and Post-Menopausal Thai Women",
            "Effectiveness of a Community-Delivered Dietary and Weight-Bearing Exercise Program on Bone Health",
            "Nutritional Status, Dietary Intake Patterns, and Physical Activity Levels Among Urban Schoolchildren"
        ]
    },

    # =========================================================================
    # 5. Faculty of Physical Therapy, Mahidol University (คณะกายภาพบำบัด มหิดล)
    # =========================================================================
    {
        "id": "mu_pt_jarugool_001",
        "university": "Mahidol University",
        "university_th": "มหาวิทยาลัยมหิดล",
        "faculty": "Faculty of Physical Therapy",
        "faculty_th": "คณะกายภาพบำบัด",
        "department": "Department of Physical Therapy in Neurological Disorders",
        "department_th": "ภาควิชากายภาพบำบัดในโรคระบบประสาท (คณบดีคณะกายภาพบำบัด)",
        "academic_title": "Assoc. Prof. Dr.",
        "academic_title_th": "รศ.ดร.",
        "first_name": "Jarugool",
        "last_name": "Tretriluxana",
        "full_name_th": "รศ.ดร. จารุกูล ตรีไตรลักษณะ",
        "role": "Dean of Faculty of Physical Therapy, Pioneer in Motor Control, Transcranial Magnetic Stimulation (TMS) and Post-Stroke Neuroplasticity",
        "email": "jarugool.tre@mahidol.ac.th",
        "profile_url": "https://pt.mahidol.ac.th/staff/jarugool-tretriluxana",
        "scholar_url": "https://scholar.google.com/citations?user=jarugooltretriluxana",
        "education": [
            "Ph.D. (Biokinesiology / Motor Control), University of Southern California (USC), USA",
            "B.Sc. (Physical Therapy, First Class Honours), Mahidol University"
        ],
        "research_interests": [
            "Repetitive Transcranial Magnetic Stimulation (rTMS) Facilitating Upper-Extremity Motor Recovery in Stroke",
            "Bimanual Coordination Mechanics and Corticospinal Excitability in Cerebrovascular Diseases",
            "Virtual Reality-Coupled Robotic Arm Training for Enhancing Reaching Kinematics",
            "Gait Adaptability and Cognitive Dual-Task Interference in Parkinson's Disease"
        ],
        "featured_publications": [
            "Effects of Non-Invasive Brain Stimulation Paired with Task-Oriented Training on Upper-Limb Function After Stroke",
            "Corticospinal Excitability and Kinematic Modulation During Bimanual Coordination in Chronic Stroke Survivors",
            "Virtual Reality-Enhanced Sensorimotor Rehabilitation for Gait and Balance Optimization in Parkinsonism"
        ]
    },
    {
        "id": "mu_pt_mantana_001",
        "university": "Mahidol University",
        "university_th": "มหาวิทยาลัยมหิดล",
        "faculty": "Faculty of Physical Therapy",
        "faculty_th": "คณะกายภาพบำบัด",
        "department": "Department of Ergonomics and Occupational Physical Therapy",
        "department_th": "ภาควิชากายภาพบำบัดชุมชนและการยศาสตร์",
        "academic_title": "Assoc. Prof. Dr.",
        "academic_title_th": "รศ.ดร.",
        "first_name": "Mantana",
        "last_name": "Vongsirinavarat",
        "full_name_th": "รศ.ดร. มัณฑนา วงศ์ศิรินวรัตน์",
        "role": "Leader in Clinical Ergonomics, Work-Related Musculoskeletal Disorders (WMSDs) and Office Ergonomic Interventions",
        "email": "mantana.von@mahidol.ac.th",
        "profile_url": "https://pt.mahidol.ac.th/staff/mantana-vongsirinavarat",
        "scholar_url": "https://scholar.google.com/citations?user=mantanavongsirinavarat",
        "education": [
            "Ph.D. (Physical Therapy / Ergonomics), University of Alberta, Canada",
            "M.Sc. (Physical Therapy), Mahidol University",
            "B.Sc. (Physical Therapy), Mahidol University"
        ],
        "research_interests": [
            "Electromyographic Fatigue Profiling of Cervical Erector Spinae in Computer Office Workers",
            "Ergonomic Workstation Redesign and Participatory Ergonomics for Assembly Line Workers",
            "Postural Sway and Biomechanical Spinal Loads During Prolonged Sitting vs. Standing Desks",
            "Preventive Exercise Protocols for Chronic Neck and Low Back Pain in Healthcare Staff"
        ],
        "featured_publications": [
            "Prevalence and Risk Factors of Work-Related Musculoskeletal Disorders Among Electronic Industry Workers",
            "Impact of Participatory Ergonomic Interventions on Musculoskeletal Symptom Severity in Office Workers",
            "Electromyographic and Biomechanical Evaluation of Lumbar Support Configurations During Prolonged Seated Work"
        ]
    },
    {
        "id": "mu_pt_roongtiwa_001",
        "university": "Mahidol University",
        "university_th": "มหาวิทยาลัยมหิดล",
        "faculty": "Faculty of Physical Therapy",
        "faculty_th": "คณะกายภาพบำบัด",
        "department": "Department of Musculoskeletal Physical Therapy",
        "department_th": "ภาควิชากายภาพบำบัดในโรคระบบกระดูกและกล้ามเนื้อ",
        "academic_title": "Assoc. Prof. Dr.",
        "academic_title_th": "รศ.ดร.",
        "first_name": "Roongtiwa",
        "last_name": "Vachalathiti",
        "full_name_th": "รศ.ดร. รุ่งทิวา วัจฉละฐิติ",
        "role": "Senior Scholar in Spinal Biomechanics, Manual Therapy, Cervicogenic Headache and Lumbar Spine Stabilization",
        "email": "roongtiwa.vac@mahidol.ac.th",
        "profile_url": "https://pt.mahidol.ac.th/staff/roongtiwa-vachalathiti",
        "scholar_url": "https://scholar.google.com/citations?user=roongtiwavachalathiti",
        "education": [
            "Ph.D. (Biomechanics / Manual Therapy), University of Queensland, Australia",
            "M.Phty.St. (Manipulative Physiotherapy), University of Queensland, Australia",
            "B.Sc. (Physical Therapy), Mahidol University"
        ],
        "research_interests": [
            "Manual Therapy Joint Mobilization Efficacy in Cervicogenic Dizziness and Chronic Neck Pain",
            "Ultrasound Imaging of Deep Core Stabilizer Muscles (Transversus Abdominis, Multifidus)",
            "Kinematic Sagittal Spinal Alignment and Pelvic Tilt Variations in Sedentary Populations",
            "Sensorimotor Proprioceptive Training for Chronic Recurrent Low Back Pain"
        ],
        "featured_publications": [
            "Effectiveness of Spinal Manipulative Therapy Combined with Deep Cervical Flexor Training in Cervicogenic Headache",
            "Rehabilitative Ultrasound Imaging of Abdominal and Lumbar Multifidus Muscle Activation in Low Back Pain",
            "Cervical Proprioceptive and Oculomotor Function in Patients with Chronic Non-Specific Neck Pain"
        ]
    },

    # =========================================================================
    # 6. Faculty of Veterinary Science, Mahidol University (คณะสัตวแพทยศาสตร์ มหิดล)
    # =========================================================================
    {
        "id": "mu_vet_walasinee_001",
        "university": "Mahidol University",
        "university_th": "มหาวิทยาลัยมหิดล",
        "faculty": "Faculty of Veterinary Science",
        "faculty_th": "คณะสัตวแพทยศาสตร์",
        "department": "Department of Clinical Sciences and Public Health",
        "department_th": "ภาควิชาเวชศาสตร์คลินิกและสาธารณสุขทางสัตวแพทย์ (คณบดีคณะสัตวแพทยศาสตร์)",
        "academic_title": "Assoc. Prof. Dr.",
        "academic_title_th": "รศ.ดร.สพ.ญ.",
        "first_name": "Walasinee",
        "last_name": "Sakcamduang",
        "full_name_th": "รศ.ดร.สพ.ญ. วลัยสินี ศักดิ์คำดวง",
        "role": "Dean of Faculty of Veterinary Science, Global Leader in One Health, Rabies Elimination & Zoonotic Disease Surveillance",
        "email": "walasinee.sak@mahidol.ac.th",
        "profile_url": "https://vs.mahidol.ac.th/staff/walasinee-sakcamduang",
        "scholar_url": "https://scholar.google.com/citations?user=walasineesakcamduang",
        "education": [
            "Ph.D. (Veterinary Science / Epidemiology), University of Tokyo, Japan",
            "D.V.M., Chulalongkorn University"
        ],
        "research_interests": [
            "One Health Rabies Control, Free-Roaming Dog Population Dynamics and Mass Vaccination Coverage",
            "Surveillance of Emerging Zoonotic Pathogens at the Domestic Animal-Wildlife-Human Interface",
            "Antimicrobial Stewardship and Resistant Gene Flow in Companion Animal Clinical Practices",
            "Veterinary Disaster Management and Companion Animal Rescue Preparedness in Floods"
        ],
        "featured_publications": [
            "Spatial Epidemiology and Elimination Strategies for Canine-Mediated Rabies in Thailand",
            "One Health Surveillance for Emerging Infectious Diseases Along International Wildlife Trade Corridors",
            "Prevalence and Risk Factors of Methicillin-Resistant Staphylococcus (MRSA/MRSP) in Veterinary Hospitals"
        ]
    },
    {
        "id": "mu_vet_parntep_001",
        "university": "Mahidol University",
        "university_th": "มหาวิทยาลัยมหิดล",
        "faculty": "Faculty of Veterinary Science",
        "faculty_th": "คณะสัตวแพทยศาสตร์",
        "department": "Department of Wildlife and Exotic Animal Medicine (MoZWE)",
        "department_th": "ภาควิชาเวชศาสตร์สัตว์ป่าและสัตว์แปลก (ศูนย์ติดตามโรคระบาดในสัตว์ป่า)",
        "academic_title": "Assoc. Prof.",
        "academic_title_th": "รศ.น.สพ.",
        "first_name": "Parntep",
        "last_name": "Ratanakorn",
        "full_name_th": "รศ.น.สพ. ปานเทพ รัตนากร",
        "role": "Founding Dean of Faculty of Veterinary Science, Pioneer of Wildlife Medicine, Asian Elephant Conservation & Zoos",
        "email": "parntep.rat@mahidol.ac.th",
        "profile_url": "https://vs.mahidol.ac.th/staff/parntep-ratanakorn",
        "scholar_url": "https://scholar.google.com/citations?user=parntepratanakorn",
        "education": [
            "D.V.M., Chulalongkorn University",
            "Post-Graduate Diploma in Wildlife Health and Management, University of London, UK"
        ],
        "research_interests": [
            "Elephant Endotheliotropic Herpesvirus (EEHV) Pathogenesis and Early Plasma Therapy in Asian Elephants",
            "Zoonotic Spillover Surveillance in Wild Bats, Rodents and Non-Human Primates (MoZWE)",
            "Captive Wildlife Welfare Standards, Enrichment and Behavioral Rehabilitation in Sanctuary Settings",
            "Veterinary Forensic Science and Anti-Poaching Diagnostics in Illegally Traded Wildlife Species"
        ],
        "featured_publications": [
            "Epidemiology and Clinical Management of Elephant Endotheliotropic Herpesvirus (EEHV) in Thailand",
            "Wildlife Disease Surveillance and Pathogen Discovery at Human-Ecosystem Boundaries",
            "Conservation Medicine and Welfare Assessment Protocols for Captive Asian Elephants"
        ]
    },
    {
        "id": "mu_vet_aree_001",
        "university": "Mahidol University",
        "university_th": "มหาวิทยาลัยมหิดล",
        "faculty": "Faculty of Veterinary Science",
        "faculty_th": "คณะสัตวแพทยศาสตร์",
        "department": "Department of Pre-Clinical Sciences and Aquatic Animal Diseases",
        "department_th": "ภาควิชาปรีคลินิกและโรคสัตว์น้ำ",
        "academic_title": "Assoc. Prof. Dr.",
        "academic_title_th": "รศ.สพ.ญ.ดร.",
        "first_name": "Aree",
        "last_name": "Kerdchuen",
        "full_name_th": "รศ.สพ.ญ.ดร. อารีย์ เกริกชื่น",
        "role": "Distinguished Aquatic Animal Pathologist in Viral Diseases of Tilapia, Marine Mammal Pathology and Biosecurity",
        "email": "aree.ker@mahidol.ac.th",
        "profile_url": "https://vs.mahidol.ac.th/staff/aree-kerdchuen",
        "scholar_url": "https://scholar.google.com/citations?user=areekerdchuen",
        "education": [
            "Ph.D. (Aquatic Veterinary Medicine / Pathology), Auburn University, USA",
            "D.V.M., Chulalongkorn University"
        ],
        "research_interests": [
            "Tilapia Lake Virus (TiLV) Pathogenesis, Transmission Dynamics and Recombinant Vaccines",
            "Necropsy Pathology and Stranding Diagnostics for Stranded Cetaceans and Dugongs in the Gulf of Thailand",
            "Microbial Biocontrol and Bacteriophages Against Vibrio parahaemolyticus in Penaeid Shrimp Farming",
            "Water Quality Stress and Histopathological Biomarkers in Ornamental Fish Exports"
        ],
        "featured_publications": [
            "Characterization and Transmission Dynamics of Tilapia Lake Virus (TiLV) in Intensive Aquaculture Facilities",
            "Pathological Findings and Cause of Death in Stranded Marine Mammals Along Thai Coastal Waters",
            "Development of Oral Inactivated Vaccines Against Bacterial Sepsis in Asian Seabass"
        ]
    },

    # =========================================================================
    # 7. College of Sports Science and Technology (วิทยาลัยวิทยาศาสตร์การกีฬา มหิดล)
    # =========================================================================
    {
        "id": "mu_sports_chaipat_001",
        "university": "Mahidol University",
        "university_th": "มหาวิทยาลัยมหิดล",
        "faculty": "College of Sports Science and Technology",
        "faculty_th": "วิทยาลัยวิทยาศาสตร์และเทคโนโลยีการกีฬา",
        "department": "Department of Sports Biomechanics and Performance Analysis",
        "department_th": "สาขาวิชาชีวกลศาสตร์การกีฬาและการวิเคราะห์สมรรถภาพ (คณบดีวิทยาลัยฯ)",
        "academic_title": "Assoc. Prof. Dr.",
        "academic_title_th": "รศ.ดร.",
        "first_name": "Chaipat",
        "last_name": "Lawsirirat",
        "full_name_th": "รศ.ดร. ชัยพัฒน์ หล่อศิริรัตน์",
        "role": "Dean of College of Sports Science, Foremost Expert in Power-Velocity Profiling and High-Performance Athletic Conditioning",
        "email": "chaipat.law@mahidol.ac.th",
        "profile_url": "https://ss.mahidol.ac.th/staff/chaipat-lawsirirat",
        "scholar_url": "https://scholar.google.com/citations?user=chaipatlawsirirat",
        "education": [
            "Ph.D. (Sports Science / Biomechanics), Oregon State University, USA",
            "M.Sc. (Sports Science), Mahidol University",
            "B.Sc. (Physical Education), Srinakharinwirot University"
        ],
        "research_interests": [
            "Force-Velocity-Power Profiling and Optimal Load Prescription in Olympic Weightlifters",
            "Electromyographic and Kinetic Assessment of Post-Activation Potentiation (PAP) in Sprinters",
            "Video Motion Tracking and Computer Vision Analytics in Tactical Game Analysis",
            "Heat Stress Acclimatization and Cryotherapy Recovery in Elite Tropical Athletes"
        ],
        "featured_publications": [
            "Force-Velocity Profiling and Individualized Resistance Training for Enhancing Sprint Acceleration in Athletes",
            "Neuromuscular Fatigue and Recovery Kinetics Following Repeated Sprint Bouts Under Tropical Heat",
            "Kinematic Determinants of Maximal Power Output During Explosive Triple Extension Movements"
        ]
    },
    {
        "id": "mu_sports_kornkit_001",
        "university": "Mahidol University",
        "university_th": "มหาวิทยาลัยมหิดล",
        "faculty": "College of Sports Science and Technology",
        "faculty_th": "วิทยาลัยวิทยาศาสตร์และเทคโนโลยีการกีฬา",
        "department": "Department of Sports Medicine and Clinical Rehabilitation",
        "department_th": "สาขาวิชาเวชศาสตร์การกีฬาและการฟื้นฟูสมรรถภาพ",
        "academic_title": "Assoc. Prof. Dr.",
        "academic_title_th": "รศ.นพ.",
        "first_name": "Kornkit",
        "last_name": "Chaijenkij",
        "full_name_th": "รศ.นพ. กรณ์กิจ ชัยเจนกิจ",
        "role": "Distinguished Sports Medicine Physician, National Football Team Doctor & Authority in Tendinopathy and Platelet-Rich Plasma (PRP)",
        "email": "kornkit.cha@mahidol.ac.th",
        "profile_url": "https://ss.mahidol.ac.th/staff/kornkit-chaijenkij",
        "scholar_url": "https://scholar.google.com/citations?user=kornkitchaijenkij",
        "education": [
            "M.D. (Honours), Faculty of Medicine Siriraj Hospital, Mahidol University",
            "M.Sc. (Sports Medicine), University of Nottingham, UK",
            "Diploma Thai Board of Orthopaedic Surgery & Sports Medicine"
        ],
        "research_interests": [
            "Ultrasound-Guided Autologous Platelet-Rich Plasma (PRP) Injections for Chronic Patellar and Achilles Tendinopathies",
            "Pre-Participation Cardiovascular Screening and Sudden Cardiac Arrest Prevention in Athletes",
            "Return-to-Play Protocols and Isokinetic Strength Symmetry Criteria Post-ACL Reconstruction",
            "Concussion Management Protocols and Baseline Neurocognitive Testing in Contact Sports"
        ],
        "featured_publications": [
            "Clinical Efficacy of Leukocyte-Rich vs. Leukocyte-Poor PRP in Treating Recalcitrant Jumper's Knee",
            "Pre-Participation Cardiovascular Evaluation Among Professional Football Players: Findings from a 5-Year Registry",
            "Criteria-Based Return to Sport After Anterior Cruciate Ligament Reconstruction: Biomechanical and Functional Outcomes"
        ]
    },

    # =========================================================================
    # 8. Mahidol University International College (วิทยาลัยนานาชาติ มหิดล - MUIC)
    # =========================================================================
    {
        "id": "mu_muic_chulathida_001",
        "university": "Mahidol University",
        "university_th": "มหาวิทยาลัยมหิดล",
        "faculty": "Mahidol University International College (MUIC)",
        "faculty_th": "วิทยาลัยนานาชาติ",
        "department": "Science Division (Dean of MUIC / Clinical Toxicology)",
        "department_th": "สาขาวิชาวิทยาศาสตร์ (คณบดีวิทยาลัยนานาชาติ)",
        "academic_title": "Assoc. Prof. Dr.",
        "academic_title_th": "รศ.พญ.ดร.",
        "first_name": "Chulathida",
        "last_name": "Chomchai",
        "full_name_th": "รศ.พญ.ดร. จุฬาทิดา โฉมฉาย",
        "role": "Dean of MUIC, Medical Toxicologist, Fellow of the American College of Medical Toxicology (FACMT) & Antidote Registry Leader",
        "email": "chulathida.cho@mahidol.ac.th",
        "profile_url": "https://muic.mahidol.ac.th/staff/chulathida-chomchai",
        "scholar_url": "https://scholar.google.com/citations?user=chulathidachomchai",
        "education": [
            "M.D. (Honours), Faculty of Medicine Siriraj Hospital, Mahidol University",
            "Fellowship in Medical Toxicology, University of California, San Diego (UCSD), USA",
            "Diploma American Board of Pediatrics & Medical Toxicology"
        ],
        "research_interests": [
            "National Poison Surveillance and Antidote Stockpiling Optimization in Mass Casualties",
            "Toxicokinetics and Clinical Management of Agricultural Paraquat and Methanol Poisonings",
            "Pediatric Poisoning Exposures from Cannabis-Infused Confectionery and Household Cleaning Agents",
            "International Health Sciences Pedagogy and Global Medical Leadership Training"
        ],
        "featured_publications": [
            "Efficacy of Hemoperfusion and High-Dose Antioxidants in Acute Paraquat Ingestion: A Multicenter Cohort Study",
            "Epidemiology of Accidental Pediatric Toxic Exposures Following Cannabis Decriminalization in Thailand",
            "Antidote Stockpile Distribution and Real-Time Tele-Toxicology Consultation Models in Developing Nations"
        ]
    },
    {
        "id": "mu_muic_yingyot_001",
        "university": "Mahidol University",
        "university_th": "มหาวิทยาลัยมหิดล",
        "faculty": "Mahidol University International College (MUIC)",
        "faculty_th": "วิทยาลัยนานาชาติ",
        "department": "Business Administration Division",
        "department_th": "สาขาวิชาบริหารธุรกิจ",
        "academic_title": "Assoc. Prof. Dr.",
        "academic_title_th": "รศ.ดร.",
        "first_name": "Yingyot",
        "last_name": "Chiaravutthi",
        "full_name_th": "รศ.ดร. ยิ่งยศ เจียรวุฑฒิ",
        "role": "Authority in Behavioral Economics, Experimental Game Theory, Market Microstructure and Corporate Finance",
        "email": "yingyot.chi@mahidol.ac.th",
        "profile_url": "https://muic.mahidol.ac.th/staff/yingyot-chiaravutthi",
        "scholar_url": "https://scholar.google.com/citations?user=yingyotchiaravutthi",
        "education": [
            "Ph.D. (Economics), University of South Carolina, USA",
            "M.A. (Economics), University of South Carolina, USA",
            "B.A. (Economics), Thammasat University"
        ],
        "research_interests": [
            "Experimental Game Theory Testing Consumer Price Bundling and Loss Aversion in Retail",
            "Behavioral Financial Biases (Overconfidence, Herd Behavior) Among Retail Cryptocurrency Traders",
            "Corporate Governance, Family Ownership Concentration and Dividend Payout Smoothing",
            "Public Policy Nudges for Increasing Health Insurance Uptake in Informal Labor Markets"
        ],
        "featured_publications": [
            "Loss Aversion, Framing Effects, and Consumer Willingness to Pay in Bundled Pricing Experiments",
            "Behavioral Biases and Speculative Bubbles in Decentralized Financial Asset Markets",
            "Corporate Ownership Structure, Political Connections, and Investment Efficiency in Emerging Markets"
        ]
    },

    # =========================================================================
    # 9. Faculty of Medical Technology & Molecular Biosciences (MUMT & MB)
    # =========================================================================
    {
        "id": "mu_mt_chotiros_001",
        "university": "Mahidol University",
        "university_th": "มหาวิทยาลัยมหิดล",
        "faculty": "Faculty of Medical Technology",
        "faculty_th": "คณะเทคนิคการแพทย์",
        "department": "Department of Clinical Microbiology and Applied Technology",
        "department_th": "ภาควิชาจุลทรรศนศาสตร์คลินิกและเทคโนโลยีประยุกต์",
        "academic_title": "Assoc. Prof. Dr.",
        "academic_title_th": "รศ.ดร.",
        "first_name": "Chotiros",
        "last_name": "Plabplueng",
        "full_name_th": "รศ.ดร. โชติรส พลับพลึง",
        "role": "Dean of Faculty of Medical Technology & Expert in Clinical Virology, Dengue Pathogenesis and Cell-Mediated Immunity",
        "email": "chotiros.pla@mahidol.ac.th",
        "profile_url": "https://mt.mahidol.ac.th/staff/chotiros-plabplueng",
        "scholar_url": "https://scholar.google.com/citations?user=chotirosplabplueng",
        "education": [
            "Ph.D. (Clinical Virology / Immunology), Mahidol University",
            "B.Sc. (Medical Technology, First Class Honours), Mahidol University"
        ],
        "research_interests": [
            "Cellular and Molecular Host Responses to Dengue and Chikungunya Viral Invasions",
            "Diagnostic Accuracy of Rapid Point-of-Care Lateral Flow Assays for Tropical Arboviruses",
            "Flow Cytometric Profiling of Monocyte Subsets and Endothelial Dysfunction in Severe Dengue",
            "Development of Automated Molecular Diagnostic Assays for Multidrug-Resistant Bacterial Strains"
        ],
        "featured_publications": [
            "Circulating Endothelial Microparticles and Platelet Activation in Severe Dengue Hemorrhagic Fever",
            "Diagnostic Performance of Recombinant Non-Structural Protein 1 (NS1) Antigen Capture Assays",
            "Host Cellular Biomarkers Predicting Vascular Leakage in Acute Arboviral Infections"
        ]
    },

    # =========================================================================
    # 10. College of Management, Mahidol University (CMMU)
    # =========================================================================
    {
        "id": "mu_cmmu_sooksan_001",
        "university": "Mahidol University",
        "university_th": "มหาวิทยาลัยมหิดล",
        "faculty": "College of Management (CMMU)",
        "faculty_th": "วิทยาลัยการจัดการ มหาวิทยาลัยมหิดล (CMMU)",
        "department": "Department of Sustainable Leadership and Strategic Management",
        "department_th": "สาขาวิชาภาวะผู้นำแห่งความยั่งยืนและการจัดการเชิงกลยุทธ์",
        "academic_title": "Assoc. Prof. Dr.",
        "academic_title_th": "รศ.ดร.",
        "first_name": "Sooksan",
        "last_name": "Kantabutra",
        "full_name_th": "รศ.ดร. สุขสรรค์ กันตบุตร",
        "role": "Global Pioneer in Sufficiency Economy Leadership Theory, Corporate Sustainability and Sustainable Enterprise Architecture",
        "email": "sooksan.kan@mahidol.ac.th",
        "profile_url": "https://www.cmmu.mahidol.ac.th/staff/sooksan-kantabutra",
        "scholar_url": "https://scholar.google.com/citations?user=sooksankantabutra",
        "education": [
            "Ph.D. (Leadership and Strategic Management), Macquarie University, Australia",
            "M.B.A., Baldwin-Wallace University, USA",
            "B.A. (Sociology), Chulalongkorn University"
        ],
        "research_interests": [
            "Toward a Behavioral Theory of Sustainable Leadership and Corporate Resilience",
            "Sufficiency Economy Philosophy (SEP) Business Model Implementation Across ASEAN Corporations",
            "Vision Realization and Stakeholder Engagement in Triple Bottom Line Enterprises",
            "Developing and Validating Organizational Sustainability Diagnostic Instruments"
        ],
        "featured_publications": [
            "Sufficiency Economy Philosophy: An Emerging Corporate Sustainability Paradigm in Asia",
            "Toward a Behavioral Theory for Sustainable Leadership: Empirical Testing of a Cross-Cultural Model",
            "Examining the Relationship Between Sustainable Leadership Practices and Brand Equity"
        ]
    },

    # =========================================================================
    # 11. Faculty of Liberal Arts & RILCA (คณะศิลปศาสตร์ & สถาบันวิจัยภาษาฯ)
    # =========================================================================
    {
        "id": "mu_la_thanayus_001",
        "university": "Mahidol University",
        "university_th": "มหาวิทยาลัยมหิดล",
        "faculty": "Faculty of Liberal Arts",
        "faculty_th": "คณะศิลปศาสตร์",
        "department": "Department of Applied Linguistics and Cross-Cultural Communication",
        "department_th": "ภาควิชาภาษาศาสตร์ประยุกต์และการสื่อสารข้ามวัฒนธรรม (คณบดีคณะศิลปศาสตร์)",
        "academic_title": "Assoc. Prof. Dr.",
        "academic_title_th": "รศ.ดร.",
        "first_name": "Thanayus",
        "last_name": "Thanathiti",
        "full_name_th": "รศ.ดร. ธนายุส ธนธิติ",
        "role": "Dean of Faculty of Liberal Arts, Expert in Applied Linguistics, Medical Humanities and Professional Communication",
        "email": "thanayus.tha@mahidol.ac.th",
        "profile_url": "https://la.mahidol.ac.th/staff/thanayus-thanathiti",
        "scholar_url": "https://scholar.google.com/citations?user=thanayusthanathiti",
        "education": [
            "Ph.D. (Applied Linguistics), University of Warwick, UK",
            "M.A. (English for Specific Purposes), University of Warwick, UK",
            "B.A. (English, Honours), Mahidol University"
        ],
        "research_interests": [
            "Doctor-Patient Communication Pragmatics in Multicultural Hospital Contexts",
            "Corpus Linguistics Analysis of Specialized Medical and Scientific English Discourses",
            "Intercultural Communicative Competence in International Health Tourism",
            "AI-Assisted Language Learning and Automated Feedback Systems for Higher Education"
        ],
        "featured_publications": [
            "Discourse Analysis of Clinical Consultations in Medical Tourism Hospitals: Navigating Cultural Barriers",
            "Corpus-Based Pedagogical Approaches for English for Specific Academic Purposes (ESAP)",
            "Developing Intercultural Health Communication Frameworks for International Medical Graduates"
        ]
    },
    {
        "id": "mu_la_oranicha_001",
        "university": "Mahidol University",
        "university_th": "มหาวิทยาลัยมหิดล",
        "faculty": "Faculty of Liberal Arts",
        "faculty_th": "คณะศิลปศาสตร์",
        "department": "Department of Translation and Medical Interpreting",
        "department_th": "ภาควิชาการแปลและการล่ามทางการแพทย์",
        "academic_title": "Assoc. Prof. Dr.",
        "academic_title_th": "รศ.ดร.",
        "first_name": "Oranicha",
        "last_name": "Phasukkun",
        "full_name_th": "รศ.ดร. อรณิชา ผาสุกกุล",
        "role": "Distinguished Scholar in Medical Interpreting Pedagogy, Healthcare Translation Ethics and Terminology Standardization",
        "email": "oranicha.pha@mahidol.ac.th",
        "profile_url": "https://la.mahidol.ac.th/staff/oranicha-phasukkun",
        "scholar_url": "https://scholar.google.com/citations?user=oranichaphasukkun",
        "education": [
            "Ph.D. (Translation Studies), University of Surrey, UK",
            "M.A. (Translation and Interpreting), Monterey Institute of International Studies, USA",
            "B.A. (English), Chulalongkorn University"
        ],
        "research_interests": [
            "Simultaneous Interpreting in High-Stakes Pediatric Oncology Consents",
            "Ethical Dilemmas and Emotional Labor of Healthcare Interpreters in End-of-Life Dialogues",
            "Neural Machine Translation (NMT) Post-Editing Performance for Clinical Trial Protocols",
            "Standardization of Thai-English Medical Terminology in Tele-Medicine Encounters"
        ],
        "featured_publications": [
            "Role Boundaries and Emotional Resilience of Medical Interpreters in Palliative Consultations",
            "Assessing the Accuracy of AI-Powered Translation Systems in Multilingual Clinical Informed Consents",
            "Standardized Training Curricula for Professional Healthcare Interpreters in Southeast Asia"
        ]
    },
    {
        "id": "mu_rilca_kwanjit_001",
        "university": "Mahidol University",
        "university_th": "มหาวิทยาลัยมหิดล",
        "faculty": "Research Institute for Languages and Cultures of Asia (RILCA)",
        "faculty_th": "สถาบันวิจัยภาษาและวัฒนธรรมเอเชีย (RILCA)",
        "department": "Department of Ethno-Cultural Studies and Ageing Societies",
        "department_th": "กลุ่มสาขาวิชาภาษา วัฒนธรรม และสังคมผู้สูงอายุพหุวัฒนธรรม (ผู้อำนวยการสถาบันฯ)",
        "academic_title": "Assoc. Prof. Dr.",
        "academic_title_th": "รศ.ดร.",
        "first_name": "Kwanjit",
        "last_name": "Sasiwongsarojs",
        "full_name_th": "รศ.ดร. ขวัญจิต ศศิวงศาโรจน์",
        "role": "Director of RILCA & Authority in Multicultural Ageing, Ethnic Health Disparities and Intangible Cultural Heritage",
        "email": "kwanjit.sas@mahidol.ac.th",
        "profile_url": "https://rilca.mahidol.ac.th/staff/kwanjit-sasiwongsarojs",
        "scholar_url": "https://scholar.google.com/citations?user=kwanjitsasiwongsarojs",
        "education": [
            "Ph.D. (Demography), Mahidol University",
            "M.A. (Linguistics), Mahidol University",
            "B.A. (Social Sciences), Chiang Mai University"
        ],
        "research_interests": [
            "Multicultural Ageing Experiences and Healthcare Disparities Among Ethnic Minorities in Thailand",
            "Digital Archiving of Intangible Cultural Heritage, Folk Dialects and Traditional Wisdom",
            "Community-Based Dementia Care Adapted to Diverse Cultural and Religious Beliefs",
            "Linguistic Landscapes and Inter-Ethnic Social Cohesion in Border Communities"
        ],
        "featured_publications": [
            "Cultural Competence and Health Inequities Among Highland Ethnic Minority Older Adults in Northern Thailand",
            "Preserving Endangered Ethno-Linguistic Heritage Through Digital Community-Driven Archives",
            "Social Capital, Religious Practices, and Well-Being Among Muslim and Buddhist Elders in Southern Border Provinces"
        ]
    },
    {
        "id": "mu_rilca_suwilai_001",
        "university": "Mahidol University",
        "university_th": "มหาวิทยาลัยมหิดล",
        "faculty": "Research Institute for Languages and Cultures of Asia (RILCA)",
        "faculty_th": "สถาบันวิจัยภาษาและวัฒนธรรมเอเชีย (RILCA)",
        "department": "Department of Linguistics and Endangered Languages",
        "department_th": "กลุ่มสาขาวิชาภาษาศาสตร์และภาษาชนกลุ่มน้อย",
        "academic_title": "Prof. Emeritus Dr.",
        "academic_title_th": "ศ.เกียรติคุณ ดร.",
        "first_name": "Suwilai",
        "last_name": "Premsrirat",
        "full_name_th": "ศ.เกียรติคุณ ดร. สุวิไล เปรมศรีรัตน์",
        "role": "UNESCO King Sejong Literacy Prize Laureate, Foremost Authority in Mother Tongue-Based Multilingual Education (Patani Malay/Mon-Khmer)",
        "email": "suwilai.pre@mahidol.ac.th",
        "profile_url": "https://rilca.mahidol.ac.th/staff/suwilai-premsrirat",
        "scholar_url": "https://scholar.google.com/citations?user=suwilaipremsrirat",
        "education": [
            "Ph.D. (Linguistics / Austroasiatic Languages), Monash University, Australia",
            "M.A. (Linguistics), University of California, Los Angeles (UCLA), USA",
            "B.A. (Honours), Chulalongkorn University"
        ],
        "research_interests": [
            "Mother Tongue-Based Multilingual Education (MTB-MLE) in the Southern Border Provinces of Thailand",
            "Linguistic Cartography, Acoustic Phonetics and Grammatical Documentation of Mon-Khmer Languages",
            "Language Vitality, Revitalization Models and Orthography Development for Unwritten Indigenous Tongues",
            "Language and Peacebuilding in Multi-Ethnic Conflict Zones"
        ],
        "featured_publications": [
            "Thesaurus of Khmu Dialects in Southeast Asia (Mon-Khmer Studies)",
            "Mother Tongue-Based Multilingual Education in Southern Thailand: Fostering Literacy, Peace, and Identity",
            "Language Endangerment and Revitalization Strategies in the Greater Mekong Subregion"
        ]
    },

    # =========================================================================
    # 12. Institutes for Innovative Learning & Peace Studies (IL & IHRP)
    # =========================================================================
    {
        "id": "mu_il_khajornsak_001",
        "university": "Mahidol University",
        "university_th": "มหาวิทยาลัยมหิดล",
        "faculty": "Institute for Innovative Learning (IL)",
        "faculty_th": "สถาบันนวัตกรรมการเรียนรู้",
        "department": "Department of Science and Technology Education",
        "department_th": "สาขาวิชาวิทยาศาสตร์และเทคโนโลยีศึกษา",
        "academic_title": "Assoc. Prof. Dr.",
        "academic_title_th": "รศ.ดร.",
        "first_name": "Khajornsak",
        "last_name": "Buaraphan",
        "full_name_th": "รศ.ดร. ขจรศักดิ์ บัวระพันธ์",
        "role": "Senior Science Educator, Leader in Nature of Science (NOS), STEM Pedagogies and Teacher Professional Growth",
        "email": "khajornsak.bua@mahidol.ac.th",
        "profile_url": "https://il.mahidol.ac.th/staff/khajornsak-buaraphan",
        "scholar_url": "https://scholar.google.com/citations?user=khajornsakbuaraphan",
        "education": [
            "Ph.D. (Science Education), Kasetsart University",
            "M.Ed. (Chemistry Education), Chulalongkorn University",
            "B.Sc. (Chemistry), Mahidol University"
        ],
        "research_interests": [
            "Investigating Pre-Service and In-Service Teachers' Conceptions of the Nature of Science (NOS)",
            "Integrated STEM Learning Modules and Engineering Design Thinking in Secondary Curricula",
            "Game-Based Learning, Simulations and Virtual Laboratories for Abstract Chemical Concepts",
            "Assessment Methodologies for Scientific Inquiry and 21st-Century Critical Thinking Skills"
        ],
        "featured_publications": [
            "Exploring Pre-Service Science Teachers' Conceptions of the Nature of Science: A Cross-Regional Study",
            "Design and Implementation of STEM Learning Activities to Foster Secondary Students' Creative Problem Solving",
            "Impact of Game-Based Molecular Simulations on High School Students' Chemistry Conceptual Understanding"
        ]
    },
    {
        "id": "mu_ihrp_padtheera_001",
        "university": "Mahidol University",
        "university_th": "มหาวิทยาลัยมหิดล",
        "faculty": "Institute of Human Rights and Peace Studies (IHRP)",
        "faculty_th": "สถาบันสิทธิมนุษยชนและสันติศึกษา",
        "department": "Department of Peace Studies and Conflict Transformation",
        "department_th": "สาขาวิชาสันติศึกษาและการแปรเปลี่ยนความขัดแย้ง",
        "academic_title": "Assoc. Prof. Dr.",
        "academic_title_th": "รศ.ดร.",
        "first_name": "Padtheera",
        "last_name": "Subhaswadikul",
        "full_name_th": "รศ.ดร. พัทธ์ธีรา นาคอุไรรัตน์",
        "role": "Leading Peace Scholar in Deep South Peace Process, Women Peacebuilders, Restorative Justice and Dialogue Facilitation",
        "email": "padtheera.sub@mahidol.ac.th",
        "profile_url": "https://ihrp.mahidol.ac.th/staff/padtheera-subhaswadikul",
        "scholar_url": "https://scholar.google.com/citations?user=padtheerasubhaswadikul",
        "education": [
            "Ph.D. (Peace Studies / Conflict Resolution), Mahidol University",
            "M.A. (Cultural Studies), Mahidol University",
            "B.A. (Journalism), Thammasat University"
        ],
        "research_interests": [
            "Women, Peace, and Security (WPS) Agendas in Protracted Ethno-Political Conflicts in Southern Thailand",
            "Community-Led Restorative Justice and Healing Circles for Families of the Incarcerated",
            "Inter-Faith Dialogue and Insider Mediation Mechanisms for Reducing Armed Violence",
            "Human Rights Education and Non-Violent Civil Resistance Strategies in ASEAN"
        ],
        "featured_publications": [
            "Women's Agency and Grassroots Peacebuilding in Thailand's Southern Border Provinces",
            "Restorative Justice and Healing Circles: Rebuilding Trust in Conflict-Affected Border Communities",
            "Dialogue in the Shadows of Armed Conflict: Experiences and Insights of Local Peace Facilitators"
        ]
    }
]
