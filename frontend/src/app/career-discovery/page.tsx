"use client";

import React, { useState, useMemo } from "react";
import Link from "next/link";
import {
  Sparkles,
  ArrowRight,
  ArrowLeft,
  CheckCircle2,
  Compass,
  GraduationCap,
  Briefcase,
  Layers,
  Award,
  Zap,
  Brain,
  Target,
  RefreshCw,
  Share2,
  Copy,
  Check,
  ChevronRight,
  ExternalLink,
  BookOpen,
  Building2,
  Home as HomeIcon,
  Heart,
  TrendingUp,
  AlertCircle,
  Clock,
  Laptop,
  Palette,
  FlaskConical,
  BookMarked,
  Wrench,
  Megaphone,
  Gamepad2,
  Camera,
  Microscope,
  Coffee,
  LineChart,
  ClipboardList,
  Crown,
  Hammer,
  Building,
  HeartHandshake,
  Stethoscope,
  Code2,
  Cpu,
  Globe2,
  FileCheck2,
  ShieldCheck
} from "lucide-react";

// Master Question Item Interface
interface QuestionItem {
  id: number;
  category: string;
  type: "single" | "multi" | "likert" | "text";
  dimension: string;
  question: string;
  subtitle?: string;
  options?: { key: string; label: string; iconName?: string; desc?: string }[];
  chips?: string[]; // Quick suggestion chips for free-text
}

interface RiasecScore {
  realistic: number;
  investigative: number;
  artistic: number;
  social: number;
  enterprising: number;
  conventional: number;
}

interface CareerItem {
  title: string;
  description: string;
  match_percentage: number;
  skills: string[];
  growth_outlook: string;
}

interface RecommendedCourse {
  id: string;
  title_th: string;
  title_en?: string;
  degree_level: string;
  degree_name?: string;
  university_th: string;
  faculty_th: string;
  tuition_per_semester?: string;
  curriculum_highlights?: string[];
  website_url?: string;
  match_score?: number;
}

interface QuizResultData {
  tier: string;
  archetype_title: string;
  archetype_code: string;
  archetype_description: string;
  riasec_scores: RiasecScore;
  personality_summary: string;
  strengths: string[];
  ideal_work_environment: string;
  growth_advice: string;
  share_quote: string;
  top_careers: CareerItem[];
  recommended_courses: RecommendedCourse[];
}

const BACKEND_URL = "http://localhost:8000/api/v1";

// Helper function to render clean Lucide icons instead of emojis
function renderOptionIcon(iconName?: string) {
  const props = { size: 20, className: "text-indigo-600 flex-shrink-0" };
  switch (iconName) {
    case "code": return <Laptop {...props} />;
    case "palette": return <Palette {...props} />;
    case "flask": return <FlaskConical {...props} />;
    case "book": return <BookMarked {...props} />;
    case "wrench": return <Wrench {...props} />;
    case "megaphone": return <Megaphone {...props} />;
    case "gamepad": return <Gamepad2 {...props} />;
    case "camera": return <Camera {...props} />;
    case "microscope": return <Microscope {...props} />;
    case "coffee": return <Coffee {...props} />;
    case "chart": return <LineChart {...props} />;
    case "clipboard": return <ClipboardList {...props} />;
    case "crown": return <Crown {...props} />;
    case "hammer": return <Hammer {...props} />;
    case "building": return <Building {...props} />;
    case "heart": return <HeartHandshake {...props} />;
    case "hospital": return <Stethoscope {...props} />;
    case "tech": return <Cpu {...props} />;
    case "global": return <Globe2 {...props} />;
    default: return <Compass {...props} />;
  }
}

// 50 Questions Master Bank (Clean, No Emojis)
const MASTER_QUESTIONS: QuestionItem[] = [
  // 1-5 (Quick Tier)
  {
    id: 1,
    category: "วิชาและกิจกรรมที่ชอบ",
    type: "multi",
    dimension: "I+A+R+S+E+C",
    question: "วิชาหรือกิจกรรมไหนที่คุณทำแล้วรู้สึกสนุกและมีสมาธิมากที่สุด? (เลือกได้หลายข้อ)",
    subtitle: "เลือกสิ่งที่ตรงกับความสนใจของคุณมากที่สุด",
    options: [
      { key: "I", label: "คณิตศาสตร์ / ฟิสิกส์ / เขียนโปรแกรม", iconName: "code", desc: "ชอบตรรกะ ตัวเลข และการแก้โจทย์เชิงลึก" },
      { key: "A", label: "ศิลปะ / ดนตรี / ออกแบบและสื่อดิจิทัล", iconName: "palette", desc: "ชอบสร้างสรรค์ จินตนาการ และการสื่ออารมณ์" },
      { key: "I+R", label: "ชีววิทยา / เคมี / การทดลองในห้องปฏิบัติการ", iconName: "flask", desc: "ชอบศึกษาสิ่งมีชีวิต กระบวนการทางเคมี และธรรมชาติ" },
      { key: "S+A", label: "ภาษาต่างประเทศ / สังคมศาสตร์ / มนุษยศาสตร์", iconName: "book", desc: "ชอบการสื่อสาร ภาษา วัฒนธรรม และความเข้าใจมนุษย์" },
      { key: "R", label: "พลศึกษา / งานช่าง / การลงมือปฏิบัติจริง", iconName: "wrench", desc: "ชอบกิจกรรมภาคปฏิบัติ การลงพื้นที่ และการทดลองจริง" },
      { key: "E+S", label: "กิจกรรมผู้นำ / สภานักเรียน / การจัดโครงการ", iconName: "megaphone", desc: "ชอบการวางแผน การบริหาร และการขับเคลื่อนเป้าหมายร่วม" }
    ]
  },
  {
    id: 2,
    category: "เวลาว่างและงานอดิเรก",
    type: "single",
    dimension: "R+A+I+S+E+C",
    question: "หากมีเวลาว่างเพื่อทำกิจกรรมที่ต้องการ คุณมักจะเลือกทำสิ่งใดเป็นอันดับแรก?",
    options: [
      { key: "R", label: "ประกอบอุปกรณ์ / เล่นเกมวางกลยุทธ์ / ซ่อมแซมสิ่งของ", iconName: "gamepad" },
      { key: "A", label: "สร้างสรรค์ผลงานภาพ / ผลิตวิดีโอ / แต่งดนตรี / ถ่ายภาพ", iconName: "camera" },
      { key: "I", label: "รับชมสารคดี / ศึกษาเทคโนโลยีใหม่ / ค้นคว้าเรื่องทางวิทยาศาสตร์", iconName: "microscope" },
      { key: "S", label: "พบปะเพื่อนฝูง / ร่วมกิจกรรมเพื่อสังคม / แลกเปลี่ยนมุมมองความคิด", iconName: "coffee" },
      { key: "E", label: "วางแผนโครงการ / ศึกษาการลงทุน / ติดตามข่าวสารเศรษฐกิจและธุรกิจ", iconName: "chart" },
      { key: "C", label: "จัดระเบียบตารางชีวิต / บันทึกข้อมูลและวางแผนเป้าหมายส่วนตัว", iconName: "clipboard" }
    ]
  },
  {
    id: 3,
    category: "สไตล์การแก้ปัญหา",
    type: "single",
    dimension: "I+R+S+A",
    question: "เมื่อต้องรับมือกับปัญหาที่ซับซ้อน คุณมักใช้แนวทางใดในการจัดการ?",
    options: [
      { key: "I", label: "วิเคราะห์หาสาเหตุอย่างเป็นระบบและรวบรวมข้อมูลก่อนลงมือ", iconName: "microscope" },
      { key: "R", label: "ลงมือทดลองแก้ไขทันทีและปรับปรุงจากข้อผิดพลาดที่เกิดขึ้นจริง", iconName: "wrench" },
      { key: "S", label: "ปรึกษาผู้เชี่ยวชาญหรือคนรอบข้างเพื่อรับฟังมุมมองที่หลากหลาย", iconName: "heart" },
      { key: "A", label: "คิดค้นวิธีใหม่ที่แตกต่างและไม่ยึดติดกับกรอบเดิม", iconName: "palette" }
    ]
  },
  {
    id: 4,
    category: "วิสัยทัศน์ชีวิต (Life Vision)",
    type: "text",
    dimension: "I+S+E",
    question: "หากคุณสามารถสร้างการเปลี่ยนแปลงในสังคมได้ 1 เรื่อง คุณอยากแก้ปัญหาใดมากที่สุด?",
    subtitle: "พิมพ์คำตอบสั้นๆ หรือเลือกคีย์เวิร์ดแนะนำด้านล่าง",
    chips: [
      "การเปลี่ยนแปลงสภาพภูมิอากาศและพลังงานสะอาด",
      "การพัฒนาปัญญาประดิษฐ์ (AI) เพื่อคุณภาพชีวิตมนุษย์",
      "การยกระดับความเท่าเทียมด้านการศึกษา",
      "การพัฒนาระบบสุขภาพและชีวการแพทย์",
      "การลดความเหลื่อมล้ำทางเศรษฐกิจและการเงิน",
      "การสร้างสรรค์สื่อและศิลปวัฒนธรรมเพื่อขับเคลื่อนสังคม"
    ]
  },
  {
    id: 5,
    category: "ลักษณะเด่นของตนเอง",
    type: "text",
    dimension: "A+S+E",
    question: "หากเพื่อนสนิทต้องอธิบายลักษณะเด่นของคุณด้วยคำสำคัญ 3 คำ จะเป็นคำว่าอะไร?",
    subtitle: "เลือกคีย์เวิร์ดหรือพิมพ์ตามมุมมองของคุณ",
    chips: [
      "มีตรรกะ ละเอียดรอบคอบ คิดเป็นระบบ",
      "เข้าอกเข้าใจ รับฟัง ชอบช่วยเหลือผู้อื่น",
      "มีความคิดสร้างสรรค์ มีเอกลักษณ์ จินตนาการสูง",
      "มีความเป็นผู้นำ กล้าตัดสินใจ มีเป้าหมายชัดเจน",
      "มุ่งมั่น อดทน ลงมือทำจริง พึ่งพาได้",
      "มีระเบียบวินัย วางแผนรอบคอบ รักษามาตรฐาน"
    ]
  },

  // 6-20 (Standard Tier)
  {
    id: 6,
    category: "บทบาทในการทำงานกลุ่ม",
    type: "single",
    dimension: "E+A+R+S+C",
    question: "เมื่อต้องทำงานร่วมกันเป็นทีม บทบาทใดที่คุณทำได้ดีและเป็นธรรมชาติที่สุด?",
    options: [
      { key: "E", label: "ผู้นำทีม (Team Leader) - วางทิศทางภาพรวมและประสานงาน", iconName: "crown" },
      { key: "A", label: "ผู้ออกแบบและสร้างสรรค์ (Creative Lead) - คิดแนวคิดและนำเสนอรูปแบบ", iconName: "palette" },
      { key: "R", label: "ผู้ปฏิบัติการหลัก (Technical Doer) - ผลิตชิ้นงานและลงมือพัฒนาส่วนสำคัญ", iconName: "hammer" },
      { key: "S", label: "ผู้ประสานงานความสัมพันธ์ (Facilitator) - เชื่อมโยงและดูแลความร่วมมือในทีม", iconName: "heart" },
      { key: "C", label: "ผู้ตรวจสอบคุณภาพ (Quality Assurance) - ตรวจสอบความถูกต้องและจัดทำเอกสาร", iconName: "clipboard" }
    ]
  },
  {
    id: 7,
    category: "ความถนัดด้านตรรกะและการวิเคราะห์",
    type: "likert",
    dimension: "I",
    question: "ฉันรู้สึกมีพลังและเพลิดเพลินเมื่อได้แก้ปัญหาเชิงตรรกะ การวิเคราะห์ข้อมูล หรือการเขียนโปรแกรม"
  },
  {
    id: 8,
    category: "ความใส่ใจต่อสังคมและเพื่อนมนุษย์",
    type: "likert",
    dimension: "S",
    question: "ฉันมีความสุขอย่างแท้จริงเมื่อได้ถ่ายทอดความรู้ ให้คำปรึกษา หรือช่วยเหลือผู้อื่นให้มีชีวิตที่ดีขึ้น"
  },
  {
    id: 9,
    category: "ความคิดสร้างสรรค์และศิลปะ",
    type: "likert",
    dimension: "A",
    question: "ฉันมักคิดถึงสิ่งใหม่ๆ และปรารถนาที่จะสร้างผลงานที่มีเอกลักษณ์ทางความคิดของตนเอง"
  },
  {
    id: 10,
    category: "ความเป็นผู้นำและการแข่งขัน",
    type: "likert",
    dimension: "E",
    question: "ฉันชอบสภาพแวดล้อมที่มีการแข่งขัน กล้าตัดสินใจในสภาวะท้าทาย และชอบผลักดันโครงการให้สำเร็จ"
  },
  {
    id: 11,
    category: "ความละเอียดรอบคอบและระบบระเบียบ",
    type: "likert",
    dimension: "C",
    question: "ฉันให้ความสำคัญกับความถูกต้องแม่นยำ และชอบการจัดวางระบบงานที่มีระเบียบแบบแผนชัดเจน"
  },
  {
    id: 12,
    category: "การลงมือปฏิบัติจริง",
    type: "likert",
    dimension: "R",
    question: "ฉันเข้าใจเนื้อหาได้ดีที่สุดเมื่อได้ทดลองทำของจริง มากกว่าการรับฟังบรรยายเพียงอย่างเดียว"
  },
  {
    id: 13,
    category: "ภาพอนาคตในการประกอบวิชาชีพ",
    type: "single",
    dimension: "E+I+S+A+C",
    question: "ในระยะยาว รูปแบบการทำงานลักษณะใดที่สอดคล้องกับความสุขของคุณมากที่สุด?",
    options: [
      { key: "E", label: "การเป็นผู้บริหาร ผู้ประกอบการ หรือผู้ขับเคลื่อนองค์กรทางธุรกิจ", iconName: "building" },
      { key: "I", label: "การเป็นนักวิจัย นักวิชาการ หรือผู้เชี่ยวชาญด้านวิทยาการและนวัตกรรม", iconName: "microscope" },
      { key: "S", label: "การทำงานในสายงานสุขภาพ การศึกษา หรือการพัฒนาสังคมและชุมชน", iconName: "hospital" },
      { key: "A", label: "การทำงานด้านการออกแบบ สื่อสารสร้างสรรค์ หรืออุตสาหกรรมคอนเทนต์", iconName: "palette" },
      { key: "C", label: "การทำงานในหน่วยงานที่มีโครงสร้างมั่นคง มีระบบบริหารจัดการที่เป็นมาตรฐาน", iconName: "clipboard" }
    ]
  },
  {
    id: 14,
    category: "ทักษะการสื่อสารและการนำเสนอ",
    type: "likert",
    dimension: "E+S",
    question: "ฉันมีความมั่นใจในการพูดต่อหน้าผู้ฟังจำนวนมาก และชอบการอธิบายเพื่อสร้างความเข้าใจ"
  },
  {
    id: 15,
    category: "ความสนใจด้านเทคโนโลยีขั้นสูง",
    type: "likert",
    dimension: "I+R",
    question: "ฉันสนใจติดตามการพัฒนาของ AI ระบบอัตโนมัติ และสถาปัตยกรรมดิจิทัลแห่งอนาคต"
  },
  {
    id: 16,
    category: "ลักษณะงานที่ไม่สอดคล้องกับตัวตน",
    type: "multi",
    dimension: "Anti",
    question: "ลักษณะงานในข้อใดที่คุณรู้สึกว่าไม่ตรงกับธรรมชาติและความถนัดของคุณมากที่สุด? (เลือกได้หลายข้อ)",
    subtitle: "การระบุสิ่งที่ไม่ถนัดจะช่วยให้ระบบคัดกรองหลักสูตรได้อย่างตรงจุดยิ่งขึ้น",
    options: [
      { key: "Anti-C", label: "งานเอกสารประจำวันที่มีขั้นตอนเคร่งครัดและไม่เปิดโอกาสให้ปรับเปลี่ยน", iconName: "clipboard" },
      { key: "Anti-E", label: "งานที่ต้องอาศัยการเจรจาต่อรอง การขาย หรือการพบปะผู้คนแปลกหน้าตลอดเวลา", iconName: "megaphone" },
      { key: "Anti-I", label: "งานที่ต้องอาศัยการคำนวณสูตรทฤษฎีซับซ้อน หรือการทำงานวิจัยเชิงลึกคนเดียว", iconName: "microscope" },
      { key: "Anti-R", label: "งานภาคสนามที่ต้องใช้แรงกายหนักหรือเผชิญสภาพแวดล้อมที่สมบุกสมบัน", iconName: "wrench" },
      { key: "Anti-S", label: "งานที่ต้องแบกรับสภาวะอารมณ์ของผู้อื่น หรือมีความรับผิดชอบต่อชีวิตมนุษย์โดยตรง", iconName: "heart" },
      { key: "Anti-A", label: "งานที่ไม่มีแบบแผนชัดเจน ต้องใช้การด้นสด และขาดความแน่นอนของกำหนดการ", iconName: "palette" }
    ]
  },
  {
    id: 17,
    category: "ค่านิยมหลักในการประกอบอาชีพ",
    type: "single",
    dimension: "Values",
    question: "ปัจจัยใดที่มีน้ำหนักสำคัญที่สุดในการตัดสินใจเลือกเส้นทางอาชีพของคุณ?",
    options: [
      { key: "Money", label: "ผลตอบแทนทางการเงินระดับสูงและความมั่นคงทางเศรษฐกิจ", iconName: "chart" },
      { key: "Meaning", label: "คุณค่าของงานที่สร้างผลกระทบเชิงบวกต่อสังคมและผู้คน", iconName: "heart" },
      { key: "Freedom", label: "ความยืดหยุ่นในการจัดสรรเวลาชีวิตและอิสรภาพในการทำงาน", iconName: "global" },
      { key: "Mastery", label: "โอกาสในการพัฒนาสู่ความเป็นเลิศและผู้เชี่ยวชาญระดับแนวหน้า", iconName: "crown" }
    ]
  },
  {
    id: 18,
    category: "บุคคลต้นแบบในการทำงาน",
    type: "text",
    dimension: "E+I+A",
    question: "มีบุคคลต้นแบบหรือนักวิชาชีพท่านใดที่คุณชื่นชมเป็นพิเศษหรือไม่ เพราะเหตุใด?",
    subtitle: "ระบุชื่อหรือแตะเลือกแนวคิดที่สอดคล้องกับคุณ",
    chips: [
      "ผู้สร้างนวัตกรรมเทคโนโลยีระดับโลกที่เปลี่ยนวิถีชีวิตผู้คน",
      "นักออกแบบและผู้สร้างสรรค์สื่อที่ผสานศิลปะเข้ากับเทคโนโลยี",
      "บุคลากรทางการแพทย์และสาธารณสุขผู้อุทิศตนเพื่อสังคม",
      "ครูอาจารย์และนักวิชาการผู้ถ่ายทอดความรู้อย่างมีคุณค่า",
      "ผู้ประกอบการสตาร์ทอัพที่สร้างธุรกิจขึ้นจากความมุ่งมั่น",
      "นักวิจัยทางวิทยาศาสตร์ผู้ค้นพบองค์ความรู้ใหม่ของมนุษยชาติ"
    ]
  },
  {
    id: 19,
    category: "สาขาวิชาที่สร้างความหลงใหล",
    type: "text",
    dimension: "I+A",
    question: "หัวข้อหรือประเด็นทางวิชาการใดที่คุณสามารถศึกษาค้นคว้าได้อย่างต่อเนื่องโดยไม่รู้สึกเบื่อหน่าย?",
    subtitle: "หัวข้อนี้บ่งชี้ถึงศักยภาพการเรียนรู้ระยะยาวของคุณ",
    chips: [
      "วิทยาการคอมพิวเตอร์ ปัญญาประดิษฐ์ และระบบข้อมูล",
      "เศรษฐศาสตร์ การเงิน การลงทุน และการจัดการธุรกิจ",
      "จิตวิทยา พฤติกรรมศาสตร์ และการพัฒนาศักยภาพมนุษย์",
      "วิทยาศาสตร์สุขภาพ การแพทย์ ชีวโมเลกุล และพันธุศาสตร์",
      "สถาปัตยกรรม ศิลปกรรม แอนิเมชัน และการออกแบบสื่อ",
      "ฟิสิกส์ ดาราศาสตร์ วิศวกรรมศาสตร์ และระบบพลังงานสะอาด"
    ]
  },
  {
    id: 20,
    category: "เป้าหมายและความกังวลในการศึกษาต่อ",
    type: "text",
    dimension: "PainPoint",
    question: "ความกังวลสำคัญที่สุดของคุณในการเลือกศึกษาต่อระดับอุดมศึกษาคือเรื่องใด?",
    chips: [
      "ความกังวลเรื่องความเข้ากันได้กับสาขาวิชาที่เลือกในระยะยาว",
      "แนวโน้มการเปลี่ยนแปลงของตลาดแรงงานและทักษะในยุค AI",
      "การปรับสมดุลระหว่างความชอบส่วนตัวกับความคาดหวังของครอบครัว",
      "การเตรียมตัวด้านพอร์ตโฟลิโอและการสอบคัดเลือก",
      "การสร้างความมั่นใจในศักยภาพและความถนัดเฉพาะทางของตนเอง"
    ]
  },

  // 21-30 (Deep Dive Sample)
  {
    id: 21,
    category: "สภาพแวดล้อมการทำงาน",
    type: "likert",
    dimension: "S",
    question: "ฉันมีสมาธิและประสิทธิภาพสูงสุดเมื่อได้ร่วมแลกเปลี่ยนความคิดเห็นกับทีมงานที่มีความหลากหลาย"
  },
  {
    id: 22,
    category: "การเปิดรับประสบการณ์สากล",
    type: "likert",
    dimension: "E",
    question: "ฉันต้องการประกอบวิชาชีพในสภาพแวดล้อมสากลที่มีโอกาสเดินทางหรือร่วมงานกับต่างประเทศ"
  },
  {
    id: 23,
    category: "โครงสร้างเวลาการทำงาน",
    type: "likert",
    dimension: "C",
    question: "ฉันทำงานได้ดีกว่าเมื่อมีกรอบเวลาและเป้าหมายที่ชัดเจน มากกว่าการทำงานแบบไร้กำหนดการ"
  },
  {
    id: 24,
    category: "สถานที่ทำงานในอุดมคติ",
    type: "single",
    dimension: "Env",
    question: "สภาพแวดล้อมทางกายภาพแบบใดที่ช่วยส่งเสริมให้คุณสร้างสรรค์ผลงานได้ดีที่สุด?",
    options: [
      { key: "I+E", label: "ศูนย์นวัตกรรมและเทคโนโลยีทันสมัย (Modern Tech Hub)", iconName: "tech" },
      { key: "I+R", label: "ห้องปฏิบัติการวิจัย สถาบันวิทยาศาสตร์ หรือโรงพยาบาลชั้นนำ", iconName: "microscope" },
      { key: "A", label: "สตูดิโอสร้างสรรค์ สเปซทางศิลปะ หรือสภาพแวดล้อมที่สงบ", iconName: "palette" },
      { key: "R", label: "พื้นที่ภาคสนาม โครงการพัฒนา หรือไซต์งานวิศวกรรม", iconName: "wrench" },
      { key: "DigitalNomad", label: "การทำงานระยะไกลแบบยืดหยุ่นผ่านระบบดิจิทัล (Remote Work)", iconName: "code" }
    ]
  },
  {
    id: 25,
    category: "ความทนทานต่อสภาวะกดดัน",
    type: "likert",
    dimension: "Stress",
    question: "ฉันสามารถจัดลำดับความสำคัญและควบคุมสมาธิได้ดีเมื่อต้องเผชิญกำหนดส่งงานที่กระชั้นชิด"
  },
  {
    id: 26,
    category: "การเรียนรู้เชิงรุก",
    type: "likert",
    dimension: "I",
    question: "ฉันชอบค้นคว้าหาคำตอบด้วยตนเองจากแหล่งข้อมูลสากลก่อนที่จะสอบถามผู้อื่น"
  },
  {
    id: 27,
    category: "วิสัยทัศน์ผู้ประกอบการ",
    type: "likert",
    dimension: "E",
    question: "ฉันมักมองเห็นโอกาสในการสร้างคุณค่าและพัฒนาบริการใหม่ๆ จากสิ่งรอบตัว"
  },
  {
    id: 28,
    category: "ความพร้อมด้านภาษาต่างประเทศ",
    type: "likert",
    dimension: "Global",
    question: "ฉันมีความสนใจที่จะศึกษาในหลักสูตรนานาชาติหรือใช้ภาษาอังกฤษเป็นเครื่องมือหลักในการเรียนรู้"
  },
  {
    id: 29,
    category: "การคิดเชิงกลยุทธ์ระยะยาว",
    type: "likert",
    dimension: "I+E",
    question: "ฉันชอบการวางแผนระยะยาวและการวิเคราะห์ผลกระทบที่จะเกิดขึ้นในอนาคต"
  },
  {
    id: 30,
    category: "ความฉลาดทางอารมณ์และความเข้าอกเข้าใจ",
    type: "likert",
    dimension: "S",
    question: "ฉันสามารถรับรู้ความรู้สึกและความต้องการของผู้อื่นได้อย่างรวดเร็วและเหมาะสม"
  }
];

// Clean Minimal SVG Radar Chart Component for Light Theme
function RiasecRadarChart({ scores }: { scores: RiasecScore }) {
  const size = 320;
  const center = size / 2;
  const radius = 105;

  const traits = [
    { key: "realistic", label: "นักปฏิบัติ (R)", code: "R", color: "#ea580c" },
    { key: "investigative", label: "นักสืบค้น (I)", code: "I", color: "#2563eb" },
    { key: "artistic", label: "นักสร้างสรรค์ (A)", code: "A", color: "#db2777" },
    { key: "social", label: "นักสังคม (S)", code: "S", color: "#059669" },
    { key: "enterprising", label: "นักบริหาร (E)", code: "E", color: "#7c3aed" },
    { key: "conventional", label: "นักจัดระเบียบ (C)", code: "C", color: "#0891b2" }
  ];

  const totalAxes = traits.length;
  const angleStep = (Math.PI * 2) / totalAxes;

  // Calculate polygon points
  const points = traits.map((trait, index) => {
    const angle = index * angleStep - Math.PI / 2;
    const value = (scores as any)[trait.key] || 40;
    const r = (value / 100) * radius;
    const x = center + r * Math.cos(angle);
    const y = center + r * Math.sin(angle);
    return `${x},${y}`;
  }).join(" ");

  const webRings = [0.25, 0.5, 0.75, 1.0];

  return (
    <div className="flex flex-col items-center justify-center p-6 bg-white rounded-3xl text-slate-800 shadow-sm border border-slate-200 relative overflow-hidden">
      <div className="w-full flex items-center justify-between mb-2">
        <div className="flex items-center gap-2 text-xs font-bold text-slate-700">
          <ShieldCheck size={16} className="text-indigo-600" />
          <span>Holland RIASEC Profile</span>
        </div>
        <span className="text-[11px] font-mono text-slate-600 bg-slate-100 px-2.5 py-0.5 rounded-full border border-slate-200">
          Standardized Metric
        </span>
      </div>

      <svg width={size} height={size} className="overflow-visible my-2">
        {/* Background Grid Rings (Light Gray) */}
        {webRings.map((scale, i) => {
          const ringPoints = traits.map((_, index) => {
            const angle = index * angleStep - Math.PI / 2;
            const r = scale * radius;
            const x = center + r * Math.cos(angle);
            const y = center + r * Math.sin(angle);
            return `${x},${y}`;
          }).join(" ");
          return (
            <polygon
              key={i}
              points={ringPoints}
              fill="none"
              stroke="#e2e8f0"
              strokeWidth="1"
              strokeDasharray={scale === 1 ? "none" : "3,3"}
            />
          );
        })}

        {/* Radial Axis Lines */}
        {traits.map((_, index) => {
          const angle = index * angleStep - Math.PI / 2;
          const x = center + radius * Math.cos(angle);
          const y = center + radius * Math.sin(angle);
          return <line key={index} x1={center} y1={center} x2={x} y2={y} stroke="#e2e8f0" strokeWidth="1" />;
        })}

        {/* Value Polygon with Light Gradient Fill */}
        <polygon
          points={points}
          fill="url(#radarGradientLight)"
          fillOpacity="0.35"
          stroke="#4f46e5"
          strokeWidth="2.5"
          className="transition-all duration-700 ease-out"
        />

        <defs>
          <linearGradient id="radarGradientLight" x1="0%" y1="0%" x2="100%" y2="100%">
            <stop offset="0%" stopColor="#3b82f6" stopOpacity="0.6" />
            <stop offset="50%" stopColor="#6366f1" stopOpacity="0.6" />
            <stop offset="100%" stopColor="#ec4899" stopOpacity="0.6" />
          </linearGradient>
        </defs>

        {/* Data Nodes & Labels */}
        {traits.map((trait, index) => {
          const angle = index * angleStep - Math.PI / 2;
          const value = (scores as any)[trait.key] || 40;
          const nodeR = (value / 100) * radius;
          const nodeX = center + nodeR * Math.cos(angle);
          const nodeY = center + nodeR * Math.sin(angle);

          const labelR = radius + 22;
          const labelX = center + labelR * Math.cos(angle);
          const labelY = center + labelR * Math.sin(angle);

          return (
            <g key={index}>
              <circle cx={nodeX} cy={nodeY} r="4.5" fill={trait.color} stroke="#ffffff" strokeWidth="2" />
              <text
                x={labelX}
                y={labelY + 4}
                textAnchor="middle"
                fontSize="10.5"
                fontWeight="700"
                fill={trait.color}
                className="select-none font-sans"
              >
                {trait.code}: {Math.round(value)}%
              </text>
            </g>
          );
        })}
      </svg>

      {/* Trait Legend Badges */}
      <div className="grid grid-cols-3 gap-2 w-full mt-2 pt-3 border-t border-slate-100 text-[11px]">
        {traits.map((t, idx) => (
          <div key={idx} className="flex items-center gap-1.5 bg-slate-50 border border-slate-150 px-2.5 py-1 rounded-lg">
            <span className="w-2 h-2 rounded-full flex-shrink-0" style={{ backgroundColor: t.color }}></span>
            <span className="text-slate-700 font-medium truncate">{t.label}</span>
          </div>
        ))}
      </div>
    </div>
  );
}

export default function CareerDiscoveryPage() {
  const [tier, setTier] = useState<"quick" | "standard" | "deep" | null>(null);
  const [currentStep, setCurrentStep] = useState(0);
  const [answers, setAnswers] = useState<Record<number, any>>({});
  const [freeTextAnswers, setFreeTextAnswers] = useState<Record<string, string>>({});
  const [isSubmitting, setIsSubmitting] = useState(false);
  const [result, setResult] = useState<QuizResultData | null>(null);
  const [error, setError] = useState<string | null>(null);
  const [copied, setCopied] = useState(false);

  // Filter questions based on chosen Tier
  const activeQuestions = useMemo(() => {
    if (!tier) return [];
    if (tier === "quick") return MASTER_QUESTIONS.slice(0, 5);
    if (tier === "standard") return MASTER_QUESTIONS.slice(0, 20);
    return MASTER_QUESTIONS;
  }, [tier]);

  const currentQ = activeQuestions[currentStep];
  const progressPct = activeQuestions.length > 0 ? Math.round(((currentStep + 1) / activeQuestions.length) * 100) : 0;

  const handleSelectOption = (questionId: number, value: any, isMulti: boolean = false) => {
    if (isMulti) {
      const currentList: string[] = answers[questionId] || [];
      if (currentList.includes(value)) {
        setAnswers({ ...answers, [questionId]: currentList.filter((item) => item !== value) });
      } else {
        setAnswers({ ...answers, [questionId]: [...currentList, value] });
      }
    } else {
      setAnswers({ ...answers, [questionId]: value });
    }
  };

  const handleFreeTextChange = (questionId: number, text: string) => {
    setAnswers({ ...answers, [questionId]: text });
    setFreeTextAnswers({ ...freeTextAnswers, [`q${questionId}`]: text });
  };

  const handleChipClick = (questionId: number, chipText: string) => {
    const existing = answers[questionId] || "";
    const updated = existing ? `${existing}, ${chipText}` : chipText;
    handleFreeTextChange(questionId, updated);
  };

  const handleNext = () => {
    if (currentStep < activeQuestions.length - 1) {
      setCurrentStep(currentStep + 1);
    } else {
      handleSubmit();
    }
  };

  const handlePrev = () => {
    if (currentStep > 0) {
      setCurrentStep(currentStep - 1);
    }
  };

  const handleSubmit = async () => {
    setIsSubmitting(true);
    setError(null);

    const formattedAnswers = activeQuestions.map((q) => ({
      question_id: q.id,
      dimension: q.dimension,
      value: answers[q.id] ?? (q.type === "likert" ? 3 : ""),
      text: q.type === "text" ? answers[q.id] || "" : undefined
    }));

    try {
      const res = await fetch(`${BACKEND_URL}/career-quiz/analyze`, {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify({
          tier: tier || "standard",
          answers: formattedAnswers,
          free_text_answers: freeTextAnswers
        })
      });

      if (!res.ok) {
        throw new Error("ไม่สามารถวิเคราะห์ผลลัพธ์ได้ กรุณาลองใหม่อีกครั้ง");
      }

      const data = await res.json();
      setResult(data);
    } catch (err: any) {
      setError(err.message || "เกิดข้อผิดพลาดในการเชื่อมต่อเซิร์ฟเวอร์");
    } finally {
      setIsSubmitting(false);
    }
  };

  const copyShareResult = () => {
    if (!result) return;
    const text = `ผลวิเคราะห์ความถนัดทางการศึกษาและอาชีพ โดย AI Thai EduCenter:\n- บุคลิกภาพเด่น: ${result.archetype_title} (Holland Code: ${result.archetype_code})\n- คำนิยาม: "${result.share_quote}"\n\nเข้าทำแบบประเมินและค้นหาหลักสูตรมหาวิทยาลัยได้ที่: ${window.location.href}`;
    navigator.clipboard.writeText(text);
    setCopied(true);
    setTimeout(() => setCopied(false), 2500);
  };

  const resetQuiz = () => {
    setTier(null);
    setCurrentStep(0);
    setAnswers({});
    setFreeTextAnswers({});
    setResult(null);
    setError(null);
  };

  return (
    <div className="min-h-screen bg-slate-50 text-slate-800 flex flex-col selection:bg-indigo-500 selection:text-white">
      {/* Top Navbar */}
      <header className="border-b border-slate-200 bg-white/90 backdrop-blur-md sticky top-0 z-50">
        <div className="max-w-6xl mx-auto px-4 sm:px-6 h-16 flex items-center justify-between">
          <Link href="/" className="flex items-center gap-2.5 text-slate-900 hover:text-indigo-600 transition">
            <div className="w-9 h-9 rounded-xl bg-gradient-to-tr from-indigo-600 to-blue-600 flex items-center justify-center text-white shadow-md shadow-indigo-500/20">
              <GraduationCap size={19} />
            </div>
            <div>
              <span className="font-black text-lg tracking-tight text-slate-900">Thai EduCenter</span>
              <span className="hidden sm:inline-block text-[10px] font-bold uppercase tracking-wider bg-indigo-50 text-indigo-700 px-2 py-0.5 rounded-full ml-2 border border-indigo-100">
                Career Profiler
              </span>
            </div>
          </Link>

          <div className="flex items-center gap-3">
            <Link
              href="/"
              className="text-xs font-semibold text-slate-600 hover:text-slate-900 transition flex items-center gap-1.5 bg-white px-3.5 py-1.5 rounded-xl border border-slate-200 shadow-xs"
            >
              <HomeIcon size={14} />
              <span>กลับหน้าหลัก</span>
            </Link>
          </div>
        </div>
      </header>

      {/* Main Content Area */}
      <main className="flex-1 max-w-4xl mx-auto w-full px-4 sm:px-6 py-8 sm:py-12 flex flex-col justify-center">
        {/* VIEW 1: Tier Selection Mode */}
        {!tier && !result && (
          <div className="text-center animate-fadeIn">
            <div className="inline-flex items-center gap-2 bg-indigo-50 border border-indigo-200 text-indigo-800 px-3.5 py-1 rounded-full text-xs font-semibold mb-6 shadow-xs">
              <Compass size={14} className="text-indigo-600" />
              <span>Holland RIASEC Psychometric Assessment</span>
            </div>

            <h1 className="text-3xl sm:text-5xl font-black text-slate-900 tracking-tight leading-tight mb-4">
              ค้นหา <span className="text-transparent bg-clip-text bg-gradient-to-r from-indigo-600 via-blue-600 to-sky-600">ศักยภาพ & สาขาวิชาที่ใช่</span><br />
              ด้วยระบบประเมินจิตวิทยาอาชีพ
            </h1>

            <p className="text-slate-600 text-sm sm:text-base max-w-xl mx-auto mb-10 leading-relaxed font-normal">
              แบบประเมินความถนัดทางการศึกษาและวิชาชีพ ออกแบบตามกรอบจิตวิทยามาตรฐานสากล พร้อมจับคู่กับหลักสูตรระดับปริญญาตรีของมหาวิทยาลัยชั้นนำทั่วประเทศ
            </p>

            {/* 3 Tier Selection Cards */}
            <div className="grid grid-cols-1 md:grid-cols-3 gap-5 text-left mb-8">
              {/* Quick Tier */}
              <button
                onClick={() => {
                  setTier("quick");
                  setCurrentStep(0);
                }}
                className="group bg-white hover:bg-slate-50/80 p-6 rounded-3xl border border-slate-200 hover:border-amber-400 transition-all shadow-sm hover:shadow-md flex flex-col justify-between"
              >
                <div>
                  <div className="w-11 h-11 rounded-2xl bg-amber-50 text-amber-600 flex items-center justify-center mb-4 group-hover:scale-105 transition-transform border border-amber-100">
                    <Zap size={22} />
                  </div>
                  <div className="flex items-center gap-2 mb-1">
                    <span className="text-xs font-bold uppercase tracking-wider text-amber-600">ระดับเร่งด่วน</span>
                    <span className="text-[10px] bg-slate-100 text-slate-600 px-2 py-0.5 rounded-full flex items-center gap-1">
                      <Clock size={10} /> 1 นาที
                    </span>
                  </div>
                  <h3 className="text-xl font-bold text-slate-900 mb-2">Quick Scan</h3>
                  <p className="text-xs text-slate-500 leading-relaxed mb-4">
                    5 คำถามสำคัญ เพื่อประเมินแนวโน้มความถนัดและภาพรวมในเบื้องต้น
                  </p>
                </div>
                <div className="flex items-center text-xs font-bold text-amber-600 group-hover:translate-x-1 transition-transform">
                  <span>เริ่มทำแบบประเมิน</span> <ChevronRight size={14} className="ml-1" />
                </div>
              </button>

              {/* Standard Tier (Recommended) */}
              <button
                onClick={() => {
                  setTier("standard");
                  setCurrentStep(0);
                }}
                className="group bg-gradient-to-b from-indigo-50/70 via-white to-white p-6 rounded-3xl border-2 border-indigo-500 hover:border-indigo-600 transition-all shadow-md hover:shadow-lg flex flex-col justify-between relative overflow-hidden scale-[1.02]"
              >
                <div className="absolute top-3 right-3 bg-indigo-600 text-white font-bold text-[10px] uppercase tracking-wider px-2.5 py-0.5 rounded-full">
                  แนะนำ
                </div>
                <div>
                  <div className="w-11 h-11 rounded-2xl bg-indigo-100 text-indigo-600 flex items-center justify-center mb-4 group-hover:scale-105 transition-transform border border-indigo-200">
                    <Target size={22} />
                  </div>
                  <div className="flex items-center gap-2 mb-1">
                    <span className="text-xs font-bold uppercase tracking-wider text-indigo-700">ระดับมาตรฐาน</span>
                    <span className="text-[10px] bg-indigo-100 text-indigo-800 px-2 py-0.5 rounded-full flex items-center gap-1 font-medium">
                      <Clock size={10} /> 4 นาที
                    </span>
                  </div>
                  <h3 className="text-xl font-bold text-slate-900 mb-2">Standard Match</h3>
                  <p className="text-xs text-slate-600 leading-relaxed mb-4">
                    20 คำถามครอบคลุมทั้งทักษะเฉพาะด้าน ความคิดสร้างสรรค์ และค่านิยมในการทำงาน
                  </p>
                </div>
                <div className="flex items-center text-xs font-bold text-indigo-600 group-hover:translate-x-1 transition-transform">
                  <span>เริ่มทำแบบประเมิน</span> <ChevronRight size={14} className="ml-1" />
                </div>
              </button>

              {/* Deep Dive Tier */}
              <button
                onClick={() => {
                  setTier("deep");
                  setCurrentStep(0);
                }}
                className="group bg-white hover:bg-slate-50/80 p-6 rounded-3xl border border-slate-200 hover:border-pink-400 transition-all shadow-sm hover:shadow-md flex flex-col justify-between"
              >
                <div>
                  <div className="w-11 h-11 rounded-2xl bg-pink-50 text-pink-600 flex items-center justify-center mb-4 group-hover:scale-105 transition-transform border border-pink-100">
                    <Brain size={22} />
                  </div>
                  <div className="flex items-center gap-2 mb-1">
                    <span className="text-xs font-bold uppercase tracking-wider text-pink-600">ระดับเจาะลึก</span>
                    <span className="text-[10px] bg-slate-100 text-slate-600 px-2 py-0.5 rounded-full flex items-center gap-1">
                      <Clock size={10} /> 10 นาที
                    </span>
                  </div>
                  <h3 className="text-xl font-bold text-slate-900 mb-2">Deep Dive DNA</h3>
                  <p className="text-xs text-slate-500 leading-relaxed mb-4">
                    30 คำถามเชิงลึก วิเคราะห์สภาวะการทำงาน การรับมือแรงกดดัน และเป้าหมายระยะยาว
                  </p>
                </div>
                <div className="flex items-center text-xs font-bold text-pink-600 group-hover:translate-x-1 transition-transform">
                  <span>เริ่มทำแบบประเมิน</span> <ChevronRight size={14} className="ml-1" />
                </div>
              </button>
            </div>

            <div className="text-xs text-slate-500 flex items-center justify-center gap-4">
              <span className="flex items-center gap-1"><ShieldCheck size={14} className="text-emerald-600" /> ผลการประเมินเพื่อการแนะแนวการศึกษา</span>
              <span>•</span>
              <span className="flex items-center gap-1"><Cpu size={14} className="text-indigo-600" /> วิเคราะห์ผ่าน AI Semantic Mapping</span>
            </div>
          </div>
        )}

        {/* VIEW 2: Submitting / Loading Screen */}
        {isSubmitting && (
          <div className="text-center py-20 animate-fadeIn">
            <div className="relative w-16 h-16 mx-auto mb-6">
              <div className="w-16 h-16 rounded-2xl bg-indigo-50 border border-indigo-200 flex items-center justify-center text-indigo-600 shadow-md animate-pulse">
                <Sparkles size={28} />
              </div>
            </div>
            <h2 className="text-2xl font-black text-slate-900 mb-2">ระบบกำลังประมวลผลข้อมูลความถนัด...</h2>
            <p className="text-sm text-slate-600 max-w-md mx-auto">
              กำลังคำนวณสัดส่วนคะแนน RIASEC และประมวลผลความสอดคล้องกับหลักสูตรมหาวิทยาลัยในฐานข้อมูล
            </p>
          </div>
        )}

        {/* VIEW 3: Step-by-Step Question Interface */}
        {tier && !result && !isSubmitting && currentQ && (
          <div className="max-w-2xl mx-auto w-full animate-fadeIn">
            {/* Progress Bar & Header */}
            <div className="mb-6">
              <div className="flex justify-between items-center text-xs font-semibold text-slate-500 mb-2">
                <span className="flex items-center gap-1.5 text-indigo-600 font-bold">
                  <Compass size={14} />
                  <span>{currentQ.category}</span>
                </span>
                <span className="font-mono text-slate-500">
                  ข้อ {currentStep + 1} / {activeQuestions.length} ({progressPct}%)
                </span>
              </div>
              <div className="w-full bg-slate-200 h-2 rounded-full overflow-hidden">
                <div
                  className="bg-gradient-to-r from-blue-600 via-indigo-600 to-sky-600 h-full rounded-full transition-all duration-300"
                  style={{ width: `${progressPct}%` }}
                ></div>
              </div>
            </div>

            {/* Question Card */}
            <div className="bg-white border border-slate-200 rounded-3xl p-6 sm:p-8 shadow-sm backdrop-blur-md mb-6">
              <span className="inline-block bg-slate-100 text-slate-600 text-[11px] font-mono font-bold px-3 py-1 rounded-full mb-3 border border-slate-200">
                Item {currentStep + 1}
              </span>

              <h2 className="text-xl sm:text-2xl font-bold text-slate-900 leading-snug mb-2">
                {currentQ.question}
              </h2>

              {currentQ.subtitle && (
                <p className="text-xs sm:text-sm text-slate-500 mb-6">{currentQ.subtitle}</p>
              )}

              {/* INPUT TYPE 1: Single Choice / Multi Choice */}
              {(currentQ.type === "single" || currentQ.type === "multi") && currentQ.options && (
                <div className="space-y-3 mt-4">
                  {currentQ.options.map((opt) => {
                    const isSelected =
                      currentQ.type === "multi"
                        ? (answers[currentQ.id] || []).includes(opt.key)
                        : answers[currentQ.id] === opt.key;

                    return (
                      <button
                        key={opt.key}
                        type="button"
                        onClick={() => handleSelectOption(currentQ.id, opt.key, currentQ.type === "multi")}
                        className={`w-full text-left p-4 rounded-2xl border transition-all flex items-center justify-between ${
                          isSelected
                            ? "bg-indigo-50/80 border-indigo-500 text-indigo-950 shadow-xs"
                            : "bg-slate-50/60 border-slate-200 text-slate-700 hover:border-slate-300 hover:bg-slate-50"
                        }`}
                      >
                        <div className="flex items-center gap-3">
                          {renderOptionIcon(opt.iconName)}
                          <div>
                            <div className="font-bold text-sm sm:text-base text-slate-900">{opt.label}</div>
                            {opt.desc && <div className="text-xs text-slate-500 mt-0.5">{opt.desc}</div>}
                          </div>
                        </div>
                        <div
                          className={`w-5 h-5 rounded-full flex items-center justify-center border flex-shrink-0 ${
                            isSelected ? "bg-indigo-600 border-indigo-600 text-white" : "border-slate-300 bg-white"
                          }`}
                        >
                          {isSelected && <Check size={12} strokeWidth={3} />}
                        </div>
                      </button>
                    );
                  })}
                </div>
              )}

              {/* INPUT TYPE 2: Likert 5-point Psychometric Scale */}
              {currentQ.type === "likert" && (
                <div className="mt-8">
                  <div className="grid grid-cols-5 gap-2 sm:gap-3">
                    {[
                      { val: 1, label: "ไม่เห็นด้วยอย่างยิ่ง", num: "1" },
                      { val: 2, label: "ไม่เห็นด้วย", num: "2" },
                      { val: 3, label: "ปานกลาง", num: "3" },
                      { val: 4, label: "เห็นด้วย", num: "4" },
                      { val: 5, label: "เห็นด้วยอย่างยิ่ง", num: "5" }
                    ].map((item) => {
                      const isSelected = answers[currentQ.id] === item.val;
                      return (
                        <button
                          key={item.val}
                          type="button"
                          onClick={() => handleSelectOption(currentQ.id, item.val, false)}
                          className={`p-3 sm:p-4 rounded-2xl border text-center transition-all flex flex-col items-center justify-between ${
                            isSelected
                              ? "bg-indigo-600 border-indigo-600 text-white shadow-md scale-105"
                              : "bg-slate-50 border-slate-200 text-slate-600 hover:border-slate-300 hover:bg-slate-100"
                          }`}
                        >
                          <span className={`w-8 h-8 rounded-full flex items-center justify-center font-bold text-sm mb-2 border ${
                            isSelected ? "bg-white text-indigo-900 border-white" : "bg-white text-slate-700 border-slate-200"
                          }`}>
                            {item.num}
                          </span>
                          <span className={`text-[10px] sm:text-xs font-semibold leading-tight line-clamp-2 ${
                            isSelected ? "text-white" : "text-slate-700"
                          }`}>
                            {item.label}
                          </span>
                        </button>
                      );
                    })}
                  </div>
                  <div className="flex justify-between text-[11px] text-slate-500 mt-4 px-1 font-medium">
                    <span>ระดับ 1 : ไม่ตรงกับข้าพเจ้า</span>
                    <span>ระดับ 5 : ตรงกับข้าพเจ้าอย่างยิ่ง</span>
                  </div>
                </div>
              )}

              {/* INPUT TYPE 3: Free-text with Suggestion Chips */}
              {currentQ.type === "text" && (
                <div className="space-y-4 mt-4">
                  <textarea
                    rows={3}
                    value={answers[currentQ.id] || ""}
                    onChange={(e) => handleFreeTextChange(currentQ.id, e.target.value)}
                    placeholder="ระบุคำตอบหรือมุมมองของคุณ..."
                    className="w-full bg-slate-50 border border-slate-200 rounded-2xl p-4 text-sm text-slate-900 placeholder-slate-400 focus:outline-none focus:bg-white focus:border-indigo-500 focus:ring-2 focus:ring-indigo-100"
                  />

                  {currentQ.chips && currentQ.chips.length > 0 && (
                    <div>
                      <div className="text-xs font-bold text-slate-500 mb-2 flex items-center gap-1.5">
                        <FileCheck2 size={13} className="text-indigo-600" />
                        <span>หรือเลือกประเด็นที่สอดคล้อง:</span>
                      </div>
                      <div className="flex flex-wrap gap-2">
                        {currentQ.chips.map((chip, idx) => (
                          <button
                            key={idx}
                            type="button"
                            onClick={() => handleChipClick(currentQ.id, chip)}
                            className="bg-slate-100 hover:bg-indigo-50 hover:border-indigo-200 text-slate-700 hover:text-indigo-900 border border-slate-200 text-xs px-3 py-1.5 rounded-xl transition font-medium text-left"
                          >
                            + {chip}
                          </button>
                        ))}
                      </div>
                    </div>
                  )}
                </div>
              )}
            </div>

            {/* Bottom Actions */}
            <div className="flex items-center justify-between">
              <button
                type="button"
                onClick={handlePrev}
                disabled={currentStep === 0}
                className="text-xs font-bold text-slate-500 hover:text-slate-900 disabled:opacity-30 transition flex items-center gap-1.5 px-4 py-2.5 rounded-xl"
              >
                <ArrowLeft size={16} /> ย้อนกลับ
              </button>

              <div className="flex items-center gap-3">
                <button
                  type="button"
                  onClick={resetQuiz}
                  className="text-xs font-semibold text-slate-500 hover:text-slate-700"
                >
                  เริ่มใหม่
                </button>

                <button
                  type="button"
                  onClick={handleNext}
                  className="bg-indigo-600 hover:bg-indigo-700 text-white text-sm font-bold px-6 py-3 rounded-2xl shadow-sm hover:shadow transition flex items-center gap-2"
                >
                  <span>{currentStep === activeQuestions.length - 1 ? "ดูผลการวิเคราะห์" : "ถัดไป"}</span>
                  <ArrowRight size={16} />
                </button>
              </div>
            </div>
          </div>
        )}

        {/* VIEW 4: Full Comprehensive Results Report */}
        {result && (
          <div className="space-y-8 animate-fadeIn max-w-4xl mx-auto w-full">
            {/* Top Shareable Archetype Card */}
            <div className="bg-gradient-to-tr from-indigo-50 via-white to-blue-50 border border-indigo-200 rounded-3xl p-6 sm:p-10 shadow-sm relative overflow-hidden">
              <div className="flex flex-col sm:flex-row justify-between items-start sm:items-center gap-4 mb-4">
                <div className="inline-flex items-center gap-2 bg-indigo-100 text-indigo-800 px-3 py-1 rounded-full text-xs font-bold font-mono border border-indigo-200">
                  <Award size={14} className="text-amber-600" />
                  <span>Holland Code: {result.archetype_code}</span>
                </div>

                <button
                  onClick={copyShareResult}
                  className="bg-white hover:bg-slate-50 text-slate-700 text-xs font-bold px-3.5 py-2 rounded-xl transition flex items-center gap-1.5 border border-slate-200 shadow-xs"
                >
                  {copied ? <Check size={14} className="text-emerald-600" /> : <Copy size={14} />}
                  <span>{copied ? "คัดลอกข้อมูลแล้ว" : "คัดลอกผลการประเมิน"}</span>
                </button>
              </div>

              <h1 className="text-2xl sm:text-4xl font-black text-slate-900 tracking-tight mb-2">
                {result.archetype_title}
              </h1>
              <p className="text-slate-600 text-sm sm:text-base font-medium mb-6 leading-relaxed">
                {result.archetype_description}
              </p>

              {/* Share Quote Banner */}
              <div className="bg-white border border-indigo-100 p-4 rounded-2xl text-xs sm:text-sm text-slate-700 flex items-center gap-3 shadow-xs">
                <Compass size={18} className="text-indigo-600 flex-shrink-0" />
                <span className="font-medium italic">"{result.share_quote}"</span>
              </div>
            </div>

            {/* Split Grid: Radar Chart + Personality Analysis */}
            <div className="grid grid-cols-1 md:grid-cols-2 gap-6">
              {/* Radar Chart */}
              <RiasecRadarChart scores={result.riasec_scores} />

              {/* Personality Summary & Strengths */}
              <div className="bg-white border border-slate-200 rounded-3xl p-6 sm:p-8 flex flex-col justify-between shadow-sm">
                <div>
                  <h3 className="text-base font-bold text-slate-900 mb-3 flex items-center gap-2">
                    <Brain size={18} className="text-indigo-600" />
                    <span>บทวิเคราะห์คุณลักษณะและศักยภาพ</span>
                  </h3>
                  <p className="text-xs sm:text-sm text-slate-600 leading-relaxed mb-6 font-normal">
                    {result.personality_summary}
                  </p>

                  <div className="text-xs font-bold text-slate-700 mb-2">ทักษะและจุดเด่นหลัก:</div>
                  <div className="flex flex-wrap gap-2 mb-6">
                    {result.strengths.map((str, idx) => (
                      <span
                        key={idx}
                        className="bg-indigo-50 border border-indigo-100 text-indigo-700 text-xs px-3 py-1 rounded-xl font-medium"
                      >
                        ✓ {str}
                      </span>
                    ))}
                  </div>
                </div>

                <div className="bg-slate-50 p-3.5 rounded-2xl border border-slate-200 text-xs text-slate-700">
                  <span className="font-bold text-indigo-700 block mb-0.5">สภาพแวดล้อมการทำงานที่เหมาะสม:</span>
                  <span>{result.ideal_work_environment}</span>
                </div>
              </div>
            </div>

            {/* Top Recommended Careers */}
            <div className="bg-white border border-slate-200 rounded-3xl p-6 sm:p-8 shadow-sm">
              <h3 className="text-lg font-bold text-slate-900 mb-1 flex items-center gap-2">
                <Briefcase size={20} className="text-blue-600" />
                <span>สาขาวิชาชีพที่สอดคล้อง (Career Alignment)</span>
              </h3>
              <p className="text-xs text-slate-500 mb-6">
                ประมวลผลจากความสอดคล้องระหว่างคะแนนทักษะและแนวโน้มความต้องการในตลาดงาน
              </p>

              <div className="grid grid-cols-1 sm:grid-cols-3 gap-4">
                {result.top_careers.map((career, idx) => (
                  <div
                    key={idx}
                    className="bg-slate-50 border border-slate-200 p-5 rounded-2xl flex flex-col justify-between hover:border-blue-300 transition-colors"
                  >
                    <div>
                      <div className="flex justify-between items-center mb-2">
                        <span className="text-[10px] font-bold bg-blue-100 text-blue-800 px-2 py-0.5 rounded-md">
                          {career.growth_outlook}
                        </span>
                        <span className="text-xs font-mono font-bold text-emerald-700">{career.match_percentage}% Match</span>
                      </div>
                      <h4 className="font-bold text-slate-900 text-sm mb-2">{career.title}</h4>
                      <p className="text-xs text-slate-600 line-clamp-3 leading-relaxed mb-4">
                        {career.description}
                      </p>
                    </div>

                    <div className="flex flex-wrap gap-1 pt-3 border-t border-slate-200">
                      {career.skills.map((skill, sIdx) => (
                        <span key={sIdx} className="text-[10px] bg-white text-slate-600 px-2 py-0.5 rounded-md border border-slate-200 font-medium">
                          {skill}
                        </span>
                      ))}
                    </div>
                  </div>
                ))}
              </div>
            </div>

            {/* Recommended Undergraduate Programs (Direct Database Match) */}
            <div className="bg-white border border-slate-200 rounded-3xl p-6 sm:p-8 shadow-sm">
              <div className="flex flex-col sm:flex-row justify-between items-start sm:items-center gap-2 mb-6">
                <div>
                  <h3 className="text-lg font-bold text-slate-900 flex items-center gap-2">
                    <BookOpen size={20} className="text-indigo-600" />
                    <span>หลักสูตรระดับปริญญาตรีที่แนะนำ</span>
                  </h3>
                  <p className="text-xs text-slate-500">
                    ดึงข้อมูลตรงจากหลักสูตรมหาวิทยาลัยในระบบที่สอดคล้องกับเส้นทางอาชีพข้างต้น
                  </p>
                </div>
                <Link
                  href="/"
                  className="text-xs font-bold text-indigo-600 hover:text-indigo-700 flex items-center gap-1"
                >
                  <span>สำรวจหลักสูตรทั้งหมด</span> <ChevronRight size={14} />
                </Link>
              </div>

              {result.recommended_courses && result.recommended_courses.length > 0 ? (
                <div className="grid grid-cols-1 sm:grid-cols-2 gap-4">
                  {result.recommended_courses.map((course) => (
                    <div
                      key={course.id}
                      className="bg-white border border-slate-200 hover:border-indigo-300 p-5 rounded-2xl flex flex-col justify-between transition-all group shadow-xs hover:shadow-sm"
                    >
                      <div>
                        <div className="flex justify-between items-start gap-2 mb-2">
                          <span className="text-[10px] font-bold bg-indigo-50 text-indigo-700 px-2.5 py-0.5 rounded-full border border-indigo-100">
                            {course.degree_level || "ปริญญาตรี"}
                          </span>
                          {course.match_score && (
                            <span className="text-xs font-mono font-bold text-emerald-700 flex items-center gap-1">
                              <Sparkles size={12} className="text-emerald-600" /> {course.match_score}% Match
                            </span>
                          )}
                        </div>

                        <h4 className="font-bold text-slate-900 text-sm sm:text-base group-hover:text-indigo-600 transition-colors leading-snug mb-1">
                          {course.title_th}
                        </h4>
                        {course.title_en && (
                          <p className="text-[11px] text-slate-400 mb-2 truncate">{course.title_en}</p>
                        )}

                        <div className="text-xs text-slate-600 flex items-center gap-1.5 mb-3 font-medium">
                          <Building2 size={14} className="text-slate-400 flex-shrink-0" />
                          <span>{course.university_th}</span>
                          <span className="text-slate-300">•</span>
                          <span className="text-slate-500 font-normal">{course.faculty_th}</span>
                        </div>
                      </div>

                      <div className="pt-3 border-t border-slate-100 flex items-center justify-between">
                        <span className="text-[11px] text-slate-500">
                          {course.tuition_per_semester || "ตามประกาศมหาวิทยาลัย"}
                        </span>
                        {course.website_url ? (
                          <a
                            href={course.website_url}
                            target="_blank"
                            rel="noreferrer"
                            className="text-xs font-bold text-white bg-slate-900 hover:bg-indigo-600 px-3 py-1.5 rounded-xl transition flex items-center gap-1"
                          >
                            <span>ดูหลักสูตร</span> <ExternalLink size={12} />
                          </a>
                        ) : (
                          <Link
                            href="/"
                            className="text-xs font-bold text-white bg-slate-900 hover:bg-indigo-600 px-3 py-1.5 rounded-xl transition flex items-center gap-1"
                          >
                            <span>ดูในระบบ</span> <ChevronRight size={12} />
                          </Link>
                        )}
                      </div>
                    </div>
                  ))}
                </div>
              ) : (
                <div className="text-center py-6 text-xs text-slate-500 bg-slate-50 rounded-2xl border border-slate-200">
                  กำลังอัปเดตข้อมูลหลักสูตรที่สอดคล้อง
                </div>
              )}
            </div>

            {/* Growth & Preparation Advice Card */}
            <div className="bg-gradient-to-r from-indigo-50/60 via-white to-blue-50/60 border border-indigo-100 rounded-3xl p-6 sm:p-8 shadow-xs">
              <h3 className="text-base font-bold text-indigo-900 mb-2 flex items-center gap-2">
                <TrendingUp size={18} className="text-indigo-600" />
                <span>คำแนะนำเพื่อการเตรียมความพร้อมทางวิชาการ</span>
              </h3>
              <p className="text-xs sm:text-sm text-slate-700 leading-relaxed font-normal">
                {result.growth_advice}
              </p>
            </div>

            {/* Bottom Actions */}
            <div className="flex flex-col sm:flex-row items-center justify-center gap-4 pt-4">
              <button
                onClick={resetQuiz}
                className="bg-white hover:bg-slate-50 text-slate-700 text-xs font-bold px-6 py-3.5 rounded-2xl border border-slate-200 shadow-xs transition flex items-center gap-2 w-full sm:w-auto justify-center"
              >
                <RefreshCw size={15} />
                <span>ทำแบบประเมินใหม่อีกครั้ง</span>
              </button>

              <Link
                href="/"
                className="bg-gradient-to-r from-blue-600 to-indigo-600 hover:from-blue-700 hover:to-indigo-700 text-white text-xs font-bold px-8 py-3.5 rounded-2xl shadow-sm hover:shadow transition flex items-center gap-2 w-full sm:w-auto justify-center"
              >
                <BookOpen size={15} />
                <span>สำรวจหลักสูตรมหาวิทยาลัยทั้งหมด</span>
              </Link>
            </div>
          </div>
        )}
      </main>
    </div>
  );
}
