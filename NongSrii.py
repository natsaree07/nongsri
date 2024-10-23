import mysql.connector #ใช้ในการเชื่อมต่อกับ Data base
from fuzzywuzzy import fuzz  # ไลบรารีสำหรับวัดความคล้ายคลึงของข้อความ
from gtts import gTTS #สำหรับแปลงข้อความเป็นเสียง
import pygame #สำหรับสร้างและเล่นไฟล์เสียง
import os #สำหรับจัดการไฟล์
import time #สำหรับหน่วงเวลา
import speech_recognition as sr  # สำหรับโหมดพูด

# เชื่อมต่อกับฐานข้อมูล MySQL
mydb = mysql.connector.connect(
    host="localhost",
    user="root",
    password="",
    database="gtts"
)

mycursor = mydb.cursor()

# เริ่มต้น pygame mixer
pygame.mixer.init()

# ฟังก์ชันสำหรับพูดข้อความ
def speak(text):
    try:
        filename = f"speech_{int(time.time())}.mp3"
        tts = gTTS(text=text, lang='th')
        tts.save(filename)
        pygame.mixer.music.load(filename)
        pygame.mixer.music.play()
        
        while pygame.mixer.music.get_busy():
            pygame.time.Clock().tick(10)

        pygame.mixer.music.stop()
        pygame.mixer.music.unload()  # ยกเลิกการโหลดไฟล์
        time.sleep(1)  # หน่วงเวลาเพื่อให้แน่ใจว่าไฟล์ถูกปล่อย
        os.remove(filename)  # ลบไฟล์หลังจากเล่นเสร็จ
    except Exception as e:
        print(f"เกิดข้อผิดพลาดในการพูด: {e}")


# ฟังก์ชันสำหรับเล่นไฟล์เสียงที่กำหนด
def play_sound(filename):
    try:
        pygame.mixer.music.load(filename)
        pygame.mixer.music.play()
        
        while pygame.mixer.music.get_busy():
            pygame.time.Clock().tick(10)

        pygame.mixer.music.stop()
        pygame.mixer.music.unload()  # ยกเลิกการโหลดไฟล์
        time.sleep(1)  # หน่วงเวลาเพื่อให้แน่ใจว่าไฟล์ถูกปล่อย
        os.remove(filename)  # ลบไฟล์หลังจากเล่นเสร็จ
    except Exception as e:
        print(f"เกิดข้อผิดพลาดในการเล่นไฟล์เสียง: {e}")

# ดึงข้อมูลทั้งหมดจากฐานข้อมูล
def fetch_data():
    mycursor.execute("SELECT * FROM gtts_db")
    return mycursor.fetchall()

# ค้นหาข้อมูลที่คล้ายที่สุดและมีคะแนนไม่น้อยกว่าที่กำหนด
def find_best_match(user_input, data):
    best_score = 0
    best_match = None
    for row in data:
        db_text = row[1]  # สมมติว่าเนื้อหาข้อความอยู่ในคอลัมน์ที่ 1
        score = fuzz.ratio(user_input, db_text)  # คำนวณความคล้ายคลึง
        if score > best_score:
            best_score = score
            best_match = row

    # ตรวจสอบว่าคะแนนความคล้ายคลึง
    if best_score >= 70:
        return best_match, best_score
    return None, best_score

# ฟังก์ชันรับข้อมูลจากการพูด
def listen_speech():
    recog = sr.Recognizer()
    with sr.Microphone() as source:
        print("กำลังฟัง...")
        audio = recog.listen(source)
        try:
            text = recog.recognize_google(audio, language='th')
            print(f"คุณพูดว่า: {text}")
            return text
        except sr.UnknownValueError:
            print("ไม่สามารถเข้าใจเสียง กรุณาลองอีกครั้ง")
            return None
        except sr.RequestError:
            print("ไม่สามารถเชื่อมต่อกับบริการ Google Speech Recognition")
            return None

# ฟังก์ชันเลือกโหมดการทำงาน
def select_mode():
    while True:
        print("=== เลือกโหมดการทำงาน ===")
        print("1: พิมพ์ข้อความ")
        print("2: พูดข้อความ")
        mode = input("เลือกโหมด (1 หรือ 2): ")
        if mode in ["1", "2"]:
            return mode
        else:
            print("กรุณาเลือก 1 หรือ 2 เท่านั้น")

print("=== ระบบค้นหาข้อมูล ===")
print("พิมพ์ 'exit' เพื่อหยุดโปรแกรม")

try:
    mode = select_mode()  # ให้ผู้ใช้เลือกโหมด

    while True:
        # รับข้อความจากผู้ใช้ตามโหมดที่เลือก
        if mode == "1":
            search_term = input("กรุณากรอกข้อความที่ต้องการค้นหา: ")
        else:
            search_term = listen_speech()
            if not search_term:
                continue  # ถ้าไม่มีข้อความ ให้เริ่มใหม่

        if search_term.lower() == 'ปิดโปรแกรม':
            msg = "โปรแกรมหยุดทำงาน"
            print(msg)
            speak(msg)
            break  # ออกจากลูป

        # ดึงข้อมูลจากฐานข้อมูล
        data = fetch_data()

        # ค้นหาชุดข้อมูลที่คล้ายที่สุดและมีความคล้ายคลึง
        best_match, best_score = find_best_match(search_term, data)

        if best_match:
            message = f"{best_match[2]}"
            print(message)
            speak(message)
        else:
            msg = "น้องศรีเองก็ไม่ทราบค่ะ "
            print(msg)
            speak(msg)

except KeyboardInterrupt:
    print("โปรแกรมหยุดทำงาน")

# ปิดการเชื่อมต่อกับฐานข้อมูล
mycursor.close()
mydb.close()
