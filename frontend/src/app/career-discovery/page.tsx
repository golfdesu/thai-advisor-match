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
  AlertCircle
} from "lucide-react";

// Master Question Item Interface
interface QuestionItem {
  id: number;
  category: string;
  type: "single" | "multi" | "likert" | "text";
  dimension: string;
  question: string;
  subtitle?: string;
  options?: { key: string; label: string; icon?: string; desc?: string }[];
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

// 50 Questions Master Bank
const MASTER_QUESTIONS: QuestionItem[] = [
  // 1-5 (Quick Tier)
  {
    id: 1,
    category: "วิชาและกิจกรรมที่ชอบ",
    type: "multi",
    dimension: "I+A+R+S+E+C",
    question: "วิชาหรือกิจกรรมไหนที่คุณทำแล้วรู้สึกสนุกและเวลาผ่านไปไวที่สุด? (เลือกได้หลายข้อ)",
    subtitle: "เลือกสิ่งที่คุณสนใจจริงจากใจ",
    options: [
      { key: "I", label: "คณิตศาสตร์ / ฟิสิกส์ / เขียนโปรแกรม", icon: "💻", desc: "ชอบตรรกะ ตัวเลข และการแก้โจทย์" },
      { key: "A", label: "ศิลปะ / ดนตรี / วาดรูป / ออกแบบ", icon: "🎨", desc: "ชอบสร้างสรรค์ จินตนาการ และความสวยงาม" },
      { key: "I+R", label: "ชีววิทยา / เคมี / การทดลองในแล็บ", icon: "🧪", desc: "ชอบศึกษาสิ่งมีชีวิตและธรรมชาติ" },
      { key: "S+A", label: "ภาษา / สังคมศึกษา / วรรณกรรม", icon: "📚", desc: "ชอบการสื่อสารและเข้าใจผู้คน" },
      { key: "R", label: "พละศึกษา / งานช่าง / การลงมือทำจริง", icon: "🛠️", desc: "ชอบกิจกรรมภาคปฏิบัติ ไม่ชอบนั่งนิ่งๆ" },
      { key: "E+S", label: "กิจกรรมชมรม / สภานักเรียน / วางแผนงาน", icon: "📢", desc: "ชอบเป็นผู้นำ จัดการ และประสานงาน" }
    ]
  },
  {
    id: 2,
    category: "เวลาว่างและงานอดิเรก",
    type: "single",
    dimension: "R+A+I+S+E+C",
    question: "ถ้ามีเวลาว่าง 1 วันเต็มๆ โดยไม่มีการบ้าน คุณอยากทำอะไรมากที่สุด?",
    options: [
      { key: "R", label: "ประกอบของ / เล่นเกมใช้กลยุทธ์ / ซ่อมอุปกรณ์", icon: "🎮" },
      { key: "A", label: "วาดรูป / ทำคลิป / แต่งเพลง / ถ่ายรูป", icon: "📷" },
      { key: "I", label: "ดูคลิปสารคดี / อ่านเรื่องวิทยาศาสตร์ / ศึกษาเทคโนโลยีใหม่ๆ", icon: "🔬" },
      { key: "S", label: "นัดเจอเพื่อน / ร่วมกิจกรรมอาสา / นั่งคุยแลกเปลี่ยนมุมมอง", icon: "☕" },
      { key: "E", label: "วางแผนหาเงิน / ขายของ / ศึกษาการลงทุนและธุรกิจ", icon: "📈" },
      { key: "C", label: "จัดห้อง / วางแพลนเนอร์ / สรุปความรู้และจัดระเบียบชีวิต", icon: "📋" }
    ]
  },
  {
    id: 3,
    category: "สไตล์การแก้ปัญหา",
    type: "single",
    dimension: "I+R+S+A",
    question: "เวลาต้องเผชิญกับปัญหายากๆ ในชีวิต คุณมักจะรับมืออย่างไร?",
    options: [
      { key: "I", label: "นั่งวิเคราะห์หาสาเหตุอย่างเป็นระบบ หาข้อมูลก่อนลงมือ", icon: "🔍" },
      { key: "R", label: "ลองผิดลองถูกเลย ลงมือแก้ทันที เดี๋ยวก็เห็นทางออก", icon: "⚡" },
      { key: "S", label: "ปรึกษาเพื่อนหรือคนที่ไว้ใจ รับฟังความคิดเห็นหลายๆ มุม", icon: "🤝" },
      { key: "A", label: "ใช้ไอเดียสร้างสรรค์ หาวิธีใหม่ๆ ที่ไม่ซ้ำใคร", icon: "💡" }
    ]
  },
  {
    id: 4,
    category: "วิสัยทัศน์ชีวิต (Life Vision)",
    type: "text",
    dimension: "I+S+E",
    question: "ถ้าคุณมีพลังวิเศษเปลี่ยนแปลงโลกได้ 1 อย่าง คุณอยากแก้ปัญหาอะไรมากที่สุด?",
    subtitle: "พิมพ์สั้นๆ 1-2 ประโยค หรือแตะเลือกคีย์เวิร์ดแนะนำด้านล่าง",
    chips: [
      "แก้ปัญหาโลกร้อนและสิ่งแวดล้อม",
      "พัฒนาเทคโนโลยี AI ให้ช่วยมนุษย์",
      "สร้างความเท่าเทียมด้านการศึกษา",
      "ยกระดับการรักษาพยาบาลให้ทุกคนเข้าถึงได้",
      "ลดความเหลื่อมล้ำทางเศรษฐกิจ",
      "สร้างสรรค์ผลงานศิลปะและคอนเทนต์สร้างแรงบันดาลใจ"
    ]
  },
  {
    id: 5,
    category: "ตัวตนในสายตาคนอื่น",
    type: "text",
    dimension: "A+S+E",
    question: "ถ้าเพื่อนสนิทต้องอธิบายความเป็นคุณใน 3 คำ เพื่อนจะบอกว่าคุณเป็นคนอย่างไร?",
    subtitle: "แตะคีย์เวิร์ดหรือพิมพ์เองได้เลย",
    chips: [
      "คิดวิเคราะห์ ละเอียด มีเหตุผล",
      "ใจดี รับฟัง ชอบช่วยเหลือ",
      "ครีเอทีฟ มีจินตนาการ ขี้เล่น",
      "มีความเป็นผู้นำ กล้าตัดสินใจ",
      "ลุยงาน อดทน พึ่งพาได้",
      "ชอบวางแผน มีระเบียบ รอบคอบ"
    ]
  },

  // 6-20 (Standard Tier)
  {
    id: 6,
    category: "บทบาทในการทำงานกลุ่ม",
    type: "single",
    dimension: "E+A+R+S+C",
    question: "เวลาทำงานกลุ่มในโรงเรียน บทบาทที่เหมาะกับคุณที่สุดคือ?",
    options: [
      { key: "E", label: "ผู้นำกลุ่ม (Leader) - วางทิศทาง แจกจ่ายงาน และคอยกระตุ้นทีม", icon: "👑" },
      { key: "A", label: "ฝ่ายสร้างสรรค์ (Creator) - คิดไอเดีย ออกแบบพรีเซนต์ และธีมงาน", icon: "🎨" },
      { key: "R", label: "ฝ่ายลงมือทำ (Doer) - ทำชิ้นงานจริง ส่วนที่ต้องประดิษฐ์หรือพิมพ์", icon: "🔨" },
      { key: "S", label: "ฝ่ายประสานงาน (Mediator) - เชื่อมความสัมพันธ์ ดูแลความรู้สึกทุกคน", icon: "💖" },
      { key: "C", label: "ฝ่ายตรวจสอบ (Checker) - เช็คความถูกต้อง จัดฟอร์แมต ตรวจคำผิด", icon: "✅" }
    ]
  },
  {
    id: 7,
    category: "ความถนัดด้านตรรกะ",
    type: "likert",
    dimension: "I",
    question: "ฉันรู้สึกตื่นเต้นและสนุกเวลาได้แก้โจทย์คณิตศาสตร์ ปริศนาตรรกะ หรือเขียนโค้ด"
  },
  {
    id: 8,
    category: "ความเห็นอกเห็นใจ",
    type: "likert",
    dimension: "S",
    question: "ฉันรู้สึกมีความสุขมากเวลาได้เป็นที่ปรึกษา ช่วยเหลือ หรือสอนการบ้านเพื่อน"
  },
  {
    id: 9,
    category: "ความคิดสร้างสรรค์",
    type: "likert",
    dimension: "A",
    question: "ฉันมักจะจินตนาการถึงสิ่งใหม่ๆ และอยากสร้างผลงานที่เป็นเอกลักษณ์ของตัวเอง"
  },
  {
    id: 10,
    category: "ความกล้าเสี่ยงและการตัดสินใจ",
    type: "likert",
    dimension: "E",
    question: "ฉันชอบความท้าทายและการแข่งขัน กล้าตัดสินใจในสถานการณ์ที่ไม่แน่นอน"
  },
  {
    id: 11,
    category: "ความละเอียดรอบคอบ",
    type: "likert",
    dimension: "C",
    question: "ฉันเป็นคนชอบจัดระเบียบ สังเกตเห็นจุดผิดพลาดเล็กๆ ที่คนอื่นมองข้าม"
  },
  {
    id: 12,
    category: "การลงมือปฏิบัติจริง",
    type: "likert",
    dimension: "R",
    question: "ฉันชอบเรียนรู้จากการลงมือทำของจริง มากกว่าการนั่งฟังทฤษฎีในห้องเรียน"
  },
  {
    id: 13,
    category: "ภาพอนาคตในวัยทำงาน",
    type: "single",
    dimension: "E+I+S+A+C",
    question: "คุณมองเห็นตัวเองทำงานในรูปแบบไหนที่มีความสุขที่สุด?",
    options: [
      { key: "E", label: "เป็นผู้บริหารหรือเจ้าของธุรกิจของตัวเอง มีอิสระและผลตอบแทนสูง", icon: "💼" },
      { key: "I", label: "นักวิจัยหรือผู้เชี่ยวชาญเฉพาะทาง ค้นพบนวัตกรรมใหม่ๆ ในแล็บ", icon: "🔬" },
      { key: "S", label: "ทำงานในโรงพยาบาล โรงเรียน หรือองค์กรที่ได้ยกระดับคุณภาพชีวิตผู้คน", icon: "🏥" },
      { key: "A", label: "ศิลปิน ครีเอเตอร์ ดีไซเนอร์ หรือฟรีแลนซ์ที่มีอิสระทางความคิด", icon: "🖌️" },
      { key: "C", label: "ทำงานในองค์กรที่มั่นคง มีระบบระเบียบชัดเจน และสวัสดิการดี", icon: "🏢" }
    ]
  },
  {
    id: 14,
    category: "ทักษะการสื่อสาร",
    type: "likert",
    dimension: "E+S",
    question: "ฉันชอบการพูดในที่สาธารณะ การนำเสนองาน หรือการโน้มน้าวใจผู้ฟัง"
  },
  {
    id: 15,
    category: "ความสนใจด้านเทคโนโลยี",
    type: "likert",
    dimension: "I+R",
    question: "ฉันติดตามข่าวสารเกี่ยวกับ AI, หุ่นยนต์, ดิจิทัล และอยากเข้าใจเบื้องหลังการทำงานของมัน"
  },
  {
    id: 16,
    category: "สิ่งที่ไม่ชอบอย่างยิ่ง (Anti-Patterns)",
    type: "multi",
    dimension: "Anti",
    question: "สิ่งไหนที่คุณรู้สึกว่า 'ไม่ใช่ตัวฉันเลย' หรือทนทำไม่ได้นานๆ? (เลือกได้หลายข้อ)",
    subtitle: "การรู้สิ่งที่ไม่ชอบจะช่วยตัดคณะที่ไม่ใช่ออกได้อย่างแม่นยำ",
    options: [
      { key: "Anti-C", label: "งานเอกสารซ้ำซาก กฎระเบียบเคร่งครัด นั่งโต๊ะทั้งวัน", icon: "📑" },
      { key: "Anti-E", label: "ต้องคอยขายของ โน้มน้าวคน หรือออกไปพูดต่อหน้าคนเยอะๆ", icon: "🗣️" },
      { key: "Anti-I", label: "ต้องนั่งอ่านงานวิจัยสูตรยากๆ ท่องจำทฤษฎีคนเดียว", icon: "📖" },
      { key: "Anti-R", label: "งานที่ต้องตากแดด เลอะเทอะ หรือใช้แรงกายหนักๆ", icon: "☀️" },
      { key: "Anti-S", label: "ต้องรับฟังปัญหาอารมณ์ของคนอื่น หรือรับผิดชอบชีวิตผู้ป่วย", icon: "💔" },
      { key: "Anti-A", label: "งานที่ไม่มีความแน่นอน ต้องด้นสดตลอดเวลา ไม่มีแบบแผน", icon: "🌀" }
    ]
  },
  {
    id: 17,
    category: "ค่านิยมสูงสุดในการเลือกงาน",
    type: "single",
    dimension: "Values",
    question: "สิ่งที่สำคัญที่สุดสำหรับคุณในการประกอบอาชีพในอนาคตคือ?",
    options: [
      { key: "Money", label: "💰 ผลตอบแทนทางการเงินที่สูงและสร้างความมั่งคั่ง", icon: "💵" },
      { key: "Meaning", label: "❤️ ได้ทำงานที่มีคุณค่าและสร้างประโยชน์ต่อสังคม", icon: "🌱" },
      { key: "Freedom", label: "🏖️ อิสรภาพในการจัดเวลาชีวิตและไลฟ์สไตล์ (Work-Life Balance)", icon: "✈️" },
      { key: "Mastery", label: "🏆 ได้เป็นผู้เชี่ยวชาญระดับท็อปในสาขาของตัวเอง", icon: "🌟" }
    ]
  },
  {
    id: 18,
    category: "บุคคลต้นแบบ (Role Model)",
    type: "text",
    dimension: "E+I+A",
    question: "มีใครที่คุณชื่นชอบหรือมองเป็นไอดอลในดวงใจไหม? เพราะอะไร?",
    subtitle: "พิมพ์ชื่อหรือแตะตัวเลือกแนะนำได้เลย",
    chips: [
      "Elon Musk - กล้าคิดการใหญ่ สร้างเทคโนโลยีเปลี่ยนโลก",
      "Steve Jobs - ผสมผสานศิลปะและเทคโนโลยีได้อย่างลงตัว",
      "หมอ/พยาบาล/บุคคลากรสาธารณสุข - เสียสละเพื่อผู้ป่วย",
      "ครู/อาจารย์ผู้สร้างแรงบันดาลใจ - ถ่ายทอดความรู้",
      "ศิลปิน/นักเขียน/ผู้กำกับ - สร้างผลงานสะเทือนอารมณ์",
      "นักธุรกิจ/Startup Founder - สร้างคุณค่าจากศูนย์"
    ]
  },
  {
    id: 19,
    category: "หัวข้อที่หลงใหล (Passion Signal)",
    type: "text",
    dimension: "I+A",
    question: "เรื่องอะไรที่คุณสามารถอ่าน ดูคลิป หรือพูดคุยได้เป็นชั่วโมงๆ โดยไม่เบื่อเลย?",
    subtitle: "หัวข้อนี้คือสัญญาณความถนัดที่แท้จริงของคุณ",
    chips: [
      "AI & Machine Learning และเทคโนโลยีล้ำยุค",
      "การเงิน หุ้น คริปโต และการทำธุรกิจ",
      "จิตวิทยา พฤติกรรมมนุษย์ และการพัฒนาตนเอง",
      "การแพทย์ พันธุศาสตร์ และสุขภาพ",
      "ดนตรี ศิลปะ แอนิเมชัน และการออกแบบ",
      "อวกาศ ฟิสิกส์ดาราศาสตร์ และความลับของจักรวาล"
    ]
  },
  {
    id: 20,
    category: "ความกังวลในการเลือกคณะ",
    type: "text",
    dimension: "PainPoint",
    question: "ความกังวลที่สุดของคุณเกี่ยวกับการเรียนต่อมหาวิทยาลัยในตอนนี้คืออะไร?",
    chips: [
      "กลัวเลือกคณะแล้วเรียนไม่ไหว/ไม่ชอบ",
      "กลัวจบมาแล้วตกงาน หรือตลาดงานเปลี่ยนเพราะ AI",
      "ความคาดหวังของครอบครัวไม่ตรงกับความชอบของตัวเอง",
      "กังวลเรื่องค่าเทอมและค่าใช้จ่าย",
      "ยังไม่มั่นใจในจุดเด่นและความสามารถของตัวเอง"
    ]
  },

  // 21-50 (Deep Dive Tier Sample items)
  {
    id: 21,
    category: "สไตล์การทำงานร่วมกับผู้อื่น",
    type: "likert",
    dimension: "S",
    question: "ฉันทำงานได้มีประสิทธิภาพและมีความสุขมากกว่าเมื่อได้ทำงานเป็นทีม"
  },
  {
    id: 22,
    category: "การเดินทางและความตื่นเต้น",
    type: "likert",
    dimension: "E",
    question: "ฉันใฝ่ฝันอยากทำงานที่ได้เดินทางไปต่างประเทศหรือเปิดรับสิ่งแวดล้อมใหม่ๆ บ่อยๆ"
  },
  {
    id: 23,
    category: "ตารางเวลาการทำงาน",
    type: "likert",
    dimension: "C",
    question: "ฉันชอบการทำงานที่มีตารางเวลาเข้า-ออกงานชัดเจนแน่นอน มากกว่าเวลาที่ยืดหยุ่นแต่ไม่แน่นอน"
  },
  {
    id: 24,
    category: "สถานที่ทำงานในฝัน",
    type: "single",
    dimension: "Env",
    question: "สถานที่ทำงานแบบไหนที่ทำให้คุณรู้สึกมีพลังในการทำงานมากที่สุด?",
    options: [
      { key: "I+E", label: "ออฟฟิศทันสมัย มีคาเฟ่และพื้นที่ระดมสมอง (Tech/Startup)", icon: "🏢" },
      { key: "I+R", label: "ห้องปฏิบัติการทดลอง ศูนย์วิจัย หรือโรงพยาบาลชั้นนำ", icon: "🔬" },
      { key: "A", label: "สตูดิโอดีไซน์ พื้นที่ศิลปะ หรือร้านกาแฟบรรยากาศสงบ", icon: "🎨" },
      { key: "R", label: "พื้นที่กลางแจ้ง ไร่นา ธรรมชาติ หรือไซต์งานวิศวกรรม", icon: "🌲" },
      { key: "DigitalNomad", label: "ที่ไหนก็ได้ในโลก ขอแค่มีโน้ตบุ๊กกับสัญญาณอินเทอร์เน็ต", icon: "💻" }
    ]
  },
  {
    id: 25,
    category: "ความอดทนต่อแรงกดดัน",
    type: "likert",
    dimension: "Stress",
    question: "ฉันสามารถรับมือกับเดดไลน์กระชั้นชิดและสภาวะกดดันสูงได้ดีโดยไม่ตื่นตระหนก"
  },
  {
    id: 26,
    category: "การเรียนรู้ด้วยตนเอง",
    type: "likert",
    dimension: "I",
    question: "ฉันชอบค้นคว้าหาความรู้ด้วยตัวเองผ่านอินเทอร์เน็ตมากกว่ารอให้ครูมาสอน"
  },
  {
    id: 27,
    category: "ความเป็นผู้ประกอบการ",
    type: "likert",
    dimension: "E",
    question: "ฉันมองเห็นโอกาสทางธุรกิจในชีวิตประจำวันเสมอ และอยากสร้างแบรนด์ของตนเอง"
  },
  {
    id: 28,
    category: "การใช้ภาษาต่างประเทศ",
    type: "likert",
    dimension: "Global",
    question: "ฉันอยากศึกษาในหลักสูตรนานาชาติหรือทำงานในสภาพแวดล้อมสากลที่ใช้ภาษาอังกฤษเป็นหลัก"
  },
  {
    id: 29,
    category: "การคิดเชิงกลยุทธ์",
    type: "likert",
    dimension: "I+E",
    question: "ฉันมักจะวางแผนล่วงหน้าเป็นขั้นเป็นตอนเสมอ ก่อนจะเริ่มต้นทำโปรเจกต์ใดๆ"
  },
  {
    id: 30,
    category: "ความอ่อนไหวต่อความรู้สึกคน",
    type: "likert",
    dimension: "S",
    question: "ฉันสามารถรับรู้ความรู้สึกและอารมณ์ของคนรอบข้างได้อย่างรวดเร็วแม้เขาไม่ได้พูดออกมา"
  }
];

// Visual Spider/Radar Chart Component in Pure SVG
function RiasecRadarChart({ scores }: { scores: RiasecScore }) {
  const size = 320;
  const center = size / 2;
  const radius = 105;

  const traits = [
    { key: "realistic", label: "นักปฏิบัติ (R)", code: "R", color: "#f97316" },
    { key: "investigative", label: "นักสืบค้น (I)", code: "I", color: "#3b82f6" },
    { key: "artistic", label: "นักสร้างสรรค์ (A)", code: "A", color: "#ec4899" },
    { key: "social", label: "นักสังคม (S)", code: "S", color: "#10b981" },
    { key: "enterprising", label: "นักบริหาร (E)", code: "E", color: "#8b5cf6" },
    { key: "conventional", label: "นักจัดระเบียบ (C)", code: "C", color: "#06b6d4" }
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

  // Background Web Rings
  const webRings = [0.25, 0.5, 0.75, 1.0];

  return (
    <div className="flex flex-col items-center justify-center p-4 bg-slate-900/90 rounded-3xl text-white shadow-xl border border-slate-800 relative overflow-hidden">
      <div className="absolute top-3 left-4 flex items-center gap-1.5 text-xs font-bold text-slate-400">
        <Sparkles size={14} className="text-amber-400" />
        <span>Holland's RIASEC Profile</span>
      </div>

      <svg width={size} height={size} className="overflow-visible mt-2">
        {/* Background Grid Rings */}
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
              stroke="#334155"
              strokeWidth="1"
              strokeDasharray={scale === 1 ? "none" : "2,2"}
            />
          );
        })}

        {/* Radial Axis Lines */}
        {traits.map((_, index) => {
          const angle = index * angleStep - Math.PI / 2;
          const x = center + radius * Math.cos(angle);
          const y = center + radius * Math.sin(angle);
          return <line key={index} x1={center} y1={center} x2={x} y2={y} stroke="#334155" strokeWidth="1" />;
        })}

        {/* Value Polygon with Gradient Fill */}
        <polygon
          points={points}
          fill="url(#radarGradient)"
          fillOpacity="0.5"
          stroke="#6366f1"
          strokeWidth="2.5"
          className="transition-all duration-700 ease-out"
        />

        <defs>
          <linearGradient id="radarGradient" x1="0%" y1="0%" x2="100%" y2="100%">
            <stop offset="0%" stopColor="#3b82f6" stopOpacity="0.7" />
            <stop offset="50%" stopColor="#8b5cf6" stopOpacity="0.7" />
            <stop offset="100%" stopColor="#ec4899" stopOpacity="0.7" />
          </linearGradient>
        </defs>

        {/* Data Nodes & Labels */}
        {traits.map((trait, index) => {
          const angle = index * angleStep - Math.PI / 2;
          const value = (scores as any)[trait.key] || 40;
          const nodeR = (value / 100) * radius;
          const nodeX = center + nodeR * Math.cos(angle);
          const nodeY = center + nodeR * Math.sin(angle);

          // Label placement outside radius
          const labelR = radius + 24;
          const labelX = center + labelR * Math.cos(angle);
          const labelY = center + labelR * Math.sin(angle);

          return (
            <g key={index}>
              {/* Point Circle */}
              <circle cx={nodeX} cy={nodeY} r="4.5" fill={trait.color} stroke="#ffffff" strokeWidth="1.5" />

              {/* Text Label */}
              <text
                x={labelX}
                y={labelY + 4}
                textAnchor="middle"
                fontSize="10.5"
                fontWeight="bold"
                fill={trait.color}
                className="select-none"
              >
                {trait.code}: {Math.round(value)}%
              </text>
            </g>
          );
        })}
      </svg>

      {/* Trait Legend Badges */}
      <div className="grid grid-cols-3 gap-2 w-full mt-3 pt-3 border-t border-slate-800 text-[11px]">
        {traits.map((t, idx) => (
          <div key={idx} className="flex items-center gap-1.5 bg-slate-800/80 px-2 py-1 rounded-lg">
            <span className="w-2 h-2 rounded-full" style={{ backgroundColor: t.color }}></span>
            <span className="text-slate-300 font-medium truncate">{t.label}</span>
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
    return MASTER_QUESTIONS; // deep dive (up to 30-50)
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

    // Format answers array
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
    const text = `🎯 ผลวิเคราะห์ตัวตนจาก AI Thai EduCenter:\n✨ ${result.archetype_title}\n"${result.share_quote}"\n\n🔍 ค้นพบตัวเองและหลักสูตรมหาวิทยาลัยที่ใช่ได้ที่: ${window.location.href}`;
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
    <div className="min-h-screen bg-slate-950 text-slate-100 flex flex-col selection:bg-indigo-500 selection:text-white">
      {/* Top Navbar */}
      <header className="border-b border-slate-800/80 bg-slate-900/60 backdrop-blur-md sticky top-0 z-50">
        <div className="max-w-6xl mx-auto px-4 sm:px-6 h-16 flex items-center justify-between">
          <Link href="/" className="flex items-center gap-2.5 text-white hover:text-indigo-400 transition">
            <div className="w-8 h-8 rounded-xl bg-gradient-to-tr from-indigo-500 to-blue-500 flex items-center justify-center text-white shadow-sm">
              <GraduationCap size={18} />
            </div>
            <span className="font-black text-lg tracking-tight">Thai EduCenter</span>
            <span className="text-[10px] font-bold uppercase bg-indigo-500/20 text-indigo-300 px-2 py-0.5 rounded-full border border-indigo-500/30">
              Career DNA
            </span>
          </Link>

          <div className="flex items-center gap-3">
            <Link
              href="/"
              className="text-xs font-semibold text-slate-400 hover:text-white transition flex items-center gap-1 bg-slate-800/80 px-3 py-1.5 rounded-xl border border-slate-700"
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
            <div className="inline-flex items-center gap-2 bg-indigo-500/10 border border-indigo-500/30 text-indigo-300 px-4 py-1.5 rounded-full text-xs font-bold mb-6 shadow-sm">
              <Sparkles size={14} className="text-indigo-400 animate-pulse" />
              <span>AI-Powered Holland RIASEC Career Discovery</span>
            </div>

            <h1 className="text-3xl sm:text-5xl font-black text-white tracking-tight leading-tight mb-4">
              ค้นหา <span className="text-transparent bg-clip-text bg-gradient-to-r from-indigo-400 via-sky-400 to-pink-400">ตัวตน & คณะที่ใช่</span><br />
              ด้วยแบบประเมินอัจฉริยะ
            </h1>

            <p className="text-slate-400 text-sm sm:text-base max-w-xl mx-auto mb-10 leading-relaxed">
              ยังไม่แน่ใจว่าจะเรียนต่อคณะไหน? ให้ AI ถอดรหัส DNA บุคลิกภาพ ความชอบ และค่านิยมของคุณ พร้อมแนะนำหลักสูตรปริญญาตรีที่ตอบโจทย์อนาคต
            </p>

            {/* 3 Tier Selection Cards */}
            <div className="grid grid-cols-1 md:grid-cols-3 gap-5 text-left mb-8">
              {/* Quick Tier */}
              <button
                onClick={() => {
                  setTier("quick");
                  setCurrentStep(0);
                }}
                className="group bg-slate-900/90 hover:bg-slate-850 p-6 rounded-3xl border border-slate-800 hover:border-amber-500/50 transition-all shadow-lg hover:shadow-amber-500/10 flex flex-col justify-between"
              >
                <div>
                  <div className="w-12 h-12 rounded-2xl bg-amber-500/10 text-amber-400 flex items-center justify-center mb-4 group-hover:scale-110 transition-transform">
                    <Zap size={24} />
                  </div>
                  <div className="flex items-center gap-2 mb-1">
                    <span className="text-xs font-bold uppercase tracking-wider text-amber-400">โหมดด่วน</span>
                    <span className="text-[10px] bg-slate-800 text-slate-400 px-2 py-0.5 rounded-full">⏱️ ~1 นาที</span>
                  </div>
                  <h3 className="text-xl font-bold text-white mb-2">⚡ Quick Scan</h3>
                  <p className="text-xs text-slate-400 leading-relaxed mb-4">
                    5 คำถามสายฟ้าแลบ สำหรับคนอยากได้ไอเดียคร่าวๆ แบบเร่งด่วน
                  </p>
                </div>
                <div className="flex items-center text-xs font-bold text-amber-400 group-hover:translate-x-1 transition-transform">
                  <span>เริ่มทำเลย</span> <ChevronRight size={14} className="ml-1" />
                </div>
              </button>

              {/* Standard Tier (Recommended) */}
              <button
                onClick={() => {
                  setTier("standard");
                  setCurrentStep(0);
                }}
                className="group bg-gradient-to-b from-indigo-950/60 to-slate-900/90 p-6 rounded-3xl border-2 border-indigo-500/60 hover:border-indigo-400 transition-all shadow-xl hover:shadow-indigo-500/20 flex flex-col justify-between relative overflow-hidden scale-[1.02]"
              >
                <div className="absolute top-3 right-3 bg-indigo-500 text-white font-black text-[10px] uppercase tracking-wider px-2.5 py-0.5 rounded-full">
                  แนะนำ ⭐
                </div>
                <div>
                  <div className="w-12 h-12 rounded-2xl bg-indigo-500/20 text-indigo-400 flex items-center justify-center mb-4 group-hover:scale-110 transition-transform">
                    <Target size={24} />
                  </div>
                  <div className="flex items-center gap-2 mb-1">
                    <span className="text-xs font-bold uppercase tracking-wider text-indigo-400">โหมดมาตรฐาน</span>
                    <span className="text-[10px] bg-slate-800 text-slate-300 px-2 py-0.5 rounded-full">⏱️ ~4 นาที</span>
                  </div>
                  <h3 className="text-xl font-bold text-white mb-2">🎯 Standard Match</h3>
                  <p className="text-xs text-slate-300 leading-relaxed mb-4">
                    20 คำถามเจาะลึก ผสมความถนัด ความคิดสร้างสรรค์ และค่านิยมการทำงาน
                  </p>
                </div>
                <div className="flex items-center text-xs font-bold text-indigo-300 group-hover:translate-x-1 transition-transform">
                  <span>เริ่มทำแบบประเมิน</span> <ChevronRight size={14} className="ml-1" />
                </div>
              </button>

              {/* Deep Dive Tier */}
              <button
                onClick={() => {
                  setTier("deep");
                  setCurrentStep(0);
                }}
                className="group bg-slate-900/90 hover:bg-slate-850 p-6 rounded-3xl border border-slate-800 hover:border-pink-500/50 transition-all shadow-lg hover:shadow-pink-500/10 flex flex-col justify-between"
              >
                <div>
                  <div className="w-12 h-12 rounded-2xl bg-pink-500/10 text-pink-400 flex items-center justify-center mb-4 group-hover:scale-110 transition-transform">
                    <Brain size={24} />
                  </div>
                  <div className="flex items-center gap-2 mb-1">
                    <span className="text-xs font-bold uppercase tracking-wider text-pink-400">สแกนระดับลึก</span>
                    <span className="text-[10px] bg-slate-800 text-slate-400 px-2 py-0.5 rounded-full">⏱️ ~10 นาที</span>
                  </div>
                  <h3 className="text-xl font-bold text-white mb-2">🧠 Deep Dive DNA</h3>
                  <p className="text-xs text-slate-400 leading-relaxed mb-4">
                    30-50 ข้อ วิเคราะห์จิตวิทยาระดับลึก ค่านิยมชีวิต และความทนทานต่อแรงกดดัน
                  </p>
                </div>
                <div className="flex items-center text-xs font-bold text-pink-400 group-hover:translate-x-1 transition-transform">
                  <span>เริ่มสแกนลึก</span> <ChevronRight size={14} className="ml-1" />
                </div>
              </button>
            </div>

            <div className="text-xs text-slate-500 flex items-center justify-center gap-4">
              <span>🔒 ไม่มีการเก็บข้อมูลส่วนบุคคล</span>
              <span>•</span>
              <span>⚡ ประมวลผลด้วย Google Gemini AI</span>
            </div>
          </div>
        )}

        {/* VIEW 2: Submitting / Loading Screen */}
        {isSubmitting && (
          <div className="text-center py-20 animate-fadeIn">
            <div className="relative w-20 h-20 mx-auto mb-6">
              <div className="absolute inset-0 rounded-full border-4 border-indigo-500/20 animate-ping"></div>
              <div className="w-20 h-20 rounded-full bg-gradient-to-tr from-indigo-600 to-pink-500 flex items-center justify-center text-white shadow-xl shadow-indigo-500/30 animate-spin">
                <Sparkles size={32} />
              </div>
            </div>
            <h2 className="text-2xl font-black text-white mb-2">AI กำลังวิเคราะห์ DNA ตัวตนของคุณ...</h2>
            <p className="text-sm text-slate-400 max-w-md mx-auto">
              กำลังคำนวณคะแนน Holland's RIASEC และค้นหาความเข้ากันได้กับหลักสูตรมหาวิทยาลัยกว่า 3,000 แห่ง...
            </p>
          </div>
        )}

        {/* VIEW 3: Step-by-Step Question Interface */}
        {tier && !result && !isSubmitting && currentQ && (
          <div className="max-w-2xl mx-auto w-full animate-fadeIn">
            {/* Progress Bar & Header */}
            <div className="mb-6">
              <div className="flex justify-between items-center text-xs font-bold text-slate-400 mb-2">
                <span className="flex items-center gap-1.5 text-indigo-400">
                  <Compass size={14} />
                  <span>{currentQ.category}</span>
                </span>
                <span>ข้อที่ {currentStep + 1} / {activeQuestions.length} ({progressPct}%)</span>
              </div>
              <div className="w-full bg-slate-800 h-2 rounded-full overflow-hidden">
                <div
                  className="bg-gradient-to-r from-indigo-500 via-sky-400 to-pink-500 h-full rounded-full transition-all duration-300"
                  style={{ width: `${progressPct}%` }}
                ></div>
              </div>
            </div>

            {/* Question Card */}
            <div className="bg-slate-900/90 border border-slate-800 rounded-3xl p-6 sm:p-8 shadow-2xl backdrop-blur-md mb-6">
              <span className="inline-block bg-slate-800 text-slate-300 text-[11px] font-bold px-3 py-1 rounded-full mb-3">
                Question {currentStep + 1}
              </span>

              <h2 className="text-xl sm:text-2xl font-bold text-white leading-snug mb-2">
                {currentQ.question}
              </h2>

              {currentQ.subtitle && (
                <p className="text-xs sm:text-sm text-slate-400 mb-6">{currentQ.subtitle}</p>
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
                            ? "bg-indigo-600/20 border-indigo-500 text-white shadow-md shadow-indigo-500/10"
                            : "bg-slate-800/60 border-slate-750 text-slate-300 hover:border-slate-600 hover:bg-slate-800"
                        }`}
                      >
                        <div className="flex items-center gap-3">
                          {opt.icon && <span className="text-2xl flex-shrink-0">{opt.icon}</span>}
                          <div>
                            <div className="font-bold text-sm sm:text-base">{opt.label}</div>
                            {opt.desc && <div className="text-xs text-slate-400 mt-0.5">{opt.desc}</div>}
                          </div>
                        </div>
                        <div
                          className={`w-6 h-6 rounded-full flex items-center justify-center border flex-shrink-0 ${
                            isSelected ? "bg-indigo-500 border-indigo-400 text-white" : "border-slate-600 bg-slate-900"
                          }`}
                        >
                          {isSelected && <Check size={14} />}
                        </div>
                      </button>
                    );
                  })}
                </div>
              )}

              {/* INPUT TYPE 2: Likert 5-point Scale */}
              {currentQ.type === "likert" && (
                <div className="mt-8">
                  <div className="grid grid-cols-5 gap-2 sm:gap-3">
                    {[
                      { val: 1, label: "ไม่เห็นด้วยเลย", emoji: "❌", color: "hover:border-red-500" },
                      { val: 2, label: "ไม่ค่อยเห็นด้วย", emoji: "👎", color: "hover:border-orange-500" },
                      { val: 3, label: "ปานกลาง", emoji: "😐", color: "hover:border-slate-400" },
                      { val: 4, label: "ค่อนข้างเห็นด้วย", emoji: "👍", color: "hover:border-sky-500" },
                      { val: 5, label: "เห็นด้วยอย่างยิ่ง", emoji: "🔥", color: "hover:border-emerald-500" }
                    ].map((item) => {
                      const isSelected = answers[currentQ.id] === item.val;
                      return (
                        <button
                          key={item.val}
                          type="button"
                          onClick={() => handleSelectOption(currentQ.id, item.val, false)}
                          className={`p-3 sm:p-4 rounded-2xl border text-center transition-all flex flex-col items-center justify-between ${
                            isSelected
                              ? "bg-indigo-600 border-indigo-400 text-white shadow-lg scale-105"
                              : `bg-slate-800/60 border-slate-750 text-slate-400 ${item.color} hover:bg-slate-800`
                          }`}
                        >
                          <span className="text-2xl sm:text-3xl mb-1">{item.emoji}</span>
                          <span className="text-[10px] sm:text-xs font-bold leading-tight line-clamp-2">
                            {item.label}
                          </span>
                        </button>
                      );
                    })}
                  </div>
                  <div className="flex justify-between text-[11px] text-slate-500 mt-3 px-1 font-medium">
                    <span>⬅️ ไม่ใช่ฉัน</span>
                    <span>ตรงกับฉันมาก ➡️</span>
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
                    placeholder="พิมพ์คำตอบของคุณที่นี่..."
                    className="w-full bg-slate-800 border border-slate-700 rounded-2xl p-4 text-sm text-white placeholder-slate-500 focus:outline-none focus:border-indigo-500 focus:ring-1 focus:ring-indigo-500"
                  />

                  {currentQ.chips && currentQ.chips.length > 0 && (
                    <div>
                      <div className="text-xs font-bold text-slate-400 mb-2 flex items-center gap-1">
                        <Sparkles size={12} className="text-amber-400" />
                        <span>หรือแตะเพื่อเลือกคีย์เวิร์ดแนะนำ:</span>
                      </div>
                      <div className="flex flex-wrap gap-2">
                        {currentQ.chips.map((chip, idx) => (
                          <button
                            key={idx}
                            type="button"
                            onClick={() => handleChipClick(currentQ.id, chip)}
                            className="bg-slate-800 hover:bg-indigo-950 hover:border-indigo-500 text-slate-300 hover:text-white border border-slate-700 text-xs px-3 py-1.5 rounded-xl transition font-medium text-left"
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
                className="text-xs font-bold text-slate-400 hover:text-white disabled:opacity-30 transition flex items-center gap-1.5 px-4 py-2.5 rounded-xl"
              >
                <ArrowLeft size={16} /> ย้อนกลับ
              </button>

              <div className="flex items-center gap-3">
                <button
                  type="button"
                  onClick={resetQuiz}
                  className="text-xs font-semibold text-slate-500 hover:text-slate-400"
                >
                  ยกเลิก
                </button>

                <button
                  type="button"
                  onClick={handleNext}
                  className="bg-gradient-to-r from-indigo-500 to-blue-600 hover:from-indigo-600 hover:to-blue-700 text-white text-sm font-bold px-6 py-3 rounded-2xl shadow-md hover:shadow-indigo-500/20 transition flex items-center gap-2"
                >
                  <span>{currentStep === activeQuestions.length - 1 ? "ดูผลวิเคราะห์" : "ถัดไป"}</span>
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
            <div className="bg-gradient-to-tr from-indigo-900 via-slate-900 to-purple-900 border border-indigo-500/40 rounded-3xl p-6 sm:p-10 shadow-2xl relative overflow-hidden">
              <div className="absolute -top-10 -right-10 w-48 h-48 bg-indigo-500/20 rounded-full blur-3xl pointer-events-none"></div>

              <div className="flex flex-col sm:flex-row justify-between items-start sm:items-center gap-4 mb-4">
                <div className="inline-flex items-center gap-2 bg-indigo-500/20 border border-indigo-400/30 text-indigo-200 px-3 py-1 rounded-full text-xs font-bold">
                  <Award size={14} className="text-amber-400" />
                  <span>Holland Code: {result.archetype_code}</span>
                </div>

                <button
                  onClick={copyShareResult}
                  className="bg-white/10 hover:bg-white/20 text-white text-xs font-bold px-3.5 py-2 rounded-xl transition flex items-center gap-1.5 backdrop-blur-xs"
                >
                  {copied ? <Check size={14} className="text-emerald-400" /> : <Copy size={14} />}
                  <span>{copied ? "คัดลอกผลลัพธ์แล้ว!" : "แชร์ผลลัพธ์"}</span>
                </button>
              </div>

              <h1 className="text-2xl sm:text-4xl font-black text-white tracking-tight mb-2">
                {result.archetype_title}
              </h1>
              <p className="text-indigo-200/90 text-sm sm:text-base font-medium mb-6">
                {result.archetype_description}
              </p>

              {/* Share Quote Banner */}
              <div className="bg-black/30 border border-white/10 p-4 rounded-2xl text-xs sm:text-sm text-slate-300 italic flex items-center gap-3">
                <Sparkles size={18} className="text-amber-400 flex-shrink-0" />
                <span>"{result.share_quote}"</span>
              </div>
            </div>

            {/* Split Grid: Radar Chart + Personality Analysis */}
            <div className="grid grid-cols-1 md:grid-cols-2 gap-6">
              {/* Radar Chart */}
              <RiasecRadarChart scores={result.riasec_scores} />

              {/* Personality Summary & Strengths */}
              <div className="bg-slate-900/90 border border-slate-800 rounded-3xl p-6 sm:p-8 flex flex-col justify-between">
                <div>
                  <h3 className="text-base font-bold text-white mb-3 flex items-center gap-2">
                    <Brain size={18} className="text-indigo-400" />
                    <span>บทวิเคราะห์ตัวตนและศักยภาพ</span>
                  </h3>
                  <p className="text-xs sm:text-sm text-slate-300 leading-relaxed mb-6 font-normal">
                    {result.personality_summary}
                  </p>

                  <div className="text-xs font-bold text-slate-400 mb-2">จุดเด่นสำคัญของคุณ:</div>
                  <div className="flex flex-wrap gap-2 mb-6">
                    {result.strengths.map((str, idx) => (
                      <span
                        key={idx}
                        className="bg-indigo-500/10 border border-indigo-500/30 text-indigo-300 text-xs px-3 py-1 rounded-xl font-medium"
                      >
                        ✓ {str}
                      </span>
                    ))}
                  </div>
                </div>

                <div className="bg-slate-800/60 p-3.5 rounded-2xl border border-slate-750 text-xs text-slate-300">
                  <span className="font-bold text-indigo-400 block mb-0.5">สภาพแวดล้อมที่เหมาะกับคุณ:</span>
                  <span>{result.ideal_work_environment}</span>
                </div>
              </div>
            </div>

            {/* Top Recommended Careers */}
            <div className="bg-slate-900/90 border border-slate-800 rounded-3xl p-6 sm:p-8">
              <h3 className="text-lg font-bold text-white mb-1 flex items-center gap-2">
                <Briefcase size={20} className="text-sky-400" />
                <span>3 อาชีพที่เหมาะสมที่สุดในอนาคต (Top Career Matches)</span>
              </h3>
              <p className="text-xs text-slate-400 mb-6">
                คัดเลือกโดย AI จากความสอดคล้องระหว่างคะแนนทักษะและแนวโน้มการเติบโตของตลาดงาน
              </p>

              <div className="grid grid-cols-1 sm:grid-cols-3 gap-4">
                {result.top_careers.map((career, idx) => (
                  <div
                    key={idx}
                    className="bg-slate-800/70 border border-slate-750 p-5 rounded-2xl flex flex-col justify-between hover:border-sky-500/50 transition-colors"
                  >
                    <div>
                      <div className="flex justify-between items-center mb-2">
                        <span className="text-[10px] font-bold bg-sky-500/20 text-sky-300 px-2 py-0.5 rounded-md">
                          {career.growth_outlook}
                        </span>
                        <span className="text-xs font-black text-emerald-400">{career.match_percentage}% Match</span>
                      </div>
                      <h4 className="font-bold text-white text-sm mb-2">{career.title}</h4>
                      <p className="text-xs text-slate-400 line-clamp-3 leading-relaxed mb-4">
                        {career.description}
                      </p>
                    </div>

                    <div className="flex flex-wrap gap-1 pt-3 border-t border-slate-700">
                      {career.skills.map((skill, sIdx) => (
                        <span key={sIdx} className="text-[10px] bg-slate-900 text-slate-300 px-2 py-0.5 rounded-md">
                          {skill}
                        </span>
                      ))}
                    </div>
                  </div>
                ))}
              </div>
            </div>

            {/* Recommended Undergraduate Programs (Direct Database Match) */}
            <div className="bg-slate-900/90 border border-slate-800 rounded-3xl p-6 sm:p-8">
              <div className="flex flex-col sm:flex-row justify-between items-start sm:items-center gap-2 mb-6">
                <div>
                  <h3 className="text-lg font-bold text-white flex items-center gap-2">
                    <BookOpen size={20} className="text-pink-400" />
                    <span>หลักสูตรปริญญาตรีที่แนะนำสำหรับคุณ</span>
                  </h3>
                  <p className="text-xs text-slate-400">
                    ดึงตรงจากฐานข้อมูลหลักสูตรมหาวิทยาลัยชั้นนำที่ตรงกับสายอาชีพข้างต้น
                  </p>
                </div>
                <Link
                  href="/"
                  className="text-xs font-bold text-indigo-400 hover:text-indigo-300 flex items-center gap-1"
                >
                  <span>ค้นหาหลักสูตรเพิ่มเติม</span> <ChevronRight size={14} />
                </Link>
              </div>

              {result.recommended_courses && result.recommended_courses.length > 0 ? (
                <div className="grid grid-cols-1 sm:grid-cols-2 gap-4">
                  {result.recommended_courses.map((course) => (
                    <div
                      key={course.id}
                      className="bg-slate-800/60 border border-slate-750 hover:border-pink-500/50 p-5 rounded-2xl flex flex-col justify-between transition-all group"
                    >
                      <div>
                        <div className="flex justify-between items-start gap-2 mb-2">
                          <span className="text-[10px] font-bold bg-pink-500/10 text-pink-300 px-2.5 py-0.5 rounded-full border border-pink-500/20">
                            {course.degree_level || "ปริญญาตรี"}
                          </span>
                          {course.match_score && (
                            <span className="text-xs font-black text-emerald-400 flex items-center gap-1">
                              <Sparkles size={12} /> {course.match_score}% Match
                            </span>
                          )}
                        </div>

                        <h4 className="font-bold text-white text-sm sm:text-base group-hover:text-pink-400 transition-colors leading-snug mb-1">
                          {course.title_th}
                        </h4>
                        {course.title_en && (
                          <p className="text-[11px] text-slate-400 mb-2 truncate">{course.title_en}</p>
                        )}

                        <div className="text-xs text-slate-300 flex items-center gap-1.5 mb-3 font-medium">
                          <Building2 size={14} className="text-slate-500 flex-shrink-0" />
                          <span>{course.university_th}</span>
                          <span className="text-slate-600">•</span>
                          <span className="text-slate-400">{course.faculty_th}</span>
                        </div>
                      </div>

                      <div className="pt-3 border-t border-slate-700/80 flex items-center justify-between">
                        <span className="text-[11px] text-slate-400">
                          {course.tuition_per_semester || "ตามประกาศมหาวิทยาลัย"}
                        </span>
                        {course.website_url ? (
                          <a
                            href={course.website_url}
                            target="_blank"
                            rel="noreferrer"
                            className="text-xs font-bold text-white bg-slate-700 hover:bg-pink-600 px-3 py-1.5 rounded-xl transition flex items-center gap-1"
                          >
                            <span>ดูหลักสูตร</span> <ExternalLink size={12} />
                          </a>
                        ) : (
                          <Link
                            href="/"
                            className="text-xs font-bold text-white bg-slate-700 hover:bg-pink-600 px-3 py-1.5 rounded-xl transition flex items-center gap-1"
                          >
                            <span>ดูในระบบ</span> <ChevronRight size={12} />
                          </Link>
                        )}
                      </div>
                    </div>
                  ))}
                </div>
              ) : (
                <div className="text-center py-6 text-xs text-slate-500 bg-slate-800/40 rounded-2xl border border-slate-800">
                  กำลังอัปเดตหลักสูตรที่ตรงกับสายอาชีพนี้
                </div>
              )}
            </div>

            {/* Growth & Preparation Advice Card */}
            <div className="bg-gradient-to-r from-amber-500/10 via-slate-900 to-indigo-500/10 border border-amber-500/30 rounded-3xl p-6 sm:p-8">
              <h3 className="text-base font-bold text-amber-300 mb-2 flex items-center gap-2">
                <Sparkles size={18} className="text-amber-400" />
                <span>คำแนะนำการเตรียมตัวช่วง ม.ปลาย (Growth Advice)</span>
              </h3>
              <p className="text-xs sm:text-sm text-slate-300 leading-relaxed font-normal">
                {result.growth_advice}
              </p>
            </div>

            {/* Bottom Actions */}
            <div className="flex flex-col sm:flex-row items-center justify-center gap-4 pt-4">
              <button
                onClick={resetQuiz}
                className="bg-slate-800 hover:bg-slate-700 text-slate-200 text-xs font-bold px-6 py-3.5 rounded-2xl border border-slate-700 transition flex items-center gap-2 w-full sm:w-auto justify-center"
              >
                <RefreshCw size={15} />
                <span>ทำแบบประเมินใหม่อีกครั้ง</span>
              </button>

              <Link
                href="/"
                className="bg-gradient-to-r from-indigo-500 to-blue-600 hover:from-indigo-600 hover:to-blue-700 text-white text-xs font-bold px-8 py-3.5 rounded-2xl shadow-lg hover:shadow-indigo-500/20 transition flex items-center gap-2 w-full sm:w-auto justify-center"
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
