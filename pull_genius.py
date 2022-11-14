#!/usr/bin/env python

import json
import requests
from bs4 import BeautifulSoup
import re
import os

GENIUS_API_TOKEN = '76GuEUMFLceLjZ8mHM9F-FPyRDPPmA54mAcrxZAxZh_xhBfmARjFpJXszdV3xokn'

def get_artist_resp(artist_name, page):
	base_url = 'https://api.genius.com'
	headers = {'Authorization': 'Bearer ' + GENIUS_API_TOKEN}
	search_url = base_url + '/search?per_page=25&page=' + str(page)
	data = {'q': artist_name}
	response = requests.get(search_url, data=data, headers=headers)
	return response

# Get Genius.com song url's from artist object
def get_song_urls(artist_name, max_songs=0):
	page = 1
	songs = []

	while max_songs == 0 or len(songs) < max_songs:
		response = get_artist_resp(artist_name, page)
		json = response.json()
		# Collect up to max_songs urls from artist
		song_infos = []
		for hit in json['response']['hits']:
			if artist_name.lower() in hit['result']['primary_artist']['name'].lower():
				lyrics_state = hit['result']['lyrics_state']
				if lyrics_state == 'complete':
					song_infos.append(hit)
				else:
					print("Skipping lyrics for {} ({})".format(hit['result']['title'], lyrics_state))

		if len(song_infos) == 0:
			print("Finished retrieving songs")
			break
		else:
			print("Parsing {} song urls for {}".format(len(song_infos), artist_name))

		# Collect song URL's from song objects
		for song in song_infos:
			if (max_songs == 0 or len(songs) < max_songs):
				songs.append({'url': song['result']['url'], 'title': song['result']['title']})
		page += 1
			
	print('Found {} songs by {}'.format(len(songs), artist_name))
	return songs

# Scrape lyrics from a Genius.com song URL
def scrape_song_lyrics(url):
	page = requests.get(url)
	html = BeautifulSoup(page.text, 'html.parser')
	lyrics_el = html.find('div', attrs={'data-lyrics-container': True})

	if lyrics_el is None:
		raise ValueError		

	lyrics = '\n'.join(lyrics_el.stripped_strings)

	#remove identifiers like chorus, verse, etc
	lyrics = re.sub(r'\[.*?\]', '', lyrics)
	return lyrics


def write_lyrics_to_file(artist_name, max_songs=0):
	artist_prefix = re.sub(r'[\s/]', '_', artist_name)
	artist_dir = 'lyrics/{}'.format(artist_prefix)
	os.makedirs(artist_dir, exist_ok=True)
	songs = get_song_urls(artist_name, max_songs)
	for song in songs:
			song_path = '{}/{}.txt'.format(artist_dir, re.sub(r'[\s/]', '_', song['title']))

			if os.path.exists(song_path):
				print("Lyrics file already exists: {}".format(song_path))
				continue

			try:
				lyrics = scrape_song_lyrics(song['url'])
			except ValueError:
				print("Failed to parse lyrics for {}".format(song['title']))
				continue

			f = open(song_path, 'wb')
			f.write(lyrics.encode("utf8"))
			f.close()
			print('Created lyric file: {}'.format(song_path))

	print('Wrote {} songs to {}'.format(len(songs), artist_dir))

def main():
	write_lyrics_to_file('Aesop Rock')

def pp(s):
	print(json.dumps(s, indent=4))	

if __name__ == '__main__':
	main()
