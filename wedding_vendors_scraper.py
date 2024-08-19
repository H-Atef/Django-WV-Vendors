from bs4 import BeautifulSoup

from abc import ABC,abstractmethod
import pandas as pd
import re


import vendor_data_extractor as wv_extractor
from web_scraping_resources import WebScarpingToolInit




class WeddingVendorsScraper(ABC):

    def __init__(self,links_list=None,category_list=None):
        self.category_list=category_list
        self.links_list=links_list
        self.drv=WebScarpingToolInit()
        self.vendor_data_extractor=wv_extractor.VendorDataExtractor()

    @abstractmethod
    def scrape_vendors_info(self):
        pass


class InstaVendorsScraper(WeddingVendorsScraper):

    def __init__(self,links_list=None,category_list=None):
        super().__init__(links_list,category_list)
        self.extractor="Instagram"
        


    def scrape_vendors_info(self)->pd.DataFrame:

        if self.links_list is None:
            return "Empty Links List"
        
        else:
            insta_vendors_df=self.vendor_data_extractor.create_extractor(self.extractor).extract_and_convert_vendor(self)
            
            return insta_vendors_df
                
                    

                   



class ArabiawWebsiteVendorsScraper(WeddingVendorsScraper):

    def __init__(self,links_list=None,category_list=None):
        super().__init__(links_list,category_list)
        self.extractor="ArabiawWebsite"

    def scrape_vendors_info(self):
        
        if self.links_list is None:
            return "Empty Links List"
        
        else:
            vendors_df=self.vendor_data_extractor.create_extractor(self.extractor).extract_and_convert_vendor(self)
            
            return vendors_df


            






class WeddingVendorScraperFactory:

    def __init__(self):
        self.scraper_registry = {
            "Instagram": InstaVendorsScraper,
            "Arabiaw": ArabiawWebsiteVendorsScraper
                            }

    def create_scraper(self,website="UNKNOWN",links_list=None,category_list=None)->WeddingVendorsScraper:
        if website in self.scraper_registry:
            return self.scraper_registry[website](links_list,category_list)
        else:
            raise ValueError("Unknown website")




if __name__ == '__main__':


    # scraper=WeddingVendorScraperFactory().create_scraper("Instagram"
    #                                     ,links_list=[

    #                                         "https://www.instagram.com/the_cake_studio_egypt/",
    #                                         "https://www.instagram.com/cake_and_sugar_egypt/",
    #                                         "https://www.instagram.com/rosacakes_cupcakes/",
    #                                         "https://www.instagram.com/keika.eg/",
    #                                         "https://www.instagram.com/devourcupcakes/"
                                                    
                                                    
    #                                                 ])
    scraper=WeddingVendorScraperFactory().create_scraper("Arabiaw"
                                        ,links_list=[

                                        'https://www.arabiaweddings.com/cairo/wedding-venues'
                                                    
                                                    ])

    scraper.scrape_vendors_info()