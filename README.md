# Dora's Information Science project

Welcome to this inefficient Rube Goldberg machine of code.

In my project, I constructed a pipeline of functions that exists in the main function that is run in the Jupyter notebook, query_DBPedia(). 
The user is prompted to input a query which is then cleaned of special characters and concatenated with a DBPedia prefix chosen by the function getAPIprefix() (provided in an email last week). 
The program then continues to a try-except block, where the function retrieve_xml() opens the concatenation of the prefix and query, if the response code of the request is 200 (working).



The etree element returned by the retrieve_xml() function is then parsed by the get_resources() function, which returns a list of resources.
The resource list is then converted into a list of json urls by the function resourcelist_to_jsonlist().
The etree element is also used to get a list of only booktitles from the results returned by the query. 


Both the booktitles_list and the json_url_list are passed into the choose_booktitle() function, which presents the user with buttons (containing the booktitle and author) for the user to choose from. 
The book_button() function, nested within the choose_booktitle() function, returns the index of the clicked button, which is then used to the get the corresponding json data, with the function get_json_data. 
The index is also used to to get the book resource URL, which is passed into the json dictionary.
The function find_languages() scans the json result and collects the language codes it finds in the 'abstract' sections. 
Finally, the json dictionary and the list of available languages is returned. 


The bookcover_finder() function searches the json_result dictionary for the key 'http://xmlns.com/foaf/0.1/isPrimaryTopicOf', giving me access to the linked Wikipedia article of the book. 
I decided to look for images of book covers, because Wikipedia articles reliably contain images, whereas the DBPedia data on To Kill a Mockingbird, for example, did not contain a link to an image of the book cover.
bookcover_finder() searches the XML of the corresponding Wikipedia Link for the book cover URL and returns it as a list object. 

choose_language() prints all of the available languages that are matched in a language_mapping dictionary that I defined in query_DBPedia. (I tried to make that dictionary exhaustive and included all the languages I could find in the DBPedia results, but I'm sure I missed some).
choose_language() uses the language codes in the abstract to print their corresponding keys, for example "English":"en". 
The user inputs the language of choice which is then returned as its corresponding language code. 


formatter() is used to strip linked URLs of useless characters and return only the relevant information. 
For example, I saw that sometimes the value for  the country of publication key, "http://dbpedia.org/property/country" was given as a URL, instead of a regular string. I wanted to return this as cleaned characters. 


formatter() is used often in the extract_bookmetadata(), which takes the json dictionary of the book and the language code.
The function extract_bookmetadata() initializes an empty dictionary to be filled in with the json data. 
The code performs a series of try-except blocks to collect metadata into keys and values if the corresponding key exists in the json dictionary, and to move on with "pass" if it doesn't. 


extract_authordata() is very similar, first opening the linked data in the "http://dbpedia.org/ontology/author" key, and performing the same steps as above. 
extract_authordata() initializes an empty dictionary and returns metadata about the author from the linked data in the original book json data. However, most DBPedia pages on authors contained a Wikicommons image link, which I stored in the string variable authorimage_url.

deuglifier() is the final step, displaying all of the keys and corresponding values from the dictionaries containing author and book data. At the head of both book and author sections, an image is printed of the book cover and author, respectively. 

***NOTE*** I used tkinter to create a button to allow the author to choose from a series of books returned by the API query. I hoped to go further with GUIs, but I failed to make a functioning GUI for when the user is prompted to choose a language. 
I wanted to include the little progress I had made with a GUI, so I left the original button that lets the user choose a book in.

In general, I wanted to include more buttons to give the user less of an opportunity to give invalid inputs that would mess up the code (misspelled languages, invalid yes/no responses, etc.) I will do more research to make sure I can make buttons work in more parts of my code. 
