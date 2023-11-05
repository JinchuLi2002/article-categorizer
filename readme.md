# Article Categorizer

## Overview
Article Categorizer is an end-to-end solution designed to categorize articles automatically into predefined categories. Using the power of EvaDB and OpenAI's language models, the tool provides a seamless experience from article ingestion to category assignment.

## Features
- Utilization of machine learning models for summarization.
- Utilization of embedding similarity search for category matching.
- Ability to refine category matches using OpenAI's GPT model.

## Prerequisites
- Python 3.7 or higher.
- Access to EvaDB database.
- OpenAI API key.

## Installation

Clone the repository:

```bash
git clone https://github.com/yourusername/article-categorizer.git
cd article-categorizer
```

Install the required packages:
```bash
pip install -r requirements.txt
```

## Usage
```bash
python3 app.py --articles articles/ --categories AmazonCategories.csv --api-key YOUR_API_KEY
```
