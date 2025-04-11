import scrapy
import os
from imbdscraper.items import MovieItem


class MovieSpider(scrapy.Spider):
    name = 'moviespider_local'

    def start_requests(self):
        html_dir = os.path.abspath(os.path.join(os.path.dirname(__file__), '..', '..', '..', 'html_movies'))

        for filename in os.listdir(html_dir):
            if filename.endswith('.html'):
                filepath = os.path.join(html_dir, filename)
                url = f'file:///{filepath.replace(os.sep, "/")}'  # compatibilidad Windows
                yield scrapy.Request(url=url, callback=self.parse_local, meta={'filepath': filepath})

    def parse_local(self, response):
        filepath = response.meta['filepath']

        with open(filepath, 'r', encoding='utf-8') as f:
            html_content = f.read()

        fake_response = scrapy.http.TextResponse(
            url=response.url,
            body=html_content,
            encoding='utf-8'
        )

        yield from self.parse(fake_response)

    def parse(self, response):
        item = MovieItem()

        title = response.css('span.hero__primary-text::text').get()
        item['title'] = title.strip() if title else None

        year_li = response.css('div.sc-70a366cc-0.bxYZmb ul.ipc-inline-list--show-dividers li')
        item['year'] = year_li[0].css('a::text').get().strip() if year_li else None

        rating = response.css('div.sc-d541859f-2 span::text').get()
        item['imbd_rating'] = rating.strip() if rating else None

        genres = response.css('a.ipc-chip span.ipc-chip__text::text').getall()
        item['genres'] = genres if genres else None

        item['directors'] = response.css(
            'ul.ipc-inline-list.ipc-inline-list--show-dividers.ipc-inline-list--inline.ipc-metadata-list-item__list-content.baseAlt li a::text'
        ).get()

        actors = response.css('div[data-testid="title-cast-item"] a[data-testid="title-cast-item__actor"]::text').getall()
        item['actors'] = actors if actors else None

        item['runtime'] = year_li[2].css('::text').get().strip() if len(year_li) > 2 else None

        raw_watch_on = response.css(
            'div[data-testid="tm-box-woc-text"] + div a.ipc-lockup-overlay.ipc-focusable::attr(aria-label)'
        ).getall()
        item['watch_on'] = self.clean_watch_on(raw_watch_on)

        yield item

    def clean_watch_on(self, platforms):
        cleaned = [p.replace('Watch on ', '').strip() for p in platforms if p]
        return cleaned if cleaned else None
