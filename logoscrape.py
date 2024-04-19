from playwright.sync_api import sync_playwright
from dataclasses import dataclass, asdict, field
import pandas as pd
import os

#Klasa Kabinet, kasnije će biti jedan redak u CSV
@dataclass
class Kabinet:
    name: str = None
    address: str = None
    website: str = None
    phone_number: str = None
    latitude: float = None
    longitude: float = None

#Lista Kabinet objekata s metodama za spremanje u CSV
@dataclass
class KabinetList:
    kabinet_list: list[Kabinet] = field(default_factory=list)
    save_at = 'output'

    #transformira listu u dataframe, potrebno kako bi se spremilo u CSV
    def dataframe(self):
        return pd.json_normalize(
            (asdict(kabinet) for kabinet in self.kabinet_list), sep="_"
        )

    def save_to_csv(self):
        if not os.path.exists(self.save_at):
            os.makedirs(self.save_at)
        self.dataframe().to_csv(f"output/kabineti.csv")

def extract_coordinates(url: str) -> tuple[float,float]:
    coordSubstring = url.split('!3d')[-1]
    latitude = coordSubstring.split('!4d')[0]
    longitude = coordSubstring.split('!4d')[1].split('!')[0]
    return float(latitude), float(longitude)

def main():
    with sync_playwright() as p:
        ##paljenje google chrome
        browser = p.chromium.launch()
        page = browser.new_page()

        #navigacija do google maps i pretraga logoped zagreb pojma
        page.goto("https://www.google.com/maps/search/logoped+zagreb/", timeout=60000)

        #prihvaćanje googleovih uvjeta poslovanja
        page.get_by_role("button", name="Prihvati sve").click()
        page.wait_for_timeout(500)

        #treba staviti miša preko liste kabineta, kako bi scrollali preko njih
        page.hover('(//a[@class="hfpxzc"])[1]')

        #scrollanje do dna liste kabineta
        while True:
            page.mouse.wheel(0, 10000)
            page.wait_for_timeout(3000)

            #klasa koja sadrži poruku "You have reached the end of the list"
            end_of_list = page.query_selector('//div[contains(@class, "tLjsW")]')

            #prekidanje petlje kad se dođe do kraja liste
            if end_of_list:
                print("Reached the end of the list.")
                break
            else:
                print("Scrolling...")

        #lista svih kabineta
        listings = page.locator('//a[@class="hfpxzc"]').all()
        kabinet_list = KabinetList();

        #definicije u DOM za naše potrebe
        name_attibute = 'aria-label'
        address_xpath = '//button[@data-item-id="address"]//div[contains(@class, "fontBodyMedium")]'
        website_xpath = '//a[@data-item-id="authority"]//div[contains(@class, "fontBodyMedium")]'
        phone_number_xpath = '//button[contains(@data-item-id, "phone:tel:")]//div[contains(@class, "fontBodyMedium")]'

        #pregled duljine liste kabineta prije spremanja
        list_length = len(listings)
        print(f"Length of list: {list_length}")

        #iteriranje kroz cijelu listu   
        for listing in listings:
            listing.click()
            page.wait_for_timeout(5000)
            
            #instanciranje novog kabineta
            kabinet = Kabinet()
            
            #populiranje kabineta s podacima, ako ih nema onda prazno
            if len(listing.get_attribute(name_attibute)) >= 1:
                kabinet.name = listing.get_attribute(name_attibute)
            else:
                kabinet.name = ""
            if page.locator(address_xpath).count() > 0:
                kabinet.address = page.locator(address_xpath).all()[0].inner_text()
            else:
                kabinet.address = ""
            if page.locator(website_xpath).count() > 0:
                kabinet.website = page.locator(website_xpath).all()[0].inner_text()
            else:
                kabinet.website = ""
            if page.locator(phone_number_xpath).count() > 0:
                kabinet.phone_number = page.locator(phone_number_xpath).all()[0].inner_text()
            else:
                kabinet.phone_number = ""
            
            #zapisivanje koordinata
            kabinet.latitude, kabinet.longitude = extract_coordinates(page.url)

            #stavljanje novog kabineta u listu kabineta
            kabinet_list.kabinet_list.append(kabinet)

            #zbog transparentnosti u terminalu
            print(f"Entry added: {kabinet.name}")
        
        #na kraju petlje, zapisivanje u csv
        kabinet_list.save_to_csv()

        #zatvaranje virtualnog chromea
        browser.close()

        #poruka za kraj skripte
        print("Script finished!")
        
if __name__ == "__main__":
    main()