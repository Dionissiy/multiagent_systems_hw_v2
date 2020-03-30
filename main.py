from selenium import webdriver
from lxml.html import fromstring
import time
import json
from tika import parser
import tika

tika.initVM()

def get_source_code(agent):
    source_code = fromstring(agent.page_source)
    return source_code


def get_links_to_journals(source_code):
    journal_section = source_code.get_element_by_id('journals')
    journal_containers = journal_section.xpath('div/div/div')
    links = [x.xpath('a/@href')[0] for x in journal_containers]
    return links


def get_links_to_articles_from_journal_page(source_code):
    collection_of_articles = source_code.get_element_by_id('VolumesIssuesRight')
    article_containers = collection_of_articles.find_class('article')

    def extract_link_to_article_from_container(container):
        element = container.find_class('paperTitle')[0]
        link = element.xpath('@href')[0]
        return link

    links = [extract_link_to_article_from_container(x) for x in article_containers]
    return links


def get_article_data(link_to_journal_page, agent):

    def button_to_article_section_click(agent):
        journal_section = agent.find_element_by_id('journals')
        bar = journal_section.find_element_by_xpath('div/div[2]/div[1]')
        button = bar.find_element_by_xpath('a[5]')
        time.sleep(2)
        button.click()
        time.sleep(2)

    agent.get(link_to_journal_page)
    button_to_article_section_click(agent)
    source_code = get_source_code(agent)
    links = get_links_to_articles_from_journal_page(source_code)

    data = [extract_data_from_article_page(link, agent) for link in links]
    return data


def button_to_journal_section_click(agent):
    header = agent.find_element_by_tag_name('header')
    button = header.find_element_by_xpath('div/div[2]/a[3]')
    time.sleep(2)
    button.click()
    time.sleep(2)


def extract_data_from_article_page(link_to_article_page, agent):
    agent.get(link_to_article_page)

    journal_section = agent.find_element_by_id('journals')
    article_data_container = journal_section.find_element_by_id('articles')

    data = dict()

    def get_content_from_meta_data(name, container=article_data_container):
        meta = container.find_element_by_name(name)
        return meta.get_attribute('content')

    data['Title'] = get_content_from_meta_data('citation_title')
    meta_authors = article_data_container.find_elements_by_name('citation_author')
    data['Authors'] = [x.get_attribute('content') for x in meta_authors]
    data['Year'] = get_content_from_meta_data('citation_publication_date')
    data['Journal'] = get_content_from_meta_data('citation_journal_title')
    data['Publisher'] = get_content_from_meta_data('DC.publisher')
    data['ISNN'] = get_content_from_meta_data('citation_issn')
    data['Link to PDF'] = get_content_from_meta_data('citation_pdf_url')
    data['Abstract'] = get_content_from_meta_data('DC.description')

    parsed_pdf = parser.from_file(data['Link to PDF'])
    data['Article text'] = parsed_pdf['content']
    return data


def get_merged_data(separated_data):
    merged_data = []
    for data in separated_data:
        merged_data += data

    return merged_data


def save_file(data):
    with open('data.json', 'w', encoding='utf-8') as f:
        json.dump(data, f, indent=4)


if __name__ == "__main__":
    driver = webdriver.Firefox()
    driver.get('https://www.ronpub.com')
    button_to_journal_section_click(driver)

    source_code = get_source_code(driver)
    journal_links = get_links_to_journals(source_code)

    separated_data = []
    for link in journal_links:
        result = get_article_data(link, driver)
        separated_data.append(result)

    data = get_merged_data(separated_data)

    save_file(data)
    driver.close()
