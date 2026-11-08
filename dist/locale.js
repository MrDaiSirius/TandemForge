"use strict";

const language = (() => {
  try {
    const chosen = localStorage.getItem("tandemforge.language");
    if (chosen === "en" || chosen === "th") return chosen;
  } catch { /* use browser language */ }
  return navigator.language.toLowerCase().startsWith("th") ? "th" : "en";
})();

const english = new Map(`
พื้นที่ทำงานส่วนตัว|Private workspace
ใส่รหัสเข้าแอป เบราว์เซอร์จะจำการเข้าสู่ระบบไว้ 30 วัน|Enter your access code. This browser will remember your session for 30 days.
รหัสเข้าใช้งาน|Access code
เข้าใช้งาน|Unlock workspace
พื้นที่ทำงาน|Workspace
เมนูหลัก|Main navigation
ประมวลผลบนเครื่อง|Runs on this PC
สตูดิโอ|Workspace
ภาพรวม|Overview
กำลังเชื่อมต่อ|Connecting
เตรียมเอนจินบน Windows|Set up engines on Windows
วาง llama-server และไฟล์ที่มากับเอนจินในโฟลเดอร์ bin แล้ววางไฟล์ GGUF ในโฟลเดอร์ models ของ TandemForge จากนั้นเปิดแอปใหม่|Place llama-server and its companion files in TandemForge’s bin folder. Place GGUF files in models, then restart the app.
สำหรับงานภาพ เปิด ComfyUI ที่พอร์ต 8188 พร้อมโมเดล FLUX.2 Klein 4B|For images, start ComfyUI on port 8188 with FLUX.2 Klein 4B installed.
เอนจินแชทพร้อม|Dialogue ready
รอตั้งค่าเอนจินแชท|Dialogue setup needed
หาโมเดลที่เหมาะกับเครื่อง|Find a model for this PC
ดูตัวเลือกตาม RAM, VRAM และพื้นที่เก็บโมเดล|See options based on RAM, VRAM, and model storage.
ตรวจสเปก|Check this PC
กำลังตรวจสเปกบนเครื่อง…|Checking local hardware…
ว่าง|free
ไม่พบข้อมูล VRAM แยก|Dedicated VRAM not detected
พื้นที่ว่างบนไดรฟ์โมเดล|Free space on model drive
ประเมินจากสเปกที่ตรวจได้ การรองรับ GPU ขึ้นกับเอนจินและไดรเวอร์|These estimates use detected hardware. GPU support depends on the engine and driver.
ตอนนี้ RAM ว่างน้อย ให้รอคิวหนักจบก่อนโหลดโมเดล|Available RAM is low. Wait for memory-intensive jobs to finish before loading a model.
ยังไม่มีรุ่นที่แนะนำตามสเปกและ RAM ว่างตอนนี้ ลองปิดโปรแกรมหนักแล้วตรวจใหม่|No model meets the current memory estimate. Close memory-intensive apps and check again.
แนะนำให้เริ่ม|Suggested starting point
ใช้ CPU · ตั้ง GPU layers เป็น 0|CPU mode · Set GPU layers to 0
ขนาดไฟล์|File size
ติดตั้งไฟล์แล้ว|Model file installed
ใช้ในห้องสนทนา ↗|Use in Dialogue ↗
ตรวจพื้นที่ว่างก่อนดาวน์โหลด|Check free disk space before downloading
ดูไฟล์ต้นทาง ↗|View source file ↗
วางไฟล์ GGUF ในโฟลเดอร์โมเดลที่ตั้งไว้ แล้วเปิด TandemForge ใหม่|Put the GGUF file in your model folder, then restart TandemForge.
สตูดิโอ AI บนเครื่องคุณ|YOUR LOCAL AI WORKSPACE
สร้างบนคอม|Create on your PC.
สั่งจากมือถือ|Control from your phone.
คุยกับโมเดล สร้างภาพ และติดตามงานจากพื้นที่เดียว|Chat with local models, create images, and follow your jobs in one workspace.
เริ่มคุย ↗|Start a chat ↗
เปิดห้องสร้างภาพ|Open Image Lab
คิวล่าสุด|Recent jobs
ดูทั้งหมด ↗|View activity ↗
มือถือ|MOBILE ACCESS
เปิดจากโทรศัพท์|Take it to your phone
วิธีเชื่อมต่อแบบส่วนตัว|Connect privately
เข้าสู่ Tailscale บนคอมและมือถือด้วยบัญชีเดียวกัน|Sign in to Tailscale on your PC and phone with the same account.
เปิด Run Phone Access บนคอม แล้วใช้ลิงก์ที่แสดง|Run Phone Access on your PC and copy the displayed link.
เปิดลิงก์บนมือถือและเพิ่มลงหน้าจอหลัก|Open the link on your phone and add it to your home screen.
ห้องสร้างภาพ|Image Lab
สร้างภาพจากข้อความ หรือแนบภาพแล้วบอกสิ่งที่อยากแก้|Generate an image from text, or attach an image and describe the edit.
เลือกงาน|Choose a workflow
ตั้งค่างาน|Job setup
สร้างภาพ|Generate image
ขนาดภาพ|Image size
ลองก่อน · 512 × 512|Draft · 512 × 512
สี่เหลี่ยม · 768 × 768|Square · 768 × 768
แนวตั้ง · 768 × 1024|Portrait · 768 × 1024
แนวนอน · 1024 × 768|Landscape · 1024 × 768
เลือกขนาดภาพจากรายการในแอป|Choose an image size from the app.
กำลังเปิด ComfyUI ที่ติดตั้งไว้|Starting the installed ComfyUI
แก้ไขภาพ|Edit image
ภาพต้นฉบับ|Source image
เอาออก|Remove
คำบรรยาย|Prompt
ส่งเข้าคิว|Add to queue
งานเรนเดอร์ประมวลผลทีละงาน|Render jobs run one at a time
ห้องสนทนา|Dialogue
โหมดงาน|Task mode
กำหนดเอง|Custom
เลือกโหมดเพื่อใช้ค่ากับข้อความที่ส่งจากหน้านี้ ค่าที่บันทึกไว้ยังใช้งานได้ในโหมดกำหนดเอง|Choose a task mode for messages sent from this page. Custom uses your saved settings.
คุยเร็ว|Quick chat
ปิดโหมดคิด เหมาะกับแชทและงานสั้น ๆ|Reasoning is off for short chats and quick tasks.
งานหลายเงื่อนไข|Detailed instructions
ลดความสุ่ม เหมาะกับการทำตามโจทย์ สรุป และช่วยดูโค้ด|Uses lower randomness for following instructions, summaries, and code assistance.
คิดวิเคราะห์|Reasoning
เปิดโหมดคิดและเผื่อโทเคนเพิ่ม คำตอบอาจใช้เวลานานขึ้น|Turns on reasoning and allows extra tokens. Replies may take longer.
อ่านภาพ|Read an image
เลือกโมเดลที่มีตัวอ่านภาพ แล้วแนบภาพจากช่องข้อความ|Chooses a model with a projector. Attach an image in the message box.
ส่งออก JSON|JSON output
จำกัดคำตอบให้เป็น JSON object เหมาะกับงานที่ต้องนำข้อมูลไปใช้ต่อ|Constrains replies to a JSON object for use in other tools.
โมเดลนี้ต้องมีไฟล์ตัวอ่านภาพที่ตรงกันก่อนแนบภาพ|Add the matching projector file to attach an image with this model.
การแนบภาพถูกปิดสำหรับโมเดลนี้|Image attachments are disabled for this model.
เพิ่มไฟล์ตัวอ่านภาพที่ตรงกับโมเดลนี้ก่อนแนบภาพ|Add the matching projector file before attaching an image.
เลือกโหมดงานจากรายการในแอป|Choose a task mode from the app.
โหมดงานนี้ยังไม่มีโมเดลที่รองรับ|This task mode has no compatible model installed.
เลือกโมเดลที่ตรงกับโหมดงาน หรือลองโหมดกำหนดเอง|Choose the model for this task mode or switch to Custom.
Gemma 12B เหมาะกับ Agent ที่เรียกเป็นครั้ง ๆ และโหลดเร็วกว่า 35B ในชุดทดสอบของเรา|Gemma 12B is suited to occasional Actions and loaded faster than 35B in our tests.
35B A3B เหมาะกับงานต่อเนื่องเมื่อโมเดลโหลดแล้ว และใช้ RAM มากกว่า Gemma 12B|35B A3B is suited to consecutive jobs once loaded and uses more RAM than Gemma 12B.
คัดลอกคำตอบ|Copy reply
คัดลอกแล้ว|Copied
คัดลอกไม่ได้ในเบราว์เซอร์นี้|Could not copy in this browser
คุย ร่างเรื่อง เขียนโค้ด หรือแนบภาพให้โมเดลอ่าน|Chat, draft stories, write code, or ask about an image.
โมเดล|Model
ตั้งค่าโมเดล|Model preferences
แชทใหม่|New chat
ข้อความ|Message
พิมพ์ข้อความถึงโมเดล…|Write a message to the model…
แนบภาพ|Attach image
ส่งข้อความ ↗|Send message ↗
งานอัตโนมัติ|Actions
พิมพ์สิ่งที่อยากให้ทำ แล้วตรวจคำสั่งก่อนอนุมัติ|Describe a task and review the proposed action before approval.
งานใหม่|New action
โมเดล Agent|Agent model
คำสั่ง|Instruction
เช่น เขียนสตอรีบอร์ด 3 ช็อตแล้วบันทึกเป็น storyboard.md|For example, write a three-shot storyboard and save it as storyboard.md.
ตรวจคิว · อ่านหรือเขียนไฟล์ในพื้นที่ Agent · ส่งงานสร้างสื่อ|Check the queue, read or write workspace files, or submit an image job.
เสนอแผน ↗|Propose action ↗
ประวัติ Agent|Action history
กิจกรรมและผลงาน|Activity
ติดตามงานที่ส่งจากแอป เปิดไฟล์ และใช้ภาพทำงานต่อ|Track jobs, open outputs, and reuse images.
ตั้งค่าพื้นที่ทำงาน|Preferences
กำหนดการตอบ การใช้ RAM / VRAM และสิทธิ์ Agent|Tune replies, memory use, and action permissions.
ขอบเขตการตั้งค่า|Settings scope
ชุดค่าที่แนะนำ|Recommended presets
ใส่ค่าชุดนี้|Load preset
คืนค่า|Reset
โหลดค่าล่าสุด|Reload saved values
บันทึกการตั้งค่า|Save preferences
ทดสอบโมเดล|Test model
ส่งข้อความสั้นด้วยค่าที่บันทึกไว้และดูจำนวนโทเคนที่ใช้|Send a short prompt with saved settings and see its token count.
ส่งข้อความทดสอบ ↗|Send test prompt ↗
สนทนา|Dialogue
สร้าง|Create
กิจกรรม|Activity
ตั้งค่า|Preferences
สร้างภาพจากข้อความ|Generate an image from a prompt
แนบภาพแล้วบอกว่าต้องการแก้ตรงไหน|Attach an image and describe what to change
เชื่อมต่อแอปไม่สำเร็จ|Could not connect to TandemForge.
ไม่ใช้ Persona|No persona
เลือกบทบาทเพื่อกำหนดรูปแบบคำตอบของข้อความถัดไป|Choose a persona for your next message.
โมเดลแนะนำ|Suggested models
ComfyUI ออนไลน์|ComfyUI online
ComfyUI ออฟไลน์|ComfyUI offline
ยอดจองหน่วยความจำ |Committed memory: 
เสร็จแล้ว|Completed
มีข้อผิดพลาด|Failed
ยกเลิกแล้ว|Cancelled
กำลังทำงาน|Running
ผลลัพธ์ |Output 
ดาวน์โหลด ↓|Download ↓
ใช้แก้ภาพ|Use for editing
ลบประวัติ|Remove from history
ยกเลิก|Cancel
ลบประวัติรายการนี้ออกจาก TandemForge?|Remove this entry from TandemForge history?
ลบประวัติรายการนี้แล้ว|Entry removed.
คิวว่าง|Queue is clear
งานที่ส่งจะปรากฏที่นี่|Submitted jobs will appear here.
ยังไม่มีงานในแอป ลองส่งงานจากแท็บสร้าง|No jobs yet. Try submitting one from Image Lab.
ยกเลิกงาน|Cancel job
เริ่มแชทได้เลย เช่น ให้ช่วยร่างเรื่องหรืออธิบายโค้ด|Start a conversation. Try outlining a story or asking about code.
ข้อความการคิด|Reasoning
ลบข้อความคู่นี้|Remove this exchange
ลบข้อความนี้|Remove this message
กำลังรอคำตอบ…|Waiting for a reply…
ข้อผิดพลาด · |Error · 
ยังไม่มีประวัติ Agent|No actions yet.
คำสั่งที่เสนอ|Proposed action
สถานะ Agent|Action status
ส่งงานเข้าคิวแล้ว|Job added to the queue.
อนุมัติให้ทำงาน|Approve action
สิทธิ์สำหรับคำสั่งนี้ปิดอยู่ในหน้าตั้งค่า|This action is disabled in Preferences.
ไฟล์ภาพต้องไม่เกิน 16 MB|Image files must be 16 MB or smaller.
เลือกภาพต้นฉบับก่อนส่งงาน|Choose a source image before submitting.
ยังไม่มีโมเดล|No local model found
เลือกชุดตามงานเพื่อใส่ค่าในฟอร์ม|Choose a preset to fill in the form.
ทั่วไป|General
ปรับเฉพาะโมเดล · |Override for this model · 
มีการแก้ไขที่ยังไม่ได้บันทึก|Unsaved changes
ค่าปัจจุบัน|Saved values
ปรับเฉพาะโมเดล|Override for this model
ใช้เป็นค่าเริ่มต้นร่วมกัน ค่าที่บันทึกมีผลกับงานที่ส่งหลังจากนี้|Saved defaults apply to new jobs.
ตัวเลือกที่ไม่ได้เปิดปรับเฉพาะโมเดลจะใช้ค่ากลาง|Settings without an override inherit the shared defaults.
คืนค่าเริ่มต้น|Restore defaults
ใช้ค่ากลางทั้งหมด|Clear all overrides
ค่ากลาง|Shared defaults
เลือกชุดค่าตามงาน|Select a preset
ใส่ค่าชุดนี้ในฟอร์มแล้ว · ตรวจค่าแล้วกดบันทึก|Preset loaded. Review the values, then save.
ชุดนี้ตรงกับค่าที่บันทึกอยู่|This preset matches the saved settings.
โหลดค่าล่าสุดแล้ว|Reloaded saved settings.
บันทึกแล้ว · ใช้กับงานถัดไป|Saved. New jobs use these settings.
กำลังส่งข้อความทดสอบ…|Sending a test prompt…
ตอบเพียงคำว่า พร้อม|Reply with just the word Ready.
 โทเคน| tokens
 ตัวเลือก| options
 เวิร์กโฟลว์| workflows
โมเดลเริ่มต้นสำหรับแชท|Default chat model
โมเดลเริ่มต้นสำหรับ Agent|Default action model
ธีม|Theme
มืด|Dark
สว่าง|Light
ตามเครื่อง|System
กด Enter เพื่อส่งแชท|Send with Enter
Shift+Enter ขึ้นบรรทัดใหม่|Use Shift+Enter for a new line.
คำสั่งประจำสำหรับแชท|Standing instructions
เช่น ตอบภาษาไทยและอธิบายโค้ดพร้อมตัวอย่าง|For example, explain code with concise examples.
จำนวนข้อความย้อนหลัง|Previous messages to include
0 ใช้เฉพาะข้อความล่าสุด|0 includes only the latest message.
การตอบและการสุ่ม|Responses and sampling
0 ปิด Top K|0 disables Top K.
โทเคนคำตอบสูงสุด|Maximum reply tokens
0 คำนวณจากขนาด Context|0 derives a limit from the context size.
-1 สุ่มใหม่ทุกครั้ง|-1 uses a random seed each time.
ช่วงย้อนหลังสำหรับ Repeat penalty|Repetition window
ข้อความที่ใช้หยุดคำตอบ|Stop sequences
หนึ่งข้อความต่อบรรทัด|One sequence per line.
ใช้แคชข้อความก่อนหน้า|Reuse prompt cache
เอนจินและหน่วยความจำ|Engine and memory
Context (โทเคน)|Context (tokens)
จำนวนเลเยอร์บน GPU|GPU layers
-2 ปรับให้พอดีอัตโนมัติ · -1 ทั้งหมด · 0 ใช้ CPU · จำนวนบวกกำหนดเอง|-2 automatic · -1 all · 0 CPU · positive values set the layer count
พื้นที่สำรอง VRAM (MiB)|VRAM headroom (MiB)
ใช้เมื่อเลือก GPU แบบอัตโนมัติ|Used with automatic GPU layers.
-1 อัตโนมัติ|-1 lets the engine decide.
CPU threads ตอนอ่านพรอมป์|Prompt processing threads
-1 ใช้ค่า CPU threads|-1 follows the CPU threads setting.
อัตโนมัติ|Automatic
เปิด|On
ปิด|Off
ย้าย KV cache ไป GPU|Offload KV cache to the GPU
โหมดโหลดโมเดล (mmap / mlock)|Model loading (mmap / mlock)
โหลดเต็มเข้า RAM|Load fully into RAM
วอร์มโมเดลตอนเปิด|Warm up the model on load
คืนหน่วยความจำแชทเมื่อว่าง (วินาที)|Unload idle models after (seconds)
0 คืนทันทีเมื่อคิวว่าง|0 unloads the model when the queue is clear.
เวลารอคำตอบสูงสุด (วินาที)|Reply timeout (seconds)
ขอคืน VRAM จาก ComfyUI ก่อนโหลดแชท|Ask ComfyUI to free VRAM before loading chat
การคิดและภาพ|Reasoning and vision
โหมดคิด|Reasoning mode
ตามโมเดล|Model default
งบโทเคนการคิด|Reasoning token budget
-1 ใช้ค่าเอนจิน · ทำงานกับโมเดลที่รองรับ|-1 uses the engine default on compatible models.
แสดงข้อความการคิดที่โมเดลส่งกลับ|Show reasoning returned by the model
อนุญาตให้แนบภาพ|Allow image attachments
ย้ายตัวอ่านภาพไป GPU|Offload the vision projector to the GPU
โทเคนภาพขั้นต่ำ|Minimum image tokens
-1 ใช้ค่าเอนจิน|-1 uses the engine default.
โทเคนภาพสูงสุด|Maximum image tokens
Temperature ของ Agent|Action temperature
โทเคนสำหรับแผน Agent|Action plan token budget
เปิด Agent|Enable Actions
อนุญาตตรวจสถานะเครื่อง|Allow status checks
อนุญาตดูรายการและอ่านไฟล์|Allow listing and reading workspace files
อนุญาตเขียนไฟล์ใหม่|Allow creating new files
อนุญาตส่งงานสร้างสื่อ|Allow submitting image jobs
แชททั่วไป · สมดุล|Everyday chat · Balanced
เริ่มจาก Qwen 9B ใช้คุย สรุป และแปลในชีวิตประจำวัน|Start with Qwen 9B for everyday chat, summaries, and translation.
คุยเล่น · คำตอบสั้น|Casual chat · Short replies
คุยเป็นกันเอง ตอบสั้นลง และส่งบริบทล่าสุดเพิ่มอีกเล็กน้อย|Shorter, casual replies with more recent context.
คุยเล่น · สายปากจัด|Casual chat · Sharp tongues
คู่กับ Persona สายปากจัด ลอง Qwen 9B Abliterated หรือ Orca 27B Uncensored|Pair with a sharp-tongued persona and a compatible model.
เขียนโค้ดและแก้บั๊ก|Coding and debugging
ลดความสุ่มและเผื่อพื้นที่ให้ตัวอย่างโค้ดกับคำอธิบาย|Lower randomness with room for code examples and explanations.
เขียนบท นิยาย และสวมบท|Scripts, fiction, and roleplay
เพิ่มความหลากหลายและความยาวสำหรับฉาก บทพูด และสตอรีบอร์ด|More variety and space for scenes, dialogue, and storyboards.
คิดวิเคราะห์หลายขั้น|Multi-step analysis
เปิดโหมดคิดให้โมเดลที่รองรับ พร้อมงบคิด 512 โทเคนและเวลารอเพิ่ม|Reasoning on compatible models, a 512-token budget, and more time.
อ่านภาพและสกรีนช็อต|Images and screenshots
เปิดแนบภาพและใช้ GPU กับตัวอ่านภาพ เริ่มลองกับ Qwen 9B|Enable image attachments and GPU vision for a compatible model.
ประหยัดหน่วยความจำ · สลับ ComfyUI|Lower memory · Switch between apps
ใช้ Context 3,072 ลดขนาด Batch และคืนโมเดลแชทเมื่อว่าง 30 วินาที|Use a 3,072-token context, smaller batches, and a 30-second idle unload.
อ่านข้อความยาว · Context 8,192|Long input · 8,192 context
สำหรับโค้ดหรือบทที่ยาวขึ้น เริ่มทดสอบกับ 9B และดูการใช้หน่วยความจำ|For longer code or scripts. Try 9B first and monitor memory use.
Agent · วางแผนและสั่งงาน|Actions · Planning
ลดความสุ่มของแผน และให้ Agent มีพื้นที่เขียนคำสั่ง 900 โทเคน|Reduce randomness and allow up to 900 tokens for an action plan.
คุยเล่น · เพื่อนและคู่คุย|Casual chat · Companions
คุยเล่น · สายมุก เกม และจินตนาการ|Casual chat · Comedy and games
ผู้ช่วยทั่วไป|General assistants
นิยาย บท และบทบาทสมมติ|Fiction, scripts, and roleplay
ภาพ วิดีโอ และเสียง|Images, video, and sound
โค้ด ข้อมูล และงานเทคนิค|Code, data, and technical work
เรียนรู้ ภาษา และค้นคว้า|Learning, languages, and research
เอกสาร งาน และการวางแผน|Writing, work, and planning
รอคิว|Queued
กำลังเริ่ม|Starting
กำลังโหลด |Loading 
กำลังวิเคราะห์คำสั่ง|Planning the action
กำลังตอบ|Generating a reply
กำลังส่งเข้า ComfyUI|Submitting to ComfyUI
กำลังเชื่อมต่อ ComfyUI ใหม่|Reconnecting to ComfyUI
ComfyUI กำลังสร้างสื่อ|ComfyUI is generating
รอในคิว ComfyUI|Queued in ComfyUI
รอหยุดงานเนื่องจากหน่วยความจำใกล้เต็ม|Stopping because system memory is nearly full
รหัสไม่ตรง ลองดูรหัสที่หน้าต่างบนคอม|Incorrect code. Check the access code on your PC.
ลองใหม่อีกครั้งในหนึ่งนาที|Try again in one minute.
ใส่รหัสเข้าแอปก่อน|Unlock the workspace first.
ไม่พบงาน|Job not found.
การแนบภาพถูกปิดสำหรับโมเดลนี้|Image attachments are disabled for this model.
ไม่พบเอนจินหรือไฟล์โมเดลที่เลือก|The local engine, selected model, or vision projector is missing.
โหลดโมเดลแชทไม่สำเร็จ ดูรายละเอียดใน chat-engine.log|Model loading failed. See chat-engine.log for details.
ComfyUI กำลังทำงานจากคิวอื่น รอให้คิวว่างแล้วลองใหม่|ComfyUI is busy. Try again when its queue is clear.
เอนจินแชทหยุดตอบระหว่างประมวลผล|The local chat engine stopped responding.
โมเดลไม่ได้ส่งคำตอบ|The model returned no reply.
รองรับภาพ PNG, JPEG และ WebP|Supported images: PNG, JPEG, and WebP.
ไม่พบไฟล์ผลงาน|Output file not found.
ไม่พบภาพที่อัปโหลด|Uploaded image not found.
เลือกไฟล์ภาพเพื่อใช้เป็นต้นฉบับ|Choose an image as the source.
เลือกภาพใหม่แล้วลองอีกครั้ง|Choose another image and try again.
หยุดงานเมื่อยอดจองหน่วยความจำใกล้เต็มต่อเนื่อง|Stopped because system memory stayed nearly full.
ComfyUI หยุดงานหรือสร้างสื่อไม่สำเร็จ|ComfyUI stopped or failed to generate an output.
ComfyUI จบงานแล้ว แต่ไม่พบไฟล์ผลลัพธ์ในโฟลเดอร์แอป|ComfyUI finished, but no output was available to import.
ไม่พบงานในคิวหรือประวัติ ComfyUI|The job was not found in the ComfyUI queue or history.
ติดต่อ ComfyUI ไม่ได้ระหว่างติดตามงาน|Lost contact with ComfyUI while following the job.
เลือกโมเดลแชท|Select a chat model.
เลือก Persona จากรายการในแอป|Select a persona from the list.
สิทธิ์ของ Agent สำหรับคำสั่งนี้ถูกปิดในหน้าตั้งค่า|This action is disabled in Preferences.
เปิดสิทธิ์ให้ Agent อย่างน้อยหนึ่งรายการในหน้าตั้งค่า|Enable at least one action in Preferences.
ตรวจสถานะ ComfyUI และคิว|Check ComfyUI and its queue
ดูรายการไฟล์ในพื้นที่ Agent|List workspace files
อ่านไฟล์ในพื้นที่ Agent|Read a workspace file
บันทึกไฟล์ใหม่ในพื้นที่ Agent|Create a new workspace file
ส่งงานสร้างสื่อเข้า ComfyUI|Submit an image job to ComfyUI
พื้นที่ Agent ยังว่าง|The action workspace is empty.
ออนไลน์|online
ออฟไลน์|offline
บันทึก |Saved 
 แล้ว|.
ค่าตั้งถูกแก้จากอีกหน้าจอ กรุณาโหลดค่าล่าสุด|Settings changed in another window. Reload saved values.
โทเคนคำตอบสูงสุดต้องน้อยกว่า Context หรือใช้ 0 สำหรับอัตโนมัติ|Maximum reply tokens must be below context size, or 0 for automatic.
Microbatch size ต้องไม่เกิน Batch size|Microbatch size must not exceed batch size.
KV cache V แบบ quantized ต้องเปิด Flash Attention|Quantized V cache requires Flash Attention to be on.
โทเคนภาพขั้นต่ำต้องไม่เกินโทเคนภาพสูงสุด|Minimum image tokens must not exceed maximum image tokens.
ลบประวัติได้เมื่องานเสร็จหรือยกเลิกแล้ว|Finish or cancel the job before removing it.
คำสั่งนี้ถูกอนุมัติแล้วหรือยังไม่พร้อม|This action is already approved or is still running.
ยกเลิกได้เฉพาะงานที่ยังรอคิว|Only queued jobs can be cancelled.
ไม่พบเส้นทาง|Route not found.
ไม่พบหน้า|Page not found.
ไม่พบหมวดประวัติ|History category not found.
ต้นทางคำขอไม่ตรงกับแอป|Request origin does not match TandemForge.
ข้อมูลมีขนาดเกินกำหนดหรือว่างเปล่า|The request body is empty or exceeds the size limit.
คำขอต้องเป็น JSON|The request must be JSON.
ข้อมูลไม่ถูกต้อง|Invalid request.
ข้อมูลตั้งค่าต้องเป็น JSON object|Settings must be a JSON object.
เลือกค่ากลางหรือโมเดลที่รองรับ|Choose shared defaults or an installed model.
รหัสรายการประวัติไม่ถูกต้อง|Invalid history entry ID.
ที่อยู่แอปไม่ถูกต้อง|Invalid TandemForge host.
เลือกประเภทงานที่รองรับ|Choose an available workflow.
ประวัติแชทไม่ถูกต้อง|Invalid conversation history.
ใช้ชื่อไฟล์สั้น ๆ เช่น storyboard.md|Use a short filename such as storyboard.md.
ไฟล์ต้องอยู่ในพื้นที่ Agent|The file must stay in the action workspace.
Agent ส่งแผนไม่ครบ ลองเพิ่มโทเคนสำหรับแผน Agent หรือย่อคำสั่ง|The action plan was incomplete. Increase its token budget or shorten the request.
Agent รองรับตรวจสถานะ ดูไฟล์ อ่านไฟล์ เขียนไฟล์ใหม่ และส่งงานสร้างสื่อ|Actions can check status, list or read files, create files, and submit image jobs.
ข้อความสำหรับคำสั่ง Agent ต้องมีความยาว 1–5,000 ตัวอักษร|Action content must be 1–5,000 characters.
เลือกงานสร้างจากข้อความ หรือแนบภาพในแท็บสร้าง|Choose text-to-image or attach an image in Image Lab.
โมเดลใช้งบโทเคนครบระหว่างคิด ลองเพิ่มโทเคนคำตอบหรือลดงบการคิด|The model used its reply budget while reasoning. Raise the reply budget or lower the reasoning budget.
`.trim().split("\n").map((line) => line.split("|")));

function t(value) {
  if (language !== "en" || typeof value !== "string") return value;
  return english.get(value) || value;
}

function localMessage(value) {
  if (language !== "en" || typeof value !== "string") return value;
  if (value.startsWith("กำลังโหลด ")) return t("กำลังโหลด ") + value.slice("กำลังโหลด ".length);
  if (/^ใส่ข้อความ 1–[\d,]+ ตัวอักษร$/.test(value)) return "Enter " + value.match(/1–[\d,]+/)[0] + " characters.";
  const status = value.match(/^ComfyUI (ออนไลน์|ออฟไลน์) · กำลังทำ (\d+) · รอ (\d+)$/);
  if (status) return "ComfyUI " + t(status[1]) + " · Running " + status[2] + " · Queued " + status[3];
  const saved = value.match(/^บันทึก (.+) แล้ว$/);
  if (saved) return "Saved " + saved[1] + ".";
  const range = value.match(/^ค่าของ (.+) อยู่นอกช่วงที่รองรับ$/);
  if (range) return t(range[1]) + " is outside the supported range.";
  const scope = value.match(/^ตัวเลือกนี้ใช้กับขอบเขตที่เลือกไม่ได้ \((.+)\)$/);
  if (scope) return "This setting cannot be changed for the selected scope (" + scope[1] + ").";
  return t(value);
}

function initLanguage() {
  document.documentElement.lang = language;
  if (language === "en") {
    const walker = document.createTreeWalker(document.body, NodeFilter.SHOW_TEXT);
    while (walker.nextNode()) {
      const node = walker.currentNode;
      const key = node.data.trim();
      if (english.has(key)) node.data = node.data.replace(key, t(key));
    }
    for (const element of document.querySelectorAll("[placeholder],[aria-label]")) {
      for (const name of ["placeholder", "aria-label"]) {
        if (element.hasAttribute(name)) element.setAttribute(name, t(element.getAttribute(name)));
      }
    }
  }
  for (const button of document.querySelectorAll("[data-language]")) {
    button.setAttribute("aria-pressed", String(button.dataset.language === language));
    button.addEventListener("click", () => {
      if (button.dataset.language === language) return;
      localStorage.setItem("tandemforge.language", button.dataset.language);
      location.reload();
    });
  }
}
