import time
from datetime import date, datetime

import pandas as pd
import sqlalchemy as sqla
from bs4 import BeautifulSoup
from selenium import webdriver
from selenium.webdriver.chrome.options import Options
from selenium.webdriver.common.by import By
from selenium.webdriver.support.ui import Select
from sqlalchemy import create_engine


class YahooScraper:
  def __init__(self):
    options = Options()
    options.add_argument('--ignore-certificate-errors-spki-list')
    options.add_argument('--incognito')
    self.driver = webdriver.Chrome("chromedriver.exe")
    self.article_links = []
    self.full_articles = []


  def driver_get_link(self, link = None):
    full_link = "https://finance.yahoo.com/" + link if link else "https://finance.yahoo.com/"
    self.driver.get(full_link) 
    time.sleep(5)


  def close_driver(self):
    self.driver.close()
    

  def check_and_close_modal(self):
    try:
      close_modal_button = self.driver.find_element(By.XPATH, "//button[contains(@class, 'close T(0) End(0) M(4) Fz(m) P(2) Pos(a) Z(3) T(12px) End(12px) O(n)')]")
      close_modal_button.click()
      return True
    except:
      return False
  

  def load_articles(self):
    self.scroll_down()
    list_of_articles = self.driver.find_elements(By.XPATH, "//div[contains(@class, 'Ov(h) Pend(44px) Pstart(25px)')]")
    print(len(list_of_articles))
    self.scan_articles_and_store(list_of_articles)
  

  def scan_articles_and_store(self, article_list):
    for article in article_list:
      html = article.get_attribute("innerHTML")
      soup = BeautifulSoup(html, 'lxml')
      a_elem = soup.find("a")
      link = a_elem['href']
      self.article_links.append(link)
    self.extract_all_articles()


  def extract_all_articles(self):
    for link in self.article_links:
      self.driver_get_link(link)
      time.sleep(5)
      self.scrape_full_article()


  def scrape_full_article(self):
    print("here")
    page_ = self.driver.page_source
    soup = BeautifulSoup(page_, "lxml")

    content_parent = soup.find("div", {"class":"caas-content-wrapper"})
    author = content_parent.find("span", {"class":"caas-author-byline-collapse"})

    date_published = content_parent.find("time")
    date_scraped = datetime.now().date()

    image_links_soup = content_parent.find_all("img")
    print(len(image_links_soup))

    image_links = []
    for link in image_links_soup:
      try:
        image_links.append(link["src"])
      except:
        image_links.append("")
        
    print(len(image_links))

    body_soup = content_parent.find("div", {"class":"caas-body"})
    paragraphs = body_soup.find_all("p")

    body = ""
    for elem in paragraphs:
      body += str(elem)
    
    self.full_articles.append([date_scraped, author, image_links, body, date_published])
    

  def save_to_sql(self):
    df = pd.DataFrame(self.full_articles, columns=['date_scraped', 'author', 'image_links', 'body', 'date_published'])
    engine = create_engine('sqlite://', echo=False)
    df.to_sql('yahoo_article', con=engine)
    engine.execute("SELECT * FROM yahoo_article").fetchall()
    engine.dispose()


  def scroll_down(self):
    height = self.driver.execute_script("return Math.max(document.body.scrollHeight, document.body.offsetHeight, document.documentElement.clientHeight, document.documentElement.scrollHeight, document.documentElement.offsetHeight);")
    while height < 20000:
      print(height)
      time.sleep(1)
      self.driver.execute_script("window.scrollTo(0, Math.max(document.body.scrollHeight, document.body.offsetHeight, document.documentElement.clientHeight, document.documentElement.scrollHeight, document.documentElement.offsetHeight));")
      height = self.driver.execute_script("return Math.max(document.body.scrollHeight, document.body.offsetHeight, document.documentElement.clientHeight, document.documentElement.scrollHeight, document.documentElement.offsetHeight);")





yahoo_scraper = YahooScraper()

yahoo_scraper.driver_get_link()
yahoo_scraper.check_and_close_modal()
yahoo_scraper.load_articles()
yahoo_scraper.save_to_sql()