import os
import sys
sys.stdout.reconfigure(encoding='utf-8')
from concurrent.futures import ThreadPoolExecutor, as_completed

# Add the parent directory to sys.path
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from app.core.database import SessionLocal
from app.models.db_models import FacultyDB
from app.core.embedding_service import embedding_service
from sqlalchemy.orm import defer, load_only

# Import datasets
from scripts.data_sources.tu_kku_faculties import TU_KKU_FACULTIES
from scripts.data_sources.psu_kmitl_kmutt_faculties import PSU_KMITL_KMUTT_FACULTIES
from scripts.data_sources.sut_swu_su_buu_faculties import SUT_SWU_SU_BUU_FACULTIES
from scripts.data_sources.batch2_faculties_expansion import BATCH2_FACULTIES
from scripts.data_sources.regional_universities_faculties import REGIONAL_UNIVERSITIES_FACULTIES
from scripts.data_sources.mfu_expanded_faculties import MFU_EXPANDED_FACULTIES
from scripts.data_sources.elite_breakthrough_faculties import ELITE_BREAKTHROUGH_FACULTIES
from scripts.data_sources.multi_disciplinary_outstanding_faculties import MULTI_DISCIPLINARY_OUTSTANDING_FACULTIES
from scripts.data_sources.new_elite_faculties_batch7 import NEW_ELITE_FACULTIES_BATCH_7
from scripts.data_sources.new_elite_faculties_batch8 import NEW_ELITE_FACULTIES_BATCH_8
from scripts.data_sources.new_elite_faculties_batch9 import NEW_ELITE_FACULTIES_BATCH_9
from scripts.data_sources.new_elite_faculties_batch10 import NEW_ELITE_FACULTIES_BATCH_10
from scripts.data_sources.new_elite_faculties_batch11_phrajomklao import PHRA_JOM_KLAO_ELITE_BATCH_11
from scripts.data_sources.new_elite_faculties_batch12_nationwide import NEW_ELITE_FACULTIES_BATCH_12
from scripts.data_sources.new_elite_faculties_batch13_deep_expansion import NEW_ELITE_FACULTIES_BATCH_13
from scripts.data_sources.new_elite_faculties_batch14_regional_hubs import NEW_ELITE_FACULTIES_BATCH_14
from scripts.data_sources.new_elite_faculties_batch15_social_econ_policy import NEW_ELITE_FACULTIES_BATCH_15
from scripts.data_sources.new_elite_faculties_batch16_hall_of_fame import NEW_ELITE_FACULTIES_BATCH_16
from scripts.data_sources.kmitl_exhaustive_expansion import KMITL_EXHAUSTIVE_FACULTIES
from scripts.data_sources.cmu_all_faculties_completion import CMU_COMPLETION_FACULTIES
from scripts.data_sources.chula_all_faculties_completion import CHULA_COMPLETION_FACULTIES
from scripts.data_sources.mahidol_all_faculties_completion import MAHIDOL_COMPLETION_FACULTIES
from scripts.data_sources.ku_all_faculties_completion import KU_COMPLETION_FACULTIES
from scripts.data_sources.cmu_specialized_engineering_faculties import CMU_SPECIALIZED_ENGINEERING_FACULTIES
from scripts.data_sources.cmu_skill_state_extracted import EXTRACTED_FACULTIES as CMU_SKILL_STATE_FACULTIES
from scripts.data_sources.chula_cp_ai_extracted import EXTRACTED_FACULTIES as CHULA_CP_FACULTIES
from scripts.data_sources.kmutt_sit_ai_extracted import EXTRACTED_FACULTIES as KMUTT_SIT_FACULTIES
from scripts.data_sources.ku_cpe_ai_extracted import EXTRACTED_FACULTIES as KU_CPE_FACULTIES
from scripts.data_sources.kmutt_cpe_ai_extracted import EXTRACTED_FACULTIES as KMUTT_CPE_FACULTIES
from scripts.data_sources.cmu_cs_ai_extracted import EXTRACTED_FACULTIES as CMU_CS_FACULTIES
from scripts.data_sources.psu_computing_ai_extracted import EXTRACTED_FACULTIES as PSU_COMPUTING_FACULTIES
from scripts.data_sources.chula_ee_ai_extracted import EXTRACTED_FACULTIES as CHULA_EE_FACULTIES
from scripts.data_sources.ku_ee_ai_extracted import EXTRACTED_FACULTIES as KU_EE_FACULTIES
from scripts.data_sources.kmutt_jgsee_ai_extracted import EXTRACTED_FACULTIES as KMUTT_JGSEE_FACULTIES
from scripts.data_sources.kmutnb_tggs_ai_extracted import EXTRACTED_FACULTIES as KMUTNB_TGGS_FACULTIES
from scripts.data_sources.tu_tbs_ai_extracted import EXTRACTED_FACULTIES as TU_TBS_FACULTIES
from scripts.data_sources.tu_law_ai_extracted import EXTRACTED_FACULTIES as TU_LAW_FACULTIES
from scripts.data_sources.cu_sasin_ai_extracted import EXTRACTED_FACULTIES as CU_SASIN_FACULTIES
from scripts.data_sources.mu_cmmu_ai_extracted import EXTRACTED_FACULTIES as MU_CMMU_FACULTIES
from scripts.data_sources.tu_polsci_mpa_ai_extracted import EXTRACTED_FACULTIES as TU_POLSCI_FACULTIES
from scripts.data_sources.psu_fms_ai_extracted import EXTRACTED_FACULTIES as PSU_FMS_FACULTIES
from scripts.data_sources.cmu_edu_ai_extracted import EXTRACTED_FACULTIES as CMU_EDU_FACULTIES
from scripts.data_sources.kku_law_ai_extracted import EXTRACTED_FACULTIES as KKU_LAW_FACULTIES
from scripts.data_sources.cmu_law_ai_extracted import EXTRACTED_FACULTIES as CMU_LAW_FACULTIES
from scripts.data_sources.psu_law_ai_extracted import EXTRACTED_FACULTIES as PSU_LAW_FACULTIES
from scripts.data_sources.cmu_polsci_ai_extracted import EXTRACTED_FACULTIES as CMU_POLSCI_FACULTIES
from scripts.data_sources.chula_law_ai_extracted import EXTRACTED_FACULTIES as CHULA_LAW_FACULTIES
from scripts.data_sources.chula_polsci_ai_extracted import EXTRACTED_FACULTIES as CHULA_POLSCI_FACULTIES
from scripts.data_sources.ru_polsci_ai_extracted import EXTRACTED_FACULTIES as RU_POLSCI_FACULTIES
from scripts.data_sources.ru_law_ai_extracted import EXTRACTED_FACULTIES as RU_LAW_FACULTIES
from scripts.data_sources.chula_vrc_ai_extracted import EXTRACTED_FACULTIES as CHULA_VRC_FACULTIES
from scripts.data_sources.mahidol_tropmed_ai_extracted import EXTRACTED_FACULTIES as MAHIDOL_TROPMED_FACULTIES
from scripts.data_sources.mahidol_bartlab_ai_extracted import EXTRACTED_FACULTIES as MAHIDOL_BARTLAB_FACULTIES
from scripts.data_sources.siit_ai_extracted import EXTRACTED_FACULTIES as SIIT_FACULTIES
from scripts.data_sources.mahidol_science_ai_extracted import EXTRACTED_FACULTIES as MAHIDOL_SCIENCE_FACULTIES
from scripts.data_sources.chula_science_ai_extracted import EXTRACTED_FACULTIES as CHULA_SCIENCE_FACULTIES
from scripts.data_sources.mahidol_medicine_ai_extracted import EXTRACTED_FACULTIES as MAHIDOL_MEDICINE_FACULTIES
from scripts.data_sources.ku_agro_vet_ai_extracted import EXTRACTED_FACULTIES as KU_AGRO_VET_FACULTIES
from scripts.data_sources.pharmacy_ai_extracted import EXTRACTED_FACULTIES as PHARMACY_FACULTIES
from scripts.data_sources.dentistry_ai_extracted import EXTRACTED_FACULTIES as DENTISTRY_FACULTIES
from scripts.data_sources.economics_ai_extracted import EXTRACTED_FACULTIES as ECONOMICS_FACULTIES
from scripts.data_sources.public_health_ai_extracted import EXTRACTED_FACULTIES as PUBLIC_HEALTH_FACULTIES
from scripts.data_sources.allied_health_ai_extracted import EXTRACTED_FACULTIES as ALLIED_HEALTH_FACULTIES
from scripts.data_sources.architecture_arts_ai_extracted import EXTRACTED_FACULTIES as ARCHITECTURE_ARTS_FACULTIES
from scripts.data_sources.humanities_social_ai_extracted import EXTRACTED_FACULTIES as HUMANITIES_SOCIAL_FACULTIES
from scripts.data_sources.commarts_journalism_ai_extracted import EXTRACTED_FACULTIES as COMM_ARTS_JOURNALISM_FACULTIES
from scripts.data_sources.finearts_humanities_ai_extracted import EXTRACTED_FACULTIES as FINEARTS_HUMANITIES_FACULTIES
from scripts.data_sources.regional_centers_ai_extracted import EXTRACTED_FACULTIES as REGIONAL_CENTERS_FACULTIES
from scripts.data_sources.sut_science_ai_extracted import EXTRACTED_FACULTIES as SUT_SCIENCE_FACULTIES
from scripts.data_sources.regional_deep_ai_extracted import EXTRACTED_FACULTIES as REGIONAL_DEEP_FACULTIES

ALL_FACULTY_DATASETS = [
    ("มหาวิทยาลัยธรรมศาสตร์ และ มหาวิทยาลัยขอนแก่น (TU & KKU)", TU_KKU_FACULTIES),
    ("ม.สงขลานครินทร์, สจล. และ มจธ. (PSU, KMITL, KMUTT - FIBO/SIT)", PSU_KMITL_KMUTT_FACULTIES),
    ("มทส., มศว, ม.ศิลปากร และ ม.บูรพา (SUT, SWU, SU, BUU)", SUT_SWU_SU_BUU_FACULTIES),
    ("ชุดที่ 2: อาจารย์ดีเด่นแห่งชาติ ธรรมศาสตร์, ขอนแก่น, ม.อ., สจล. และ มจธ. (Batch 2 Expansion)", BATCH2_FACULTIES),
    ("ชุดที่ 3: อาจารย์และนักวิจัยมหาวิทยาลัยภูมิภาค (PSU, NU, BUU, MFU, UBU, MSU, WU, UP, TSU, MJU, SU, SWU)", REGIONAL_UNIVERSITIES_FACULTIES),
    ("ชุดที่ 4: คณาจารย์และนักวิจัยชั้นนำ มหาวิทยาลัยแม่ฟ้าหลวง (MFU Comprehensive Expansion)", MFU_EXPANDED_FACULTIES),
    ("ชุดที่ 5: นักวิทยาศาสตร์ดีเด่นแห่งชาติและระดับโลก (CU, CMU, SUT, KKU Breakthrough Leaders)", ELITE_BREAKTHROUGH_FACULTIES),
    ("ชุดที่ 6: อาจารย์ดีเด่นแห่งชาติและผู้ทรงคุณวุฒิหลากหลายสาขา (KU, TU, KKU, CU, MU Multi-Disciplinary)", MULTI_DISCIPLINARY_OUTSTANDING_FACULTIES),
    ("ชุดที่ 7: นักวิจัยดีเด่นแห่งชาติและนักวิทยาศาสตร์รางวัลสากล (Batch 7: Elite Scholars)", NEW_ELITE_FACULTIES_BATCH_7),
    ("ชุดที่ 8: นักวิจัยดีเด่นแห่งชาติและนักวิทยาศาสตร์รางวัลสากล (Batch 8: Elite Scholars)", NEW_ELITE_FACULTIES_BATCH_8),
    ("ชุดที่ 9: นักวิจัยดีเด่นแห่งชาติและนักวิทยาศาสตร์รางวัลสากล (Batch 9: Elite Scholars)", NEW_ELITE_FACULTIES_BATCH_9),
    ("ชุดที่ 10: วิศวกรรมศาสตร์ดีเด่นแห่งชาติและการพัฒนาที่ยั่งยืน (Batch 10: Engineering Elites)", NEW_ELITE_FACULTIES_BATCH_10),
    ("ชุดที่ 11: คณาจารย์และนักวิจัยดีเด่นแห่งชาติ 3 พระจอมเกล้า (Batch 11: 3 Phra Jom Klao Elites)", PHRA_JOM_KLAO_ELITE_BATCH_11),
    ("ชุดที่ 12: คณาจารย์และนักวิจัยดีเด่นระดับชาติและภูมิภาค (Batch 12: Nationwide Elite Scholars)", NEW_ELITE_FACULTIES_BATCH_12),
    ("ชุดที่ 13: คณาจารย์ 3 พระจอมเกล้า และมหาวิทยาลัยวิจัยภูมิภาคเชิงลึก (Batch 13: Deep Engineering & Science)", NEW_ELITE_FACULTIES_BATCH_13),
    ("ชุดที่ 14: คณาจารย์และนักวิจัยมหาวิทยาลัยภูมิภาคและท้องถิ่น (Batch 14: Regional Hubs - UBU, MSU, WU, UP, MJU, TSU)", NEW_ELITE_FACULTIES_BATCH_14),
    ("ชุดที่ 15: คณาจารย์และผู้เชี่ยวชาญเศรษฐศาสตร์ สังคม นโยบายสาธารณะและสันติศึกษา (Batch 15: Social, Econ & Policy)", NEW_ELITE_FACULTIES_BATCH_15),
    ("ชุดที่ 16: ปรมาจารย์และนักวิทยาศาสตร์ระดับชาติ (Batch 16: National Grand Masters & Academic Hall of Fame)", NEW_ELITE_FACULTIES_BATCH_16),
    ("ชุดที่ 17: คณาจารย์ สจล. ครบทุกสำนักวิชาและศูนย์วิจัย (Batch 17: KMITL Comprehensive Mastery)", KMITL_EXHAUSTIVE_FACULTIES),
    ("ชุดที่ 18: คณาจารย์ ม.เชียงใหม่ ครบทุกคณะและสถาบันวิจัย (Batch 18: CMU Complete Faculty Mastery)", CMU_COMPLETION_FACULTIES),
    ("ชุดที่ 19: คณาจารย์ จุฬาลงกรณ์มหาวิทยาลัย ครบทุกคณะและสถาบันวิจัย (Batch 19: CU Complete Faculty Mastery)", CHULA_COMPLETION_FACULTIES),
    ("ชุดที่ 20: คณาจารย์ มหาวิทยาลัยมหิดล ครบทุกคณะและสถาบันวิจัย (Batch 20: MU Complete Faculty Mastery)", MAHIDOL_COMPLETION_FACULTIES),
    ("ชุดที่ 21: คณาจารย์ มหาวิทยาลัยเกษตรศาสตร์ ครบทุกคณะและสถาบันวิจัย (Batch 21: KU Complete Faculty Mastery)", KU_COMPLETION_FACULTIES),
    ("ชุดที่ 22: คณาจารย์วิศวกรรมเฉพาะทางและสหวิทยาการ มช. (Batch 22: CMU Specialized & Interdisciplinary Engineering)", CMU_SPECIALIZED_ENGINEERING_FACULTIES),
    ("ชุดที่ 23: คณาจารย์วิศวกรรมศาสตร์ มช. ที่ดึงผ่าน SKILL.state Agent (Batch 23: CMU Engineering Live Scraped)", CMU_SKILL_STATE_FACULTIES),
    ("ชุดที่ 24: คณาจารย์วิศวกรรมคอมพิวเตอร์ จุฬาลงกรณ์มหาวิทยาลัย (Batch 24: Chulalongkorn Computer Engineering AI/Data)", CHULA_CP_FACULTIES),
    ("ชุดที่ 25: คณาจารย์คณะเทคโนโลยีสารสนเทศ มจธ. (Batch 25: KMUTT School of Information Technology)", KMUTT_SIT_FACULTIES),
    ("ชุดที่ 26: คณาจารย์วิศวกรรมคอมพิวเตอร์ ม.เกษตรศาสตร์ (Batch 26: Kasetsart Computer Engineering & AI)", KU_CPE_FACULTIES),
    ("ชุดที่ 27: คณาจารย์วิศวกรรมคอมพิวเตอร์ มจธ. (Batch 27: KMUTT Computer Engineering & CPS)", KMUTT_CPE_FACULTIES),
    ("ชุดที่ 28: คณาจารย์วิทยาการคอมพิวเตอร์ ม.เชียงใหม่ (Batch 28: CMU Computer Science & Data Science)", CMU_CS_FACULTIES),
    ("ชุดที่ 29: คณาจารย์วิทยาลัยการคอมพิวเตอร์ ม.สงขลานครินทร์ (Batch 29: PSU College of Computing & AI)", PSU_COMPUTING_FACULTIES),
    ("ชุดที่ 30: คณาจารย์วิศวกรรมไฟฟ้า จุฬาลงกรณ์มหาวิทยาลัย (Batch 30: Chulalongkorn Electrical Engineering)", CHULA_EE_FACULTIES),
    ("ชุดที่ 31: คณาจารย์วิศวกรรมไฟฟ้า มหาวิทยาลัยเกษตรศาสตร์ (Batch 31: Kasetsart Electrical Engineering)", KU_EE_FACULTIES),
    ("ชุดที่ 32: คณาจารย์บัณฑิตวิทยาลัยร่วมฯ JGSEE มจธ. (Batch 32: KMUTT JGSEE Energy & Environment)", KMUTT_JGSEE_FACULTIES),
    ("ชุดที่ 33: คณาจารย์บัณฑิตวิทยาลัยวิศวกรรมศาสตร์นานาชาติสิรินธร ไทย-เยอรมัน มจพ. (Batch 33: KMUTNB TGGS Engineering)", KMUTNB_TGGS_FACULTIES),
    ("ชุดที่ 34: คณาจารย์คณะพาณิชยศาสตร์และการบัญชี มหาวิทยาลัยธรรมศาสตร์ (Batch 34: Thammasat Business School - TBS)", TU_TBS_FACULTIES),
    ("ชุดที่ 35: คณาจารย์คณะนิติศาสตร์ มหาวิทยาลัยธรรมศาสตร์ (Batch 35: Thammasat Faculty of Law - LL.M.)", TU_LAW_FACULTIES),
    ("ชุดที่ 36: คณาจารย์สถาบันบัณฑิตบริหารธุรกิจ ศศินทร์ จุฬาฯ (Batch 36: Sasin School of Management - MBA)", CU_SASIN_FACULTIES),
    ("ชุดที่ 37: คณาจารย์วิทยาลัยการจัดการ มหาวิทยาลัยมหิดล (Batch 37: Mahidol CMMU Management)", MU_CMMU_FACULTIES),
    ("ชุดที่ 38: คณาจารย์คณะรัฐศาสตร์ มหาวิทยาลัยธรรมศาสตร์ (Batch 38: Thammasat Political Science & MPA)", TU_POLSCI_FACULTIES),
    ("ชุดที่ 39: คณาจารย์คณะวิทยาการจัดการ ม.สงขลานครินทร์ (Batch 39: PSU Faculty of Management Sciences - MBA/MPA)", PSU_FMS_FACULTIES),
    ("ชุดที่ 40: คณาจารย์คณะศึกษาศาสตร์ มหาวิทยาลัยเชียงใหม่ (Batch 40: CMU Faculty of Education - M.Ed.)", CMU_EDU_FACULTIES),
    ("ชุดที่ 41: คณาจารย์คณะนิติศาสตร์ มหาวิทยาลัยขอนแก่น (Batch 41: Khon Kaen Faculty of Law - LL.B./LL.M.)", KKU_LAW_FACULTIES),
    ("ชุดที่ 42: คณาจารย์คณะนิติศาสตร์ มหาวิทยาลัยเชียงใหม่ (Batch 42: CMU Faculty of Law - LL.B./LL.M.)", CMU_LAW_FACULTIES),
    ("ชุดที่ 43: คณาจารย์คณะนิติศาสตร์ มหาวิทยาลัยสงขลานครินทร์ (Batch 43: PSU Faculty of Law - LL.B./LL.M.)", PSU_LAW_FACULTIES),
    ("ชุดที่ 44: คณาจารย์คณะรัฐศาสตร์และรัฐประศาสนศาสตร์ มหาวิทยาลัยเชียงใหม่ (Batch 44: CMU Political Science & Public Admin)", CMU_POLSCI_FACULTIES),
    ("ชุดที่ 45: คณาจารย์คณะนิติศาสตร์ จุฬาลงกรณ์มหาวิทยาลัย (Batch 45: Chulalongkorn Faculty of Law)", CHULA_LAW_FACULTIES),
    ("ชุดที่ 46: คณาจารย์คณะรัฐศาสตร์ จุฬาลงกรณ์มหาวิทยาลัย (Batch 46: Chulalongkorn Faculty of Political Science)", CHULA_POLSCI_FACULTIES),
    ("ชุดที่ 47: คณาจารย์คณะรัฐศาสตร์ มหาวิทยาลัยรามคำแหง (Batch 47: Ramkhamhaeng Faculty of Political Science)", RU_POLSCI_FACULTIES),
    ("ชุดที่ 48: คณาจารย์คณะนิติศาสตร์ มหาวิทยาลัยรามคำแหง (Batch 48: Ramkhamhaeng Faculty of Law)", RU_LAW_FACULTIES),
    ("ชุดที่ 49: คณาจารย์และนักวิจัยศูนย์วิจัยวัคซีน จุฬาลงกรณ์มหาวิทยาลัย (Batch 49: Chula Vaccine Research Center - VRC)", CHULA_VRC_FACULTIES),
    ("ชุดที่ 50: คณาจารย์คณะเวชศาสตร์เขตร้อน มหาวิทยาลัยมหิดล (Batch 50: Mahidol Faculty of Tropical Medicine)", MAHIDOL_TROPMED_FACULTIES),
    ("ชุดที่ 51: คณาจารย์วิศวกรรมชีวการแพทย์และหุ่นยนต์การแพทย์ ม.มหิดล (Batch 51: Mahidol BME & BART LAB)", MAHIDOL_BARTLAB_FACULTIES),
    ("ชุดที่ 52: คณาจารย์สถาบันเทคโนโลยีนานาชาติสิรินธร ม.ธรรมศาสตร์ (Batch 52: Thammasat SIIT International Institute)", SIIT_FACULTIES),
    ("ชุดที่ 53: คณาจารย์คณะวิทยาศาสตร์ มหาวิทยาลัยมหิดล (Batch 53: Mahidol Faculty of Science)", MAHIDOL_SCIENCE_FACULTIES),
    ("ชุดที่ 54: คณาจารย์คณะวิทยาศาสตร์ จุฬาลงกรณ์มหาวิทยาลัย (Batch 54: Chulalongkorn Faculty of Science)", CHULA_SCIENCE_FACULTIES),
    ("ชุดที่ 55: คณาจารย์คณะแพทยศาสตร์ ศิริราชและรามาธิบดี ม.มหิดล (Batch 55: Mahidol Medicine Siriraj & Rama)", MAHIDOL_MEDICINE_FACULTIES),
    ("ชุดที่ 56: คณาจารย์คณะอุตสาหกรรมเกษตรและสัตวแพทยศาสตร์ มก. (Batch 56: Kasetsart Agro-Industry & Vet)", KU_AGRO_VET_FACULTIES),
    ("ชุดที่ 57: คณาจารย์คณะเภสัชศาสตร์ จุฬาฯ, มหิดล, มช. (Batch 57: Pharmacy CU, MU, CMU)", PHARMACY_FACULTIES),
    ("ชุดที่ 58: คณาจารย์คณะทันตแพทยศาสตร์ จุฬาฯ และ มหิดล (Batch 58: Dentistry CU & MU)", DENTISTRY_FACULTIES),
    ("ชุดที่ 59: คณาจารย์คณะเศรษฐศาสตร์ จุฬาฯ, ธรรมศาสตร์, เกษตรฯ (Batch 59: Economics CU, TU, KU)", ECONOMICS_FACULTIES),
    ("ชุดที่ 60: คณาจารย์คณะสาธารณสุขศาสตร์ มหิดล และ มช. (Batch 60: Public Health MU & CMU)", PUBLIC_HEALTH_FACULTIES),
    ("ชุดที่ 61: คณาจารย์คณะสหเวชศาสตร์และเทคนิคการแพทย์ จุฬาฯ และ มหิดล (Batch 61: Allied Health & MedTech CU & MU)", ALLIED_HEALTH_FACULTIES),
    ("ชุดที่ 62: คณาจารย์คณะสถาปัตยกรรมศาสตร์ จุฬาฯ, ศิลปากร, มจพ. (Batch 62: Architecture CU, SU, KMUTNB)", ARCHITECTURE_ARTS_FACULTIES),
    ("ชุดที่ 63: คณาจารย์คณะจิตวิทยา, สังคมศาสตร์, มนุษยศาสตร์ (Batch 63: Psychology & Humanities CU, CMU, TU)", HUMANITIES_SOCIAL_FACULTIES),
    ("ชุดที่ 64: คณาจารย์คณะนิเทศศาสตร์ จุฬาฯ และ วารสารศาสตร์ฯ มธ. (Batch 64: CommArts CU & Journalism TU)", COMM_ARTS_JOURNALISM_FACULTIES),
    ("ชุดที่ 65: คณาจารย์คณะจิตรกรรม ศิลปากร, วิจิตรศิลป์ มช., อักษรศาสตร์ (Batch 65: Fine Arts & Arts SU, CMU)", FINEARTS_HUMANITIES_FACULTIES),
    ("ชุดที่ 66: คณาจารย์แพทย์และวิทยาศาสตร์ ม.ภูมิภาค ขอนแก่น, ม.อ., มทส. (Batch 66: Regional Centers KKU, PSU, SUT)", REGIONAL_CENTERS_FACULTIES),
    ("ชุดที่ 67: คณาจารย์สำนักวิชาวิทยาศาสตร์ มทส. (Batch 67: SUT Institute of Science)", SUT_SCIENCE_FACULTIES),
    ("ชุดที่ 68: คณาจารย์มหาวิทยาลัยภูมิภาคเชิงลึก นเรศวร, บูรพา, ศิลปากร, มมส., วลัยลักษณ์, พะเยา, แม่โจ้, ทักษิณ, อุบลฯ (Batch 68: Regional Universities Deep Expansion)", REGIONAL_DEEP_FACULTIES),
]

def build_faculty_embedding_text(f: FacultyDB) -> str:
    # Safely format publications whether list of dicts or list of strings
    pubs_text = []
    for p in (f.featured_publications or []):
        if isinstance(p, dict):
            t = p.get("title") or ""
            v = p.get("venue") or ""
            pubs_text.append(f"{t} {v}".strip())
        else:
            pubs_text.append(str(p).strip())

    parts = [
        f"{f.first_name or ''} {f.last_name or ''}".strip(),
        f.full_name_th or "",
        f.academic_title_th or "",
        f.faculty_th or "",
        f.department_th or "",
        f.faculty or "",
        f.department or "",
        f.university_th or "",
        f.university or "",
        f.role or "",
        " ".join([str(i) for i in (f.research_interests or [])]),
        " ".join(pubs_text),
        " ".join([str(e) for e in (f.education or [])])
    ]
    return " ".join([p.strip() for p in parts if p.strip()])[:6000]

def run_faculty_ingestion():
    print("=================================================================")
    print("🚀 MASSIVE FACULTY ADVISOR INGESTION & AI EMBEDDING PIPELINE")
    print("=================================================================")

    db = SessionLocal()
    total_added = 0
    total_updated = 0
    ids_to_embed = set()

    # Pre-fetch existing IDs and whether they already have embeddings for fast in-memory lookup.
    # Egress guard: id + a boolean flag only — never ship the 768-dim vectors.
    existing_records = {
        r.id: (r.embedding is not None)
        for r in db.query(FacultyDB.id, FacultyDB.embedding).all()
    }
    print(f"📊 Loaded {len(existing_records)} existing records from database for fast indexing.")

    # Slim columns for the update path — the loop below only sets these, so
    # never ship embedding / embedding_text back from Supabase per row.
    _INGEST_UPDATE_COLUMNS = (
        FacultyDB.id,
        FacultyDB.university, FacultyDB.university_th,
        FacultyDB.faculty, FacultyDB.faculty_th,
        FacultyDB.department, FacultyDB.department_th,
        FacultyDB.academic_title_th,
        FacultyDB.first_name, FacultyDB.last_name, FacultyDB.full_name_th,
        FacultyDB.role, FacultyDB.email, FacultyDB.image_url, FacultyDB.profile_url,
        FacultyDB.education, FacultyDB.research_interests, FacultyDB.taught_courses,
        FacultyDB.featured_publications, FacultyDB.scholar_url, FacultyDB.embedding_text,
    )

    for dataset_name, dataset in ALL_FACULTY_DATASETS:
        print(f"\n👨‍🏫 กำลังประมวลผลชุดข้อมูลอาจารย์: {dataset_name} ({len(dataset)} ท่าน)...")
        added_in_set = 0
        updated_in_set = 0

        # Egress guard: one batched IN fetch per dataset (slim columns) instead
        # of N per-row .first() full-row round trips.
        dataset_ids = [item["id"] for item in dataset]
        existing_map = {
            f.id: f
            for f in db.query(FacultyDB)
            .options(load_only(*_INGEST_UPDATE_COLUMNS))
            .filter(FacultyDB.id.in_(dataset_ids))
            .all()
        }

        for item in dataset:
            fid = item["id"]
            has_embedding = existing_records.get(fid)

            filtered_data = {
                "id": item["id"],
                "university": item.get("university"),
                "university_th": item.get("university_th"),
                "faculty": item.get("faculty"),
                "faculty_th": item.get("faculty_th"),
                "department": item.get("department"),
                "department_th": item.get("department_th"),
                "academic_title_th": item.get("academic_title_th"),
                "first_name": item.get("first_name"),
                "last_name": item.get("last_name"),
                "full_name_th": item.get("full_name_th"),
                "role": item.get("role"),
                "email": item.get("email"),
                "image_url": item.get("image_url"),
                "profile_url": item.get("profile_url"),
                "education": item.get("education", []),
                "research_interests": item.get("research_interests", []),
                "taught_courses": item.get("taught_courses", []),
                "featured_publications": item.get("featured_publications", []),
                "scholar_url": item.get("scholar_url"),
                "embedding_text": ""
            }

            if fid not in existing_records:
                new_f = FacultyDB(**filtered_data)
                new_f.embedding_text = build_faculty_embedding_text(new_f)
                db.add(new_f)
                ids_to_embed.add(new_f.id)
                existing_records[fid] = False
                added_in_set += 1
                total_added += 1
            else:
                existing = existing_map.get(fid)
                if existing:
                    for k, v in filtered_data.items():
                        if k != "id":
                            setattr(existing, k, v)
                    existing.embedding_text = build_faculty_embedding_text(existing)
                    if not has_embedding:
                        ids_to_embed.add(existing.id)
                    updated_in_set += 1
                    total_updated += 1

        db.commit()
        print(f"   -> เพิ่มอาจารย์ใหม่: {added_in_set} | ปรับปรุงข้อมูล: {updated_in_set}")

    db.close()
    print(f"\n=================================================================")
    print(f"📊 สรุปการประมวลผลเบื้องต้น: เพิ่มใหม่อาจารย์ {total_added} ท่าน | ปรับปรุง {total_updated} ท่าน")
    print(f"=================================================================")

    # STEP 2: MULTI-THREADED AI VECTOR EMBEDDING (768-DIM)
    print(f"\n🧠 กำลังคำนวณและบันทึก AI Vector Embeddings สำหรับอาจารย์ {len(ids_to_embed)} ท่าน...")
    id_list = list(ids_to_embed)

    def fetch_vec(fid):
        with SessionLocal() as s:
            obj = s.query(FacultyDB).filter(FacultyDB.id == fid).first()
            if obj and obj.embedding_text:
                vec = embedding_service.get_embedding(obj.embedding_text)
                return fid, vec
        return fid, None

    CHUNK = 20
    for i in range(0, len(id_list), CHUNK):
        batch = id_list[i:i+CHUNK]
        v_map = {}
        with ThreadPoolExecutor(max_workers=min(8, len(batch))) as executor:
            futs = {executor.submit(fetch_vec, fid): fid for fid in batch}
            for fut in as_completed(futs):
                fid, vec = fut.result()
                if vec:
                    v_map[fid] = vec
        if v_map:
            with SessionLocal() as s:
                for fid, vec in v_map.items():
                    f_obj = s.query(FacultyDB).filter(FacultyDB.id == fid).first()
                    if f_obj:
                        f_obj.embedding = vec
                s.commit()
        print(f"   -> บันทึกเวกเตอร์สำเร็จ: {min(i+CHUNK, len(id_list))}/{len(id_list)}")

    print("\n=================================================================")
    print("✅ FACULTY ADVISOR INGESTION & AI EMBEDDING COMPLETED 100%!")
    print("=================================================================")

if __name__ == "__main__":
    run_faculty_ingestion()
