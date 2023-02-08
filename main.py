# %% [markdown]
# ### Scraping Embedded PDFS from a website that uses pdfemb

# %%
import time
from selenium import webdriver
from selenium.webdriver.support.ui import Select
from selenium.webdriver.common.by import By
from selenium.webdriver.common.keys import Keys
from selenium import webdriver
from webdriver_manager.chrome import ChromeDriverManager
import base64
from fpdf import FPDF
import random
import logging
import pandas as pd


# %% [markdown]
# Creates a Logging File to track the success of our scraper

# %%
logging.basicConfig(filename="logfileerror.log", level=logging.INFO) # Create log file

# %% [markdown]
# Construct a function which adds whitepaper name and corresponding URL to our hashmap dictionary.

# %%
#note the function references globally defined variables driver and hashmap which we expect to already be initialised.
def addtohashmap():
    #Get Links
    Links = driver.find_elements(By.LINK_TEXT, 'Whitepaper') #Get all links to whitepaper in order that they appear in the table
    Linkstext = [elem.get_attribute("href") for elem in Links] #Get hyperlink

    #Get labels
    tags = driver.find_elements(By.TAG_NAME, 'td')  #Search for td tagged elements in the order that they appear
    Labelselem = []
    for elem in tags:
        if elem.text !="Whitepaper": #Only want the text in the table which doesn't refer to the whitepaper links 
            Labelselem.append(elem)
    Labelstext = [elem.text for elem in Labelselem] #Convert Selenium Elements to text


    #add label and links to our hashmap
    if len(Linkstext) != len(Labelstext):
        raise Exception("Number of titles don't match number of rows")#If the number of whitepapers is
        # more or less than the number of labels. There may be a misalignment.
    for i in range(len(Links)):
        if Labelstext[i] not in hashmap:
            hashmap[Labelstext[i]] =  Linkstext[i]
        else:
            hashmap[Labelstext[i] + "DUPLICATE"] = Linkstext[i] #If one name has 2 or more different links, we do not want to 
                #overwrite the data and lose one of the links

# %%
#Open Chrome window using chromium
driver = webdriver.Chrome(ChromeDriverManager().install())
driver.maximize_window()

driver.get("https://www.allcryptowhitepapers.com/whitepaper-overview/") #Gets link to the table
xpath = "//a[contains(@class,'paginate_button next')]" #Locates next button

while(True):
    addtohashmap() #Scan page for table data and add this to hashmap
    
    #Finds next button and clicks it
    #Note that the next button is of aria type meaning that we need to do an additional step to click on button
    cls = driver.find_element_by_xpath(xpath).get_attribute("class")
    if 'disabled' not in cls:
        driver.find_element_by_xpath(xpath).click()
    else:
        break

#Save all to dataframe
df = pd.DataFrame()
df['Whitepaper Name'] = list(hashmap.keys())
df['Links'] = list(hashmap.values())

df.to_csv('Whitepaperswithlinks.csv')

# %% [markdown]
# Reconstruct hashmap from the file that we may have originally stored.

# %%
df = pd.read_csv(".\Whitepaperswithlinks.csv")
names = list(df['Whitepaper Name'])
link = list(df['Links'])
hashmap = {}
for i in range(0,len(names)):
    hashmap[names[i]] = link[i]

# %% [markdown]
# Here we run our scraper

# %%
driver = webdriver.Chrome(ChromeDriverManager().install())
driver.maximize_window()

#For each link in our hashmap we would like to scrape our whitepaper
for t in range(0,len(hashmap)):
    #Navigate to our weblink
    whitepaper = list(hashmap.keys())[t]
    driver.get(hashmap[whitepaper])

    #Wait for webpage to load
    time.sleep(10)
    label = driver.find_element(By.XPATH, "//h1[@class = 'entry-title']").text # get current name of whitepaper listed on website
    print("Loading webpage " + label)

    # Scrape the embedded PDF and save it as a PDF.
    totalcanvases = []
    k=1
    j=1
    while True:
        try:
            #Make sure each pdf page has loaded
            time.sleep(1)
            #
            #Find button for next page on pdf document
            nextpage = driver.find_element(By.XPATH, "//button[@class = 'pdfemb-next']")
            #Select the kth canvas and take a snapshot of it
            page = driver.find_element(By.XPATH, "//div[@class = 'pdfemb-inner-div pdfemb-page"+str(k)+"']//canvas")
            canvas_base64 = driver.execute_script("return arguments[0].toDataURL('image/png').substring(21);", page)
            canvas_png = base64.b64decode(canvas_base64)
            with open(r"canvas" + str(j) + ".png", 'wb') as f: #save to image
                f.write(canvas_png)
                print("Create " + str(j) + "th canvas to png.")
            
            #Incremement page
            j+=1
            #Click on next page on pdf document
            nextpage.click()
            time.sleep(0.5)
            #get how many pages we have scanned so far
            totalcanvases.append(page)
            k+=1
        except Exception as e:  #We hit this exception when we get the last page. An error is thrown in
            # the pevious chunk as the next page XPATH doesn't exist.
            #We deal with this case in the following by not trying to find the "next button"

            #If there are less than 3 pages scraped, log a warning
            if k<3:
                logging.warning("check "+label + " download.")
            
            #got
            time.sleep(0.5)
            page = driver.find_element(By.XPATH, "//div[@class = 'pdfemb-inner-div pdfemb-page"+str(k)+"']//canvas")
            canvas_base64 = driver.execute_script("return arguments[0].toDataURL('image/png').substring(21);", page)
            # decode
            canvas_png = base64.b64decode(canvas_base64)
            #save to image
            with open(r"canvas" + str(j) + ".png", 'wb') as f:
                f.write(canvas_png)
                print("Create " + str(j) + "th canvas to png.")
            j+=1
            totalcanvases.append(page)
            k+=1
            break

    
    #no canvases might imply that there is no pdf embedded on the page
    if len(totalcanvases) == 0:
        logging.error("Whitepaper for " + label + " doesn't exist")
        Next_Link = driver.find_elements(By.PARTIAL_LINK_TEXT, ' Whitepaper')[-1].get_attribute("href")
        print("There is no link to pdf so skip " + label)
        continue

    
    #merge our png (derived from canvases) to pdf
    imagelist = ["canvas"+ str(i) + ".png" for i in range(1,j)]
    pdf = FPDF()
    k=1
    for image in imagelist:
        pdf.add_page()
        pdf.image(image,0,0,210,297)
        print("Added " + str(k) +"th image to pdf")
        k+=1

    pdf.output("./whitepapers/" + label +".pdf", "F")
    print("PDF has been generated for "+ label)

    logging.info("PDF Creation Success for " + str(label))
    print("NEXT LINK")


