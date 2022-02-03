# Grab tables of variables from the SDK docs
#
# Run via:
#
#       scrapy runspider scrapevars.py --nolog  -o -:json | jq '. | sort_by(.url)' > scvars.json
#
import scrapy
import unicodedata


base_url = 'https://docs.flightsimulator.com/html/Programming_Tools/SimVars/Simulation_Variables.htm'


def normtext(s):
    return unicodedata.normalize('NFKC', s)


class SimConnectSpider(scrapy.Spider):
    name = "SimConnectSDK"

    def start_requests(self):
        yield scrapy.Request(base_url, callback=self.find_vars)

    def find_vars(self, response):
        urls = response.xpath('//div//ul/li/a/@href').getall()
        for url in urls:
            yield scrapy.Request(url=response.urljoin(url), callback=self.parse)

    def parse(self, response):
        def alltext(elt):
            if elt:
                return ''.join(map(normtext, elt.xpath('.//text()').getall())).strip()
            else:
                return None

        def parse_row(row):
            tds = row.xpath('td')
            ncol = len(tds)
            if ncol < 2:
                return None
            # simvar tables have 4 or 5 cols, with last two being units and settable
            # sometimes omitting multiplayer,
            # other tables have two or three cols
            simvar = ncol >= 4
            labels = ['name', 'description', 'multiplayer', 'units', 'settable']
            vs = [
                tds[0].xpath('code/text()').get()
            ] + [
                alltext(td) for td in tds[1:ncol-1 if simvar else ncol]
            ]
            if simvar:
                if ncol < 5:
                    # drop the multiplayer col
                    labels = labels[:2] + labels[-2:]
                vs.append(tds.xpath('span[@class="checkmark"]/span/@class').get() == 'checkmark_circle')
            return dict(zip(labels, vs))

        # look for nested pages
        for req in self.find_vars(response):
            yield req

        sections = [
            {
                'section': normtext(div.xpath('h4/text()').get()),
                'vars': list(filter(
                    None,
                    (parse_row(row) for row in div.xpath('table/tbody/tr'))
                ))
            }
            for div in response.xpath('//table/..')
        ]
        yield [] if not sections else {
            'url': response.url,
            'page': normtext(response.xpath('//h2/text()').get()),
            'sections': sections
        }
