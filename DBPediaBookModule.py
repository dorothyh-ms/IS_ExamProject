#!/usr/bin/env python
# coding: utf-8

# In[1]:


import json
import urllib.parse
import urllib.request
import urllib.error
from xml.etree import ElementTree as ET
import re
from IPython.display import display, HTML
from tkinter import *
from pprint import pprint

def query_DBPedia():
    """
    The main function of the exam project containing the function pipeline
    """
    dbpedia_prefix = 'https://lookup.dbpedia.org/api/prefix?query='
    search = input("Please input your search: ")
    search = clean(search)
    url = dbpedia_prefix + search
    try:
        root, resp_code = retrieve_xml(url)
        if resp_code == 200:
            resource_list = get_resources(root)
            json_url_list = resourcelist_to_jsonlist(resource_list)
            booktitles_list = get_booktitles(root)
            json_result, lang_list = choose_booktitle(booktitles_list, json_url_list, resource_list)
            bookcover_url = bookcover_finder(json_result)
            language_mapping = {'Chinese':'zh', 'Dutch':'nl', 'Portuguese':'pt', 'Japanese':'ja', "French":'fr',
               'Arabic':'ar', 'Polish':'pl',
               "Spanish":'es', 'English':'en',
               'Italian':"it", 'German': "de",
              'Russian': 'ru', "Korean": 'ko',
              "Ukranian": 'uk', "Swedish": 'sv'}
            lang_code = choose_language(lang_list, language_mapping)
            if lang_code in language_mapping.values():
                bookdata_dict = extract_bookmetadata(json_result, lang_code)
                authordata_dict, authorimage_url = extract_authordata(json_result, lang_code)
                deuglifier(bookdata_dict, authordata_dict, authorimage_url, bookcover_url)
            else:
                print("That language is not available. Please run your query again.")
        elif resp_code == 403:
            print("Error 403: request is forbidden.")
        elif resp_code == 404:
            print("Error 404: not found.")
        elif resp_code == 400:
            print("Error 400: bad request.")
        else:
            print("Please run your query again.")
    except TypeError:
        print("Please run your query again.")
    except urllib.error.URLError:
        print("Check your internet connection.")

def retrieve_xml(url) -> (ET.Element, int):
    """
    Get a parsed XML tree from the API query
    """
    with urllib.request.urlopen(url) as query:
        resp_code = query.code
        query = query.read()
        query = query.decode('UTF-8')
        root = ET.fromstring(query)
        return root, resp_code

def clean(string: str) -> str:
    """
    Clean input string and URL encode
    """
    string = string.strip()
    string = string.casefold()
    string = urllib.parse.quote(string)
    return string

def get_resources(root : bytes) -> list:
    """
    Parse the results and only keep URIs of books
    """
    resource_list = []
    for x in root.findall("Result"):
        item = x.find("Label")
        cl = x.find("Classes")
        for c in cl.findall("Class"):
            label = c.find("Label")
            if label.text == "Book":
                uri = x.find("URI")
                resource_list.append(uri.text)
    return resource_list

def resourcelist_to_jsonlist(resource_list: list) -> list:
    """
    Change the URIs into URLs that can get JSON data
    """
    json_url_list = []
    for string1 in resource_list:
        newstring = ""
        newstring = re.sub('resource', 'data', string1)
        newstring += ".json"
        json_url_list.append(newstring)
    return json_url_list

def get_booktitles(root : bytes) -> list:
    """
    Parse the results and only keep the results that are titles of books
    """
    booktitles_list = []
    for x in root.findall("Result"):
        item = x.find("Label")
        cl = x.find("Classes")
        for c in cl.findall("Class"):
            label = c.find("Label")
            if label.text == "Book":
                booktitles_list.append(item.text)
    return booktitles_list

def get_json_data(json_url) -> dict:
    """
    Use a JSON URL to get its results as a dictionary
    """
    with urllib.request.urlopen(json_url) as query:
        result = query.read()
        parsed_result = json.loads(result)
        return parsed_result

def get_authorname(json_result) -> str:
    """
    Read a JSON dictionary using the book's URI and extract the author's name as a string
    """
    for k, v in json_result.items():
        if k == "http://dbpedia.org/ontology/author":
            author_resource = v[0]['value']
            author = re.findall('(?<=resource\/)(.+)', author_resource)
            for a in author:
                author_formatted = re.sub("_", " ", a)
            return author_formatted

def book_button(booktitles_list, json_url_list, resource_list) -> int:
    """
    Create buttons for a user to click on a book - returns the index of the clicked button in the button list
    """
    root = Tk()
    btn = []
    authors = []
    label = Label(root, text="Please choose from the following options:")
    label.grid(row=0)
    for k in range(len(booktitles_list)):
        json_dict = get_json_data(json_url_list[k])
        book_resource = resource_list[k]
        json_result = json_dict[book_resource]
        author = get_authorname(json_result)
        authors.append(author)
    def get_button_index():
        global choice_index
        choice_index = i
        root.destroy()
    for i in range(0, len(booktitles_list)):
        btn.append(Button(command = get_button_index, text = booktitles_list[i] + " - Written by: " + authors[i]))
        btn[i].grid(row = i+1)
    root = mainloop()
    return choice_index

def find_languages(json_result) -> list:
    """
    Loop through and collect all of the languages found in the abstract section of the JSON book metadata as a list
    """
    description_list = json_result['http://dbpedia.org/ontology/abstract']
    lang_list = []
    for description in description_list:
        lang = description["lang"]
        lang_list.append(lang)
    return lang_list

def choose_booktitle(booktitles_list, json_url_list, resource_list) -> (list, list):
    """
    Loop through a list of book titles to let the user choose one, returning a list of json data and languages
    """
    if len(booktitles_list) == 0:
        print("Your query did not return any results.")
    else:
        choice_index = book_button(booktitles_list, json_url_list, resource_list)
        json_dict = get_json_data(json_url_list[choice_index])
        book_resource = resource_list[choice_index]
        json_result = json_dict[book_resource]
        lang_list = find_languages(json_result)
        return json_result, lang_list

def bookcover_finder(json_result) -> list:
    """
    Get a the linked Wikipedia URL and retrieve its Wikimedia image url of the book cover, returning a list object
    """
    wikipedia_link = json_result['http://xmlns.com/foaf/0.1/isPrimaryTopicOf'][0]['value']
    query = urllib.request.urlopen(wikipedia_link)
    query = query.read()
    query = query.decode('utf-8')
    query
    matches = re.findall('(?<=<meta property="og:image" content=").*(?="\/>)', query)
    return matches

def choose_language(lang_list, language_mapping) -> str:
    """
    Allow the user to choose the language for the book and author description, returning a language code string object
    """
    print("The description of this book is available in the following languages: ")
    for lang in lang_list:
        for k, langcode in language_mapping.items():
            if lang == langcode:
                print(k)
    language = input("Please input a language: ")
    language = language.strip()
    language = language.casefold()
    for k, langcode in language_mapping.items():
        if language == k.lower():
            return langcode
def formatter(json_list) -> list:
    """
    If the value in a JSON dictionary is a hyperlink, this function cleans the hyperlink into text, returning a list object
    """
    formatted_list = []
    for item in json_list:
        i = item['value']
        i = re.findall('(?<=resource\/)(.+)', i)
        i_formatted = re.sub("_", " ", i[0])
        formatted_list.append(i_formatted)
    return formatted_list

def extract_bookmetadata(json_result, language) -> dict:
    """
    Read a JSON dictionary and return a cleaned, readable dictionary with relevant metadata
    """
    bookdata_dict = {}
    try:
        bookdata_dict["Caption: "] = json_result['http://dbpedia.org/property/caption'][0]['value']
    except KeyError:
        pass
    try:
        bookdata_dict["Cover Artist: "] = json_result['http://dbpedia.org/property/coverArtist'][0]['value']
    except KeyError:
        pass
    try:
        bookdata_dict["Date Published: "] = json_result['http://dbpedia.org/property/published'][0]["value"]
    except KeyError:
        pass
    try:
        if json_result['http://dbpedia.org/ontology/mediaType'][0]['value'][0:4] == "http":
            mediaType = json_result['http://dbpedia.org/ontology/mediaType']
            mediaType = formatter(mediaType)
            bookdata_dict['Media Type: '] = mediaType
        else:
            bookdata_dict["Media Type: "] = json_result['http://dbpedia.org/ontology/mediaType'][0]['value']
    except KeyError:
        pass
    try:
        if json_result['http://dbpedia.org/property/mediaType'][0]['value'][0:4] == "http":
            mediaType = json_result['http://dbpedia.org/property/mediaType']
            mediaType = formatter(mediaType)
            bookdata_dict['Media Type: '] = mediaType
        else:
            bookdata_dict["Media Type: "] = json_result['http://dbpedia.org/property/mediaType'][0]['value']
    except KeyError:
        pass
    try:
        bookdata_dict["Release Date: "] = json_result['http://dbpedia.org/ontology/releaseDate'][0]['value']
    except KeyError:
        pass
    try:
        bookdata_dict["Number of Pages: "] = json_result['http://dbpedia.org/ontology/numberOfPages'][0]['value']
    except KeyError:
        pass
    try:
        if json_result['http://dbpedia.org/property/country'][0]['value'][0:4] == "http":
            pub_country = json_result['http://dbpedia.org/property/country']
            pub_country = formatter(pub_country)
            bookdata_dict['Country of Publication: '] = pub_country
        else:
            bookdata_dict["Country of Publication: "] = json_result['http://dbpedia.org/property/country'][0]['value']
    except KeyError:
        pass
    try:
        bookdata_dict["Language of Publication: "] = json_result['http://dbpedia.org/property/language'][0]['value']
    except KeyError:
        pass
    try:
        bookdata_dict["Publisher: "] = json_result['http://purl.org/dc/elements/1.1/publisher'][0]['value']
    except KeyError:
        pass
    try:
        bookdata_dict['LCC: '] = json_result['http://dbpedia.org/ontology/lcc'][0]['value']
    except KeyError:
        pass
    try:
        if json_result['http://dbpedia.org/ontology/previousWork'][0]['value'][0:4] == "http":
            precededby = json_result['http://dbpedia.org/ontology/previousWork']
            precededby = formatter(precededby)
            bookdata_dict['Previous Work: '] = precededby
        else:
            bookdata_dict["Previous Work: "] = json_result['http://dbpedia.org/ontology/previousWork'][0]['value']
    except KeyError:
        pass
    try:
        if json_result['http://dbpedia.org/ontology/subsequentWork'][0]['value'][0:4] == "http":
            subsequent = json_result['http://dbpedia.org/ontology/subsequentWork']
            subsequent = formatter(subsequent)
            bookdata_dict['Subsequent Work: '] = subsequent
        else:
            bookdata_dict["Subsequent Work: "] = json_result['http://dbpedia.org/ontology/subsequentWork'][0]['value']
    except KeyError:
        pass
    try:
        if json_result['http://dbpedia.org/ontology/publisher'][0]['value'][0:4] == "http":
            publisher = json_result['http://dbpedia.org/ontology/publisher']
            publisher = formatter(publisher)
            bookdata_dict['Publisher: '] = publisher
        else:
            bookdata_dict["Publisher: "] = json_result['http://dbpedia.org/ontology/publisher'][0]['value']
    except KeyError:
        pass
    try:
        genrelist = []
        genres = json_result['http://dbpedia.org/ontology/literaryGenre']
        for genre in genres:
            g = genre['value']
            g = re.findall('(?<=resource\/)(.+)', g)
            g_formatted = re.sub("_", " ", g[0])
            genrelist.append(g_formatted)
        bookdata_dict["Genre: "] = genrelist
    except KeyError:
        pass
    try:
        abstract_list = json_result['http://dbpedia.org/ontology/abstract']
        for abstract in abstract_list:
            if abstract["lang"] == language:
                bookdata_dict['Book Description: '] = abstract['value']
    except KeyError:
        pass
    return bookdata_dict

def extract_authordata(json_result, language) -> (dict, str):
    """
    Read a JSON dictionary and return a cleaned, readable dictionary with relevant metadata about the author
    """
    for k, v in json_result.items():
        if k == "http://dbpedia.org/ontology/author":
            author_resource = v[0]['value']
    author_json_url = ""
    author_json_url = re.sub('resource', 'data', author_resource)
    author_json_url += ".json"
    author_json_result = get_json_data(author_json_url)
    #pprint(author_json_result[author_resource])
    authordata_dict = {}
    try:
        authordata_dict["Birth name: "] = author_json_result[author_resource]['http://dbpedia.org/ontology/birthName'][0]["value"]
    except KeyError:
        pass
    try:
        authordata_dict["Gender: "] = author_json_result[author_resource]['http://xmlns.com/foaf/0.1/gender'][0]['value']
    except KeyError:
        pass
    try:
        birthplaces = author_json_result[author_resource]['http://dbpedia.org/ontology/birthPlace']
        birthlist = formatter(birthplaces)
        authordata_dict["Place of birth: "] = birthlist
    except KeyError:
        pass
    try:
        deathplaces = author_json_result[author_resource]['http://dbpedia.org/ontology/deathPlace']
        deathlist = formatter(deathplaces)
        authordata_dict["Place of death: "] = deathlist
    except KeyError:
        pass
    try:
        authordata_dict["Date of birth: "] = author_json_result[author_resource]['http://dbpedia.org/ontology/birthDate'][0]['value']
    except KeyError:
        pass
    try:
        authordata_dict["Date of death: "] = author_json_result[author_resource]['http://dbpedia.org/ontology/deathDate'][0]['value']
    except KeyError:
        pass
    try:
        authordata_dict["Pseudonym: "] = author_json_result[author_resource]['http://dbpedia.org/ontology/pseudonym'][0]['value']
    except KeyError:
        pass
    try:
        if author_json_result[author_resource]['http://dbpedia.org/property/nationality'][0]['value'][0:4] == "http":
            nationality = author_json_result[author_resource]['http://dbpedia.org/property/nationality']
            nationality = formatter(nationality)
            authordata_dict['Nationality: '] = nationality
        else:
            authordata_dict["Nationality: "] = author_json_result[author_resource]['http://dbpedia.org/property/nationality'][0]['value']
    except KeyError:
        pass
    try:
        colleges = author_json_result[author_resource]['http://dbpedia.org/ontology/almaMater']
        college_list = formatter(colleges)
        authordata_dict["Alma mater: "] = college_list
    except KeyError:
        pass
    try:
        influences = author_json_result[author_resource]['http://dbpedia.org/ontology/influencedBy']
        influencelist = formatter(influences)
        authordata_dict["Influenced by: "] = influencelist
    except KeyError:
        pass
    try:
        movements = author_json_result[author_resource]['http://dbpedia.org/ontology/movement']
        movementlist = formatter(movements)
        authordata_dict["Movement: "] = movementlist
    except KeyError:
        pass
    try:
        spouses = author_json_result[author_resource]['http://dbpedia.org/ontology/spouse']
        spouselist = formatter(spouses)
        authordata_dict["Spouse: "] = spouselist
    except KeyError:
        pass
    try:
        notableworks = author_json_result[author_resource]['http://dbpedia.org/ontology/notableWork']
        workslist = formatter(notableworks)
        authordata_dict["Notable works: "] = workslist
    except KeyError:
        pass
    try:
        abstract_list = author_json_result[author_resource]['http://dbpedia.org/ontology/abstract']
        for abstract in abstract_list:
            if abstract["lang"] == language:
                authordata_dict['Author description: '] = abstract['value']
    except KeyError:
        pass
    try:
        authorimage_url = author_json_result[author_resource]['http://xmlns.com/foaf/0.1/depiction'][0]['value']
    except KeyError:
        pass
    return authordata_dict, authorimage_url

def deuglifier(bookdata_dict, authordata_dict, authorimage_url, bookcover_url):
    """
    Display the relevant metadata with HTML formatting
    """
    from IPython.display import display, HTML
    display(HTML("<h1 style='text-align:center;'>"+ "Book Data" + "</h1>"))
    display(HTML('<p>' + '<img width=200 src=' + bookcover_url[0] + "></img>" + "</p>"))
    for k, v in bookdata_dict.items():
        if type(v) == list:
            display(HTML("<h2>"+ str(k) + "</h2>"))
            for item in v:
                display(HTML("<p>"+ str(item) + "</p>"))
        else:
            display(HTML("<h2>"+ str(k) + "</h2>"))
            display(HTML("<p>"+ str(v) + "</p>"))
    display(HTML("<h1 style='text-align:center;'>"+ "Author Data" + "</h1>"))
    display(HTML('<p>' + '<img width=200 src=' + authorimage_url +"></img>" + "</p>"))
    for k, v in authordata_dict.items():
        if type(v) == list:
            display(HTML("<h2>"+ str(k) + "</h2>"))
            for item in v:
                display(HTML("<p>"+ str(item) + "</p>"))
        else:
            display(HTML("<h2>"+ str(k) + "</h2>"))
            display(HTML("<p>"+ str(v) + "</p>"))



# In[2]:





# In[ ]:
