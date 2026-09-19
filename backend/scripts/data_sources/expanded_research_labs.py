# -*- coding: utf-8 -*-
"""
Curated Expanded Dataset of Premier Research Laboratories and Centers of Excellence in Thailand.
Covers 46 high-impact laboratories across Central, Northern, Northeastern, Southern, and Eastern regions.
Schema compliant with ResearchLabDB (AGENTS.md & PDPA).
"""

EXPANDED_RESEARCH_LABS = [
    # =========================================================================
    # EASTERN REGION - Burapha University (BUU - มหาวิทยาลัยบูรพา)
    # =========================================================================
    {
        "id": "buu_marine_biotech_center",
        "name_th": "สถาบันวิทยาศาสตร์ทางทะเลและเทคโนโลยีชีวภาพทางทะเล มหาวิทยาลัยบูรพา",
        "name_en": "Marine Science Institute & Marine Biotechnology Research Center (BIMS)",
        "university": "Burapha University",
        "university_th": "มหาวิทยาลัยบูรพา",
        "faculty": "Marine Science Institute",
        "faculty_th": "สถาบันวิทยาศาสตร์ทางทะเล",
        "department": "Marine Biotechnology & Aquaculture Division",
        "department_th": "สาขาเทคโนโลยีชีวภาพทางทะเลและการเพาะเลี้ยงสัตว์น้ำ",
        "lead_advisor_id": "regionalun_facultymem_amornratanaphan_011",
        "member_faculty_ids": ["regionalun_facultymem_amornratanaphan_011", "buu_ahs_narisara_001"],
        "description": "ศูนย์ความเป็นเลิศชั้นนำด้านวิทยาศาสตร์ทางทะเลในเขตพัฒนาพิเศษภาคตะวันออก (EEC) มุ่งเน้นการค้นหาสารออกฤทธิ์ทางชีวภาพจากสิ่งมีชีวิตใต้ทะเลลึก การอนุรักษ์แนวปะการัง และการประยุกต์ใช้เทคโนโลยีชีวภาพเพื่อการเพาะเลี้ยงสัตว์น้ำเศรษฐกิจ",
        "research_domains": [
            "Marine Bioactive Compounds & Drug Discovery",
            "Coral Reef Ecology & Climate Change Resilience",
            "Microalgae Biomass & Sustainable Biofuel",
            "Coastal Marine Environmental Pollution & Microplastics"
        ],
        "flagship_equipment": [
            "Liquid Chromatography-Mass Spectrometry (LC-MS/MS Triple Quad)",
            "Deep-Sea Oceanographic Sampling Remotely Operated Vehicle (ROV)",
            "Continuous Microalgae Photobioreactor System",
            "Controlled Environment Marine Organism Culture Tanks"
        ],
        "industry_partners": [
            "Department of Marine and Coastal Resources (DMCR)",
            "PTT Global Chemical (PTTGC)",
            "Charoen Pokphand Foods (CPF)",
            "Thai Union Group"
        ],
        "open_positions": [
            "Master's RA: Marine Natural Products Extraction (ทุนเต็มจำนวน)",
            "PhD Candidate: Coral Genomics under Ocean Acidification"
        ],
        "website_url": "https://bims.buu.ac.th",
        "image_url": "https://images.unsplash.com/photo-1544551763-46a013bb70d5?w=800&q=80"
    },
    {
        "id": "buu_eec_automation_smart_mfg",
        "name_th": "ศูนย์วิจัยระบบอัตโนมัติ หุ่นยนต์อุตสาหกรรม และการผลิตอัจฉริยะ EEC มหาวิทยาลัยบูรพา",
        "name_en": "EEC Automation, Industrial Robotics & Smart Manufacturing Research Center",
        "university": "Burapha University",
        "university_th": "มหาวิทยาลัยบูรพา",
        "faculty": "Faculty of Engineering",
        "faculty_th": "คณะวิศวกรรมศาสตร์",
        "department": "Department of Mechanical & Industrial Engineering",
        "department_th": "ภาควิชาวิศวกรรมเครื่องกลและอุตสาหการ",
        "lead_advisor_id": "regionalun_facultymem_amornratanaphan_011",
        "member_faculty_ids": ["regionalun_facultymem_amornratanaphan_011"],
        "description": "ศูนย์นวัตกรรมสนับสนุนอุตสาหกรรมเป้าหมาย (S-Curve) ในพื้นที่เขตเศรษฐกิจพิเศษภาคตะวันออก มุ่งเน้นการพัฒนาระบบสายการผลิตอัจฉริยะ หุ่นยนต์ร่วมปฏิบัติงาน (Cobots) และการประยุกต์ใช้ AI ในการควบคุมคุณภาพเชิงทำนาย",
        "research_domains": [
            "Industrial Internet of Things (IIoT) & Factory Digital Twin",
            "Collaborative Robotics (Cobots) in Assembly Lines",
            "Predictive Maintenance with AI & Vibration Diagnostics",
            "Additive Manufacturing & Advanced Tooling"
        ],
        "flagship_equipment": [
            "Industry 4.0 Flexible Manufacturing Testbed",
            "KUKA & UR Collaborative Robot Cell",
            "High-Speed Laser 3D Metal Sintering Machine",
            "Laser Doppler Vibrometer for Non-contact Vibration Analysis"
        ],
        "industry_partners": [
            "Mitsubishi Electric Factory Automation",
            "Eastern Economic Corridor (EEC) Office",
            "Denso Manufacturing Thailand",
            "Siam Kubota Corporation"
        ],
        "open_positions": [
            "Graduate RA in Industrial Digital Twin Systems",
            "Postdoctoral Researcher in Robotic Machine Vision"
        ],
        "website_url": "https://eng.buu.ac.th",
        "image_url": "https://images.unsplash.com/photo-1581092160607-ee22621dd758?w=800&q=80"
    },
    {
        "id": "buu_informatics_data_ai_lab",
        "name_th": "ห้องปฏิบัติการวิทยาการข้อมูล นวัตกรรมปัญญาประดิษฐ์ และความปลอดภัยไซเบอร์ มหาวิทยาลัยบูรพา",
        "name_en": "Data Science, Artificial Intelligence & Cybersecurity Innovation Laboratory",
        "university": "Burapha University",
        "university_th": "มหาวิทยาลัยบูรพา",
        "faculty": "Faculty of Informatics",
        "faculty_th": "คณะวิทยาการสารสนเทศ",
        "department": "Department of Computer Science & Intelligent Systems",
        "department_th": "ภาควิชาวิทยาการคอมพิวเตอร์และระบบสารสนเทศ",
        "lead_advisor_id": "buu_ahs_narisara_001",
        "member_faculty_ids": ["buu_ahs_narisara_001"],
        "description": "ห้องปฏิบัติการวิจัยด้านวิทยาการข้อมูลและปัญญาประดิษฐ์สำหรับเมืองอัจฉริยะ (Smart City EEC) การวิเคราะห์ข้อมูลสุขภาพเชิงพื้นที่ และการตรวจสอบความปลอดภัยทางไซเบอร์ในโครงสร้างพื้นฐานสำคัญ",
        "research_domains": [
            "Smart City Data Analytics & Intelligent Traffic Management",
            "Medical Informatics & Spatial Health Disparity Analysis",
            "Deepfake Detection & AI-Driven Threat Hunting",
            "Applied NLP for Thai Local Government Administrative Tasks"
        ],
        "flagship_equipment": [
            "NVIDIA A100 GPU Deep Learning Supercomputing Node",
            "Cyber Range Security Simulation Platform",
            "High-Capacity Secured Storage Area Network (SAN)",
            "IoT Environmental Sensor Telemetry Testbed"
        ],
        "industry_partners": [
            "Digital Economy Promotion Agency (depa)",
            "Chonburi Provincial Administration",
            "True Digital Park",
            "Kasikorn Business-Technology Group (KBTG)"
        ],
        "open_positions": [
            "Research Assistant in Geo-Spatial AI Analytics (ป.โท/เอก)",
            "Software Engineer - Cloud Native Cyber Range Development"
        ],
        "website_url": "https://informatics.buu.ac.th",
        "image_url": "https://images.unsplash.com/photo-1551288049-bebda4e38f71?w=800&q=80"
    },

    # =========================================================================
    # CENTRAL REGION - Srinakharinwirot University (SWU - มศว)
    # =========================================================================
    {
        "id": "swu_med_biomedical_health_lab",
        "name_th": "ศูนย์ความเป็นเลิศด้านการวิจัยทางการแพทย์และชีวการแพทย์ มศว",
        "name_en": "SWU Center of Excellence in Medical & Biomedical Research",
        "university": "Srinakharinwirot University",
        "university_th": "มหาวิทยาลัยศรีนครินทรวิโรฒ",
        "faculty": "Faculty of Medicine",
        "faculty_th": "คณะแพทยศาสตร์",
        "department": "Biomedical Science Research Unit",
        "department_th": "หน่วยวิจัยวิทยาศาสตร์ชีวการแพทย์",
        "lead_advisor_id": "srinakhari_facultyofe_jantarasaratoon_077",
        "member_faculty_ids": ["srinakhari_facultyofe_jantarasaratoon_077"],
        "description": "ศูนย์วิจัยระดับสถาบันที่มุ่งเน้นการศึกษาชีววิทยาของมะเร็งในระดับโมเลกุล การพัฒนาชีวโมเลกุลและนวัตกรรมการรักษาแบบมุ่งเป้า (Targeted Therapy) และการประยุกต์ใช้เซลล์ต้นกำเนิดเพื่อการฟื้นฟูเนื้อเยื่อ",
        "research_domains": [
            "Cancer Molecular Biology & Biomarker Discovery",
            "Targeted Drug Delivery Systems & Nanomedicine",
            "Stem Cell Biology & Regenerative Medicine",
            "Infectious Disease Surveillance & Immunodiagnostics"
        ],
        "flagship_equipment": [
            "Next-Generation Sequencer (Illumina NextSeq 550)",
            "High-Resolution Confocal Laser Scanning Microscope",
            "Real-Time Droplet Digital PCR (ddPCR System)",
            "Automated Flow Cytometer & Cell Sorter"
        ],
        "industry_partners": [
            "Her Royal Highness Princess Maha Chakri Sirindhorn Medical Center",
            "Government Pharmaceutical Organization (GPO)",
            "Roche Diagnostics Thailand"
        ],
        "open_positions": [
            "Postdoctoral Researcher: Cancer Epigenetics & Liquid Biopsy",
            "Master's RA: Nanoparticle-Mediated Drug Formulation"
        ],
        "website_url": "https://med.swu.ac.th",
        "image_url": "https://images.unsplash.com/photo-1532187863486-abf9dbad1b69?w=800&q=80"
    },
    {
        "id": "swu_sci_smart_nanomaterials",
        "name_th": "ห้องปฏิบัติการวัสดุอัจฉริยะ เซนเซอร์เคมีชีวภาพ และนาโนเทคโนโลยี มศว",
        "name_en": "Smart Nanomaterials, Biosensors & Applied Nanotechnology Laboratory",
        "university": "Srinakharinwirot University",
        "university_th": "มหาวิทยาลัยศรีนครินทรวิโรฒ",
        "faculty": "Faculty of Science",
        "faculty_th": "คณะวิทยาศาสตร์",
        "department": "Department of Materials Science",
        "department_th": "ภาควิชาวิทยาการวัสดุ",
        "lead_advisor_id": "srinakhari_facultyofe_ltkittikoonrung_006",
        "member_faculty_ids": ["srinakhari_facultyofe_ltkittikoonrung_006"],
        "description": "วิจัยและพัฒนาวัสดุโครงสร้างนาโนขั้นสูงสำหรับอุปกรณ์ตรวจวัดเคมี-ชีวภาพแบบพกพา (Point-of-Care Biosensors) การกักเก็บพลังงานสะอาด และฟิล์มเคลือบอัจฉริยะสำหรับงานอุตสาหกรรม",
        "research_domains": [
            "Electrochemical Biosensors for Point-of-Care Diagnostics",
            "2D Nanomaterials (MXenes & Graphene) Synthesis",
            "Functional Polymers for Flexible Electronics",
            "Supercapacitors & Solid-State Electrolytes"
        ],
        "flagship_equipment": [
            "Field Emission Scanning Electron Microscope (FE-SEM)",
            "Multichannel Potentiostat/Galvanostat/EIS Station",
            "Atomic Force Microscope (AFM Nanoscale Profiler)",
            "X-Ray Diffractometer (XRD Powder & Thin Film)"
        ],
        "industry_partners": [
            "National Nanotechnology Center (NANOTEC)",
            "SCG Chemicals",
            "IRPC Public Company Limited"
        ],
        "open_positions": [
            "PhD Candidate: 2D MXene Biosensing Platforms (ทุน พสวท.)"
        ],
        "website_url": "https://science.swu.ac.th",
        "image_url": "https://images.unsplash.com/photo-1582719478250-c89cae4dc85b?w=800&q=80"
    },

    # =========================================================================
    # CENTRAL REGION - Silpakorn University (SU - มหาวิทยาลัยศิลปากร)
    # =========================================================================
    {
        "id": "su_pharm_drug_delivery_lab",
        "name_th": "ศูนย์วิจัยนวัตกรรมเภสัชกรรมและการพัฒนาระบบนำส่งยา มหาวิทยาลัยศิลปากร",
        "name_en": "Pharmaceutical Innovation & Advanced Drug Delivery Systems Center",
        "university": "Silpakorn University",
        "university_th": "มหาวิทยาลัยศิลปากร",
        "faculty": "Faculty of Pharmacy",
        "faculty_th": "คณะเภสัชศาสตร์",
        "department": "Department of Pharmaceutical Technology",
        "department_th": "ภาควิชาเทคโนโลยีเภสัชกรรม",
        "lead_advisor_id": "su_pharm_praneet_001",
        "member_faculty_ids": ["su_pharm_praneet_001"],
        "description": "ศูนย์นวัตกรรมด้านเภสัชกรรมชั้นนำของประเทศ มุ่งเน้นการพัฒนาระบบนำส่งยาผ่านผิวหนัง (Transdermal Microneedles) นาโนอิมัลชันสำหรับยาละลายน้ำยาก และการตั้งตำรับยาสมุนไพรไทยสู่มาตรฐานสากล",
        "research_domains": [
            "Microneedle Arrays for Painless Transdermal Drug Delivery",
            "Lipid Nanoparticles (LNP) for mRNA Delivery",
            "Biomimetic Polymer Formulation & Controlled Release",
            "Phytopharmaceutical Standardization & Cosmeceuticals"
        ],
        "flagship_equipment": [
            "Laser Micro-machining System for Microneedle Fabrication",
            "Franz Diffusion Cell Automated Testing Console",
            "Particle Size & Zeta Potential Analyzer (Zetasizer Ultra)",
            "Differential Scanning Calorimeter (DSC High Precision)"
        ],
        "industry_partners": [
            "Mega Lifesciences Public Company Limited",
            "Bangkok Lab and Cosmetic (BLC)",
            "Government Pharmaceutical Organization (GPO)"
        ],
        "open_positions": [
            "Postdoc Fellow: Dissolving Microneedle Vaccines",
            "Graduate RA in Advanced Nanoparticle Drug Formulation"
        ],
        "website_url": "https://pharmacy.su.ac.th",
        "image_url": "https://images.unsplash.com/photo-1584515979956-d9f6e5d09982?w=800&q=80"
    },
    {
        "id": "su_eng_biopolymer_advanced_materials",
        "name_th": "ห้องปฏิบัติการวิศวกรรมพอลิเมอร์ชีวภาพและบรรจุภัณฑ์ยั่งยืน มหาวิทยาลัยศิลปากร",
        "name_en": "Biopolymer Engineering & Sustainable Packaging Materials Laboratory",
        "university": "Silpakorn University",
        "university_th": "มหาวิทยาลัยศิลปากร",
        "faculty": "Faculty of Engineering and Industrial Technology",
        "faculty_th": "คณะวิศวกรรมศาสตร์และเทคโนโลยีอุตสาหกรรม",
        "department": "Department of Materials Science and Engineering",
        "department_th": "ภาควิชาวิทยาการและวิศวกรรมวัสดุ",
        "lead_advisor_id": "su_eng_teacher_074",
        "member_faculty_ids": ["su_eng_teacher_074"],
        "description": "วิจัยพัฒนาพลาสติกชีวภาพย่อยสลายได้ทางชีวภาพ (Biodegradable Plastics) ฟิล์มห่อหุ้มอาหารอัจฉริยะที่บ่งชี้ความสด และการรีไซเคิลพอลิเมอร์เชิงเคมีเพื่อระบบเศรษฐกิจหมุนเวียน (Circular Economy)",
        "research_domains": [
            "Bio-based Polylactic Acid (PLA) & Polyhydroxyalkanoate (PHA) Blends",
            "Active and Intelligent Food Packaging Films",
            "Chemical Upcycling of Post-Consumer Plastics",
            "Bio-nanocomposites for Green Electronics"
        ],
        "flagship_equipment": [
            "Co-rotating Twin Screw Extruder for Polymer Compounding",
            "Blown Film Extrusion Pilot Line",
            "Oxygen and Water Vapor Transmission Rate Analyzers (OTR/WVTR)",
            "Universal Testing Machine (Instron Tensile/Flexural)"
        ],
        "industry_partners": [
            "PTT Global Chemical (GC)",
            "TotalEnergies Corbion",
            "Thai Plastic and Chemicals (TPC)"
        ],
        "open_positions": [
            "Master's RA: Antimicrobial Bio-Packaging Formulation"
        ],
        "website_url": "https://eng.su.ac.th",
        "image_url": "https://images.unsplash.com/photo-1507668077129-56e32842fceb?w=800&q=80"
    },

    # =========================================================================
    # NORTHERN REGION - Mae Fah Luang University (MFU - ม.แม่ฟ้าหลวง)
    # =========================================================================
    {
        "id": "mfu_tea_coffee_institute",
        "name_th": "สถาบันชาและกาแฟ มหาวิทยาลัยแม่ฟ้าหลวง",
        "name_en": "Tea and Coffee Institute of Mae Fah Luang University",
        "university": "Mae Fah Luang University",
        "university_th": "มหาวิทยาลัยแม่ฟ้าหลวง",
        "faculty": "School of Agro-Industry",
        "faculty_th": "สำนักวิชาอุตสาหกรรมเกษตร",
        "department": "Post-Harvest Technology & Sensory Science Unit",
        "department_th": "สาขาเทคโนโลยีหลังการเก็บเกี่ยวและวิทยาศาสตร์ประสาทสัมผัส",
        "lead_advisor_id": "mfu_agro_chanida_001",
        "member_faculty_ids": ["mfu_agro_chanida_001"],
        "description": "ศูนย์ความเป็นเลิศชั้นนำระดับเอเชียด้านการวิจัยชาและกาแฟครบวงจร ตั้งแต่การปรับปรุงสายพันธุ์ กระบวนการหมักชีวภาพ (Specialty Coffee Fermentation) การวิเคราะห์สารออกฤทธิ์ทางชีวภาพ และการประเมินรสสัมผัสขั้นสูง",
        "research_domains": [
            "Microbial Dynamics in Controlled Coffee Fermentation",
            "Flavonoid and Catechin Profiles in Highland Wild Tea",
            "Volatile Aroma Compound Chromatography & Sensory Mapping",
            "Circular Utilization of Coffee Cascara and Agro-Waste"
        ],
        "flagship_equipment": [
            "Gas Chromatography-Mass Spectrometry with Olfactometry (GC-MS-O)",
            "High-Performance Liquid Chromatography (HPLC DAD/FLD)",
            "SCA Certified Specialty Coffee Roasting and Sensory Laboratory",
            "Supercritical Fluid CO2 Extraction Pilot Unit"
        ],
        "industry_partners": [
            "Doi Chaang Coffee Original",
            "Royal Project Foundation",
            "Boon Rawd Brewery (Singha Park Chiang Rai)",
            "Specialty Coffee Association (SCA Thailand)"
        ],
        "open_positions": [
            "Postdoctoral Fellow in Fermentation Microbiology & Flavor Chemistry",
            "Graduate RA in Sustainable Bioactive Compound Extraction"
        ],
        "website_url": "https://teacoffee.mfu.ac.th",
        "image_url": "https://images.unsplash.com/photo-1495474472287-4d71bcdd2085?w=800&q=80"
    },
    {
        "id": "mfu_fungal_research_excellence",
        "name_th": "ศูนย์ความเป็นเลิศด้านการวิจัยเชื้อรา มหาวิทยาลัยแม่ฟ้าหลวง (Center of Excellence in Fungal Research)",
        "name_en": "Center of Excellence in Fungal Research (CEFR MFU)",
        "university": "Mae Fah Luang University",
        "university_th": "มหาวิทยาลัยแม่ฟ้าหลวง",
        "faculty": "School of Science",
        "faculty_th": "สำนักวิชาวิทยาศาสตร์",
        "department": "Division of Applied Mycology & Biodiversity",
        "department_th": "สาขาวิทยาเห็ดราประยุกต์และความหลากหลายทางชีวภาพ",
        "lead_advisor_id": "mfu_agro_chanida_001",
        "member_faculty_ids": ["mfu_agro_chanida_001"],
        "description": "ศูนย์วิจัยเห็ดราที่ติดอันดับ Top-10 ของโลกด้านอนุกรมวิธานและการค้นพบเชื้อราชนิดใหม่ มุ่งเน้นการใช้ประโยชน์จากเชื้อราป่าในการสังเคราะห์สารต้านจุลชีพ เอนไซม์อุตสาหกรรม และการควบคุมศัตรูพืชโดยชีววิธี",
        "research_domains": [
            "Fungal Taxonomy, Phylogenetics & Global Biodiversity",
            "Endophytic Fungi & Secondary Metabolite Synthesis",
            "Industrial Myco-enzymes for Cellulose Degradation",
            "Entomopathogenic Fungi for Biological Pest Control"
        ],
        "flagship_equipment": [
            "Automated High-Throughput DNA Sequencer",
            "Cryo-Preservation Fungal Culture Bank (10,000+ Strains)",
            "Preparative High-Pressure Liquid Chromatography (Prep-HPLC)",
            "Fluorescence In Situ Hybridization (FISH) System"
        ],
        "industry_partners": [
            "National Center for Genetic Engineering and Biotechnology (BIOTEC)",
            "Kunming Institute of Botany (Chinese Academy of Sciences)",
            "Royal Botanic Gardens, Kew (UK)"
        ],
        "open_positions": [
            "PhD Research Fellowship in Fungal Evolutionary Genomics",
            "Research Assistant in Bioactive Fungal Metabolites"
        ],
        "website_url": "https://science.mfu.ac.th",
        "image_url": "https://images.unsplash.com/photo-1543852786-1cf6624b9987?w=800&q=80"
    },
    {
        "id": "mfu_cosmetic_natural_extracts",
        "name_th": "ศูนย์นวัตกรรมวิทยาศาสตร์เครื่องสำอางและสารสกัดสมุนไพร มหาวิทยาลัยแม่ฟ้าหลวง",
        "name_en": "Cosmetic Science & Herbal Natural Extracts Innovation Center",
        "university": "Mae Fah Luang University",
        "university_th": "มหาวิทยาลัยแม่ฟ้าหลวง",
        "faculty": "School of Cosmetic Science",
        "faculty_th": "สำนักวิชาวิทยาศาสตร์เครื่องสำอาง",
        "department": "Department of Cosmetic Formulation & Efficacy Testing",
        "department_th": "สาขาวิชาการพัฒนาตำรับเครื่องสำอางและการทดสอบประสิทธิภาพ",
        "lead_advisor_id": "mfu_antiaging_001",
        "member_faculty_ids": ["mfu_antiaging_001"],
        "description": "ศูนย์วิจัยชั้นนำของอาเซียนด้านวิทยาศาสตร์เครื่องสำอาง การพัฒนาระบบกักเก็บสารออกฤทธิ์ระดับนาโน (Nanoencapsulation) และการทดสอบประสิทธิภาพทางคลินิกบนผิวหนังมนุษย์",
        "research_domains": [
            "Nanoencapsulated Botanical Antioxidants & Anti-Aging Actives",
            "In Vitro & Clinical Human Skin Barrier Efficacy Testing",
            "Clean Beauty & Sustainable Green Surfactant Formulation",
            "Natural Sunscreen Filters and Blue Light Protection"
        ],
        "flagship_equipment": [
            "Non-Invasive Skin Bioengineering Probes (Cutometer, Tewameter, Corneometer)",
            "High-Resolution 3D Skin Surface Topography Scanner (Primos CR)",
            "Cell Culture & In Vitro Toxicity Screening Laboratory",
            "Homogenizer and High-Pressure Microfluidizer"
        ],
        "industry_partners": [
            "L'Oréal Research & Innovation",
            "Mistine (Better Way Thailand)",
            "Givaudan Fragrances & Actives"
        ],
        "open_positions": [
            "Graduate RA in Advanced Cosmetic Delivery Systems",
            "Clinical Skin Evaluation Specialist"
        ],
        "website_url": "https://cosmeticscience.mfu.ac.th",
        "image_url": "https://images.unsplash.com/photo-1556228720-195a672e8a03?w=800&q=80"
    },

    # =========================================================================
    # NORTHERN REGION - University of Phayao (UP - มหาวิทยาลัยพะเยา)
    # =========================================================================
    {
        "id": "up_smart_agriculture_bioeconomy",
        "name_th": "ศูนย์นวัตกรรมเกษตรอัจฉริยะและการเพิ่มมูลค่าชีวภาพล้านนา มหาวิทยาลัยพะเยา",
        "name_en": "Center of Excellence in Smart Agriculture & Bio-Economy (SABE UP)",
        "university": "University of Phayao",
        "university_th": "มหาวิทยาลัยพะเยา",
        "faculty": "School of Agriculture and Natural Resources",
        "faculty_th": "คณะเกษตรศาสตร์และทรัพยากรธรรมชาติ",
        "department": "Department of Agricultural Technology & Resource Management",
        "department_th": "สาขาวิชาเทคโนโลยีการเกษตรและการจัดการทรัพยากร",
        "lead_advisor_id": "up_energy_wittaya_001",
        "member_faculty_ids": ["up_energy_wittaya_001"],
        "description": "มุ่งเน้นการยกระดับภาคการเกษตรในพื้นที่ภาคเหนือตอนบนด้วยเทคโนโลยีฟาร์มแม่นยำ (Precision Farming) การปรับปรุงพันธุ์ข้าวเหนียวและพืชท้องถิ่น และการแปรรูปวัสดุเหลือทิ้งทางการเกษตรเป็นถ่านชีวภาพ (Biochar)",
        "research_domains": [
            "IoT-based Precision Irrigation & Soil Nutrient Monitoring",
            "Lanna Glutinous Rice Genetics & Stress Tolerance",
            "High-Carbon Sequestration Biochar Production",
            "Post-Harvest Biological Pest Control"
        ],
        "flagship_equipment": [
            "Multi-spectral Agricultural Drone & LiDAR Payload",
            "Automated Pyrolysis Pilot Plant for Biochar Production",
            "Elemental CHNS-O Analyzer",
            "Climate-Controlled Smart Greenhouses"
        ],
        "industry_partners": [
            "Phayao Organic Agriculture Network",
            "Mitra Phol Bio-based Products",
            "Bank for Agriculture and Agricultural Cooperatives (BAAC)"
        ],
        "open_positions": [
            "Graduate RA in Smart Agricultural Sensing Systems"
        ],
        "website_url": "https://agr.up.ac.th",
        "image_url": "https://images.unsplash.com/photo-1592417817098-8f3d69109853?w=800&q=80"
    },

    # =========================================================================
    # NORTHERN REGION - Maejo University (MJU - มหาวิทยาลัยแม่โจ้)
    # =========================================================================
    {
        "id": "mju_organic_smart_farming_center",
        "name_th": "ศูนย์ความเป็นเลิศด้านการเกษตรอินทรีย์และการทำฟาร์มอัจฉริยะ มหาวิทยาลัยแม่โจ้",
        "name_en": "Center of Excellence in Organic Agriculture & Smart Farming Systems",
        "university": "Maejo University",
        "university_th": "มหาวิทยาลัยแม่โจ้",
        "faculty": "Faculty of Agricultural Production",
        "faculty_th": "คณะผลิตกรรมการเกษตร",
        "department": "Department of Horticulture & Organic Production",
        "department_th": "สาขาวิชาพืชสวนและการผลิตพืชอินทรีย์",
        "lead_advisor_id": "mju_agr_arnat_001",
        "member_faculty_ids": ["mju_agr_arnat_001", "mju_agri_weerapon_001"],
        "description": "สถาบันการศึกษาด้านการเกษตรที่เก่าแก่ที่สุดแห่งหนึ่งของไทย เชี่ยวชาญการผลิตปุ๋ยอินทรีย์ชีวภาพระดับอุตสาหกรรม (Maejo Organic Compost) การปลูกพืชสมุนไพรมาตรฐาน GAP/Ifoam และโรงงานพืชระบบปิด (Plant Factory with Artificial Light)",
        "research_domains": [
            "Industrial-Scale Thermophilic Composting Technology",
            "Indoor Plant Factory (PFAL) & Controlled Spectrum Lighting",
            "Soil Microbiome Engineering for Organic Systems",
            "Medicinal Cannabis and Herbal Cultivation Optimization"
        ],
        "flagship_equipment": [
            "Commercial-scale Closed Plant Factory Facility",
            "Aerated Static Pile Composting Monitoring System",
            "Photosynthesis & Chlorophyll Fluorescence Analyzer (Li-Cor LI-6800)",
            "Inductively Coupled Plasma Mass Spectrometry (ICP-MS Heavy Metals)"
        ],
        "industry_partners": [
            "Siam Kubota Corporation",
            "Betagro Group",
            "Organic Agriculture Certification Thailand (ACT)"
        ],
        "open_positions": [
            "Postdoctoral Researcher: Soil Microbial Consortium Design",
            "Master's Student: PFAL Light Spectrum Optimization"
        ],
        "website_url": "https://ap.mju.ac.th",
        "image_url": "https://images.unsplash.com/photo-1530836369250-ef72a3f5cda8?w=800&q=80"
    },
    {
        "id": "mju_renewable_energy_biomass",
        "name_th": "ศูนย์วิจัยพลังงานทดแทน เชื้อเพลิงชีวภาพ และแก๊สซิฟิเคชัน มหาวิทยาลัยแม่โจ้",
        "name_en": "Renewable Energy, Biofuel & Biomass Gasification Research Center",
        "university": "Maejo University",
        "university_th": "มหาวิทยาลัยแม่โจ้",
        "faculty": "School of Renewable Energy",
        "faculty_th": "วิทยาลัยพลังงานทดแทน",
        "department": "Biomass Energy Technology Division",
        "department_th": "สาขาวิชาเทคโนโลยีพลังงานชีวมวล",
        "lead_advisor_id": "mju_agri_weerapon_001",
        "member_faculty_ids": ["mju_agri_weerapon_001"],
        "description": "มุ่งเน้นการเปลี่ยนของเสียจากภาคการเกษตรเป็นพลังงานสะอาด การวิจัยระบบแก๊สซิฟิเคชันชีวมวลประสิทธิภาพสูง การผลิตก๊าซชีวภาพอัดความดัน (CBG) และระบบไมโครกริดพลังงานชุมชน",
        "research_domains": [
            "Biomass Downdraft & Fluidized Bed Gasification",
            "Anaerobic Digestion & Biomethane Upgrading to CBG",
            "Pelletized Solid Biofuel from Agricultural Residues",
            "Rural Community Microgrid Energy Storage"
        ],
        "flagship_equipment": [
            "100 kW Biomass Gasification Demonstration Power Plant",
            "Automated Bomb Calorimeter for Fuel Heat Values",
            "Biogas Chromatograph Gas Analyzer (Agilent Micro-GC)",
            "Continuous High-Pressure Pellet Mill Pilot Line"
        ],
        "industry_partners": [
            "Provincial Electricity Authority (PEA)",
            "PTT Oil and Retail Business (OR)",
            "Chiang Mai Provincial Energy Office"
        ],
        "open_positions": [
            "Graduate RA in Advanced Biogas Upgrading Technologies"
        ],
        "website_url": "https://sre.mju.ac.th",
        "image_url": "https://images.unsplash.com/photo-1497440001374-f26997328c1b?w=800&q=80"
    },

    # =========================================================================
    # NORTHERN REGION - Naresuan University (NU - มหาวิทยาลัยนเรศวร)
    # =========================================================================
    {
        "id": "nu_solar_energy_smart_grid",
        "name_th": "วิทยาลัยพลังงานทดแทนและสมาร์ตกริดเทคโนโลยี มหาวิทยาลัยนเรศวร (SGtech)",
        "name_en": "School of Renewable Energy & Smart Grid Technology (SGtech NU)",
        "university": "Naresuan University",
        "university_th": "มหาวิทยาลัยนเรศวร",
        "faculty": "School of Renewable Energy and Smart Grid Technology",
        "faculty_th": "วิทยาลัยพลังงานทดแทนและสมาร์ตกริดเทคโนโลยี",
        "department": "Smart Grid & Solar Photovoltaic Systems Division",
        "department_th": "สาขาวิชาสมาร์ตกริดและระบบเซลล์แสงอาทิตย์",
        "lead_advisor_id": "regionalun_facultymem_kongpran_043",
        "member_faculty_ids": ["regionalun_facultymem_kongpran_043"],
        "description": "ศูนย์วิจัยพลังงานแสงอาทิตย์ชั้นนำของประเทศไทย มีระบบทดสอบแผงโซลาร์เซลล์มาตรฐานสากล การบริหารจัดการพลังงานในระบบโครงข่ายไฟฟ้าอัจฉริยะ และการประเมินการเสื่อมสภาพของเซลล์แสงอาทิตย์ในสภาพภูมิอากาศเขตร้อนชื้น",
        "research_domains": [
            "Bifacial Solar Photovoltaic Performance in Tropical Climates",
            "AI-Driven Solar Irradiance and Power Forecasting",
            "Microgrid Central Controller & Battery Inverter Dynamics",
            "Solar-Powered Agricultural Cold Storage & Water Pumping"
        ],
        "flagship_equipment": [
            "Class AAA Solar Simulator for PV Module Testing",
            "Outdoor PV Reliability & Degradation Long-term Testbed",
            "Smart Grid Controller Hardware-in-the-Loop (CHIL)",
            "High-Accuracy Solar Pyranometer & Weather Station Network"
        ],
        "industry_partners": [
            "Electricity Generating Authority of Thailand (EGAT)",
            "Solar Edge Technologies",
            "Energy Absolute Public Company Limited (EA)"
        ],
        "open_positions": [
            "PhD Candidate: AI Forecasting for Solar-BESS Hybrid Plants",
            "Master's RA: Floating Solar System Thermal Analysis"
        ],
        "website_url": "https://sgtech.nu.ac.th",
        "image_url": "https://images.unsplash.com/photo-1509391365360-2e959784a276?w=800&q=80"
    },
    {
        "id": "nu_medical_biotech_genomics",
        "name_th": "ศูนย์ความเป็นเลิศด้านเทคโนโลยีชีวภาพทางการแพทย์และภูมิคุ้มกันวิทยา มหาวิทยาลัยนเรศวร",
        "name_en": "Center of Excellence in Medical Biotechnology & Immunology (CEMBI NU)",
        "university": "Naresuan University",
        "university_th": "มหาวิทยาลัยนเรศวร",
        "faculty": "Faculty of Medical Science",
        "faculty_th": "คณะวิทยาศาสตร์การแพทย์",
        "department": "Department of Microbiology & Parasitology",
        "department_th": "ภาควิชาจุลชีววิทยาและปรสิตวิทยา",
        "lead_advisor_id": "regionalun_facultymem_theerawattanasu_052",
        "member_faculty_ids": ["regionalun_facultymem_theerawattanasu_052"],
        "description": "ศูนย์วิจัยทางการแพทย์หลักในภาคเหนือตอนล่าง เชี่ยวชาญการวิจัยแอนติบอดีบำบัด โรคติดเชื้อไวรัสอุบัติใหม่และอุบัติซ้ำ และการพัฒนาชุดตรวจโรคทางภูมิคุ้มกันวิทยาแบบรวดเร็ว (Rapid Diagnostic Kits)",
        "research_domains": [
            "Recombinant Monoclonal Antibodies & Therapeutic Proteins",
            "Vector-Borne Viral Pathogen Surveillance (Dengue & Chikungunya)",
            "Lateral Flow Immunoassay (LFIA) Development",
            "Antimicrobial Resistance (AMR) Genomic Epidemiology"
        ],
        "flagship_equipment": [
            "Surface Plasmon Resonance (Biacore Molecular Interaction)",
            "Biosafety Level 3 (BSL-3) Containment Laboratory",
            "AKTA Pure Protein Purification Fast-Protein Liquid Chromatography",
            "Automated Fluorescent Cell Imager"
        ],
        "industry_partners": [
            "Naresuan University Hospital",
            "Department of Disease Control (Ministry of Public Health)",
            "Biolab Co., Ltd."
        ],
        "open_positions": [
            "Postdoctoral Researcher: Therapeutic Antibody Engineering",
            "Graduate RA in Pathogen Genomic Sequencing"
        ],
        "website_url": "https://medsci.nu.ac.th",
        "image_url": "https://images.unsplash.com/photo-1579684385127-1ef15d508118?w=800&q=80"
    },

    # =========================================================================
    # SOUTHERN REGION - Prince of Songkla University (PSU - ม.สงขลานครินทร์)
    # =========================================================================
    {
        "id": "psu_marine_coastal_resources",
        "name_th": "สถาบันวิจัยทรัพยากรทางทะเลและชายฝั่ง มหาวิทยาลัยสงขลานครินทร์",
        "name_en": "Coastal Oceanography and Marine Resources Research Institute (COMRRI PSU)",
        "university": "Prince of Songkla University",
        "university_th": "มหาวิทยาลัยสงขลานครินทร์",
        "faculty": "Faculty of Science",
        "faculty_th": "คณะวิทยาศาสตร์",
        "department": "Department of Marine Science & Environmental Biology",
        "department_th": "ภาควิชาวิทยาศาสตร์ทางทะเลและชีววิทยาสิ่งแวดล้อม",
        "lead_advisor_id": "princeofso_facultyofs_boonkerd_025",
        "member_faculty_ids": ["princeofso_facultyofs_boonkerd_025", "psu_computing_jirawat_t"],
        "description": "ศูนย์กลางการวิจัยสมุทรศาสตร์และทรัพยากรทางทะเลของภาคใต้ ทั้งฝั่งอ่าวไทยและอันดามัน มุ่งเน้นการพยากรณ์คลื่นลมชายฝั่ง บลูคาร์บอน (Blue Carbon in Mangroves and Seagrass) และระบบนิเวศแนวปะการัง",
        "research_domains": [
            "Blue Carbon Sequestration in Mangroves and Seagrass Beds",
            "Coastal Hydrodynamic Modeling & Storm Surge Prediction",
            "Marine Environmental DNA (eDNA) Biodiversity Tracking",
            "Fisheries Stock Assessment & Sustainable Catch Models"
        ],
        "flagship_equipment": [
            "Coastal Acoustic Doppler Current Profiler (ADCP Array)",
            "Research Vessel with CTD Water Profiling Winch",
            "Gas Chromatography Combustion Isotope Ratio MS (GC-C-IRMS)",
            "Unmanned Surface Vehicle (USV Autonomous Bathymetric Drone)"
        ],
        "industry_partners": [
            "Department of Marine and Coastal Resources",
            "Chevron Thailand Exploration and Production",
            "World Wildlife Fund (WWF Thailand)"
        ],
        "open_positions": [
            "PhD Candidate: Seagrass Blue Carbon Dynamics (ทุน คปก.)",
            "Graduate RA in Coastal Ocean Current Modeling"
        ],
        "website_url": "https://marine.psu.ac.th",
        "image_url": "https://images.unsplash.com/photo-1518837695005-2083093ee35b?w=800&q=80"
    },
    {
        "id": "psu_rubber_materials_innovation",
        "name_th": "ศูนย์ความเป็นเลิศด้านนวัตกรรมยางพาราและพอลิเมอร์ขั้นสูง มหาวิทยาลัยสงขลานครินทร์",
        "name_en": "Center of Excellence in Natural Rubber & Advanced Polymer Innovation",
        "university": "Prince of Songkla University",
        "university_th": "มหาวิทยาลัยสงขลานครินทร์",
        "faculty": "Faculty of Science and Industrial Technology",
        "faculty_th": "คณะวิทยาศาสตร์และเทคโนโลยีอุตสาหกรรม",
        "department": "Department of Rubber Technology and Polymer Science",
        "department_th": "ภาควิชาเทคโนโลยียางและพอลิเมอร์",
        "lead_advisor_id": "princeofso_facultyofs_boonkerd_025",
        "member_faculty_ids": ["princeofso_facultyofs_boonkerd_025"],
        "description": "ศูนย์วิจัยยางพาราอันดับ 1 ของประเทศ ตั้งอยู่ในแหล่งปลูกยางหลักของโลก เชี่ยวชาญการปรับปรุงโครงสร้างโมเลกุลน้ำยางธรรมชาติ นวัตกรรมยางล้อประหยัดพลังงาน ยางทางการแพทย์ และวัสดุดูดซับแรงสั่นสะเทือนจากแผ่นดินไหว",
        "research_domains": [
            "Chemically Modified Natural Rubber (Epoxidized & Depolymerized NR)",
            "Green Silica-Reinforced Tire Tread Compounds",
            "Medical Grade Natural Latex & Protein-Allergen Free Gloves",
            "Seismic Isolation Rubber Bearings for Civil Structures"
        ],
        "flagship_equipment": [
            "Moving Die Rheometer & Rubber Process Analyzer (RPA Elite)",
            "Internal Banbury Rubber Mixer & Two-Roll Mill Pilot Plant",
            "Dynamic Mechanical Thermal Analyzer (DMTA DMA 850)",
            "Dynamic Fatigue and Abrasion Testing Machines"
        ],
        "industry_partners": [
            "Rubber Authority of Thailand (RAOT)",
            "Sri Trang Agro-Industry Public Company Limited",
            "Michelin Siam Co., Ltd.",
            "Bridgestone Carbon Black"
        ],
        "open_positions": [
            "Postdoc Fellow: Low-Rolling-Resistance Tire Formulations",
            "Master's RA: Advanced Bio-Based Rubber Nanocomposites"
        ],
        "website_url": "https://rubber.psu.ac.th",
        "image_url": "https://images.unsplash.com/photo-1563986768609-322da13575f3?w=800&q=80"
    },

    # =========================================================================
    # SOUTHERN REGION - Walailak University (WU - มหาวิทยาลัยวลัยลักษณ์)
    # =========================================================================
    {
        "id": "wu_wood_biomaterials_center",
        "name_th": "ศูนย์ความเป็นเลิศด้านไม้และวัสดุชีวภาพ มหาวิทยาลัยวลัยลักษณ์",
        "name_en": "Center of Excellence in Wood and Biomaterials (WU CEWB)",
        "university": "Walailak University",
        "university_th": "มหาวิทยาลัยวลัยลักษณ์",
        "faculty": "School of Engineering and Technology",
        "faculty_th": "สำนักวิชาวิศวกรรมศาสตร์และเทคโนโลยี",
        "department": "Department of Materials Science and Civil Infrastructure",
        "department_th": "สาขาวิชาวัสดุศาสตร์และวิศวกรรมโครงสร้างพื้นฐาน",
        "lead_advisor_id": "regionalun_facultymem_thamrongrat_041",
        "member_faculty_ids": ["regionalun_facultymem_thamrongrat_041", "regionalun_facultymem_kaewprasertrakk_042"],
        "description": "ศูนย์วิจัยเฉพาะทางด้านไม้ยางพาราและชีวมวลปาล์มน้ำมันของภาคใต้ พัฒนาเทคโนโลยีการอบไม้ยางพาราแบบประหยัดพลังงาน วัสดุไม้คอมโพสิตทนไฟ และการสังเคราะห์เซลลูโลสนาโนไฟเบอร์ (CNF) จากเศษเหลือทิ้งทางการเกษตร",
        "research_domains": [
            "Thermal Modification & Energy-Efficient Rubberwood Drying",
            "Cellulose Nanofibers (CNF) from Oil Palm Fronds",
            "Fire-Retardant and Weather-Resistant Wood Plastic Composites",
            "Engineered Timber Structures for Sustainable Architecture"
        ],
        "flagship_equipment": [
            "Pilot-Scale Radio Frequency Vacuum (RFV) Wood Kiln",
            "High-Pressure Homogenizer for Nanocellulose Fibrillation",
            "Cone Calorimeter for Fire Hazard Characterization",
            "Structural Timber Testing Loading Frame (500 kN)"
        ],
        "industry_partners": [
            "Southern Wood Industry Association",
            "Vanachai Group Public Company Limited",
            "Forest Industry Organization (FIO)"
        ],
        "open_positions": [
            "Graduate RA in Advanced Nanocellulose Composite Materials"
        ],
        "website_url": "https://wood.wu.ac.th",
        "image_url": "https://images.unsplash.com/photo-1546484396-fb3fc6f95f98?w=800&q=80"
    },

    # =========================================================================
    # NORTHEASTERN REGION - Suranaree University of Technology (SUT - มทส.)
    # =========================================================================
    {
        "id": "sut_synchrotron_materials_lab",
        "name_th": "ศูนย์วิจัยวัสดุศาสตร์ขั้นสูงและการประยุกต์ใช้แสงซินโครตรอน มทส.",
        "name_en": "Center of Excellence in Advanced Functional Materials & Synchrotron Science",
        "university": "Suranaree University of Technology",
        "university_th": "มหาวิทยาลัยเทคโนโลยีสุรนารี",
        "faculty": "Institute of Science",
        "faculty_th": "สำนักวิชาวิทยาศาสตร์",
        "department": "School of Physics",
        "department_th": "สาขาวิชาฟิสิกส์",
        "lead_advisor_id": "sut_sci_ayut_001",
        "member_faculty_ids": ["sut_sci_ayut_001", "sut_agr_nantakorn_001"],
        "description": "ศูนย์วิจัยที่ทำงานร่วมกับสถาบันวิจัยแสงซินโครตรอน (องค์การมหาชน) เพื่อวิเคราะห์โครงสร้างผลึกและอิเล็กตรอนของวัสดุในระดับอะตอม มุ่งเน้นวัสดุตัวนำยิ่งยวด แคโทดแบตเตอรี่รุ่นใหม่ และตัวเร่งปฏิกิริยาเคมีแสง",
        "research_domains": [
            "X-ray Absorption Spectroscopy (XAS) & Synchrotron Structural Analysis",
            "High-Temperature Superconductors & Quantum Magnetic Materials",
            "Next-Gen Solid-State Battery Cathode Crystal Evolution",
            "Single-Atom Catalysts for CO2 Reduction and Hydrogen Generation"
        ],
        "flagship_equipment": [
            "Access to SLRI Synchrotron Beamline Station (BL1.1W & BL8)",
            "Physical Property Measurement System (PPMS 14-Tesla Cryogenic)",
            "High-Resolution X-Ray Photoelectron Spectrometer (XPS PHI5000)",
            "In Situ Heating Stage for Operando Powder Diffraction"
        ],
        "industry_partners": [
            "Synchrotron Light Research Institute (SLRI)",
            "PTT Innovation Institute",
            "Japan Synchrotron Radiation Research Institute (SPring-8)"
        ],
        "open_positions": [
            "Postdoctoral Researcher in Operando XAS Battery Characterization",
            "PhD Candidate: Quantum Materials Analysis (ทุน พสวท./คปก.)"
        ],
        "website_url": "https://science.sut.ac.th",
        "image_url": "https://images.unsplash.com/photo-1507668077129-56e32842fceb?w=800&q=80"
    },
    {
        "id": "sut_ev_battery_testbed",
        "name_th": "ศูนย์ทดสอบและพัฒนายานยนต์ไฟฟ้า แบตเตอรี่ และการขับขี่อัตโนมัติ มทส.",
        "name_en": "Connected & Autonomous Electric Vehicle Testing and Battery Prototyping Center",
        "university": "Suranaree University of Technology",
        "university_th": "มหาวิทยาลัยเทคโนโลยีสุรนารี",
        "faculty": "Institute of Engineering",
        "faculty_th": "สำนักวิชาวิศวกรรมศาสตร์",
        "department": "School of Mechanical Engineering & Automotive Automation",
        "department_th": "สาขาวิชาวิศวกรรมเครื่องกลและยานยนต์",
        "lead_advisor_id": "sut_sci_ayut_001",
        "member_faculty_ids": ["sut_sci_ayut_001"],
        "description": "ศูนย์วิจัยชั้นนำของภาคอีสานด้านยานยนต์ไฟฟ้า (EV) ระบบแบตเตอรี่แพ็คประสิทธิภาพสูง และระบบขับเคลื่อนอัตโนมัติ (Autonomous Driving Level 3) บนเส้นทางทดสอบภายในมหาวิทยาลัย",
        "research_domains": [
            "Battery Pack Thermal Management System (BTMS) Optimization",
            "BMS State-of-Charge (SoC) & State-of-Health (SoH) AI Algorithms",
            "V2X (Vehicle-to-Everything) Communication & Platooning Control",
            "Chassis Dynamometer EV Powertrain Efficiency Benchmarking"
        ],
        "flagship_equipment": [
            "All-Wheel Drive EV Chassis Dynamometer Test Cell",
            "High-Voltage Battery Cell/Module Cycler with Environmental Chamber",
            "RT-Lab Hardware-in-the-Loop Real-Time Simulator",
            "Autonomous Drive Sensor Suite (Ouster 64-Beam LiDAR & RTK-GNSS)"
        ],
        "industry_partners": [
            "Mercedes-Benz Manufacturing Thailand",
            "Thai Summit Group",
            "Energy Absolute (Mine Mobility)"
        ],
        "open_positions": [
            "Graduate RA in Electric Powertrain Calibration",
            "Embedded Systems Engineer - BMS Firmware Development"
        ],
        "website_url": "https://eng.sut.ac.th",
        "image_url": "https://images.unsplash.com/photo-1558441719-8b489c63f7d1?w=800&q=80"
    },

    # =========================================================================
    # NORTHEASTERN REGION - Khon Kaen University (KKU - มหาวิทยาลัยขอนแก่น)
    # =========================================================================
    {
        "id": "kku_lithium_battery_factory",
        "name_th": "โรงงานต้นแบบผลิตแบตเตอรี่ลิเธียมไอออนและศูนย์ความเป็นเลิศด้านการกักเก็บพลังงาน มข.",
        "name_en": "Lithium-Ion Battery Pilot Plant & Energy Storage Excellence Center",
        "university": "Khon Kaen University",
        "university_th": "มหาวิทยาลัยขอนแก่น",
        "faculty": "Faculty of Science",
        "faculty_th": "คณะวิทยาศาสตร์",
        "department": "Department of Materials Science & Nanotechnology",
        "department_th": "สาขาวิชาวัสดุศาสตร์และนาโนเทคโนโลยี",
        "lead_advisor_id": "khonkaenun_facultyofm_santiworakul_037",
        "member_faculty_ids": ["khonkaenun_facultyofm_santiworakul_037"],
        "description": "โรงงานต้นแบบผลิตแบตเตอรี่ลิเธียมไอออนแห่งแรกของสถาบันอุดมศึกษาไทย สามารถผลิตเซลล์แบตเตอรี่ทรงกระบอก (18650 & 21700) และ Pouch Cells จากวัสดุทางเลือก เช่น นาโนซิลิกอนจากแกลบข้าว",
        "research_domains": [
            "Silicon Anode Materials derived from Agricultural Rice Husk Ash",
            "Semi-Solid & All-Solid-State Lithium Battery Fabrication",
            "Battery Cell Recycling & Hydrometallurgical Metal Recovery",
            "Industrial Energy Storage System (ESS) Integration"
        ],
        "flagship_equipment": [
            "Fully Automated Roll-to-Roll Lithium Battery Pouch Cell Line",
            "Dry Room (-50 deg C Dew Point Precision Environment)",
            "Battery Cell Abuse Testing Bunker (Overcharge, Nail Penetration, Crush)",
            "Slurry Coater with High-Precision Slot-Die Head"
        ],
        "industry_partners": [
            "Global Power Synergy Public Company Limited (GPSC)",
            "Electricity Generating Authority of Thailand (EGAT)",
            "Khon Kaen City Development (KKTT)"
        ],
        "open_positions": [
            "Postdoctoral Researcher: Solid-State Battery Electrolytes",
            "Battery Manufacturing Process Engineer (RA)"
        ],
        "website_url": "https://science.kku.ac.th",
        "image_url": "https://images.unsplash.com/photo-1619642751034-765dfdf7c58e?w=800&q=80"
    },
    {
        "id": "kku_tropical_cholangiocarcinoma",
        "name_th": "สถาบันวิจัยมะเร็งท่อน้ำดีและโรคเขตร้อน คณะแพทยศาสตร์ มหาวิทยาลัยขอนแก่น (CASCAP)",
        "name_en": "Cholangiocarcinoma Research Institute (CASCAP KKU)",
        "university": "Khon Kaen University",
        "university_th": "มหาวิทยาลัยขอนแก่น",
        "faculty": "Faculty of Medicine",
        "faculty_th": "คณะแพทยศาสตร์",
        "department": "Department of Parasitology & Oncology Research Unit",
        "department_th": "ภาควิชาปรสิตวิทยาและหน่วยวิจัยโรคมะเร็ง",
        "lead_advisor_id": "khonkaenun_facultyofm_santiworakul_037",
        "member_faculty_ids": ["khonkaenun_facultyofm_santiworakul_037"],
        "description": "ศูนย์วิจัยระดับแนวหน้าของโลกในการต่อสู้กับโรคมะเร็งท่อน้ำดีและพยาธิใบไม้ตับ (Opisthorchis viverrini) ซึ่งเป็นปัญหาสาธารณสุขสำคัญของภาคอีสาน บูรณาการการคัดกรองด้วยอัลตราซาวด์ระบบ AI จีโนมิกส์ และชีวเคมีเชิงลึก",
        "research_domains": [
            "Genomic Landscape and Mutational Signatures of Cholangiocarcinoma",
            "AI-Assisted Ultrasound Screening for Early Liver Fluke Lesions",
            "Liquid Biopsy Urine and Serum Biomarkers for Early Detection",
            "Host-Parasite Immunopathology and Vaccine Development"
        ],
        "flagship_equipment": [
            "High-Throughput Digital Pathology Whole Slide Scanner (Aperio GT 450)",
            "Mass Spectrometry Imaging (MALDI-TOF/TOF MSI)",
            "Ultrasound AI Field Screening Vans with Cloud Tele-radiology",
            "Automated Multiplex ELISA & Luminex Platform"
        ],
        "industry_partners": [
            "World Health Organization (WHO Collaborating Centre)",
            "National Cancer Institute of Thailand",
            "Srinagarind Hospital",
            "Wellcome Sanger Institute (UK)"
        ],
        "open_positions": [
            "Postdoc in Cancer Genomics & Computational Biology",
            "Clinical Trial Research Coordinator (Master's RA)"
        ],
        "website_url": "https://cascap.kku.ac.th",
        "image_url": "https://images.unsplash.com/photo-1579154204601-01588f351e67?w=800&q=80"
    },

    # =========================================================================
    # CENTRAL REGION - Mahidol University (MU - มหาวิทยาลัยมหิดล)
    # =========================================================================
    {
        "id": "mu_siriraj_sicore_genomics",
        "name_th": "ศูนย์วิจัยความเป็นเลิศด้านจีโนมิกส์และการแพทย์แม่นยำ ศิริราช (SiCORE-Genomics)",
        "name_en": "Siriraj Center of Research Excellence in Precision Medicine and Pharmacogenomics",
        "university": "Mahidol University",
        "university_th": "มหาวิทยาลัยมหิดล",
        "faculty": "Faculty of Medicine Siriraj Hospital",
        "faculty_th": "คณะแพทยศาสตร์ศิริราชพยาบาล",
        "department": "Department of Biochemistry & Genomic Medicine Unit",
        "department_th": "ภาควิชาชีวเคมีและหน่วยเวชศาสตร์จีโนม",
        "lead_advisor_id": "mahidoluni_facultyofp_wattanaburanon_020",
        "member_faculty_ids": ["mahidoluni_facultyofp_wattanaburanon_020"],
        "description": "ศูนย์วิจัยชั้นนำด้านการแพทย์แม่นยำ (Precision Medicine) ของโรงพยาบาลศิริราช ศึกษาพันธุกรรมเชิงลึกของประชากรไทย การตรวจหายีนแพ้ยาขั้นรุนแรง (Pharmacogenomics) และการเลือกยารักษาโรคมะเร็งเฉพาะบุคคล",
        "research_domains": [
            "Whole Genome Sequencing (WGS) of Thai Population",
            "Clinical Pharmacogenomics & Adverse Drug Reaction Prevention",
            "Cancer Somatic Mutation Profiling & Targeted Drug Matching",
            "Rare Undiagnosed Disease Genetics & Clinical Variant Curation"
        ],
        "flagship_equipment": [
            "Illumina NovaSeq X Plus Ultra-High Throughput Sequencer",
            "Oxford Nanopore PromethION Long-Read Sequencing Console",
            "Capillary Electrophoresis Genetic Analyzer (Applied Biosystems 3500xL)",
            "Automated Liquid Handling Workstations (Biomek i7)"
        ],
        "industry_partners": [
            "Genomics Thailand Initiative (HSRI)",
            "Siriraj Genomics Center",
            "AstraZeneca Thailand",
            "Illumina Inc."
        ],
        "open_positions": [
            "Bioinformatics Scientist (High-Performance Computing & WGS Pipeline)",
            "PhD Candidate in Precision Oncology & Pharmacogenomics"
        ],
        "website_url": "https://www.sicore.siriraj.org",
        "image_url": "https://images.unsplash.com/photo-1530497610245-94d3c16cda28?w=800&q=80"
    },
    {
        "id": "mu_rama_precision_cancer_lab",
        "name_th": "ศูนย์วิจัยมะเร็งแม่นยำและการบำบัดระดับเซลล์ โรงพยาบาลรามาธิบดี",
        "name_en": "Ramathibodi Center for Precision Cancer Medicine & Cell Therapy",
        "university": "Mahidol University",
        "university_th": "มหาวิทยาลัยมหิดล",
        "faculty": "Faculty of Medicine Ramathibodi Hospital",
        "faculty_th": "คณะแพทยศาสตร์โรงพยาบาลรามาธิบดี",
        "department": "Comprehensive Cancer Center & Cellular Immunotherapy Unit",
        "department_th": "ศูนย์ความเป็นเลิศด้านมะเร็งและหน่วยภูมิคุ้มกันบำบัด",
        "lead_advisor_id": "mahidoluni_facultyofp_wattanaburanon_020",
        "member_faculty_ids": ["mahidoluni_facultyofp_wattanaburanon_020"],
        "description": "มุ่งเน้นการวิจัยและผลิตเซลล์บำบัดมะเร็ง CAR-T Cell Therapy แห่งแรกๆ ของประเทศไทย การศึกษาเซลล์ต้นกำเนิดเม็ดเลือด และการส่องกล้องตรวจดีเอ็นเอมะเร็งจากกระแสเลือด (Liquid Biopsy ctDNA)",
        "research_domains": [
            "Chimeric Antigen Receptor T-Cell (CAR-T Cell) Engineering",
            "Circulating Tumor DNA (ctDNA) Liquid Biopsy Diagnostics",
            "Hematopoietic Stem Cell Transplantation Immunobiology",
            "Monoclonal Antibody Production & Checkpoint Inhibitor Resistance"
        ],
        "flagship_equipment": [
            "GMP-Certified Cleanroom for Human Cell Therapy Manufacturing",
            "CliniMACS Prodigy Automated Cell Processing System",
            "Digital Droplet PCR (Bio-Rad QX200) for ctDNA Quantification",
            "Sony Spectral Cell Sorter (5-Laser High Dimension Flow)"
        ],
        "industry_partners": [
            "Ramathibodi Foundation",
            "Novartis Thailand",
            "National Science and Technology Development Agency (NSTDA)"
        ],
        "open_positions": [
            "Postdoctoral Researcher: CAR-T Cell Molecular Re-engineering",
            "Master's RA in Liquid Biopsy Clinical Assays"
        ],
        "website_url": "https://www.rama.mahidol.ac.th",
        "image_url": "https://images.unsplash.com/photo-1579165466791-788226ab77b6?w=800&q=80"
    },

    # =========================================================================
    # CENTRAL REGION - Chulalongkorn University (CU - จุฬาลงกรณ์มหาวิทยาลัย)
    # =========================================================================
    {
        "id": "cu_med_chulavax_vaccine_center",
        "name_th": "ศูนย์วิจัยวัคซีน คณะแพทยศาสตร์ จุฬาลงกรณ์มหาวิทยาลัย (ChulaVax)",
        "name_en": "Chulalongkorn Vaccine Research Center (ChulaVax)",
        "university": "Chulalongkorn University",
        "university_th": "จุฬาลงกรณ์มหาวิทยาลัย",
        "faculty": "Faculty of Medicine",
        "faculty_th": "คณะแพทยศาสตร์",
        "department": "Department of Medicine & Vaccine Innovation Center",
        "department_th": "ภาควิชาอายุรศาสตร์และศูนย์นวัตกรรมวัคซีน",
        "lead_advisor_id": "chulalongk_facultyofa_silaket_010",
        "member_faculty_ids": ["chulalongk_facultyofa_silaket_010"],
        "description": "ศูนย์วิจัยวัคซีนชั้นนำของภูมิภาค ผู้พัฒนาวัคซีน ChulaCov19 (mRNA Vaccine สัญชาติไทย) มุ่งเน้นการออกแบบและทดสอบวัคซีน mRNA สำหรับโรคติดเชื้ออุบัติใหม่ วัคซีนรักษามะเร็งเฉพาะบุคคล และวัคซีนไข้เลือดออก",
        "research_domains": [
            "Lipid Nanoparticle-Encapsulated mRNA Vaccine Design",
            "Therapeutic Cancer Vaccines & Neoantigen Identification",
            "Dengue & Emerging Viral Pathogen Cross-Neutralizing Epitopes",
            "Non-Human Primate and Clinical Trial Phase I/II Immunology"
        ],
        "flagship_equipment": [
            "Automated mRNA In Vitro Transcription & Cap-1 Enzymatic Reactor",
            "Microfluidics NanoAssemblr Spark & Ignite Systems",
            "EliSpot & FluoroSpot Automated Readers for T-Cell Responses",
            "High-Containment BSL-2+ Vaccine Challenge Facility"
        ],
        "industry_partners": [
            "BioNet-Asia Co., Ltd.",
            "University of Pennsylvania (Weissman Laboratory Partner)",
            "National Vaccine Institute of Thailand (NVI)"
        ],
        "open_positions": [
            "Postdoctoral Fellow in mRNA Structural Biology and LNP Formulation",
            "Graduate RA in Humoral & Cellular Vaccine Immunology"
        ],
        "website_url": "https://chulavax.chula.ac.th",
        "image_url": "https://images.unsplash.com/photo-1584036561566-baf8f5f1b144?w=800&q=80"
    },
    {
        "id": "cu_energy_research_institute",
        "name_th": "สถาบันวิจัยพลังงาน จุฬาลงกรณ์มหาวิทยาลัย (ERI Chula)",
        "name_en": "Energy Research Institute, Chulalongkorn University (ERI Chula)",
        "university": "Chulalongkorn University",
        "university_th": "จุฬาลงกรณ์มหาวิทยาลัย",
        "faculty": "Energy Research Institute",
        "faculty_th": "สถาบันวิจัยพลังงาน",
        "department": "Clean Energy Transition & Carbon Neutrality Division",
        "department_th": "สาขาการเปลี่ยนผ่านพลังงานและนโยบายความเป็นกลางทางคาร์บอน",
        "lead_advisor_id": "chulalongk_facultyofa_silaket_010",
        "member_faculty_ids": ["chulalongk_facultyofa_silaket_010", "chulalongk_facultyofa_silpvidhayadilo_016"],
        "description": "สถาบันวิจัยด้านนโยบายและเทคโนโลยีพลังงานระดับชาติ วิจัยแบบจำลองการเปลี่ยนผ่านพลังงาน (Energy Transition Modeling) เทคโนโลยีการดักจับ ใช้ประโยชน์ และกักเก็บคาร์บอน (CCUS) และการพัฒนาตลาดซื้อขายคาร์บอนเครดิต",
        "research_domains": [
            "National Energy Transition Pathways & Net-Zero Scenarios",
            "Carbon Capture, Utilization & Geological Storage (CCUS)",
            "Hydrogen Economy and Infrastructure Roadmap for Thailand",
            "Decarbonized Power System Economic dispatch"
        ],
        "flagship_equipment": [
            "Integrated Energy System Optimization Modeling Platform (TIMES-Chula)",
            "CO2 Adsorption Breakthrough Column & Chemisorption Reactor",
            "Gas Chromatography for Reforming and Syngas Synthesis",
            "High-Pressure Geological Core-Flooding Simulator"
        ],
        "industry_partners": [
            "Ministry of Energy of Thailand",
            "PTT Public Company Limited",
            "International Energy Agency (IEA)",
            "Asian Development Bank (ADB)"
        ],
        "open_positions": [
            "Research Fellow in Carbon Accounting & Energy Economics",
            "Graduate RA in Hydrogen Supply Chain Modeling"
        ],
        "website_url": "https://www.eri.chula.ac.th",
        "image_url": "https://images.unsplash.com/photo-1473341304170-971dccb5ac1e?w=800&q=80"
    },

    # =========================================================================
    # CENTRAL REGION - KMITL (สจล. ลาดกระบัง)
    # =========================================================================
    {
        "id": "kmitl_space_satellite_eng_lab",
        "name_th": "ห้องปฏิบัติการวิศวกรรมอวกาศและเทคโนโลยีดาวเทียม สจล.",
        "name_en": "Space Technology and Small Satellite Engineering Laboratory (Space KMITL)",
        "university": "King Mongkut's Institute of Technology Ladkrabang",
        "university_th": "สถาบันเทคโนโลยีพระจอมเกล้าเจ้าคุณทหารลาดกระบัง",
        "faculty": "International Academy of Aviation Industry",
        "faculty_th": "วิทยาลัยอุตสาหกรรมการบินนานาชาติ (IAAI)",
        "department": "Department of Aerospace Engineering",
        "department_th": "ภาควิชาวิศวกรรมการบินและอวกาศ",
        "lead_advisor_id": "kmitl_aero_001",
        "member_faculty_ids": ["kmitl_aero_001", "kingmongku_schoolofen_suwanngam_067"],
        "description": "ศูนย์วิจัยและพัฒนาดาวเทียมขนาดเล็ก (CubeSat) ระบบสื่อสารเลเซอร์อวกาศ (Optical Intersatellite Links) และระบบควบคุมทิศทางดาวเทียมแบบความแม่นยำสูง (ADCS)",
        "research_domains": [
            "CubeSat (1U-6U) Bus Architecture and Thermal-Structural Design",
            "Attitude Determination and Control System (ADCS) Dynamics",
            "Spaceborne Optical Payload & Earth Observation Imaging",
            "Deep Space Communications and Ground Station Telemetry"
        ],
        "flagship_equipment": [
            "Thermal Vacuum Chamber (TVAC Space Environment Simulation)",
            "Electrodynamic Vibration Shaker Table for Launch Simulation",
            "Air-Bearing Table for 3-Axis Satellite Attitude Simulation",
            "UHF/VHF & S-Band Automated Tracking Ground Station Dish"
        ],
        "industry_partners": [
            "Geo-Informatics and Space Technology Development Agency (GISTDA)",
            "National Astronomical Research Institute of Thailand (NARIT)",
            "Thaicom Public Company Limited"
        ],
        "open_positions": [
            "Spacecraft Structural & Thermal Systems Engineer (ป.โท/เอก)",
            "Postdoctoral Researcher in Satellite Optical Communication"
        ],
        "website_url": "https://iaai.kmitl.ac.th",
        "image_url": "https://images.unsplash.com/photo-1517976487507-598f111a9f60?w=800&q=80"
    },
    {
        "id": "kmitl_semiconductor_nanoelectronics",
        "name_th": "ศูนย์วิจัยนวัตกรรมเซมิคอนดักเตอร์และอุปกรณ์อิเล็กทรอนิกส์ระดับนาโน สจล.",
        "name_en": "Center of Excellence in Semiconductor & Nanoelectronics Devices (KMITL Nano)",
        "university": "King Mongkut's Institute of Technology Ladkrabang",
        "university_th": "สถาบันเทคโนโลยีพระจอมเกล้าเจ้าคุณทหารลาดกระบัง",
        "faculty": "School of Engineering",
        "faculty_th": "คณะวิศวกรรมศาสตร์",
        "department": "Department of Electronic Engineering",
        "department_th": "ภาควิชาวิศวกรรมอิเล็กทรอนิกส์",
        "lead_advisor_id": "kingmongku_schoolofen_suwanngam_067",
        "member_faculty_ids": ["kingmongku_schoolofen_suwanngam_067", "kmitl_aero_001"],
        "description": "ห้องปฏิบัติการห้องสะอาด (Cleanroom Class 100) สำหรับการประดิษฐ์แผ่นเวเฟอร์เซมิคอนดักเตอร์ อุปกรณ์สารกึ่งตัวนำกำลังสูง (GaN & SiC Power Devices) สำหรับยานยนต์ไฟฟ้า และเซนเซอร์ MEMS",
        "research_domains": [
            "Wide Bandgap Semiconductors (Gallium Nitride & Silicon Carbide)",
            "Power Electronic Switch Modules for EV Inverters",
            "Micro-Electro-Mechanical Systems (MEMS Accelerometers & Gyros)",
            "Neuromorphic Computing Hardware & Memristor Arrays"
        ],
        "flagship_equipment": [
            "Class 100/1000 Cleanroom Microfabrication Facility",
            "Plasma-Enhanced Chemical Vapor Deposition (PECVD System)",
            "Deep Reactive Ion Etcher (DRIE for Silicon Micro-machining)",
            "Semiconductor Parameter Analyzer with Cryogenic Probe Station"
        ],
        "industry_partners": [
            "Western Digital Thailand",
            "Delta Electronics (Thailand)",
            "Microchip Technology (Thailand)"
        ],
        "open_positions": [
            "PhD Fellowship in GaN Power Semiconductor Devices",
            "Cleanroom Process Fabrication Specialist (RA)"
        ],
        "website_url": "https://eng.kmitl.ac.th",
        "image_url": "https://images.unsplash.com/photo-1518770660439-4636190af475?w=800&q=80"
    },

    # =========================================================================
    # CENTRAL REGION - KMUTNB (มจพ. พระนครเหนือ)
    # =========================================================================
    {
        "id": "kmutnb_german_welding_materials",
        "name_th": "สถาบันนวัตกรรมเทคโนโลยีไทย-เยอรมันและวิศวกรรมการเชื่อมชั้นสูง มจพ.",
        "name_en": "Thai-German Technology Institute for Advanced Welding & NDT Inspection",
        "university": "King Mongkut's University of Technology North Bangkok",
        "university_th": "มหาวิทยาลัยเทคโนโลยีพระจอมเกล้าพระนครเหนือ",
        "faculty": "Faculty of Engineering",
        "faculty_th": "คณะวิศวกรรมศาสตร์",
        "department": "Department of Production & Materials Engineering",
        "department_th": "ภาควิชาวิศวกรรมการผลิตและวัสดุ",
        "lead_advisor_id": "kingmongku_facultyofe_asawarungsaengk_007",
        "member_faculty_ids": ["kingmongku_facultyofe_asawarungsaengk_007", "kingmongku_facultyofe_benjanarasut_029"],
        "description": "ศูนย์ความเป็นเลิศชั้นนำของอาเซียนด้านวิศวกรรมการเชื่อมขั้นสูง (Laser & Friction Stir Welding) การทดสอบแบบไม่ทำลาย (NDT) สำหรับอุตสาหกรรมอากาศยาน รถไฟความเร็วสูง และแท่นขุดเจาะน้ำมันนอกชายฝั่ง",
        "research_domains": [
            "Friction Stir Welding (FSW) of Dissimilar Lightweight Alloys",
            "Fiber Laser Robotic Cladding and Metal Additive Repair",
            "Phased Array Ultrasonic Non-Destructive Testing (PAUT)",
            "Residual Stress and Fatigue Life Prediction of Heavy Welded Joints"
        ],
        "flagship_equipment": [
            "Heavy-Duty Gantry Friction Stir Welding Machine",
            "IPG 10 kW High-Power Industrial Fiber Laser System",
            "Olympus OmniScan X3 Advanced Phased Array UT Scanner",
            "X-Ray Diffraction Residual Stress Analyzer (Stresstech)"
        ],
        "industry_partners": [
            "DVS - German Welding Society Partner",
            "PTT Exploration and Production (PTTEP)",
            "State Railway of Thailand (High-Speed Train Consortium)",
            "Thai Airways International Technical Department"
        ],
        "open_positions": [
            "Graduate RA in Advanced Friction Stir Welding Simulation",
            "NDT Research Engineer in Automated Ultrasonic Imaging"
        ],
        "website_url": "https://eng.kmutnb.ac.th",
        "image_url": "https://images.unsplash.com/photo-1504917599217-d4dc5ebe6122?w=800&q=80"
    },
    {
        "id": "kmutnb_satellite_ground_station",
        "name_th": "ศูนย์วิจัยและพัฒนาดาวเทียมขนาดเล็กและสถานีภาคพื้นดิน มจพ.",
        "name_en": "Small Satellite Research Center and Ground Control Station (KNACKSAT)",
        "university": "King Mongkut's University of Technology North Bangkok",
        "university_th": "มหาวิทยาลัยเทคโนโลยีพระจอมเกล้าพระนครเหนือ",
        "faculty": "Faculty of Engineering",
        "faculty_th": "คณะวิศวกรรมศาสตร์",
        "department": "Department of Electrical and Computer Engineering",
        "department_th": "ภาควิชาวิศวกรรมไฟฟ้าและคอมพิวเตอร์",
        "lead_advisor_id": "kingmongku_facultyofe_benjanarasut_029",
        "member_faculty_ids": ["kingmongku_facultyofe_benjanarasut_029"],
        "description": "ผู้สร้างและส่งดาวเทียม 'KNACKSAT' ดาวเทียมสัญชาติไทยดวงแรกที่ออกแบบและประกอบโดยมหาวิทยาลัยไทยขึ้นสู่อวกาศ เชี่ยวชาญการออกแบบระบบสื่อสารดาวเทียม การควบคุมภาคพื้นดิน และการประมวลผลข้อมูลโทรมาตร",
        "research_domains": [
            "CubeSat Satellite Bus Avionics and Power Distribution",
            "Ground Station Satellite Telecommand & Tracking Protocols",
            "Space Radiation Hardening of Commercial-Off-The-Shelf (COTS) Parts",
            "Interplanetary Nanosatellite Propulsion Concepts"
        ],
        "flagship_equipment": [
            "Multi-Axis Satellite Ground Station Dish Antenna Array",
            "Electromagnetic Compatibility (EMC/EMI) Anechoic Test Chamber",
            "Helmholtz Coil Magnetic Field Simulation Cage for Satellite Magnetometers",
            "Clean Assembly Hoods for Spacecraft Integration"
        ],
        "industry_partners": [
            "National Broadcasting and Telecommunications Commission (NBTC)",
            "GISTDA",
            "Mu Space and Advanced Technology"
        ],
        "open_positions": [
            "CubeSat Embedded Firmware Engineer (RA)",
            "Postdoctoral Researcher in Satellite RF Communication"
        ],
        "website_url": "https://kmutnb.ac.th",
        "image_url": "https://images.unsplash.com/photo-1451187580459-43490279c0fa?w=800&q=80"
    },

    # =========================================================================
    # CENTRAL REGION - Thammasat University (TU - มหาวิทยาลัยธรรมศาสตร์)
    # =========================================================================
    {
        "id": "tu_ai_data_analytics_center",
        "name_th": "ศูนย์ปัญญาประดิษฐ์และวิทยาการข้อมูล มหาวิทยาลัยธรรมศาสตร์ (TU AI Center)",
        "name_en": "Thammasat Artificial Intelligence & Data Analytics Center",
        "university": "Thammasat University",
        "university_th": "มหาวิทยาลัยธรรมศาสตร์",
        "faculty": "Faculty of Science and Technology",
        "faculty_th": "คณะวิทยาศาสตร์และเทคโนโลยี",
        "department": "Department of Computer Science",
        "department_th": "ภาควิชาวิทยาการคอมพิวเตอร์",
        "lead_advisor_id": "tu_tbs_001",
        "member_faculty_ids": ["tu_tbs_001", "tu_law_kittisak_001"],
        "description": "ศูนย์วิจัยที่มุ่งเน้นการประยุกต์ใช้ AI ในการบริหารภาครัฐ การวิเคราะห์ข้อมูลเศรษฐกิจและนโยบายสาธารณะ กฎหมายปัญญาประดิษฐ์และจริยธรรม AI (AI Governance & Ethics) และโมเดลภาษาขนาดใหญ่สำหรับภาษาไทย",
        "research_domains": [
            "AI Ethics, Policy & Regulatory Sandboxing in Thailand",
            "Thai Legal-NLP: Automated Judicial Contract and Case Analysis",
            "Financial Crime and Anti-Money Laundering (AML) Graph Analytics",
            "Public Healthcare Resource Allocation Optimization"
        ],
        "flagship_equipment": [
            "Enterprise Deep Learning Cluster with InfiniBand Interconnect",
            "Secured Synthetic Data Sandbox for Health and Financial Records",
            "Large-Scale High-Performance Compute Nodes (NVIDIA Tensor Cores)",
            "Multi-User Virtual Machine Cloud Computing Lab"
        ],
        "industry_partners": [
            "Securities and Exchange Commission of Thailand (SEC)",
            "Electronic Transactions Development Agency (ETDA)",
            "Thammasat University Hospital",
            "Siam Commercial Bank (SCB)"
        ],
        "open_positions": [
            "Graduate RA in Legal-AI and Natural Language Processing",
            "Research Fellow in AI Governance & Data Privacy Compliance"
        ],
        "website_url": "https://ai.tu.ac.th",
        "image_url": "https://images.unsplash.com/photo-1526374965328-7f61d4dc18c5?w=800&q=80"
    },
    {
        "id": "tu_med_stemcell_therapy",
        "name_th": "ศูนย์ความเป็นเลิศด้านการวิจัยเซลล์ต้นกำเนิดและการรักษาด้วยเซลล์ มธ.",
        "name_en": "Center of Excellence in Stem Cell Research & Cell Therapy (TU-StemCell)",
        "university": "Thammasat University",
        "university_th": "มหาวิทยาลัยธรรมศาสตร์",
        "faculty": "Faculty of Medicine",
        "faculty_th": "คณะแพทยศาสตร์",
        "department": "Stem Cell & Regenerative Medicine Research Unit",
        "department_th": "หน่วยวิจัยเซลล์ต้นกำเนิดและเวชศาสตร์ฟื้นฟูสภาวะเสื่อม",
        "lead_advisor_id": "tu_tbs_001",
        "member_faculty_ids": ["tu_tbs_001"],
        "description": "ศูนย์วิจัยทางการแพทย์เฉพาะทางด้านเซลล์บำบัด มุ่งเน้นการเพาะเลี้ยงเซลล์ต้นกำเนิดมีเซนไคม์ (MSCs) สำหรับรักษาโรคข้อเข่าเสื่อม โรคแผลเรื้อรังจากเบาหวาน และการสร้างเนื้อเยื่อกระจกตาเทียม",
        "research_domains": [
            "Mesenchymal Stem Cell (MSC) Paracrine Factor Characterization",
            "Biocompatible Hydrogel Scaffolds for Cartilage Tissue Engineering",
            "Exosome and Extracellular Vesicle (EV) Therapeutics",
            "Corneal Endothelial Cell Regeneration and Banking"
        ],
        "flagship_equipment": [
            "Automated Bioreactor for Large-Scale Stem Cell Expansion",
            "Nanoparticle Tracking Analysis (NTA ZetaView for Exosomes)",
            "Live-Cell High-Content Imaging System (Incucyte S3)",
            "Liquid Nitrogen Bio-Repository Tank with 24/7 Telemetry"
        ],
        "industry_partners": [
            "Thammasat University Hospital",
            "Medeze Group Public Company Limited",
            "Queen Sirikit National Institute of Child Health"
        ],
        "open_positions": [
            "PhD Candidate: Exosome-Based Regenerative Therapies",
            "Stem Cell Bioprocess Quality Control Specialist"
        ],
        "website_url": "https://med.tu.ac.th",
        "image_url": "https://images.unsplash.com/photo-1576086213369-97a306d36557?w=800&q=80"
    },

    # =========================================================================
    # CENTRAL REGION - Kasetsart University (KU - มหาวิทยาลัยเกษตรศาสตร์)
    # =========================================================================
    {
        "id": "ku_genomics_bioeconomy_center",
        "name_th": "ศูนย์จีโนมิกส์พืชเศรษฐกิจและความมั่นคงทางอาหาร มหาวิทยาลัยเกษตรศาสตร์",
        "name_en": "Center of Excellence in Crop Genomics & Food Security (KU Genomics)",
        "university": "Kasetsart University",
        "university_th": "มหาวิทยาลัยเกษตรศาสตร์",
        "faculty": "Faculty of Agriculture",
        "faculty_th": "คณะเกษตร",
        "department": "Department of Agronomy & Crop Genetics",
        "department_th": "ภาควิชาพืชไร่นาและพันธุศาสตร์พืช",
        "lead_advisor_id": "agr-ku-001_0458e1",
        "member_faculty_ids": ["agr-ku-001_0458e1", "ku_eng_ee_039"],
        "description": "ศูนย์วิจัยจีโนมิกส์พืชชั้นนำของประเทศ ผู้บุกเบิกการถอดรหัสพันธุกรรมข้าวสายพันธุ์ไทย (เช่น ข้าวหอมมะลิ ข้าวไรซ์เบอร์รี่) และมันสำปะหลัง มุ่งเน้นการปรับปรุงพันธุ์พืชต้านทานน้ำท่วม ภัยแล้ง และโรคระบาดด้วยเทคโนโลยี CRISPR/Cas9",
        "research_domains": [
            "Marker-Assisted Selection (MAS) and Genomic Breeding",
            "CRISPR-Cas9 Precision Gene Editing in Staple Crops",
            "Plant Phenomics Using Automated High-Throughput Imaging",
            "Crop Functional Genomics under Abiotic Climate Stress"
        ],
        "flagship_equipment": [
            "High-Throughput Plant Phenotyping Automated Conveyor Platform",
            "Capillary Electrophoresis Fragment Analyzer for Genotyping",
            "Real-Time Quantitative PCR Arrays (Bio-Rad CFX384)",
            "Climate-Controlled Walk-in Plant Growth Chambers"
        ],
        "industry_partners": [
            "Rice Department (Ministry of Agriculture and Cooperatives)",
            "Charoen Pokphand Produce (CPP)",
            "East-West Seed Thailand"
        ],
        "open_positions": [
            "Postdoctoral Researcher in CRISPR Crop Gene Editing",
            "Graduate RA in High-Throughput Plant Phenomics"
        ],
        "website_url": "https://agr.ku.ac.th",
        "image_url": "https://images.unsplash.com/photo-1530836369250-ef72a3f5cda8?w=800&q=80"
    },
    {
        "id": "ku_autonomous_agri_drone_lab",
        "name_th": "ห้องปฏิบัติการหุ่นยนต์การเกษตรและอากาศยานไร้คนขับเพื่อการเกษตรแม่นยำ มก. กำแพงแสน",
        "name_en": "Agricultural Robotics, Autonomous Drone & Precision Farm Lab (AgriBot KU)",
        "university": "Kasetsart University",
        "university_th": "มหาวิทยาลัยเกษตรศาสตร์",
        "faculty": "Faculty of Engineering at Kamphaeng Saen",
        "faculty_th": "คณะวิศวกรรมศาสตร์ กำแพงแสน",
        "department": "Department of Agricultural Engineering",
        "department_th": "ภาควิชาวิศวกรรมเกษตร",
        "lead_advisor_id": "ku_eng_ee_039",
        "member_faculty_ids": ["ku_eng_ee_039", "agr-ku-001_0458e1"],
        "description": "ศูนย์วิจัยวิศวกรรมเกษตรชั้นนำ พัฒนารถแทรกเตอร์ไร้คนขับ โดรนเกษตรอัจฉริยะที่ฉีดพ่นสารชีวภัณฑ์แบบระบุพิกัดโรค และระบบคอมพิวเตอร์วิทัศน์จำแนกวัชพืชแบบ Real-time",
        "research_domains": [
            "Autonomous Field Tractor Navigation via RTK-GPS & Obstacle Avoidance",
            "AI Computer Vision for Real-time Weed and Pest Identification",
            "Variable Rate Technology (VRT) for Spraying and Fertilizer Application",
            "Crop Health Index (NDVI/NDRE) Multispectral Drone Mapping"
        ],
        "flagship_equipment": [
            "Custom Autonomous Electric Tractor Research Platform",
            "DJI Enterprise Multispectral & Thermal Agricultural Drones",
            "Real-Time Kinematic (RTK) Base Station Network",
            "Hydraulic & Power Take-Off (PTO) Testing Dynamometer"
        ],
        "industry_partners": [
            "Siam Kubota Corporation",
            "Yanmar S.P. Co., Ltd.",
            "HG Robotics (Thailand)"
        ],
        "open_positions": [
            "Robotics & Autonomous Navigation Software Engineer (RA)",
            "Master's RA: Drone Multispectral Yield Prediction"
        ],
        "website_url": "https://eng.kps.ku.ac.th",
        "image_url": "https://images.unsplash.com/photo-1508614589041-895b88991e3e?w=800&q=80"
    },

    # =========================================================================
    # CENTRAL REGION - NIDA (นิด้า - สถาบันบัณฑิตพัฒนบริหารศาสตร์)
    # =========================================================================
    {
        "id": "nida_bigdata_social_innovation",
        "name_th": "ศูนย์วิจัยข้อมูลขนาดใหญ่ การวิเคราะห์นโยบาย และนวัตกรรมเพื่อสังคม นิด้า",
        "name_en": "NIDA Center for Big Data Analytics, Public Policy & Social Innovation",
        "university": "National Institute of Development Administration",
        "university_th": "สถาบันบัณฑิตพัฒนบริหารศาสตร์ (นิด้า)",
        "faculty": "School of Applied Statistics",
        "faculty_th": "คณะสถิติประยุกต์",
        "department": "Department of Data Science and Analytics",
        "department_th": "สาขาวิทยาการข้อมูลและการวิเคราะห์",
        "lead_advisor_id": "nida_as_analytics_002",
        "member_faculty_ids": ["nida_as_analytics_002"],
        "description": "ศูนย์วิจัยการวิเคราะห์ข้อมูลเชิงนโยบายระดับชาติ ประยุกต์ใช้โมเดล Big Data, AI และ Machine Learning เพื่อแก้ปัญหาความยากจน การกระจายรายได้ และการประเมินผลสัมฤทธิ์ของโครงการรัฐ",
        "research_domains": [
            "Public Policy Impact Evaluation using Quasi-Experimental Big Data",
            "Social Media Sentiment Analysis & Citizen Feedback Mining",
            "Socio-Economic Mobility & Poverty Mapping Algorithms",
            "Predictive Governance & Government Service Optimization"
        ],
        "flagship_equipment": [
            "High-Throughput Social Data Ingestion & ETL Server Farm",
            "Statistically Secured Data Enclave for Census and Tax Datasets",
            "Parallel High-Performance Statistical Computing Nodes",
            "Executive Interactive Policy Dashboard Visualizations"
        ],
        "industry_partners": [
            "National Economic and Social Development Council (NESDC)",
            "National Statistical Office of Thailand (NSO)",
            "United Nations Development Programme (UNDP Thailand)"
        ],
        "open_positions": [
            "Postdoctoral Researcher in Econometrics & Social Machine Learning",
            "Data Engineer - Government Open Data Integration"
        ],
        "website_url": "https://as.nida.ac.th",
        "image_url": "https://images.unsplash.com/photo-1460925895917-afdab827c52f?w=800&q=80"
    },

    # =========================================================================
    # NORTHERN REGION - Chiang Mai University (CMU - มหาวิทยาลัยเชียงใหม่)
    # =========================================================================
    {
        "id": "cmu_ai_center_of_excellence",
        "name_th": "ศูนย์ความเป็นเลิศด้านปัญญาประดิษฐ์ ระบบอัตโนมัติ และข้อมูลอัจฉริยะ มหาวิทยาลัยเชียงใหม่",
        "name_en": "CMU Center of Excellence in Artificial Intelligence & Smart Automation",
        "university": "Chiang Mai University",
        "university_th": "มหาวิทยาลัยเชียงใหม่",
        "faculty": "Faculty of Engineering",
        "faculty_th": "คณะวิศวกรรมศาสตร์",
        "department": "Department of Computer Engineering",
        "department_th": "ภาควิชาวิศวกรรมคอมพิวเตอร์",
        "lead_advisor_id": "cmu_eng_ee_014",
        "member_faculty_ids": ["cmu_eng_ee_014"],
        "description": "ศูนย์กลางการวิจัยปัญญาประดิษฐ์ชั้นนำในภาคเหนือ เชี่ยวชาญการประมวลผลสัญญาณเสียงภาษาไทย (Thai Speech Recognition) การรู้จำภาพทางการแพทย์ในโรงพยาบาลมหาราชนครเชียงใหม่ และหุ่นยนต์บริการอัจฉริยะ",
        "research_domains": [
            "Northern Dialect and Thai Speech Recognition & Synthesis",
            "Computer Vision for Diabetic Retinopathy and Chest X-Ray Screening",
            "Smart Agriculture IoT Edge AI for Highland Crops",
            "Autonomous Mobile Robot Fleet Coordination in Hospitals"
        ],
        "flagship_equipment": [
            "NVIDIA DGX Station A100 AI Compute Appliance",
            "Acoustic Anechoic Chamber for Precision Audio Modeling",
            "Tele-presence Hospital Delivery Robot Prototypes",
            "Edge-AI Heterogeneous Embedded Dev-Kit Testbench"
        ],
        "industry_partners": [
            "Maharaj Nakorn Chiang Mai Hospital",
            "Kasikorn Business-Technology Group (KBTG)",
            "Thai Association for Artificial Intelligence (AIAT)"
        ],
        "open_positions": [
            "Graduate RA in Multimodal Medical Image Synthesis",
            "Speech AI Engineer (Thai & Lanna Dialect Models)"
        ],
        "website_url": "https://cmu.ac.th",
        "image_url": "https://images.unsplash.com/photo-1485827404703-89b55fcc595e?w=800&q=80"
    },
    {
        "id": "cmu_environmental_pm25_lab",
        "name_th": "ศูนย์วิจัยวิทยาศาสตร์สิ่งแวดล้อมและการจัดการมลพิษทางอากาศ PM2.5 มช.",
        "name_en": "Environmental Science & PM2.5 Air Pollution Research Center (CMU Air Quality)",
        "university": "Chiang Mai University",
        "university_th": "มหาวิทยาลัยเชียงใหม่",
        "faculty": "Faculty of Science",
        "faculty_th": "คณะวิทยาศาสตร์",
        "department": "Environmental Science Research Center (ESRC)",
        "department_th": "ศูนย์วิจัยวิทยาศาสตร์สิ่งแวดล้อม",
        "lead_advisor_id": "cmu_eng_ee_014",
        "member_faculty_ids": ["cmu_eng_ee_014"],
        "description": "ศูนย์วิจัยหลักระดับประเทศในการศึกษาวิกฤตฝุ่นควันและมลพิษทางอากาศ PM2.5 ในภาคเหนือ มีเครือข่ายเซนเซอร์ตรวจวัดคุณภาพอากาศแบบเรียลไทม์ การวิเคราะห์องค์ประกอบทางเคมีและแหล่งกำเนิดฝุ่น และการพยากรณ์ล่วงหน้า",
        "research_domains": [
            "Chemical Speciation & Source Apportionment of PM2.5 (PAHs and Heavy Metals)",
            "Satellite Remote Sensing & Aerosol Optical Depth (AOD) Calibration",
            "Machine Learning for 72-Hour Transboundary Haze Dispersion Forecasting",
            "Health Impact Assessment & Indoor Clean Air Technologies"
        ],
        "flagship_equipment": [
            "High-Volume Air Samplers with PM2.5 Size-Selective Inlets",
            "Thermal-Optical Carbon Analyzer for Organic & Elemental Carbon (OC/EC)",
            "Lidar Atmospheric Profiler for Boundary Layer Smoke Height",
            "Gas Chromatography-Mass Spectrometry for Toxic Polycyclic Aromatics"
        ],
        "industry_partners": [
            "Pollution Control Department (PCD)",
            "Chiang Mai Clean Air Network",
            "NASA Aerosol Robotic Network (AERONET Partner)"
        ],
        "open_positions": [
            "Postdoctoral Researcher in Atmospheric Chemical Transport Modeling",
            "Graduate RA: Sensor Calibration and Satellite Haze Tracking"
        ],
        "website_url": "https://esrc.science.cmu.ac.th",
        "image_url": "https://images.unsplash.com/photo-1534088568595-a066f410bcda?w=800&q=80"
    },

    # =========================================================================
    # SOUTHERN REGION - Thaksin University (TSU - มหาวิทยาลัยทักษิณ)
    # =========================================================================
    {
        "id": "tsu_songkhla_lake_basin_center",
        "name_th": "สถาบันวิจัยและพัฒนาลุ่มน้ำทะเลสาบสงขลา มหาวิทยาลัยทักษิณ",
        "name_en": "Songkhla Lake Basin Research & Ecological Sustainable Development Institute",
        "university": "Thaksin University",
        "university_th": "มหาวิทยาลัยทักษิณ",
        "faculty": "Faculty of Economics and Business Administration",
        "faculty_th": "คณะเศรษฐศาสตร์และการบริหาร",
        "department": "Community Enterprise and Local Economic Development Division",
        "department_th": "สาขาการพัฒนาวิสาหกิจชุมชนและเศรษฐกิจฐานราก",
        "lead_advisor_id": "thaksinuni_facultyofe_hitaphong_024",
        "member_faculty_ids": ["thaksinuni_facultyofe_hitaphong_024", "thaksinuni_facultyofe_khiawkae_027"],
        "description": "ศูนย์วิจัยเชิงพื้นที่หลักเพื่อการอนุรักษ์และฟื้นฟูระบบนิเวศลุ่มน้ำทะเลสาบสงขลา (3 น้ำ: จืด กร่อย เค็ม) มุ่งเน้นการพัฒนาเศรษฐกิจสีเขียว (Green Economy) วิสาหกิจชุมชนประมงพื้นบ้าน และการบริหารจัดการน้ำอย่างยั่งยืน",
        "research_domains": [
            "Songkhla Lake Estuarine Hydro-Ecology & Biodiversity Conservation",
            "Local Community-Based Sustainable Tourism & Heritage Preservation",
            "Aquaculture Co-management & Traditional Artisanal Fisheries",
            "Blue Economy & Climate Change Adaptation in Coastal Communities"
        ],
        "flagship_equipment": [
            "Mobile Water Quality Laboratory & Lake Bathymetry Sonar Boat",
            "Multi-Parameter Water Quality Sondes (YSI ProDSS)",
            "Geographic Information System (GIS) Spatial Modeling Cluster",
            "Community Enterprise Food Innovation Incubator"
        ],
        "industry_partners": [
            "Office of the National Water Resources (ONWR)",
            "Songkhla Provincial Administrative Organization",
            "Sustainable Agriculture Foundation Thailand"
        ],
        "open_positions": [
            "Master's RA in Watershed Resource Economics & Policy",
            "Community GIS Spatial Analyst"
        ],
        "website_url": "https://www.tsu.ac.th",
        "image_url": "https://images.unsplash.com/photo-1507525428034-b723cf961d3e?w=800&q=80"
    },
    {
        "id": "tsu_stem_education_innovation",
        "name_th": "ศูนย์นวัตกรรมการเรียนรู้สะเต็มศึกษาและพัฒนาศักยภาพครูภาคใต้ มหาวิทยาลัยทักษิณ",
        "name_en": "Southern STEM Education & Pedagogical Innovation Center (TSU STEM)",
        "university": "Thaksin University",
        "university_th": "มหาวิทยาลัยทักษิณ",
        "faculty": "Faculty of Education",
        "faculty_th": "คณะศึกษาศาสตร์",
        "department": "Department of Science and Mathematics Education",
        "department_th": "กลุ่มหลักสูตรการสอนวิทยาศาสตร์และคณิตศาสตร์",
        "lead_advisor_id": "thaksinuni_facultyofe_pianram_056",
        "member_faculty_ids": ["thaksinuni_facultyofe_pianram_056", "thaksinuni_facultyofe_pairat_029"],
        "description": "ศูนย์นวัตกรรมด้านการศึกษาที่ใหญ่ที่สุดในภาคใต้ มุ่งเน้นการวิจัยพัฒนาหลักสูตรสะเต็มศึกษา (STEM Education) ปัญญาประดิษฐ์เพื่อการเรียนรู้เฉพาะบุคคล (AI for Personalized Learning) และการยกระดับครูชนบท",
        "research_domains": [
            "Active Learning & Integrated STEM Curriculum Design",
            "AI-Powered Learning Analytics & Educational Diagnostics",
            "Indigenous Knowledge Integration in Science Teaching",
            "Augmented & Virtual Reality (AR/VR) Classrooms for Rural Schools"
        ],
        "flagship_equipment": [
            "Immersive VR Educational Simulation Studio",
            "Eye-Tracking & Cognitive Load Laboratory (Tobii Pro)",
            "Makerspace Prototyping Lab (3D Printers & Robotics Dev Kits)",
            "Smart Micro-Teaching Observational Suites"
        ],
        "industry_partners": [
            "Equitable Education Fund (EEF Thailand)",
            "SEAMEO Regional Centre for STEM Education",
            "Southern Primary Educational Service Area Offices"
        ],
        "open_positions": [
            "Doctoral Fellowship in Educational Technology and Learning Analytics",
            "Educational Media Instructional Designer"
        ],
        "website_url": "https://edu.tsu.ac.th",
        "image_url": "https://images.unsplash.com/photo-1509062522246-3755977927d7?w=800&q=80"
    },

    # =========================================================================
    # NORTHEASTERN REGION - Ubon Ratchathani University (UBU - มหาวิทยาลัยอุบลราชธานี)
    # =========================================================================
    {
        "id": "ubu_mekong_agro_food_center",
        "name_th": "ศูนย์ความเป็นเลิศด้านนวัตกรรมเกษตรและอาหารแปรรูปลุ่มน้ำโขง มหาวิทยาลัยอุบลราชธานี",
        "name_en": "Mekong Basin Agricultural Innovation & Functional Food Excellence Center",
        "university": "Ubon Ratchathani University",
        "university_th": "มหาวิทยาลัยอุบลราชธานี",
        "faculty": "Faculty of Agriculture",
        "faculty_th": "คณะเกษตรศาสตร์",
        "department": "Department of Food Technology and Agro-Processing",
        "department_th": "ภาควิชาเทคโนโลยีการอาหาร",
        "lead_advisor_id": "ubonratcha_facultyofa_thatpitchayangk_015",
        "member_faculty_ids": ["ubonratcha_facultyofa_thatpitchayangk_015", "ubonratcha_facultyofa_chaiwattrakul_019"],
        "description": "ศูนย์วิจัยเกษตรและอาหารแปรรูปชายแดนลุ่มน้ำโขง มุ่งเน้นการสกัดสารออกฤทธิ์ทางชีวภาพจากพืชสมุนไพรพื้นถิ่นอีสาน การยกระดับผลิตภัณฑ์ปลาน้ำจืดลุ่มน้ำโขง และการพัฒนาอาหารฟังก์ชันสำหรับผู้สูงอายุ",
        "research_domains": [
            "Indigenous Herbal Bioactive Extraction & Nano-encapsulation",
            "Mekong River Native Fish Protein Hydrolysates & Collagen",
            "Fermented Food Microbiome (Isan Traditional Fermentation)",
            "Climate-Resilient Tropical Forage Crops & Livestock Nutrition"
        ],
        "flagship_equipment": [
            "Supercritical CO2 Fluid Extraction Pilot Plant",
            "Spray Dryer & Freeze Dryer Commercial Pilot Units",
            "Texture Analyzer & Food Rheometer (TA.XT Plus)",
            "Gas Chromatography-Mass Spectrometry (GC-MS for Food Aromas)"
        ],
        "industry_partners": [
            "Ubon Bio Ethanol Public Company Limited (UBE)",
            "Betagro Agro Group",
            "National Innovation Agency (NIA Thailand)"
        ],
        "open_positions": [
            "Graduate RA in Functional Food Product Development",
            "Postdoctoral Researcher in Fermentation Biotechnology"
        ],
        "website_url": "https://agri.ubu.ac.th",
        "image_url": "https://images.unsplash.com/photo-1555396273-367ea4eb4db5?w=800&q=80"
    },
    {
        "id": "ubu_mekong_cultural_crossborder_lab",
        "name_th": "ศูนย์วิจัยสังคม วัฒนธรรม และการค้าระหว่างประเทศลุ่มน้ำโขง มหาวิทยาลัยอุบลราชธานี",
        "name_en": "Mekong Sub-Region Cross-Border Trade & Cultural Innovation Center",
        "university": "Ubon Ratchathani University",
        "university_th": "มหาวิทยาลัยอุบลราชธานี",
        "faculty": "Faculty of Liberal Arts",
        "faculty_th": "คณะศิลปศาสตร์",
        "department": "Division of Cross-Border Studies and International Relations",
        "department_th": "สาขาวิชาลุ่มน้ำโขงศึกษาและความสัมพันธ์ระหว่างประเทศ",
        "lead_advisor_id": "ubonratcha_collegeofl_kongphiantham_036",
        "member_faculty_ids": ["ubonratcha_collegeofl_kongphiantham_036", "ubonratcha_collegeofl_chanphuang_025"],
        "description": "ศูนย์วิจัยยุทธศาสตร์เพื่อการเชื่อมโยงความร่วมมือทางเศรษฐกิจ สังคม และภาษาศาสตร์ในอนุภูมิภาคลุ่มน้ำโขง (ไทย-ลาว-กัมพูชา-เวียดนาม) การวิจัยเส้นทางการค้าชายแดนและโลจิสติกส์อาเซียน",
        "research_domains": [
            "Cross-Border Trade Economics & ASEAN Logistics Connectivity",
            "Mekong Transboundary Water Governance & Ecological Justice",
            "Comparative Linguistics & Digital Oral History Preservation",
            "Migrant Worker Socio-Economic Integration in Border Economic Zones"
        ],
        "flagship_equipment": [
            "Cross-Border Geographic Information System (GIS) Data Lab",
            "Simultaneous Interpretation Soundproof Testing Booths",
            "Digital Audio-Visual Oral History Archive Suite",
            "Sub-regional Trade Flow Telemetry Dashboard"
        ],
        "industry_partners": [
            "Mekong Institute (MI Khon Kaen)",
            "Ubon Ratchathani Chamber of Commerce",
            "Ministry of Foreign Affairs of Thailand"
        ],
        "open_positions": [
            "Research Fellow in Cross-Border Logistics and Policy Analysis"
        ],
        "website_url": "https://la.ubu.ac.th",
        "image_url": "https://images.unsplash.com/photo-1526778548025-fa2f459cd5c1?w=800&q=80"
    },

    # =========================================================================
    # NORTHEASTERN REGION - Mahasarakham University (MSU - มหาวิทยาลัยมหาสารคาม)
    # =========================================================================
    {
        "id": "msu_informatics_smart_gis_lab",
        "name_th": "ห้องปฏิบัติการสารสนเทศภูมิศาสตร์อัจฉริยะและการวิเคราะห์ข้อมูลเชิงพื้นที่ มมส.",
        "name_en": "Smart Geospatial Information, Remote Sensing & Spatial Data Analytics Lab",
        "university": "Mahasarakham University",
        "university_th": "มหาวิทยาลัยมหาสารคาม",
        "faculty": "Faculty of Informatics",
        "faculty_th": "คณะวิทยาการสารสนเทศ",
        "department": "Department of Information Technology & Geospatial Computing",
        "department_th": "ภาควิชาเทคโนโลยีสารสนเทศ",
        "lead_advisor_id": "mahasarakh_facultyofi_saithong_005",
        "member_faculty_ids": ["mahasarakh_facultyofi_saithong_005", "mahasarakh_facultyofi_noiamka_009"],
        "description": "ศูนย์วิจัยข้อมูลสารสนเทศภูมิศาสตร์และดาวเทียมสำรวจชั้นนำของภาคอีสาน วิจัยแบบจำลองคาดการณ์ภัยแล้งและน้ำท่วมลุ่มน้ำชี การจำแนกพื้นที่เพาะปลูกอ้อยและข้าวด้วย AI และการวางผังเมืองอัจฉริยะ",
        "research_domains": [
            "AI-Driven Satellite Crop Classification & Yield Prediction",
            "Drought Early Warning & Groundwater Table Geostatistics",
            "Geospatial Big Data Infrastructure & Cloud GIS Services",
            "Disaster Evacuation Simulation for Isan River Basins"
        ],
        "flagship_equipment": [
            "High-Resolution Satellite Ground Receiver & Processing Cluster",
            "UAV Drone Fleet with Hyperspectral & LiDAR Sensors",
            "High-Performance Geo-Computation Server Array",
            "3D Virtual Geographic Environment Projection Center"
        ],
        "industry_partners": [
            "GISTDA",
            "Department of Disaster Prevention and Mitigation (DDPM)",
            "Mitr Phol Sugar Corporation"
        ],
        "open_positions": [
            "Graduate RA in Satellite Machine Learning & Computer Vision",
            "GIS Cloud Infrastructure Developer"
        ],
        "website_url": "https://it.msu.ac.th",
        "image_url": "https://images.unsplash.com/photo-1524661135-423995f22d0b?w=800&q=80"
    },
    {
        "id": "msu_digital_humanities_cultural_lab",
        "name_th": "ศูนย์นวัตกรรมมนุษยศาสตร์ดิจิทัลและคลังมรดกวัฒนธรรมอีสาน มหาวิทยาลัยมหาสารคาม",
        "name_en": "Digital Humanities & Isan Cultural Heritage Informatics Laboratory",
        "university": "Mahasarakham University",
        "university_th": "มหาวิทยาลัยมหาสารคาม",
        "faculty": "Faculty of Informatics",
        "faculty_th": "คณะวิทยาการสารสนเทศ",
        "department": "Department of Digital Media and Creative Computing",
        "department_th": "ภาควิชาสื่อนฤมิตและคอมพิวเตอร์สร้างสรรค์",
        "lead_advisor_id": "mahasarakh_facultyofi_noiamka_009",
        "member_faculty_ids": ["mahasarakh_facultyofi_noiamka_009", "mahasarakh_facultyofi_saithong_005"],
        "description": "ศูนย์กลางการอนุรักษ์มรดกภูมิปัญญาทางวัฒนธรรมอีสานด้วยเทคโนโลยีดิจิทัล การแปลงใบลานอักษรธรรมโบราณด้วย AI OCR การสร้างพิพิธภัณฑ์เสมือนจริง 3D Metaverse และการพัฒนาเกมส่งเสริมการเรียนรู้วัฒนธรรม",
        "research_domains": [
            "Ancient Palm-Leaf Manuscript AI-OCR & Semantic Knowledge Graphs",
            "3D Photogrammetry & Virtual Reality Cultural Heritage Tours",
            "Isan Ethnomusicology Digital Sound Archives & Audio Synthesis",
            "Serious Games & Gamification for Cultural Preservation"
        ],
        "flagship_equipment": [
            "Ultra-High-Resolution Book & Palm-Leaf Manuscript Scanner (Zeutschel)",
            "Artec 3D Handheld Precision Optical Scanners",
            "Spatial Audio Recording & Dolby Atmos Mixing Studio",
            "Motion Capture Body Tracking Rig for Folk Performance Recording"
        ],
        "industry_partners": [
            "Fine Arts Department (Ministry of Culture)",
            "Princess Maha Chakri Sirindhorn Anthropology Centre",
            "Thai PBS"
        ],
        "open_positions": [
            "Research Assistant in Optical Character Recognition for Ancient Scripts",
            "3D Virtual Reality Heritage Artist"
        ],
        "website_url": "https://it.msu.ac.th",
        "image_url": "https://images.unsplash.com/photo-1518709268805-4e9042af9f23?w=800&q=80"
    },

    # =========================================================================
    # CENTRAL REGION - Ramkhamhaeng University (RU - มหาวิทยาลัยรามคำแหง)
    # =========================================================================
    {
        "id": "ru_public_policy_governance_lab",
        "name_th": "ศูนย์วิจัยนโยบายสาธารณะ ธรรมาภิบาล และการบริหารงานยุติธรรม มหาวิทยาลัยรามคำแหง",
        "name_en": "Center for Public Policy Research, Good Governance & Justice Administration",
        "university": "Ramkhamhaeng University",
        "university_th": "มหาวิทยาลัยรามคำแหง",
        "faculty": "Faculty of Political Science",
        "faculty_th": "คณะรัฐศาสตร์",
        "department": "Department of Public Administration & Public Policy Analysis",
        "department_th": "ภาควิชารัฐประศาสนศาสตร์และการวิเคราะห์นโยบาย",
        "lead_advisor_id": "ramkhamhae_facultyofp_pongsung_031",
        "member_faculty_ids": ["ramkhamhae_facultyofp_pongsung_031", "ramkhamhae_facultyofp_sukcharoen_016"],
        "description": "ศูนย์วิจัยนโยบายสาธารณะที่ใหญ่ที่สุดแห่งหนึ่งของประเทศ มุ่งเน้นการประเมินความคุ้มค่าของกฎหมาย (Regulatory Impact Assessment - RIA) การต่อต้านการทุจริตในภาครัฐ และนวัตกรรมการมีส่วนร่วมของพลเมือง",
        "research_domains": [
            "Regulatory Impact Assessment (RIA) & Administrative Law Reform",
            "Anti-Corruption Analytics & Transparency in Procurement",
            "Local Administrative Decentralization & Fiscal Sustainability",
            "Electoral Systems, Democratic Resilience & Citizen Engagement"
        ],
        "flagship_equipment": [
            "Public Policy Simulation & Behavioral Experimentation Lab",
            "National Administrative Data Analytics Suite",
            "Focus Group Facility with Two-Way Mirror and Audio-Visual Tracking",
            "Legal & Legislative Text Mining Repository"
        ],
        "industry_partners": [
            "Office of the Public Sector Development Commission (OPDC)",
            "National Anti-Corruption Commission (NACC)",
            "King Prajadhipok's Institute (KPI)"
        ],
        "open_positions": [
            "Doctoral RA in Regulatory Impact Modeling",
            "Public Administration Research Officer"
        ],
        "website_url": "https://pol.ru.ac.th",
        "image_url": "https://images.unsplash.com/photo-1450133064473-71024230f91b?w=800&q=80"
    },

    # =========================================================================
    # CENTRAL REGION - Suan Sunandha Rajabhat University (SSRU - มรภ.สวนสุนันทา)
    # =========================================================================
    {
        "id": "ssru_creative_wellness_tourism_center",
        "name_th": "ศูนย์นวัตกรรมเศรษฐกิจสร้างสรรค์ การท่องเที่ยวเชิงสุขภาพ และอาหารชาววัง สวนสุนันทา",
        "name_en": "Suan Sunandha Center of Excellence in Creative Economy & Wellness Tourism",
        "university": "Suan Sunandha Rajabhat University",
        "university_th": "มหาวิทยาลัยราชภัฏสวนสุนันทา",
        "faculty": "Faculty of Education",
        "faculty_th": "คณะครุศาสตร์",
        "department": "Department of Early Childhood Education & Human Development",
        "department_th": "สาขาวิชาการศึกษาปฐมวัยและการพัฒนาทุนมนุษย์",
        "lead_advisor_id": "suansunand_facultyofe_thitisophonsak_005",
        "member_faculty_ids": ["suansunand_facultyofe_thitisophonsak_005", "suansunand_facultyofe_ngiwline_025"],
        "description": "ศูนย์ความเป็นเลิศชั้นนำในการต่อยอดมรดกทางวัฒนธรรมวังสวนสุนันทาสู่เศรษฐกิจสร้างสรรค์ระดับสากล การวิจัยและพัฒนาตำรับอาหารชาววังเพื่อสุขภาพ และการสร้างมาตรฐานอุตสาหกรรมท่องเที่ยวเชิงสุขภาพ (Wellness Tourism)",
        "research_domains": [
            "Authentic Royal Thai Culinary Science & Modern Nutraceuticals",
            "Medical Wellness Tourism Standards and Spa Accreditation",
            "Creative Cultural Product Design & Global Soft Power Branding",
            "Early Childhood Development Pedagogies & Brain-Based Learning"
        ],
        "flagship_equipment": [
            "Culinary Science Sensory Evaluation & Test Kitchen Laboratory",
            "Wellness Spa Bio-Metric and Stress Relaxation Monitoring Suite",
            "Creative Design & Textile Laser Cutting Studio",
            "Child Behavioral Observation and Neuro-Development Room"
        ],
        "industry_partners": [
            "Tourism Authority of Thailand (TAT)",
            "Department of Thai Traditional and Alternative Medicine",
            "Thai Spa Association"
        ],
        "open_positions": [
            "Master's RA in Gastronomy Science and Food Heritage",
            "Wellness Tourism Product Design Specialist"
        ],
        "website_url": "https://ssru.ac.th",
        "image_url": "https://images.unsplash.com/photo-1540555700478-4be289fbecef?w=800&q=80"
    },

    # =========================================================================
    # NORTHERN REGION - University of Phayao (UP - มหาวิทยาลัยพะเยา)
    # =========================================================================
    {
        "id": "up_renewable_energy_clean_env_lab",
        "name_th": "ศูนย์วิจัยพลังงานทดแทน ชุมชนคาร์บอนต่ำ และสิ่งแวดล้อม มหาวิทยาลัยพะเยา",
        "name_en": "Renewable Energy, Low-Carbon Community & Environmental Innovation Lab",
        "university": "University of Phayao",
        "university_th": "มหาวิทยาลัยพะเยา",
        "faculty": "School of Energy and Environment",
        "faculty_th": "คณะพลังงานและสิ่งแวดล้อม",
        "department": "Department of Renewable Energy Technology",
        "department_th": "สาขาวิชาเทคโนโลยีพลังงานทดแทน",
        "lead_advisor_id": "up_energy_wittaya_001",
        "member_faculty_ids": ["up_energy_wittaya_001"],
        "description": "มุ่งเน้นการวิจัยพัฒนาเทคโนโลยีพลังงานแสงอาทิตย์แบบลอยน้ำบนกว๊านพะเยา การแปรรูปขยะมูลฝอยชุมชนเป็นเชื้อเพลิงชีวมวลอัดแท่ง และการประเมินรอยเท้าคาร์บอน (Carbon Footprint) ในชุมชนเกษตรกรรมล้านนา",
        "research_domains": [
            "Floating Solar PV Integration on Freshwater Inland Lakes",
            "Community Municipal Solid Waste-to-Energy Pyrolysis",
            "Lanna Agro-Forestry Carbon Sequestration Modeling",
            "Small-Scale Hydroelectric Turbines for Mountain Villages"
        ],
        "flagship_equipment": [
            "Floating PV Demonstration Platform at Kwan Phayao",
            "Bomb Calorimeter for Solid Fuel Energy Content",
            "Thermal Imaging Infrared Drone for Solar Module Inspection",
            "Mobile Flue Gas Emission Gas Chromatography Analyzer"
        ],
        "industry_partners": [
            "Phayao Provincial Energy Office",
            "Provincial Electricity Authority (PEA)",
            "Kwan Phayao Wetland Conservation Network"
        ],
        "open_positions": [
            "Master's RA: Floating Solar Microclimatic Interaction",
            "Environmental Carbon Accounting Officer"
        ],
        "website_url": "https://energy.up.ac.th",
        "image_url": "https://images.unsplash.com/photo-1497440001374-f26997328c1b?w=800&q=80"
    },

    # =========================================================================
    # SOUTHERN REGION - Walailak University (WU - มหาวิทยาลัยวลัยลักษณ์)
    # =========================================================================
    {
        "id": "wu_tropical_medicine_marine_ecology",
        "name_th": "ศูนย์ความเป็นเลิศด้านการวิจัยเวชศาสตร์เขตร้อนและนิเวศวิทยาทางทะเล มหาวิทยาลัยวลัยลักษณ์",
        "name_en": "Center of Excellence in Tropical Medicine & Coastal Marine Ecology",
        "university": "Walailak University",
        "university_th": "มหาวิทยาลัยวลัยลักษณ์",
        "faculty": "School of Medicine",
        "faculty_th": "สำนักวิชาแพทยศาสตร์",
        "department": "Division of Tropical Infectious Diseases & Vector Biology",
        "department_th": "สาขาวิชาโรคติดเชื้อเขตร้อนและชีววิทยาพาหะ",
        "lead_advisor_id": "regionalun_facultymem_thamrongrat_041",
        "member_faculty_ids": ["regionalun_facultymem_thamrongrat_041", "regionalun_facultymem_kaewprasertrakk_042"],
        "description": "ศูนย์วิจัยทางการแพทย์และวิทยาศาสตร์ชายฝั่งทะเลอ่าวไทยตอนใต้ มุ่งเน้นการเฝ้าระวังโรคติดต่อเขตร้อน พาหะนำโรคในป่าชายเลน และการศึกษาสารสกัดจากพืชสมุนไพรและสัตว์ทะเลสำหรับต้านเชื้อดื้อยา",
        "research_domains": [
            "Arboviral Vector Ecology (Aedes & Culex Mosquito Genetics)",
            "Marine Microbial Metabolites as Novel Antibacterial Leads",
            "Malaria and Zoonotic Parasite Genomic Surveillance in Southern Thailand",
            "Coastal Mangrove Biodiversity & Benthic Ecosystem Resilience"
        ],
        "flagship_equipment": [
            "Inverted Fluorescence Microscopy with Micro-manipulators",
            "Biosafety Level 2+ Insectary and Vector Rearing Facility",
            "High-Throughput Microplate Reader (SpectraMax iD5)",
            "Automated Real-Time PCR Detection System"
        ],
        "industry_partners": [
            "Walailak University Hospital",
            "Nakhon Si Thammarat Provincial Public Health Office",
            "Armed Forces Research Institute of Medical Sciences (AFRIMS)"
        ],
        "open_positions": [
            "Postdoctoral Researcher in Vector-Borne Pathogen Genomics",
            "Graduate RA in Marine Natural Antibacterial Agents"
        ],
        "website_url": "https://med.wu.ac.th",
        "image_url": "https://images.unsplash.com/photo-1579684385127-1ef15d508118?w=800&q=80"
    },

    # =========================================================================
    # CENTRAL REGION - KMUTT (มจธ. บางมด)
    # =========================================================================
    {
        "id": "kmutt_clean_energy_solid_oxide_fuel_cell",
        "name_th": "ศูนย์วิจัยวัสดุพลังงานขั้นสูงและเซลล์เชื้อเพลิงออกไซด์ของแข็ง มจธ.",
        "name_en": "Center of Excellence in Clean Energy Materials & Solid Oxide Fuel Cells (SOFC KMUTT)",
        "university": "King Mongkut's University of Technology Thonburi",
        "university_th": "มหาวิทยาลัยเทคโนโลยีพระจอมเกล้าธนบุรี",
        "faculty": "Faculty of Engineering",
        "faculty_th": "คณะวิศวกรรมศาสตร์",
        "department": "Department of Chemical Engineering",
        "department_th": "ภาควิชาวิศวกรรมเคมี",
        "lead_advisor_id": "kmutt_chem_suwit_001",
        "member_faculty_ids": ["kmutt_chem_suwit_001"],
        "description": "ศูนย์วิจัยเฉพาะทางระดับแนวหน้าของอาเซียนด้านเซลล์เชื้อเพลิงออกไซด์ของแข็ง (SOFC) และการสังเคราะห์ไฮโดรเจนบริสุทธิ์เพื่อระบบพลังงานสะอาด การออกแบบตัวเร่งปฏิกิริยานาโนสำหรับปฏิกิริยา Steam Methane Reforming",
        "research_domains": [
            "Solid Oxide Fuel Cell (SOFC) & Solid Oxide Electrolysis Cell (SOEC)",
            "High-Temperature Ceramic Membrane Reactors for Pure Hydrogen",
            "CO2 Methanation and Synthetic Natural Gas (SNG) Catalysis",
            "Electrochemical Impedance Spectroscopy (EIS) Modeling at High Temp"
        ],
        "flagship_equipment": [
            "High-Temperature SOFC Single Cell and Short-Stack Testing Station (up to 1,000 deg C)",
            "Solartron High-Frequency Impedance Analyzer with Temperature Controller",
            "Automated Chemisorption & Catalyst Surface Area Analyzer (Autosorb iQ)",
            "High-Temperature Tubular Sintering Furnaces (1,700 deg C)"
        ],
        "industry_partners": [
            "PTT Exploration and Production (PTTEP)",
            "SCG Chemicals Public Company Limited",
            "Electricity Generating Authority of Thailand (EGAT)"
        ],
        "open_positions": [
            "Postdoctoral Researcher: Reversible Solid Oxide Cells for Green Hydrogen",
            "PhD Fellowship in Ceramic Electrolyte Defect Chemistry"
        ],
        "website_url": "https://che.kmutt.ac.th",
        "image_url": "https://images.unsplash.com/photo-1507668077129-56e32842fceb?w=800&q=80"
    }
]

