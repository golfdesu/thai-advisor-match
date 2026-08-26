import json
import os
from pathlib import Path

courses = [
    # =========================================================================
    # KMUTT (มหาวิทยาลัยเทคโนโลยีพระจอมเกล้าธนบุรี)
    # =========================================================================
    {
        "id": "kmutt_fibo_robotics_beng",
        "title_th": "หลักสูตรวิศวกรรมศาสตรบัณฑิต สาขาวิชาวิศวกรรมหุ่นยนต์และระบบอัตโนมัติ",
        "title_en": "Bachelor of Engineering Program in Robotics and Automation Engineering",
        "degree_level": "ปริญญาตรี",
        "degree_name": "วศ.บ. (วิศวกรรมหุ่นยนต์และระบบอัตโนมัติ)",
        "university": "King Mongkut's University of Technology Thonburi",
        "university_th": "มหาวิทยาลัยเทคโนโลยีพระจอมเกล้าธนบุรี",
        "faculty": "Institute of Field Robotics (FIBO)",
        "faculty_th": "สถาบันวิทยาการหุ่นยนต์ภาคสนาม (ฟีโบ้)",
        "department": "Robotics and Automation Engineering",
        "department_th": "สาขาวิชาวิศวกรรมหุ่นยนต์และระบบอัตโนมัติ",
        "program_type": "ภาคปกติ",
        "duration_years": "4 ปี",
        "total_credits": "136 หน่วยกิต",
        "tuition_per_semester": "28,000 บาท",
        "tuition_total": "224,000 บาท",
        "description": "หลักสูตรบูรณาการสหวิทยาการด้านกลศาสตร์ อิเล็กทรอนิกส์ การควบคุม และปัญญาประดิษฐ์เพื่อสร้างหุ่นยนต์และระบบอัตโนมัติอัจฉริยะ เน้นการเรียนรู้แบบ Outcome-based และ Project-based Learning ตั้งแต่ปี 1 จนถึงปี 4 ร่วมกับภาคอุตสาหกรรม",
        "curriculum_highlights": [
            "Industrial & Service Robotics Design",
            "Sensors, Actuators & Embedded Systems",
            "Robot Kinematics, Dynamics & Control",
            "Autonomous Mobile Robots & ROS (Robot Operating System)",
            "AI & Computer Vision for Robotics",
            "Automation System Integration & PLC"
        ],
        "career_paths": [
            "Robotics Engineer",
            "Automation & Control Engineer",
            "Robotics AI / Vision Developer",
            "System Integration Engineer",
            "R&D Engineer in Advanced Automation"
        ],
        "tags": ["Robotics", "Automation", "AI", "Embedded Systems", "Engineering", "KMUTT", "Bachelor"],
        "website_url": "https://www.fibo.kmutt.ac.th"
    },
    {
        "id": "kmutt_fibo_robotics_meng",
        "title_th": "หลักสูตรวิศวกรรมศาสตรมหาบัณฑิต สาขาวิชาวิทยาการหุ่นยนต์และระบบอัตโนมัติ",
        "title_en": "Master of Engineering Program in Robotics and Automation",
        "degree_level": "ปริญญาโท",
        "degree_name": "วศ.ม. (วิทยาการหุ่นยนต์และระบบอัตโนมัติ)",
        "university": "King Mongkut's University of Technology Thonburi",
        "university_th": "มหาวิทยาลัยเทคโนโลยีพระจอมเกล้าธนบุรี",
        "faculty": "Institute of Field Robotics (FIBO)",
        "faculty_th": "สถาบันวิทยาการหุ่นยนต์ภาคสนาม (ฟีโบ้)",
        "department": "Robotics and Automation",
        "department_th": "วิทยาการหุ่นยนต์และระบบอัตโนมัติ",
        "program_type": "ภาคปกติ",
        "duration_years": "2 ปี",
        "total_credits": "36 หน่วยกิต",
        "tuition_per_semester": "45,000 บาท",
        "tuition_total": "180,000 บาท",
        "description": "มุ่งเน้นการวิจัยและพัฒนานวัตกรรมหุ่นยนต์ขั้นสูง การประยุกต์ใช้ปัญญาประดิษฐ์เชิงลึก ระบบอัตโนมัติระดับอุตสาหกรรม 4.0 และการสร้างเทคโนโลยีเชิงลึก (Deep Tech) เพื่อตอบสนองความต้องการของภาคอุตสาหกรรมและสถาบันวิจัยระดับสากล",
        "curriculum_highlights": [
            "Advanced Robot Kinematics and Dynamics",
            "Deep Learning & Reinforcement Learning in Robotics",
            "Smart Manufacturing & Industrial IoT",
            "Human-Robot Interaction (HRI)",
            "Master Thesis Research in Advanced Robotics"
        ],
        "career_paths": [
            "Senior Robotics Engineer",
            "AI Robotics Researcher",
            "Industrial Automation Consultant",
            "Chief Technology Officer (CTO) in Robotics Startup",
            "University Lecturer"
        ],
        "tags": ["Robotics", "Automation", "Deep Tech", "AI", "Engineering", "KMUTT", "Master"],
        "website_url": "https://www.fibo.kmutt.ac.th"
    },
    {
        "id": "kmutt_cpe_beng",
        "title_th": "หลักสูตรวิศวกรรมศาสตรบัณฑิต สาขาวิชาวิศวกรรมคอมพิวเตอร์",
        "title_en": "Bachelor of Engineering Program in Computer Engineering",
        "degree_level": "ปริญญาตรี",
        "degree_name": "วศ.บ. (วิศวกรรมคอมพิวเตอร์)",
        "university": "King Mongkut's University of Technology Thonburi",
        "university_th": "มหาวิทยาลัยเทคโนโลยีพระจอมเกล้าธนบุรี",
        "faculty": "Faculty of Engineering",
        "faculty_th": "คณะวิศวกรรมศาสตร์",
        "department": "Department of Computer Engineering",
        "department_th": "ภาควิชาวิศวกรรมคอมพิวเตอร์",
        "program_type": "ภาคปกติ",
        "duration_years": "4 ปี",
        "total_credits": "134 หน่วยกิต",
        "tuition_per_semester": "24,000 บาท",
        "tuition_total": "192,000 บาท",
        "description": "หลักสูตรวิศวกรรมคอมพิวเตอร์ชั้นนำที่เน้นการเรียนรู้แบบบูรณาการทั้งด้านฮาร์ดแวร์ ซอฟต์แวร์ ระบบเครือข่าย ปัญญาประดิษฐ์ และความมั่นคงปลอดภัยไซเบอร์ เพื่อสร้างวิศวกรคอมพิวเตอร์ที่มีทักษะการแก้ปัญหาทางวิศวกรรมขั้นสูง",
        "curriculum_highlights": [
            "Data Structures, Algorithms & Problem Solving",
            "Computer Architecture & Microprocessor Systems",
            "Software Architecture & Full-Stack Engineering",
            "Computer Networks & Cyber Threat Intelligence",
            "Artificial Intelligence & Machine Learning Systems",
            "Cloud Infrastructure & Distributed Computing"
        ],
        "career_paths": [
            "Software Engineer",
            "Full Stack Developer",
            "Embedded Systems Engineer",
            "Cloud & DevOps Engineer",
            "Cybersecurity Engineer",
            "AI/ML Engineer"
        ],
        "tags": ["Computer Engineering", "Software Engineering", "AI", "Cloud", "Cybersecurity", "KMUTT", "Bachelor"],
        "website_url": "https://www.cpe.kmutt.ac.th"
    },
    {
        "id": "kmutt_cpe_inter_beng",
        "title_th": "หลักสูตรวิศวกรรมศาสตรบัณฑิต สาขาวิชาวิศวกรรมคอมพิวเตอร์ (หลักสูตรนานาชาติ)",
        "title_en": "Bachelor of Engineering Program in Computer Engineering (International Program)",
        "degree_level": "ปริญญาตรี",
        "degree_name": "วศ.บ. (วิศวกรรมคอมพิวเตอร์)",
        "university": "King Mongkut's University of Technology Thonburi",
        "university_th": "มหาวิทยาลัยเทคโนโลยีพระจอมเกล้าธนบุรี",
        "faculty": "Faculty of Engineering",
        "faculty_th": "คณะวิศวกรรมศาสตร์",
        "department": "Department of Computer Engineering",
        "department_th": "ภาควิชาวิศวกรรมคอมพิวเตอร์",
        "program_type": "นานาชาติ",
        "duration_years": "4 ปี",
        "total_credits": "134 หน่วยกิต",
        "tuition_per_semester": "65,000 บาท",
        "tuition_total": "520,000 บาท",
        "description": "หลักสูตรนานาชาติที่จัดการเรียนการสอนเป็นภาษาอังกฤษ 100% มีความร่วมมือกับมหาวิทยาลัยชั้นนำในต่างประเทศ (เช่น University of Missouri) เน้นมาตรฐานระดับสากลในด้านการพัฒนาระบบคลาวด์ ปัญญาประดิษฐ์ และวิศวกรรมซอฟต์แวร์ระดับโลก",
        "curriculum_highlights": [
            "Global Software Engineering & Architecture",
            "Deep Learning & Advanced Computer Vision",
            "Distributed Systems & High-Performance Computing",
            "Information Security & Privacy Engineering",
            "International Capstone Project & Internship"
        ],
        "career_paths": [
            "Global Software Engineer",
            "AI Solutions Architect",
            "International DevOps Specialist",
            "Cybersecurity Consultant",
            "Technology Entrepreneur"
        ],
        "tags": ["Computer Engineering", "International", "AI", "Software Engineering", "Cloud", "KMUTT", "Bachelor"],
        "website_url": "https://www.cpe.kmutt.ac.th"
    },
    {
        "id": "kmutt_cpe_meng",
        "title_th": "หลักสูตรวิศวกรรมศาสตรมหาบัณฑิต สาขาวิชาวิศวกรรมคอมพิวเตอร์ (หลักสูตรนานาชาติ)",
        "title_en": "Master of Engineering Program in Computer Engineering (International Program)",
        "degree_level": "ปริญญาโท",
        "degree_name": "วศ.ม. (วิศวกรรมคอมพิวเตอร์)",
        "university": "King Mongkut's University of Technology Thonburi",
        "university_th": "มหาวิทยาลัยเทคโนโลยีพระจอมเกล้าธนบุรี",
        "faculty": "Faculty of Engineering",
        "faculty_th": "คณะวิศวกรรมศาสตร์",
        "department": "Department of Computer Engineering",
        "department_th": "ภาควิชาวิศวกรรมคอมพิวเตอร์",
        "program_type": "นานาชาติ",
        "duration_years": "2 ปี",
        "total_credits": "36 หน่วยกิต",
        "tuition_per_semester": "55,000 บาท",
        "tuition_total": "220,000 บาท",
        "description": "หลักสูตรปริญญาโทนานาชาติ มุ่งเน้นการวิจัยขั้นสูงในสาขาวิทยาการข้อมูล ปัญญาประดิษฐ์ การประมวลผลสัญญาณดิจิทัล และความปลอดภัยไซเบอร์ เพื่อผลิตนักวิจัยและผู้เชี่ยวชาญระดับสูงสำหรับอุตสาหกรรมเทคโนโลยีขั้นสูง",
        "curriculum_highlights": [
            "Advanced Artificial Intelligence & Natural Language Processing",
            "High Performance Parallel Computing",
            "Advanced Cyber Threat Hunting & Mitigation",
            "Data Science at Scale & Distributed Databases",
            "Research Methodology and Master Thesis"
        ],
        "career_paths": [
            "Lead Computer Systems Architect",
            "Principal AI/ML Scientist",
            "Security Architect",
            "Research Scientist",
            "Academic Faculty"
        ],
        "tags": ["Computer Engineering", "International", "AI", "Data Science", "Research", "KMUTT", "Master"],
        "website_url": "https://www.cpe.kmutt.ac.th"
    },
    {
        "id": "kmutt_health_ds_bsc",
        "title_th": "หลักสูตรวิทยาศาสตรบัณฑิต สาขาวิชาวิทยาศาสตร์ข้อมูลสุขภาพ",
        "title_en": "Bachelor of Science Program in Health Data Science",
        "degree_level": "ปริญญาตรี",
        "degree_name": "วท.บ. (วิทยาศาสตร์ข้อมูลสุขภาพ)",
        "university": "King Mongkut's University of Technology Thonburi",
        "university_th": "มหาวิทยาลัยเทคโนโลยีพระจอมเกล้าธนบุรี",
        "faculty": "Faculty of Engineering & Faculty of Science",
        "faculty_th": "คณะวิศวกรรมศาสตร์ ร่วมกับ คณะวิทยาศาสตร์",
        "department": "Health Data Science Program",
        "department_th": "โครงการร่วมวิทยาศาสตร์ข้อมูลสุขภาพ",
        "program_type": "ภาคปกติ",
        "duration_years": "4 ปี",
        "total_credits": "130 หน่วยกิต",
        "tuition_per_semester": "35,000 บาท",
        "tuition_total": "280,000 บาท",
        "description": "หลักสูตรพหุวิทยาการที่ผสานวิทยาการข้อมูล (Data Science) วิศวกรรมคอมพิวเตอร์ และวิทยาศาสตร์การแพทย์เข้าด้วยกัน เพื่อผลิตบัณฑิตที่มีความสามารถในการวิเคราะห์ข้อมูลชีวการแพทย์ ข้อมูลสุขภาพขนาดใหญ่ (Big Health Data) และสร้างโมเดล AI ทางการแพทย์",
        "curriculum_highlights": [
            "Biomedical Data Analytics & Informatics",
            "Machine Learning in Healthcare",
            "Medical Imaging & Computer Vision",
            "Health Informatics & Electronic Health Records (EHR)",
            "Genomics & Bioinformatics Data Analysis"
        ],
        "career_paths": [
            "Health Data Scientist",
            "Biomedical AI Developer",
            "Healthcare Informatics Specialist",
            "Clinical Data Analyst",
            "Healthcare Software Engineer"
        ],
        "tags": ["Health Data Science", "Data Science", "AI", "Healthcare", "Bioinformatics", "KMUTT", "Bachelor"],
        "website_url": "https://www.cpe.kmutt.ac.th"
    },
    {
        "id": "kmutt_automation_beng",
        "title_th": "หลักสูตรวิศวกรรมศาสตรบัณฑิต สาขาวิชาวิศวกรรมระบบอัตโนมัติ",
        "title_en": "Bachelor of Engineering Program in Automation Engineering",
        "degree_level": "ปริญญาตรี",
        "degree_name": "วศ.บ. (วิศวกรรมระบบอัตโนมัติ)",
        "university": "King Mongkut's University of Technology Thonburi",
        "university_th": "มหาวิทยาลัยเทคโนโลยีพระจอมเกล้าธนบุรี",
        "faculty": "Faculty of Engineering",
        "faculty_th": "คณะวิศวกรรมศาสตร์",
        "department": "Department of Control System and Instrumentation Engineering",
        "department_th": "ภาควิชาวิศวกรรมระบบควบคุมและเครื่องมือวัด",
        "program_type": "ภาคปกติ",
        "duration_years": "4 ปี",
        "total_credits": "138 หน่วยกิต",
        "tuition_per_semester": "24,000 บาท",
        "tuition_total": "192,000 บาท",
        "description": "เน้นระบบควบคุมอัตโนมัติ ระบบสมองกล เครื่องมือวัดทางอุตสาหกรรม และการผสาน IoT เข้ากับโรงงานอัจฉริยะ (Smart Factory) เพื่อขับเคลื่อนระบบการผลิตตามแนวคิด Industry 4.0",
        "curriculum_highlights": [
            "Feedback Control Systems & Advanced Process Control",
            "PLC, SCADA and Industrial Networking",
            "Industrial Internet of Things (IIoT)",
            "Embedded Automation & Smart Sensors",
            "Smart Factory & Digital Twin Technologies"
        ],
        "career_paths": [
            "Automation Engineer",
            "Control Systems Specialist",
            "Instrumentation Engineer",
            "Smart Factory Integration Engineer",
            "IIoT Solutions Developer"
        ],
        "tags": ["Automation", "Control Systems", "IIoT", "Smart Factory", "Engineering", "KMUTT", "Bachelor"],
        "website_url": "https://inc.kmutt.ac.th"
    },
    {
        "id": "kmutt_sit_cs_bsc",
        "title_th": "หลักสูตรวิทยาศาสตรบัณฑิต สาขาวิชาวิทยาการคอมพิวเตอร์ (หลักสูตรภาษาอังกฤษ)",
        "title_en": "Bachelor of Science Program in Computer Science (English Program)",
        "degree_level": "ปริญญาตรี",
        "degree_name": "วท.บ. (วิทยาการคอมพิวเตอร์)",
        "university": "King Mongkut's University of Technology Thonburi",
        "university_th": "มหาวิทยาลัยเทคโนโลยีพระจอมเกล้าธนบุรี",
        "faculty": "School of Information Technology",
        "faculty_th": "คณะเทคโนโลยีสารสนเทศ",
        "department": "Computer Science",
        "department_th": "สาขาวิชาวิทยาการคอมพิวเตอร์",
        "program_type": "นานาชาติ",
        "duration_years": "4 ปี",
        "total_credits": "130 หน่วยกิต",
        "tuition_per_semester": "45,000 บาท",
        "tuition_total": "360,000 บาท",
        "description": "หลักสูตรวิทยาการคอมพิวเตอร์ภาษาอังกฤษที่เน้นทฤษฎีทางคอมพิวเตอร์เข้มข้น การพัฒนาซอฟต์แวร์มาตรฐานสากล วิทยาการข้อมูล ปัญญาประดิษฐ์ และระบบคลาวด์ เพื่อเตรียมพร้อมบัณฑิตสู่การทำงานในองค์กรเทคโนโลยีชั้นนำทั่วโลก",
        "curriculum_highlights": [
            "Algorithms, Data Structures & Computational Theory",
            "Enterprise Software Engineering & Web Technologies",
            "Machine Learning & Artificial Intelligence",
            "Database Systems & Big Data Processing",
            "Cloud Computing & Distributed Architecture",
            "Mobile Application Development & Security"
        ],
        "career_paths": [
            "Software Engineer",
            "Full-Stack Web Developer",
            "Data Engineer",
            "Machine Learning Developer",
            "Cloud Solutions Developer"
        ],
        "tags": ["Computer Science", "Software Engineering", "AI", "Cloud", "English Program", "KMUTT", "Bachelor"],
        "website_url": "https://www.sit.kmutt.ac.th"
    },
    {
        "id": "kmutt_sit_it_bsc",
        "title_th": "หลักสูตรวิทยาศาสตรบัณฑิต สาขาวิชาเทคโนโลยีสารสนเทศ",
        "title_en": "Bachelor of Science Program in Information Technology",
        "degree_level": "ปริญญาตรี",
        "degree_name": "วท.บ. (เทคโนโลยีสารสนเทศ)",
        "university": "King Mongkut's University of Technology Thonburi",
        "university_th": "มหาวิทยาลัยเทคโนโลยีพระจอมเกล้าธนบุรี",
        "faculty": "School of Information Technology",
        "faculty_th": "คณะเทคโนโลยีสารสนเทศ",
        "department": "Information Technology",
        "department_th": "สาขาวิชาเทคโนโลยีสารสนเทศ",
        "program_type": "ภาคปกติ",
        "duration_years": "4 ปี",
        "total_credits": "128 หน่วยกิต",
        "tuition_per_semester": "38,000 บาท",
        "tuition_total": "304,000 บาท",
        "description": "มุ่งเน้นการประยุกต์ใช้เทคโนโลยีสารสนเทศเพื่อขับเคลื่อนธุรกิจและองค์กร ครอบคลุมการพัฒนาเว็บและโมบายแอพ การบริหารจัดการระบบเครือข่าย คลาวด์คอมพิวติ้ง และระบบความปลอดภัยสารสนเทศ",
        "curriculum_highlights": [
            "Modern Web & Mobile App Development",
            "Network Infrastructure & System Administration",
            "Cloud Computing & Virtualization",
            "Cybersecurity Fundamentals & Defense",
            "Data Analytics & Business Intelligence"
        ],
        "career_paths": [
            "IT Infrastructure Specialist",
            "System Administrator",
            "Frontend / Backend Developer",
            "Network Engineer",
            "IT Support / Business Analyst"
        ],
        "tags": ["Information Technology", "IT Infrastructure", "Cloud", "Cybersecurity", "KMUTT", "Bachelor"],
        "website_url": "https://www.sit.kmutt.ac.th"
    },
    {
        "id": "kmutt_sit_dsi_ba",
        "title_th": "หลักสูตรศิลปศาสตรบัณฑิต สาขาวิชานวัตกรรมบริการดิจิทัล",
        "title_en": "Bachelor of Arts Program in Digital Service Innovation",
        "degree_level": "ปริญญาตรี",
        "degree_name": "ศศ.บ. (นวัตกรรมบริการดิจิทัล)",
        "university": "King Mongkut's University of Technology Thonburi",
        "university_th": "มหาวิทยาลัยเทคโนโลยีพระจอมเกล้าธนบุรี",
        "faculty": "School of Information Technology",
        "faculty_th": "คณะเทคโนโลยีสารสนเทศ",
        "department": "Digital Service Innovation",
        "department_th": "สาขาวิชานวัตกรรมบริการดิจิทัล",
        "program_type": "ภาคปกติ",
        "duration_years": "4 ปี",
        "total_credits": "126 หน่วยกิต",
        "tuition_per_semester": "40,000 บาท",
        "tuition_total": "320,000 บาท",
        "description": "หลักสูตรพันธุ์ใหม่ที่ผสานเทคโนโลยีดิจิทัล การออกแบบบริการ (Service Design) และโมเดลธุรกิจเข้าด้วยกัน เพื่อสร้างนวัตกรและผู้นำการเปลี่ยนแปลงทางดิจิทัล (Digital Transformation) ให้กับองค์กรยุคใหม่",
        "curriculum_highlights": [
            "Service Design Thinking & User Experience (UX)",
            "Digital Transformation & Business Strategy",
            "Low-Code/No-Code Platform & Rapid Prototyping",
            "Digital Marketing & Customer Journey Analytics",
            "Agile Project Management & Scrum"
        ],
        "career_paths": [
            "Digital Transformation Consultant",
            "UX/UI Designer",
            "Product Owner / Product Manager",
            "Digital Business Analyst",
            "Technology Startup Founder"
        ],
        "tags": ["Digital Service", "Service Design", "UX/UI", "Product Management", "Digital Transformation", "KMUTT", "Bachelor"],
        "website_url": "https://www.sit.kmutt.ac.th"
    },
    {
        "id": "kmutt_sit_cs_msc",
        "title_th": "หลักสูตรวิทยาศาสตรมหาบัณฑิต สาขาวิชาวิทยาการคอมพิวเตอร์",
        "title_en": "Master of Science Program in Computer Science",
        "degree_level": "ปริญญาโท",
        "degree_name": "วท.ม. (วิทยาการคอมพิวเตอร์)",
        "university": "King Mongkut's University of Technology Thonburi",
        "university_th": "มหาวิทยาลัยเทคโนโลยีพระจอมเกล้าธนบุรี",
        "faculty": "School of Information Technology",
        "faculty_th": "คณะเทคโนโลยีสารสนเทศ",
        "department": "Computer Science",
        "department_th": "สาขาวิชาวิทยาการคอมพิวเตอร์",
        "program_type": "ภาคปกติ",
        "duration_years": "2 ปี",
        "total_credits": "36 หน่วยกิต",
        "tuition_per_semester": "42,000 บาท",
        "tuition_total": "168,000 บาท",
        "description": "หลักสูตรระดับบัณฑิตศึกษาที่เน้นการวิจัยเชิงลึกด้าน Machine Learning, Computer Vision, Big Data Architecture, และระบบความปลอดภัยขั้นสูง เพื่อเตรียมบุคลากรสู่ตำแหน่งผู้เชี่ยวชาญด้านวิทยาการคอมพิวเตอร์",
        "curriculum_highlights": [
            "Advanced Machine Learning & Deep Neural Networks",
            "Big Data Analytics & Data Engineering",
            "Advanced Computer Systems & Cloud Computing",
            "Cryptography & Information Security",
            "Thesis / Independent Study in CS"
        ],
        "career_paths": [
            "Senior Data Scientist",
            "Machine Learning Engineer",
            "CS Researcher",
            "Lead Software Architect",
            "Academic Lecturer"
        ],
        "tags": ["Computer Science", "Machine Learning", "Big Data", "AI", "KMUTT", "Master"],
        "website_url": "https://www.sit.kmutt.ac.th"
    },
    {
        "id": "kmutt_sit_it_msc",
        "title_th": "หลักสูตรวิทยาศาสตรมหาบัณฑิต สาขาวิชาเทคโนโลยีสารสนเทศ",
        "title_en": "Master of Science Program in Information Technology",
        "degree_level": "ปริญญาโท",
        "degree_name": "วท.ม. (เทคโนโลยีสารสนเทศ)",
        "university": "King Mongkut's University of Technology Thonburi",
        "university_th": "มหาวิทยาลัยเทคโนโลยีพระจอมเกล้าธนบุรี",
        "faculty": "School of Information Technology",
        "faculty_th": "คณะเทคโนโลยีสารสนเทศ",
        "department": "Information Technology",
        "department_th": "สาขาวิชาเทคโนโลยีสารสนเทศ",
        "program_type": "ภาคพิเศษ / ภาคค่ำ-วันหยุด",
        "duration_years": "2 ปี",
        "total_credits": "36 หน่วยกิต",
        "tuition_per_semester": "48,000 บาท",
        "tuition_total": "192,000 บาท",
        "description": "หลักสูตรปริญญาโทสำหรับคนทำงาน เน้นความเชี่ยวชาญด้าน Data Science, Business Analytics, Cyber Defense และการบริหารจัดการเทคโนโลยีสารสนเทศระดับองค์กร สามารถเรียนควบคู่กับการทำงานได้",
        "curriculum_highlights": [
            "Data Science for Business Decision Making",
            "Enterprise Architecture & IT Governance",
            "Cyber Threat Intelligence & Compliance",
            "Cloud Strategy & Migration",
            "Applied Business Intelligence"
        ],
        "career_paths": [
            "IT Project Manager",
            "Enterprise Architect",
            "Business Intelligence Manager",
            "Chief Information Security Officer (CISO)",
            "IT Strategy Consultant"
        ],
        "tags": ["Information Technology", "Business Analytics", "IT Management", "Cybersecurity", "KMUTT", "Master"],
        "website_url": "https://www.sit.kmutt.ac.th"
    },
    {
        "id": "kmutt_sit_se_ai_msc",
        "title_th": "หลักสูตรวิทยาศาสตรมหาบัณฑิต สาขาวิศวกรรมซอฟต์แวร์เพื่อปัญญาประดิษฐ์",
        "title_en": "Master of Science Program in Software Engineering for Artificial Intelligence",
        "degree_level": "ปริญญาโท",
        "degree_name": "วท.ม. (วิศวกรรมซอฟต์แวร์เพื่อปัญญาประดิษฐ์)",
        "university": "King Mongkut's University of Technology Thonburi",
        "university_th": "มหาวิทยาลัยเทคโนโลยีพระจอมเกล้าธนบุรี",
        "faculty": "School of Information Technology",
        "faculty_th": "คณะเทคโนโลยีสารสนเทศ",
        "department": "Software Engineering and AI",
        "department_th": "สาขาวิชาวิศวกรรมซอฟต์แวร์และปัญญาประดิษฐ์",
        "program_type": "ภาคปกติ / ภาคพิเศษ",
        "duration_years": "2 ปี",
        "total_credits": "36 หน่วยกิต",
        "tuition_per_semester": "50,000 บาท",
        "tuition_total": "200,000 บาท",
        "description": "หลักสูตรเฉพาะทางที่เน้นการสร้างซอฟต์แวร์เกรดโปรดักชันที่ขับเคลื่อนด้วย AI (AI-driven Software Engineering), MLOps, LLMOps, และการบริหารจัดการวงจรชีวิตของระบบปัญญาประดิษฐ์ขนาดใหญ่",
        "curriculum_highlights": [
            "MLOps & LLMOps Pipeline Engineering",
            "Software Architecture for AI Systems",
            "Large Language Model Integration & Fine-Tuning",
            "Automated Testing & Quality Assurance for AI",
            "Responsible & Ethical AI Engineering"
        ],
        "career_paths": [
            "MLOps Engineer",
            "AI Software Architect",
            "Lead AI Engineer",
            "Production Machine Learning Specialist",
            "AI Solutions Consultant"
        ],
        "tags": ["Software Engineering", "AI", "MLOps", "LLMOps", "Cloud", "KMUTT", "Master"],
        "website_url": "https://www.sit.kmutt.ac.th"
    },
    {
        "id": "kmutt_media_arts_bfa",
        "title_th": "หลักสูตรศิลปกรรมศาสตรบัณฑิต สาขาวิชามีเดียอาตส์",
        "title_en": "Bachelor of Fine Arts Program in Media Arts",
        "degree_level": "ปริญญาตรี",
        "degree_name": "ศล.บ. (มีเดียอาตส์)",
        "university": "King Mongkut's University of Technology Thonburi",
        "university_th": "มหาวิทยาลัยเทคโนโลยีพระจอมเกล้าธนบุรี",
        "faculty": "School of Architecture and Design (SoA+D)",
        "faculty_th": "คณะสถาปัตยกรรมศาสตร์และการออกแบบ",
        "department": "Media Arts and Technology Program",
        "department_th": "โครงการร่วมบริหารหลักสูตรฯ (มีเดีย) วิทยาเขตบางขุนเทียน",
        "program_type": "ภาคปกติ",
        "duration_years": "4 ปี",
        "total_credits": "132 หน่วยกิต",
        "tuition_per_semester": "36,000 บาท",
        "tuition_total": "288,000 บาท",
        "description": "มุ่งเน้นการสร้างสรรค์ศิลปะดิจิทัล แอนิเมชัน 2D/3D โมชันกราฟิก การผลิตภาพยนตร์ และวิชวลเอฟเฟกต์ (VFX) โดยผสานเทคโนโลยี Generative AI เข้ากับการเล่าเรื่องและการออกแบบเชิงศิลปะ",
        "curriculum_highlights": [
            "3D Animation & Character Modeling",
            "Visual Effects (VFX) & Compositing",
            "Concept Art & Digital Illustration",
            "Motion Graphics & Creative Direction",
            "Generative AI for Digital Art & Media Production"
        ],
        "career_paths": [
            "3D Animator / Modeler",
            "VFX Artist",
            "Concept Artist / Illustrator",
            "Motion Graphic Designer",
            "Creative Director in Digital Media"
        ],
        "tags": ["Media Arts", "Animation", "VFX", "Digital Art", "Creative Design", "KMUTT", "Bachelor"],
        "website_url": "https://mediaarts.kmutt.ac.th"
    },
    {
        "id": "kmutt_media_tech_bsc",
        "title_th": "หลักสูตรวิทยาศาสตรบัณฑิต สาขาวิชาเทคโนโลยีมีเดีย",
        "title_en": "Bachelor of Science Program in Media Technology",
        "degree_level": "ปริญญาตรี",
        "degree_name": "วท.บ. (เทคโนโลยีมีเดีย)",
        "university": "King Mongkut's University of Technology Thonburi",
        "university_th": "มหาวิทยาลัยเทคโนโลยีพระจอมเกล้าธนบุรี",
        "faculty": "School of Architecture and Design (SoA+D)",
        "faculty_th": "คณะสถาปัตยกรรมศาสตร์และการออกแบบ",
        "department": "Media Technology Program",
        "department_th": "โครงการร่วมบริหารหลักสูตรฯ (มีเดีย) วิทยาเขตบางขุนเทียน",
        "program_type": "ภาคปกติ",
        "duration_years": "4 ปี",
        "total_credits": "130 หน่วยกิต",
        "tuition_per_semester": "36,000 บาท",
        "tuition_total": "288,000 บาท",
        "description": "เน้นการพัฒนาเทคโนโลยีดิจิทัลเชิงปฏิสัมพันธ์ การพัฒนาเกมด้วย Unity และ Unreal Engine เทคโนโลยีความจริงเสมือน (VR/AR/XR) และเทคโนโลยีดิจิทัลทวิน (Digital Twin) เพื่ออุตสาหกรรมบันเทิงและองค์กรดิจิทัล",
        "curriculum_highlights": [
            "Game Programming & Engine Architecture (Unreal/Unity)",
            "Virtual Reality & Augmented Reality (VR/AR/XR)",
            "Interactive Media Systems & Physical Computing",
            "3D Simulation & Digital Twin Technologies",
            "UX/UI for Immersive Experiences"
        ],
        "career_paths": [
            "Game Developer / Game Programmer",
            "VR/AR/XR Developer",
            "Interactive Media Developer",
            "Technical Artist",
            "Digital Twin Specialist"
        ],
        "tags": ["Media Technology", "Game Development", "VR/AR", "XR", "Interactive Design", "KMUTT", "Bachelor"],
        "website_url": "https://mediaarts.kmutt.ac.th"
    },
    {
        "id": "kmutt_med_sci_media_bsc",
        "title_th": "หลักสูตรวิทยาศาสตรบัณฑิต สาขาวิชามีเดียทางการแพทย์และวิทยาศาสตร์",
        "title_en": "Bachelor of Science Program in Medical and Science Media",
        "degree_level": "ปริญญาตรี",
        "degree_name": "วท.บ. (มีเดียทางการแพทย์และวิทยาศาสตร์)",
        "university": "King Mongkut's University of Technology Thonburi",
        "university_th": "มหาวิทยาลัยเทคโนโลยีพระจอมเกล้าธนบุรี",
        "faculty": "School of Architecture and Design (SoA+D)",
        "faculty_th": "คณะสถาปัตยกรรมศาสตร์และการออกแบบ",
        "department": "Medical and Science Media Program",
        "department_th": "โครงการร่วมบริหารหลักสูตรฯ (มีเดีย) วิทยาเขตบางขุนเทียน",
        "program_type": "ภาคปกติ",
        "duration_years": "4 ปี",
        "total_credits": "130 หน่วยกิต",
        "tuition_per_semester": "36,000 บาท",
        "tuition_total": "288,000 บาท",
        "description": "หลักสูตรแรกและแห่งเดียวในไทยที่ผสานความรู้ด้านการแพทย์ กายวิภาคศาสตร์ วิทยาศาสตร์สุขภาพ เข้ากับการออกแบบสื่อดิจิทัล โมเดล 3 มิติทางการแพทย์ และสื่อภาพเสมือนจริงเพื่อการศึกษาและวิจัยทางการแพทย์",
        "curriculum_highlights": [
            "Medical & Scientific Visualization",
            "3D Medical Anatomy Modeling & Simulation",
            "Surgical Simulation Media & Virtual Anatomy",
            "Health Communication & Instructional Media",
            "Interactive Medical Training Applications"
        ],
        "career_paths": [
            "Medical Illustrator / Animator",
            "Healthcare Media Developer",
            "Surgical Simulator Content Creator",
            "Scientific Communication Specialist",
            "Educational Health Media Producer"
        ],
        "tags": ["Medical Media", "Science Media", "3D Modeling", "Health Tech", "Visualization", "KMUTT", "Bachelor"],
        "website_url": "https://mediaarts.kmutt.ac.th"
    },
    {
        "id": "kmutt_sci_applied_cs_bsc",
        "title_th": "หลักสูตรวิทยาศาสตรบัณฑิต สาขาวิชาวิทยาการคอมพิวเตอร์ประยุกต์",
        "title_en": "Bachelor of Science Program in Applied Computer Science",
        "degree_level": "ปริญญาตรี",
        "degree_name": "วท.บ. (วิทยาการคอมพิวเตอร์ประยุกต์)",
        "university": "King Mongkut's University of Technology Thonburi",
        "university_th": "มหาวิทยาลัยเทคโนโลยีพระจอมเกล้าธนบุรี",
        "faculty": "Faculty of Science",
        "faculty_th": "คณะวิทยาศาสตร์",
        "department": "Department of Mathematics",
        "department_th": "ภาควิชาคณิตศาสตร์",
        "program_type": "ภาคปกติ",
        "duration_years": "4 ปี",
        "total_credits": "132 หน่วยกิต",
        "tuition_per_semester": "22,000 บาท",
        "tuition_total": "176,000 บาท",
        "description": "ผสานคณิตศาสตร์ประยุกต์ วิทยาการคอมพิวเตอร์ และการวิเคราะห์ข้อมูลเชิงตัวเลข เพื่อสร้างอัลกอริทึมขั้นสูงสำหรับการประมวลผลข้อมูลขนาดใหญ่ การเงินเชิงปริมาณ และการจำลองระบบซับซ้อน",
        "curriculum_highlights": [
            "Applied Mathematics & Numerical Methods",
            "Algorithm Design & Complexity Analysis",
            "Data Science & Statistical Modeling",
            "Computational Finance & Risk Analytics",
            "Scientific Programming (Python/C++/R)"
        ],
        "career_paths": [
            "Quantitative Analyst (Quant)",
            "Applied Computer Scientist",
            "Data Scientist / Algorithm Developer",
            "Financial Systems Engineer",
            "Software Developer"
        ],
        "tags": ["Applied Computer Science", "Applied Mathematics", "Quant", "Data Science", "KMUTT", "Bachelor"],
        "website_url": "https://math.kmutt.ac.th"
    },

    # =========================================================================
    # KMITL (สถาบันเทคโนโลยีพระจอมเกล้าเจ้าคุณทหารลาดกระบัง)
    # =========================================================================
    {
        "id": "kmitl_eng_ce_beng",
        "title_th": "หลักสูตรวิศวกรรมศาสตรบัณฑิต สาขาวิชาวิศวกรรมคอมพิวเตอร์",
        "title_en": "Bachelor of Engineering Program in Computer Engineering",
        "degree_level": "ปริญญาตรี",
        "degree_name": "วศ.บ. (วิศวกรรมคอมพิวเตอร์)",
        "university": "King Mongkut's Institute of Technology Ladkrabang",
        "university_th": "สถาบันเทคโนโลยีพระจอมเกล้าเจ้าคุณทหารลาดกระบัง",
        "faculty": "School of Engineering",
        "faculty_th": "คณะวิศวกรรมศาสตร์",
        "department": "Department of Computer Engineering",
        "department_th": "ภาควิชาวิศวกรรมคอมพิวเตอร์",
        "program_type": "ภาคปกติ",
        "duration_years": "4 ปี",
        "total_credits": "142 หน่วยกิต",
        "tuition_per_semester": "25,000 บาท",
        "tuition_total": "200,000 บาท",
        "description": "หนึ่งในหลักสูตรวิศวกรรมคอมพิวเตอร์ที่มีชื่อเสียงที่สุดในประเทศไทย มุ่งเน้นการบูรณาการด้านระบบฮาร์ดแวร์ สถาปัตยกรรมคอมพิวเตอร์ ซอฟต์แวร์เชิงลึก ระบบสมองกลฝังตัว ปัญญาประดิษฐ์ และระบบเครือข่ายความเร็วสูง",
        "curriculum_highlights": [
            "Computer Architecture & Microprocessor Interfacing",
            "Operating Systems & Distributed Architecture",
            "Advanced Data Structures & High-Performance Computing",
            "Embedded Systems Design & FPGA",
            "AI, Deep Learning & Computer Vision",
            "Network Engineering & Cloud Infrastructure"
        ],
        "career_paths": [
            "Computer Hardware/Firmware Engineer",
            "Software Engineer / Backend Developer",
            "Embedded Systems Engineer",
            "AI/ML Systems Engineer",
            "Network & Cloud Infrastructure Engineer"
        ],
        "tags": ["Computer Engineering", "Hardware", "Embedded Systems", "AI", "Cloud", "KMITL", "Bachelor"],
        "website_url": "https://www.ce.kmitl.ac.th"
    },
    {
        "id": "kmitl_eng_cybersecurity_beng",
        "title_th": "หลักสูตรวิศวกรรมศาสตรบัณฑิต สาขาวิชาวิศวกรรมคอมพิวเตอร์และความปลอดภัยไซเบอร์",
        "title_en": "Bachelor of Engineering Program in Computer Engineering and Cybersecurity",
        "degree_level": "ปริญญาตรี",
        "degree_name": "วศ.บ. (วิศวกรรมคอมพิวเตอร์และความปลอดภัยไซเบอร์)",
        "university": "King Mongkut's Institute of Technology Ladkrabang",
        "university_th": "สถาบันเทคโนโลยีพระจอมเกล้าเจ้าคุณทหารลาดกระบัง",
        "faculty": "School of Engineering",
        "faculty_th": "คณะวิศวกรรมศาสตร์",
        "department": "Department of Computer Engineering",
        "department_th": "ภาควิชาวิศวกรรมคอมพิวเตอร์",
        "program_type": "ภาคปกติ / โครงการพิเศษ",
        "duration_years": "4 ปี",
        "total_credits": "138 หน่วยกิต",
        "tuition_per_semester": "45,000 บาท",
        "tuition_total": "360,000 บาท",
        "description": "เน้นทักษะความเชี่ยวชาญด้านความมั่นคงปลอดภัยสารสนเทศ การป้องกันการโจมตีทางไซเบอร์ การตรวจพิสูจน์พยานหลักฐานดิจิทัล (Digital Forensics) การทดสอบเจาะระบบ (Penetration Testing) และการรักษาความปลอดภัยของระบบคลาวด์และโครงสร้างพื้นฐานสำคัญ",
        "curriculum_highlights": [
            "Ethical Hacking & Penetration Testing",
            "Digital Forensics & Incident Response (DFIR)",
            "Network Security & Firewall Architecture",
            "Secure Coding & Software Vulnerability Assessment",
            "Cloud Security & DevSecOps Practices",
            "Cyber Threat Intelligence & SOC Operations"
        ],
        "career_paths": [
            "Cybersecurity Engineer",
            "Penetration Tester / Ethical Hacker",
            "Security Operations Center (SOC) Analyst",
            "Digital Forensic Investigator",
            "DevSecOps Engineer"
        ],
        "tags": ["Cybersecurity", "Ethical Hacking", "Digital Forensics", "Computer Engineering", "KMITL", "Bachelor"],
        "website_url": "https://www.ce.kmitl.ac.th"
    },
    {
        "id": "kmitl_eng_se_inter_beng",
        "title_th": "หลักสูตรวิศวกรรมศาสตรบัณฑิต สาขาวิชาวิศวกรรมซอฟต์แวร์ (หลักสูตรนานาชาติ)",
        "title_en": "Bachelor of Engineering Program in Software Engineering (International Program)",
        "degree_level": "ปริญญาตรี",
        "degree_name": "วศ.บ. (วิศวกรรมซอฟต์แวร์)",
        "university": "King Mongkut's Institute of Technology Ladkrabang",
        "university_th": "สถาบันเทคโนโลยีพระจอมเกล้าเจ้าคุณทหารลาดกระบัง",
        "faculty": "School of Engineering",
        "faculty_th": "คณะวิศวกรรมศาสตร์ (SIIE)",
        "department": "Software Engineering Program",
        "department_th": "หลักสูตรวิศวกรรมซอฟต์แวร์นานาชาติ",
        "program_type": "นานาชาติ",
        "duration_years": "4 ปี",
        "total_credits": "136 หน่วยกิต",
        "tuition_per_semester": "90,000 บาท",
        "tuition_total": "720,000 บาท",
        "description": "หลักสูตรนานาชาติระดับพรีเมียมที่เน้นการสร้างสถาปัตยกรรมซอฟต์แวร์ขนาดใหญ่ การพัฒนาแบบ Agile/Scrum การออกแบบคลาวด์เนทีฟ (Cloud-Native) การผสานเทคโนโลยี AI และ Microservices สู่มาตรฐานซอฟต์แวร์ระดับโลก",
        "curriculum_highlights": [
            "Software Architecture & Design Patterns",
            "Cloud-Native Application Development & Kubernetes",
            "DevOps, Continuous Integration & Deployment (CI/CD)",
            "Scalable Distributed Database Systems",
            "AI-Powered Software Development & MLOps",
            "International Industry Capstone Project"
        ],
        "career_paths": [
            "Senior Software Engineer",
            "Software Architect",
            "Full Stack Cloud Developer",
            "DevOps Engineer",
            "Tech Lead / Engineering Manager"
        ],
        "tags": ["Software Engineering", "Cloud Native", "DevOps", "International", "AI", "KMITL", "Bachelor"],
        "website_url": "https://se.kmitl.ac.th"
    },
    {
        "id": "kmitl_eng_robotics_ai_beng",
        "title_th": "หลักสูตรวิศวกรรมศาสตรบัณฑิต สาขาวิชาวิศวกรรมหุ่นยนต์และปัญญาประดิษฐ์ (หลักสูตรนานาชาติ)",
        "title_en": "Bachelor of Engineering Program in Robotics and AI Engineering (International Program)",
        "degree_level": "ปริญญาตรี",
        "degree_name": "วศ.บ. (วิศวกรรมหุ่นยนต์และปัญญาประดิษฐ์)",
        "university": "King Mongkut's Institute of Technology Ladkrabang",
        "university_th": "สถาบันเทคโนโลยีพระจอมเกล้าเจ้าคุณทหารลาดกระบัง",
        "faculty": "School of Engineering",
        "faculty_th": "คณะวิศวกรรมศาสตร์ (RAI KMITL)",
        "department": "Robotics and AI Engineering Program",
        "department_th": "หลักสูตรวิศวกรรมหุ่นยนต์และปัญญาประดิษฐ์นานาชาติ",
        "program_type": "นานาชาติ",
        "duration_years": "4 ปี",
        "total_credits": "138 หน่วยกิต",
        "tuition_per_semester": "90,000 บาท",
        "tuition_total": "720,000 บาท",
        "description": "หลักสูตรนานาชาติเรือธงที่ผสมผสานวิทยาการหุ่นยนต์ (Robotics), ระบบอัตโนมัติ และปัญญาประดิษฐ์ (AI) เข้าด้วยกันอย่างสมบูรณ์แบบ ได้รับการยอมรับในระดับนานาชาติ เน้นสร้างระบบขับเคลื่อนอัตโนมัติ หุ่นยนต์บริการ และ AI ขั้นสูง",
        "curriculum_highlights": [
            "Autonomous Mobile Robots & SLAM Navigation",
            "Deep Reinforcement Learning for Robotics",
            "Computer Vision & 3D Sensor Processing",
            "Robot Control Systems & Embedded AI Chips",
            "Industrial Robot Arm Kinematics & Manipulation",
            "Drone & Autonomous Vehicle Technology"
        ],
        "career_paths": [
            "Robotics & AI Engineer",
            "Autonomous Vehicle Algorithm Engineer",
            "Computer Vision Specialist",
            "Smart Automation Architect",
            "Robotics Software Developer"
        ],
        "tags": ["Robotics", "AI", "Autonomous Systems", "International", "Engineering", "KMITL", "Bachelor"],
        "website_url": "https://rai.kmitl.ac.th"
    },
    {
        "id": "kmitl_eng_iot_beng",
        "title_th": "หลักสูตรวิศวกรรมศาสตรบัณฑิต สาขาวิชาวิศวกรรมระบบไอโอทีและสารสนเทศ",
        "title_en": "Bachelor of Engineering Program in IoT Systems and Information Engineering",
        "degree_level": "ปริญญาตรี",
        "degree_name": "วศ.บ. (วิศวกรรมระบบไอโอทีและสารสนเทศ)",
        "university": "King Mongkut's Institute of Technology Ladkrabang",
        "university_th": "สถาบันเทคโนโลยีพระจอมเกล้าเจ้าคุณทหารลาดกระบัง",
        "faculty": "School of Engineering",
        "faculty_th": "คณะวิศวกรรมศาสตร์",
        "department": "Department of IoT Systems and Information Engineering",
        "department_th": "ภาควิชาวิศวกรรมระบบไอโอทีและสารสนเทศ",
        "program_type": "ภาคปกติ",
        "duration_years": "4 ปี",
        "total_credits": "136 หน่วยกิต",
        "tuition_per_semester": "25,000 บาท",
        "tuition_total": "200,000 บาท",
        "description": "บูรณาการเทคโนโลยี Internet of Things (IoT), ระบบเครือข่าย 5G/6G, เซ็นเซอร์อัจฉริยะ, และการประมวลผลข้อมูล AI บน Edge Device เพื่อรองรับเมืองอัจฉริยะ (Smart City) และเกษตรแม่นยำสูง",
        "curriculum_highlights": [
            "IoT Architecture & Wireless Sensor Networks",
            "Edge AI & TinyML Implementation",
            "Cloud Platforms for Massive IoT (AWS/Azure/GCP)",
            "Smart City & Smart Agriculture Solutions",
            "IoT Cyber-Physical System Security"
        ],
        "career_paths": [
            "IoT Solutions Architect",
            "Edge AI Developer",
            "Smart Systems Engineer",
            "Network & IoT Infrastructure Specialist",
            "Embedded IoT Developer"
        ],
        "tags": ["IoT", "Edge AI", "Smart City", "Embedded Systems", "Information Engineering", "KMITL", "Bachelor"],
        "website_url": "https://iot.kmitl.ac.th"
    },
    {
        "id": "kmitl_eng_bme_beng",
        "title_th": "หลักสูตรวิศวกรรมศาสตรบัณฑิต สาขาวิชาวิศวกรรมชีวการแพทย์",
        "title_en": "Bachelor of Engineering Program in Biomedical Engineering",
        "degree_level": "ปริญญาตรี",
        "degree_name": "วศ.บ. (วิศวกรรมชีวการแพทย์)",
        "university": "King Mongkut's Institute of Technology Ladkrabang",
        "university_th": "สถาบันเทคโนโลยีพระจอมเกล้าเจ้าคุณทหารลาดกระบัง",
        "faculty": "School of Engineering",
        "faculty_th": "คณะวิศวกรรมศาสตร์",
        "department": "Department of Biomedical Engineering",
        "department_th": "ภาควิชาวิศวกรรมชีวการแพทย์",
        "program_type": "ภาคปกติและนานาชาติ",
        "duration_years": "4 ปี",
        "total_credits": "138 หน่วยกิต",
        "tuition_per_semester": "30,000 บาท",
        "tuition_total": "240,000 บาท",
        "description": "ผสานวิศวกรรมศาสตร์ การแพทย์ และเทคโนโลยีสารสนเทศเพื่อคิดค้นเครื่องมือแพทย์ ระบบอวัยวะเทียม เซ็นเซอร์ติดตามสุขภาพทางไกล และโมเดล AI สำหรับวิเคราะห์โรคและภาพถ่ายทางการแพทย์",
        "curriculum_highlights": [
            "Biomedical Instrumentation & Medical Sensors",
            "Medical Image Processing & AI Diagnosis",
            "Biomechanics & Rehabilitation Robotics",
            "Biosignal Processing (ECG/EEG/EMG)",
            "Medical Device Standards & Regulatory Affairs"
        ],
        "career_paths": [
            "Biomedical Engineer",
            "Medical Equipment Specialist",
            "Clinical AI Developer",
            "Medical Device R&D Engineer",
            "Healthcare Technology Consultant"
        ],
        "tags": ["Biomedical Engineering", "Medical AI", "Health Tech", "Instrumentation", "KMITL", "Bachelor"],
        "website_url": "https://bme.kmitl.ac.th"
    },
    {
        "id": "kmitl_eng_financial_eng_beng",
        "title_th": "หลักสูตรวิศวกรรมศาสตรบัณฑิต สาขาวิชาวิศวกรรมการเงิน",
        "title_en": "Bachelor of Engineering Program in Financial Engineering",
        "degree_level": "ปริญญาตรี",
        "degree_name": "วศ.บ. (วิศวกรรมการเงิน)",
        "university": "King Mongkut's Institute of Technology Ladkrabang",
        "university_th": "สถาบันเทคโนโลยีพระจอมเกล้าเจ้าคุณทหารลาดกระบัง",
        "faculty": "School of Engineering & KMITL Business School",
        "faculty_th": "คณะวิศวกรรมศาสตร์ ร่วมกับ คณะบริหารธุรกิจ",
        "department": "Financial Engineering Program",
        "department_th": "หลักสูตรวิศวกรรมการเงิน",
        "program_type": "ภาคปกติ (Dual Degree)",
        "duration_years": "4 ปี",
        "total_credits": "144 หน่วยกิต",
        "tuition_per_semester": "60,000 บาท",
        "tuition_total": "480,000 บาท",
        "description": "หลักสูตรข้ามศาสตร์ชั้นนำที่ผสานคณิตศาสตร์การเงิน วิศวกรรมคอมพิวเตอร์ และเศรษฐศาสตร์การเงิน เพื่อสร้างผู้เชี่ยวชาญด้านการคำนวณราคาตราสารอนุพันธ์ การเทรดด้วยอัลกอริทึม (Algo-trading) และการบริหารความเสี่ยงเชิงปริมาณ",
        "curriculum_highlights": [
            "Financial Mathematics & Stochastic Calculus",
            "Quantitative Trading & Algorithmic Trading Systems",
            "Financial Risk Management & Portfolio Optimization",
            "Machine Learning for Financial Markets",
            "FinTech, Blockchain & Smart Contracts"
        ],
        "career_paths": [
            "Quantitative Analyst (Quant)",
            "Algorithmic Trader",
            "Financial Risk Analyst",
            "FinTech Software Developer",
            "Portfolio Manager"
        ],
        "tags": ["Financial Engineering", "FinTech", "Quant", "Trading", "AI", "KMITL", "Bachelor"],
        "website_url": "https://fe.kmitl.ac.th"
    },
    {
        "id": "kmitl_eng_ece_meng",
        "title_th": "หลักสูตรวิศวกรรมศาสตรมหาบัณฑิต สาขาวิชาวิศวกรรมไฟฟ้าและคอมพิวเตอร์",
        "title_en": "Master of Engineering Program in Electrical and Computer Engineering",
        "degree_level": "ปริญญาโท",
        "degree_name": "วศ.ม. (วิศวกรรมไฟฟ้าและคอมพิวเตอร์)",
        "university": "King Mongkut's Institute of Technology Ladkrabang",
        "university_th": "สถาบันเทคโนโลยีพระจอมเกล้าเจ้าคุณทหารลาดกระบัง",
        "faculty": "School of Engineering",
        "faculty_th": "คณะวิศวกรรมศาสตร์",
        "department": "Department of Computer Engineering",
        "department_th": "ภาควิชาวิศวกรรมคอมพิวเตอร์",
        "program_type": "ภาคปกติและภาคพิเศษ",
        "duration_years": "2 ปี",
        "total_credits": "36 หน่วยกิต",
        "tuition_per_semester": "35,000 บาท",
        "tuition_total": "140,000 บาท",
        "description": "เน้นงานวิจัยและการประยุกต์ใช้งานวิศวกรรมไฟฟ้าและคอมพิวเตอร์ขั้นสูง เช่น ระบบปัญญาประดิษฐ์อัจฉริยะ ระบบการประมวลผลสัญญาณและภาพ สถาปัตยกรรมไมโครอิเล็กทรอนิกส์ และโครงข่ายการสื่อสารยุคใหม่",
        "curriculum_highlights": [
            "Advanced Computer Systems and Architectures",
            "Machine Learning and Deep Neural Networks",
            "Advanced Digital Signal and Image Processing",
            "Distributed Cyber-Physical Systems",
            "Master Thesis Research"
        ],
        "career_paths": [
            "Principal Computer Engineer",
            "AI/ML Research Scientist",
            "Embedded Systems Architect",
            "Advanced Hardware Design Engineer",
            "University Lecturer"
        ],
        "tags": ["Electrical and Computer Engineering", "AI", "Hardware", "Research", "KMITL", "Master"],
        "website_url": "https://www.ce.kmitl.ac.th"
    },
    {
        "id": "kmitl_eng_robotics_ai_meng",
        "title_th": "หลักสูตรวิศวกรรมศาสตรมหาบัณฑิต สาขาวิชาวิศวกรรมหุ่นยนต์และปัญญาประดิษฐ์",
        "title_en": "Master of Engineering Program in Robotics and Artificial Intelligence",
        "degree_level": "ปริญญาโท",
        "degree_name": "วศ.ม. (วิศวกรรมหุ่นยนต์และปัญญาประดิษฐ์)",
        "university": "King Mongkut's Institute of Technology Ladkrabang",
        "university_th": "สถาบันเทคโนโลยีพระจอมเกล้าเจ้าคุณทหารลาดกระบัง",
        "faculty": "School of Engineering",
        "faculty_th": "คณะวิศวกรรมศาสตร์",
        "department": "Robotics and AI Graduate Program",
        "department_th": "หลักสูตรบัณฑิตศึกษาวิศวกรรมหุ่นยนต์และปัญญาประดิษฐ์",
        "program_type": "นานาชาติ",
        "duration_years": "2 ปี",
        "total_credits": "36 หน่วยกิต",
        "tuition_per_semester": "60,000 บาท",
        "tuition_total": "240,000 บาท",
        "description": "หลักสูตรปริญญาโทระดับนานาชาติ มุ่งเน้นการวิจัยเชิงลึกในระบบหุ่นยนต์อัตโนมัติขั้นสูง หุ่นยนต์ทางการแพทย์ ปัญญาประดิษฐ์เชิงกำเนิด และการควบคุมอัตโนมัติระดับอุตสาหกรรม",
        "curriculum_highlights": [
            "Advanced Autonomous Navigation and Localization",
            "Deep Reinforcement Learning & Neural Control",
            "Medical & Surgical Robotics",
            "Multi-Agent Robotic Systems",
            "Master Thesis in Robotics and AI"
        ],
        "career_paths": [
            "Lead Robotics Researcher",
            "AI Systems Architect",
            "Robotics Startup Founder / CTO",
            "Senior Automation Consultant",
            "Faculty Member"
        ],
        "tags": ["Robotics", "AI", "Deep Learning", "International", "KMITL", "Master"],
        "website_url": "https://rai.kmitl.ac.th"
    },
    {
        "id": "kmitl_eng_aiot_meng",
        "title_th": "หลักสูตรวิศวกรรมศาสตรมหาบัณฑิต สาขาวิชาเอไอโอทีและสารสนเทศ",
        "title_en": "Master of Engineering Program in AIoT and Information Engineering",
        "degree_level": "ปริญญาโท",
        "degree_name": "วศ.ม. (เอไอโอทีและสารสนเทศ)",
        "university": "King Mongkut's Institute of Technology Ladkrabang",
        "university_th": "สถาบันเทคโนโลยีพระจอมเกล้าเจ้าคุณทหารลาดกระบัง",
        "faculty": "School of Engineering",
        "faculty_th": "คณะวิศวกรรมศาสตร์",
        "department": "Department of IoT Systems and Information Engineering",
        "department_th": "ภาควิชาวิศวกรรมระบบไอโอทีและสารสนเทศ",
        "program_type": "ภาคปกติและภาคพิเศษ",
        "duration_years": "2 ปี",
        "total_credits": "36 หน่วยกิต",
        "tuition_per_semester": "38,000 บาท",
        "tuition_total": "152,000 บาท",
        "description": "เน้นการพัฒนาเทคโนโลยี AIoT (Artificial Intelligence of Things) การวิเคราะห์ข้อมูลขนาดใหญ่จากอุปกรณ์ IoT เครือข่ายไร้สาย 5G/6G และการออกแบบระบบคลาวด์และเอดจ์ขั้นสูง",
        "curriculum_highlights": [
            "AIoT System Architecture & Edge Computing",
            "Advanced 5G/6G Wireless Communication",
            "Big Data Analytics from IoT Streams",
            "Cyber-Physical Security in AIoT",
            "Master Thesis in AIoT Applications"
        ],
        "career_paths": [
            "AIoT Solutions Architect",
            "Principal IoT Engineer",
            "Smart Infrastructure Consultant",
            "AIoT Researcher",
            "Lecturer"
        ],
        "tags": ["AIoT", "IoT", "5G", "Edge Computing", "AI", "KMITL", "Master"],
        "website_url": "https://iot.kmitl.ac.th"
    },
    {
        "id": "kmitl_it_bsc",
        "title_th": "หลักสูตรวิทยาศาสตรบัณฑิต สาขาวิชาเทคโนโลยีสารสนเทศ",
        "title_en": "Bachelor of Science Program in Information Technology",
        "degree_level": "ปริญญาตรี",
        "degree_name": "วท.บ. (เทคโนโลยีสารสนเทศ)",
        "university": "King Mongkut's Institute of Technology Ladkrabang",
        "university_th": "สถาบันเทคโนโลยีพระจอมเกล้าเจ้าคุณทหารลาดกระบัง",
        "faculty": "School of Information Technology",
        "faculty_th": "คณะเทคโนโลยีสารสนเทศ",
        "department": "Department of Information Technology",
        "department_th": "สาขาวิชาเทคโนโลยีสารสนเทศ",
        "program_type": "ภาคปกติ",
        "duration_years": "4 ปี",
        "total_credits": "130 หน่วยกิต",
        "tuition_per_semester": "32,000 บาท",
        "tuition_total": "256,000 บาท",
        "description": "หลักสูตรไอทียอดนิยมที่เน้นการพัฒนาซอฟต์แวร์ฟูลสแตก (Full Stack Development), ระบบฐานข้อมูลขนาดใหญ่, ระบบเครือข่ายและความมั่นคงปลอดภัยไซเบอร์ ตลอดจนการประยุกต์ใช้คลาวด์ในองค์กร",
        "curriculum_highlights": [
            "Full Stack Web & Mobile Development",
            "Database Systems & Data Modeling",
            "Network Infrastructure & Cloud Architecture",
            "Cybersecurity Principles & Threat Prevention",
            "DevOps Methodologies & Containerization"
        ],
        "career_paths": [
            "Software Developer",
            "Full Stack Engineer",
            "DevOps / Cloud Administrator",
            "System Analyst",
            "Network Engineer"
        ],
        "tags": ["Information Technology", "Software Development", "Full Stack", "Cloud", "KMITL", "Bachelor"],
        "website_url": "https://www.it.kmitl.ac.th"
    },
    {
        "id": "kmitl_it_dsba_bsc",
        "title_th": "หลักสูตรวิทยาศาสตรบัณฑิต สาขาวิชาวิทยาการข้อมูลและการวิเคราะห์เชิงธุรกิจ",
        "title_en": "Bachelor of Science Program in Data Science and Business Analytics",
        "degree_level": "ปริญญาตรี",
        "degree_name": "วท.บ. (วิทยาการข้อมูลและการวิเคราะห์เชิงธุรกิจ)",
        "university": "King Mongkut's Institute of Technology Ladkrabang",
        "university_th": "สถาบันเทคโนโลยีพระจอมเกล้าเจ้าคุณทหารลาดกระบัง",
        "faculty": "School of Information Technology",
        "faculty_th": "คณะเทคโนโลยีสารสนเทศ",
        "department": "Data Science and Business Analytics Program",
        "department_th": "สาขาวิชาวิทยาการข้อมูลและการวิเคราะห์เชิงธุรกิจ",
        "program_type": "ภาคปกติ",
        "duration_years": "4 ปี",
        "total_credits": "128 หน่วยกิต",
        "tuition_per_semester": "32,000 บาท",
        "tuition_total": "256,000 บาท",
        "description": "เน้นการเปลี่ยนผ่านข้อมูลเป็นมูลค่าทางธุรกิจ ครอบคลุมการวิเคราะห์ข้อมูลขั้นสูง (Data Analytics), แมชชีนเลิร์นนิง, การจัดทำแดชบอร์ดและการเล่าเรื่องด้วยข้อมูล (Data Storytelling) รวมถึงการบริหารจัดการข้อมูลระดับองค์กร",
        "curriculum_highlights": [
            "Data Mining & Machine Learning",
            "Big Data Engineering & Pipeline Development",
            "Business Intelligence & Data Visualization (Tableau/PowerBI)",
            "Predictive Analytics & Statistical Modeling",
            "Natural Language Processing for Business Insights"
        ],
        "career_paths": [
            "Data Scientist",
            "Data Analyst",
            "Data Engineer",
            "Business Intelligence Developer",
            "AI / Analytics Consultant"
        ],
        "tags": ["Data Science", "Business Analytics", "Machine Learning", "Big Data", "KMITL", "Bachelor"],
        "website_url": "https://www.it.kmitl.ac.th"
    },
    {
        "id": "kmitl_it_dti_bsc",
        "title_th": "หลักสูตรวิทยาศาสตรบัณฑิต สาขาวิชาเทคโนโลยีดิจิทัลและนวัตกรรม",
        "title_en": "Bachelor of Science Program in Digital Technology and Innovation",
        "degree_level": "ปริญญาตรี",
        "degree_name": "วท.บ. (เทคโนโลยีดิจิทัลและนวัตกรรม)",
        "university": "King Mongkut's Institute of Technology Ladkrabang",
        "university_th": "สถาบันเทคโนโลยีพระจอมเกล้าเจ้าคุณทหารลาดกระบัง",
        "faculty": "School of Information Technology",
        "faculty_th": "คณะเทคโนโลยีสารสนเทศ",
        "department": "Digital Technology and Innovation Program",
        "department_th": "สาขาวิชาเทคโนโลยีดิจิทัลและนวัตกรรม",
        "program_type": "ภาคปกติ",
        "duration_years": "4 ปี",
        "total_credits": "128 หน่วยกิต",
        "tuition_per_semester": "32,000 บาท",
        "tuition_total": "256,000 บาท",
        "description": "สร้างนักพัฒนานวัตกรรมดิจิทัลที่เชี่ยวชาญทั้งการสร้างซอฟต์แวร์ การพัฒนาแพลตฟอร์มดิจิทัล เทคโนโลยี Web3/Blockchain และการออกแบบประสบการณ์ผู้ใช้ (UX/UI) เพื่อสร้างสรรค์ผลิตภัณฑ์ดิจิทัลรุ่นใหม่",
        "curriculum_highlights": [
            "Digital Innovation & Product Management",
            "Cross-Platform Mobile & Web Development",
            "Blockchain Technology & Smart Contract Development",
            "UI/UX Design & Usability Testing",
            "AI-Driven Digital Products"
        ],
        "career_paths": [
            "Digital Product Manager",
            "UX/UI Designer",
            "Cross-Platform App Developer",
            "Blockchain Developer",
            "Tech Entrepreneur"
        ],
        "tags": ["Digital Innovation", "UX/UI", "Blockchain", "Product Management", "Software", "KMITL", "Bachelor"],
        "website_url": "https://www.it.kmitl.ac.th"
    },
    {
        "id": "kmitl_it_msc",
        "title_th": "หลักสูตรวิทยาศาสตรมหาบัณฑิต สาขาวิชาเทคโนโลยีสารสนเทศ",
        "title_en": "Master of Science Program in Information Technology",
        "degree_level": "ปริญญาโท",
        "degree_name": "วท.ม. (เทคโนโลยีสารสนเทศ)",
        "university": "King Mongkut's Institute of Technology Ladkrabang",
        "university_th": "สถาบันเทคโนโลยีพระจอมเกล้าเจ้าคุณทหารลาดกระบัง",
        "faculty": "School of Information Technology",
        "faculty_th": "คณะเทคโนโลยีสารสนเทศ",
        "department": "Department of Information Technology",
        "department_th": "สาขาวิชาเทคโนโลยีสารสนเทศ",
        "program_type": "ภาคปกติและภาคพิเศษ",
        "duration_years": "2 ปี",
        "total_credits": "36 หน่วยกิต",
        "tuition_per_semester": "38,000 บาท",
        "tuition_total": "152,000 บาท",
        "description": "หลักสูตรปริญญาโทที่มุ่งเน้นการจัดการเทคโนโลยีสารสนเทศระดับสูง วิศวกรรมข้อมูล (Data Engineering) คลาวด์คอมพิวติ้ง และความมั่นคงปลอดภัยไซเบอร์สำหรับองค์กรขนาดใหญ่",
        "curriculum_highlights": [
            "Advanced Information Technology Management",
            "Enterprise Data Engineering & Big Data Architecture",
            "Cloud Security & Infrastructure Architecture",
            "Advanced Software Quality Assurance",
            "Master Thesis / Special Project in IT"
        ],
        "career_paths": [
            "Senior IT Manager",
            "Enterprise Data Architect",
            "Cloud Architect",
            "IT Security Director",
            "IT Consultant"
        ],
        "tags": ["Information Technology", "Data Engineering", "Cloud", "IT Management", "KMITL", "Master"],
        "website_url": "https://www.it.kmitl.ac.th"
    },
    {
        "id": "kmitl_it_aiba_msc",
        "title_th": "หลักสูตรวิทยาศาสตรมหาบัณฑิต สาขาวิชาปัญญาประดิษฐ์เพื่อการวิเคราะห์เชิงธุรกิจ",
        "title_en": "Master of Science Program in Artificial Intelligence for Business Analytics",
        "degree_level": "ปริญญาโท",
        "degree_name": "วท.ม. (ปัญญาประดิษฐ์เพื่อการวิเคราะห์เชิงธุรกิจ)",
        "university": "King Mongkut's Institute of Technology Ladkrabang",
        "university_th": "สถาบันเทคโนโลยีพระจอมเกล้าเจ้าคุณทหารลาดกระบัง",
        "faculty": "School of Information Technology",
        "faculty_th": "คณะเทคโนโลยีสารสนเทศ",
        "department": "Artificial Intelligence and Analytics",
        "department_th": "สาขาวิชาปัญญาประดิษฐ์และการวิเคราะห์ข้อมูล",
        "program_type": "ภาคพิเศษ (วันหยุด เสาร์-อาทิตย์)",
        "duration_years": "2 ปี",
        "total_credits": "36 หน่วยกิต",
        "tuition_per_semester": "45,000 บาท",
        "tuition_total": "180,000 บาท",
        "description": "เน้นการนำปัญญาประดิษฐ์ (AI), Deep Learning, โมเดลภาษาขนาดใหญ่ (LLMs) และ Business Intelligence มาขับเคลื่อนกลยุทธ์ทางธุรกิจ การพยากรณ์ตลาด และการเพิ่มประสิทธิภาพการดำเนินงาน",
        "curriculum_highlights": [
            "Applied Artificial Intelligence & Machine Learning for Business",
            "Generative AI & Enterprise LLM Applications",
            "Customer Analytics & Churn Prediction Models",
            "Strategic Data-Driven Decision Making",
            "AI Ethics & Governance in Organizations"
        ],
        "career_paths": [
            "Lead AI Business Analyst",
            "Chief Data & Analytics Officer (CDAO)",
            "AI Strategy Consultant",
            "Enterprise Data Scientist",
            "Head of Business Intelligence"
        ],
        "tags": ["AI for Business", "Generative AI", "Business Analytics", "Data Science", "KMITL", "Master"],
        "website_url": "https://www.it.kmitl.ac.th"
    },
    {
        "id": "kmitl_arch_digital_media_bfa",
        "title_th": "หลักสูตรศิลปกรรมศาสตรบัณฑิต สาขาวิชาดิจิทัลมีเดียและศิลปะปฏิสัมพันธ์",
        "title_en": "Bachelor of Fine Arts Program in Digital Media and Interactive Design",
        "degree_level": "ปริญญาตรี",
        "degree_name": "ศล.บ. (ดิจิทัลมีเดียและศิลปะปฏิสัมพันธ์)",
        "university": "King Mongkut's Institute of Technology Ladkrabang",
        "university_th": "สถาบันเทคโนโลยีพระจอมเกล้าเจ้าคุณทหารลาดกระบัง",
        "faculty": "School of Architecture, Art, and Design",
        "faculty_th": "คณะสถาปัตยกรรม ศิลปะและการออกแบบ",
        "department": "Department of Digital Media Arts",
        "department_th": "ภาควิชาศิลปะดิจิทัลมีเดีย",
        "program_type": "ภาคปกติ",
        "duration_years": "4 ปี",
        "total_credits": "130 หน่วยกิต",
        "tuition_per_semester": "26,000 บาท",
        "tuition_total": "208,000 บาท",
        "description": "ผสมผสานศิลปะ การเล่าเรื่อง การออกแบบอินเทอร์แอคทีฟ แอนิเมชัน 3 มิติ และเทคโนโลยีดิจิทัลสมัยใหม่ เช่น Generative Art, Projection Mapping และ Virtual Reality",
        "curriculum_highlights": [
            "Interactive Media Design & Creative Coding",
            "3D Digital Animation & Motion Design",
            "Projection Mapping & Immersive Installation",
            "UI/UX Design for Digital Experiences",
            "Generative AI in Visual Arts"
        ],
        "career_paths": [
            "Interactive Media Artist / Designer",
            "Motion Graphics Designer",
            "UX/UI Visual Designer",
            "Creative Technologist",
            "3D Animation Artist"
        ],
        "tags": ["Digital Media", "Interactive Art", "Animation", "Creative Design", "KMITL", "Bachelor"],
        "website_url": "https://aad.kmitl.ac.th"
    },
    {
        "id": "kmitl_sci_cs_bsc",
        "title_th": "หลักสูตรวิทยาศาสตรบัณฑิต สาขาวิชาวิทยาการคอมพิวเตอร์",
        "title_en": "Bachelor of Science Program in Computer Science",
        "degree_level": "ปริญญาตรี",
        "degree_name": "วท.บ. (วิทยาการคอมพิวเตอร์)",
        "university": "King Mongkut's Institute of Technology Ladkrabang",
        "university_th": "สถาบันเทคโนโลยีพระจอมเกล้าเจ้าคุณทหารลาดกระบัง",
        "faculty": "School of Science",
        "faculty_th": "คณะวิทยาศาสตร์",
        "department": "Department of Computer Science",
        "department_th": "ภาควิชาวิทยาการคอมพิวเตอร์",
        "program_type": "ภาคปกติ",
        "duration_years": "4 ปี",
        "total_credits": "134 หน่วยกิต",
        "tuition_per_semester": "19,000 บาท",
        "tuition_total": "152,000 บาท",
        "description": "เน้นรากฐานทฤษฎีวิทยาการคอมพิวเตอร์ที่เข้มแข็ง การพัฒนาอัลกอริทึมขั้นสูง ปัญญาประดิษฐ์ การประมวลผลข้อมูลขนาดใหญ่ และการเขียนโปรแกรมเชิงแข่งขัน",
        "curriculum_highlights": [
            "Advanced Algorithm Design & Analysis",
            "Artificial Intelligence & Machine Learning",
            "Web & Mobile Application Development",
            "Data Science & Statistical Learning",
            "Cloud Computing & Database Architecture"
        ],
        "career_paths": [
            "Software Engineer",
            "Data Scientist",
            "AI Developer",
            "Backend Developer",
            "Algorithm Specialist"
        ],
        "tags": ["Computer Science", "Algorithms", "AI", "Software Development", "KMITL", "Bachelor"],
        "website_url": "https://www.science.kmitl.ac.th"
    },

    # =========================================================================
    # KMUTNB (มหาวิทยาลัยเทคโนโลยีพระจอมเกล้าพระนครเหนือ)
    # =========================================================================
    {
        "id": "kmutnb_eng_cpe_beng",
        "title_th": "หลักสูตรวิศวกรรมศาสตรบัณฑิต สาขาวิชาวิศวกรรมคอมพิวเตอร์",
        "title_en": "Bachelor of Engineering Program in Computer Engineering",
        "degree_level": "ปริญญาตรี",
        "degree_name": "วศ.บ. (วิศวกรรมคอมพิวเตอร์)",
        "university": "King Mongkut's University of Technology North Bangkok",
        "university_th": "มหาวิทยาลัยเทคโนโลยีพระจอมเกล้าพระนครเหนือ",
        "faculty": "Faculty of Engineering",
        "faculty_th": "คณะวิศวกรรมศาสตร์",
        "department": "Department of Computer Engineering",
        "department_th": "ภาควิชาวิศวกรรมคอมพิวเตอร์",
        "program_type": "ภาคปกติ",
        "duration_years": "4 ปี",
        "total_credits": "140 หน่วยกิต",
        "tuition_per_semester": "19,000 บาท",
        "tuition_total": "152,000 บาท",
        "description": "หลักสูตรวิศวกรรมคอมพิวเตอร์ที่เน้นการปฏิบัติงานจริงสไตล์พระนครเหนือ (Hands-on Engineering) มีความเชี่ยวชาญทั้งระบบฮาร์ดแวร์ ไมโครคอนโทรลเลอร์ ระบบเครือข่าย วิศวกรรมซอฟต์แวร์ และปัญญาประดิษฐ์เชิงวิศวกรรม",
        "curriculum_highlights": [
            "Digital Circuits & Microcontroller Interfacing",
            "Object-Oriented & Full-Stack Software Engineering",
            "Computer Networks & Network Security Protocols",
            "Embedded Linux & Real-Time Operating Systems",
            "Applied Machine Learning & Computer Vision",
            "Cloud Infrastructure & Virtualization"
        ],
        "career_paths": [
            "Computer Engineer",
            "Embedded Systems Developer",
            "Full Stack Software Developer",
            "Network & Security Specialist",
            "AI/ML Systems Engineer"
        ],
        "tags": ["Computer Engineering", "Embedded Systems", "Hardware", "Software", "KMUTNB", "Bachelor"],
        "website_url": "https://eng.kmutnb.ac.th"
    },
    {
        "id": "kmutnb_eng_robotics_beng",
        "title_th": "หลักสูตรวิศวกรรมศาสตรบัณฑิต สาขาวิชาวิศวกรรมหุ่นยนต์และระบบอัตโนมัติ",
        "title_en": "Bachelor of Engineering Program in Robotic Engineering and Automation Systems",
        "degree_level": "ปริญญาตรี",
        "degree_name": "วศ.บ. (วิศวกรรมหุ่นยนต์และระบบอัตโนมัติ)",
        "university": "King Mongkut's University of Technology North Bangkok",
        "university_th": "มหาวิทยาลัยเทคโนโลยีพระจอมเกล้าพระนครเหนือ",
        "faculty": "Faculty of Engineering",
        "faculty_th": "คณะวิศวกรรมศาสตร์",
        "department": "Department of Robotics and Automation Engineering",
        "department_th": "ภาควิชาวิศวกรรมหุ่นยนต์และระบบอัตโนมัติ",
        "program_type": "ภาคปกติ",
        "duration_years": "4 ปี",
        "total_credits": "142 หน่วยกิต",
        "tuition_per_semester": "22,000 บาท",
        "tuition_total": "176,000 บาท",
        "description": "สร้างวิศวกรผู้เชี่ยวชาญด้านหุ่นยนต์อุตสาหกรรม (Industrial Robots), ระบบอัตโนมัติในสายการผลิต, ระบบแมคคาทรอนิกส์, และการควบคุมด้วยสมองกลอัจฉริยะ โดดเด่นด้วยประวัติศาสตร์ทีมหุ่นยนต์กู้ภัยแชมป์โลก World RoboCup",
        "curriculum_highlights": [
            "Industrial Robotics & Robot Kinematics",
            "PLC, HMI & Automated Control Systems",
            "Robotic Sensors, Vision & Actuation",
            "Robotics Middleware (ROS/ROS2)",
            "Factory Automation & Digital Manufacturing"
        ],
        "career_paths": [
            "Robotics Engineer",
            "Automation Systems Integrator",
            "Mechatronics Engineer",
            "PLC & Control Programmer",
            "Industrial Robot Maintenance Specialist"
        ],
        "tags": ["Robotics", "Automation", "Mechatronics", "PLC", "Engineering", "KMUTNB", "Bachelor"],
        "website_url": "https://eng.kmutnb.ac.th"
    },
    {
        "id": "kmutnb_eng_electrical_software_beng",
        "title_th": "หลักสูตรวิศวกรรมศาสตรบัณฑิต สาขาวิชาวิศวกรรมไฟฟ้าและระบบซอฟต์แวร์",
        "title_en": "Bachelor of Engineering Program in Electrical and Software Systems Engineering",
        "degree_level": "ปริญญาตรี",
        "degree_name": "วศ.บ. (วิศวกรรมไฟฟ้าและระบบซอฟต์แวร์)",
        "university": "King Mongkut's University of Technology North Bangkok",
        "university_th": "มหาวิทยาลัยเทคโนโลยีพระจอมเกล้าพระนครเหนือ",
        "faculty": "Faculty of Engineering",
        "faculty_th": "คณะวิศวกรรมศาสตร์",
        "department": "Department of Electrical and Computer Engineering",
        "department_th": "ภาควิชาวิศวกรรมไฟฟ้าและคอมพิวเตอร์",
        "program_type": "ภาคปกติ",
        "duration_years": "4 ปี",
        "total_credits": "138 หน่วยกิต",
        "tuition_per_semester": "20,000 บาท",
        "tuition_total": "160,000 บาท",
        "description": "ผสานศาสตร์วิศวกรรมไฟฟ้าเข้ากับการพัฒนาซอฟต์แวร์ระบบ เช่น ระบบสมาร์ตกริด (Smart Grid) การจัดการพลังงานอัจฉริยะ ระบบควบคุมยานยนต์ไฟฟ้า (EV) และระบบซอฟต์แวร์ฝังตัวชั้นสูง",
        "curriculum_highlights": [
            "Smart Grid Systems & Energy Management",
            "Embedded Software & Real-Time Firmware",
            "Electric Vehicle (EV) Control Architectures",
            "Industrial IoT & SCADA Software",
            "Applied AI for Power and Energy Systems"
        ],
        "career_paths": [
            "Electrical & Software Systems Engineer",
            "EV Systems Engineer",
            "Smart Grid Software Specialist",
            "Embedded Firmware Developer",
            "Industrial Energy Automation Engineer"
        ],
        "tags": ["Electrical Engineering", "Software Systems", "Smart Grid", "EV", "Embedded", "KMUTNB", "Bachelor"],
        "website_url": "https://eng.kmutnb.ac.th"
    },
    {
        "id": "kmutnb_eng_cpe_meng",
        "title_th": "หลักสูตรวิศวกรรมศาสตรมหาบัณฑิต สาขาวิชาวิศวกรรมคอมพิวเตอร์",
        "title_en": "Master of Engineering Program in Computer Engineering",
        "degree_level": "ปริญญาโท",
        "degree_name": "วศ.ม. (วิศวกรรมคอมพิวเตอร์)",
        "university": "King Mongkut's University of Technology North Bangkok",
        "university_th": "มหาวิทยาลัยเทคโนโลยีพระจอมเกล้าพระนครเหนือ",
        "faculty": "Faculty of Engineering",
        "faculty_th": "คณะวิศวกรรมศาสตร์",
        "department": "Department of Computer Engineering",
        "department_th": "ภาควิชาวิศวกรรมคอมพิวเตอร์",
        "program_type": "ภาคปกติและภาคพิเศษ",
        "duration_years": "2 ปี",
        "total_credits": "36 หน่วยกิต",
        "tuition_per_semester": "28,000 บาท",
        "tuition_total": "112,000 บาท",
        "description": "หลักสูตรปริญญาโทที่มุ่งเน้นการวิจัยทางวิศวกรรมคอมพิวเตอร์ขั้นสูง เช่น ระบบปัญญาประดิษฐ์อุตสาหกรรม, เครือข่ายการสื่อสารความเร็วสูง, สถาปัตยกรรมคลาวด์และเอดจ์ และการรักษาความปลอดภัยระบบไซเบอร์-กายภาพ",
        "curriculum_highlights": [
            "Advanced Embedded System Architecture",
            "Deep Learning & Industrial AI Applications",
            "Cyber-Physical System Security",
            "Distributed Computing & Big Data Engineering",
            "Master Thesis Research in Computer Engineering"
        ],
        "career_paths": [
            "Principal Computer Engineer",
            "AI/ML Research Engineer",
            "Embedded Architecture Lead",
            "Senior Systems Architect",
            "Engineering Educator"
        ],
        "tags": ["Computer Engineering", "AI", "Embedded", "Research", "KMUTNB", "Master"],
        "website_url": "https://eng.kmutnb.ac.th"
    },
    {
        "id": "kmutnb_tggs_esse_meng",
        "title_th": "หลักสูตรวิศวกรรมศาสตรมหาบัณฑิต สาขาวิชาวิศวกรรมระบบไฟฟ้าและซอฟต์แวร์ (TGGS)",
        "title_en": "Master of Engineering Program in Electrical and Software Systems Engineering (TGGS)",
        "degree_level": "ปริญญาโท",
        "degree_name": "วศ.ม. (วิศวกรรมระบบไฟฟ้าและซอฟต์แวร์)",
        "university": "King Mongkut's University of Technology North Bangkok",
        "university_th": "มหาวิทยาลัยเทคโนโลยีพระจอมเกล้าพระนครเหนือ",
        "faculty": "The Sirindhorn International Thai-German Graduate School (TGGS)",
        "faculty_th": "บัณฑิตวิทยาลัยวิศวกรรมศาสตร์นานาชาติสิรินธร ไทย-เยอรมัน (TGGS)",
        "department": "Electrical and Software Systems Engineering",
        "department_th": "สาขาวิชาวิศวกรรมระบบไฟฟ้าและซอฟต์แวร์",
        "program_type": "นานาชาติ",
        "duration_years": "2 ปี",
        "total_credits": "36 หน่วยกิต",
        "tuition_per_semester": "60,000 บาท",
        "tuition_total": "240,000 บาท",
        "description": "หลักสูตรนานาชาติมาตรฐานเยอรมัน ร่วมมือกับมหาวิทยาลัย RWTH Aachen University ประเทศเยอรมนี เน้นการสร้างระบบซอฟต์แวร์ฝังตัวขนาดใหญ่ สถาปัตยกรรมซอฟต์แวร์สำหรับยานยนต์และระบบอัตโนมัติ พร้อมโอกาสฝึกงานวิจัยในประเทศเยอรมนี",
        "curriculum_highlights": [
            "German-Standard Software Architecture & Quality Engineering",
            "Automotive Software Systems & AUTOSAR",
            "Embedded Real-Time Operating Systems",
            "Advanced Control & AI for Industrial Cyber-Physical Systems",
            "International Industry Internship & Master Thesis"
        ],
        "career_paths": [
            "Automotive Software Engineer",
            "Embedded Systems Architect",
            "Lead Software Engineer (German Industry Standard)",
            "R&D Engineer in Europe & Global Tech",
            "Doctoral Researcher"
        ],
        "tags": ["TGGS", "Software Systems", "German Standard", "Automotive Software", "International", "KMUTNB", "Master"],
        "website_url": "https://tggs.kmutnb.ac.th"
    },
    {
        "id": "kmutnb_tggs_csg_meng",
        "title_th": "หลักสูตรวิศวกรรมศาสตรมหาบัณฑิต สาขาวิชาวิศวกรรมระบบสื่อสารและสมาร์ตกริด (TGGS)",
        "title_en": "Master of Engineering Program in Communications and Smart Grid Engineering (TGGS)",
        "degree_level": "ปริญญาโท",
        "degree_name": "วศ.ม. (วิศวกรรมระบบสื่อสารและสมาร์ตกริด)",
        "university": "King Mongkut's University of Technology North Bangkok",
        "university_th": "มหาวิทยาลัยเทคโนโลยีพระจอมเกล้าพระนครเหนือ",
        "faculty": "The Sirindhorn International Thai-German Graduate School (TGGS)",
        "faculty_th": "บัณฑิตวิทยาลัยวิศวกรรมศาสตร์นานาชาติสิรินธร ไทย-เยอรมัน (TGGS)",
        "department": "Communications and Smart Grid Engineering",
        "department_th": "สาขาวิชาวิศวกรรมระบบสื่อสารและสมาร์ตกริด",
        "program_type": "นานาชาติ",
        "duration_years": "2 ปี",
        "total_credits": "36 หน่วยกิต",
        "tuition_per_semester": "60,000 บาท",
        "tuition_total": "240,000 บาท",
        "description": "หลักสูตรนานาชาติมาตรฐานเยอรมัน มุ่งเน้นระบบสื่อสารไร้สาย 5G/6G, ระบบสมาร์ตกริด, การประมวลผลสัญญาณอัจฉริยะ, และการจัดการพลังงานหมุนเวียนยุคใหม่ ร่วมมือกับ RWTH Aachen University",
        "curriculum_highlights": [
            "Smart Grid Communication & Cyber Security",
            "Advanced Wireless Communications (5G/6G)",
            "Statistical Signal Processing & Machine Learning",
            "Renewable Energy Grid Integration",
            "Master Thesis Research with RWTH Aachen Collaboration"
        ],
        "career_paths": [
            "Smart Grid Specialist",
            "Telecommunications Engineer",
            "Wireless Network Architect",
            "Energy IoT Solutions Engineer",
            "International Research Scientist"
        ],
        "tags": ["TGGS", "Communications", "Smart Grid", "5G", "International", "KMUTNB", "Master"],
        "website_url": "https://tggs.kmutnb.ac.th"
    },
    {
        "id": "kmutnb_tggs_mechatronics_meng",
        "title_th": "หลักสูตรวิศวกรรมศาสตรมหาบัณฑิต สาขาวิชาวิศวกรรมเมคคาทรอนิกส์ (TGGS)",
        "title_en": "Master of Engineering Program in Mechatronics Engineering (TGGS)",
        "degree_level": "ปริญญาโท",
        "degree_name": "วศ.ม. (วิศวกรรมเมคคาทรอนิกส์)",
        "university": "King Mongkut's University of Technology North Bangkok",
        "university_th": "มหาวิทยาลัยเทคโนโลยีพระจอมเกล้าพระนครเหนือ",
        "faculty": "The Sirindhorn International Thai-German Graduate School (TGGS)",
        "faculty_th": "บัณฑิตวิทยาลัยวิศวกรรมศาสตร์นานาชาติสิรินธร ไทย-เยอรมัน (TGGS)",
        "department": "Mechatronics Engineering",
        "department_th": "สาขาวิชาวิศวกรรมเมคคาทรอนิกส์",
        "program_type": "นานาชาติ",
        "duration_years": "2 ปี",
        "total_credits": "36 หน่วยกิต",
        "tuition_per_semester": "60,000 บาท",
        "tuition_total": "240,000 บาท",
        "description": "หลักสูตรระดับสากลเน้นการบูรณาการขั้นสูงของระบบกลศาสตร์ อิเล็กทรอนิกส์ การควบคุม และการประมวลผลคอมพิวเตอร์ สำหรับหุ่นยนต์อุตสาหกรรม ยานยนต์อัตโนมัติ และระบบการผลิตขั้นสูงตามมาตรฐานอุตสาหกรรมเยอรมนี",
        "curriculum_highlights": [
            "Advanced Mechatronic System Modeling & Simulation",
            "State-Space Control & Robust Control Design",
            "Sensors & Actuators in Advanced Robotics",
            "Autonomous Driving Systems & ADAS",
            "Master Thesis in Mechatronics"
        ],
        "career_paths": [
            "Senior Mechatronics Engineer",
            "Autonomous Driving Systems Engineer",
            "Robotics & Automation Specialist",
            "R&D Engineer in Automotive/Manufacturing",
            "Academic Researcher"
        ],
        "tags": ["TGGS", "Mechatronics", "Robotics", "Autonomous Vehicles", "International", "KMUTNB", "Master"],
        "website_url": "https://tggs.kmutnb.ac.th"
    },
    {
        "id": "kmutnb_sci_cs_bsc",
        "title_th": "หลักสูตรวิทยาศาสตรบัณฑิต สาขาวิชาวิทยาการคอมพิวเตอร์",
        "title_en": "Bachelor of Science Program in Computer Science",
        "degree_level": "ปริญญาตรี",
        "degree_name": "วท.บ. (วิทยาการคอมพิวเตอร์)",
        "university": "King Mongkut's University of Technology North Bangkok",
        "university_th": "มหาวิทยาลัยเทคโนโลยีพระจอมเกล้าพระนครเหนือ",
        "faculty": "Faculty of Applied Science",
        "faculty_th": "คณะวิทยาศาสตร์ประยุกต์",
        "department": "Department of Computer and Information Science",
        "department_th": "ภาควิชาวิทยาการคอมพิวเตอร์และสารสนเทศ",
        "program_type": "ภาคปกติ",
        "duration_years": "4 ปี",
        "total_credits": "132 หน่วยกิต",
        "tuition_per_semester": "19,000 บาท",
        "tuition_total": "152,000 บาท",
        "description": "เน้นรากฐานการพัฒนาซอฟต์แวร์ที่มีประสิทธิภาพสูง อัลกอริทึม โครงสร้างข้อมูล ปัญญาประดิษฐ์ และระบบความปลอดภัยทางคอมพิวเตอร์ พร้อมสายแทร็กให้เลือกเรียนในปี 3-4 เช่น AI, Full Stack และ Network & Security",
        "curriculum_highlights": [
            "Algorithms, Data Structures & System Programming",
            "Full Stack Web & Mobile Software Development",
            "Artificial Intelligence, Machine Learning & NLP",
            "Database Systems & Distributed Storage",
            "Cybersecurity & Cloud Systems"
        ],
        "career_paths": [
            "Software Developer",
            "Full Stack Developer",
            "Data Scientist / ML Developer",
            "System Analyst",
            "Cybersecurity Analyst"
        ],
        "tags": ["Computer Science", "Software Development", "AI", "Applied Science", "KMUTNB", "Bachelor"],
        "website_url": "https://sci.kmutnb.ac.th"
    },
    {
        "id": "kmutnb_sci_dse_bsc",
        "title_th": "หลักสูตรวิทยาศาสตรบัณฑิต สาขาวิชาวิทยาการข้อมูลและวิศวกรรมซอฟต์แวร์",
        "title_en": "Bachelor of Science Program in Data Science and Software Engineering",
        "degree_level": "ปริญญาตรี",
        "degree_name": "วท.บ. (วิทยาการข้อมูลและวิศวกรรมซอฟต์แวร์)",
        "university": "King Mongkut's University of Technology North Bangkok",
        "university_th": "มหาวิทยาลัยเทคโนโลยีพระจอมเกล้าพระนครเหนือ",
        "faculty": "Faculty of Applied Science",
        "faculty_th": "คณะวิทยาศาสตร์ประยุกต์",
        "department": "Department of Computer and Information Science",
        "department_th": "ภาควิชาวิทยาการคอมพิวเตอร์และสารสนเทศ",
        "program_type": "ภาคปกติ",
        "duration_years": "4 ปี",
        "total_credits": "130 หน่วยกิต",
        "tuition_per_semester": "20,000 บาท",
        "tuition_total": "160,000 บาท",
        "description": "หลักสูตรที่ผสมผสานระหว่างวิทยาการข้อมูล (Data Science) และวิศวกรรมซอฟต์แวร์ (Software Engineering) เพื่อผลิตบุคลากรที่สามารถพัฒนาไปป์ไลน์ข้อมูลขนาดใหญ่และสร้างโมเดล AI ขึ้นสู่ระบบจริงได้อย่างสมบูรณ์",
        "curriculum_highlights": [
            "Data Engineering & Big Data Architectures",
            "Machine Learning & Deep Learning Implementation",
            "Enterprise Software Architecture & Clean Code",
            "DevOps, MLOps & CI/CD Pipelines",
            "Data Visualization & Business Analytics"
        ],
        "career_paths": [
            "Data Engineer",
            "Machine Learning Engineer",
            "Data Scientist",
            "Full Stack Software Engineer",
            "MLOps Specialist"
        ],
        "tags": ["Data Science", "Software Engineering", "Big Data", "MLOps", "AI", "KMUTNB", "Bachelor"],
        "website_url": "https://sci.kmutnb.ac.th"
    },
    {
        "id": "kmutnb_sci_stat_ds_bsc",
        "title_th": "หลักสูตรวิทยาศาสตรบัณฑิต สาขาวิชาวิทยาศาสตร์ข้อมูลและการวิเคราะห์เชิงสถิติ",
        "title_en": "Bachelor of Science Program in Statistical Data Science and Analytics",
        "degree_level": "ปริญญาตรี",
        "degree_name": "วท.บ. (วิทยาศาสตร์ข้อมูลและการวิเคราะห์เชิงสถิติ)",
        "university": "King Mongkut's University of Technology North Bangkok",
        "university_th": "มหาวิทยาลัยเทคโนโลยีพระจอมเกล้าพระนครเหนือ",
        "faculty": "Faculty of Applied Science",
        "faculty_th": "คณะวิทยาศาสตร์ประยุกต์",
        "department": "Department of Applied Statistics",
        "department_th": "ภาควิชาสถิติประยุกต์",
        "program_type": "ภาคปกติ",
        "duration_years": "4 ปี",
        "total_credits": "130 หน่วยกิต",
        "tuition_per_semester": "19,000 บาท",
        "tuition_total": "152,000 บาท",
        "description": "เน้นการสร้างแบบจำลองทางสถิติขั้นสูง การวิเคราะห์ข้อมูลขนาดใหญ่ การพยากรณ์เชิงธุรกิจ และการประยุกต์ใช้โมเดล Machine Learning ในอุตสาหกรรมการเงิน ประกันภัย และธุรกิจดิจิทัล",
        "curriculum_highlights": [
            "Statistical Inference & Probability Modeling",
            "Predictive Modeling & Machine Learning",
            "Time Series Analysis & Forecasting",
            "R & Python for Statistical Data Analysis",
            "Business Analytics & Risk Assessment"
        ],
        "career_paths": [
            "Statistical Data Scientist",
            "Data Analyst",
            "Risk Analyst",
            "Actuarial & Business Intelligence Specialist",
            "Quantitative Researcher"
        ],
        "tags": ["Data Science", "Statistics", "Analytics", "Machine Learning", "KMUTNB", "Bachelor"],
        "website_url": "https://sci.kmutnb.ac.th"
    },
    {
        "id": "kmutnb_sci_applied_math_bsc",
        "title_th": "หลักสูตรวิทยาศาสตรบัณฑิต สาขาวิชาคณิตศาสตร์ประยุกต์",
        "title_en": "Bachelor of Science Program in Applied Mathematics",
        "degree_level": "ปริญญาตรี",
        "degree_name": "วท.บ. (คณิตศาสตร์ประยุกต์)",
        "university": "King Mongkut's University of Technology North Bangkok",
        "university_th": "มหาวิทยาลัยเทคโนโลยีพระจอมเกล้าพระนครเหนือ",
        "faculty": "Faculty of Applied Science",
        "faculty_th": "คณะวิทยาศาสตร์ประยุกต์",
        "department": "Department of Mathematics",
        "department_th": "ภาควิชาคณิตศาสตร์",
        "program_type": "ภาคปกติ",
        "duration_years": "4 ปี",
        "total_credits": "132 หน่วยกิต",
        "tuition_per_semester": "19,000 บาท",
        "tuition_total": "152,000 บาท",
        "description": "มุ่งเน้นการประยุกต์ใช้แบบจำลองทางคณิตศาสตร์ การคำนวณเชิงตัวเลข การเงินเชิงปริมาณ และการออกแบบอัลกอริทึมการคำนวณขั้นสูงเพื่อแก้ปัญหาในภาคอุตสาหกรรมและการเงิน",
        "curriculum_highlights": [
            "Numerical Analysis & Scientific Computing",
            "Mathematical Optimization & Operations Research",
            "Financial Mathematics & Quantitative Modeling",
            "Data Science Algorithms & Python/MATLAB",
            "Differential Equations & System Simulation"
        ],
        "career_paths": [
            "Quantitative Analyst",
            "Operations Research Analyst",
            "Applied Mathematician",
            "Data Scientist",
            "Financial Model Developer"
        ],
        "tags": ["Applied Mathematics", "Quant", "Operations Research", "Data Science", "KMUTNB", "Bachelor"],
        "website_url": "https://sci.kmutnb.ac.th"
    },
    {
        "id": "kmutnb_sci_industrial_physics_bsc",
        "title_th": "หลักสูตรวิทยาศาสตรบัณฑิต สาขาวิชาฟิสิกส์อุตสาหกรรมและอุปกรณ์การแพทย์",
        "title_en": "Bachelor of Science Program in Industrial Physics and Medical Device Technology",
        "degree_level": "ปริญญาตรี",
        "degree_name": "วท.บ. (ฟิสิกส์อุตสาหกรรมและอุปกรณ์การแพทย์)",
        "university": "King Mongkut's University of Technology North Bangkok",
        "university_th": "มหาวิทยาลัยเทคโนโลยีพระจอมเกล้าพระนครเหนือ",
        "faculty": "Faculty of Applied Science",
        "faculty_th": "คณะวิทยาศาสตร์ประยุกต์",
        "department": "Department of Industrial Physics and Medical Devices",
        "department_th": "ภาควิชาฟิสิกส์อุตสาหกรรมและอุปกรณ์การแพทย์",
        "program_type": "ภาคปกติ",
        "duration_years": "4 ปี",
        "total_credits": "136 หน่วยกิต",
        "tuition_per_semester": "19,000 บาท",
        "tuition_total": "152,000 บาท",
        "description": "เน้นฟิสิกส์ประยุกต์ทางอุตสาหกรรม เซมิคอนดักเตอร์ เลเซอร์ โฟโทนิกส์ และเทคโนโลยีเครื่องมือและอุปกรณ์ทางการแพทย์ การบำรุงรักษาและการสอบเทียบมาตรฐานสากล",
        "curriculum_highlights": [
            "Medical Device Technology & Calibration",
            "Applied Optics, Lasers & Photonics",
            "Semiconductor Physics & Sensor Fabrication",
            "Radiation Physics & Medical Imaging Systems",
            "Industrial Quality Control & Standards"
        ],
        "career_paths": [
            "Medical Device Specialist",
            "Industrial Physicist",
            "Photonics & Optics Engineer",
            "Calibration & Quality Assurance Specialist",
            "Semiconductor Process Engineer"
        ],
        "tags": ["Applied Physics", "Medical Devices", "Photonics", "Semiconductor", "KMUTNB", "Bachelor"],
        "website_url": "https://sci.kmutnb.ac.th"
    },
    {
        "id": "kmutnb_sci_cs_msc",
        "title_th": "หลักสูตรวิทยาศาสตรมหาบัณฑิต สาขาวิชาวิทยาการคอมพิวเตอร์",
        "title_en": "Master of Science Program in Computer Science",
        "degree_level": "ปริญญาโท",
        "degree_name": "วท.ม. (วิทยาการคอมพิวเตอร์)",
        "university": "King Mongkut's University of Technology North Bangkok",
        "university_th": "มหาวิทยาลัยเทคโนโลยีพระจอมเกล้าพระนครเหนือ",
        "faculty": "Faculty of Applied Science",
        "faculty_th": "คณะวิทยาศาสตร์ประยุกต์",
        "department": "Department of Computer and Information Science",
        "department_th": "ภาควิชาวิทยาการคอมพิวเตอร์และสารสนเทศ",
        "program_type": "ภาคปกติและภาคพิเศษ",
        "duration_years": "2 ปี",
        "total_credits": "36 หน่วยกิต",
        "tuition_per_semester": "25,000 บาท",
        "tuition_total": "100,000 บาท",
        "description": "เน้นงานวิจัยและการพัฒนาเชิงลึกในด้านปัญญาประดิษฐ์ การประมวลผลภาษาธรรมชาติ (NLP), เครือข่ายประสาทเทียมขั้นสูง, และสถาปัตยกรรมข้อมูลขนาดใหญ่",
        "curriculum_highlights": [
            "Advanced Machine Learning & Neural Networks",
            "Natural Language Processing & LLM Fine-Tuning",
            "Cloud & Distributed Systems Computing",
            "Information Security & Privacy",
            "Master Thesis Research in Computer Science"
        ],
        "career_paths": [
            "Senior Data Scientist",
            "AI/ML Research Scientist",
            "Lead Software Engineer",
            "University Lecturer",
            "IT Research Consultant"
        ],
        "tags": ["Computer Science", "Machine Learning", "NLP", "Applied Science", "KMUTNB", "Master"],
        "website_url": "https://sci.kmutnb.ac.th"
    },
    {
        "id": "kmutnb_sci_math_comp_ai_msc",
        "title_th": "หลักสูตรวิทยาศาสตรมหาบัณฑิต สาขาวิชาคณิตศาสตร์เชิงวิทยาการคอมพิวเตอร์และปัญญาเชิงคำนวณ",
        "title_en": "Master of Science Program in Mathematics in Computer Science and Computational Intelligence",
        "degree_level": "ปริญญาโท",
        "degree_name": "วท.ม. (คณิตศาสตร์เชิงวิทยาการคอมพิวเตอร์และปัญญาเชิงคำนวณ)",
        "university": "King Mongkut's University of Technology North Bangkok",
        "university_th": "มหาวิทยาลัยเทคโนโลยีพระจอมเกล้าพระนครเหนือ",
        "faculty": "Faculty of Applied Science",
        "faculty_th": "คณะวิทยาศาสตร์ประยุกต์",
        "department": "Department of Mathematics",
        "department_th": "ภาควิชาคณิตศาสตร์",
        "program_type": "ภาคปกติและภาคพิเศษ",
        "duration_years": "2 ปี",
        "total_credits": "36 หน่วยกิต",
        "tuition_per_semester": "26,000 บาท",
        "tuition_total": "104,000 บาท",
        "description": "หลักสูตรบัณฑิตศึกษาเฉพาะทางที่ผสานรากฐานคณิตศาสตร์เชิงลึก เข้ากับอัลกอริทึมวิทยาการคอมพิวเตอร์และปัญญาเชิงคำนวณ (Computational Intelligence) เพื่อการวิเคราะห์และการจำลองโมเดลที่มีความซับซ้อนสูง",
        "curriculum_highlights": [
            "Computational Intelligence & Evolutionary Algorithms",
            "Mathematical Foundations of Deep Learning",
            "Advanced Optimization Techniques",
            "Numerical Linear Algebra for Big Data",
            "Master Thesis in Computational Intelligence"
        ],
        "career_paths": [
            "Computational AI Researcher",
            "Quantitative Algorithm Developer",
            "Optimization Specialist",
            "Machine Learning Mathematician",
            "Academic Faculty"
        ],
        "tags": ["Computational Intelligence", "Applied Mathematics", "AI", "Optimization", "KMUTNB", "Master"],
        "website_url": "https://sci.kmutnb.ac.th"
    },
    {
        "id": "kmutnb_itdi_it_bsc",
        "title_th": "หลักสูตรวิทยาศาสตรบัณฑิต สาขาวิชาเทคโนโลยีสารสนเทศ",
        "title_en": "Bachelor of Science Program in Information Technology",
        "degree_level": "ปริญญาตรี",
        "degree_name": "วท.บ. (เทคโนโลยีสารสนเทศ)",
        "university": "King Mongkut's University of Technology North Bangkok",
        "university_th": "มหาวิทยาลัยเทคโนโลยีพระจอมเกล้าพระนครเหนือ",
        "faculty": "Faculty of Information Technology and Digital Innovation (ITDI)",
        "faculty_th": "คณะเทคโนโลยีสารสนเทศและนวัตกรรมดิจิทัล",
        "department": "Department of Information Technology",
        "department_th": "ภาควิชาเทคโนโลยีสารสนเทศ",
        "program_type": "ภาคปกติ",
        "duration_years": "4 ปี",
        "total_credits": "130 หน่วยกิต",
        "tuition_per_semester": "20,000 บาท",
        "tuition_total": "160,000 บาท",
        "description": "เน้นการประยุกต์ใช้เทคโนโลยีสารสนเทศ การพัฒนาซอฟต์แวร์ระดับองค์กร การบริหารจัดการโครงสร้างพื้นฐานคลาวด์ และความมั่นคงปลอดภัยสารสนเทศเพื่อสนับสนุนนวัตกรรมดิจิทัล",
        "curriculum_highlights": [
            "Enterprise Web & Mobile App Development",
            "Cloud Infrastructure & System Administration",
            "Cybersecurity Management & Incident Handling",
            "Data Analytics & Business Intelligence",
            "IT Project Management & Agile Methods"
        ],
        "career_paths": [
            "Software Developer",
            "Cloud / DevOps Specialist",
            "IT Infrastructure Engineer",
            "Cybersecurity Specialist",
            "IT Business Analyst"
        ],
        "tags": ["Information Technology", "Cloud", "Cybersecurity", "ITDI", "KMUTNB", "Bachelor"],
        "website_url": "https://itdi.kmutnb.ac.th"
    },
    {
        "id": "kmutnb_itdi_dsi_msc",
        "title_th": "หลักสูตรวิทยาศาสตรมหาบัณฑิต สาขาวิชาวิทยาศาสตร์ข้อมูลเพื่อนวัตกรรม",
        "title_en": "Master of Science Program in Data Science for Innovation",
        "degree_level": "ปริญญาโท",
        "degree_name": "วท.ม. (วิทยาศาสตร์ข้อมูลเพื่อนวัตกรรม)",
        "university": "King Mongkut's University of Technology North Bangkok",
        "university_th": "มหาวิทยาลัยเทคโนโลยีพระจอมเกล้าพระนครเหนือ",
        "faculty": "Faculty of Information Technology and Digital Innovation (ITDI)",
        "faculty_th": "คณะเทคโนโลยีสารสนเทศและนวัตกรรมดิจิทัล",
        "department": "Department of Data Science for Innovation",
        "department_th": "ภาควิชาวิทยาศาสตร์ข้อมูลเพื่อนวัตกรรม",
        "program_type": "ภาคพิเศษ (วันเสาร์-อาทิตย์)",
        "duration_years": "2 ปี",
        "total_credits": "36 หน่วยกิต",
        "tuition_per_semester": "35,000 บาท",
        "tuition_total": "140,000 บาท",
        "description": "หลักสูตรปริญญาโทสำหรับผู้บริหารและผู้เชี่ยวชาญด้านข้อมูล มุ่งเน้นการวิเคราะห์ข้อมูลขนาดใหญ่ การสร้างโมเดล Machine Learning และการประยุกต์ใช้ปัญญาประดิษฐ์เพื่อสร้างนวัตกรรมทางธุรกิจและบริการภาครัฐ/เอกชน",
        "curriculum_highlights": [
            "Advanced Data Science & Machine Learning",
            "Big Data Architecture & Real-Time Analytics",
            "AI Innovation Strategy & Digital Transformation",
            "Data Governance, Privacy & Ethics (PDPA)",
            "Master Thesis / Independent Study in Data Innovation"
        ],
        "career_paths": [
            "Senior Data Scientist",
            "AI Innovation Manager",
            "Data Analytics Consultant",
            "Chief Data Officer (CDO)",
            "Business Intelligence Director"
        ],
        "tags": ["Data Science", "Innovation", "Machine Learning", "Big Data", "ITDI", "KMUTNB", "Master"],
        "website_url": "https://itdi.kmutnb.ac.th"
    }
]

def main():
    target_dir = Path(r"C:\Users\chaya\Documents\Program\Project\Teacher\backend\data\courses_new")
    target_dir.mkdir(parents=True, exist_ok=True)
    target_file = target_dir / "courses_3phrajomklao.json"
    
    # Required keys according to AGENTS.md
    required_keys = [
        "id", "title_th", "title_en", "degree_level", "degree_name",
        "university", "university_th", "faculty", "faculty_th",
        "department", "department_th", "program_type", "duration_years",
        "total_credits", "tuition_per_semester", "tuition_total",
        "description", "curriculum_highlights", "career_paths", "tags",
        "website_url"
    ]
    
    # Validate each course
    seen_ids = set()
    for idx, c in enumerate(courses):
        # Check required keys
        for k in required_keys:
            if k not in c:
                raise ValueError(f"Course #{idx} (id={c.get('id')}) missing key: {k}")
            if not c[k] and c[k] != 0:
                raise ValueError(f"Course #{idx} (id={c.get('id')}) key {k} is empty")
        
        # Check unique id
        if c["id"] in seen_ids:
            raise ValueError(f"Duplicate id: {c['id']}")
        seen_ids.add(c["id"])
        
        # Check degree_level enum
        if c["degree_level"] not in ["ปริญญาตรี", "ปริญญาโท", "ปริญญาเอก"]:
            raise ValueError(f"Invalid degree_level in {c['id']}: {c['degree_level']}")

    with open(target_file, "w", encoding="utf-8") as f:
        json.dump(courses, f, ensure_ascii=False, indent=2)

    print(f"Successfully generated {len(courses)} courses at {target_file}")
    
    # Summary stats
    by_uni = {}
    by_deg = {}
    for c in courses:
        by_uni[c["university_th"]] = by_uni.get(c["university_th"], 0) + 1
        by_deg[c["degree_level"]] = by_deg.get(c["degree_level"], 0) + 1
    
    print("\nSummary by University:")
    for u, cnt in by_uni.items():
        print(f" - {u}: {cnt} courses")
        
    print("\nSummary by Degree Level:")
    for d, cnt in by_deg.items():
        print(f" - {d}: {cnt} courses")

if __name__ == "__main__":
    main()
