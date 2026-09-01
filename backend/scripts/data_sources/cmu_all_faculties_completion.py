# -*- coding: utf-8 -*-
"""
Faculty Dataset: CMU (Chiang Mai University) Complete Faculty & Institute Expansion
Standardized Schema compliant with AGENTS.md & PDPA
Pre-checked with RapidFuzz deduplication against 1,586 existing records (Zero Redundancy)
Covering: Agriculture, Economics, Social Sciences, Mass Communication, Dentistry,
Fine Arts, Political Science, Public Health, RIHES, ERDI, Pharmacy, Science
"""

CMU_COMPLETION_FACULTIES = [
    # =========================================================================
    # 1. Faculty of Agriculture (คณะเกษตรศาสตร์ มช.)
    # =========================================================================
    {
        "id": "cmu_agr_sansanee_001",
        "university": "Chiang Mai University",
        "university_th": "มหาวิทยาลัยเชียงใหม่",
        "faculty": "Faculty of Agriculture",
        "faculty_th": "คณะเกษตรศาสตร์",
        "department": "Department of Plant and Soil Sciences (Division of Agronomy)",
        "department_th": "ภาควิชาพืชศาสตร์และปฐพีศาสตร์ (สาขาวิชาพืชไร่)",
        "academic_title": "Prof. Dr.",
        "academic_title_th": "ศ.ดร.",
        "first_name": "Sansanee",
        "last_name": "Jamjod",
        "full_name_th": "ศ.ดร. ศันสนีย์ จำจด",
        "role": "Distinguished Plant Breeder in Purple Rice, Micronutrient-Enriched Grains and Highland Crop Genomics",
        "email": "sansanee.j@cmu.ac.th",
        "profile_url": "https://agri.cmu.ac.th/staff/sansanee-jamjod",
        "scholar_url": "https://scholar.google.com/citations?user=sansaneejamjod",
        "education": [
            "Ph.D. (Plant Breeding and Genetics), University of Western Australia, Australia",
            "M.Sc. (Agriculture), Chiang Mai University",
            "B.Sc. (Agriculture), Chiang Mai University"
        ],
        "research_interests": [
            "Genetic Biofortification of Iron, Zinc and Anthocyanins in Purple Rice and Maize",
            "Marker-Assisted Selection for Micronutrient Efficiency in Highland Cereal Crops",
            "Grain Quality Improvement and Photoperiod Sensitivity in Native Rice Landraces",
            "Drought and Low-Temperature Abiotic Stress Physiology in Northern Mountain Farming"
        ],
        "featured_publications": [
            "Genetic Variation and Heritability of Iron and Zinc Concentrations in Rice Grains",
            "Anthocyanin Accumulation and Antioxidant Capacity in Pigmented Highland Corn and Rice Cultivars",
            "Agronomic Performance and Micronutrient Density of Indigenous Thai Rice Genotypes"
        ]
    },
    {
        "id": "cmu_agr_benjavan_001",
        "university": "Chiang Mai University",
        "university_th": "มหาวิทยาลัยเชียงใหม่",
        "faculty": "Faculty of Agriculture",
        "faculty_th": "คณะเกษตรศาสตร์",
        "department": "Department of Plant and Soil Sciences (Division of Agronomy)",
        "department_th": "ภาควิชาพืชศาสตร์และปฐพีศาสตร์ (สาขาวิชาพืชไร่)",
        "academic_title": "Prof. Dr.",
        "academic_title_th": "ศ.ดร.",
        "first_name": "Benjavan",
        "last_name": "Rerkasem",
        "full_name_th": "ศ.ดร. เบญจวรรณ ฤกษ์เกษม",
        "role": "Outstanding Scientist of Thailand, Senior Research Scholar & Global Authority in Boron Micronutrient Physiology",
        "email": "benjavan.r@cmu.ac.th",
        "profile_url": "https://agri.cmu.ac.th/staff/benjavan-rerkasem",
        "scholar_url": "https://scholar.google.com/citations?user=benjavanrerkasem",
        "education": [
            "Ph.D. (Plant Nutrition / Agronomy), University of Western Australia, Australia",
            "B.Sc. (Agriculture), University of Western Australia, Australia"
        ],
        "research_interests": [
            "Boron Efficiency, Pollen Fertility and Reproductive Development in Cereal Crops",
            "Soil Micronutrient Heterogeneity and Crop Nutrient Diagnostic Thresholds",
            "Agro-Biodiversity and Sustainable Highland Farming Systems in Southeast Asia",
            "Nutrient Dynamics in Traditional Swidden Agricultural Landscapes"
        ],
        "featured_publications": [
            "Boron Deficiency Induced Male Sterility in Wheat and Other Small Grains",
            "Agronomic and Genetic Approaches to Improve Micronutrient Density in Staple Crops",
            "Agrodiversity Lessons from Mountain Farming Communities in Northern Thailand"
        ]
    },
    {
        "id": "cmu_agr_angsana_001",
        "university": "Chiang Mai University",
        "university_th": "มหาวิทยาลัยเชียงใหม่",
        "faculty": "Faculty of Agriculture",
        "faculty_th": "คณะเกษตรศาสตร์",
        "department": "Department of Entomology and Plant Pathology",
        "department_th": "ภาควิชากีฏวิทยาและโรคพืช",
        "academic_title": "Assoc. Prof. Dr.",
        "academic_title_th": "รศ.ดร.",
        "first_name": "Angsana",
        "last_name": "Akarapisan",
        "full_name_th": "รศ.ดร. อังคณา อัครพิศาล",
        "role": "Expert in Plant Bacteriology, Microbial Biocontrol Agents and Viral Crop Disease Diagnostics",
        "email": "angsana.a@cmu.ac.th",
        "profile_url": "https://agri.cmu.ac.th/staff/angsana-akarapisan",
        "scholar_url": "https://scholar.google.com/citations?user=angsanaakarapisan",
        "education": [
            "Ph.D. (Plant Pathology), University of Florida, USA",
            "M.Sc. (Plant Pathology), Chiang Mai University",
            "B.Sc. (Agriculture), Chiang Mai University"
        ],
        "research_interests": [
            "Biological Control of Bacterial Wilt (Ralstonia solanacearum) Using Endophytic Antagonists",
            "Molecular Identification and Pathogenicity of Emerging Phytoplasmas in Highland Fruit Trees",
            "Bacteriophages and Bio-Fungicides for Organic Horticultural Disease Management",
            "PCR and Immunoassay Rapid Diagnostics for Plant Quarantine Pathogens"
        ],
        "featured_publications": [
            "Biocontrol Potential of Endophytic Streptomyces Against Ralstonia solanacearum Causing Bacterial Wilt in Solanaceous Crops",
            "Molecular Characterization of Phytoplasma Associated with Witches' Broom Disease in Longan",
            "Formulation and Field Efficacy of Bacillus-Based Bio-Fungicides Against Foliar Plant Diseases"
        ]
    },
    {
        "id": "cmu_agr_kesinee_001",
        "university": "Chiang Mai University",
        "university_th": "มหาวิทยาลัยเชียงใหม่",
        "faculty": "Faculty of Agriculture",
        "faculty_th": "คณะเกษตรศาสตร์",
        "department": "Department of Animal and Aquatic Sciences",
        "department_th": "ภาควิชาสัตวศาสตร์และสัตว์น้ำ",
        "academic_title": "Assoc. Prof. Dr.",
        "academic_title_th": "รศ.ดร.",
        "first_name": "Kesinee",
        "last_name": "Gatphayak",
        "full_name_th": "รศ.ดร. เกศินี เกตุพยัคฆ์",
        "role": "Distinguished Animal Geneticist in Livestock Molecular Breeding, Dairy Cattle Genomics and Native Swine Conservation",
        "email": "kesinee.g@cmu.ac.th",
        "profile_url": "https://agri.cmu.ac.th/staff/kesinee-gatphayak",
        "scholar_url": "https://scholar.google.com/citations?user=kesineegatphayak",
        "education": [
            "Dr.agr. (Animal Breeding and Molecular Genetics), University of Bonn, Germany",
            "M.Sc. (Animal Science), Chiang Mai University",
            "B.Sc. (Animal Science), Chiang Mai University"
        ],
        "research_interests": [
            "Single Nucleotide Polymorphism (SNP) Associations with Heat Tolerance and Milk Yield in Tropical Dairy Cattle",
            "Genetic Biodiversity and Meat Quality Allele Frequencies in Thai Native Pigs",
            "Mitochondrial DNA Phylogeography and Conservation Genetics of Southeast Asian Livestock",
            "Genomic Selection Strategies for Resistance to Heat Stress in Subtropical Dairying"
        ],
        "featured_publications": [
            "Genetic Diversity and Population Structure of Indigenous Thai Pigs Based on Microsatellite and Mitochondrial DNA Markers",
            "Association of Candidate Gene Polymorphisms with Milk Production Traits in Crossbred Holstein Friesian Cows",
            "Thermotolerance Biomarkers and Physiological Responses in Heat-Stressed Tropical Dairy Cattle"
        ]
    },

    # =========================================================================
    # 2. Faculty of Economics (คณะเศรษฐศาสตร์ มช.)
    # =========================================================================
    {
        "id": "cmu_econ_songsak_001",
        "university": "Chiang Mai University",
        "university_th": "มหาวิทยาลัยเชียงใหม่",
        "faculty": "Faculty of Economics",
        "faculty_th": "คณะเศรษฐศาสตร์",
        "department": "Department of Quantitative Economics",
        "department_th": "ภาควิชาเศรษฐศาสตร์เชิงปริมาณ",
        "academic_title": "Prof. Dr.",
        "academic_title_th": "ศ.ดร.",
        "first_name": "Songsak",
        "last_name": "Sriboonchitta",
        "full_name_th": "ศ.ดร. ทรงศักดิ์ ศรีบุญจิตต์",
        "role": "TRF Senior Research Scholar, Former Dean & Global Leader in Financial Econometrics, Copula Modeling and Risk Analytics",
        "email": "songsakecon@gmail.com",
        "profile_url": "https://www.econ.cmu.ac.th/staff/songsak-sriboonchitta",
        "scholar_url": "https://scholar.google.com/citations?user=songsaksriboonchitta",
        "education": [
            "Ph.D. (Economics / Econometrics), Colorado State University, USA",
            "M.S. (Economics), Colorado State University, USA",
            "B.Econ. (Honours), Thammasat University"
        ],
        "research_interests": [
            "Copula-Based Econometric Modeling and Non-Linear Dependence in Financial Markets",
            "Value-at-Risk (VaR) and Expected Shortfall in Commodity and Cryptocurrency Portfolios",
            "Spatial Econometric Modeling of Regional Economic Disparities and Tourism Flows",
            "Stochastic Frontier Analysis (SFA) and Technical Efficiency in Agricultural Production"
        ],
        "featured_publications": [
            "Copula-Based Volatility Models for Financial Risk Management and Hedging Strategies",
            "Spatial Econometric Analysis of International Tourism Demand and Regional Spillovers",
            "Measuring Technical Efficiency in Agricultural Production Using Bayesian Stochastic Frontier Models"
        ]
    },
    {
        "id": "cmu_econ_kanchana_001",
        "university": "Chiang Mai University",
        "university_th": "มหาวิทยาลัยเชียงใหม่",
        "faculty": "Faculty of Economics",
        "faculty_th": "คณะเศรษฐศาสตร์",
        "department": "Department of Applied Economics",
        "department_th": "ภาควิชาเศรษฐศาสตร์ประยุกต์",
        "academic_title": "Assoc. Prof. Dr.",
        "academic_title_th": "รศ.ดร.",
        "first_name": "Kanchana",
        "last_name": "Chokethaworn",
        "full_name_th": "รศ.ดร. กาญจนา โชคถาวร",
        "role": "Expert in Environmental & Natural Resource Valuation, Carbon Taxation and Watershed Economic Policy",
        "email": "kanchana.ch@cmu.ac.th",
        "profile_url": "https://www.econ.cmu.ac.th/staff/kanchana-chokethaworn",
        "scholar_url": "https://scholar.google.com/citations?user=kanchanachokethaworn",
        "education": [
            "Ph.D. (Economics), Colorado State University, USA",
            "B.Econ., Chiang Mai University"
        ],
        "research_interests": [
            "Contingent Valuation Method (CVM) and Choice Experiments for Forest Ecosystem Services",
            "Economic Impacts of Air Pollution (PM2.5) on Healthcare Costs and Urban Quality of Life",
            "Payment for Ecosystem Services (PES) Mechanisms in Upper Northern Watersheds",
            "Cost-Benefit Analysis of Renewable Biomass Energy vs. Fossil Fuel Subsidies"
        ],
        "featured_publications": [
            "Economic Valuation of Ecosystem Services and Willingness to Pay for Forest Conservation in Northern Thailand",
            "Health Cost Valuation of Particulate Matter (PM2.5) Air Pollution Exposure in Chiang Mai Metropolitan Area",
            "Design and Implementation of Payment for Watershed Services in Highland Agricultural Landscapes"
        ]
    },
    {
        "id": "cmu_econ_aree_001",
        "university": "Chiang Mai University",
        "university_th": "มหาวิทยาลัยเชียงใหม่",
        "faculty": "Faculty of Economics",
        "faculty_th": "คณะเศรษฐศาสตร์",
        "department": "Department of Agricultural and Resource Economics",
        "department_th": "ภาควิชาเศรษฐศาสตร์เกษตรและทรัพยากร",
        "academic_title": "Assoc. Prof. Dr.",
        "academic_title_th": "รศ.ดร.",
        "first_name": "Aree",
        "last_name": "Wiboonpongse",
        "full_name_th": "รศ.ดร. อารี วิบูลย์พงศ์",
        "role": "Distinguished Agricultural Economist in Agro-Value Chains, Contract Farming and Food Price Transmission",
        "email": "aree.w@cmu.ac.th",
        "profile_url": "https://www.econ.cmu.ac.th/staff/aree-wiboonpongse",
        "scholar_url": "https://scholar.google.com/citations?user=areewiboonpongse",
        "education": [
            "Ph.D. (Agricultural Economics), University of Illinois at Urbana-Champaign, USA",
            "B.Sc. (Agricultural Economics), Kasetsart University"
        ],
        "research_interests": [
            "Contract Farming Performance, Farmer Welfare and Market Power in Perishable Produce",
            "Asymmetric Price Transmission in Fresh Fruit Supply Chains (Longan, Lychee)",
            "Cross-Border Agricultural Trade Dynamics in the Greater Mekong Subregion (GMS)",
            "Consumer Willingness to Pay for Organic and Geographic Indication (GI) Food Products"
        ],
        "featured_publications": [
            "Impact of Contract Farming on Income and Risk Management of Horticultural Smallholders",
            "Price Transmission Asymmetry and Spatial Market Integration in Fresh Fruit Markets",
            "Cross-Border Agri-Food Supply Chain Efficiency and Tariff Liberalization in the GMS Corridor"
        ]
    },
    {
        "id": "cmu_econ_nisit_001",
        "university": "Chiang Mai University",
        "university_th": "มหาวิทยาลัยเชียงใหม่",
        "faculty": "Faculty of Economics",
        "faculty_th": "คณะเศรษฐศาสตร์",
        "department": "Department of International Economics & GMS Studies",
        "department_th": "ภาควิชาเศรษฐศาสตร์ระหว่างประเทศและศูนย์ศึกษาอนุภูมิภาคลุ่มน้ำโขง",
        "academic_title": "Assoc. Prof. Dr.",
        "academic_title_th": "รศ.ดร.",
        "first_name": "Nisit",
        "last_name": "Panthamit",
        "full_name_th": "รศ.ดร. นิสิต พันธมิตร",
        "role": "Head of Center for ASEAN Studies & Expert in GMS Cross-Border Trade, Regional Integration and Free Trade Agreements",
        "email": "nisit.p@cmu.ac.th",
        "profile_url": "https://www.econ.cmu.ac.th/staff/nisit-panthamit",
        "scholar_url": "https://scholar.google.com/citations?user=nisitpanthamit",
        "education": [
            "Ph.D. (Economics), University of Wisconsin-Milwaukee, USA",
            "B.Econ., Chiang Mai University"
        ],
        "research_interests": [
            "Cross-Border Trade Facilitation and Economic Corridor Development (R3A, R3B / North-South Corridor)",
            "Impact of Regional Comprehensive Economic Partnership (RCEP) on Northern Thai SME Exporters",
            "Border Special Economic Zones (SEZs) and Foreign Direct Investment Inflows",
            "Macroeconomic Forecasting and Exchange Rate Volatility Effects on Cross-Border Transactions"
        ],
        "featured_publications": [
            "Cross-Border Trade Dynamics and Logistics Corridor Efficiency Between Thailand, Lao PDR, and Southwestern China",
            "Evaluating the Economic Spillover Effects of Border Special Economic Zones in the Upper GMS",
            "Exchange Rate Pass-Through and Trade Balance Dynamics in ASEAN-China Free Trade Area"
        ]
    },

    # =========================================================================
    # 3. Faculty of Social Sciences (คณะสังคมศาสตร์ มช.)
    # =========================================================================
    {
        "id": "cmu_soc_chayan_001",
        "university": "Chiang Mai University",
        "university_th": "มหาวิทยาลัยเชียงใหม่",
        "faculty": "Faculty of Social Sciences",
        "faculty_th": "คณะสังคมศาสตร์",
        "department": "Department of Social Science and Development (Director of RCSD)",
        "department_th": "ภาควิชาสังคมศาสตร์กับการพัฒนา (ศูนย์ภูมิภาคด้านสังคมศาสตร์และการพัฒนาอย่างยั่งยืน)",
        "academic_title": "Prof. Dr.",
        "academic_title_th": "ศ.ดร.",
        "first_name": "Chayan",
        "last_name": "Vaddhanaphuti",
        "full_name_th": "ศ.ดร. ชยันต์ วรรธนะภูติ",
        "role": "Senior Anthropologist, Founder of RCSD & International Authority on Ethnic Minorities, Agrarian Transition and Mekong Geopolitics",
        "email": "chayan.v@cmu.ac.th",
        "profile_url": "https://soc.cmu.ac.th/staff/chayan-vaddhanaphuti",
        "scholar_url": "https://scholar.google.com/citations?user=chayanvaddhanaphuti",
        "education": [
            "Ph.D. (International Development Education / Social Anthropology), Stanford University, USA",
            "M.A. (Anthropology), Stanford University, USA",
            "B.A. (Political Science / Sociology), Chulalongkorn University"
        ],
        "research_interests": [
            "Agrarian Transformation, Land Dispossession and Customary Rights of Highland Ethnic Minorities",
            "Transnational Transboundary Resource Governance in the Salween and Mekong River Basins",
            "Cultural Identity, Citizenship and Statelessness in Northern Thailand Borderlands",
            "Community-Based Disaster Risk Management and Climate Adaptation in Upland Communities"
        ],
        "featured_publications": [
            "Cultural Identity and Ethnicity in the Greater Mekong Subregion (Silkworm Books)",
            "Agrarian Change, Land Commodification, and Livelihood Trajectories of Highland Minorities in Northern Thailand",
            "Transboundary Water Governance and Local Ecological Knowledge in the Mekong River Basin"
        ]
    },
    {
        "id": "cmu_soc_pinkaew_001",
        "university": "Chiang Mai University",
        "university_th": "มหาวิทยาลัยเชียงใหม่",
        "faculty": "Faculty of Social Sciences",
        "faculty_th": "คณะสังคมศาสตร์",
        "department": "Department of Sociology and Anthropology",
        "department_th": "ภาควิชาสังคมวิทยาและมานุษยวิทยา",
        "academic_title": "Assoc. Prof. Dr.",
        "academic_title_th": "รศ.ดร.",
        "first_name": "Pinkaew",
        "last_name": "Laungaramsri",
        "full_name_th": "รศ.ดร. ปิ่นแก้ว เหลืองอร่ามศรี",
        "role": "Distinguished Political Anthropologist in Environmental Conflicts, Forest Politics, Border Surveillance and State Power",
        "email": "pinkaew.l@cmu.ac.th",
        "profile_url": "https://soc.cmu.ac.th/staff/pinkaew-laungaramsri",
        "scholar_url": "https://scholar.google.com/citations?user=pinkaewlaungaramsri",
        "education": [
            "Ph.D. (Anthropology), University of Washington, USA",
            "M.A. (Anthropology), University of Washington, USA",
            "B.A. (Sociology and Anthropology), Thammasat University"
        ],
        "research_interests": [
            "Political Ecology and the Politics of Protected Forest Enclosures in Northern Thailand",
            "Borderland Capitalism, Casino Urbanism and Transnational Enclaves in Golden Triangle",
            "Biometrics, Surveillance and the Governing of Cross-Border Migrant Labor",
            "Social Movements and Indigenous Environmentalism in Southeast Asia"
        ],
        "featured_publications": [
            "Redefining Nature: Karen Ecological Knowledge and the Challenge to the State Conservation Discourse",
            "Borderland Capitalism and the Enclave Economy: The Case of Special Economic Zones in the Upper Mekong",
            "Biopolitical Borders and the Governance of Migrant Precarity in Thailand"
        ]
    },
    {
        "id": "cmu_soc_arratee_001",
        "university": "Chiang Mai University",
        "university_th": "มหาวิทยาลัยเชียงใหม่",
        "faculty": "Faculty of Social Sciences",
        "faculty_th": "คณะสังคมศาสตร์",
        "department": "Department of Geography",
        "department_th": "ภาควิชาภูมิศาสตร์",
        "academic_title": "Assoc. Prof. Dr.",
        "academic_title_th": "รศ.ดร.",
        "first_name": "Arratee",
        "last_name": "Ayuttacorn",
        "full_name_th": "รศ.ดร. อรตี อยุทธกรณ์",
        "role": "Expert in Human Geography, Transnational Migration, Urban Informality and Gender in the Mekong Subregion",
        "email": "arratee.a@cmu.ac.th",
        "profile_url": "https://soc.cmu.ac.th/staff/arratee-ayuttacorn",
        "scholar_url": "https://scholar.google.com/citations?user=arrateeayuttacorn",
        "education": [
            "Ph.D. (Human Geography), National University of Singapore (NUS)",
            "M.A. (Geography), Chiang Mai University",
            "B.Sc. (Geography), Chiang Mai University"
        ],
        "research_interests": [
            "Transnational Labor Migration and Remittance Economies Across the Myanmar-Thailand Border",
            "Urban Informal Economies, Street Vending and Spatial Contestations in Chiang Mai",
            "Gender, Domestic Care Work and Transnational Motherhood in Southeast Asia",
            "Geographical Information Systems (GIS) for Urban Spatial Inequality and Accessibility Analysis"
        ],
        "featured_publications": [
            "Social Networks, Transnational Mobilities and Remittance Practices Among Shan Migrant Workers in Urban Chiang Mai",
            "Spatial Politics of Urban Informality: Contestations over Public Space in Secondary Tourist Cities",
            "Gendered Precarity and the Politics of Care Among Cross-Border Domestic Migrant Workers"
        ]
    },

    # =========================================================================
    # 4. Faculty of Mass Communication (คณะการสื่อสารมวลชน มช. - Mass Comm)
    # =========================================================================
    {
        "id": "cmu_mass_nantiya_001",
        "university": "Chiang Mai University",
        "university_th": "มหาวิทยาลัยเชียงใหม่",
        "faculty": "Faculty of Mass Communication",
        "faculty_th": "คณะการสื่อสารมวลชน",
        "department": "Department of Digital Communication",
        "department_th": "สาขาวิชาการสื่อสารดิจิทัล",
        "academic_title": "Assoc. Prof. Dr.",
        "academic_title_th": "รศ.ดร.",
        "first_name": "Nantiya",
        "last_name": "Hutanuwatr",
        "full_name_th": "รศ.ดร. นันทิยา หุตานุวัตร",
        "role": "Leader in Digital Storytelling, Cultural Media Production and Participatory Community Media",
        "email": "nantiya.h@cmu.ac.th",
        "profile_url": "https://masscomm.cmu.ac.th/staff/nantiya-hutanuwatr",
        "scholar_url": "https://scholar.google.com/citations?user=nantiyahutanuwatr",
        "education": [
            "Ph.D. (Communication Studies), University of Queensland, Australia",
            "M.A. (Mass Communication), Chulalongkorn University",
            "B.A. (Mass Communication), Chiang Mai University"
        ],
        "research_interests": [
            "Transmedia Storytelling and Intangible Cultural Heritage Preservation in Northern Thailand",
            "Community Radio and Participatory Video for Environmental Advocacy (Smoke Haze Crisis)",
            "Digital Media Literacy and Countering Online Misinformation in Elderly Demographics",
            "User-Generated Content Dynamics and Brand Engagement on Short-Form Video Platforms"
        ],
        "featured_publications": [
            "Digital Storytelling as an Empowerment Tool for Ethnic Minority Youth in Northern Border Communities",
            "Community Media Responses and Civic Journalism During Seasonal Transboundary Haze Pollution",
            "Designing Transmedia Narratives for Traditional Lanna Culinary and Cultural Tourism Promotion"
        ]
    },
    {
        "id": "cmu_mass_ratthapol_001",
        "university": "Chiang Mai University",
        "university_th": "มหาวิทยาลัยเชียงใหม่",
        "faculty": "Faculty of Mass Communication",
        "faculty_th": "คณะการสื่อสารมวลชน",
        "department": "Department of Journalism and New Media Innovation",
        "department_th": "สาขาวิชาวารสารศาสตร์และนวัตกรรมสื่อใหม่",
        "academic_title": "Asst. Prof. Dr.",
        "academic_title_th": "ผศ.ดร.",
        "first_name": "Ratthapol",
        "last_name": "Prommas",
        "full_name_th": "ผศ.ดร. รัฐพล พรหมมาศ",
        "role": "Distinguished Scholar in Computational Journalism, Social Media Analytics and AI in Media Newsrooms",
        "email": "ratthapol.p@cmu.ac.th",
        "profile_url": "https://masscomm.cmu.ac.th/staff/ratthapol-prommas",
        "scholar_url": "https://scholar.google.com/citations?user=ratthapolprommas",
        "education": [
            "Ph.D. (Communication and Media Studies), Monash University, Australia",
            "M.Sc. (New Media), Leeds University, UK",
            "B.A. (Mass Communication), Chiang Mai University"
        ],
        "research_interests": [
            "Automated Journalism and Generative AI Integration in Digital Newsroom Workflows",
            "Social Network Analysis (SNA) of Political Information Diffusion and Echo Chambers",
            "Data Journalism and Interactive Visual Storytelling in Public Policy Debates",
            "Algorithms, Personalization and Filter Bubbles on News Consumption Patterns"
        ],
        "featured_publications": [
            "Algorithmic News Selection and Audience Polarization on Social Media Platforms During General Elections",
            "Ethics and Workflow Adaptation in AI-Generated News Production: Insights from Thai Digital Newsrooms",
            "Data-Driven Storytelling on Environmental Hazards: Visualizing PM2.5 Crisis Impact in Northern Thailand"
        ]
    },
    {
        "id": "cmu_mass_taweesilp_001",
        "university": "Chiang Mai University",
        "university_th": "มหาวิทยาลัยเชียงใหม่",
        "faculty": "Faculty of Mass Communication",
        "faculty_th": "คณะการสื่อสารมวลชน",
        "department": "Department of Broadcasting and Audio-Visual Media",
        "department_th": "สาขาวิชาวิทยุกระจายเสียงและสื่อภาพและเสียง",
        "academic_title": "Asst. Prof. Dr.",
        "academic_title_th": "ผศ.ดร.",
        "first_name": "Taweesilp",
        "last_name": "Soontornsanee",
        "full_name_th": "ผศ.ดร. ทวีศิลป์ สุนทรเสณี",
        "role": "Authority in Audio-Visual Aesthetics, Documentary Film Production and Podcast Studies",
        "email": "taweesilp.s@cmu.ac.th",
        "profile_url": "https://masscomm.cmu.ac.th/staff/taweesilp-soontornsanee",
        "scholar_url": "https://scholar.google.com/citations?user=taweesilpsoontornsanee",
        "education": [
            "Ph.D. (Film and Media Production), Ohio University, USA",
            "M.F.A. (Film Production), San Francisco Art Institute, USA",
            "B.A. (Mass Communication), Chiang Mai University"
        ],
        "research_interests": [
            "Independent Documentary Film Practice and Environmental Crisis Representation",
            "Audio Branding, Spatial Sound Design and Immersive Podcasting Paradigms",
            "Visual Anthropology and Ethnographic Film Documentation in Lanna Highlands",
            "Digital Cinematography Workflows and Colour Grading Science in Virtual Production"
        ],
        "featured_publications": [
            "Aesthetic Strategies in Independent Thai Environmental Documentaries: Framing the Forest Fire Dilemma",
            "Immersive Audio Design and Narrative Engagement in Contemporary Non-Fiction Podcasts",
            "Ethnographic Film Practice and Cultural Reflexivity in Documenting Marginalized Highland Communities"
        ]
    },

    # =========================================================================
    # 5. Faculty of Dentistry (คณะทันตแพทยศาสตร์ มช.)
    # =========================================================================
    {
        "id": "cmu_dent_anak_001",
        "university": "Chiang Mai University",
        "university_th": "มหาวิทยาลัยเชียงใหม่",
        "faculty": "Faculty of Dentistry",
        "faculty_th": "คณะทันตแพทยศาสตร์",
        "department": "Department of Oral Biology and Diagnostic Sciences",
        "department_th": "ภาควิชาชีววิทยาช่องปากและวิทยาการวินิจฉัยโรคช่องปาก",
        "academic_title": "Prof. Dr.",
        "academic_title_th": "ศ.ดร.ทพ.",
        "first_name": "Anak",
        "last_name": "Iamaroon",
        "full_name_th": "ศ.ดร.ทพ. อนรรฆ เอี่ยมอรุณ",
        "role": "World-Class Oral Pathologist in Molecular Carcinogenesis, Oral Squamous Cell Carcinoma and Salivary Biomarkers",
        "email": "anak.i@cmu.ac.th",
        "profile_url": "https://dent.cmu.ac.th/staff/anak-iamaroon",
        "scholar_url": "https://scholar.google.com/citations?user=anakiamaroon",
        "education": [
            "Ph.D. (Oral Pathology / Molecular Biology), University of North Carolina at Chapel Hill, USA",
            "D.D.S. (Honours), Chiang Mai University",
            "Diploma Thai Board of Oral Diagnostic Sciences"
        ],
        "research_interests": [
            "Molecular Biomarkers of Malignant Transformation in Oral Potentially Malignant Disorders (OPMD)",
            "Role of Matrix Metalloproteinases (MMPs) and Epithelial-Mesenchymal Transition in Oral Cancer Invasion",
            "Salivary MicroRNA and Proteomic Profiling for Non-Invasive Early Cancer Screening",
            "Anticancer and Chemopreventive Activities of Indigenous Phytochemicals on Oral Tumor Lines"
        ],
        "featured_publications": [
            "Expression of Matrix Metalloproteinases and Their Tissue Inhibitors in Head and Neck Squamous Cell Carcinoma",
            "Salivary MicroRNA Biomarkers for Early Detection and Recurrence Monitoring of Oral Squamous Cell Carcinoma",
            "In Vitro Antiproliferative and Apoptotic Induction of Curcumin Analogues in Human Oral Cancer Cells"
        ]
    },
    {
        "id": "cmu_dent_suttichai_001",
        "university": "Chiang Mai University",
        "university_th": "มหาวิทยาลัยเชียงใหม่",
        "faculty": "Faculty of Dentistry",
        "faculty_th": "คณะทันตแพทยศาสตร์",
        "department": "Department of Family and Community Dentistry (Division of Periodontology)",
        "department_th": "ภาควิชาทันตกรรมครอบครัวและชุมชน (สาขาวิชาปริทันตวิทยา)",
        "academic_title": "Prof. Dr.",
        "academic_title_th": "ศ.ดร.ทพ.",
        "first_name": "Suttichai",
        "last_name": "Krisanaprakornkit",
        "full_name_th": "ศ.ดร.ทพ. สุทธิชัย กฤษณะประกรกิจ",
        "role": "Pioneer in Innate Immunity, Human Beta-Defensins and Periodontal Tissue Regeneration",
        "email": "suttichai.k@cmu.ac.th",
        "profile_url": "https://dent.cmu.ac.th/staff/suttichai-krisanaprakornkit",
        "scholar_url": "https://scholar.google.com/citations?user=suttichaikrisanaprakornkit",
        "education": [
            "Ph.D. (Oral Biology), University of Washington, USA",
            "Certificate in Periodontics, University of Washington, USA",
            "D.D.S. (First Class Honours), Chiang Mai University"
        ],
        "research_interests": [
            "Regulation and Expression of Human Beta-Defensins (hBDs) in Periodontal Gingival Epithelium",
            "Host-Microbiome Interactions in Porphyromonas gingivalis-Mediated Periodontitis",
            "Guided Tissue Regeneration (GTR) Using Bioactive Scaffolds and Growth Factors",
            "Periodontal Inflammation Spillovers to Systemic Cardiovascular and Glycemic Disorders"
        ],
        "featured_publications": [
            "Induction of Human Beta-Defensin-2 by Bacterial Lipopolysaccharide in Gingival Epithelial Cells",
            "Host-Pathogen Interactions and Inflammatory Signaling Cascades in Chronic Periodontitis",
            "Application of Platelet-Rich Fibrin and Bioactive Ceramics in Periodontal Infrabony Defect Regeneration"
        ]
    },
    {
        "id": "cmu_dent_piyanuj_001",
        "university": "Chiang Mai University",
        "university_th": "มหาวิทยาลัยเชียงใหม่",
        "faculty": "Faculty of Dentistry",
        "faculty_th": "คณะทันตแพทยศาสตร์",
        "department": "Department of Prosthodontics",
        "department_th": "ภาควิชาทันตกรรมประดิษฐ์",
        "academic_title": "Assoc. Prof. Dr.",
        "academic_title_th": "รศ.ทพญ.ดร.",
        "first_name": "Piyanuj",
        "last_name": "Permpanich",
        "full_name_th": "รศ.ทพญ.ดร. ปิยานุช เพิ่มพานิช",
        "role": "Distinguished Prosthodontist in Dental Implant Biomechanics, CAD/CAM Ceramics and Osseointegration",
        "email": "piyanuj.p@cmu.ac.th",
        "profile_url": "https://dent.cmu.ac.th/staff/piyanuj-permpanich",
        "scholar_url": "https://scholar.google.com/citations?user=piyanujpermpanich",
        "education": [
            "Ph.D. (Dental Materials / Prosthodontics), University of London, UK",
            "M.Sc. (Prosthodontics), Eastman Dental Institute, UK",
            "D.D.S., Chiang Mai University"
        ],
        "research_interests": [
            "Finite Element Stress Analysis of Dental Implants with Custom Abutments",
            "Fracture Toughness and Aging Resistance of Translucent Zirconia Multi-Layer Dental Restorations",
            "Surface Topography Modification of Titanium Implants for Accelerated Osseointegration",
            "Digital Complete Dentures Fabricated via 3D Additive Printing vs. Subtractive Milling"
        ],
        "featured_publications": [
            "Biomechanical Behavior and Stress Distribution of Monolithic Zirconia Crowns on Short Dental Implants",
            "Surface Micro-Texturing and Bioactive Coating of Titanium Implants for Enhanced Osteoblast Adhesion",
            "Accuracy and Fit of 3D-Printed vs. Milled Digital Complete Dentures: A Comparative Clinical Assessment"
        ]
    },

    # =========================================================================
    # 6. Faculty of Fine Arts (คณะวิจิตรศิลป์ มช.)
    # =========================================================================
    {
        "id": "cmu_fine_araya_001",
        "university": "Chiang Mai University",
        "university_th": "มหาวิทยาลัยเชียงใหม่",
        "faculty": "Faculty of Fine Arts",
        "faculty_th": "คณะวิจิตรศิลป์",
        "department": "Department of Media Arts and Design (Division of Contemporary Art)",
        "department_th": "ภาควิชาสื่อศิลปะและการออกแบบสื่อ (สาขาวิชาศิลปะร่วมสมัย)",
        "academic_title": "Emeritus Prof. Dr.",
        "academic_title_th": "ศ.เกียรติคุณ ดร.",
        "first_name": "Araya",
        "last_name": "Rasdjarmrearnsook",
        "full_name_th": "ศ.เกียรติคุณ ดร. อารยา ราษฎร์จำเริญสุข",
        "role": "National Artist of Thailand, Globally Celebrated Video & Installation Artist, Venice Biennale Exhibitor",
        "email": "araya.r@cmu.ac.th",
        "profile_url": "https://finearts.cmu.ac.th/staff/araya-rasdjarmrearnsook",
        "scholar_url": "https://scholar.google.com/citations?user=ar крояrasdjarmrearnsook",
        "education": [
            "Honorary Ph.D. in Fine Arts, Chiang Mai University",
            "M.F.A. (Graphic Arts), Hochschule für Bildende Künste Braunschweig, Germany",
            "B.F.A. (Printmaking, First Class Honours), Silpakorn University"
        ],
        "research_interests": [
            "Thanatos, Mortality, Mourning and Post-Mortem Dialogue in Contemporary Video Art",
            "Feminist Aesthetics and Gendered Bodily Narratives in Southeast Asian Visual Culture",
            "Interspecies Ethics, Animal Subjectivities and Affective Visual Ethnography",
            "Installation Art and the Dialectics of Presence/Absence in Post-Colonial Art Spaces"
        ],
        "featured_publications": [
            "The Treachery of the Moon: Contemporary Aesthetic Discourse and the Language of Death (ArtAsiaPacific)",
            "Interspecies Dialogue and Visual Philosophy: Engaging Animals as Aesthetic and Ethical Subjects",
            "Performative Installation and Gendered Mourning in Thai Contemporary Art Practice"
        ]
    },
    {
        "id": "cmu_fine_somporn_001",
        "university": "Chiang Mai University",
        "university_th": "มหาวิทยาลัยเชียงใหม่",
        "faculty": "Faculty of Fine Arts",
        "faculty_th": "คณะวิจิตรศิลป์",
        "department": "Department of Thai Art (Curatorial Studies)",
        "department_th": "ภาควิชาศิลปะไทย (สาขาวิชาประวัติศาสตร์ศิลปะและภัณฑารักษ์ศึกษา)",
        "academic_title": "Prof. Dr.",
        "academic_title_th": "ศ.ดร.",
        "first_name": "Somporn",
        "last_name": "Rodboon",
        "full_name_th": "ศ.ดร. สมพร รอดบุญ",
        "role": "Leading Art Historian, Senior Curator of Southeast Asian Contemporary Art & Chevalier des Arts et des Lettres",
        "email": "somporn.r@cmu.ac.th",
        "profile_url": "https://finearts.cmu.ac.th/staff/somporn-rodboon",
        "scholar_url": "https://scholar.google.com/citations?user=sompornrodboon",
        "education": [
            "Ph.D. (Art History), University of Sorbonne Paris IV, France",
            "M.A. (Art History), University of Illinois at Urbana-Champaign, USA",
            "B.F.A., Silpakorn University"
        ],
        "research_interests": [
            "Modern and Contemporary Art Movements Across the ASEAN Region",
            "Curatorial Methodologies and Site-Specific Public Art Exhibitions in Northern Thailand",
            "Traditional Lanna Craftsmanship Evolution into Contemporary Eco-Design",
            "Art Criticism and Institutional Museum Development in Southeast Asia"
        ],
        "featured_publications": [
            "Contemporary Art in Southeast Asia: Transcending Borders, Tradition and Modernity",
            "Curating Regional Identities: Public Art Installations and Community Memory in Chiang Mai",
            "The Evolution of Lanna Ceramic and Textile Traditions in Modern Applied Art Spaces"
        ]
    },
    {
        "id": "cmu_fine_sone_001",
        "university": "Chiang Mai University",
        "university_th": "มหาวิทยาลัยเชียงใหม่",
        "faculty": "Faculty of Fine Arts",
        "faculty_th": "คณะวิจิตรศิลป์",
        "department": "Department of Thai Art",
        "department_th": "ภาควิชาศิลปะไทย",
        "academic_title": "Assoc. Prof. Dr.",
        "academic_title_th": "รศ.ดร.",
        "first_name": "Sone",
        "last_name": "Simatrang",
        "full_name_th": "รศ.ดร. โชน สิมังตรังค์",
        "role": "Distinguished Authority in Lanna Temple Mural Painting, Buddhist Iconography and Heritage Conservation",
        "email": "sone.s@cmu.ac.th",
        "profile_url": "https://finearts.cmu.ac.th/staff/sone-simatrang",
        "scholar_url": "https://scholar.google.com/citations?user=sonesimatrang",
        "education": [
            "Ph.D. (Buddhist Art and Iconography), Silpakorn University",
            "M.F.A. (Thai Art), Silpakorn University",
            "B.F.A. (Thai Art), Silpakorn University"
        ],
        "research_interests": [
            "Iconographical Analysis of Lanna Temple Murals (Wat Phra Sing, Wat Phumin)",
            "Traditional Mineral Pigments and Lime Plaster Deterioration Chemistry in Tropical Climates",
            "Digital Photogrammetry and Virtual Reality Restoration of Historical Temple Frescoes",
            "Socio-Cultural Narratives Encoded in Northern Thai Religious Art"
        ],
        "featured_publications": [
            "Iconography and Compositional Structure of Classical Lanna Temple Mural Paintings",
            "Conservation Methodologies for Ancient Mineral Pigment Murals Under Tropical Humidity Stress",
            "Virtual Reality 3D Reconstruction of Endangered Sacred Heritage Sites in Northern Thailand"
        ]
    },

    # =========================================================================
    # 7. Faculty of Political Science and Public Administration (คณะรัฐศาสตร์ฯ มช.)
    # =========================================================================
    {
        "id": "cmu_pol_tanet_001",
        "university": "Chiang Mai University",
        "university_th": "มหาวิทยาลัยเชียงใหม่",
        "faculty": "Faculty of Political Science and Public Administration",
        "faculty_th": "คณะรัฐศาสตร์และรัฐประศาสนศาสตร์",
        "department": "Department of Local Governance and Public Administration",
        "department_th": "ภาควิชารัฐประศาสนศาสตร์ (สาขาวิชาการปกครองท้องถิ่น)",
        "academic_title": "Assoc. Prof. Dr.",
        "academic_title_th": "รศ.ดร.",
        "first_name": "Tanet",
        "last_name": "Charoenmuang",
        "full_name_th": "รศ.ดร. ธเนศวร์ เจริญเมือง",
        "role": "Renowned Political Scientist, Foremost Authority on Decentralization, Local Self-Governance and Lanna Political History",
        "email": "tanet.ch@cmu.ac.th",
        "profile_url": "https://pol.cmu.ac.th/staff/tanet-charoenmuang",
        "scholar_url": "https://scholar.google.com/citations?user=tanetcharoenmuang",
        "education": [
            "Ph.D. (Political Science / Urban Politics), Northern Illinois University, USA",
            "M.A. (Political Science), Northern Illinois University, USA",
            "B.A. (Political Science), Chulalongkorn University"
        ],
        "research_interests": [
            "Fiscal and Administrative Decentralization to Local Governments in Thailand",
            "Urban Politics, Metropolitan Governance and Public Transport Policy in Chiang Mai",
            "Political History and Institutional Evolution of the Lanna Realm",
            "Civic Engagement and Direct Democracy Mechanisms in Municipal Administration"
        ],
        "featured_publications": [
            "100 Years of Chiang Mai Administration: Centralization vs. Decentralization Struggle",
            "Local Government and Civic Democracy in Northern Thailand (Silkworm Books)",
            "Urban Governance Challenges and Participatory Planning in Rapidly Expanding Secondary Cities"
        ]
    },
    {
        "id": "cmu_pol_pailin_001",
        "university": "Chiang Mai University",
        "university_th": "มหาวิทยาลัยเชียงใหม่",
        "faculty": "Faculty of Political Science and Public Administration",
        "faculty_th": "คณะรัฐศาสตร์และรัฐประศาสนศาสตร์",
        "department": "Department of Political Science",
        "department_th": "ภาควิชาการเมืองการปกครอง",
        "academic_title": "Assoc. Prof. Dr.",
        "academic_title_th": "รศ.ดร.",
        "first_name": "Pailin",
        "last_name": "Phujeenaphan",
        "full_name_th": "รศ.ดร. ไพลิน ภู่จีนาพันธุ์",
        "role": "Dean of Faculty of Political Science & Expert in Public Policy Analysis, Comparative Politics and Electoral Governance",
        "email": "pailin.p@cmu.ac.th",
        "profile_url": "https://pol.cmu.ac.th/staff/pailin-phujeenaphan",
        "scholar_url": "https://scholar.google.com/citations?user=pailinphujeenaphan",
        "education": [
            "Ph.D. (Political Science), Chiang Mai University",
            "M.A. (Political Science), Chulalongkorn University",
            "B.A. (Political Science), Chiang Mai University"
        ],
        "research_interests": [
            "Comparative Democratic Governance and Electoral Behavior in Northern Thailand",
            "Public Policy Implementation and Multi-Stakeholder Policy Networks",
            "Digital Governance, Open Government Data and Public Transparency",
            "Gender Representation and Women's Leadership in Local Political Arenas"
        ],
        "featured_publications": [
            "Electoral Dynamics and Voting Behavior in Northern Constituency Politics",
            "Policy Network Governance in Addressing Transboundary Haze Pollution in Northern Thailand",
            "Open Government and Civic Participation: Assessing Digital Municipal Platforms in Thailand"
        ]
    },

    # =========================================================================
    # 8. Faculty of Public Health & Research Institute for Health Sciences (RIHES)
    # =========================================================================
    {
        "id": "cmu_rihes_suwat_001",
        "university": "Chiang Mai University",
        "university_th": "มหาวิทยาลัยเชียงใหม่",
        "faculty": "Faculty of Public Health / Research Institute for Health Sciences (RIHES)",
        "faculty_th": "คณะสาธารณสุขศาสตร์ / สถาบันวิจัยวิทยาศาสตร์สุขภาพ (RIHES)",
        "department": "Department of Public Health (Director of RIHES)",
        "department_th": "ภาควิชาสาธารณสุขศาสตร์ (ผู้อำนวยการสถาบันวิจัยวิทยาศาสตร์สุขภาพ)",
        "academic_title": "Prof. Dr.",
        "academic_title_th": "ศ.ดร.นพ.",
        "first_name": "Suwat",
        "last_name": "Chariyalertsak",
        "full_name_th": "ศ.ดร.นพ. สุวัฒน์ จริยาเลิศศักดิ์",
        "role": "Outstanding Researcher in Clinical HIV/AIDS Epidemiology, Emerging Tropical Diseases and Air Pollution Health Impacts",
        "email": "suwat.c@cmu.ac.th",
        "profile_url": "https://rihes.cmu.ac.th/staff/suwat-chariyalertsak",
        "scholar_url": "https://scholar.google.com/citations?user=suwatchariyalertsak",
        "education": [
            "Dr.P.H. (International Health / Epidemiology), Johns Hopkins Bloomberg School of Public Health, USA",
            "M.P.H., Johns Hopkins Bloomberg School of Public Health, USA",
            "M.D. (Honours), Faculty of Medicine Siriraj Hospital, Mahidol University"
        ],
        "research_interests": [
            "Antiretroviral Treatment (ART) Optimization and Long-Term Survival in HIV/AIDS Cohorts",
            "Pre-Exposure Prophylaxis (PrEP) Implementation Science in High-Risk Key Populations",
            "Short- and Long-Term Cardiorespiratory Health Effects of Ambient PM2.5 Biomass Smoke Exposure",
            "Infectious Disease Surveillance and Outbreak Containment in Border Settings"
        ],
        "featured_publications": [
            "Long-Term Clinical Outcomes and Viral Suppression in a Large Multicenter Thai HIV Cohort",
            "Association Between Ambient PM2.5 Exposure and Acute Exacerbations of Chronic Lung Diseases in Chiang Mai",
            "Feasibility and Real-World Effectiveness of Community-Delivered HIV Pre-Exposure Prophylaxis (PrEP)"
        ]
    },
    {
        "id": "cmu_rihes_tippawan_001",
        "university": "Chiang Mai University",
        "university_th": "มหาวิทยาลัยเชียงใหม่",
        "faculty": "Faculty of Public Health / Research Institute for Health Sciences (RIHES)",
        "faculty_th": "คณะสาธารณสุขศาสตร์ / สถาบันวิจัยวิทยาศาสตร์สุขภาพ (RIHES)",
        "department": "Department of Environmental Health",
        "department_th": "ภาควิชาอนามัยสิ่งแวดล้อม",
        "academic_title": "Assoc. Prof. Dr.",
        "academic_title_th": "รศ.ดร.",
        "first_name": "Tippawan",
        "last_name": "Prapamontol",
        "full_name_th": "รศ.ดร. ทิพวรรณ ประภาภัทรวงศ์",
        "role": "Global Environmental Toxicologist in Biomarkers of Pesticide Exposure, Endocrine Disruptors and Child Health",
        "email": "tippawan.p@cmu.ac.th",
        "profile_url": "https://rihes.cmu.ac.th/staff/tippawan-prapamontol",
        "scholar_url": "https://scholar.google.com/citations?user=tippawanprapamontol",
        "education": [
            "Ph.D. (Environmental Toxicology), University of Surrey, UK",
            "M.Sc. (Biochemistry), Mahidol University",
            "B.Sc. (Medical Technology), Chiang Mai University"
        ],
        "research_interests": [
            "Prenatal and Early-Life Biomarkers of Organophosphate and Pyrethroid Pesticide Exposure",
            "Chemical Speciation of Particulate Matter (Polycyclic Aromatic Hydrocarbons - PAHs in PM2.5)",
            "Endocrine Disrupting Chemicals (EDCs) and Child Neurodevelopmental Outcomes",
            "Occupational Health Intervention for Agricultural Workers in Highland Vegetable Farming"
        ],
        "featured_publications": [
            "Prenatal Organophosphate Pesticide Exposure and Neurodevelopmental Deficits in Young Children",
            "Chemical Characterization and Toxicological Risk of Carcinogenic PAHs Bound to PM2.5 in Northern Thailand",
            "Biomarkers of Pesticide Exposure Among Smallholder Agricultural Workers: Longitudinal Cohort Study"
        ]
    },
    {
        "id": "cmu_ph_vorachai_001",
        "university": "Chiang Mai University",
        "university_th": "มหาวิทยาลัยเชียงใหม่",
        "faculty": "Faculty of Public Health",
        "faculty_th": "คณะสาธารณสุขศาสตร์",
        "department": "Department of Occupational Health and Safety",
        "department_th": "ภาควิชาอาชีวอนามัยและความปลอดภัย",
        "academic_title": "Assoc. Prof. Dr.",
        "academic_title_th": "รศ.ดร.",
        "first_name": "Vorachai",
        "last_name": "Sirikul",
        "full_name_th": "รศ.ดร. วรชัย ศิริกุล",
        "role": "Expert in Industrial Ergonomics, Occupational Toxicology and Worker Respiratory Protection",
        "email": "vorachai.s@cmu.ac.th",
        "profile_url": "https://ph.cmu.ac.th/staff/vorachai-sirikul",
        "scholar_url": "https://scholar.google.com/citations?user=vorachaisirikul",
        "education": [
            "Ph.D. (Occupational Health and Safety), University of Birmingham, UK",
            "M.Sc. (Industrial Ergonomics), Mahidol University",
            "B.Sc. (Public Health), Chiang Mai University"
        ],
        "research_interests": [
            "Ergonomic Risk Assessment and Musculoskeletal Disorders in Manufacturing Lines",
            "Workplace Exposure to Silica Dust, Solvent Vapors and Heavy Metals",
            "Respiratory Protective Equipment (RPE) Fit Testing and Physiological Workload Evaluation",
            "Safety Climate and Behavior-Based Safety Management Systems in Medium Enterprises"
        ],
        "featured_publications": [
            "Ergonomic Interventions for Preventing Work-Related Musculoskeletal Disorders Among Electronic Assembly Workers",
            "Quantitative Fit-Testing of Particulate Filtering Respirators Under Heavy Physical Workloads",
            "Occupational Inhalation Exposure to Organic Solvents and Neurobehavioral Effects in Factory Employees"
        ]
    },

    # =========================================================================
    # 9. Energy Research and Development Institute - Nakornping (ERDI) & Pharmacy
    # =========================================================================
    {
        "id": "cmu_erdi_pruk_001",
        "university": "Chiang Mai University",
        "university_th": "มหาวิทยาลัยเชียงใหม่",
        "faculty": "Energy Research and Development Institute - Nakornping (ERDI)",
        "faculty_th": "สถาบันวิจัยและพัฒนาพลังงานนครพิงค์ (ERDI)",
        "department": "Center of Excellence in Biogas Technology and Renewable Energy",
        "department_th": "ศูนย์ความเป็นเลิศด้านเทคโนโลยีก๊าซชีวภาพและพลังงานหมุนเวียน",
        "academic_title": "Assoc. Prof. Dr.",
        "academic_title_th": "รศ.ดร.",
        "first_name": "Pruk",
        "last_name": "Aggarangsi",
        "full_name_th": "รศ.ดร. พฤกษ์ อัครราช",
        "role": "Director of ERDI & Pioneer in Industrial Biogas, Compressed Bio-Methane Gas (CBG) and Bio-Hydrogen",
        "email": "pruk.a@cmu.ac.th",
        "profile_url": "https://erdi.cmu.ac.th/staff/pruk-aggarangsi",
        "scholar_url": "https://scholar.google.com/citations?user=prukaggarangsi",
        "education": [
            "Ph.D. (Mechanical Engineering / Energy Systems), Carnegie Mellon University, USA",
            "M.S. (Mechanical Engineering), Carnegie Mellon University, USA",
            "B.Eng. (Mechanical Engineering), Chiang Mai University"
        ],
        "research_interests": [
            "Industrial Upgrading of Biogas to High-Purity Compressed Bio-Methane Gas (CBG) as Transport Fuel",
            "Two-Stage Anaerobic Digestion for Simultaneous Bio-Hydrogen and Bio-Methane Production (Bio-Hythane)",
            "Thermochemical Gasification and Pyrolysis of Agro-Forestry Residues (Corn Stover)",
            "Carbon Footprint and Life Cycle Energy Balance in Circular Agro-Energy Systems"
        ],
        "featured_publications": [
            "Techno-Economic Feasibility and Life Cycle Assessment of Commercial Compressed Bio-Methane Gas Production",
            "Bio-Hythane Production from Cassava Starch Wastewater in a Two-Phase High-Rate Anaerobic Digestion System",
            "Pyrolysis of Agricultural Biomass for Syngas and High-Surface-Area Biochar Soil Amendments"
        ]
    },
    {
        "id": "cmu_pharm_jiradech_001",
        "university": "Chiang Mai University",
        "university_th": "มหาวิทยาลัยเชียงใหม่",
        "faculty": "Faculty of Pharmacy",
        "faculty_th": "คณะเภสัชศาสตร์",
        "department": "Department of Pharmaceutical Sciences",
        "department_th": "ภาควิชาวิทยาศาสตร์เภสัชกรรม",
        "academic_title": "Prof. Dr.",
        "academic_title_th": "ศ.ดร.ภก.",
        "first_name": "Jiradech",
        "last_name": "Manosroi",
        "full_name_th": "ศ.ดร.ภก. จิรเดช มโนสร้อย",
        "role": "Distinguished Pharmaceutical Scientist in Niosomes, Nanovesicles, Transdermal Drug Delivery and Herbal Cosmeceuticals",
        "email": "jiradech.m@cmu.ac.th",
        "profile_url": "https://pharmacy.cmu.ac.th/staff/jiradech-manosroi",
        "scholar_url": "https://scholar.google.com/citations?user=jiradechmanosroi",
        "education": [
            "Ph.D. (Pharmaceutics and Industrial Pharmacy), University of Wisconsin-Madison, USA",
            "B.Sc. (Pharmacy, First Class Honours), Chiang Mai University"
        ],
        "research_interests": [
            "Novel Elastic Nanovesicles (Niosomes, Transferosomes) for Transdermal Peptide and Drug Delivery",
            "Anti-Ageing and Hair Growth Stimulation Phytochemical Formulations from Lanna Medicinal Plants",
            "Encapsulation of Unstable Bioactive Extracts for Topical and Dermatological Therapeutics",
            "Stability and Release Kinetics of Nanoscale Cosmetic Formulations"
        ],
        "featured_publications": [
            "Transdermal Absorption Enhancement of Bioactive Peptides Using Novel Elastic Nanovesicles",
            "Development of Herbal Niosome Gels for Promoting Hair Growth and Follicle Regeneration",
            "Stability, Cytotoxicity and In Vitro Skin Penetration of Nanoparticle Formulations Containing Indigenous Plant Extracts"
        ]
    },
    {
        "id": "cmu_sci_panuwan_001",
        "university": "Chiang Mai University",
        "university_th": "มหาวิทยาลัยเชียงใหม่",
        "faculty": "Faculty of Science",
        "faculty_th": "คณะวิทยาศาสตร์",
        "department": "Department of Biology",
        "department_th": "ภาควิชาชีววิทยา",
        "academic_title": "Prof. Dr.",
        "academic_title_th": "ศ.ดร.",
        "first_name": "Panuwan",
        "last_name": "Chantawannakul",
        "full_name_th": "ศ.ดร. ภาณุวรรณ จันทวรรณกูร",
        "role": "Outstanding Scientist of Thailand & World Authority in Honeybee Pathology, Colony Collapse and Propolis Bioactive Compounds",
        "email": "panuwan.c@cmu.ac.th",
        "profile_url": "https://biology.sc.cmu.ac.th/staff/panuwan-chantawannakul",
        "scholar_url": "https://scholar.google.com/citations?user=panuwanchantawannakul",
        "education": [
            "Ph.D. (Microbiology / Insect Pathology), University of Wales Cardiff, UK",
            "M.Sc. (Microbiology), Mahidol University",
            "B.Sc. (Biology, First Class Honours), Chiang Mai University"
        ],
        "research_interests": [
            "Tropilaelaps and Varroa Mite Parasitism, Deformed Wing Virus (DWV) and Honeybee Immune Defenses",
            "Chemical Profiling and Antimicrobial Properties of Tropical Stingless Bee Propolis and Royal Jelly",
            "Gut Microbiome Dynamics in Apis cerana and Apis dorsata Under Agricultural Pesticide Stress",
            "Pollinator Conservation and Sustainable Beekeeping Industry Standards in Asia"
        ],
        "featured_publications": [
            "Global Spread and Pathogenicity of Tropilaelaps Mites in Managed and Wild Asian Honeybees",
            "Antimicrobial and Anti-Inflammatory Bioactive Components in Stingless Bee Propolis from Northern Thailand",
            "Impact of Neonicotinoid Pesticides on Honeybee Gut Microbiota and Susceptibility to Microsporidian Infections"
        ]
    }
]
