import tkinter as tk
from PIL import Image
import pytesseract
from groq import Groq
import base64
import io
import keyboard
import json
import os
import time
import re
import win32gui
from windows_capture import WindowsCapture
from dotenv import load_dotenv

load_dotenv()

GROQ_API_KEY = os.getenv('GROQ_API_KEY')

pytesseract.pytesseract.tesseract_cmd = r'C:\Program Files\Tesseract-OCR\tesseract.exe'

class ScreenSelector:
    def __init__(self):
        self.root = tk.Tk()
        self.root.attributes('-fullscreen', True)
        self.root.attributes('-alpha', 0.3)
        self.canvas = tk.Canvas(self.root, highlightthickness=0)
        self.canvas.pack(fill=tk.BOTH, expand=True)
        self.canvas.bind('<ButtonPress-1>', self.on_press)
        self.canvas.bind('<B1-Motion>', self.on_drag)
        self.canvas.bind('<ButtonRelease-1>', self.on_release)
        self.start_x = self.start_y = 0
        self.rect = None
        self.selections = []

    def on_press(self, event):
        self.start_x = self.canvas.canvasx(event.x)
        self.start_y = self.canvas.canvasy(event.y)
        self.rect = self.canvas.create_rectangle(
            self.start_x, self.start_y, self.start_x, self.start_y, outline='red'
        )

    def on_drag(self, event):
        cur_x = self.canvas.canvasx(event.x)
        cur_y = self.canvas.canvasy(event.y)
        self.canvas.coords(self.rect, self.start_x, self.start_y, cur_x, cur_y)

    def on_release(self, event):
        end_x = self.canvas.canvasx(event.x)
        end_y = self.canvas.canvasy(event.y)
        self.selections.append((int(self.start_x), int(self.start_y), int(end_x), int(end_y)))
        if len(self.selections) == 7:
            self.root.quit()

    def run(self):
        self.root.mainloop()
        self.root.destroy()
        return self.selections

def capture_window_content(window_title):
    hwnd = win32gui.FindWindow(None, window_title)
    if not hwnd:
        raise Exception(f'Window not found: {window_title}')

    capture = WindowsCapture(window_name=window_title)
    frame = capture.get_latest_frame()

    if frame is not None:
        image = Image.fromarray(frame)
        image.save("capture.png")
        print(f"Image captured and saved as capture.png")
        return image
    else:
        print("Failed to capture the window content.")
        return None

def capture_screen(bbox):
    window_image = capture_window_content("AirDroid Cast v1.2.1.0")
    if window_image:
        return window_image.crop(bbox)
    else:
        return None

def ocr_image(image):
    try:
        custom_config = r'--psm 6'
        return pytesseract.image_to_string(image, config=custom_config)
    except Exception as e:
        print(f"Error during OCR: {e}")
        return ""

def encode_image(image):
    buffered = io.BytesIO()
    image.save(buffered, format="PNG")
    return base64.b64encode(buffered.getvalue()).decode('utf-8')

def get_answer_from_groq(image, title, answers):
    client = Groq(api_key=GROQ_API_KEY)
    base64_image = encode_image(image)
    
    completion = client.chat.completions.create(
        model="llama-3.2-11b-vision-preview",
        messages=[
            {
                "role": "user",
                "content": [
                    {
                        "type": "text",
                        "text": f"Given the title '{title}' and the following answer options: {answers}, please determine which one is correct. If the image is necessary to answer the question, analyze it carefully. If the question can be answered without the image, you may disregard it. Please explain your reasoning. After you've determined the answer, end your response with the correct answer on its own line, with this format <ANSWER>answer goes here</ANSWER>. You MUST follow that format."
                    },
                    {
                        "type": "image_url",
                        "image_url": {
                            "url": f"data:image/png;base64,{base64_image}"
                        }
                    }
                ]
            }
        ],
        temperature=0.5,
        max_tokens=1000,
        top_p=1,
        stream=False,
        stop=None,
    )

    content = completion.choices[0].message.content
    print(content)
    start = content.find("<ANSWER>") + 8
    end = content.find("</ANSWER>")
    if start != -1 and end != -1:
        return content[start:end].strip()
    else:
        return None

def load_or_create_bounding_boxes():
    filename = "bounding_boxes_2.json"
    if os.path.exists(filename):
        with open(filename, "r") as f:
            return json.load(f)
    else:
        selector = ScreenSelector()
        selections = selector.run()
        with open(filename, "w") as f:
            json.dump(selections, f)
        return selections

def wait_for_space():
    print("Waiting for key press...")
    keyboard.wait('space')

def main():
    selections = load_or_create_bounding_boxes()

    previous_question_number = ""
    consecutive_different_text_count = 0

    print("Press space to start")
    wait_for_space()

    while True:
        question_number_bbox, title_bbox, image_bbox, *answer_bboxes = selections

        question_number_image = capture_screen(question_number_bbox)
        current_question_number = ocr_image(question_number_image)

        text = current_question_number.replace(" ", "")
        if re.match(r'Q\d+0f\d+|Q\d+of\d+|Q\d+o0f\d+', text):
            if current_question_number != previous_question_number:
                consecutive_different_text_count += 1
                if consecutive_different_text_count < 5:
                    print(consecutive_different_text_count)

                if consecutive_different_text_count == 5:
                    title_image = capture_screen(title_bbox)
                    answer_images = [capture_screen(bbox) for bbox in answer_bboxes]

                    title = ocr_image(title_image)
                    answers = [ocr_image(img) for img in answer_images]

                    question_image = capture_screen(image_bbox)

                    print(f"Question Number: {current_question_number}")
                    print(f"Question Title: {title}")
                    print(f"Answers: {answers}")
                    
                    if not any(not answer for answer in answers):
                        print(f"New question detected. Processing... {current_question_number}: {title}")
                        
                        correct_answer = get_answer_from_groq(question_image, title, answers)
                        print(f"The correct answer is: {correct_answer}")

                        if correct_answer is not None:
                            correct_index = next((i for i, answer in enumerate(answers) if correct_answer.lower() in answer.lower()), None)
                            
                            if correct_index is not None:
                                print(f"The correct answer is option {correct_index + 1}")
                            else:
                                print("Couldn't match the correct answer to an option.")
                        else:
                            print("No correct answer was returned from the API.")

                    consecutive_different_text_count = 0
                    previous_question_number = current_question_number
            else:
                consecutive_different_text_count = 0
        else:
            print(f"Skipping. Question number format not recognized: {current_question_number}")

        time.sleep(0.1)

capture_window_content("description - Notepad")
exit()

if __name__ == "__main__":
    main()
