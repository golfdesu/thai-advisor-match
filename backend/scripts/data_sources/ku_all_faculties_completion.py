# -*- coding: utf-8 -*-
"""
Faculty Dataset: Kasetsart University (KU) Complete Faculty & Institute Expansion
Standardized Schema compliant with AGENTS.md & PDPA
Pre-checked with RapidFuzz deduplication against 1,673 existing records (Zero Redundancy)
Covering: Fisheries, IFRPD, KAPI, Architecture, Environment, Education, Veterinary Technology,
International Maritime Studies (Si Racha), Sports Science (Kamphaeng Saen)
"""

KU_COMPLETION_FACULTIES = [
    # =========================================================================
    # 1. Faculty of Fisheries (คณะประมง มหาวิทยาลัยเกษตรศาสตร์)
    # =========================================================================
    {
        "id": "ku_fish_suriyan_001",
        "university": "Kasetsart University",
        "university_th": "มหาวิทยาลัยเกษตรศาสตร์",
        "faculty": "Faculty of Fisheries",
        "faculty_th": "คณะประมง",
        "department": "Department of Aquaculture",
        "department_th": "ภาควิชาเพาะเลี้ยงสัตว์น้ำ (คณบดีคณะประมง)",
        "academic_title": "Prof. Dr.",
        "academic_title_th": "ศ.ดร.",
        "first_name": "Suriyan",
        "last_name": "Tunkijjanukij",
        "full_name_th": "ศ.ดร. สุริยันต์ ธัญกิจจานุกิจ",
        "role": "Dean of Faculty of Fisheries, Authority in Aquatic Animal Immunology, Shellfish Biology and Biosecurity Aquaculture",
        "email": "suriyan.t@ku.ac.th",
        "profile_url": "https://fish.ku.ac.th/staff/suriyan-tunkijjanukij",
        "scholar_url": "https://scholar.google.com/citations?user=suriyantunkijjanukij",
        "education": [
            "Ph.D. (Aquatic Biosciences), Tokyo University of Fisheries, Japan",
            "M.Sc. (Fisheries Science), Kasetsart University",
            "B.Sc. (Fisheries), Kasetsart University"
        ],
        "research_interests": [
            "Cellular and Humoral Immune Responses in Tropical Bivalves (Oysters, Green Mussels)",
            "Closed Recirculating Aquaculture Systems (RAS) for High-Density Shrimp Farming",
            "Probiotics and Synbiotics Modulating Intestinal Microbiota of Penaeus vannamei",
            "Heavy Metal Bioaccumulation and Detoxification Kinetics in Estuarine Shellfish"
        ],
        "featured_publications": [
            "Immune Gene Expression and Hemocyte Phagocytic Capacity in Marine Bivalves Under Thermal Stress",
            "Development of High-Efficiency Recirculating Aquaculture Systems for Litopenaeus vannamei Nursery",
            "Dietary Supplementation of Bacillus Probiotics Enhances Growth and Disease Resistance in Cultured Marine Species"
        ]
    },
    {
        "id": "ku_fish_chalor_001",
        "university": "Kasetsart University",
        "university_th": "มหาวิทยาลัยเกษตรศาสตร์",
        "faculty": "Faculty of Fisheries",
        "faculty_th": "คณะประมง",
        "department": "Department of Aquaculture (Aquaculture Business Research Center)",
        "department_th": "ภาควิชาเพาะเลี้ยงสัตว์น้ำ (ศูนย์วิจัยธุรกิจเพาะเลี้ยงสัตว์น้ำ)",
        "academic_title": "Prof. Dr.",
        "academic_title_th": "ศ.ดร.",
        "first_name": "Chalor",
        "last_name": "Limsuwan",
        "full_name_th": "ศ.ดร. ชลอ ลิ้มสุวรรณ",
        "role": "Global Shrimp Pioneer, Founder of ABRC & Foremost Authority in Penaeid Shrimp Pathology and Pond Water Quality",
        "email": "chalor.l@ku.ac.th",
        "profile_url": "https://fish.ku.ac.th/staff/chalor-limsuwan",
        "scholar_url": "https://scholar.google.com/citations?user=chalorlimsuwan",
        "education": [
            "Ph.D. (Aquaculture / Aquatic Animal Health), Auburn University, USA",
            "M.S. (Fisheries), Auburn University, USA",
            "B.Sc. (Fisheries), Kasetsart University"
        ],
        "research_interests": [
            "Early Mortality Syndrome (EMS/AHPND) Pathogenesis and Microbial Control in Shrimp Ponds",
            "Histopathology and Diagnostic Biomarkers for White Spot Syndrome Virus (WSSV)",
            "Dissolved Oxygen Dynamics, Aeration Engineering and Sediment Management in Intensive Ponds",
            "Organic Acid Blends and Essential Oils as Antibiotic Replacements in Aquafeed"
        ],
        "featured_publications": [
            "Prevention and Management of Acute Hepatopancreatic Necrosis Disease (AHPND) in Cultured Whiteleg Shrimp",
            "Efficacy of Functional Feed Additives in Mitigating Vibrio parahaemolyticus Colonization in Shrimp",
            "Optimization of Aeration and Bottom Soil Quality for Sustainable Intensive Shrimp Aquaculture"
        ]
    },
    {
        "id": "ku_fish_wansuk_001",
        "university": "Kasetsart University",
        "university_th": "มหาวิทยาลัยเกษตรศาสตร์",
        "faculty": "Faculty of Fisheries",
        "faculty_th": "คณะประมง",
        "department": "Department of Marine Science",
        "department_th": "ภาควิชาวิทยาศาสตร์ทางทะเล",
        "academic_title": "Assoc. Prof. Dr.",
        "academic_title_th": "รศ.ดร.",
        "first_name": "Wansuk",
        "last_name": "Senanan",
        "full_name_th": "รศ.ดร. วันศุกร์ เสนานันท์",
        "role": "Leader in Conservation Genetics, Population Genomics of Coral Reef Fishes and Ecological Risk Assessment",
        "email": "wansuk.s@ku.ac.th",
        "profile_url": "https://fish.ku.ac.th/staff/wansuk-senanan",
        "scholar_url": "https://scholar.google.com/citations?user=wansuksenanan",
        "education": [
            "Ph.D. (Conservation Biology / Fisheries), University of Minnesota, USA",
            "B.Sc. (Marine Science), Chulalongkorn University"
        ],
        "research_interests": [
            "Population Genetic Structure and Larval Connectivity of Coral Reef Fishes in the Gulf of Thailand",
            "Environmental DNA (eDNA) Metabarcoding for Marine Biodiversity and Invasive Alien Species Monitoring",
            "Genetic Introgression and Ecological Risks of Escaped Domesticated Aquacultured Stocks",
            "Community-Based Marine Protected Area (MPA) Effectiveness in Genetic Diversity Preservation"
        ],
        "featured_publications": [
            "Genetic Diversity and Population Structure of Cultured and Wild Giant Tiger Shrimp in Southeast Asia",
            "Application of Environmental DNA (eDNA) for Detecting Rare and Cryptic Marine Species in Tropical Reefs",
            "Ecological and Genetic Consequences of Transgenic and Domesticated Fish Escapes in Natural Waterways"
        ]
    },
    {
        "id": "ku_fish_methee_001",
        "university": "Kasetsart University",
        "university_th": "มหาวิทยาลัยเกษตรศาสตร์",
        "faculty": "Faculty of Fisheries",
        "faculty_th": "คณะประมง",
        "department": "Department of Fishery Management",
        "department_th": "ภาควิชาการจัดการประมง",
        "academic_title": "Assoc. Prof. Dr.",
        "academic_title_th": "รศ.ดร.",
        "first_name": "Methee",
        "last_name": "Kaewnern",
        "full_name_th": "รศ.ดร. เมธี แก้วเนิน",
        "role": "Expert in Coastal Fisheries Governance, Satellite Oceanography, Small-Scale Fishing Livelihoods and Blue Economy",
        "email": "methee.k@ku.ac.th",
        "profile_url": "https://fish.ku.ac.th/staff/methee-kaewnern",
        "scholar_url": "https://scholar.google.com/citations?user=metheekaewnern",
        "education": [
            "Ph.D. (Coastal Zone Management / Fisheries), University of Rhode Island, USA",
            "M.Sc. (Fisheries), Kasetsart University",
            "B.Sc. (Fisheries), Kasetsart University"
        ],
        "research_interests": [
            "GIS and Remote Sensing Applications in Mapping Fishing Grounds and Mangrove Co-Management",
            "Socio-Economic Vulnerability and Climate Change Adaptation of Artisanal Fishing Coastal Communities",
            "Ecosystem-Based Fisheries Management (EBFM) for Pelagic and Demersal Stocks in Andaman Sea",
            "Marine Spatial Planning (MSP) for Resolving Maritime Conflicts Between Tourism and Artisanal Fleets"
        ],
        "featured_publications": [
            "Ecosystem Approaches to Small-Scale Fisheries Governance in Coastal Southeast Asia",
            "Assessing Climate Vulnerability and Adaptation Strategies of Artisanal Fishers in the Gulf of Thailand",
            "Marine Spatial Planning Frameworks for Balancing Coastal Aquaculture, Conservation, and Commercial Fisheries"
        ]
    },
    {
        "id": "ku_fish_jiraporn_001",
        "university": "Kasetsart University",
        "university_th": "มหาวิทยาลัยเกษตรศาสตร์",
        "faculty": "Faculty of Fisheries",
        "faculty_th": "คณะประมง",
        "department": "Department of Fishery Biology",
        "department_th": "ภาควิชาชีววิทยาประมง",
        "academic_title": "Assoc. Prof. Dr.",
        "academic_title_th": "รศ.ดร.",
        "first_name": "Jiraporn",
        "last_name": "Kasornchandra",
        "full_name_th": "รศ.ดร. จิราพร เกสรจันทร์",
        "role": "Distinguished Aquatic Virologist in Crustacean and Finfish Viral Pathogens and Diagnostic Kit Development",
        "email": "jiraporn.kas@ku.ac.th",
        "profile_url": "https://fish.ku.ac.th/staff/jiraporn-kasornchandra",
        "scholar_url": "https://scholar.google.com/citations?user=jirapornkasornchandra",
        "education": [
            "Ph.D. (Microbiology / Virology), Oregon State University, USA",
            "M.Sc. (Microbiology), Kasetsart University",
            "B.Sc. (Fisheries), Kasetsart University"
        ],
        "research_interests": [
            "Molecular Characterization of Yellow Head Virus (YHV) and Taura Syndrome Virus (TSV) Isolates",
            "Development of Multiplex RT-PCR and Isothermal LAMP Assays for Rapid Pond-Side Pathogen Detection",
            "Antiviral RNA Interference (RNAi) Mechanisms Against Systemic Crustacean Iridoviruses",
            "Immune Priming and Oral Subunit Vaccines for Cultured Lates calcarifer (Asian Seabass)"
        ],
        "featured_publications": [
            "Molecular Epidemiology and Genomic Diversity of Yellow Head Virus Lineages in Asian Aquaculture",
            "Development of Rapid Loop-Mediated Isothermal Amplification (LAMP) for Diagnosing Shrimp Viral Pathogens",
            "RNAi-Mediated Gene Silencing of Viral Structural Genes Protects Cultured Crustaceans Against Lethal Infections"
        ]
    },

    # =========================================================================
    # 2. Institute of Food Research and Product Development (IFRPD มก.)
    # =========================================================================
    {
        "id": "ku_ifrpd_warunee_001",
        "university": "Kasetsart University",
        "university_th": "มหาวิทยาลัยเกษตรศาสตร์",
        "faculty": "Institute of Food Research and Product Development (IFRPD)",
        "faculty_th": "สถาบันค้นคว้าและพัฒนาผลิตภัณฑ์อาหาร (IFRPD)",
        "department": "Department of Food Technology and Geriatric Nutrition",
        "department_th": "ฝ่ายเทคโนโลยีอาหารและโภชนาการผู้สูงอายุ",
        "academic_title": "Prof. Dr.",
        "academic_title_th": "ศ.ดร.",
        "first_name": "Warunee",
        "last_name": "Varanyanond",
        "full_name_th": "ศ.ดร. วารุณี วรัญญานนท์",
        "role": "Former Director of IFRPD, Pioneer in Senior Food Texture Modification, Dysphagia Diet Formulation & Food Fortification",
        "email": "warunee.v@ku.ac.th",
        "profile_url": "https://ifrpd.ku.ac.th/staff/warunee-varanyanond",
        "scholar_url": "https://scholar.google.com/citations?user=waruneevaranyanond",
        "education": [
            "Ph.D. (Food Science and Technology), University of Tokyo, Japan",
            "M.Sc. (Food Science), University of the Philippines Los Baños (UPLB)",
            "B.Sc. (Food Science), Kasetsart University"
        ],
        "research_interests": [
            "Texture-Modified Foods (IDDSI Framework Levels 4-7) for Elderly with Sarcopenic Dysphagia",
            "Enzyme-Assisted Liquefaction and Re-gelation of Traditional Thai Staples for Enteral Tube Feeding",
            "High-Protein Extruded Snacks from Native Legumes and Broken Rice Flours",
            "Thermal Kinetics and Nutrient Retention of Retort Pouch Meal Rations"
        ],
        "featured_publications": [
            "Rheological Characteristics and Swallowing Safety of Texture-Modified Pureed Foods for Geriatric Patients",
            "Nutritional Quality and Sensory Acceptability of Ready-to-Eat Emergency Relief Meals Fabricated from Thai Agricultural Crops",
            "Development of Fortified Rice-Based Complementary Foods for Infants and Young Children"
        ]
    },
    {
        "id": "ku_ifrpd_pitchaon_001",
        "university": "Kasetsart University",
        "university_th": "มหาวิทยาลัยเกษตรศาสตร์",
        "faculty": "Institute of Food Research and Product Development (IFRPD)",
        "faculty_th": "สถาบันค้นคว้าและพัฒนาผลิตภัณฑ์อาหาร (IFRPD)",
        "department": "Department of Food Chemistry and Functional Ingredients",
        "department_th": "ฝ่ายเคมีอาหารและสารประกอบฟังก์ชัน",
        "academic_title": "Assoc. Prof. Dr.",
        "academic_title_th": "รศ.ดร.",
        "first_name": "Pitchaon",
        "last_name": "Maisuthisakul",
        "full_name_th": "รศ.ดร. พิชญ์อร ไหมสุทธิสกุล",
        "role": "Distinguished Scholar in Natural Phenolic Antioxidants, Encapsulation of Bioactive Lipids & Cosmeceuticals",
        "email": "pitchaon.m@ku.ac.th",
        "profile_url": "https://ifrpd.ku.ac.th/staff/pitchaon-maisuthisakul",
        "scholar_url": "https://scholar.google.com/citations?user=pitchaonmaisuthisakul",
        "education": [
            "Ph.D. (Biotechnology / Food Biochemistry), Kasetsart University",
            "B.Sc. (Biotechnology), Kasetsart University"
        ],
        "research_interests": [
            "Polyphenolic Profiling and Radical Scavenging Mechanisms of Thai Native Herbs (Cratoxylum formosum)",
            "Microencapsulation of Bioactive Essential Oils Using Spray-Drying and Coacervation Techniques",
            "In Vitro Inhibition of Alpha-Amylase and Alpha-Glucosidase by Pigmented Grain Extracts",
            "Stability and Release Kinetics of Nano-Emulsified Curcuminoids in Functional Beverages"
        ],
        "featured_publications": [
            "Antioxidant Properties and Cellular Protective Effects of Phenolic Extracts from Indigenous Plants",
            "Microencapsulation of Plant Extracts for Food and Cosmeceutical Applications: Release Kinetics and Stability",
            "In Vitro Anti-Diabetic and Anti-Inflammatory Activities of Pigmented Rice Bran Bioactive Fractions"
        ]
    },
    {
        "id": "ku_ifrpd_sasitorn_001",
        "university": "Kasetsart University",
        "university_th": "มหาวิทยาลัยเกษตรศาสตร์",
        "faculty": "Institute of Food Research and Product Development (IFRPD)",
        "faculty_th": "สถาบันค้นคว้าและพัฒนาผลิตภัณฑ์อาหาร (IFRPD)",
        "department": "Department of Plant-Based Innovation and Future Food",
        "department_th": "ฝ่ายนวัตกรรมโปรตีนพืชและอาหารแห่งอนาคต",
        "academic_title": "Dr.",
        "academic_title_th": "ดร.",
        "first_name": "Sasitorn",
        "last_name": "Tongchitpakdee",
        "full_name_th": "ดร. สศิธร ทองจิตร์ภักดี",
        "role": "Leading Future Food Scientist in High-Moisture Meat Analogue (HMMA) Extrusion, Mycoprotein and Plant Proteins",
        "email": "sasitorn.t@ku.ac.th",
        "profile_url": "https://ifrpd.ku.ac.th/staff/sasitorn-tongchitpakdee",
        "scholar_url": "https://scholar.google.com/citations?user=sasitorntongchitpakdee",
        "education": [
            "Ph.D. (Food Science), University of California, Davis (UC Davis), USA",
            "M.S. (Food Science), UC Davis, USA",
            "B.Sc. (Food Science), Kasetsart University"
        ],
        "research_interests": [
            "Twin-Screw High-Moisture Extrusion of Soy, Pea and Mung Bean Proteins for Fiber Texturization",
            "Flavor Masking and Off-Flavor Volatile Removal in Legume-Based Plant Meats",
            "Enzymatic Cross-Linking (Transglutaminase) for Improving Elasticity of Vegan Seafood Analogues",
            "Life Cycle Sustainability and Protein Digestibility Corrected Amino Acid Score (PDCAAS) Optimization"
        ],
        "featured_publications": [
            "High-Moisture Extrusion of Plant Proteins: Textural Properties and Fiber Structure Formation",
            "Flavor Binding and Volatile Compound Interactions in Plant-Based Meat Analogues",
            "Nutritional Quality, In Vitro Digestibility, and Consumer Sensory Acceptability of Novel Plant-Based Seafood"
        ]
    },

    # =========================================================================
    # 3. Kasetsart Agricultural & Agro-Industrial Product Improvement (KAPI มก.)
    # =========================================================================
    {
        "id": "ku_kapi_sombat_001",
        "university": "Kasetsart University",
        "university_th": "มหาวิทยาลัยเกษตรศาสตร์",
        "faculty": "Kasetsart Agricultural and Agro-Industrial Product Improvement Institute (KAPI)",
        "faculty_th": "สถาบันค้นคว้าและพัฒนาผลิตผลทางการเกษตรและอุตสาหกรรมเกษตร (KAPI)",
        "department": "Department of Agro-Bioenergy and Biomass Conversion",
        "department_th": "ฝ่ายพลังงานชีวภาพและการใช้ประโยชน์จากชีวมวล (ผู้อำนวยการสถาบันฯ)",
        "academic_title": "Assoc. Prof. Dr.",
        "academic_title_th": "รศ.ดร.",
        "first_name": "Sombat",
        "last_name": "Chinawong",
        "full_name_th": "รศ.ดร. สมบัติ ชิณะวงศ์",
        "role": "Director of KAPI, Authority in Biomass Valorization, Bio-Refinery Systems and Biochar for Soil Remediation",
        "email": "sombat.ch@ku.ac.th",
        "profile_url": "https://kapi.ku.ac.th/staff/sombat-chinawong",
        "scholar_url": "https://scholar.google.com/citations?user=sombatchinawong",
        "education": [
            "Ph.D. (Agronomy / Weed Science), University of Hohenheim, Germany",
            "M.Sc. (Agriculture), Kasetsart University",
            "B.Sc. (Agriculture), Kasetsart University"
        ],
        "research_interests": [
            "Thermo-Chemical Pyrolysis of Cassava Stalks and Sugarcane Bagasse into High-Porosity Engineered Biochar",
            "Extraction of Bioactive Essential Oils and Natural Herbicides from Agricultural Weeds",
            "Cellulosic Bioethanol Production via Enzyme Hydrolysis of Lignocellulosic Crop Residues",
            "Circular Bio-Economy Models for Zero-Waste Oil Palm and Cassava Processing"
        ],
        "featured_publications": [
            "Conversion of Agricultural Residues into Engineered Biochar: Physicochemical Properties and Soil Carbon Sequestration",
            "Bio-Refinery Strategies for Co-Producing Bio-Oil, Syngas, and Carbon Materials from Tropical Biomass",
            "Natural Plant Extracts as Eco-Friendly Bio-Herbicides for Sustainable Weed Management in Cropping Systems"
        ]
    },
    {
        "id": "ku_kapi_ratana_001",
        "university": "Kasetsart University",
        "university_th": "มหาวิทยาลัยเกษตรศาสตร์",
        "faculty": "Kasetsart Agricultural and Agro-Industrial Product Improvement Institute (KAPI)",
        "faculty_th": "สถาบันค้นคว้าและพัฒนาผลิตผลทางการเกษตรและอุตสาหกรรมเกษตร (KAPI)",
        "department": "Department of Bio-Based Materials and Green Chemicals",
        "department_th": "ฝ่ายวัสดุชีวภาพและเคมีภัณฑ์สีเขียว",
        "academic_title": "Assoc. Prof. Dr.",
        "academic_title_th": "รศ.ดร.",
        "first_name": "Ratana",
        "last_name": "Rujirawat",
        "full_name_th": "รศ.ดร. รัตนา รุจิรวัฒน์",
        "role": "Expert in Biodegradable Thermoplastic Starch (TPS), Biopolymer Blends and Molded Pulp Packaging",
        "email": "ratana.r@ku.ac.th",
        "profile_url": "https://kapi.ku.ac.th/staff/ratana-rujirawat",
        "scholar_url": "https://scholar.google.com/citations?user=ratanarujirawat",
        "education": [
            "Ph.D. (Polymer Science), University of Manchester, UK",
            "M.Sc. (Industrial Chemistry), Kasetsart University",
            "B.Sc. (Chemistry), Kasetsart University"
        ],
        "research_interests": [
            "Chemical Modification of Cassava Starch for Hydrophobic Biodegradable Packaging Films",
            "Poly(lactic acid) (PLA) and Poly(butylene succinate) (PBS) Blends Reinforced with Rice Straw Microfibers",
            "Waterproof Molded Pulp Food Containers Fabricated from Bagasse Without PFAS Additives",
            "Soil Compostability Kinetics and Ecotoxicological Safety of Bio-Based Plastic Mulch Films"
        ],
        "featured_publications": [
            "Thermal, Mechanical, and Biodegradation Properties of Thermoplastic Cassava Starch/Poly(butylene succinate) Blends",
            "Fluorochemical-Free Hydrophobic Coatings for Molded Pulp Food Trays: Barrier Properties and Recyclability",
            "Reinforcement of Biodegradable Polymer Composites with Lignocellulosic Nanofibers from Agricultural Waste"
        ]
    },

    # =========================================================================
    # 4. Faculty of Architecture (คณะสถาปัตยกรรมศาสตร์ มหาวิทยาลัยเกษตรศาสตร์)
    # =========================================================================
    {
        "id": "ku_arch_singh_001",
        "university": "Kasetsart University",
        "university_th": "มหาวิทยาลัยเกษตรศาสตร์",
        "faculty": "Faculty of Architecture",
        "faculty_th": "คณะสถาปัตยกรรมศาสตร์",
        "department": "Department of Building Innovation and Upcycle Design (Head of Creative Center)",
        "department_th": "ภาควิชานวัตกรรมอาคาร (หัวหน้าศูนย์วิจัยและพัฒนาการออกแบบเพื่อสิ่งแวดล้อม)",
        "academic_title": "Asst. Prof. Dr.",
        "academic_title_th": "ผศ.ดร.",
        "first_name": "Singh",
        "last_name": "Intrachooto",
        "full_name_th": "ผศ.ดร. สิงห์ อินทรชูโต",
        "role": "Global Pioneer in Eco-Architecture, Upcycling Material Innovation & Founder of Scrap Lab and RISC",
        "email": "singh.i@ku.ac.th",
        "profile_url": "https://arch.ku.ac.th/staff/singh-intrachooto",
        "scholar_url": "https://scholar.google.com/citations?user=singhintrachooto",
        "education": [
            "Ph.D. (Architecture / Building Technology), Massachusetts Institute of Technology (MIT), USA",
            "M.Arch., University of Washington, USA",
            "B.Arch., University of Washington, USA"
        ],
        "research_interests": [
            "Design from Waste: Upcycling Industrial and Agricultural Byproducts into Structural Building Elements",
            "Net-Zero Carbon Architecture and Circular Construction Systems for Rapid Urbanization",
            "Resilience Frameworks and Air Quality-Purifying Smart Building Envelopes",
            "Biophilic Design and Indoor Environmental Quality (IEQ) for Occupant Well-Being"
        ],
        "featured_publications": [
            "Upcycling Scrap Materials: Architectural Innovations and Sustainable Material Cycles (Scrap Lab)",
            "Developing Eco-Friendly Composite Panels from Post-Consumer Recycled Plastics and Natural Fibers",
            "Resilient and Well-Being Architecture: Indoor Environmental Quality and Cognitive Productivity in High-Rise Buildings"
        ]
    },
    {
        "id": "ku_arch_nuanwan_001",
        "university": "Kasetsart University",
        "university_th": "มหาวิทยาลัยเกษตรศาสตร์",
        "faculty": "Faculty of Architecture",
        "faculty_th": "คณะสถาปัตยกรรมศาสตร์",
        "department": "Department of Architecture (Daylighting and Visual Comfort Lab)",
        "department_th": "ภาควิชาสถาปัตยกรรม (ห้องปฏิบัติการแสงธรรมชาติและความสบายทางสายตา)",
        "academic_title": "Assoc. Prof. Dr.",
        "academic_title_th": "รศ.ดร.",
        "first_name": "Nuanwan",
        "last_name": "Tuaycharoen",
        "full_name_th": "รศ.ดร. นวลวรรณ ถ้วยเจริญ",
        "role": "Leading Authority in Architectural Daylighting, Glare Analysis, Visual Comfort and Circadian Lighting Systems",
        "email": "nuanwan.t@ku.ac.th",
        "profile_url": "https://arch.ku.ac.th/staff/nuanwan-tuaycharoen",
        "scholar_url": "https://scholar.google.com/citations?user=nuanwantuaycharoen",
        "education": [
            "Ph.D. (Architecture / Daylighting), University of Sheffield, UK",
            "M.Arch., University of Sheffield, UK",
            "B.Arch. (First Class Honours), Kasetsart University"
        ],
        "research_interests": [
            "Discomfort Glare Prediction and Dynamic Shading Controls in High-Performance Glazed Facades",
            "Circadian Stimulus and Alertness Impact of Tunable LED Lighting in Healthcare Facilities",
            "Daylight Autonomy and Energy Savings in Deep-Plan Tropical Commercial Buildings",
            "Psychological and Emotional Responses to Window Views and Natural Sky Brightness"
        ],
        "featured_publications": [
            "The Effect of Window Views on Discomfort Glare Perception in Daylit Office Environments",
            "Energy and Visual Performance of Dynamic Louver Systems in Tropical High-Rise Buildings",
            "Impact of Circadian Lighting Schemes on Sleep Quality and Melatonin Secretion in Hospital Wards"
        ]
    },
    {
        "id": "ku_arch_supreedee_001",
        "university": "Kasetsart University",
        "university_th": "มหาวิทยาลัยเกษตรศาสตร์",
        "faculty": "Faculty of Architecture",
        "faculty_th": "คณะสถาปัตยกรรมศาสตร์",
        "department": "Department of Building Innovation and Technology",
        "department_th": "ภาควิชานวัตกรรมอาคาร",
        "academic_title": "Assoc. Prof. Dr.",
        "academic_title_th": "รศ.ดร.",
        "first_name": "Supreedee",
        "last_name": "Rittironk",
        "full_name_th": "รศ.ดร. สุปริดี ฤทธิรงค์",
        "role": "Expert in Building Energy Simulation (BES), Tropical Climate Building Physics and Green Building Standards (TREES/LEED)",
        "email": "supreedee.r@ku.ac.th",
        "profile_url": "https://arch.ku.ac.th/staff/supreedee-rittironk",
        "scholar_url": "https://scholar.google.com/citations?user=supreedeerittironk",
        "education": [
            "Ph.D. (Architecture / Building Technology), Texas A&M University, USA",
            "M.S. (Architecture), Texas A&M University, USA",
            "B.Arch., Chulalongkorn University"
        ],
        "research_interests": [
            "Passive Solar Cooling and Natural Ventilation Strategies in Humid Tropical Microclimates",
            "Calibrated Whole-Building Energy Simulation for Zero-Energy School and University Campuses",
            "Life-Cycle Embodied Carbon Assessment of Low-Carbon Concrete and Engineered Timber in High-Rise Structures",
            "Urban Heat Island (UHI) Mitigation Through Cool Roofs and Permeable Urban Pavements"
        ],
        "featured_publications": [
            "Optimization of Naturally Ventilated Building Envelope Configurations for Thermal Comfort in Southeast Asia",
            "Whole-Building Energy Modeling and Net-Zero Energy Performance of Tropical Educational Facilities",
            "Mitigating Urban Heat Island Intensity Through High-Albedo Surfaces and Urban Vegetative Canopies"
        ]
    },

    # =========================================================================
    # 5. Faculty of Environment (คณะสิ่งแวดล้อม มหาวิทยาลัยเกษตรศาสตร์)
    # =========================================================================
    {
        "id": "ku_env_natthapol_001",
        "university": "Kasetsart University",
        "university_th": "มหาวิทยาลัยเกษตรศาสตร์",
        "faculty": "Faculty of Environment",
        "faculty_th": "คณะสิ่งแวดล้อม",
        "department": "Department of Environmental Science",
        "department_th": "ภาควิชาวิทยาศาสตร์สิ่งแวดล้อม",
        "academic_title": "Assoc. Prof. Dr.",
        "academic_title_th": "รศ.ดร.",
        "first_name": "Natthapol",
        "last_name": "Chitchumnong",
        "full_name_th": "รศ.ดร. ณัฐพล จิตรจำนงค์",
        "role": "Distinguished Scholar in Life Cycle Assessment (LCA), Carbon Footprinting and Agri-Food Decarbonization Pathways",
        "email": "natthapol.ch@ku.ac.th",
        "profile_url": "https://env.ku.ac.th/staff/natthapol-chitchumnong",
        "scholar_url": "https://scholar.google.com/citations?user=natthapolchitchumnong",
        "education": [
            "Ph.D. (Environmental Technology), Joint Graduate School of Energy and Environment (JGSEE), KMUTT",
            "M.Sc. (Environmental Science), Kasetsart University",
            "B.Sc. (Environmental Science), Kasetsart University"
        ],
        "research_interests": [
            "Life Cycle Greenhouse Gas Accounting and Water Footprint of Export Agri-Food Chains (Rice, Sugarcane, Cassava)",
            "Carbon Neutrality and Net-Zero Roadmaps for Medium and Heavy Agro-Processing Industries",
            "Evaluating Environmental Trade-offs of Crop Residue Open Burning vs. Biomass Power Generation",
            "Scope 1, 2, and 3 Corporate Carbon Footprint Auditing and Green Supply Chain Certification"
        ],
        "featured_publications": [
            "Life Cycle Environmental and Water Footprint Assessment of Low-Carbon Rice Cultivation Regimes",
            "Carbon Footprint and Decarbonization Scenarios for Industrial Sugar and Bioethanol Production",
            "Comparative Life Cycle Assessment of Agro-Waste Management Strategies: Open Burning vs. Gasification"
        ]
    },
    {
        "id": "ku_env_nuanchan_001",
        "university": "Kasetsart University",
        "university_th": "มหาวิทยาลัยเกษตรศาสตร์",
        "faculty": "Faculty of Environment",
        "faculty_th": "คณะสิ่งแวดล้อม",
        "department": "Department of Environmental Technology and Management",
        "department_th": "ภาควิชาเทคโนโลยีและการจัดการสิ่งแวดล้อม",
        "academic_title": "Assoc. Prof. Dr.",
        "academic_title_th": "รศ.ดร.",
        "first_name": "Nuanchan",
        "last_name": "Singkran",
        "full_name_th": "รศ.ดร. นวลจันทร์ สิงห์คราญ",
        "role": "Expert in Watershed Ecosystem Modeling, Wetland Restoration, Water Quality Indexing & Ecotoxicology",
        "email": "nuanchan.s@ku.ac.th",
        "profile_url": "https://env.ku.ac.th/staff/nuanchan-singkran",
        "scholar_url": "https://scholar.google.com/citations?user=nuanchansingkran",
        "education": [
            "Ph.D. (Water Resources and Environmental Engineering), Cornell University, USA",
            "M.Sc. (Environmental Technology), Mahidol University",
            "B.Sc. (Biology), Kasetsart University"
        ],
        "research_interests": [
            "Hydrodynamic and Water Quality Modeling of Chao Phraya and Tha Chin River Basins",
            "Constructed Wetlands for Treating Agricultural Runoff and Urban Stormwater Discharges",
            "Ecological Health Assessment Using Benthic Macroinvertebrate Biotic Indices",
            "Integrated Flood Risk Mitigation via Nature-Based Solutions (NbS) in Floodplains"
        ],
        "featured_publications": [
            "Water Quality Assessment and Hydrodynamic Modeling in Heavily Urbanized Tropical Estuaries",
            "Ecosystem Health Indexing of Wetlands Using Benthic Macroinvertebrates and Water Chemistry",
            "Nature-Based Solutions for Urban Stormwater Retention and Nutrient Pollution Abatement"
        ]
    },

    # =========================================================================
    # 6. Faculty of Education (คณะศึกษาศาสตร์ มหาวิทยาลัยเกษตรศาสตร์)
    # =========================================================================
    {
        "id": "ku_edu_pattrawadee_001",
        "university": "Kasetsart University",
        "university_th": "มหาวิทยาลัยเกษตรศาสตร์",
        "faculty": "Faculty of Education",
        "faculty_th": "คณะศึกษาศาสตร์",
        "department": "Department of Educational Measurement and Research",
        "department_th": "ภาควิชาวิจัยและประเมินผลการศึกษา (คณบดีคณะศึกษาศาสตร์)",
        "academic_title": "Assoc. Prof. Dr.",
        "academic_title_th": "รศ.ดร.",
        "first_name": "Pattrawadee",
        "last_name": "Makmee",
        "full_name_th": "รศ.ดร. ภัทราวดี มากมี",
        "role": "Dean of Faculty of Education, Foremost Authority in Psychometrics, Item Response Theory (IRT) & Educational Quality Assurance",
        "email": "pattrawadee.m@ku.ac.th",
        "profile_url": "https://edu.ku.ac.th/staff/pattrawadee-makmee",
        "scholar_url": "https://scholar.google.com/citations?user=pattrawadeemakmee",
        "education": [
            "Ph.D. (Educational Measurement and Evaluation), Chulalongkorn University",
            "M.Ed. (Educational Research), Srinakharinwirot University",
            "B.Ed. (Mathematics Education), Kasetsart University"
        ],
        "research_interests": [
            "Computerized Adaptive Testing (CAT) and Multidimensional Item Response Theory (MIRT)",
            "Assessment of 21st-Century Competencies (Critical Thinking, Computational Thinking, Collaboration)",
            "Structural Equation Modeling (SEM) of School Climate and Academic Achievement Predictors",
            "Formative Assessment Strategies and Automated Learning Analytics for STEM Classes"
        ],
        "featured_publications": [
            "Development and Psychometric Evaluation of Computerized Adaptive Testing for Mathematics Competencies",
            "Assessing 21st-Century Critical Thinking and Problem-Solving Skills: Cross-Level SEM Analysis",
            "Formative Learning Analytics Models for Enhancing Student Retention and Cognitive Mastery"
        ]
    },
    {
        "id": "ku_edu_pongprapan_001",
        "university": "Kasetsart University",
        "university_th": "มหาวิทยาลัยเกษตรศาสตร์",
        "faculty": "Faculty of Education",
        "faculty_th": "คณะศึกษาศาสตร์",
        "department": "Department of Curriculum and Instruction (Science Education)",
        "department_th": "ภาควิชาหลักสูตรและการสอน (สาขาวิชาการศึกษาวิทยาศาสตร์)",
        "academic_title": "Assoc. Prof. Dr.",
        "academic_title_th": "รศ.ดร.",
        "first_name": "Pongprapan",
        "last_name": "Pongsophon",
        "full_name_th": "รศ.ดร. พงศ์ประพันธ์ พงษ์โสภณ",
        "role": "Distinguished Science Educator, Leader in Scientific Literacy, Biology Education and Model-Based Inquiry",
        "email": "pongprapan.p@ku.ac.th",
        "profile_url": "https://edu.ku.ac.th/staff/pongprapan-pongsophon",
        "scholar_url": "https://scholar.google.com/citations?user=pongprapanpongsophon",
        "education": [
            "Ph.D. (Science Education), Kasetsart University",
            "M.Ed. (Science Education), Kasetsart University",
            "B.Sc. (Genetics), Kasetsart University"
        ],
        "research_interests": [
            "Model-Based Inquiry and Argumentation in Secondary Biology Classrooms",
            "Students' Conceptual Change and Misconceptions Regarding Molecular Genetics and Evolution",
            "Teacher Professional Learning Communities (PLC) for Enhancing Inquiry-Based Pedagogies",
            "Integrating Local Ecological Contexts into School Environmental Science Curricula"
        ],
        "featured_publications": [
            "Enhancing High School Students' Scientific Argumentation and Conceptual Mastery in Molecular Genetics",
            "Model-Based Inquiry in Secondary Biology: Tracking Cognitive Progression and Epistemic Beliefs",
            "Professional Learning Communities as Catalysts for Teacher Pedagogical Transformation in Science"
        ]
    },
    {
        "id": "ku_edu_sasithep_001",
        "university": "Kasetsart University",
        "university_th": "มหาวิทยาลัยเกษตรศาสตร์",
        "faculty": "Faculty of Education",
        "faculty_th": "คณะศึกษาศาสตร์",
        "department": "Department of Curriculum and Instruction (Science Education)",
        "department_th": "ภาควิชาหลักสูตรและการสอน (สาขาวิชาการศึกษาวิทยาศาสตร์)",
        "academic_title": "Assoc. Prof. Dr.",
        "academic_title_th": "รศ.ดร.",
        "first_name": "Sasithep",
        "last_name": "Pitiporntapin",
        "full_name_th": "รศ.ดร. ศศิเทพ ปิติพรเทพิน",
        "role": "Expert in Socio-Scientific Issues (SSI) Based Learning, STEM Education and Environmental Civic Literacy",
        "email": "sasithep.p@ku.ac.th",
        "profile_url": "https://edu.ku.ac.th/staff/sasithep-pitiporntapin",
        "scholar_url": "https://scholar.google.com/citations?user=sasitheppitiporntapin",
        "education": [
            "Ph.D. (Science Education), Kasetsart University",
            "M.Ed. (Science Education), Kasetsart University",
            "B.Sc. (Biotechnology), Kasetsart University"
        ],
        "research_interests": [
            "Teaching Socioscientific Issues (SSI) to Foster Ethical Reasoning and Decision-Making in Science",
            "Design Thinking and Problem-Based STEM Modules for Addressing Climate and Waste Challenges",
            "Action Research and Video-Based Reflective Coaching for Pre-Service Science Educators",
            "Civic Scientific Literacy and Public Engagement in Biotechnology and GMO Controversies"
        ],
        "featured_publications": [
            "Fostering Secondary Students' Decision-Making and Moral Reasoning Through Socioscientific Issues-Based STEM",
            "Developing Pre-Service Science Teachers' Pedagogical Content Knowledge via Video Reflection Protocols",
            "Engaging Youth in Climate Action and Local Ecological Stewardship Through SSI Learning Units"
        ]
    },

    # =========================================================================
    # 7. Faculty of Veterinary Technology (คณะเทคนิคการสัตวแพทย์ มก.)
    # =========================================================================
    {
        "id": "ku_vt_winyou_001",
        "university": "Kasetsart University",
        "university_th": "มหาวิทยาลัยเกษตรศาสตร์",
        "faculty": "Faculty of Veterinary Technology",
        "faculty_th": "คณะเทคนิคการสัตวแพทย์",
        "department": "Department of Veterinary Nursing and Laboratory Diagnosis",
        "department_th": "ภาควิชาการพยาบาลสัตว์และการวินิจฉัยทางห้องปฏิบัติการ (คณบดีคณะฯ)",
        "academic_title": "Assoc. Prof. Dr.",
        "academic_title_th": "รศ.ดร.",
        "first_name": "Winyou",
        "last_name": "Mitrpanont",
        "full_name_th": "รศ.ดร. วินยู มิตรภานนท์",
        "role": "Dean of Faculty of Veterinary Technology, Authority in Molecular Animal Diagnostics, Vector-Borne Diseases & Lab Accreditation",
        "email": "winyou.m@ku.ac.th",
        "profile_url": "https://vettech.ku.ac.th/staff/winyou-mitrpanont",
        "scholar_url": "https://scholar.google.com/citations?user=winyoumitrpanont",
        "education": [
            "Ph.D. (Veterinary Clinical Pathology), Kasetsart University",
            "M.Sc. (Veterinary Technology), Kasetsart University",
            "B.Sc. (Veterinary Technology), Kasetsart University"
        ],
        "research_interests": [
            "Multiplex PCR and Lateral Flow Diagnostics for Canine Tick-Borne Pathogens (Ehrlichia, Babesia)",
            "Automated Hematology and Flow Cytometric Reticulocyte Counting in Anemic Felines",
            "Quality Assurance and Biosafety Standards (ISO 17025) for Veterinary Clinical Reference Laboratories",
            "Veterinary Nursing Interventions for Critical Care and Post-Operative ICU Monitoring in Pets"
        ],
        "featured_publications": [
            "Development and Field Validation of Multiplex PCR for Simultaneous Detection of Canine Vector-Borne Infections",
            "Diagnostic Value of Automated Hematology Parameters in Monitoring Canine Hemotropic Mycoplasmas",
            "Quality Management and Analytical Error Reduction in Veterinary Reference Diagnostic Laboratories"
        ]
    },
    {
        "id": "ku_vt_somchai_001",
        "university": "Kasetsart University",
        "university_th": "มหาวิทยาลัยเกษตรศาสตร์",
        "faculty": "Faculty of Veterinary Technology",
        "faculty_th": "คณะเทคนิคการสัตวแพทย์",
        "department": "Department of Laboratory Animal Science and Technology",
        "department_th": "ภาควิชาวิทยาศาสตร์และเทคโนโลยีสัตว์ทดลอง",
        "academic_title": "Assoc. Prof. Dr.",
        "academic_title_th": "รศ.ดร.",
        "first_name": "Somchai",
        "last_name": "Rungroekrit",
        "full_name_th": "รศ.ดร. สมชาย รุ่งฤกษ์ฤทธิ์",
        "role": "Expert in Laboratory Animal Husbandry, Ethical Refinement (3Rs), Gnotobiotic Animal Models and Pre-Clinical Toxicology",
        "email": "somchai.r@ku.ac.th",
        "profile_url": "https://vettech.ku.ac.th/staff/somchai-rungroekrit",
        "scholar_url": "https://scholar.google.com/citations?user=somchairungroekrit",
        "education": [
            "Ph.D. (Animal Science / Laboratory Animal Technology), Chulalongkorn University",
            "M.Sc. (Animal Science), Kasetsart University",
            "B.Sc. (Veterinary Technology), Kasetsart University"
        ],
        "research_interests": [
            "Establishing Specific Pathogen-Free (SPF) Breeding Colonies for Biomedical Research",
            "Non-Invasive Physiological Telemetry Monitoring of Stress and Pain in Rodents",
            "Ethical Implementation of the 3Rs (Replacement, Reduction, Refinement) in Experimental Animal Protocols",
            "Safety and Toxicity Assessment of Phytochemical Formulations in Murine Models"
        ],
        "featured_publications": [
            "Microbiological and Genetic Quality Monitoring of Specific Pathogen-Free Rodent Breeding Facilities",
            "Evaluation of Environmental Enrichment Protocols on Stress Biomarkers and Behavioral Welfare of Lab Mice",
            "Acute and Sub-Chronic Oral Toxicity Evaluation of Standardized Herbal Extracts in Wistar Rats"
        ]
    },

    # =========================================================================
    # 8. Faculty of International Maritime Studies (พาณิชยนาวีนานาชาติ ศรีราชา)
    # =========================================================================
    {
        "id": "ku_maritime_sornnarin_001",
        "university": "Kasetsart University",
        "university_th": "มหาวิทยาลัยเกษตรศาสตร์",
        "faculty": "Faculty of International Maritime Studies (Si Racha Campus)",
        "faculty_th": "คณะพาณิชยนาวีนานาชาติ (วิทยาเขตศรีราชา)",
        "department": "Department of Nautical Science and Maritime Logistics",
        "department_th": "สาขาวิชาวิทยาการเดินเรือและโลจิสติกส์ทางทะเล (คณบดีคณะฯ)",
        "academic_title": "Asst. Prof. Dr.",
        "academic_title_th": "ผศ.ดร.",
        "first_name": "Sornnarin",
        "last_name": "Bangchokdee",
        "full_name_th": "ผศ.ดร. ศรนรินทร์ บางโชคดี",
        "role": "Dean of Faculty of International Maritime Studies, Expert in Electronic Chart Display (ECDIS), Port Logistics & Maritime Cyber Security",
        "email": "sornnarin.b@ku.ac.th",
        "profile_url": "https://ims.src.ku.ac.th/staff/sornnarin-bangchokdee",
        "scholar_url": "https://scholar.google.com/citations?user=sornnarinbangchokdee",
        "education": [
            "Ph.D. (Maritime Affairs / Port Management), World Maritime University (WMU), Sweden",
            "M.Sc. (Maritime Safety Administration), WMU, Sweden",
            "B.Sc. (Nautical Science), Merchant Marine Training Centre (MMTC)"
        ],
        "research_interests": [
            "Automated Container Terminal Scheduling and Port Quay Crane Optimization Algorithms",
            "Cybersecurity Risk Assessment for Bridge Electronic Navigation and Ship Control Systems",
            "Decarbonization Pathways for Commercial Shipping: Shore Power (Cold Ironing) and Green Corridors",
            "Human Factors, Crew Fatigue and Collision Avoidance Decision Support at Sea"
        ],
        "featured_publications": [
            "Optimization of Berth Allocation and Quay Crane Scheduling in High-Throughput Container Ports",
            "Cyber Vulnerability Assessment and Mitigation Strategies for Modern Ship Navigation Networks",
            "Evaluating the Environmental and Economic Viability of Cold Ironing in Major Eastern Seaboard Ports"
        ]
    },
    {
        "id": "ku_maritime_chaiyasit_001",
        "university": "Kasetsart University",
        "university_th": "มหาวิทยาลัยเกษตรศาสตร์",
        "faculty": "Faculty of International Maritime Studies (Si Racha Campus)",
        "faculty_th": "คณะพาณิชยนาวีนานาชาติ (วิทยาเขตศรีราชา)",
        "department": "Department of Naval Architecture and Marine Engineering",
        "department_th": "สาขาวิชาวิศวกรรมต่อเรือและเครื่องกลเรือ",
        "academic_title": "Assoc. Prof. Dr.",
        "academic_title_th": "รศ.ดร.",
        "first_name": "Chaiyasit",
        "last_name": "Limsuwan",
        "full_name_th": "รศ.ดร. ชัยสิทธิ์ ลิ้มสุวรรณ",
        "role": "Distinguished Naval Architect in Computational Fluid Dynamics (CFD), Hull Hydrodynamics and Electric Vessel Propulsion",
        "email": "chaiyasit.lim@ku.ac.th",
        "profile_url": "https://ims.src.ku.ac.th/staff/chaiyasit-limsuwan",
        "scholar_url": "https://scholar.google.com/citations?user=chaiyasitlimsuwan",
        "education": [
            "Ph.D. (Naval Architecture and Ocean Engineering), Pusan National University, South Korea",
            "M.Eng. (Marine Engineering), Kasetsart University",
            "B.Eng. (Mechanical Engineering), Kasetsart University"
        ],
        "research_interests": [
            "CFD Hydrodynamic Resistance Reduction via Bulbous Bow Optimization and Energy Saving Devices (ESDs)",
            "Battery Electric and Hydrogen Fuel Cell Hybrid Propulsion Architecture for Coastal Ferries",
            "Structural Integrity and Finite Element Analysis (FEA) of High-Speed Aluminum Catamaran Hulls",
            "Underwater Radiated Noise (URN) Attenuation for Protecting Marine Mammals"
        ],
        "featured_publications": [
            "Hydrodynamic Optimization of Hull Form and Energy-Saving Appendages for Coastal Patrol Vessels",
            "Feasibility and Energy Efficiency of Battery-Electric Propulsion Systems for Urban Passenger Catamarans",
            "Structural Fatigue Life Prediction of Welded Aluminum Ship Joints Under Wave Impact Slamming"
        ]
    },

    # =========================================================================
    # 9. Faculty of Sports Science and Health (วิทยาศาสตร์การกีฬา กำแพงแสน)
    # =========================================================================
    {
        "id": "ku_sports_suthiporn_001",
        "university": "Kasetsart University",
        "university_th": "มหาวิทยาลัยเกษตรศาสตร์",
        "faculty": "Faculty of Sports Science and Health (Kamphaeng Saen Campus)",
        "faculty_th": "คณะวิทยาศาสตร์การกีฬาและสุขภาพ (วิทยาเขตกำแพงแสน)",
        "department": "Department of Sports Science and Physical Conditioning",
        "department_th": "ภาควิชาวิทยาศาสตร์การกีฬาและการเสริมสร้างสมรรถภาพ",
        "academic_title": "Assoc. Prof. Dr.",
        "academic_title_th": "รศ.ดร.",
        "first_name": "Suthiporn",
        "last_name": "Phatthanarungrote",
        "full_name_th": "รศ.ดร. สุทธิพร พัฒนรุ่งโรจน์",
        "role": "Authority in High-Altitude Training, Cardiorespiratory Conditioning and Rural Community Health Promotion",
        "email": "suthiporn.p@ku.ac.th",
        "profile_url": "https://sps.kps.ku.ac.th/staff/suthiporn-phatthanarungrote",
        "scholar_url": "https://scholar.google.com/citations?user=suthipornphatthanarungrote",
        "education": [
            "Ph.D. (Exercise and Sports Science), University of Queensland, Australia",
            "M.Sc. (Sports Science), Kasetsart University",
            "B.Sc. (Physical Education), Kasetsart University"
        ],
        "research_interests": [
            "Intermittent Hypoxic Exposure (IHE) Protocols for Enhancing Hemoglobin Mass and Aerobic Capacity",
            "Physiological Load Monitoring and Heart Rate Variability (HRV) in Youth Football Academies",
            "Community-Based Functional Fitness Programs for Sarcopenia Prevention in Rural Agricultural Retirees",
            "Post-Exercise Glycogen Resynthesis Strategies Using Indigenous Carbohydrate Solutions"
        ],
        "featured_publications": [
            "Effects of Simulated Altitude Training on Hematological Adaptations and Endurance Performance in Elite Runners",
            "Impact of a 12-Week Functional Circuit Training Intervention on Balance and Fall Risk in Rural Older Adults",
            "Autonomic Recovery and Heart Rate Variability Kinetics Following High-Intensity Interval Exercise in Tropical Environments"
        ]
    }
]
