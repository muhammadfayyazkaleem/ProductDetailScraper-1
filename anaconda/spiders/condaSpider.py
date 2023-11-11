import scrapy
import csv
from anaconda.items import AnacondaItem

class CondaspiderSpider(scrapy.Spider):
    name = "condaSpider"
    allowed_domains = ["anacondastores.com"]
    start_urls = ["https://anacondastores.com"]

    def parse(self, response):
    
        top_categories_nodes = response.xpath("//div[@id='mainNav']/div/ul/li[div[@class='nav-link']/a[not(contains(text(),'Water') or contains(text(),'Gift') or contains(text(),'Catalogues'))]]")
        for top_category_node in top_categories_nodes:
            top_category_title = top_category_node.xpath("./div/a/text()").get()
            
            categories_nodes = top_category_node.xpath(".//ul[@class='sub-nav-list']/li[div/a]")
            for category_node in categories_nodes:
                category_title = category_node.xpath("./div/a/text()").get()
                
                sub_categories_nodes = category_node.xpath(".//div[@class='sub-nav-items']/ul/li/a")
                for sub_category_node in sub_categories_nodes:
                    sub_category_title = sub_category_node.xpath("./text()").get()
                    
                    sub_category_url=sub_category_node.xpath("./@href").get()
                    breadcrumb = top_category_title + " "+category_title+" "+sub_category_title
                    yield scrapy.Request(url=response.urljoin(sub_category_url),callback = self.listing,meta={'breadcrumb':breadcrumb})

    def listing(self,response):

        product_nodes = response.xpath("//div[@class='product__list--wrapper']//a")
        for product_node in product_nodes:
            product_url = product_node.xpath("./@href").get()
            yield scrapy.Request(url=response.urljoin(product_url),callback=self.product_details,meta=response.meta)     
        totalpages = int(response.xpath("//span[@itemprop='numberOfItems']/text()").get())
        next_pages = totalpages//18
        
        if next_pages >= 1:
            for next_page in range(1,next_pages+1):
                next_page_url = f"{response.url}?q=&page={next_page}"
                yield scrapy.Request(url=next_page_url,callback=self.listing,meta=response.meta)

    def product_details(self,response):
       
        breadcrumb = response.meta['breadcrumb'] 
        name = self.get_name(response)
        regular_price,sale_price = self.get_price(response)
        size = self.get_size(response)
        color = self.get_color(response)
        with open("anaconda.csv","a+",encoding="UTF8",newline="") as f:
            writer = csv.writer(f)
            writer = writer.writerow([breadcrumb,name,regular_price,sale_price,size,color])

    def get_name(self,response):
        return response.xpath("//span[@class='pdp-title']/text()").get()

    def get_price(self, response):
        sale_price = ""
        regular_price = ""
        sale_price_node = response.xpath("//p[contains(@class,'price-vip')]//span[@class='amount']/text()").get()
        if sale_price_node is not None:
            sale_price = sale_price_node
            regular_price = response.xpath("//p[contains(@class,'price-standard')]/span[not(contains(@class,'prefix'))]/text()").get()
            return regular_price,sale_price 
        else:
            regular_price = response.xpath("//p[contains(@class,'price-regular')]/span/text()").get()
            return regular_price, sale_price if sale_price is None else ""

        
    def get_size(self,response):
        sizes = []
        size_nodes = response.xpath("//div[contains(@class,'size-grid-wrapper')]/a[not(contains(@class,'out-of-stock'))]")
        for size_node in size_nodes:
            size = size_node.xpath("./text()").get().strip()
            sizes.append(size)
        return sizes
    
    def get_color(self,response):
        colors = []
        colors_nodes=response.xpath("//div[contains(@class,'variant-selector')]/div/a")
        for color_node in colors_nodes:
            color = color_node.xpath("./@title").get().strip()
            colors.append(color)
        return colors

    
    