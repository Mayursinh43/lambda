from selenium import webdriver
from selenium.webdriver.chrome.options import Options
import pandas as pd
from selenium.webdriver.common.action_chains import ActionChains
import traceback
import time
from itertools import cycle
from selenium import webdriver
import requests
import os
import zipfile

def hello(event, context):

    proxies = requests.get("https://proxy.webshare.io/api/proxy/list/?page=4", headers={"Authorization": "Token d81c3f75b10aee27fe69beebc25966ea4d915cea"}).json()['results']

    proxy_pool = cycle(proxies)
    url = 'http://tools.verifyemailaddress.io'
    count = 0
    rowcount = 1
    loopcount = 0

    for i in range(1,700):
        # Get a proxy from the pool
        search_results = None
        search_results = pd.DataFrame()
        proxy = next(proxy_pool)
        print(proxy)
        print("Request #%d"%i)
        try:

            PROXY_HOST =  proxy['proxy_address']
            PROXY_PORT =  proxy['ports']['http']
            PROXY_USER =  proxy['username']
            PROXY_PASS =  proxy['password']

            manifest_json = """
            {
                "version": "1.0.0",
                "manifest_version": 2,
                "name": "Chrome Proxy",
                "permissions": [
                    "proxy",
                    "tabs",
                    "unlimitedStorage",
                    "storage",
                    "<all_urls>",
                    "webRequest",
                    "webRequestBlocking"
                ],
                "background": {
                    "scripts": ["background.js"]
                },
                "minimum_chrome_version":"22.0.0"
            }
            """

            background_js = """
            var config = {
                    mode: "fixed_servers",
                    rules: {
                    singleProxy: {
                        scheme: "http",
                        host: "%s",
                        port: parseInt(%s)
                    },
                    bypassList: ["localhost"]
                    }
                };

            chrome.proxy.settings.set({value: config, scope: "regular"}, function() {});

            function callbackFn(details) {
                return {
                    authCredentials: {
                        username: "%s",
                        password: "%s"
                    }
                };
            }

            chrome.webRequest.onAuthRequired.addListener(
                        callbackFn,
                        {urls: ["<all_urls>"]},
                        ['blocking']
            );
            """ % (PROXY_HOST, PROXY_PORT, PROXY_USER, PROXY_PASS)


            def get_chromedriver(use_proxy=False, user_agent=None):
                chrome_options = webdriver.ChromeOptions()
        
                #options = Options()
                chrome_options.binary_location = '/opt/headless-chromium'
                chrome_options.add_argument('--headless')
                chrome_options.add_argument('--no-sandbox')
                chrome_options.add_argument('--single-process')
                chrome_options.add_argument('--disable-dev-shm-usage')

                if use_proxy:
                    pluginfile = 'proxy_auth_plugin.zip'

                    with zipfile.ZipFile(pluginfile, 'w') as zp:
                        zp.writestr("manifest.json", manifest_json)
                        zp.writestr("background.js", background_js)
                    chrome_options.add_extension(pluginfile)
                if user_agent:
                    chrome_options.add_argument('--user-agent=%s' % user_agent)
                driver_path = 'chromedriver'
                driver = webdriver.Chrome(driver_path, chrome_options=chrome_options)
                return driver

            
            driver = get_chromedriver(use_proxy=True)
            driver.set_page_load_timeout(60)
            driver.get('https://tools.verifyemailaddress.io')
            time.sleep(2)
            loopcount = rowcount
            data = pd.read_csv("yelp_insurance_agent.csv", skiprows=rowcount)
            for column in data.values:
                if(loopcount == count):
                    break
                print(column[2])
                element = driver.find_element_by_id("input-email-address")
                loopcount = loopcount + 1
                if element == None:
                    continue
                actions1 = ActionChains(driver)
                actions1.move_to_element(element)
                element.clear()
                element.send_keys(column[2])
                actions1.perform()
                time.sleep(2)

                element1 = driver.find_element_by_class_name("input-group-append")
                if element1 == None:
                    continue
                actions2 = ActionChains(driver)
                actions2.move_to_element(element1).click().perform()
                time.sleep(5)

                table = driver.find_element_by_id("dt-grid1")
                if table != None:
                    row = table.find_elements_by_tag_name("tr")[1]
                    status= row.find_elements_by_tag_name("td")[1].text
                    print(status)
                    data_dict = {
                        "business_name": column[0],
                        "site_url": column[1],
                        "EmailAddress": column[2],
                        "status": status,
                    }
                else:
                    print("Table Not Found")
                    data_dict = {
                        "business_name": column[0],
                        "site_url": column[1],
                        "EmailAddress": column[2],
                        "status": status
                    }
                search_results = search_results.append([data_dict])

            count = count + (loopcount-rowcount);
            rowcount = rowcount + (loopcount-rowcount)

            df = pd.read_csv('yelp_insurance_agent_verified.csv')
            amount_results = len(search_results)
            if df.empty:
                timestamp = str(int(time.time()))
                filename = 'yelp_insurance_agent_verified.csv'
                outdir = '.\\'
                if not os.path.exists(outdir):
                    os.mkdir(outdir)

                full_file_path = os.path.join(outdir, filename)

                if amount_results > 0:
                    print("Stored total of " + str(amount_results)
                        + " search results in file "
                        + str(full_file_path))

                    search_results.to_csv(full_file_path,
                                        index=False,
                                        columns=["business_name","site_url","EmailAddress","status"])
            else:
                if amount_results > 0:
                    search_results.to_csv('yelp_insurance_agent_verified.csv', index=False, mode='a',
                                        header=False,
                                        columns=["business_name","site_url","EmailAddress","status"])

            element2 = driver.find_element_by_id("buttons-excel")
            if element2 == None:
                time.sleep(300)
                continue
            actions3 = ActionChains(driver)
            actions3.move_to_element(element2).click().perform()
            time.sleep(7)
            driver.quit()

        except:
            traceback.print_exc()
            #Most free proxies will often get connection errors. You will have retry the entire request using another proxy to work.
            #We will just skip retries as its beyond the scope of this tutorial and we are only downloading a single url

            count = count + (loopcount - rowcount);
            rowcount = rowcount + (loopcount - rowcount)

            df = pd.read_csv('yelp_insurance_agent_verified.csv')
            amount_results = len(search_results)
            if df.empty:
                timestamp = str(int(time.time()))
                filename = 'yelp_insurance_agent_verified.csv'
                outdir = '.\\'
                if not os.path.exists(outdir):
                    os.mkdir(outdir)

                full_file_path = os.path.join(outdir, filename)

                if amount_results > 0:
                    print("Stored total of " + str(amount_results)
                        + " search results in file "
                        + str(full_file_path))

                    search_results.to_csv(full_file_path,
                                        index=False,
                                        columns=["business_name", "site_url", "EmailAddress", "status"])
            else:
                if amount_results > 0:
                    search_results.to_csv('yelp_insurance_agent_verified.csv', index=False, mode='a',
                                        header=False,
                                        columns=["business_name", "site_url", "EmailAddress", "status"])

            driver.quit()
            print("Skipping. Connnection error")

