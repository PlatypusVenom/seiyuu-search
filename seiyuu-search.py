##################################################
## Takes a MyAnimeList username and a seiyuu's 
## name and outputs a list of characters the 
## seiyuu has voiced from the user's anime list.
##################################################
## Author: James M. Dale
## 2020, seiyuu-search
##################################################



import tkinter as tk
import requests
from requests.exceptions import RequestException
from bs4 import BeautifulSoup
from contextlib import closing
from urllib import parse

# Update headers to allow access to webpages
headers = requests.utils.default_headers()
headers.update({'User-Agent': 'Mozilla/5.0 (X11; Ubuntu; Linux x86_64; rv:52.0) Gecko/20100101 Firefox/52.0',})

########################################################################################
# https://www.pybloggers.com/2018/01/practical-introduction-to-web-scraping-in-python/ #
########################################################################################

def simple_get(url):
    """
    Attempts to get the content at `url` by making an HTTP GET request.
    If the content-type of response is some kind of HTML/XML, return the
    text content, otherwise return None.
    """
    try:
        with closing(requests.get(url, stream=True)) as resp:
            if is_good_response(resp):
                return resp.content
            else:
                return None
    except RequestException as e:
        print('Error during requests to {0} : {1}'.format(url, str(e)))
        return None

def is_good_response(resp):
    """
    Returns True if the response seems to be HTML, False otherwise.
    """
    content_type = resp.headers['Content-Type'].lower()
    return (content_type is not None # removed response code check
            and content_type.find('html') > -1)

########################################################################################
#                                   END OF CITATION                                    #
########################################################################################

class AnimeList():
    '''
    Represents a user's anime list from MyAnimeList.net.
    
    ...
    
    Attributes
    ----------
    username : str
        A MyAnimeList username.
    url : str
        The url of the specified user's anime list webpage.
    anime : list
        Contains a list of Anime from the anime list.
    anime_details : list
        Contains a dictionary of attributes for each anime on the anime list.
    is_valid : bool
        True if anime list is valid, False otherwise.
    '''
    
    def __init__(self, username):
        '''
        Parameters
        ----------
        username : str
            a MyAnimeList username
        
        Returns
        -------
        None.
        '''
        
        self.username = username
        self.url = 'https://myanimelist.net/animelist/' + username
        self.anime = []
        self.anime_details = []
        self.is_valid = False
        self.load_anime_list()
    
    def load_anime_list(self):
        '''
        Loads anime list webpage and extracts data into self.anime.
        
        ...

        Returns
        -------
        None.

        '''
        # Load anime list webpage and locate data
        mylist = simple_get(self.url)
        if mylist is None:
            return 
        mylist = mylist.decode('utf-8')
        i = mylist.find('data-items')+14
        mylist = mylist[i:mylist.find(']',i)-1]
        
        # Convert string to python-friendly syntax
        mylist = '{' + mylist + '}'
        r = ['&quot;',  '"',
             'null',    'None',
             'true',    'True',
             'false',   'False',
             '\\',      '']
        for i in range(int(len(r)/2)):
            mylist = mylist.replace(r[i*2], r[i*2+1])
        
        self.anime_details = list(eval(mylist))
        self.anime = [Anime(A['anime_title'],
                            'https://myanimelist.net' + A['anime_url']) for A in self.anime_details]
        self.is_valid = True

class Character():
    '''
    Represents an anime character.
    
    ...
    
    Attributes
    ----------
    seiyuu : Seiyuu
        The voice actor that plays this character.
    name : str
        The character's name.
    role : str
        The character's role. Main or Supporting.
    url : str
        The url of the character's webpage.
    anime : list
        Contains all anime that this character appears in.
    '''
    
    def __init__(self, seiyuu, name, role, url):
        '''
        Parameters
        ----------
        seiyuu : Seiyuu
            The voice actor that plays this character.
        name : str
            The character's name.
        role : str
            The character's role. Main or Supporting.
        url : str
            The url of the character's webpage.

        Returns
        -------
        None.
        '''
        self.seiyuu = seiyuu
        self.name = name
        self.role = role
        self.url = url
        self.anime = []

class Anime():
    '''
    Represents an anime series.
    
    ...
    
    Attributes
    ----------
    name : str
        The title of the anime.
    url : str
        The url of the anime webpage.
    '''
    
    def __init__(self, name, url):
        '''
        Parameters
        ----------
        name : str
            The title of the anime.
        url : str
            The url of the anime webpage.

        Returns
        -------
        None.

        '''
        self.name = name
        self.url = url

class Seiyuu():
    '''
    Represents an anime voice actor.
    
    ...
    
    Attributes
    ----------
    url : str
        The url of the voice actor's MyAnimeList webpage.
    characters : list
        Contains Characters played by the voice actor.
    '''
    
    def __init__(self, url):
        '''
        Parameters
        ----------
        url : str
            The url of the voice actor's MyAnimeList webpage.

        Returns
        -------
        None.
        '''
        self.url = url
        self.characters = []
        self.load_seiyuu()
        
    def load_seiyuu(self):
        '''
        Loads voice actor's MyAnimeList webpage and populates attributes.
        
        ...

        Returns
        -------
        None.
        '''
        soup = BeautifulSoup(simple_get(self.url), 'html.parser')
        rows = soup.find_all('table')[1].find_all('tr')
        for row in rows:
            a_name = row.find_all('td')[1].find('a').string.strip()
            a_url = row.find_all('td')[1].find('a').attrs['href']
            c_name = row.find_all('td')[2].find('a').string.strip()
            c_role = row.find_all('td')[2].find('div').string.strip()
            c_url = row.find_all('td')[2].find('a').attrs['href']
            if c_url not in [c.url for c in self.characters]:
                c = Character(self, c_name, c_role, c_url)
                self.characters.append(c)
                c.anime.append(Anime(a_name, a_url))
            else:
                for c in self.characters:
                    if c.url == c_url:
                        if a_url not in [a.url for a in c.anime]:
                            c.anime.append(Anime(a_name, a_url))
                        break

def search_seiyuu(search):
    '''
    Searches MyAnimeList voice actors with the search term and returns results.
    
    ...

    Parameters
    ----------
    search : str
        A search term for a voice actor.

    Returns
    -------
    seiyuu : dict
        A dictionary with a voice actor's name as the key and url as the value.
    '''
    
    seiyuu = {}
    url = 'https://myanimelist.net/people.php?q=' + parse.quote(search) + '&cat=person'
    soup = BeautifulSoup(simple_get(url), 'html.parser')
    
    if soup.title.string != 'Search People - MyAnimeList.net\n':
        return {soup.find('h1').string: soup.find('table').find_all('td')[1].find_all('div')[2].find('a').attrs['href']}
    
    rows = soup.find('table').find_all('tr')

    if len(rows) == 1 and not rows[0].find('a'):
        return seiyuu
    for row in rows:
        seiyuu[row.find_all('a')[1].string] = 'https://myanimelist.net' + row.find_all('a')[0].attrs['href']
    return seiyuu

class Main(tk.Tk):
    '''
    The root of the tkinter GUI.
    
    Attributes
    ----------
    anime_list : AnimeList
        Stores the inputted anime list.
    seiyuu_list : dict
        Stores voice actor search results.
    seiyuu : str
        Stores currently selected voice actor.
    state : int
        Keeps track of GUI states for disabling widgets.
    '''
    def __init__(self):
        '''
        Returns
        -------
        None.
        '''
        super().__init__()
        
        self.title('Seiyuu Search')
        self.columnconfigure(0, weight=1)
        self.columnconfigure(1, weight=1)
        self.rowconfigure(0, weight=1)
        
        self.anime_list = None
        self.seiyuu_list = {}
        self.seiyuu = None
        self.state = 0
        
        self.create_widgets()
        self.set_state(0)
    
    def create_widgets(self):
        '''
        Create initial widgets.

        Returns
        -------
        None.
        '''
        self.search_frame = tk.Frame(self, width=300)
        self.search_frame.grid(row=0, column=0, sticky='nsew')
        self.search_frame.rowconfigure(3, weight=1)
        
        self.message_label = tk.Label(self.search_frame, text='', relief='ridge')
        self.message_label.grid(row=0, column=0, columnspan=3, sticky='nsew')
        
        self.user_label = tk.Label(self.search_frame, text='MAL Username:')
        self.user_label.grid(row=1, column=0, sticky='nse')
        
        self.user_var = tk.StringVar()
        self.user_entry = tk.Entry(self.search_frame, textvariable=self.user_var, width=30)
        self.user_entry.grid(row=1, column=1, sticky='nsew')
        self.user_var.trace_add('write', self.user_callback)
        
        self.user_button = tk.Button(self.search_frame, text='Load', command=self.load_anime_list)
        self.user_button.grid(row=1, column=2, sticky='nsew')
        
        self.seiyuu_label = tk.Label(self.search_frame, text='Voice Actor:')
        self.seiyuu_label.grid(row=2, column=0, sticky='nse')
        
        self.seiyuu_var = tk.StringVar()
        self.seiyuu_entry = tk.Entry(self.search_frame, textvariable=self.seiyuu_var)
        self.seiyuu_entry.grid(row=2, column=1, sticky='nsew')
        self.seiyuu_var.trace_add('write', self.seiyuu_callback)
        
        self.seiyuu_button = tk.Button(self.search_frame, text='Search', command=self.load_seiyuu_list)
        self.seiyuu_button.grid(row=2, column=2, sticky='nsew')
        
        self.seiyuu_listbox = tk.Listbox(self.search_frame)
        self.seiyuu_listbox.grid(row=3, column=0, columnspan=3, sticky='nsew')
        
        self.char_button = tk.Button(self.search_frame, text='Search Characters', command=self.load_char_list)
        self.char_button.grid(row=4, column=0, columnspan=3, sticky='nsew')
        
        
        
        self.results_mainframe = tk.Frame(self)
        self.results_mainframe.grid(row=0, column=1, sticky='nsew')
        self.results_mainframe.columnconfigure(0, weight=1)
        self.results_mainframe.columnconfigure(1, weight=1)
        
        self.results_canvas = tk.Canvas(self.results_mainframe)
        self.results_frame = tk.Canvas(self.results_canvas)
        
        self.results_scrollbary = tk.Scrollbar(self.results_mainframe, orient="vertical", command=self.results_canvas.yview)
        self.results_scrollbarx = tk.Scrollbar(self.results_mainframe, orient="horizontal", command=self.results_canvas.xview)
        self.results_canvas.configure(yscrollcommand=self.results_scrollbary.set)
        self.results_canvas.configure(xscrollcommand=self.results_scrollbarx.set)
        
        self.results_scrollbary.grid(row=0, column=1, sticky='nse')
        self.results_scrollbarx.grid(row=1, column=0, sticky='new')
        self.results_canvas.grid(row=0, column=0, sticky='nsew')
        self.results_canvas.create_window((0,0), window=self.results_frame, anchor='nw')
        self.results_frame.bind("<Configure>", self.scroll)
    
    def scroll(self, event):
        '''
        Handles scroll events.
        
        Returns
        -------
        None.
        '''
        self.results_canvas.configure(scrollregion=self.results_canvas.bbox("all"),width=400,height=500)
    
    def user_callback(self, var, indx, mode):
        self.set_state(0)
    
    def seiyuu_callback(self, var, indx, mode):
        self.set_state(1)
    
    def set_state(self, state):
        '''
        Sets button state of GUI.

        Parameters
        ----------
        state : int
            The desired state of the GUI.

        Returns
        -------
        None.
        '''
        if state == 0:
            self.message_label.config(text='Load anime list from MAL username.')
            self.user_button.config(state='normal')
            self.seiyuu_entry.config(state='disabled')
            self.seiyuu_button.config(state='disabled')
            self.char_button.config(state='disabled')
        elif state == 1:
            self.message_label.config(text='Search for voice actor.')
            self.user_button.config(state='disabled')
            self.seiyuu_entry.config(state='normal')
            self.seiyuu_button.config(state='normal')
            self.char_button.config(state='disabled')
        elif state == 2:
            self.message_label.config(text='Select correct voice actor.')
            self.user_button.config(state='disabled')
            self.seiyuu_entry.config(state='normal')
            self.seiyuu_button.config(state='disabled')
            self.char_button.config(state='normal')
        self.state = state
    
    def load_anime_list(self):
        '''
        Creates and stores an AnimeList object.

        Returns
        -------
        None.
        '''
        user_var = self.user_var.get()
        if user_var.strip() == '':
            self.anime_list = None
            self.set_state(1)
            return
        self.anime_list = AnimeList(user_var)
        if not self.anime_list.is_valid:
            self.set_state(0)
            self.message_label.config(text='Error: invalid MAL username.')
        else:
            self.set_state(1)
    
    def load_seiyuu_list(self):
        '''
        Generates voice actor search results.

        Returns
        -------
        None.
        '''
        self.seiyuu_listbox.delete(0, 'end')
        self.seiyuu_list = search_seiyuu(self.seiyuu_var.get())
        if len(self.seiyuu_list.keys()) == 0:
            self.set_state(1)
            self.message_label.config(text='Error: no voice actors found.')
        else:
            self.set_state(2)
            for s in self.seiyuu_list.keys():
                self.seiyuu_listbox.insert('end', s)
    
    def load_char_list(self):
        '''
        Generates character search results.

        Returns
        -------
        None.
        '''
        k = self.seiyuu_listbox.get(self.seiyuu_listbox.curselection())
        self.seiyuu = Seiyuu(self.seiyuu_list[k])
        for child in self.results_frame.winfo_children():
            child.destroy()
        for i in range(len(self.seiyuu.characters)):
            c = self.seiyuu.characters[i]
            if self.anime_list != None and not any(item in [A.url for A in self.anime_list.anime] for item in [A.url for A in c.anime]):
                continue
            
            c_name = tk.Label(self.results_frame, text=c.name)
            a_frame = tk.Frame(self.results_frame)
            for j in range(len(c.anime)):
                a = c.anime[j]
                a_name = tk.Label(a_frame, text=a.name)
                a_name.grid(row=j, column=0, sticky='nw')
            
            c_name.grid(row=i, column=0, sticky='nw')
            a_frame.grid(row=i, column=1, sticky='nsw')

root = Main()
root.mainloop()