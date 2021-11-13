from flask import Flask, render_template, request
from bs4 import BeautifulSoup
import re
import math
import pandas as pd
import requests
import lxml
import csv
import numpy as np
import app


exposure_list = []
outcome_list = []
exclusion_list = []

@app.route('/search_builder')
def search_builder():
    return render_template("pubscraper.html", exposure_list=exposure_list,
                           outcome_list=outcome_list,
                           exclusion_list=exclusion_list)


@app.route('/search_builder_1', methods=["GET", "POST"])
def exposure():
    if request.method == "POST":
        exposure = request.form.get("exposure")
        exposure_list.append(exposure)
    return render_template("pubscraper.html", exposure_list=exposure_list,
                           outcome_list=outcome_list,
                           exclusion_list=exclusion_list)


@app.route('/search_builder_2', methods=["GET", "POST"])
def outcome():
    if request.method == "POST":
        outcome = request.form.get("outcome")
        outcome_list.append(outcome)
    return render_template("pubscraper.html", exposure_list=exposure_list,
                           outcome_list=outcome_list,
                           exclusion_list=exclusion_list)


@app.route('/search_builder_3', methods=["GET", "POST"])
def exclusion():
    if request.method == "POST":
        exclusion = request.form.get("exclusion")
        exclusion_list.append(exclusion)
    return render_template("pubscraper.html", exposure_list=exposure_list,
                           outcome_list=outcome_list,
                           exclusion_list=exclusion_list)


@app.route('/searchbuilder_4', methods=["GET", "POST"])
def searchbuilder():
    TermString = ""
    TermString += "((("
    for term in exposure_list:
        TermString += term
        TermString += "[Title/Abstract]) OR ("
    TermString = TermString[:-5]
    TermString += ") AND (("
    for term in outcome_list:
        TermString += term
        TermString += "[Title/Abstract]) OR ("
    TermString = TermString[:-5]
    TermString += ") NOT (("
    for term in exclusion_list:
        TermString += term
        TermString += "[Title]) OR ("
    TermString = TermString[:-5]
    TermString += "))"
    search = TermString
    searchbuilder.search = search
    if request.method == "POST":
        return render_template("pubscraper.html", exposure_list=exposure_list, outcome_list=outcome_list,
                               exclusion_list=exclusion_list, search=search)


@app.route('/searchbuilder_5', methods=["GET", "POST"])
def searchurl():
    search_url = searchbuilder.search.replace(" ", "+") \
        .replace("(", "%28") \
        .replace(")", "%29") \
        .replace("[", "%5B") \
        .replace("/", "%2F") \
        .replace("]", "%5D") \
        .replace(",", "%2C")
    url_s = "https://pubmed.ncbi.nlm.nih.gov/?term="
    url = url_s + search_url
    searchurl.url = url
    if request.method == "POST":
        return render_template("pubscraper.html", exposure_list=exposure_list, outcome_list=outcome_list,
                               exclusion_list=exclusion_list, url=url)


@app.route('/pubscrape', methods=["GET", "POST"])
def pubscrape():
    if request.method == "POST":
        firstscrape = requests.get(searchurl.url).text
        # CREATE BEAUTIFUL SOUP
        firstsoup = BeautifulSoup(firstscrape, 'lxml')
        # FIND NUMBER OF RESULTS
        results_num = firstsoup.find("span", class_="value").text.replace(",", "")
        # CONVERT RESULTS NUMBER TO A FLOAT
        resultsnumfloat = float(results_num)
        # OBTAIN PAGE NUMBER FROM RESULTS AND MAXIMUM PAGE NUMBER (200)
        pages_num = math.ceil(resultsnumfloat / 200)
        ### print(pages_num)
        # CREATE A LIST OF THE PAGE NUMBERS
        pageList = list(range(1, pages_num + 1, 1))
        ### print(pageList)
        # URL VARIABLES
        URLsize = "&size=200"
        URLpage = "&page="
        ABSformat = "&format=abstract"
        # OPEN AND PREPARE CSV FILE TO HAVE RESULTS WRITTEN TO IT
        pm_df = pd.DataFrame(columns=["Title", "Author", "Year", "Abstract", "Full Text", "Database"])
        pm_df_abs = pd.DataFrame(columns=["Title", "Author", "Year", "Abstract", "Full Text", "Database"])
        pm_df_ft = pd.DataFrame(columns=["Title", "Author", "Year", "Abstract", "Full Text", "Database"])
        pm_rows = []
        # NESTED FOR LOOP SCRAPING ALL SEARCH RESULTS FOR TITLE, AUTHOR AND YEAR
        for i in pageList:
            URL = searchurl.url + '{}{}{}{}'.format(ABSformat, URLsize, URLpage, i)
            secondscrape = requests.get(URL).text
            secondsoup = BeautifulSoup(secondscrape, 'lxml')
            for study in secondsoup.find_all('div', class_="results-article"):
                title_raw = study.find('h1', class_="heading-title").text
                title_stripped = title_raw.replace("\n", "").replace("\t", "")
                title_stripped = re.sub("\s\s+", "", title_stripped)
                author_raw = study.find('span', class_="full-name").text
                author = author_raw + " et al"
                try:
                    year_raw = study.find('span', class_="cit").text
                    year = year_raw[0:4]
                except:
                    year = ""

                try:
                    abstract_raw = study.find('div', class_="abstract-content selected").text
                    abstract = abstract_raw.replace("\n", "").replace("\t", "")
                    abstract = re.sub("\s\s+", "", abstract)
                except:
                    abstract = ""
                try:
                    DOI_raw = study.find('span', class_="identifier doi").text
                    DOI_stripped = DOI_raw.replace("\n", "").replace("\t", "").replace("DOI:", "")
                    DOI_stripped = re.sub("\s\s+", "", DOI_stripped)
                    FT_URL = '<a href="https://doi.org/' + DOI_stripped + '">' + "Full Text" + '</a>'
                except:
                    FT_URL = ""
                pm_rows.append([title_stripped, author, year, abstract, FT_URL, "Medline"])
                pm_df = pd.DataFrame(data=pm_rows)
        pm_df.columns = ["Title", "Author", "Year", "Abstract", "Full Text", "Database"]
        pm_df_abs.columns = ["Title", "Author", "Year", "Abstract", "Full Text", "Database"]
        pm_df_ft.columns = ["Title", "Author", "Year", "Abstract", "Full Text", "Database"]
        print(pm_rows)
        print(pm_df)
        return render_template("pubscrape.html", results_num=results_num, data_frame=pm_df.to_html(table_id="table1",
                                                       classes="table table-striped table-bordered compact hover", escape=False),
                                                       data_frame_abs=pm_df_abs.to_html(table_id="table2",
                                                       classes="table table-striped table-bordered compact hover", escape=False),
                                                       data_frame_ft=pm_df_ft.to_html(table_id="table3",
                                                       classes="table table-striped table-bordered compact hover", escape=False)
                               )

