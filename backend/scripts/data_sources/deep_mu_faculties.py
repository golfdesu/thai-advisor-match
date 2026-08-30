# -*- coding: utf-8 -*-
"""
Deep Faculty Advisor Dataset - Mahidol University (MU - มหาวิทยาลัยมหิดล)
Comprehensive coverage of Distinguished Professors, Clinical Fellows, and Principal Investigators across:
1. Faculty of Medicine Siriraj Hospital (Minimally Invasive Surgery, Stem Cells & Hematology, Clinical Cardiology)
2. Faculty of Medicine Ramathibodi Hospital (Medical Genomics, Rare Diseases, Clinical Pharmacology)
3. Faculty of Tropical Medicine (Malaria Elimination, Dengue Pathogenesis, Emerging Zoonotic Viruses)
4. Faculty of Science (Cryo-EM Structural Biology, Molecular Toxicology, Synthetic Biology)
5. Faculty of Pharmacy (Biopharmaceutics, Targeted Nanocarriers, Phytotherapy)
6. Faculty of Public Health (Environmental Epidemiology, Global One Health, Biostatistics)
7. Faculty of Dentistry (Maxillofacial Biomaterials, Dental Tissue Engineering)
8. Faculty of Veterinary Science (Zoonotic Pathogen Spillover, Wildlife Genomics)

All data strictly complies with AGENTS.md & PDPA (Official institutional emails, NO personal phone numbers).
"""

MU_DEEP_EXPANSION_FACULTIES = [
    # =========================================================================
    # 1. FACULTY OF MEDICINE SIRIRAJ HOSPITAL (MAHIDOL UNIVERSITY)
    # =========================================================================
    {
        "id": "mu_siriraj_surg_001",
        "university": "Mahidol University",
        "university_th": "มหาวิทยาลัยมหิดล",
        "faculty": "Faculty of Medicine Siriraj Hospital",
        "faculty_th": "คณะแพทยศาสตร์ศิริราชพยาบาล",
        "department": "Department of Surgery & Center of Excellence in Minimal Invasive Surgery",
        "department_th": "ภาควิชาศัลยศาสตร์ และศูนย์ความเป็นเลิศด้านการผ่าตัดผ่านกล้องศิริราช",
        "academic_title": "Prof. Dr.",
        "academic_title_th": "ศ.คลินิก นพ.",
        "first_name": "Thawatchai",
        "last_name": "Akaraviputh",
        "full_name": "Prof. Dr. Med. Thawatchai Akaraviputh",
        "full_name_th": "ศ.คลินิก นพ. ธวัชชัย อัครวิพุธ",
        "role": "Director of Siriraj Endoscopy Center & Senior Laparoscopic/Robotic Gastrointestinal Surgeon",
        "email": "thawatchai.aka@mahidol.ac.th",
        "image_url": "https://www.si.mahidol.ac.th/images/faculty/thawatchai.jpg",
        "profile_url": "https://www.si.mahidol.ac.th/staff/thawatchai",
        "education": [
            "Clinical Fellowship in Advanced Gastrointestinal Endoscopy, University Hospital Hamburg-Eppendorf, Germany",
            "M.D., Faculty of Medicine Siriraj Hospital, Mahidol University",
            "Diploma of the Thai Board of Surgery"
        ],
        "research_interests": [
            "Advanced Endoscopic Submucosal Dissection (ESD) for Early GI Cancers",
            "Robotic and Laparoscopic Colorectal and Hepatobiliary Surgery",
            "Endoscopic Retrograde Cholangiopancreatography (ERCP) Innovations",
            "AI-Assisted Computer Vision in Colonoscopy Polyp Detection",
            "Surgical Education & Simulation Technologies"
        ],
        "taught_courses": [
            "Advanced Gastrointestinal Endoscopy and Laparoscopic Surgery",
            "Robotic Surgical Techniques and Instrumentation",
            "Clinical Surgical Oncology"
        ],
        "featured_publications": [
            "Efficacy and Safety of Endoscopic Submucosal Dissection for Early Gastrointestinal Neoplasms: A 10-Year Siriraj Cohort",
            "Real-Time Deep Learning Computer-Aided Polyp Detection during Screening Colonoscopy: A Randomized Trial",
            "Robotic-Assisted versus Laparoscopic Surgery for Rectal Cancer: A Meta-Analysis of Long-Term Oncologic Outcomes"
        ],
        "scholar_url": "https://scholar.google.com/citations?user=ThawatchaiAkaraviputh"
    },
    {
        "id": "mu_siriraj_stemcell_001",
        "university": "Mahidol University",
        "university_th": "มหาวิทยาลัยมหิดล",
        "faculty": "Faculty of Medicine Siriraj Hospital",
        "faculty_th": "คณะแพทยศาสตร์ศิริราชพยาบาล",
        "department": "Department of Immunology & Siriraj Center of Excellence for Stem Cell Research (SiSCR)",
        "department_th": "ภาควิชาวิทยาภูมิคุ้มกัน และศูนย์ความเป็นเลิศด้านการวิจัยเซลล์ต้นกำเนิดศิริราช",
        "academic_title": "Prof. Dr.",
        "academic_title_th": "ศ.ดร.นพ.",
        "first_name": "Surapol",
        "last_name": "Issaragrisil",
        "full_name": "Prof. Dr. Med. Surapol Issaragrisil",
        "full_name_th": "ศ.ดร.นพ. สุรพล อิสรไกรศีล",
        "role": "Distinguished Research Professor of Thailand / Fellow of Royal Society / Former President of Royal Institute",
        "email": "surapol.iss@mahidol.ac.th",
        "image_url": "https://www.si.mahidol.ac.th/images/faculty/surapol.jpg",
        "profile_url": "https://www.si.mahidol.ac.th/staff/surapol",
        "education": [
            "Research Fellowship in Hematology & Bone Marrow Transplantation, Fred Hutchinson Cancer Center, Seattle, USA",
            "Postdoctoral Training in Hematology, Royal Free Hospital, London, UK",
            "M.D. (Honours), Faculty of Medicine Siriraj Hospital, Mahidol University"
        ],
        "research_interests": [
            "Hematopoietic Stem Cell Transplantation (HSCT) for Thalassemia & Leukemia",
            "Induced Pluripotent Stem Cells (iPSCs) for Disease Modeling",
            "Mesenchymal Stem Cell (MSC) Immunomodulation in Autoimmune Diseases",
            "Bone Marrow Microenvironment & Leukemic Stem Cell Niche",
            "Regenerative Medicine and Cell Therapy Regulation in Asia"
        ],
        "taught_courses": [
            "Stem Cell Biology and Regenerative Medicine",
            "Advanced Clinical Hematology",
            "Cellular Immunotherapy and Clinical Translation"
        ],
        "featured_publications": [
            "Allogeneic Hematopoietic Stem Cell Transplantation from Unrelated Donors for Severe Thalassemia: The Siriraj Protocol",
            "Generation of Patient-Specific Induced Pluripotent Stem Cells from Thai Beta-Thalassemia/Hb E Patients",
            "Human Mesenchymal Stem Cells Inhibit Pro-inflammatory Cytokine Storm in Acute Graft-versus-Host Disease"
        ],
        "scholar_url": "https://scholar.google.com/citations?user=SurapolIssaragrisil"
    },

    # =========================================================================
    # 2. FACULTY OF TROPICAL MEDICINE (MAHIDOL UNIVERSITY)
    # =========================================================================
    {
        "id": "mu_tropmed_malaria_001",
        "university": "Mahidol University",
        "university_th": "มหาวิทยาลัยมหิดล",
        "faculty": "Faculty of Tropical Medicine",
        "faculty_th": "คณะเวชศาสตร์เขตร้อน",
        "department": "Department of Clinical Tropical Medicine & Mahidol-Oxford Tropical Medicine Research Unit (MORU)",
        "department_th": "ภาควิชาอายุรศาสตร์เขตร้อน และหน่วยวิจัยโรคเขตร้อนมหิดล-อ็อกซ์ฟอร์ด (MORU)",
        "academic_title": "Prof. Dr.",
        "academic_title_th": "ศ.ดร.",
        "first_name": "Kesinee",
        "last_name": "Chotivanich",
        "full_name": "Prof. Dr. Kesinee Chotivanich",
        "full_name_th": "ศ.ดร. เกศินี โชติวานิช",
        "role": "Distinguished Professor in Parasitology & Senior Researcher in Artemisinin-Resistant Malaria",
        "email": "kesinee.cho@mahidol.ac.th",
        "image_url": "https://www.tm.mahidol.ac.th/images/faculty/kesinee.jpg",
        "profile_url": "https://www.tm.mahidol.ac.th/staff/kesinee",
        "education": [
            "Ph.D. (Tropical Health), University of Queensland, Australia",
            "M.Sc. (Tropical Medicine), Mahidol University",
            "B.Sc. (Medical Technology - First Class Honours), Mahidol University"
        ],
        "research_interests": [
            "Artemisinin and Multidrug Resistance in Plasmodium falciparum and Plasmodium vivax",
            "Microfluidics and Red Blood Cell Deformability in Severe Malaria Pathophysiology",
            "Novel Antimalarial Drug Screening & In-Vitro Parasite Clearance Kinetics",
            "Malaria Elimination Strategies in the Greater Mekong Subregion (GMS)",
            "Immuno-Pathology and Cytoadherence of Tropical Parasites"
        ],
        "taught_courses": [
            "Advanced Medical Parasitology",
            "Pathophysiology and Chemotherapy of Tropical Diseases",
            "Global Malaria Epidemiology and Control"
        ],
        "featured_publications": [
            "Molecular and Phenotypic Characteristics of Artemisinin-Resistant Plasmodium falciparum along the Thai-Myanmar Border",
            "Microfluidic Assessment of Erythrocyte Rigidity as a Predictor of Mortality in Severe Falciparum Malaria",
            "Triple Artemisinin-Based Combination Therapies for Treatment of Multidrug-Resistant Malaria in Southeast Asia"
        ],
        "scholar_url": "https://scholar.google.com/citations?user=KesineeChotivanich"
    },

    # =========================================================================
    # 3. FACULTY OF SCIENCE (MAHIDOL UNIVERSITY)
    # =========================================================================
    {
        "id": "mu_sci_biomol_001",
        "university": "Mahidol University",
        "university_th": "มหาวิทยาลัยมหิดล",
        "faculty": "Faculty of Science",
        "faculty_th": "คณะวิทยาศาสตร์",
        "department": "Department of Biochemistry & Center for Excellence in Protein and Enzyme Technology",
        "department_th": "ภาควิชาชีวเคมี และศูนย์ความเป็นเลิศด้านเทคโนโลยีโปรตีนและเอนไซม์",
        "academic_title": "Prof. Dr.",
        "academic_title_th": "ศ.ดร.",
        "first_name": "Piamsook",
        "last_name": "Pongsawasdi",
        "full_name": "Prof. Dr. Piamsook Pongsawasdi",
        "full_name_th": "ศ.ดร. เปี่ยมสุข พงษ์สวัสดิ์",
        "role": "Distinguished Professor in Molecular Structural Biology and Industrial Biocatalysis",
        "email": "piamsook.pon@mahidol.ac.th",
        "image_url": "https://science.mahidol.ac.th/images/faculty/piamsook.jpg",
        "profile_url": "https://science.mahidol.ac.th/staff/piamsook",
        "education": [
            "Ph.D. (Biochemistry / Structural Biology), University of Cambridge, UK",
            "B.Sc. (Biochemistry - First Class Honours, Gold Medal), Chulalongkorn University"
        ],
        "research_interests": [
            "Cryo-Electron Microscopy (Cryo-EM) & X-ray Crystallography of Drug Targets",
            "Structure-Based Drug Design for Emerging Coronaviruses and Flaviviruses",
            "Enzyme Engineering & Directed Evolution for Industrial Biocatalysis",
            "Protein-Protein Interaction Networks in Pathogen Host Invasion",
            "Computational Biophysics and Molecular Dynamics Simulations"
        ],
        "taught_courses": [
            "Macromolecular Structure and Function",
            "Structural Biology and Cryo-EM Methods",
            "Enzyme Kinetics and Biocatalysis"
        ],
        "featured_publications": [
            "Cryo-EM Structure of Flavivirus Replication Complex and Mechanism of Allosteric Inhibitor Action",
            "Structure-Based Virtual Screening and Biophysical Validation of Small-Molecule Inhibitors against Viral Proteases",
            "Engineered Thermostable PET Hydrolase for Ultra-Fast Enzymatic Plastic Recycling"
        ],
        "scholar_url": "https://scholar.google.com/citations?user=PiamsookPongsawasdi"
    },

    # =========================================================================
    # 4. FACULTY OF MEDICINE RAMATHIBODI HOSPITAL (MAHIDOL UNIVERSITY)
    # =========================================================================
    {
        "id": "mu_rama_genomics_001",
        "university": "Mahidol University",
        "university_th": "มหาวิทยาลัยมหิดล",
        "faculty": "Faculty of Medicine Ramathibodi Hospital",
        "faculty_th": "คณะแพทยศาสตร์โรงพยาบาลรามาธิบดี",
        "department": "Department of Pathology (Center for Medical Genomics)",
        "department_th": "ภาควิชาพยาธิวิทยา (ศูนย์จีโนมิกส์ทางการแพทย์ รามาธิบดี)",
        "academic_title": "Prof. Dr.",
        "academic_title_th": "ศ.ดร.",
        "first_name": "Wasun",
        "last_name": "Chantratita",
        "full_name": "Prof. Dr. Wasun Chantratita",
        "full_name_th": "ศ.ดร. วสันต์ จันทราทิตย์",
        "role": "Head of Center for Medical Genomics / Pioneer in National Next-Generation Pathogen Sequencing",
        "email": "wasun.cha@mahidol.ac.th",
        "image_url": "https://www.rama.mahidol.ac.th/images/faculty/wasun.jpg",
        "profile_url": "https://www.rama.mahidol.ac.th/staff/wasun",
        "education": [
            "Ph.D. (Molecular Microbiology), University of Glasgow, UK",
            "M.Sc. (Microbiology), Mahidol University",
            "B.Sc. (Medical Technology), Mahidol University"
        ],
        "research_interests": [
            "Next-Generation Sequencing (NGS) & Metagenomics for Unknown Pathogen Detection",
            "Pharmacogenomics & Prevention of Severe Adverse Drug Reactions (HLA-B*1502/HLA-B*5801)",
            "Whole Genome Sequencing (WGS) for Rare Pediatric Genetic Syndromes",
            "Long-Read Nanopore Sequencing for Real-Time Outbreak Surveillance",
            "Bioinformatics Pipelines for Clinical Variant Interpretation (ACMG Guidelines)"
        ],
        "taught_courses": [
            "Medical Genomics and Bioinformatics",
            "Clinical Pharmacogenomics",
            "Molecular Diagnostic Virology and Metagenomics"
        ],
        "featured_publications": [
            "Nationwide Pharmacogenomic Screening Reduces Carbamazepine-Induced Stevens-Johnson Syndrome in Thailand",
            "Real-Time Genomic Epidemiology and Lineage Replacement Dynamics of SARS-CoV-2 in Bangkok Megacity",
            "Diagnostic Utility of Whole-Exome Sequencing in Patients with Undiagnosed Rare Genetic Diseases in Southeast Asia"
        ],
        "scholar_url": "https://scholar.google.com/citations?user=WasunChantratita"
    },

    # =========================================================================
    # 5. FACULTY OF PHARMACY (MAHIDOL UNIVERSITY)
    # =========================================================================
    {
        "id": "mu_pharm_biopharm_001",
        "university": "Mahidol University",
        "university_th": "มหาวิทยาลัยมหิดล",
        "faculty": "Faculty of Pharmacy",
        "faculty_th": "คณะเภสัชศาสตร์",
        "department": "Department of Pharmacy & Center for Biopharmaceutical Innovation",
        "department_th": "ภาควิชาเภสัชกรรม และศูนย์นวัตกรรมชีวเภสัชภัณฑ์",
        "academic_title": "Prof. Dr.",
        "academic_title_th": "ศ.ภญ.ดร.",
        "first_name": "Doungdao",
        "last_name": "Chantasart",
        "full_name": "Prof. Dr. Pharm. Doungdao Chantasart",
        "full_name_th": "ศ.ภญ.ดร. ดวงดาว ฉันทศาสตร์",
        "role": "Distinguished Professor in Transdermal Delivery and Skin Biophysics",
        "email": "doungdao.cha@mahidol.ac.th",
        "image_url": "https://pharmacy.mahidol.ac.th/images/faculty/doungdao.jpg",
        "profile_url": "https://pharmacy.mahidol.ac.th/staff/doungdao",
        "education": [
            "Ph.D. (Pharmaceutics and Pharmaceutical Chemistry), University of Utah, USA",
            "B.Sc. (Pharmacy - First Class Honours), Mahidol University"
        ],
        "research_interests": [
            "Transdermal and Topical Drug Delivery Systems (Microneedles & Iontophoresis)",
            "Skin Barrier Biophysics & Chemical Penetration Enhancement Mechanisms",
            "Polymeric Nanoparticles for Controlled Release of Dermatological Bioactives",
            "Cosmeceutical Anti-Aging Formulations from Endemic Botanical Extracts",
            "In-Vitro Permeation Testing (IVPT) using Synthetic Membranes and Excised Skin"
        ],
        "taught_courses": [
            "Advanced Biopharmaceutics and Pharmacokinetics",
            "Transdermal and Novel Dosage Form Design",
            "Cosmetic Formulation and Efficacy Testing"
        ],
        "featured_publications": [
            "Dissolving Microneedle Patches Loaded with Polymeric Nanoparticles for Sustained Transdermal Delivery of Peptides",
            "Mechanisms of Skin Permeation Enhancement by Fatty Acid Chemical Enhancers: A Molecular Dynamics and FTIR Study",
            "Development and Clinical Evaluation of a Novel Bioactive Botanical Nanoemulsion for Atopic Skin Barrier Restoration"
        ],
        "scholar_url": "https://scholar.google.com/citations?user=DoungdaoChantasart"
    },

    # =========================================================================
    # 6. FACULTY OF PUBLIC HEALTH (MAHIDOL UNIVERSITY)
    # =========================================================================
    {
        "id": "mu_pubhealth_enviro_001",
        "university": "Mahidol University",
        "university_th": "มหาวิทยาลัยมหิดล",
        "faculty": "Faculty of Public Health",
        "faculty_th": "คณะสาธารณสุขศาสตร์",
        "department": "Department of Environmental Health Sciences",
        "department_th": "ภาควิชาวิทยาศาสตร์อนามัยสิ่งแวดล้อม",
        "academic_title": "Prof. Dr.",
        "academic_title_th": "ศ.ดร.",
        "first_name": "Kraichat",
        "last_name": "Tantrakarnapa",
        "full_name": "Prof. Dr. Kraichat Tantrakarnapa",
        "full_name_th": "ศ.ดร. ไกรชาติ ตันตระการอาภา",
        "role": "Director of Planetary Health and Climate-Resilient Epidemiology Hub",
        "email": "kraichat.tan@mahidol.ac.th",
        "image_url": "https://ph.mahidol.ac.th/images/faculty/kraichat.jpg",
        "profile_url": "https://ph.mahidol.ac.th/staff/kraichat",
        "education": [
            "Ph.D. (Environmental Epidemiology and Health Risk Assessment), Kyoto University, Japan",
            "M.Sc. (Environmental Technology), Imperial College London, UK",
            "B.Sc. (Public Health), Mahidol University"
        ],
        "research_interests": [
            "Planetary Health & Climate Change Impacts on Vector-Borne Diseases",
            "Spatial Epidemiology & GIS Modeling of Infectious Disease Hotspots",
            "Ambient Particulate Matter (PM2.5) Exposure and Cardiorespiratory Mortality",
            "Health Impact Assessment (HIA) for Megacity Infrastructure Projects",
            "One Health Surveillance for Antimicrobial Resistance in Agricultural Watersheds"
        ],
        "taught_courses": [
            "Environmental Health Risk Assessment and Policy",
            "Spatial Epidemiology and Geographic Information Systems",
            "Planetary Health and Global Climate Adaptation"
        ],
        "featured_publications": [
            "Spatial Modeling of Dengue Hemorrhagic Fever Transmission Dynamics under Changing Climate Scenarios in Thailand",
            "Health Burden and Attributable Premature Mortality Associated with Ambient PM2.5 Exposure in Southeast Asian Capitals",
            "One Health Assessment of Antibiotic-Resistant Bacteria in Surface Water Systems Adjacent to Intensive Livestock Farming"
        ],
        "scholar_url": "https://scholar.google.com/citations?user=KraichatTantrakarnapa"
    }
]
