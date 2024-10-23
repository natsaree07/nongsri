import pygame
import mysql.connector
from fuzzywuzzy import fuzz
from gtts import gTTS
import os
import time
import speech_recognition as sr

# เชื่อมต่อกับฐานข้อมูล MySQL
mydb = mysql.connector.connect(
    host="localhost",
    user="root",
    password="",
    database="gtts"
)
mycursor = mydb.cursor()

# เริ่มต้น Pygame
pygame.init()
screen_width, screen_height = 800, 600
screen = pygame.display.set_mode((screen_width, screen_height))
pygame.display.set_caption("Nongsri Assistant")
clock = pygame.time.Clock()

# โหลดภาพ PNG ขณะพูดและไม่พูด
idle_image = pygame.image.load("ani1.png").convert_alpha()  # ขณะไม่พูด
speaking_image = pygame.image.load("ani2.png").convert_alpha()  # ขณะพูด

current_image = idle_image  # เริ่มด้วยการแสดงผลขณะไม่พูด
center_x = (screen_width - current_image.get_width()) // 2
center_y = (screen_height - current_image.get_height()) // 2

# ฟังก์ชันพูดข้อความ
def speak(text):
    global current_image, speaking, mode  # อัปเดตสถานะการพูดและโหมด
    output_message = text
    filename = f"speech_{int(time.time())}.mp3"
    tts = gTTS(text=text, lang='th')
    tts.save(filename)
    pygame.mixer.music.load(filename)
    pygame.mixer.music.play()

    current_image = speaking_image  # เปลี่ยนเป็นภาพขณะพูด
    speaking = True  # ตั้งค่าสถานะการพูดเป็น True

    while speaking:  # รอจนกว่าจะเสียงเล่นเสร็จ
        for event in pygame.event.get():
            if event.type == pygame.QUIT:
                pygame.quit()
                mycursor.close()
                mydb.close()
                os.remove(filename)  # ลบไฟล์เสียงเมื่อออกจากโปรแกรม
                exit()

        # แสดงอนิเมชันขณะพูด
        screen.fill((100, 100, 100))  # เติมพื้นหลังให้เป็นสีเทา
        display_image()  # แสดงภาพขณะพูด
        pygame.display.flip()
        clock.tick(10)

        if not pygame.mixer.music.get_busy():  # ตรวจสอบว่าเสียงหยุดเล่นหรือไม่
            speaking = False  # เปลี่ยนสถานะเมื่อเสียงหยุดเล่น
            pygame.mixer.music.stop()
            pygame.mixer.music.unload()
            time.sleep(1)
            os.remove(filename)  # ลบไฟล์เสียงหลังจากเล่นเสร็จ
            current_image = idle_image  # เปลี่ยนกลับไปแสดงภาพขณะไม่พูด
            mode = "None"  # เปลี่ยนกลับไปที่โหมดเริ่มต้น

# ฟังก์ชันรับเสียงจากไมโครโฟน
def listen_speech():
    recog = sr.Recognizer()
    with sr.Microphone() as source:
        print("กำลังฟัง...")
        speak("กำลังฟังค่ะ")
        audio = recog.listen(source)
        try:
            text = recog.recognize_google(audio, language='th')
            print(f"คุณพูดว่า: {text}")
            return text
        except sr.UnknownValueError:
            print("ไม่เข้าใจเสียง")
            return None
        except Exception as e:
            print(f"Error recognizing speech: {e}")
            return None

# ฟังก์ชันดึงข้อมูลจาก MySQL
def fetch_data():
    mycursor.execute("SELECT * FROM gtts_db")
    return mycursor.fetchall()

# ค้นหาข้อความที่คล้ายที่สุด
def find_best_match(user_input, data):
    best_score = 0
    best_match = None
    for row in data:
        db_text = row[1]
        score = fuzz.partial_ratio(user_input, db_text)
        if score > best_score:
            best_score = score
            best_match = row
    if best_score >= 40:
        return best_match
    return None

# ฟังก์ชันแสดงภาพ
def display_image():
    screen.blit(current_image, (center_x, center_y))

# โหลดฟอนต์ที่รองรับภาษาไทย
font_path = "THSarabunNew.ttf"
font_size = 36
font = pygame.font.Font(font_path, font_size)

# วาดปุ่ม
def draw_button(text, x, y, width, height, color):
    pygame.draw.rect(screen, color, (x, y, width, height))
    text_surface = font.render(text, True, (255, 255, 255))
    text_rect = text_surface.get_rect(center=(x + width // 2, y + height // 2))
    screen.blit(text_surface, text_rect)

# ตรวจสอบการคลิกปุ่ม
def button_clicked(mouse_pos, button_rect):
    return button_rect.collidepoint(mouse_pos)

# กำหนดสถานะเริ่มต้น
mode = "None"
input_text = ""
output_message = ""
speaking = False  # สถานะการพูด

# วนลูปหลัก
running = True
while running:
    for event in pygame.event.get():
        if event.type == pygame.QUIT:
            running = False
        elif event.type == pygame.MOUSEBUTTONDOWN:
            mouse_pos = pygame.mouse.get_pos()
            if button_clicked(mouse_pos, pygame.Rect(100, 550, 200, 50)):
                mode = "Chat"
                input_text = ""
                output_message = ""
            elif button_clicked(mouse_pos, pygame.Rect(500, 550, 200, 50)):
                mode = "Talk"
                output_message = ""
            elif button_clicked(mouse_pos, pygame.Rect(300, 550, 200, 50)):
                mode = "None"
                output_message = ""

        # เช็คการกดคีย์ในโหมด Chat
        if mode == "Chat" and event.type == pygame.KEYDOWN:
            if event.key == pygame.K_BACKSPACE:
                input_text = input_text[:-1]
            elif event.key == pygame.K_RETURN:
                if input_text.lower() == "ปิดโปรแกรม" or input_text.lower() == "exit":
                    running = False
                else:
                    data = fetch_data()
                    best_match = find_best_match(input_text, data)
                    if best_match:
                        message = best_match[2]
                        output_message = message
                        print(message)
                        speak(message)
                    else:
                        msg = "น้องศรีไม่พบข้อมูลค่ะ"
                        output_message = msg
                        print(msg)
                        speak(msg)
                    input_text = ""
            else:
                input_text += event.unicode

    # วาดพื้นหลังและตัวละคร
    screen.fill((255, 255, 255))
    display_image()

    # วาดปุ่ม
    draw_button("Chat", 100, 550, 200, 50, (0, 128, 0))
    draw_button("Talk", 500, 550, 200, 50, (0, 0, 128))
    draw_button("Back to None", 300, 550, 200, 50, (128, 0, 0))

    # แสดงโหมดปัจจุบัน
    mode_text = font.render(f"Mode: {mode}", True, (255, 255, 255))
    screen.blit(mode_text, mode_text.get_rect(center=(screen_width // 2, 50)))

    # แสดงกล่องพิมพ์ข้อความในโหมด Chat
    if mode == "Chat":
        pygame.draw.rect(screen, (0, 0, 0), (100, 500, 600, 40))
        input_surface = font.render(input_text, True, (255, 255, 255))
        screen.blit(input_surface, (105, 505))

    # ฟังเสียงในโหมด Talk
    if mode == "Talk" and not speaking:  # ตรวจสอบว่ากำลังพูดหรือไม่
        search_term = listen_speech()
        if search_term:
            if search_term.lower() == "ปิดโปรแกรม" or search_term.lower() == "exit":
                running = False
            elif search_term.lower() == "เปลี่ยนโหมด":  # เปลี่ยนโหมดกลับไปที่ Chat
                mode = "Chat"
                output_message = "กลับไปที่โหมดเริ่มต้นค่ะ"
                speak(output_message)
            else:
                data = fetch_data()
                best_match = find_best_match(search_term, data)
                if best_match:
                    message = best_match[2]
                    output_message = message
                    print(message)
                    speak(message)
                else:
                    msg = "น้องศรีไม่พบข้อมูลค่ะ"
                    output_message = msg
                    print(msg)
                    speak(msg)

    pygame.display.flip()
    clock.tick(10)

pygame.quit()
mycursor.close()
mydb.close()
