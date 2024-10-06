from bs4 import BeautifulSoup
from selenium.webdriver.common.keys import Keys
from selenium.webdriver.common.by import By
from selenium.webdriver.support.wait import WebDriverWait
from selenium.webdriver.support import expected_conditions as ec


import re
import pandas as pd
import json

from concurrent.futures import ThreadPoolExecutor
from threading import Thread

from egypt_locations import egypt_locations_dict
import wedding_vendors_scraper as wv_scraper
from vendor_scraper_helper import VendorScraperHelper as VsHelper 


class VendorDataExtractor:
    
    def __init__(self):
        self.extractor_registry={
            "Instagram":InstaVendorDataExtractor(),
            "ArabiawWebsite":ArabiawVendorDataExtractor()
        }

    def create_extractor(self,data_extractor):

        if data_extractor in self.extractor_registry:
            return self.extractor_registry[data_extractor]
        else:
            raise ValueError("Invaild Input! Data Extractor Is Not Found")


class InstaVendorDataExtractor:

    def extract_vendor_data(self,profile_info_elements,category="Vendor")->dict:

        if category is None:
            category="Vendor"

        vendor_data = {}

        if len(profile_info_elements) > 0:
            vendor_data['vendor_name'] = profile_info_elements[0].get("content").split('•')[0]
            vendor_data['vendor_followers_num'] = profile_info_elements[1].get('content').split(", ")[0]
            vendor_data['vendor_following_num'] = profile_info_elements[1].get('content').split(", ")[1]


            try:
                vendor_phone_numbers = re.findall(r'\b\d{11,12}\b', profile_info_elements[2].get('content'))
                vendor_data['vendor_phone_numbers'] = ",".join(vendor_phone_numbers) if vendor_phone_numbers else ["UNKNOWN"]
            except Exception as e:
                vendor_data['vendor_phone_numbers'] = "UNKNOWN"

            try:
                vendor_locations = [location for location in egypt_locations_dict
                                    if location.lower() in profile_info_elements[2].get('content').lower()]
                
                vendor_data['vendor_locations'] = ",".join(vendor_locations) if vendor_locations else ["UNKNOWN"]

            except Exception as e:
                vendor_data['vendor_locations'] = "UNKNOWN"

            vendor_data['vendor_category'] = category

            # description = profile_info_elements[2].get('content').lower()
            # vendor_data['vendor_description'] = description if description and description != "" else "Not Available"

        return vendor_data
    
    def convert_vendors_list_to_df(self,vendors_info_list)->pd.DataFrame:
        df = pd.DataFrame(vendors_info_list)
        return df
    

    
    def extract_and_convert_vendor(self,scraper:wv_scraper.InstaVendorsScraper)->pd.DataFrame:
        
            collected_vendors_data=[]

            for index,link in enumerate(scraper.links_list):

                try:
                    page=scraper.drv.initialize_requests_client(link)
                except Exception as e:
                    raise Exception("Error In Connection")
                
                soup=BeautifulSoup(page.content,"lxml")
                profile_info_elements=soup.find_all(VsHelper().find_meta_with_description)

                #Check if category_list exists and has the same length of links_list
                if scraper.category_list and len(scraper.category_list)==len(scraper.links_list):
                    vendor_info=self.extract_vendor_data(profile_info_elements
                                                                                ,scraper.category_list[index])
                else:
                    vendor_info=self.extract_vendor_data(profile_info_elements)

                collected_vendors_data.append(vendor_info)

            vendor_info_df=self.convert_vendors_list_to_df(collected_vendors_data)

            #print(vendor_info_df)

            return vendor_info_df


class ArabiawVendorDataExtractor:

    all_included_vendors_list=[]


    def extract_vendor_data_process(self,
                                    vendor_link,
                                    scraper:wv_scraper.ArabiawWebsiteVendorsScraper):
        
        vendor_data = {}
        try:
            split_vendor_link =vendor_link.split("https://www.arabiaweddings.com/")[1].split("#")[0]
            vendor_json="https://www.arabiaweddings.com/_next/data/pkKdR-7xWpD7EbKbWkha2/en/"+split_vendor_link+".json"
            drv=scraper.drv.initialize_requests_client(vendor_json)

            #print(vendor_json)

            if (drv.status_code == 200):  
                json_data=json.loads(drv.content.decode('utf-8'))
                vendor_data["vendor_link"]=vendor_link

        except Exception as e:

            raise ConnectionError("The Driver Cannot Connect To The Website!")
        
        try:
            name=json_data["pageProps"]["pageData"]["meta"]["title"]
            vendor_data["vendor_name"]= name if name is not None else "-"

        except Exception as e:

            vendor_data["vendor_name"]="UNKNOWN"

        
        try:
            des=json_data["pageProps"]["pageData"]["meta"]["description"]
            vendor_data["vendor_description"]= des if des is not None else "-"

        except Exception as e:

            vendor_data["vendor_description"]="UNKNOWN"


  



        try:
            price=json_data["pageProps"]["pageData"]["price"]
            vendor_data["vendor_price"]= price if price is not None else "-"


        except Exception as e:

            vendor_data["vendor_price"]="UNKNOWN"

        try:
            category=json_data["pageProps"]["pageData"]["categories"][0]
            vendor_data['vendor_category']= category if category is not None else "-"
        
        except Exception as e:
            vendor_data["vendor_category"]="Vendor"


        try:
            address=json_data["pageProps"]["pageData"]["address"]
            vendor_data['vendor_locations']= address if address is not None else "-"

        except Exception as e:
            vendor_data['vendor_locations']="UNKNOWN"
        

        try:
            phone= json_data["pageProps"]["pageData"]["phone"]
            vendor_data['vendor_phone_numbers']= phone if phone is not None else "-"
        
        except Exception as e:
            vendor_data['vendor_phone_numbers']='UNKNOWN'

        self.all_included_vendors_list.append(vendor_data)

        drv.close()


    def extract_each_vendor_data(self,
                            collected_vendors_links,
                            scraper:wv_scraper.ArabiawWebsiteVendorsScraper)->list:
        

        
        thread_list=[]
        
        for vendor_link in collected_vendors_links:

            vendor_thread=Thread(target=self.extract_vendor_data_process,args=(vendor_link,scraper))
            vendor_thread.start()
            
            thread_list.append(vendor_thread)

        for t in thread_list:
            t.join()

            

        return self.all_included_vendors_list
    
    # def extract_each_vendor_data(self, collected_vendors_links, scraper):
    #     with ThreadPoolExecutor() as executor:
    #         futures = []
    #         for vendor_link in collected_vendors_links:
    #             futures.append(executor.submit(self.extract_vendor_data_process, vendor_link, scraper))

    #         for future in futures:
    #             future.result()

    #     return self.all_included_vendors_list

    
    def convert_vendors_list_to_df(self,vendors_info_list)->pd.DataFrame:
        df = pd.DataFrame(vendors_info_list)
        return df
    
    def collect_vendors_links(self,
                              scraper:wv_scraper.ArabiawWebsiteVendorsScraper)->list:

        collected_vendors_links=[]

        for link in scraper.links_list:

            try:
                page=scraper.drv.initialize_requests_client(link)
            except Exception as e:
                raise Exception("Error In Connection")
                
            soup=BeautifulSoup(page.content,"lxml")

            specified_vendors_section=soup.find("section",
                                                {'class':'listing_search__sICwA'}).select_one("ul")
            
            specified_vendors_links= list(

                set(['https://www.arabiaweddings.com'+str(x.get('href')) 
                for x in  specified_vendors_section.find_all("a")])
                
                                        )
            
            #print(specified_vendors_links)
            collected_vendors_links.extend(specified_vendors_links)

        page.close()

        return collected_vendors_links
    
    
    

    
    def extract_and_convert_vendor(self,
                                   scraper:wv_scraper.ArabiawWebsiteVendorsScraper):
        
        collected_vendors_data=[]

        collected_vendors_links=self.collect_vendors_links(scraper)
        print(len(collected_vendors_links))

        each_vendor_info=self.extract_each_vendor_data(collected_vendors_links,scraper)
        df=self.convert_vendors_list_to_df(each_vendor_info)
        print(df)
        df.to_csv("output.csv",index=False)





         
            