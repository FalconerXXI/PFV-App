from dotenv import load_dotenv
from langchain.chains import (create_extraction_chain, create_extraction_chain_pydantic)
from langchain.chat_models import ChatOpenAI
import os

class AiScrapper:
    def __init__(self, html):
        load_dotenv()
        self.html = html
        self.llm = ChatOpenAI(temperature=0, model="gpt-4o-mini", openai_api_key=os.getenv("OPENAI_API_KEY"))
        self.prompt = (
    "You are tasked with extracting computer specifications from a webpage. The webpage contains one computer"
    "Please follow these instructions carefully: \n\n"
    "1. **Extract Information:** Only extract the information that directly pertains to the computer being scanned. "
    "2. **No Extra Content:** Do not include any additional text, comments, or explanations in your response. "
    "3. **Empty Response:** If no information matches the description, return an empty string ('')."
    "4. **Format:** The extracted information should be in the following format in a dictionary that I can manipulate directly: \n\n"
    "Brand: Lenovo (usually Lenovo, HP or Dell)\n"
    "Name: ThinkPad X1 Carbon Gen 9\n"
    "Form Factor: 15 (if its a desktop [Tiny, SFF, Desktop, All-in-One] and if its a notebook use the screensize rounded down to nearest int)\n"
    "Processor: Intel Core i7-10700\n"
    "RAM: 16 (remove GB)\n"
    "Storage: 512 (remove GB)\n"
    "OS: Windows 11 Pro\n"
    "Graphics: NVIDIA GeForce RTX 3080\n"
    "Warranty: 1 (remove year(S))\n"
    "Screen Size: 15 (rounded down to nearest int)\n"
    "Screen Resolution: Full HD\n"
    "Keyboard: English\n"
    "DDR: DDR4 (usually ddr4 or ddr5)\n"
    "WiFi: Yes (Yes or No)\n"
    "Ethernet: Yes (Yes or No)\n"
    "Touch: Yes (Yes or No)\n"
    "4. **Direct Data Only:** Your output should contain only the data that is explicitly requested, with no other text."
)

    

    def parse_with_chatgpt(self):
        chain = self.prompt | self.model
        response = create_extraction_chain()
        return response
    
    