import scrapy
import w3lib.html
import pdb

class Delivery(scrapy.Spider):
    name = "delivery"
    start_urls = ["https://training.gov.au/Search/SearchOrganisation?IncludeUnregisteredRtos=false&IncludeNotRtos=true%2Cfalse&orgSearchByNameSubmit=Search&JavaScriptEnabled=true&gridRtoSearchResults-page=1&setFocus=gridRtoSearchResults"]
    data = {}
    idx = 0
    code = ["TAALLN401B", "TAELLN401A", "TAELLN411", "TAAASS402C", "TAEASS402B", "TAEASS402A", "TAEASS402", "TAEDES401A",
            "TAEDES401", "TAEDES402A", "TAEDES402", "TAADEL401B", "TAEDEL401A", "TAEDEL401", "TAADEL403B", "TAEDEL402A",
            "TAEDEL402", "TAEASS502A", "TAEASS502B", "TAEASS502", "TAEASS403", "TAEASS401", "TAEDEL301", "BSBCMM401",
            "TAADEL301C", "TAEDEL301A", "BSBCMM401A", "TAEDEL403A", "TAEDEL404A", "TAEDEL501A", "TAETAS401A", "BSBAUD402B",
            "BSBLED401A", "TAEDEL403", "TAEDEL404", "TAEDEL501", "TAETAS401", "BSBAUD402", "BSBLED401", "TAEDEL301C",
            "TAEASS301B", "TAEASS301", "BSBMKG413", "BSBMKG413A", "BSBREL402", "BSBREL402A", "BSBRES401", "BSBRES401A"]

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
            if data.css('a::text').extract() in [['Regulatory Decision Information'], ['Scope'], ['Registration'], ['Contacts']]:
                continue
            elif data.css('a::text').extract() in [['Delivery']]:
                urls.append("https://training.gov.au" + data.css('a::attr(href)').extract()[0])

        for url in urls:
            yield scrapy.Request(url=url, callback=self.parse_item, meta={'idx': response.meta['idx']})

    def parse_item(self, response):
        have_tae = "no"
        for tr in response.css('div#DeliveryNotifications').css('tbody tr'):
            items = tr.css('td::text').extract_first().strip().split(', ')
            for item in items:
                if item in self.code:
                    have_tae = "yes"
                    break
            if have_tae == 'yes':
                next = ['#']
                break
            else:
                next_selector = response.xpath('//*[@title="Next page"]/@href')
                next = next_selector.extract()
                for url in next:
                    yield scrapy.Request("https://training.gov.au" + url, callback=self.parse_item,
                                         meta={'idx': response.meta['idx']})

        if 'Have tae' in self.data[response.meta['idx']]:
            if have_tae == 'yes':
                self.data[response.meta['idx']].update({'Have tae': have_tae})
        else:
            self.data[response.meta['idx']].update({'Have tae': have_tae})

        if next == ['#']:
            yield self.data[response.meta['idx']]
        pass

