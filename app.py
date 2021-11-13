from flask import Flask, render_template, request
from bs4 import BeautifulSoup
import re
import math
import pandas as pd
import requests
import lxml
import csv
import numpy as np

app = Flask(__name__)


@app.route('/')
@app.route('/home')
def home():  # put application's code here
    return render_template("index.html")


@app.route('/about')
def about():
    return render_template("about.html")


@app.route('/portfolio')
def portfolio():
    return render_template("portfolio.html")


@app.route('/ww_obesity')
def ww_obesity():
    return render_template("written_work/ww_obesity.html")

@app.route('/ww_quorn')
def ww_quorn():
    return render_template("written_work/ww_quorn.html")

@app.route('/ww_habit')
def ww_habit():
    return render_template("written_work/ww_habit.html")

@app.route('/ww_bsc_diss')
def ww_bsc_diss():
    return render_template("written_work/ww_bsc_diss.html")

@app.route('/ww_msc_diss')
def ww_msc_diss():
    return render_template("written_work/ww_msc_diss.html")

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
        return render_template("pubscrape_results.html", results_num=results_num, data_frame=pm_df.to_html(table_id="table1",
                                                       classes="display", escape=False),
                                                       data_frame_abs=pm_df_abs.to_html(table_id="table2",
                                                       classes="display", escape=False),
                                                       data_frame_ft=pm_df_ft.to_html(table_id="table3",
                                                       classes="display", escape=False)
                               )


@app.route('/football', methods=["GET", "POST"])
def football_stats():
    stats_list = ['Non-Penalty Goals', 'npxG+xA', 'Goals', 'Shots Total',
                  'Shots on target', 'Shots on target %', 'Goals/Shot',
                  'Goals/Shot on target', 'Average Shot Distance',
                  'Shots from free kicks', 'Penalty Kicks Made',
                  'Penalty Kicks Attempted', 'xG', 'npxG', 'npxG/Sh',
                  'Goals - xG', 'Non-Penalty Goals - npxG', 'Passes Completed',
                  'Passes Attempted', 'Pass Completion %', 'Total Passing Distance',
                  'Progressive Passing Distance', 'Passes Completed (Short)',
                  'Passes Attempted (Short)', 'Pass Completion % (Short)',
                  'Passes Completed (Medium)', 'Passes Attempted (Medium)',
                  'Pass Completion % (Medium)', 'Passes Completed (Long)',
                  'Passes Attempted (Long)', 'Pass Completion % (Long)',
                  'Assists', 'xA', 'Key Passes', 'Passes into Final Third',
                  'Passes into Penalty Area', 'Crosses into Penalty Area',
                  'Progressive Passes', 'Passes Attempted', 'Live-ball passes',
                  'Dead-ball passes', 'Passes from Free Kicks', 'Through Balls',
                  'Passes Under Pressure', 'Switches', 'Crosses', 'Corner Kicks',
                  'Inswinging Corner Kicks', 'Outswinging Corner Kicks', 'Straight Corner Kicks',
                  'Ground passes', 'Low Passes', 'High Passes', 'Passes Attempted (Left)',
                  'Passes Attempted (Right)', 'Passes Attempted (Head)', 'Throw-Ins taken',
                  'Passes Attempted (Other)', 'Passes Completed', 'Passes Offside', 'Passes Out of Bounds',
                  'Passes Intercepted', 'Passes Blocked', 'Shot-Creating Actions', 'SCA (PassLive)',
                  'SCA (PassDead)', 'SCA (Drib)', 'SCA (Sh)', 'SCA (Fld)', 'SCA (Def)',
                  'Goal-Creating Actions', 'GCA (PassLive)', 'GCA (PassDead)',
                  'GCA (Drib)', 'GCA (Sh)', 'GCA (Fld)', 'GCA (Def)', 'Tackles',
                  'Tackles Won', 'Tackles (Def 3rd)', 'Tackles (Mid 3rd)',
                  'Tackles (Att 3rd)', 'Dribblers Tackled', 'Dribbles Contested',
                  '% of dribblers tackled', 'Dribbled Past', 'Pressures',
                  'Successful Pressures', 'Successful Pressure %', 'Pressures (Def 3rd)',
                  'Pressures (Mid 3rd)', 'Pressures (Att 3rd)', 'Blocks', 'Shots Blocked',
                  'Shots Saved', 'Passes Blocked', 'Interceptions', 'Tkl+Int', 'Clearances',
                  'Errors', 'Touches', 'Touches (Def Pen)', 'Touches (Def 3rd)', 'Touches (Mid 3rd)',
                  'Touches (Att 3rd)', 'Touches (Att Pen)', 'Touches (Live-Ball)', 'Dribbles Completed',
                  'Dribbles Attempted', 'Successful Dribble %', 'Players Dribbled Past', 'Nutmegs', 'Carries',
                  'Total Carrying Distance', 'Progressive Carrying Distance', 'Progressive Carries',
                  'Carries into Final Third', 'Carries into Penalty Area', 'Miscontrols', 'Dispossessed',
                  'Pass Targets', 'Passes Received', 'Passes Received %', 'Progressive Passes Rec', 'Yellow Cards',
                  'Red Cards', 'Second Yellow Card', 'Fouls Committed', 'Fouls Drawn', 'Offsides',
                  'Crosses', 'Interceptions', 'Tackles Won', 'Penalty Kicks Won', 'Penalty Kicks Conceded',
                  'Own Goals', 'Ball Recoveries', 'Aerials won', 'Aerials lost', '% of Aerials Won']
    position_list = ["CB", "FB", "MF", "AM", "FW"]
    if request.method == "POST":
        player = request.form.get("football_stats")
        position = request.form.get("football_stats")
        print(player)
        print(position)
    return render_template("football_player_stats.html.", stats_list=stats_list, position_list=position_list)




if __name__ == '__main__':
    app.run()
