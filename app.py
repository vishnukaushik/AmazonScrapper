from flask import Flask, render_template, request
import requests
from bs4 import BeautifulSoup as bs
from urllib.request import urlopen as uReq
import pymongo
app = Flask(__name__)

@app.route('/',methods=['GET','POST'])
def index():
        if request.method=="POST":
            searchString = request.form['content'].replace(" ", "")
            try:
                dbConn = pymongo.MongoClient("mongodb://localhost:27017/")
                db = dbConn['AmazonCrawler']
                reviews = db[searchString].find({})
                if reviews.count() > 0:
                    return render_template('results.html', reviews=reviews)
                else:
                    amazon_url = "https://www.amazon.in/s?k=" + searchString
                    amazonPage = request.get(amazon_url).text
                    amazon_html = bs(amazonPage, "lxml")
                    src = amazon_html.find('div', attrs={"class": "sg-col-20-of-24 sg-col-28-of-32 sg-col-16-of-20 sg-col sg-col-32-of-36 sg-col-8-of-12 sg-col-12-of-16 sg-col-24-of-28"})
                    check = src.find('div', attrs={"class": "s-main-slot s-result-list s-search-results sg-row"})
                    boxes = check.findAll('div', attrs={"data-component-type": "s-search-result"})
                    box = boxes[0]
                    productLink = "https://www.amazon.in/" + box.div.span.div.div.find('div',attrs={"class":"a-section a-spacing-none a-spacing-top-small"}).div.div.a['href']
                    uClient = uReq(productLink)
                    prodRes = uClient.read()
                    uClient.close()
                    prod_html = bs(prodRes, "lxml")
                    commentboxes = prod_html.findAll('div',{'class':'a-section review aok-relative'})
                    try:
                        prod_name = prod_html.find('div', {"class": "a-section a-spacing-none", "id": "titleSection"}).span.text.strip()
                    except:
                        prod_name = ""
                    table = db[searchString]
                    reviews = []
                    for commentbox in commentboxes:
                        try:
                            name = commentbox.div.div.div.findAll('span',{'class':"a-profile-name"})[0].text
                        except:
                            name = 'No Name'
                        try:
                            rating = commentbox.div.div.findAll('div',{"class":"a-row"})[1].a['title']
                        except:
                            rating = 'No Rating'
                        try:
                            commentHead = commentbox.div.div.findAll('div',{"class":"a-row"})[1].findAll('a',{"class":"a-size-base a-link-normal review-title a-color-base review-title-content a-text-bold"})[0].span.text
                        except:
                            commentHead = 'No Comment Heading'
                        try:
                            custComment = commentbox.div.div.findAll('div',{"class":"a-row"})[3].find('div',{"class":"a-expander-content reviewText review-text-content a-expander-partial-collapse-content"}).span.text
                        except:
                            custComment = 'No Customer Comment'
                        mydict = {"Product": searchString + "\n("+prod_name+")", "Name": name, "Rating": rating, "CommentHead": commentHead,"Comment": custComment}
                        table.insert_one(mydict)
                        reviews.append(mydict)
                    return render_template('results.html', reviews=reviews)
            except:
                return 'something is wrong'
        else:
            return render_template('index.html')


if __name__ == "__main__":
    app.run(port=5000, debug=True)
