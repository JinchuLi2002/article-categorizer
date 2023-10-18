import evadb
import openai
import os
import csv
import re
import nest_asyncio
import numpy as np

def categorize_articles(article_dir_path, category_csv_path, api_key):
    # Initialization
    nest_asyncio.apply()

    # Set API Key
    openai.api_key = api_key
    os.environ['OPENAI_KEY'] = api_key

    cursor = evadb.connect().cursor()

    # Importing and processing categories
    third_level_categories = set()
    with open(category_csv_path, 'r') as csvfile:
        reader = csv.reader(csvfile, delimiter=';')
        for row in reader:
            if len(row) > 3 and row[2] and not row[3]:
                third_level_categories.add(row[2])

    # Create and populate category table
    cursor.query("DROP TABLE IF EXISTS categories").df()
    cursor.query("CREATE TABLE categories (id INTEGER, category TEXT(30))").df()

    categories_list = list(third_level_categories)
    filtered_categories = sorted([re.sub(r'[^A-Za-z ]', '', category) for category in categories_list])
    data_to_insert = [(idx, category) for idx, category in enumerate(filtered_categories)][:10]

    for idx, category in data_to_insert:
        cursor.query(f"INSERT INTO categories (id, category) VALUES ({idx}, '{category}')").df()

    # Importing and processing articles
    texts = []
    for filename in os.listdir(article_dir_path):
        if filename.endswith('.txt'):
            with open(os.path.join(article_dir_path, filename), 'r') as file:
                text = file.read().replace("\n", " ")
                texts.append(re.sub(r'[^A-Za-z ]', '', text))

    cursor.query("DROP TABLE IF EXISTS articles").df()
    cursor.query("CREATE TABLE articles (id INTEGER, article TEXT(30000))").df()
    for i, t in enumerate(texts):
        cursor.query(f"INSERT INTO articles (id, article) VALUES ({i}, '{t}')").df()

    # Generate summaries for each article
    cursor.query("CREATE FUNCTION IF NOT EXISTS TextSummarizer TYPE HuggingFace TASK 'summarization' MODEL 'facebook/bart-large-cnn';").df()
    cursor.query("DROP TABLE IF EXISTS articles_with_summaries;").df()
    cursor.query("CREATE TABLE articles_with_summaries AS SELECT a.id, a.article, t.summary_text FROM articles AS a JOIN (SELECT id, TextSummarizer(article) FROM articles) AS t ON a.id = t.id;").df()

    # Get most relevant categories for each article and refine with ChatGPT
    cursor.query("DROP TABLE IF EXISTS article_final_category;").df()
    cursor.query("CREATE TABLE article_final_category (article_id INTEGER, selected_category TEXT(300));").df()
    
    all_articles = cursor.query("SELECT * FROM article_similar_categories;").df()
    for index, row in all_articles.iterrows():
        article_id = row[1]
        summary_text = row[2]
        categories = [row[3], row[4], row[5], row[6], row[7]]

        prompt = (f"Given the summary: '{summary_text}', "
              f"please choose the category that most closely aligns with the topic. "
              f"If none are even remotely related, reply 'none'. "
              f"The available categories are: {', '.join([cat for cat in categories if cat])}.")

        category_choice = cursor.query(f'SELECT ChatGPT("{prompt}")').df().iloc[0][0]
        cursor.query(f"INSERT INTO article_final_category (article_id, selected_category) VALUES ({article_id}, '{category_choice}');").df()

    result = cursor.query("SELECT * FROM article_final_category;").df()
    print(result)

if __name__ == '__main__':
    article_dir_path = input("Enter the path to the articles directory: ")
    category_csv_path = input("Enter the path to the category CSV: ")
    api_key = input("Enter your OpenAI API key: ")

    categorize_articles(article_dir_path, category_csv_path, api_key)
