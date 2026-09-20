# Task 1: Research Labs Expansion

> **Priority:** 🔥 Tier 1 (Critical Gap)  
> **Target:** Expand national flagship research laboratories from 30 to 70–100 labs.

---

## 1. Problem Statement & Baseline Status
The `research_labs` table currently contains only **30 labs** nationwide, resulting in sparse representation across the lab discovery interface and search results for graduate students:
- Chulalongkorn University (CU): 4 labs
- Mahidol University (MU): 3 labs
- Chiang Mai University (CMU): 3 labs
- King Mongkut's Institute of Technology Ladkrabang (KMITL): 3 labs
- King Mongkut's University of Technology Thonburi (KMUTT): 3 labs
- Mae Fah Luang University (MFU): 2 labs
- Khon Kaen University (KKU): 2 labs
- King Mongkut's University of Technology North Bangkok (KMUTNB): 2 labs
- Thammasat University (TU): 2 labs
- Prince of Songkla University (PSU): 2 labs
- Suranaree University of Technology (SUT): 2 labs
- Kasetsart University (KU): 2 labs

---

## 2. Key Research Domains for Expansion

### Group 1: AI, Data Science, Cybersecurity & Robotics
- **FIBO (KMUTT):** Institute of Field Robotics (Field Robotics, Industrial Automation, Service Robots).
- **VISTEC:** School of Information Science and Technology (IST) - NLP, Computer Vision, Big Data Labs.
- **KMITL Robotics & AI:** Robotics and Artificial Intelligence Innovation Center, Faculty of Engineering.
- **Chulalongkorn AI / Data Science:** Smart Mobility Lab, Computational Intelligence Lab.
- **CMU Center of Excellence in AI:** Artificial Intelligence Research Center, Chiang Mai University.

### Group 2: HealthTech, Medicine, Genomics & Drug Discovery
- **Faculty of Medicine Siriraj Hospital (MU):** SiCORE (Siriraj Center of Research Excellence) — e.g. SiCORE-Allergy, SiCORE-Genomics, SiCORE-Dengue.
- **Faculty of Medicine Ramathibodi Hospital (MU):** Center for Medical Genomics & Precision Medicine.
- **Faculty of Pharmacy (CU / CMU / MU):** Biopharmaceuticals and Lanna Herbal Medicine Innovation Research Center.
- **Advanced Dentistry:** CU and MU Dental Innovation and Tissue Engineering Research Centers.

### Group 3: Energy, EV, Batteries & CleanTech
- **SUT:** Renewable Energy and Electric Vehicle Research Center (Synchrotron-related energy research).
- **KMUTT:** Clean Energy & Fuel Cell Laboratory, The Joint Graduate School of Energy and Environment (JGSEE).
- **CU:** Energy Research Institute (ERI), Advanced Battery & Supercapacitor Lab.

### Group 4: Agriculture, Food Innovation & Biotechnology
- **KU:** Rice Gene Discovery and Biotechnology Research Center, National Food Innovation Center.
- **MFU:** Tea & Coffee Institute, Cosmetic Extraction and Phytomedicine Labs.
- **PSU:** Natural Rubber Innovation Research Institute, Marine Biotechnology Lab.

---

## 3. Schema Definition for `research_labs`
The `research_labs` table structure in PostgreSQL:
```sql
CREATE TABLE public.research_labs (
    id serial PRIMARY KEY,
    name_th varchar(255) NOT NULL,
    name_en varchar(255),
    university_th varchar(255) NOT NULL,
    faculty_th varchar(255),
    department_th varchar(255),
    lead_advisor_id integer REFERENCES faculties(id),
    research_domains json,       -- e.g. ["AI", "Computer Vision", "Medical Imaging"]
    flagship_equipment json,     -- e.g. ["NVIDIA DGX H100", "Micro-CT Scanner", "Confocal Microscope"]
    open_positions json,         -- e.g. ["Master RA (Full Funding)", "PhD Candidate (1 position)"]
    contact_email varchar(255),
    website_url text,
    image_url text,
    embedding vector(768)
);
```

---

## 4. Execution Plan for Resumption
1. **Target Lab Compilation:** Compile laboratory datasets from research centers of excellence and map `lead_advisor_id` to existing faculty in `faculties` (enabling bidirectional profile linking).
2. **Generate 768-dim Embeddings:** Synthesize search text payload:
   ```python
   text_to_embed = f"{name_th} {name_en} {university_th} {faculty_th} {' '.join(research_domains)} {' '.join(flagship_equipment)}"
   ```
3. **Commit to Local PostgreSQL:** Ingest directly into the containerized database (`localhost:5432`).
4. **Verification & Semantic Search Testing:** Validate bidirectional links and semantic search recall via `/api/labs`.
