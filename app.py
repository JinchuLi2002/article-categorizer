import click
from categorizer import Categorizer


@click.command()
@click.option('--articles', help='Directory of articles to categorize.')
@click.option('--categories', help='Path to the categories CSV file.')
@click.option('--api-key', default=None, help='API key for any external service calls, if required.')
def main(articles, categories, api_key):
    """
    This script categorizes articles from a given directory into categories defined in a CSV file.
    """
    try:
        categorizer = Categorizer(api_key, categories, articles)
        categorizer.populate_articles_table()
        categorizer.populate_categories_table()
        categorizer.execute_matching()
        categorizer.refine_matches_with_chatgpt()
        click.echo("Article categorization complete.")
        categorizer.execute_query("SELECT * FROM article_final_category;")
    except Exception as e:
        click.echo(f"An error occurred during categorization: {e}", err=True)


if __name__ == '__main__':
    main()
