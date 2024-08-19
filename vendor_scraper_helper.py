import re

class VendorScraperHelper:
    
    # Custom function to find meta tag using regex
    def find_meta_with_description(self,tag):
        return tag.name == 'meta' and any(re.search(r'\b(description|og:title)\b',
                                                     value, 
                                                     re.IGNORECASE) for value in tag.attrs.values())