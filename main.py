from bs4 import BeautifulSoup
import pandas as pd

from http_client import HTTPSClient

def main():
    url = "https://companiesmarketcap.com/defense-contractors/largest-companies-by-market-cap/"

    client = HTTPSClient()

    custom_headers = {
        'Accept-Language': 'en-US,en;q=0.9',
        'Cache-Control': 'no-cache',
        'Accept-Encoding': 'gzip'
    }
    html_content, status_code = client.get_content(url, custom_headers)

    companies = {"Rank": [], "Name": [], "Market Cap (millions)": [], "Price": [], "Country": []}
    
    if status_code != None and html_content != None:
        soup = BeautifulSoup(html_content, "lxml")
        table_element = soup.find("table", class_="marketcap-table")
        if table_element != None:
            tbody_element = table_element.find("tbody")
            if tbody_element != None:
                tr_elements = tbody_element.find_all("tr")
                for tr_element in tr_elements:
                    td_elements = tr_element.find_all("td")

                    i = 0
                    for td_element in td_elements:
                        if td_element.has_attr("class"):
                            if "rank-td" in td_element.attrs["class"]:
                                rank_s = td_element.get_text()
                                rank = int(rank_s)
                                companies["Rank"].append(rank)
                            elif "name-td" in td_element.attrs["class"]:
                                company_name_div_element = td_element.find("div", class_="company-name")
                                if company_name_div_element != None:
                                    company_name = company_name_div_element.get_text()
                                    companies["Name"].append(company_name)
                            elif "td-right" in td_element.attrs["class"]:
                                if i == 3:
                                    # Market cap
                                    market_cap_s = td_element.get_text()
                                    if market_cap_s[-1] == "B":
                                        market_cap_s = market_cap_s[:-2]
                                        market_cap_s = market_cap_s.removeprefix("$")
                                        market_cap = float(market_cap_s) * 1000
                                        companies["Market Cap (millions)"].append(market_cap)
                                    elif market_cap_s[-1] == "M":
                                        market_cap_s = market_cap_s[:-2]
                                        market_cap_s = market_cap_s.removeprefix("$")
                                        market_cap = float(market_cap_s)
                                        companies["Market Cap (millions)"].append(market_cap)
                                elif i == 4:
                                    # Price
                                    price_s = td_element.get_text()
                                    price_s = price_s.removeprefix("$")
                                    price_s = price_s.replace(",", "")
                                    price = float(price_s)
                                    companies["Price"].append(price)
                        elif i == 7:
                            span_element = td_element.find("span")
                            if span_element != None:
                                country = span_element.get_text()
                                companies["Country"].append(country)
                        i += 1

        df = pd.DataFrame(companies)

        country = "USA"
        df = df.query("Country == @country")
        df.to_csv(path_or_buf="data/largest_companies.csv", index=False)
                    
        print(f"HTTP Status Code: {status_code}")
        print(f"URL: {url}")
        print(f"Retrieved {len(html_content)} characters")
        print(f"First 300 chars: \n{html_content[:100]}")
    else:
        print(f"Failed to retrieve content, HTTP status code: {status_code}")
        print(f"URL: {url}")

if __name__ == "__main__":
    main()
    