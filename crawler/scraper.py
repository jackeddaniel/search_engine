import scrapy
import os

class HtmlSpider(scrapy.Spider):
    name = "html_downloader"
    start_urls = ['https://en.wikipedia.org/wiki/Manchester_United_F.C.']

    custom_settings = {
        'USER_AGENT': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36',
        'LOG_LEVEL': 'INFO',
    }

    def parse(self, response):
        page_html = response.xpath('//html').get()
        filename = "manchester_united.html"
        
        # Saving to the current working directory
        with open(filename, 'w', encoding='utf-8') as f:
            f.write(page_html)
        
        self.logger.info(f'File created at: {os.path.abspath(filename)}')
