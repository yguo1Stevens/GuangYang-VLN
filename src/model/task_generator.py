import speech_recognition as sr
from transformers import BertTokenizer, BertForSequenceClassification
import torch
import json
import pandas as pd
import os
import pyttsx3

# Load the saved model and tokenizer
model_name = 'bert-base-uncased'
tokenizer = BertTokenizer.from_pretrained(model_name)
model = BertForSequenceClassification.from_pretrained('./results')
engine = pyttsx3.init()

# Determine the device and move the model to that device
device = torch.device('cuda') if torch.cuda.is_available() else torch.device('cpu')
model.to(device)

# Load the label_to_idx dictionary and create the idx_to_label dictionary
with open('/home/sunny/catkin_ws/src/project/src/results/label_to_idx.json', 'r') as f:
    label_to_idx = json.load(f)
idx_to_label = {str(idx): label for label, idx in label_to_idx.items()}

engine.say('What Can I do for you?')
engine.runAndWait()

# Initialize the recognizer
recognizer = sr.Recognizer()


# Record the audio
with sr.Microphone() as source:
    print("Please say something...")
    audio_data = recognizer.record(source, duration=8)  # Adjust duration as needed
    print("Recording completed.")

# Convert the audio to text using Google Speech-to-Text
try:
    new_text = recognizer.recognize_google(audio_data)
    print("You said: " + new_text)
    
except sr.UnknownValueError:
    print("Google Speech-to-Text could not understand the audio")
except sr.RequestError:
    print("Could not request results from Google Speech-to-Text; check your network connection")

# Predict the label for the new text
if new_text:
    new_text_encoding = tokenizer(new_text, truncation=True, padding=True, return_tensors='pt').to(device)
    output = model(**new_text_encoding)
    pred_label = output.logits.argmax(-1).item()

    # Convert the predicted index to label
    pred_label_text = idx_to_label[str(pred_label)]
print(f"The predicted label is: {pred_label_text}")

engine.say('You said: ' + new_text + 'and you want: ' + pred_label_text)

# 读取memory file
memory_file_path = '/home/sunny/catkin_ws/src/project/src/memory/memory.csv'
if not os.path.exists(memory_file_path):
    raise FileNotFoundError(f"Cannot find the memory file at {memory_file_path}")

# 读取CSV，并确保object_name是字符串类型
memory_df = pd.read_csv(memory_file_path, dtype={'object_name': str})

# 清除object_name列中的空白字符并将其转换为小写
memory_df['object_name'] = memory_df['object_name'].str.strip().str.lower()

# 将pred_label_text也转换为小写进行匹配
matched_object = memory_df[memory_df['object_name'].str.contains(pred_label_text.lower(), case=False, na=False)]


print(memory_df['object_name'],'\n', pred_label_text.lower())
print('')

if not matched_object.empty:
    # 如果找到匹配项，从matched_object中获取坐标
    position_tuple = matched_object.iloc[0][['x', 'y', 'z']].values

    # 创建并执行roslaunch命令
    os.system(f'roslaunch project move_base_test.launch goal_x:={position_tuple[0]} goal_y:={position_tuple[1]}')
else:
    # 如果没有找到匹配项，打印提示信息
    print("Cannot find the object in the environment")

