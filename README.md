# 🍳 Recipe Generator

A smart recipe generator that helps you create delicious meals based on ingredients you have in your fridge. Built with Streamlit and powered by Google's Gemini AI.<br/>
📹 <a href="https://youtu.be/BGbdfH671M8">Video Demo</a>

## ✨ Features

- Generate recipes based on available ingredients
- Support for various dietary restrictions
- Multiple cuisine and food type options
- Nutritional information for each recipe
- AI-generated food images
- Price estimates for missing ingredients
- Direct links to local grocery stores (NTUC, Sheng Siong)
- Downloadable PDF recipes

## 🚀 Getting Started

### Prerequisites

- Python 3.8+
- pip
- wkhtmltopdf (for PDF generation)

### Installation

1. Clone the repository
```bash
git clone <https://github.com/evonneng05/recipe-generator.git>
```

2. Install dependencies
```bash
pip install -r requirements.txt
```
3. Set up environment variables
Create a .env file in the project root directory and add your Google API key:
GOOGLE_API_KEY=your_api_key_here

4. Run the app
```bash
streamlit run recipe_generator.py
```

### 🛠️ Usage
1. Input your available ingredients in the respective sections:
- Freezer
- Fridge Body
- Cold Storage Area
- Other ingredients
2. Select your dietary restrictions and preferred food type
3. Click "Generate recipes!" to create personalized recipes
4. For each recipe, you can:
- View nutritional information
- See required ingredients and estimated costs
- Follow step-by-step cooking instructions
- Download the recipe as a PDF
- Find missing ingredients with direct links to local grocery stores
