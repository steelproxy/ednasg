import newspaper
import bottom_win
import message_win

def scrape_article_content(articles):
    message_win.clear_buffer()
    transformed_articles = []
    for article in articles:
        message_win.baprint(f"Scraping article {article["url"]}...")
        news_article = newspaper.Article(article['url'])
        news_article.download()
        news_article.parse()
        article_text = news_article.text
        new_article = {
            'date': article['date'],
            'title': article['title'],
            'summary': article_text,
            'url': article['url']
        }
        transformed_articles.append(new_article)
    return transformed_articles