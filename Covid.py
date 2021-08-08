import json
import pyttsx3
import speech_recognition as sr
import re
import threading
import time
from GoogleNews import GoogleNews
from newspaper import Article
import pandas as pd
from datetime import date

key = "tXoQweA0-9_g"
Proj_token = "tYTnVz_2wqUW"
run_tok = "tMa-BSw9uGOm"

# The different classes, and sub classes for collecting data

class Data:
	def __init__(self, key, Proj_token):
		self.key = key
		self.Proj_token = Proj_token
		self.params = {
			"key": self.key
		}
		self.data = self.get_data()

	def get_data(self):
		response = requests.get(f'https://www.parsehub.com/api/v2/projects/{self.Proj_token}/last_ready_run/data', params=self.params)
		data = json.loads(response.text)
		return data

	def total_cases(self):
		data = self.data['Total']

		for x in data:
			if x['name'] == "Coronavirus Cases:":
				return x['value']

	def total_deaths(self):
		data = self.data['Total']

		for x in data:
			if x['name'] == "Deaths:":
				return x['value']

		return "0"

	def get_country_data(self, country):
		data = self.data["country"]

		for x in data:
			if x['name'].lower() == country.lower():
				return x

		return "0"

	def get_list_of_countries(self):
		countries = []
		for country in self.data['country']:
			countries.append(country['name'].lower())

		return countries

	def update_data(self):
		response = requests.post(f'https://www.parsehub.com/api/v2/projects/{self.Proj_token}/run', params=self.params)

		def poll():
			time.sleep(0.1)
			old_data = self.data
			while True:
				new_data = self.get_data()
				if new_data != old_data:
					self.data = new_data
					print("Data updated")
					break
				time.sleep(5)


		t = threading.Thread(target=poll)
		t.start()

#initializing the speech engine 

def speak(text):
	engine = pyttsx3.init()
	engine.say(text)
	engine.runAndWait()


def get_audio():
	r = sr.Recognizer()
	with sr.Microphone() as source:
		audio = r.listen(source)
		said = ""

		try:
			said = r.recognize_google(audio)
		except Exception as e:
			print("Exception:", str(e))

	return said.lower()
# to find the top headline on google 
def headline():
    today = date.today()
    d1 = today.strftime("%m/%d/%Y")
    x = str(d1)
    googlenews=GoogleNews(start= x,end=x)
    googlenews.search('Coronavirus')
    result=googlenews.result()
    return result[0]['title']

def main():
	print("Started Program")
	data = Data(key, Proj_token)
	END_PHRASE = "stop"
	country_list = data.get_list_of_countries()

# creating of reg ex phrases 

	Total_Data = {
        re.compile("[\w\s]+ total [\w\s]+ cases"):data.total_cases,
        re.compile("[\w\s]+ total cases"): data.total_cases,
        re.compile("[\w\s]+ total [\w\s]+ deaths"): data.total_deaths,
        re.compile("[\w\s]+ total deaths"): data.total_deaths,
        re.compile("[\w\s]+ latest news"): headline,
					}

	country_info = {
		re.compile("[\w\s]+ cases [\w\s]+"): lambda country: data.get_country_data(country)['total_cases'],
		re.compile("[\w\s]+ deaths [\w\s]+"): lambda country: data.get_country_data(country)['total_deaths'],
        re.compile("[\w\s]+ active cases [\w\s]+"): lambda country: data.get_country_data(country)['active_cases'],
                    }

	update = "update"

	while True:
		print("Listening...")
		text = get_audio()
		print(text)
		result = None

		for pattern, func in country_info.items():
			if pattern.match(text):
				words = set(text.split(" "))
				for country in country_list:
					if country in words:
						result = func(country)
						break

		for pattern, func in Total_Data.items():
			if pattern.match(text):
				result = func()
				break

		if text == update:
			result = "Data is being updated. This may take a moment!"
			data.update_data()

		if result:
			speak(result)
            

		if text.find(END_PHRASE) != -1:  
			print("Exit")
			break

main()

#made while following a tutorial by techwithtim
# https://github.com/techwithtim