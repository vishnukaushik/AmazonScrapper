from flask import Flask, render_template, request
import requests
from bs4 import BeautifulSoup as bs
from urllib.request import urlopen as uReq
import pymongo
app = Flask(__name__)

#https://www.amazon.in/s?k=
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
                    uClient = uReq(amazon_url)
                    amazonPage = uClient.read()
                    uClient.close()
                    amazon_html = bs(amazonPage, "html.parser")
                    bigboxes = amazon_html.findAll("div", {"data-component-type": "s-search-result","class": "s-main-slot s-result-list s-search-results sg-row"})
                    del bigboxes[0:4]
                    box = bigboxes[0]
                    productLink = "https://www.amazon.in/" + box.div.span.div.div.div.h2.a['href']
                    prodRes = requests.get(productLink)
                    prod_html = bs(prodRes.text, "html.parser")
                    commentboxes = prod_html.find_all('div', { 'class': "a-section review aok-relative"})

                    table = db[searchString]
                    reviews = []
                    for commentbox in commentboxes:
                        try:
                            name = commentbox.div.div.div.a.find_all('span', {'class': 'a-profile-name'})[0].text
                        except:
                            name = 'No Name'
                        try:
                            rating = commentbox.div.div.div.div.text
                        except:
                            rating = 'No Rating'
                        try:
                            commentHead = commentbox.div.div.div.p.text
                        except:
                            commentHead = 'No Comment Heading'
                        try:
                            comtag = commentbox.div.div.find_all('div', {'class': ''})
                            custComment = comtag[0].div.text
                        except:
                            custComment = 'No Customer Comment'
                        mydict = {"Product": searchString, "Name": name, "Rating": rating, "CommentHead": commentHead,"Comment": custComment}
                        table.insert_one(mydict)
                        reviews.append(mydict)
                    return render_template('results.html', reviews=reviews)
            except:
                return 'something is wrong'
        else:
            return render_template('index.html')


if __name__ == "__main__":
    app.run(port=8000, debug=True)
