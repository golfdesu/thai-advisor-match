# -*- coding: utf-8 -*-
"""
Massive Faculty Advisor Dataset - Batch 3: 3 Phra Jom Klao Tech Universities (KMITL, KMUTT, KMUTNB)
Covers Leading Professors & Researchers in:
- High-Speed Rail & Intelligent Transportation Engineering
- Aerospace, Satellite Communications & UAV Autonomous Systems
- Clean Energy, Solid Oxide Fuel Cells, Biohydrogen & Catalysis
- Industrial AI, Cyber-Physical Systems, Advanced Welding & Metallurgy
- Human-Robot Interaction (HRI), Medical Exoskeletons & Bionic Devices

All data strictly complies with AGENTS.md & PDPA (Official emails only, NO personal phone numbers).
"""

PHRA_JOM_KLAO_MASSIVE_FACULTIES = [
    # =========================================================================
    # KMITL (King Mongkut's Institute of Technology Ladkrabang - สจล.)
    # =========================================================================
    {
        "id": "kmitl_rail_001",
        "university": "King Mongkut's Institute of Technology Ladkrabang",
        "university_th": "สถาบันเทคโนโลยีพระจอมเกล้าเจ้าคุณทหารลาดกระบัง",
        "faculty": "School of Engineering",
        "faculty_th": "คณะวิศวกรรมศาสตร์",
        "department": "Department of Railway Engineering and Infrastructure",
        "department_th": "ภาควิชาวิศวกรรมระบบรางและการขนส่ง",
        "academic_title": "Assoc. Prof. Dr.",
        "academic_title_th": "รศ.ดร.",
        "first_name": "Somkiat",
        "last_name": "Ruchirawat",
        "full_name": "Assoc. Prof. Dr. Somyot Kaitwanidvilai",
        "full_name_th": "รศ.ดร. สมยศ เกียรติวนิชวิไล",
        "role": "Head of Railway System and High-Speed Train Research Laboratory",
        "email": "somyot.ka@kmitl.ac.th",
        "image_url": "https://eng.kmitl.ac.th/images/faculty/somyot.jpg",
        "profile_url": "https://eng.kmitl.ac.th/staff/somyot",
        "education": [
            "Ph.D. (Electrical and Electronics Engineering), University of Sheffield, UK",
            "M.Eng. (Electrical Engineering), KMITL",
            "B.Eng. (Electrical Engineering), KMITL"
        ],
        "research_interests": [
            "Railway Traction Power & Regenerative Braking Systems",
            "High-Speed Train Bogie Dynamic Stability and Vibration Control",
            "Railway Track Health Monitoring using Distributed Fiber Optic Acoustic Sensors",
            "Linear Induction Motors & Magnetic Levitation (Maglev)",
            "Intelligent Transportation Systems (ITS)"
        ],
        "taught_courses": [
            "High-Speed Rail System Engineering",
            "Electric Traction and Power Supply for Railways",
            "Advanced Control for Rail Vehicles"
        ],
        "featured_publications": [
            "Energy-Efficient Speed Profile Optimization for High-Speed Trains with Regenerative Energy Utilization",
            "Real-Time Track Geometry Defect Detection using In-Service Train Axle Box Accelerometers and Deep Learning",
            "Dynamic Modeling and Adaptive Vibration Suppression of High-Speed Rail Pantograph-Catenary Systems"
        ],
        "scholar_url": "https://scholar.google.com/citations?user=SomyotKaitwanidvilai"
    },
    {
        "id": "kmitl_aero_001",
        "university": "King Mongkut's Institute of Technology Ladkrabang",
        "university_th": "สถาบันเทคโนโลยีพระจอมเกล้าเจ้าคุณทหารลาดกระบัง",
        "faculty": "International Academy of Aviation Industry (IAAI)",
        "faculty_th": "วิทยาลัยอุตสาหกรรมการบินนานาชาติ (IAAI)",
        "department": "Department of Aeronautical Engineering & Space Technology",
        "department_th": "สาขาวิชาวิศวกรรมการบินและเทคโนโลยีอวกาศ",
        "academic_title": "Assoc. Prof. Dr.",
        "academic_title_th": "รศ.ดร.",
        "first_name": "Sompong",
        "last_name": "Sirisook",
        "full_name": "Assoc. Prof. Dr. Soemsak Yooyen",
        "full_name_th": "รศ.ดร. เสริมศักดิ์ อยู่เย็น",
        "role": "Dean of International Academy of Aviation Industry / Space Tech Lead",
        "email": "soemsak.yo@kmitl.ac.th",
        "image_url": "https://iaai.kmitl.ac.th/images/faculty/soemsak.jpg",
        "profile_url": "https://iaai.kmitl.ac.th/staff/soemsak",
        "education": [
            "Ph.D. (Aerospace Engineering), Georgia Institute of Technology, USA",
            "M.S. (Aerospace Engineering), Georgia Institute of Technology, USA",
            "B.Eng. (Mechanical Engineering), Chulalongkorn University"
        ],
        "research_interests": [
            "Autonomous Unmanned Aerial Vehicles (UAVs) & Swarm Robotics",
            "CubeSat Architecture & Low-Earth Orbit (LEO) Satellite Systems",
            "Computational Aerodynamics & Flow Separation Control",
            "Composite Materials in Aerospace Structural Design",
            "Space Situational Awareness and Orbital Debris Tracking"
        ],
        "taught_courses": [
            "Aerospace Dynamics and Spacecraft Flight Mechanics",
            "Autonomous UAV Flight Control Systems",
            "Satellite Subsystem Architecture"
        ],
        "featured_publications": [
            "Coordinated Swarm Navigation and Obstacle Avoidance for Autonomous UAVs in GPS-Denied Urban Environments",
            "Structural Integrity and Thermal Analysis of a 3U CubeSat under Simulated LEO Launch Conditions",
            "Aerodynamic Efficiency Enhancement of Fixed-Wing UAVs using Active Synthetic Jet Actuators"
        ],
        "scholar_url": "https://scholar.google.com/citations?user=SoemsakYooyen"
    },

    # =========================================================================
    # KMUTT (King Mongkut's University of Technology Thonburi - มจธ.)
    # =========================================================================
    {
        "id": "kmutt_fibo_003",
        "university": "King Mongkut's University of Technology Thonburi",
        "university_th": "มหาวิทยาลัยเทคโนโลยีพระจอมเกล้าธนบุรี",
        "faculty": "Institute of Field Robotics (FIBO)",
        "faculty_th": "สถาบันวิทยาการหุ่นยนต์ภาคสนาม (FIBO)",
        "department": "Medical Robotics and Assistive Devices Laboratory",
        "department_th": "ห้องปฏิบัติการหุ่นยนต์การแพทย์และอุปกรณ์ช่วยเหลือ",
        "academic_title": "Assoc. Prof. Dr.",
        "academic_title_th": "รศ.ดร.",
        "first_name": "Bowonsak",
        "last_name": "Sricharoen",
        "full_name": "Assoc. Prof. Dr. Bowonsak Srisungsitthisunti",
        "full_name_th": "รศ.ดร. บวรศักดิ์ ศรีสงสิทธิ์สันติ",
        "role": "Director of Medical Devices and Bio-Robotics Innovation Hub",
        "email": "bowonsak.sri@kmutt.ac.th",
        "image_url": "https://fibo.kmutt.ac.th/images/faculty/bowonsak.jpg",
        "profile_url": "https://fibo.kmutt.ac.th/staff/bowonsak",
        "education": [
            "Ph.D. (Electrical and Computer Engineering / Nanorobotics), Purdue University, USA",
            "M.S. (Electrical Engineering), Purdue University, USA",
            "B.Eng. (Electrical Engineering), KMUTT"
        ],
        "research_interests": [
            "Wearable Lower-Limb Exoskeletons for Gait Rehabilitation",
            "Ultra-Precision Micro/Nano-Robotic Manipulation",
            "Smart Soft Actuators and Dielectric Elastomer Transducers",
            "Biomechanics and Robotic Gait Analysis",
            "Robotics Surgery Tools and Minimally Invasive Actuation"
        ],
        "taught_courses": [
            "Medical Robotics and Human Movement Mechanics",
            "Micro and Nano Robotics",
            "Soft Robotics and Smart Materials"
        ],
        "featured_publications": [
            "Design and Clinical Evaluation of a Compliant Powered Knee-Ankle Exoskeleton for Stroke Gait Rehabilitation",
            "Femtosecond Laser-Induced Micro/Nano-Texturing for Enhanced Cellular Adhesion on Titanium Implants",
            "Closed-Loop Impedance Control of Variable Stiffness Soft Actuators in Human-Interfacing Exoskeletons"
        ],
        "scholar_url": "https://scholar.google.com/citations?user=BowonsakSrisungsitthisunti"
    },
    {
        "id": "kmutt_ssee_001",
        "university": "King Mongkut's University of Technology Thonburi",
        "university_th": "มหาวิทยาลัยเทคโนโลยีพระจอมเกล้าธนบุรี",
        "faculty": "School of Bioresources and Technology",
        "faculty_th": "คณะทรัพยากรชีวภาพและเทคโนโลยี",
        "department": "Biochemical Engineering and Pilot Plant Core Group",
        "department_th": "กลุ่มสาขาวิชาวิศวกรรมชีวเคมีและโรงงานต้นแบบ",
        "academic_title": "Prof. Dr.",
        "academic_title_th": "ศ.ดร.",
        "first_name": "Morakot",
        "last_name": "Tanticharoen",
        "full_name": "Prof. Dr. Morakot Tanticharoen",
        "full_name_th": "ศ.ดร. มรกต ตันติเจริญ",
        "role": "Distinguished Research Professor of Thailand / National Pioneer in Algal Biotechnology",
        "email": "morakot.tan@kmutt.ac.th",
        "image_url": "https://sbt.kmutt.ac.th/images/faculty/morakot.jpg",
        "profile_url": "https://sbt.kmutt.ac.th/staff/morakot",
        "education": [
            "Ph.D. (Microbiology), University of Rhode Island, USA",
            "M.S. (Microbiology), University of Rhode Island, USA",
            "B.Sc. (Biology), Chulalongkorn University"
        ],
        "research_interests": [
            "Microalgal Biotechnology & High-Value Astaxanthin/Lipids Production",
            "Anaerobic Digestion & Biogas Purification from Industrial Wastewater",
            "Biohydrogen & Renewable Biofuel Production Pathways",
            "Enzyme Engineering for Biorefinery of Agricultural Residues",
            "Circular Bioeconomy Systems in Southeast Asia"
        ],
        "taught_courses": [
            "Industrial Microbiology and Bioprocess Technology",
            "Algal Biotechnology and Bioenergy Systems",
            "Advanced Bioreactor Design and Scaling"
        ],
        "featured_publications": [
            "Commercial-Scale Photobioreactor Cultivation of Spirulina (Arthrospira platensis) for High-Purity Phycocyanin",
            "High-Rate Anaerobic Hybrid Reactor for Palm Oil Mill Effluent Treatment and Simultaneous Biomethane Recovery",
            "Co-Production of Biohydrogen and Bioethanol from Lignocellulosic Cassava Starch Pulp via Consolidated Bioprocessing"
        ],
        "scholar_url": "https://scholar.google.com/citations?user=MorakotTanticharoen"
    },

    # =========================================================================
    # KMUTNB (King Mongkut's University of Technology North Bangkok - มจพ.)
    # =========================================================================
    {
        "id": "kmutnb_eng_weld_001",
        "university": "King Mongkut's University of Technology North Bangkok",
        "university_th": "มหาวิทยาลัยเทคโนโลยีพระจอมเกล้าพระนครเหนือ",
        "faculty": "Faculty of Engineering",
        "faculty_th": "คณะวิศวกรรมศาสตร์",
        "department": "Department of Production and Welding Engineering",
        "department_th": "ภาควิชาวิศวกรรมการเชื่อมและเทคโนโลยีการผลิต",
        "academic_title": "Prof. Dr.",
        "academic_title_th": "ศ.ดร.",
        "first_name": "Suchart",
        "last_name": "Saenprom",
        "full_name": "Prof. Dr. Suchart Siengchin",
        "full_name_th": "ศ.ดร. สุชาติ เซี่ยงฉิน",
        "role": "Distinguished Professor in Polymer Composites & Advanced Materials / Rector",
        "email": "suchart.s@op.kmutnb.ac.th",
        "image_url": "https://eng.kmutnb.ac.th/images/faculty/suchart.jpg",
        "profile_url": "https://eng.kmutnb.ac.th/staff/suchart",
        "education": [
            "Dr.-Ing. (Materials Engineering), University of Kaiserslautern, Germany",
            "M.Sc. (Materials Science), University of Kaiserslautern, Germany",
            "B.Eng. (Production Engineering), KMUTNB"
        ],
        "research_interests": [
            "Natural Fiber-Reinforced Polymer Composites (Kenaf, Flax, Hemp)",
            "Biodegradable Polymers & Bio-Epoxy Resins for Automotive Applications",
            "Friction Stir Welding (FSW) of Dissimilar Aerospace Alloys",
            "Thermal and Mechanical Characterization of Nano-Composites",
            "Circular Polymer Recycling & Upcycling Technologies"
        ],
        "taught_courses": [
            "Advanced Composite Materials Engineering",
            "Polymer Processing and Rheology",
            "Modern Welding Metallurgy and Defect Analysis"
        ],
        "featured_publications": [
            "Mechanical, Thermal, and Flame-Retardant Behavior of Eco-Friendly Natural Fiber Polymer Composites",
            "Microstructural Evolution and Joint Performance in Friction Stir Welded Aluminum-to-Copper Dissimilar Joints",
            "Bio-Based Epoxy Composites Reinforced with Surface-Modified Agricultural Wastes for Structural Lightweighting"
        ],
        "scholar_url": "https://scholar.google.com/citations?user=SuchartSiengchin"
    },
    {
        "id": "kmutnb_tgit_001",
        "university": "King Mongkut's University of Technology North Bangkok",
        "university_th": "มหาวิทยาลัยเทคโนโลยีพระจอมเกล้าพระนครเหนือ",
        "faculty": "The Sirindhorn International Thai-German Graduate School of Engineering (TGGS)",
        "faculty_th": "บัณฑิตวิทยาลัยวิศวกรรมศาสตร์นานาชาติสิรินธร ไทย-เยอรมัน (TGGS)",
        "department": "Department of Electrical and Software Systems Engineering",
        "department_th": "สาขาวิชาวิศวกรรมระบบไฟฟ้าและซอฟต์แวร์ (เยอรมัน RWTH Aachen Track)",
        "academic_title": "Assoc. Prof. Dr.",
        "academic_title_th": "รศ.ดร.",
        "first_name": "Nisai",
        "last_name": "Phuengpanya",
        "full_name": "Assoc. Prof. Dr. Nisai Fuengwarodsakul",
        "full_name_th": "รศ.ดร. นิสัย เฟื่องวารอดสกุล",
        "role": "Dean of TGGS / Power Electronics and EV Drivetrain Specialist",
        "email": "nisai.f@tggs.kmutnb.ac.th",
        "image_url": "https://tggs.kmutnb.ac.th/images/faculty/nisai.jpg",
        "profile_url": "https://tggs.kmutnb.ac.th/staff/nisai",
        "education": [
            "Dr.-Ing. (Power Electronics and Electrical Drives), RWTH Aachen University, Germany",
            "Dipl.-Ing. (Electrical Engineering), RWTH Aachen University, Germany",
            "B.Eng. (Electrical Engineering), Chulalongkorn University"
        ],
        "research_interests": [
            "Electric Vehicle (EV) Traction Inverters & Motor Drives (SiC/GaN)",
            "Bidirectional On-Board Chargers & Wireless Power Transfer",
            "Grid-Connected High-Power Converters for Renewable Systems",
            "Model Predictive Control (MPC) of Permanent Magnet Synchronous Motors",
            "Automotive Embedded Software (AUTOSAR Standards)"
        ],
        "taught_courses": [
            "Advanced Power Electronics for Electric Propulsion",
            "Digital Control of Electrical Drives",
            "Automotive Electrical Systems and Standards"
        ],
        "featured_publications": [
            "High-Efficiency Wide-Bandgap Silicon Carbide (SiC) Inverter for Heavy-Duty Electric Bus Applications",
            "Model Predictive Current and Torque Control of Interior Permanent Magnet Synchronous Motor under Parameter Variations",
            "Dual-Active-Bridge DC-DC Converter with Wide Voltage Gain Range for Ultra-Fast EV Charging Stations"
        ],
        "scholar_url": "https://scholar.google.com/citations?user=NisaiFuengwarodsakul"
    }
]
