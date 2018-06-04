import scrapy
from scrapy_splash import SplashRequest
import w3lib.html
import pdb

script = """
function main(splash)
    splash:init_cookies(splash.args.cookies)
    local url = splash.args.url
    assert(splash:go(url))
    assert(splash:wait(5))
    return {
        cookies = splash:get_cookies(),
        html = splash:html()
    }
end
"""

script2 = """
function main(splash)
    splash:init_cookies(splash.args.cookies)
    local url = splash.args.url
    assert(splash:go(url))
    assert(splash:wait(0.5))
    return {
        cookies = splash:get_cookies(),
        html = splash:html()
    }
end
"""

script3 = """
function main(splash)
  splash:init_cookies(splash.args.cookies)
  assert(splash:go{
    splash.args.url,
    headers=splash.args.headers,
    http_method=splash.args.http_method,
    body=splash.args.body,
    })
  assert(splash:wait(0.5))

  local entries = splash:history()
  local last_response = entries[#entries].response
  return {
    url = splash:url(),
    headers = last_response.headers,
    http_status = last_response.status,
    cookies = splash:get_cookies(),
    html = splash:html(),
  }
end
"""


class IvetDataSpider(scrapy.Spider):
    name = "ivet_data"
    start_urls = ["https://training.gov.au/Search/SearchOrganisation?Name=&IncludeUnregisteredRtos=false&IncludeNotRtos=true&IncludeNotRtos=false&orgSearchByNameSubmit=Search&AdvancedSearch=&JavaScriptEnabled=true"]
    data = {}

    def start_requests(self):
        for url in self.start_urls:
            yield SplashRequest(url, self.parse, endpoint='execute',
                                args={'lua_source': script})

    def parse(self, response):
        next_selector = response.xpath('//*[@title="Next page"]/@href')
        for url in next_selector.extract():
            yield SplashRequest("https://training.gov.au" + url, endpoint='execute',
                                args={'lua_source': script2})

        url_selector = response.css('#gridRtoSearchResults')

        for row in url_selector.css('tbody tr'):
            yield SplashRequest("https://training.gov.au" + row.css('td a::attr(href)')[0].extract(),
                                callback=self.parse_page, endpoint='execute', args={'lua_source': script2})

    def parse_page(self, response):
        url_selector = response.css('ul.t-reset.t-tabstrip-items')[0].css('li.t-item')

        urls = [response.url]

        for data in url_selector:
            if data.css('a::text').extract() in [['Regulatory Decision Information'], ['Delivery'], ['Scope']]:
                continue
            elif data.css('a::text').extract() in [['Registration'], ['Contacts']]:
                urls += ["https://training.gov.au" + data.css('a::attr(href)').extract()[0]]

        self.data = {}
        for url in urls:
            if url == urls[-1]:
                export = 'ok'
            else:
                export = ''
            yield SplashRequest(url, callback=self.parse_item, endpoint='execute', args={'lua_source': script3},
                                meta={'export': export})

    def parse_item(self, response):
        for quote in response.css('div.display-row'):

            data = {
                w3lib.html.strip_html5_whitespace(quote.css('div.display-label::text').extract_first() or '').strip().replace("\n", ""):
                    w3lib.html.strip_html5_whitespace(
                        quote.css('div.display-field-no-width::text').extract_first() or quote.css(
                            'div.display-field-unblocked-narrowest::text' or '').extract_first()).strip()
            }
            self.data.update(data)
        if response.meta['export'] == 'ok':
            yield self.data
        pass
