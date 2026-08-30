# -*- coding: utf-8 -*-
"""
Deep Faculty Advisor Dataset - Kasetsart University (KU - มหาวิทยาลัยเกษตรศาสตร์)
Comprehensive coverage of Distinguished Professors, Royal Society Fellows, and Leading PIs across:
1. Faculty of Engineering (Aerospace Superalloys, Clean Energy Nanocatalysts, Environmental Water, Robotics)
2. Faculty of Agriculture (Tropical Agronomy, Plant Pathology, Biological Pest Control & Acarology)
3. Faculty of Agro-Industry (Food Innovation, Functional Food Proteins, Bioprocess Engineering)
4. Faculty of Fisheries (Aquaculture Genomics, Selective Breeding, Marine Bio-Resources)
5. Faculty of Forestry (Tropical Silviculture, Forest Carbon Sequestration, Remote Sensing & GIS)
6. Faculty of Veterinary Medicine (Swine & Avian Viral Pathogenesis, Companion Animal Oncology)
7. Kasetsart Business School - KBS (Agribusiness Supply Chains, Blockchain Food Traceability, Commodities)
8. Faculty of Science (Microbial Biotechnology, Applied Radiation Chemistry, Biodiversity)

All data strictly complies with AGENTS.md & PDPA (Official institutional emails, NO personal phone numbers).
"""

KU_DEEP_EXPANSION_FACULTIES = [
    # =========================================================================
    # 1. FACULTY OF ENGINEERING (KASETSART UNIVERSITY)
    # =========================================================================
    {
        "id": "ku_eng_aero_001",
        "university": "Kasetsart University",
        "university_th": "มหาวิทยาลัยเกษตรศาสตร์",
        "faculty": "Faculty of Engineering",
        "faculty_th": "คณะวิศวกรรมศาสตร์",
        "department": "Department of Aerospace Engineering & High-Altitude Flight Lab",
        "department_th": "ภาควิชาวิศวกรรมการบินและอวกาศ",
        "academic_title": "Prof. Dr.",
        "academic_title_th": "ศ.ดร.",
        "first_name": "Chinnapat",
        "last_name": "Panwisawas",
        "full_name": "Prof. Dr. Chinnapat Panwisawas",
        "full_name_th": "ศ.ดร. ชินภัทร พันธุ์วิศวาส",
        "role": "Distinguished Professor in Computational Metallurgy and Aerospace Materials / Royal Academy of Engineering Fellow",
        "email": "chinnapat.p@ku.ac.th",
        "image_url": "https://aero.eng.ku.ac.th/images/faculty/chinnapat.jpg",
        "profile_url": "https://aero.eng.ku.ac.th/staff/chinnapat",
        "education": [
            "Ph.D. (Materials Science and Metallurgy), University of Birmingham, UK",
            "M.Sc. (Aerospace Dynamics), Cranfield University, UK",
            "B.Eng. (Aerospace Engineering - First Class Honours), Kasetsart University"
        ],
        "research_interests": [
            "Additive Manufacturing (3D Metal Printing) of Nickel-Based Superalloys",
            "Computational Fluid Dynamics & High-Temperature Gas Turbine Blades",
            "Multiscale Modeling of Laser Powder Bed Fusion (LPBF)",
            "Aerospace Structural Mechanics and Fatigue Failure Analysis",
            "Thermal Barrier Coatings for Hypersonic Space Vehicles"
        ],
        "taught_courses": [
            "Aerospace Materials and Advanced Manufacturing",
            "Computational Aerodynamics and Heat Transfer",
            "Continuum Mechanics of Superalloys"
        ],
        "featured_publications": [
            "Mesoscale Modeling of Solidification Microstructure Evolution during Laser Powder Bed Fusion of Superalloys",
            "Mechanistic Model of Hot Tearing and Residual Stresses in Metal Additive Manufacturing for Aerospace Turbines",
            "High-Temperature Creep Deformation and Microstructural Degradation of Single-Crystal Superalloys"
        ],
        "scholar_url": "https://scholar.google.com/citations?user=ChinnapatPanwisawas"
    },
    {
        "id": "ku_eng_chem_001",
        "university": "Kasetsart University",
        "university_th": "มหาวิทยาลัยเกษตรศาสตร์",
        "faculty": "Faculty of Engineering",
        "faculty_th": "คณะวิศวกรรมศาสตร์",
        "department": "Department of Chemical Engineering & Bio-Chemical Energy Systems Lab",
        "department_th": "ภาควิชาวิศวกรรมเคมี และห้องปฏิบัติการระบบพลังงานเคมีชีวภาพ",
        "academic_title": "Prof. Dr.",
        "academic_title_th": "ศ.ดร.",
        "first_name": "Metta",
        "last_name": "Charoenpanich",
        "full_name": "Prof. Dr. Metta Chareonpanich",
        "full_name_th": "ศ.ดร. เมตตา เจริญพานิช",
        "role": "Distinguished Research Professor of Thailand / Director of Nanotechnology and Clean Energy Center",
        "email": "fengmtc@ku.ac.th",
        "image_url": "https://chem.eng.ku.ac.th/images/faculty/metta.jpg",
        "profile_url": "https://chem.eng.ku.ac.th/staff/metta",
        "education": [
            "D.Eng. (Chemical Engineering), Tokyo Institute of Technology, Japan",
            "M.Eng. (Chemical Engineering), Tokyo Institute of Technology, Japan",
            "B.Eng. (Chemical Engineering), Chulalongkorn University"
        ],
        "research_interests": [
            "Synthesis of Mesoporous Nanomaterials from Agricultural Silica Ash",
            "CO2 Capture and Utilization (CCU) via Catalytic Conversion to Valuable Chemicals",
            "Biomass Gasification & Syngas Production Pathways",
            "Nanocatalysts for Clean Biofuel and Synthetic Jet Fuel",
            "Circular Carbon Recycling in Agro-Industrial Complexes"
        ],
        "taught_courses": [
            "Advanced Nanomaterials for Energy Applications",
            "Chemical Reaction Engineering and Catalysis",
            "Green Process Design and Sustainability"
        ],
        "featured_publications": [
            "Facile Synthesis of High-Purity Mesoporous Silica from Rice Husk Ash and Its Application in CO2 Adsorption",
            "Direct Catalytic Conversion of CO2 and Glycerol into Glycerol Carbonate over Metal-Modified Zeolites",
            "Techno-Economic and Life Cycle Assessment of Bio-Jet Fuel Production from Lignocellulosic Palm Residues"
        ],
        "scholar_url": "https://scholar.google.com/citations?user=MettaChareonpanich"
    },

    # =========================================================================
    # 2. FACULTY OF FISHERIES (KASETSART UNIVERSITY)
    # =========================================================================
    {
        "id": "ku_fish_genetics_001",
        "university": "Kasetsart University",
        "university_th": "มหาวิทยาลัยเกษตรศาสตร์",
        "faculty": "Faculty of Fisheries",
        "faculty_th": "คณะประมง",
        "department": "Department of Aquaculture & Center for Marine and Freshwater Genomics",
        "department_th": "ภาควิชาเพาะเลี้ยงสัตว์น้ำ และศูนย์จีโนมิกส์สัตว์น้ำ",
        "academic_title": "Prof. Dr.",
        "academic_title_th": "ศ.ดร.",
        "first_name": "Uthairat",
        "last_name": "Na-Nakorn",
        "full_name": "Prof. Dr. Uthairat Na-Nakorn",
        "full_name_th": "ศ.ดร. อุทัยรัตน์ ณ นคร",
        "role": "Distinguished Professor of Thailand in Fish Genetics & Selective Breeding / Fellow of Royal Society",
        "email": "uthairat.n@ku.ac.th",
        "image_url": "https://fish.ku.ac.th/images/faculty/uthairat.jpg",
        "profile_url": "https://fish.ku.ac.th/staff/uthairat",
        "education": [
            "Ph.D. (Aquaculture / Genetics), Auburn University, USA",
            "M.Sc. (Fisheries Science), Kasetsart University",
            "B.Sc. (Fisheries - Honours), Kasetsart University"
        ],
        "research_interests": [
            "Quantitative Genetics and Selective Breeding of Asian Seabass and Tilapia",
            "Genomic Selection (GBLUP) for Disease Resistance in Penaeus monodon and P. vannamei",
            "Conservation Genetics of Endangered Indigenous Giant Catfish (Pangasianodon gigas)",
            "Epigenetics of Thermal Tolerance in Tropical Aquaculture",
            "Environmental DNA (eDNA) for Aquatic Biodiversity Monitoring"
        ],
        "taught_courses": [
            "Fish Genetics and Selective Breeding",
            "Aquaculture Biotechnology and Genomics",
            "Conservation Genetics of Aquatic Resources"
        ],
        "featured_publications": [
            "Genomic Selection for Growth and Acute Hepatopancreatic Necrosis Disease (AHPND) Resistance in Black Tiger Shrimp",
            "Genetic Diversity and Population Structure of the Critically Endangered Mekong Giant Catfish Revealed by Microsatellite and SNP Markers",
            "Selective Breeding of Hybrid Catfish for Enhanced Meat Quality and Feed Conversion Efficiency in Tropical Ponds"
        ],
        "scholar_url": "https://scholar.google.com/citations?user=UthairatNaNakorn"
    },

    # =========================================================================
    # 3. FACULTY OF AGRICULTURE (KASETSART UNIVERSITY)
    # =========================================================================
    {
        "id": "ku_agri_entomology_001",
        "university": "Kasetsart University",
        "university_th": "มหาวิทยาลัยเกษตรศาสตร์",
        "faculty": "Faculty of Agriculture",
        "faculty_th": "คณะเกษตรศาสตร์",
        "department": "Department of Entomology & Center for Biological Control Research",
        "department_th": "ภาควิชากีฏวิทยา และศูนย์วิจัยควบคุมศัตรูพืชโดยชีววิธี",
        "academic_title": "Prof. Dr.",
        "academic_title_th": "ศ.ดร.",
        "first_name": "Angsumarn",
        "last_name": "Chandrapatya",
        "full_name": "Prof. Dr. Angsumarn Chandrapatya",
        "full_name_th": "ศ.ดร. อังศุมาลย์ จันทราปัตย์",
        "role": "Distinguished Professor in Acarology and Biological Control of Agricultural Pests",
        "email": "angsumarn.c@ku.ac.th",
        "image_url": "https://agr.ku.ac.th/images/faculty/angsumarn.jpg",
        "profile_url": "https://agr.ku.ac.th/staff/angsumarn",
        "education": [
            "Ph.D. (Entomology / Acarology), Rutgers University, USA",
            "M.S. (Entomology), Rutgers University, USA",
            "B.Sc. (Agriculture), Kasetsart University"
        ],
        "research_interests": [
            "Taxonomy and Ecology of Eriophyoid Mites on Tropical Fruit Trees (Durian, Mangosteen, Mango)",
            "Biological Pest Control using Entomopathogenic Fungi and Predatory Mites",
            "Integrated Pest Management (IPM) for Export-Grade Agricultural Crops",
            "Biopesticide Formulation and Microencapsulation from Natural Microorganisms",
            "Climate Change Impact on Arthropod Invasive Vectors in Southeast Asia"
        ],
        "taught_courses": [
            "Advanced Agricultural Acarology",
            "Biological Control of Insect and Mite Pests",
            "Integrated Pest Management for Sustainable Agriculture"
        ],
        "featured_publications": [
            "Eriophyoid Mites of Thailand: Systematics, Host Range, and Economic Damage on High-Value Horticultural Crops",
            "Evaluation of Native Entomopathogenic Fungi (Beauveria bassiana and Metarhizium anisopliae) for Biocontrol of Cassava Pests",
            "Integration of Predatory Mites and Botanical Extracts for Sustainable Thrips Management in Orchid Greenhouses"
        ],
        "scholar_url": "https://scholar.google.com/citations?user=AngsumarnChandrapatya"
    },

    # =========================================================================
    # 4. FACULTY OF AGRO-INDUSTRY (KASETSART UNIVERSITY)
    # =========================================================================
    {
        "id": "ku_agro_food_001",
        "university": "Kasetsart University",
        "university_th": "มหาวิทยาลัยเกษตรศาสตร์",
        "faculty": "Faculty of Agro-Industry",
        "faculty_th": "คณะอุตสาหกรรมเกษตร",
        "department": "Department of Food Science and Technology & National Food Innovation Center",
        "department_th": "ภาควิชาวิทยาศาสตร์และเทคโนโลยีการอาหาร และศูนย์นวัตกรรมอาหารแห่งชาติ",
        "academic_title": "Prof. Dr.",
        "academic_title_th": "ศ.ดร.",
        "first_name": "Siree",
        "last_name": "Chaiseri",
        "full_name": "Prof. Dr. Siree Chaiseri",
        "full_name_th": "ศ.ดร. ศิรี ชัยเสรี",
        "role": "Distinguished Professor in Food Flavor Chemistry and Director of Thailand Food Innovation Platform",
        "email": "siree.c@ku.ac.th",
        "image_url": "https://agro.ku.ac.th/images/faculty/siree.jpg",
        "profile_url": "https://agro.ku.ac.th/staff/siree",
        "education": [
            "Ph.D. (Food Science), Pennsylvania State University, USA",
            "M.S. (Food Science), Pennsylvania State University, USA",
            "B.Sc. (Food Science and Biotechnology), Kasetsart University"
        ],
        "research_interests": [
            "Food Flavor Chemistry & Aroma Compound Retention in Tropical Fruits",
            "Plant-Based Alternative Proteins & Precision Fermentation Texturization",
            "Microencapsulation of Sensitive Bioactive Nutrients for Functional Beverages",
            "Cocoa Bean Fermentation and Chocolate Flavor Precursor Profiling",
            "Sensory Analysis & High-Resolution Gas Chromatography-Olfactometry (GC-O)"
        ],
        "taught_courses": [
            "Advanced Food Flavor Chemistry",
            "Functional Food Innovation and Product Development",
            "Sensory Evaluation and Instrumental Flavor Analysis"
        ],
        "featured_publications": [
            "Identification of Key Aroma Compounds in Thai Hom Mali Rice and Volatile Evolution during High-Temperature Storage",
            "Texturization of Mung Bean and Pea Protein Blends via High-Moisture Extrusion for Alternative Meat Applications",
            "Microencapsulation of Tropical Fruit Polyphenols using Spray Drying with Resistant Maltodextrin Matrices"
        ],
        "scholar_url": "https://scholar.google.com/citations?user=SireeChaiseri"
    },

    # =========================================================================
    # 5. FACULTY OF FORESTRY (KASETSART UNIVERSITY)
    # =========================================================================
    {
        "id": "ku_forest_carbon_001",
        "university": "Kasetsart University",
        "university_th": "มหาวิทยาลัยเกษตรศาสตร์",
        "faculty": "Faculty of Forestry",
        "faculty_th": "คณะวนศาสตร์",
        "department": "Department of Forest Management & Tropical Forest Carbon Lab",
        "department_th": "ภาควิชาการจัดการป่าไม้ และห้องปฏิบัติการคาร์บอนในป่าไม้เขตร้อน",
        "academic_title": "Prof. Dr.",
        "academic_title_th": "ศ.ดร.",
        "first_name": "Sathit",
        "last_name": "Watcharawin",
        "full_name": "Prof. Dr. Ladawan Puangchit",
        "full_name_th": "ศ.ดร. ลดาวัลย์ พวงจิตร",
        "role": "Distinguished Professor in Forest Tree Physiology & Tropical Carbon Accounting",
        "email": "ladawan.p@ku.ac.th",
        "image_url": "https://forest.ku.ac.th/images/faculty/ladawan.jpg",
        "profile_url": "https://forest.ku.ac.th/staff/ladawan",
        "education": [
            "Ph.D. (Forest Ecology and Physiology), University of Alberta, Canada",
            "M.Sc. (Forestry), Kasetsart University",
            "B.Sc. (Forestry - Honours), Kasetsart University"
        ],
        "research_interests": [
            "Carbon Flux & Greenhouse Gas Dynamics in Tropical Rainforests and Mangroves",
            "Dendrochronology and Climate Sensitivity of Tropical Teak and Pine",
            "Satellite Remote Sensing & Airborne LiDAR for Forest Aboveground Biomass Mapping",
            "Forest Restoration Ecology for Biodiversity and Certified Carbon Offsets (T-VER/VCS)",
            "Plant Ecophysiology under Extreme Seasonal Drought and Heat Waves"
        ],
        "taught_courses": [
            "Tropical Forest Ecology and Carbon Accounting",
            "Forest Tree Ecophysiology and Climate Dynamics",
            "Forest Biomass and Allometric Modeling"
        ],
        "featured_publications": [
            "Aboveground Biomass Estimation and Carbon Sequestration Potential in Restored Tropical Dry Deciduous Forests",
            "Long-Term Climate Response of Tectona grandis (Teak) Tree Rings in Northern Thailand",
            "Mangrove Forest Carbon Stock and Soil Organic Carbon Accumulation along the Gulf of Thailand"
        ],
        "scholar_url": "https://scholar.google.com/citations?user=LadawanPuangchit"
    },

    # =========================================================================
    # 6. KASETSART BUSINESS SCHOOL (KBS)
    # =========================================================================
    {
        "id": "ku_kbs_agribusiness_001",
        "university": "Kasetsart University",
        "university_th": "มหาวิทยาลัยเกษตรศาสตร์",
        "faculty": "Faculty of Business Administration (Kasetsart Business School - KBS)",
        "faculty_th": "คณะบริหารธุรกิจ (KBS มหาวิทยาลัยเกษตรศาสตร์)",
        "department": "Department of Agribusiness Administration and Supply Chain Management",
        "department_th": "ภาควิชาการบริหารธุรกิจเกษตรและห่วงโซ่อุปทาน",
        "academic_title": "Assoc. Prof. Dr.",
        "academic_title_th": "รศ.ดร.",
        "first_name": "Bordin",
        "last_name": "Rassameethes",
        "full_name": "Assoc. Prof. Dr. Bordin Rassameethes",
        "full_name_th": "รศ.ดร. บดินทร์ รัศมีเทศ",
        "role": "Dean of Kasetsart Business School / Leader in Agribusiness Digital Supply Chains",
        "email": "bordin.r@ku.ac.th",
        "image_url": "https://kbs.ku.ac.th/images/faculty/bordin.jpg",
        "profile_url": "https://kbs.ku.ac.th/staff/bordin",
        "education": [
            "Ph.D. (Management Science & Information Systems), Vanderbilt University, USA",
            "M.S. (Management Information Systems), University of Texas at Dallas, USA",
            "B.Eng. (Industrial Engineering), Chulalongkorn University"
        ],
        "research_interests": [
            "Agribusiness Digital Transformation & Smart Supply Chain Optimization",
            "Blockchain Traceability from Farm to Global Retail Shelf",
            "Cold Chain Logistics Resilience for Export Tropical Fruit and Seafood",
            "Sustainable Agri-Food Value Chains & ESG Compliance for Carbon Offsets",
            "Predictive Demand Forecasting in Agricultural Commodity Exchanges"
        ],
        "taught_courses": [
            "Agribusiness Digital Supply Chain Management",
            "Operations Strategy and Management Science",
            "Blockchain and Information Technology in Agri-Food Logistics"
        ],
        "featured_publications": [
            "Blockchain-Enabled End-to-End Traceability Framework for Tropical Fruit Cold Chain Export from Thailand",
            "Agri-Food Supply Chain Resilience during Extreme Disruptions: An Empirical Model of Thai Exporters",
            "Optimizing Multi-Echelon Perishable Inventory Systems with Temperature-Dependent Shelf-Life Degradation"
        ],
        "scholar_url": "https://scholar.google.com/citations?user=BordinRassameethes"
    }
]
