# 🛠️ แนะนำ Agent Skills & MCP Servers สำหรับระบบ Thai EduCenter

จากการค้นคว้าและทำความเข้าใจสถาปัตยกรรมระบบ **Thai EduCenter & Advisor Match** ของเรา (Next.js 16, FastAPI, PostgreSQL + PgVector บน Supabase, Gemini API, Web Scraping) และอ้างอิงจากแหล่งข้อมูลที่น่าเชื่อถือระดับโลก (เช่น *Official MCP Registry, Awesome MCP Servers, AgenticSkills.io*) 

เพื่อให้ AI Agent (ทั้งในฝั่งผู้ช่วยนักพัฒนาและตัวระบบเอง) ทำงานได้อย่างมีประสิทธิภาพและสอดคล้องกับ Tech Stack ของเรา ขอเสนอรายชื่อ **Agent Skills / MCP Servers** ที่ควรพิจารณาติดตั้งดังนี้ครับ:

---

## 1. กลุ่มฐานข้อมูลและ Vector Search (Database & Vector Store)
เนื่องจากระบบเราใช้ PostgreSQL ร่วมกับ PgVector ในการทำ Semantic Search การให้ Agent สามารถเข้าถึงโครงสร้างข้อมูลโดยตรงจะช่วยให้การพัฒนารวดเร็วขึ้นมาก

*   **Skill/Server ที่แนะนำ:** `@modelcontextprotocol/server-postgres` หรือ `SchemaFlow`
*   **แหล่งที่มา:** [Official MCP Servers Repository](https://github.com/modelcontextprotocol/servers)
*   **ทำไมถึงควรติดตั้ง:** 
    *   ช่วยให้ AI Agent สามารถตรวจสอบ Schema ของตาราง `faculties` และ `courses` ได้ทันที
    *   สามารถทดสอบ Query การทำ `cosine_distance` ของ PgVector ได้โดยตรง 
    *   ลดข้อผิดพลาดในการเขียน SQL Query และช่วย Debug ข้อมูลใน Supabase แบบ Real-time (ในโหมด Read-only เพื่อความปลอดภัย)

## 2. กลุ่ม Web Scraping และ Browser Automation
ระบบของเรามีการดึงข้อมูล (Scraping) หลักสูตรและโปรไฟล์อาจารย์จากมหาวิทยาลัยต่างๆ (เช่น `cmu_scraper`)

*   **Skill/Server ที่แนะนำ:** `@modelcontextprotocol/server-puppeteer` หรือ `ScrapeGraphAI`
*   **แหล่งที่มา:** [Awesome MCP Servers](https://github.com/wong2/awesome-mcp-servers) / [AgenticSkills](https://agenticskills.io/)
*   **ทำไมถึงควรติดตั้ง:**
    *   เครื่องมือพื้นฐานอย่าง `BeautifulSoup` หรือ `requests` อาจเจอปัญหาเมื่อเว็บไซต์เป้าหมายเปลี่ยนเป็น SPA (Single Page Application) หรือมีระบบป้องกัน
    *   การติดตั้ง Skill ฝั่ง Browser Automation จะช่วยให้ Agent สามารถจำลองการเปิดเบราว์เซอร์, Render JavaScript, ดึง CSS Selectors ที่ถูกต้อง และแก้บั๊กการ Scraping ข้อมูลหน้าเว็บอาจารย์ได้อย่างแม่นยำ

## 3. กลุ่มการค้นหาข้อมูลวิชาการและการเชื่อมต่อภายนอก (Web & Scholar Search)
ฟีเจอร์หลักของเราคือการจับคู่งานวิจัยและโปรไฟล์อาจารย์ (Advisor Match) ซึ่งปัจจุบันใช้ SerpApi สำหรับ Google Scholar

*   **Skill/Server ที่แนะนำ:** `@modelcontextprotocol/server-brave-search` (สำหรับการค้นหาทั่วไป) หรือ `SerpApi Skill / Google Scholar MCP`
*   **แหล่งที่มา:** [MCP Registry](https://registry.modelcontextprotocol.io/) 
*   **ทำไมถึงควรติดตั้ง:**
    *   เพิ่มความสามารถให้ AI Agent ค้นหาและดึงข้อมูลอัปเดตล่าสุดจากอินเทอร์เน็ตได้โดยตรง เพื่อใช้ในการปรับจูน Prompt ของระบบ AI Match Explanation
    *   ช่วยทดสอบการเชื่อมต่อ API ของ SerpApi ว่าข้อมูล publications ถูกดึงมาได้อย่างถูกต้องก่อนเขียนโค้ดลงไปในระบบจริง

## 4. กลุ่มการจัดการ Codebase และ Monorepo
ระบบของเราเป็น Monorepo ที่แบ่งเป็น `/frontend` และ `/backend` ชัดเจน

*   **Skill/Server ที่แนะนำ:** `@modelcontextprotocol/server-git` และ `@modelcontextprotocol/server-filesystem`
*   **แหล่งที่มา:** [Official MCP Servers Repository](https://github.com/modelcontextprotocol/servers)
*   **ทำไมถึงควรติดตั้ง:**
    *   ช่วยให้ AI Agent เข้าใจภาพรวมของการทำงานข้ามโฟลเดอร์ สามารถอ่านประวัติ Git Commit และเช็คการเปลี่ยนแปลง (Diff) ของโค้ดได้แม่นยำขึ้น
    *   บังคับใช้กฎระเบียบต่างๆ ที่เขียนไว้ใน `AGENTS.md` ได้อย่างเคร่งครัดเวลาวิเคราะห์ไฟล์จำนวนมาก

## 5. (เพิ่มเติม) AI Agent Skills สำหรับตัวระบบ (Educational Platform)
หากมองในมุมมองการเพิ่มขีดความสามารถของ **ระบบ Thai EduCenter เอง** เพื่อให้เป็น AI Advisor ที่เก่งขึ้น ควรพิจารณา Skills เพิ่มเติมในอนาคตดังนี้:
*   **Calendar / Scheduling Skill:** (เช่น Google Calendar MCP) เพื่อให้ระบบสามารถช่วยนัดหมายเวลาคุยกับอาจารย์ได้ทันที หลังจากที่ AI ร่างอีเมล (Cold Email) เสร็จแล้ว
*   **Document Analysis Skill:** (เช่น PDF Parser) เพื่อให้นักศึกษาสามารถอัปโหลดไฟล์โครงร่างวิทยานิพนธ์ (Proposal PDF) แล้วให้ AI ดึงข้อมูลไปทำ Semantic Matching ได้แม่นยำยิ่งขึ้น

---

> [!TIP]
> **ข้อเสนอแนะในการดำเนินการ:** ตามคำสั่งของคุณ ผมจะ **ไม่ทำการติดตั้งเครื่องมือเหล่านี้เอง** แต่คุณสามารถเลือกติดตั้ง MCP Servers เหล่านี้ได้ผ่านทาง Configuration File ของ Client ที่คุณใช้งาน (เช่น Antigravity, Cursor, หรือ Claude Desktop) หรือใช้ผ่าน CLI ของ Agent ได้เลยครับ
