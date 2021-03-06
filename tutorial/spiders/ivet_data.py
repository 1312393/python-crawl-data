import scrapy
import w3lib.html
import pdb

class IvetDataSpider(scrapy.Spider):
    name = "ivet"
    start_urls = ["https://training.gov.au/Search/SearchOrganisation?Name=&IncludeUnregisteredRtos=false&IncludeNotRtos=true&IncludeNotRtos=false&orgSearchByNameSubmit=Search&AdvancedSearch=&JavaScriptEnabled=true"]
    data = {}
    idx = 0
    def start_requests(self):
        for url in self.start_urls:
            yield scrapy.Request(url=url, callback=self.parse)

    def parse(self, response):
        next_selector = response.xpath('//*[@title="Next page"]/@href')
        for url in next_selector.extract():
            yield scrapy.Request("https://training.gov.au" + url)

        url_selector = response.css('#gridRtoSearchResults')

        for row in url_selector.css('tbody tr'):
            self.data.update({self.idx: {}})
            url = "https://training.gov.au" + row.css('td a::attr(href)')[0].extract()
            yield scrapy.Request(url=url, callback=self.parse_page, meta={'idx': self.idx})
            self.idx += 1

    def parse_page(self, response):
        url_selector = response.css('ul.t-reset.t-tabstrip-items')[0].css('li.t-item')

        for outer in response.css('div.outer'):
            for quote in outer.css('div.display-row'):
                column = w3lib.html.strip_html5_whitespace(quote.css('div.display-label::text').extract_first() or '').strip().replace("\n", "")
                if column == 'Status:':
                    data = {
                        column: w3lib.html.strip_html5_whitespace(quote.css('span.green::text').extract_first())
                            .strip().replace("\n                                   ", "")
                    }
                elif column == 'ABN:':
                    data = {
                        column: w3lib.html.strip_html5_whitespace(quote.css('a::text').extract_first()).strip()
                    }
                else:
                    data = {
                        column:
                            w3lib.html.strip_html5_whitespace(
                                quote.css('div.display-field-no-width::text').extract_first() or quote.css(
                                    'div.display-field-unblocked-narrowest::text' or '').extract_first())
                                .strip().replace("\n                                   ", "")
                    }
                self.data[response.meta['idx']].update(data)
        urls = []

        for data in url_selector:
            if data.css('a::text').extract() in [['Regulatory Decision Information'], ['Scope'], ['Delivery']]:
                continue
            elif data.css('a::text').extract() in [['Registration'], ['Contacts']]:
                urls.append("https://training.gov.au" + data.css('a::attr(href)').extract()[0])

        for url in urls:
            if url == urls[-1]:
                export = 'ok'
            else:
                export = ''
            yield scrapy.Request(url=url, callback=self.parse_item, meta={'export': export, 'idx': response.meta['idx']})

    def parse_item(self, response):
        for outer in response.css('div.outer'):
            for quote in outer.css('div.display-row'):
                column = w3lib.html.strip_html5_whitespace(quote.css('div.display-label::text').extract_first() or '').strip().replace("\n", "")
                if response.meta['export'] == 'ok':
                    column = w3lib.html.strip_html5_whitespace(outer.css('h2.legend::text').extract_first()).strip() + ' - ' + column
                data = {
                    column:
                        w3lib.html.strip_html5_whitespace(
                            quote.css('div.display-field-no-width::text').extract_first() or quote.css(
                                'div.display-field-unblocked-narrowest::text' or '').extract_first())
                            .strip().replace("\n                                   ", "")
                }
                self.data[response.meta['idx']].update(data)
        if response.meta['export'] == 'ok':
            yield self.data[response.meta['idx']]
        pass

