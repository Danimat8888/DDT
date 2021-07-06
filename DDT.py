""" Importación de librerias necesarias
"""
import tweepy
import twint
import tkinter as tk
from tkinter import ttk
import pandas as pd
from tkinter import *
from tkinter.ttk import *
from tkinter.scrolledtext import *
from queue import Queue
import threading
import datetime
import time
import aiohttp


""" Declaración variables globales """


CONSOLE_TEMPLATE = '{}: {}\n'
TWEET_TEXT_TEMPLATE = '{:500}'
Tweets_df = pd.DataFrame()
SEP = ";"
resultString = ""
resultString2 = ""


""" Función que ordena el DataFrame en la visualización en pantalla en la búsqueda en el histórico """


def treeview_sort_column(tv, col, reverse):
  l = [(tv.set(k, col), k) for k in tv.get_children('')]
  l.sort(reverse=reverse)
  for index, (val, k) in enumerate(l):
    tv.move(k, '', index)
  tv.heading(col, text=col, command=lambda _col=col: \
    treeview_sort_column(tv, _col, not reverse))

""" Método que realiza búsqueda en el histórico de Twitter mediante Twint, filtrando por diferentes campos la búsqueda """


def search():
    global complete_df
    try:
      c = twint.Config()
      c.Search = palabraString.get()
      c.Since = FechaInicioString.get()
      c.Until = FechaFinString.get()
      if CiudadString.get():
        c.Near = CiudadString.get()
      if UsuarioString.get():
        c.Username = UsuarioString.get()
      if LimiteInt.get():
        c.Limit = LimiteInt.get()
      else:
        c.Limit = 100000
      c.User_full = True
      c.Pandas = True
      c.Hide_output = True
      twint.run.Search(c)
      resultString.set("Busqueda Finalizada")
      global Tweets_df
      complete_df = twint.storage.panda.Tweets_df
    except aiohttp.client_exceptions.ClientPayloadError:
        time.sleep(2)
        twint.run.Search(c)
    except aiohttp.client_exceptions.ClientConnectorError:
        time.sleep(5)
        twint.run.Search(c)
    except aiohttp.client_exceptions.ClientOSError:
        time.sleep(10)
        twint.run.Search(c)
    except ConnectionResetError:
        time.sleep(5)
        twint.run.Search(c)
    if complete_df.empty:
        resultString.set("Busqueda Finalizada Sin Resultados")
    # Si encuentra resultados muestra en pantalla filtrando por campos y ordenando en un data frame.
    else:
        root = tk.Tk()
        root.title("TWEET ENCONTRADOS QUE CONTIENEN:" + " ' " + palabraString.get() + " ' ")
        root.geometry("+0+500")
        Tweets_df = complete_df.filter(items=['username', 'date', 'time', 'near', 'tweet'])
        Tweets_df['date'] = pd.to_datetime(Tweets_df['date'])
        Tweets_df.rename(columns={'username': 'Usuario','date': 'Fecha','time': 'Hora', 'near' : 'Ubicacion', 'tweet': 'Tweet'},inplace=True)
        cols = list(Tweets_df.columns)
        tree = ttk.Treeview(root)
        vsb = ttk.Scrollbar(root, orient="vertical", command=tree.yview)
        vsb.pack(side='right', fill='y')
        tree.configure(yscrollcommand=vsb.set)
        hsb = ttk.Scrollbar(root, orient="horizontal", command=tree.xview)
        hsb.pack(side='bottom', fill='x')
        tree.configure(xscrollcommand=hsb.set)
        tree.pack(fill='x')
        tree.pack(fill='y')
        tree["columns"] = cols
        treeview_sort_column(tree, 'Fecha', True)
        for i in cols:
            tree.column(i, anchor="w")
            tree.heading(i, text=i, anchor='w')
            if i == 'Usuario':
                tree.column(i, width=110, anchor="w")
                tree.heading(i, text=i, anchor='w')
                treeview_sort_column(tree, 'Usuario', True)
            if i == 'Fecha':
                tree.column(i, width=140, anchor="w")
                tree.heading(i, text=i, anchor='w')
                treeview_sort_column(tree, 'Fecha', False)
            if i == 'Ubicacion':
                tree.column(i, width=100, anchor="w")
                tree.heading(i, text=i, anchor='w')
                treeview_sort_column(tree, 'Ubicacion', True)
            if i == 'Tweet':
                tree.column(i, width=1400, anchor="w")
                tree.heading(i, text=i, anchor='w')
                treeview_sort_column(tree, 'Tweet', True)
        for index, row in Tweets_df.iterrows():
            tree.insert("", 0, text=index, values=list(row))
    root.mainloop()

""" Método para guardar la búsqueda realizada en el histórico de tweets de Twitter, filtrando los campos que interesan"""


def storesearch():
  Tweets_df.to_excel("./" + palabraString.get() + FechaInicioString.get() + FechaFinString.get() + CiudadString.get() + UsuarioString.get() + ".xlsx", index=False)
  resultString2.set("Archivo Guardado")


""" Clase para la escucha de los Tweets en streaming, para guardarlos en un fichero csv y mostrarlos en pantalla, utlizando Tweepy """


class StdOutListener(tweepy.StreamListener):

    #Método constructor de la clase
    def __init__(self, gui):
        super().__init__()
        self.gui = gui
        csv = open(palabraString.get() + '.csv', 'a', encoding="utf-8")
        csv.write('Fecha' + SEP + 'Usuario' + SEP + 'Ubicacion' + SEP  + 'Tweet\n')

    #Método mientras se va recibiendo la captura de tweets, los guarda en un fichero csv y los muestra en pantalla, filtrando campos
    def on_status(self, status):
        with open(palabraString.get() + '.csv', 'a', encoding="utf-8") as f:
            Created = status.created_at.strftime("%Y-%m-%d-%H:%M:%S")
            if hasattr(status, 'retweeted_status'):
                try:
                    Text = status.retweeted_status.extended_tweet["full_text"].replace('\n', ' ').replace('\r', '').replace(SEP, ' ')
                except:
                    Text = status.retweeted_status.text.replace('\n', ' ').replace('\r', '').replace(SEP, ' ')
            else:
                try:
                    Text = status.extended_tweet["full_text"].replace('\n', ' ').replace('\r', '').replace(SEP, ' ')
                except AttributeError:
                    Text = status.text.replace('\n', ' ').replace('\r', '').replace(SEP, ' ')
            Location = status.user.location
            Name = status.user.screen_name
            f.write(str(Created) + SEP + str(Name) + SEP + str(Location) + SEP + str(Text.encode('ASCII', 'ignore')) + '\n')
            tweet_text = 'Fecha: %s' ' | ' 'Usuario: %s' ' | ' 'Ubicacion: %s\n' '   Tweet: %s\n' '--------------------------------------------------------------------------------------------------------------------------------------------------------------------------' \
                         % (Created,Name,Location,Text)
            self.gui.tweet_q.put(tweet_text)
            if self.gui.window.winfo_exists() == 1:
                self.gui.window.event_generate('<<new_tweet>>', when='tail')
            else:
               f.close()

    # En caso de error en el scrapping de tweets
    def on_error(self, status):
        if status == 420:
            print("Encontrado error 420. Desconectando streaming...")
            return False
        else:
            print("Encontrado error con codigo:{}".format(status))
            return True

    # en caso de problemas en la conexión
    def on_timeout(self):
        print("Timeout...")
        return True

""" Método  que inicia la conexión con el API de Twitter para la búsqueda en tiempo real, identificandose e iniciando el streaming """


def init_stream(gui):
    try:
        print('Iniciando captura tweets en streaming...')
        listener = StdOutListener(gui)
        auth = tweepy.OAuthHandler("tXaz8uEL7FyHXbPijitzXYayb", "wExvbZzodkaLYAm2U5mdNBddZxM88VellhAvCxudkkWCfDsvbf")
        auth.set_access_token("1388616558965108736-rR6gKPeDGe7ah4H6gHxYtyC3APjpDr","R3r83A1hATCeDkzyoJttFN46oaOT9gWu6je7NRadQBPRg")
        stream = tweepy.Stream(auth, listener,tweet_mode='extended')
        stream.filter(track=[palabraString.get()])
    except KeyboardInterrupt:
        print("%s - Interrupcion por teclado. Cerrando streaming y saliendo." % datetime.now())
        stream.disconnect()
        pass
    except tweepy.RateLimitError:
        print("Error, Límite sobrepasado. Esperando 15 minutos para continuar...")
        time.sleep(900)
        stream = tweepy.Stream(auth, listener, tweet_mode='extended')
        stream.filter(track=[palabraString.get()])
    except tweepy.TweepError as e:
        if 'Fallo al enviar petición:' in e.reason:
            print("Error de timeout")
            time.sleep(900)
            stream = tweepy.Stream(auth, listener,tweet_mode='extended')
            stream.filter(track=[palabraString.get()])
        else:
            print("Otro Error leyendo...")
            pass

""" Clase que crea la ventana en pantalla con los tweets que se van capturando en la búsqueda en tiempo real, para mostrarlos """


class TwitterGui:

    #Método constructor de la clase que crea la ventana
    def __init__(self, window, tweet_q):
        self.tweet_q = tweet_q
        self.display_q = Queue()
        self.window = window
        self.output_tweet_text = StringVar()
        self.current_tweet = None
        self.tweet_input = StringVar()
        self.console_frame = Frame(window)
        self.console_frame.grid(row=3, column=0, columnspan=3)
        self.tweet_console = ScrolledText(self.console_frame, wrap=WORD, width=170, height=40)
        self.tweet_console.pack()
        self.output_label = Label(window, textvariable=self.output_tweet_text)
        self.output_label.grid(row=0, column=2, rowspan=2)
        self.output_label.config(wraplength=600)
        Button(window,text="Salir Programa", command=self.quit).grid(row=2, column=0)
        Button(window,text="Volver a Pantalla Principal", command=self.volver).grid(row=1, column=0)
        self.scroll()
        self.number = 0
        self.live_tweets = {}

    #método que numera los tweets capturdados
    def next_number(self):
        self.number += 1
        return self.number

    #Método que define cuando se captura un nuevo tweet
    def on_new_tweet(self, *args):
        if not self.tweet_q.empty():
            new_tweet_data = self.tweet_q.get()
            self.add_tweet(new_tweet_data)

    #Método que añade un nuevo tweet capturado
    def add_tweet(self, tweet_text):
        new_tweet = Tweet(tweet_text, self.next_number())
        self.display_q.put(new_tweet)
        self.live_tweets[new_tweet.number] = new_tweet
        self.update_console()

    #método que actualiza la pantalla con nuevo tweet
    def update_console(self):
        console_text = ''
        for tweet_num in sorted(self.live_tweets.keys()):
            tweet = self.live_tweets[tweet_num]
            console_text += CONSOLE_TEMPLATE.format(tweet.number, tweet.text)
        self.tweet_console.delete('1.0', END)
        self.tweet_console.insert(INSERT, console_text)

    #Método para el scrolling en la pantalla que muestra tweets capturados
    def scroll(self):
        if not self.display_q.empty():
            if self.current_tweet: self.display_q.put(self.current_tweet)
            self.current_tweet = self.display_q.get()
            self.output_tweet_text.set(self.current_tweet.text)
        self.window.after(5000, self.scroll)

    #Método que paraliza la búsqueda en tiempo real y vuelve a la pantalla principal del programa
    def volver(self):
        self.window.destroy()
        if 'normal' != app.state():
            app.deiconify()

    #Método para salir del programa desde la búsqueda en tiempo real
    def quit(self):
        self.window.destroy()
        app.destroy()

""" Clase que crea los Tweets en el formato escogido para mostrar """


class Tweet:
    def __init__(self, text, number):
        self.text = TWEET_TEXT_TEMPLATE.format(text)
        self.number = number
        self.is_live = True

"""Método para realizar la búsqueda en tiempo real """


def searchtimereal():
    window = Toplevel()
    window.title("BUSCANDO Y GUARDANDO EN TIEMPO REAL TWEETS CON EL TEXTO: " + " ' " + palabraString.get() + " ' ")
    tweet_q = Queue()
    gui = TwitterGui(window, tweet_q)
    window.bind('<<new_tweet>>', gui.on_new_tweet)
    t1 = threading.Thread(target=init_stream, args=(gui,))
    t1.setDaemon(True)
    gui.stream_thread = t1
    t1.start()


""" Creación pantalla inicial, menú principal del programa"""


app = tk.Tk()
app.geometry('800x300')
app.title(" DDT: BUSQUEDA DE DELITOS EN TWITTER")
labelpalabra = tk.Label(app,text="Palabra a buscar: ")
labelpalabra.grid(column=0, row=0, sticky=tk.W)
labelFechaInicio = tk.Label(app, text="Desde Fecha: (yyyy-mm-dd) ")
labelFechaInicio.grid(column=0, row=1, sticky=tk.W)
labelFechaFin = tk.Label(app, text="Hasta fecha: (yyyy-mm-dd) ")
labelFechaFin.grid(column=0, row=2, sticky=tk.W)
labelCiudad = tk.Label(app, text="En Ciudad: ")
labelCiudad.grid(column=0, row=3, sticky=tk.W)
labelUsuario = tk.Label(app, text="De Usuario: ")
labelUsuario.grid(column=0, row=4, sticky=tk.W)
labelLimite = tk.Label(app, text="Número Máximo Tweets: \n (por defecto 100.000)")
labelLimite.grid(column=0, row=5, sticky=tk.W)
palabraString = tk.StringVar()
FechaInicioString = tk.StringVar()
FechaFinString = tk.StringVar()
CiudadString = tk.StringVar()
UsuarioString = tk.StringVar()
LimiteInt = tk.StringVar()
entrypalabra = tk.Entry(app, width=30, textvariable=palabraString)
entryFechaInicio = tk.Entry(app, width=30, textvariable=FechaInicioString)
entryFechaFin = tk.Entry(app, width=30, textvariable=FechaFinString)
entryCiudad = tk.Entry(app, width=30, textvariable=CiudadString)
entryUsuario = tk.Entry(app, width=30, textvariable=UsuarioString)
entryLimite = tk.Entry(app, width=30, textvariable=LimiteInt)
entrypalabra.grid(column=1, row=0, padx=10)
entryFechaInicio.grid(column=1, row=1, padx=10)
entryFechaFin.grid(column=1, row=2, padx=10)
entryCiudad.grid(column=1, row=3, padx=10)
entryUsuario.grid(column=1, row=4, padx=10)
entryLimite.grid(column=1, row=5, padx=10)
resultButton = tk.Button(app, text='Buscar Tweets en Histórico',command=search)
resultButton.grid(column=1, row=6, pady=10, sticky=tk.W)
resultButton2 = tk.Button(app, text='Guardar Resultados en Excel',command=storesearch)
resultButton2.grid(column=1, row=7, pady=10, sticky=tk.W)
resultButton3 = tk.Button(app, text='Buscar y Guardar En Tiempo Real',command=searchtimereal)
resultButton3.grid(column=3, row=0, pady=20, sticky=tk.W)
resultString = tk.StringVar()
resultLabel = tk.Label(app, textvariable=resultString)
resultLabel.grid(column=2, row=6, padx=10, sticky=tk.W)
resultString2 = tk.StringVar()
resultLabel = tk.Label(app, textvariable=resultString2)
resultLabel.grid(column=2, row=7, padx=10, sticky=tk.W)
app.mainloop()















