# Grab tables of variables from the SDK docs
#
# Run via:
#
#       scrapy runspider scripts/scrapevars.py --nolog -O simconnect/scvars.json
#
import scrapy
import scrapy.exporters
import unicodedata
import json


base_url = 'https://docs.flightsimulator.com/html/Programming_Tools/SimVars/Simulation_Variables.htm'


def normtext(s):
    return unicodedata.normalize('NFKC', s) if s else ''


def jointext(xs):
    return ''.join(map(normtext, xs.getall())).strip()


class PostProcessExporter(scrapy.exporters.BaseItemExporter):
    def __init__(self, file, **kwargs):
        super().__init__(dont_fail=True, **kwargs)
        self.file = file
        self.items = []

    def start_exporting(self):
        pass

    def export_item(self, item):
        self.items.append(item)

    def finish_exporting(self):
        output = dict()
        for item in sorted(self.items, key=lambda d: (d['page'], d['index'])):
            typ = item['type']
            del item['type']
            del item['index']
            output.setdefault(typ, []).append(item)
        s = json.dumps(output, indent=4).encode('utf-8')
        self.file.write(s)


class SimConnectSpider(scrapy.Spider):
    name = "SimConnectSDK"

    custom_settings = {
        'FEED_EXPORTERS': {'json': PostProcessExporter}
    }

    def start_requests(self):
        yield scrapy.Request(base_url, callback=self.find_vars)

    def find_vars(self, response):
        urls = response.xpath('//div//ul/li/a/@href').getall()
        for url in urls:
            yield scrapy.Request(url=response.urljoin(url), callback=self.parse)

    def parse(self, response):
        def alltext(elt):
            if elt:
                return jointext(elt.xpath('.//text()'))
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
                jointext(tds[0].xpath('.//text()'))
            ] + [
                alltext(td) for td in tds[1:(ncol-1 if simvar else ncol)]
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

        page = normtext(response.xpath('//h2/text()').get()).strip()
        context = {
            'url': response.url,
            'page': page,
            'type': page.split()[-1].replace('IDs', 'EVENTS')
        }
        i = 0
        for tbl in response.xpath('//table'):
            section = tbl.xpath('preceding-sibling::h4[1]') or tbl.xpath('preceding-sibling::h3[1]')
            context['section'] = normtext(section.xpath('text()').get())
            for row in tbl.xpath('tbody/tr'):
                d = parse_row(row)
                if d:
                    d.update(context, index=i)
                    i += 1
                    yield d
