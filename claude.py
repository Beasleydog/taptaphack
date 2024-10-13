import tkinter as tk
from PIL import ImageGrab, Image
import pytesseract
from anthropic import Anthropic
import base64
import io
import keyboard
import json
import os
from dotenv import load_dotenv

load_dotenv()

ANTHROPIC_API_KEY = os.getenv('ANTHROPIC_API_KEY')

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
        if len(self.selections) == 6:
            self.root.quit()

    def run(self):
        self.root.mainloop()
        self.root.destroy()
        return self.selections

def capture_screen(bbox):
    return ImageGrab.grab(bbox)

def ocr_image(image):
    return pytesseract.image_to_string(image)

def encode_image(image):
    buffered = io.BytesIO()
    image.save(buffered, format="PNG")
    return base64.b64encode(buffered.getvalue()).decode('utf-8')

def get_answer_from_claude(image, title, answers):
    client = Anthropic(api_key=ANTHROPIC_API_KEY)
    base64_image = encode_image(image)
    
    completion = client.messages.create(
        model="claude-3-haiku-20240307",
        max_tokens=1000,
        temperature=0.5,
        messages=[
            {
                "role": "user",
                "content": [
                    {
                        "type": "text",
                        "text": f"Given the title '{title}' and the following answer options: {answers}, please determine which one is correct. If the image is necessary to answer the question, analyze it carefully. If the question can be answered without the image, you may disregard it. Please explain your reasoning. After you've determined the answer, end your response with the correct answer on its own line, with this format <ANSWER>answer goes here</ANSWER>. You MUST follow that format."
                    },
                    {
                        "type": "image",
                        "source": {
                            "type": "base64",
                            "media_type": "image/png",
                            "data": base64_image
                        }
                    }
                ]
            }
        ]
    )

    content = completion.content[0].text
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

    while True:
        print("waiting")
        wait_for_space()
        print("running")
        title_bbox, image_bbox, *answer_bboxes = selections

        title_image = capture_screen(title_bbox)
        question_image = capture_screen(image_bbox)
        answer_images = [capture_screen(bbox) for bbox in answer_bboxes]

        title = ocr_image(title_image)
        answers = [ocr_image(img) for img in answer_images]

        correct_answer = get_answer_from_claude(question_image, title, answers)
        print(f"The correct answer is: {correct_answer}")

if __name__ == "__main__":
    main()
