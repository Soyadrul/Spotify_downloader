from typing import Final
import subprocess
import re
import pathlib
from datetime import date
from datetime import datetime
import os
import shutil
import pytz
from telegram import Update, InputFile, InputMediaAudio
from telegram.ext import Application, CommandHandler, MessageHandler, filters, ContextTypes


TOKEN = ""
BOT_USERNAME: Final = "@spotify_song_downloader_bot"

START_COMMAND_STRING: Final = "start"
DOWNLOAD_COMMAND_STRING: Final = "download"

start_command_message = "I'm here to help you download your favourite songs. You can control me by sending this command:\n/download - downloads the song/album/playlist at a given Spotify link"
download_command_message = "Send me the link of a Spotify song, album or playlist"
download_command_message_after_link = "Perfect, I'm downloading your music ..."

regex = r"(?i)\b((?:https?://|www\d{0,3}[.]|[a-z0-9.\-]+[.][a-z]{2,4}/)(?:[^\s()<>]+|\(([^\s()<>]+|(\([^\s()<>]+\)))*\))+(?:\(([^\s()<>]+|(\([^\s()<>]+\)))*\)|[^\s`!()\[\]{};:'\".,<>?«»“”‘’]))"

chat_history = []






#----------------------------COMMANDS----------------------------
async def start_command(update: Update, context: ContextTypes.DEFAULT_TYPE):
	await update.message.reply_text(start_command_message)
	chat_history.append("/"+START_COMMAND_STRING)

async def download_command(update: Update, context: ContextTypes.DEFAULT_TYPE):
	await update.message.reply_text(download_command_message)
	chat_history.append("/"+DOWNLOAD_COMMAND_STRING)
	
	
	
	



#-------------------------DOWNLOAD MUSIC-------------------------
def download_music(update: Update):
	link = chat_history[len(chat_history)-1]
	link_string = find_links(link)
	
	
	child_directory_name = "user:" + str(update.message.chat.id) + "_date:" + date.today().strftime("%d-%m-%Y") + "_time:" + datetime.now(pytz.timezone('Europe/Rome')).strftime("%H:%M:%S")
	
	child_directory_name = str(child_directory_name)
	child_directory = pathlib.Path(child_directory_name)
	
	child_directory.mkdir(parents = False, exist_ok = False)
	
	current_directory = pathlib.Path.cwd().joinpath(child_directory_name)
	os.chdir(current_directory)
	
	download_command = "spotdl download " + link_string + " --threads 100"
	download_process = subprocess.Popen(download_command, shell=True)
	download_process.wait() #waits until the download_process has finished, then it continue executing code
	os.chdir(pathlib.Path.cwd().parent)
	
	return child_directory_name
	
	
# returns a string containing the links
def find_links(link):
	separator = "?si=" #Spotify sometimes adds an optional "?si=" in the link followed by other chracters that gives more information (author, ...) but sometimes it makes the bot fail on downloading or sending the music
	link = re.findall(regex, link)
	link = [ x[0] for x in link ]
	
	link_string = ""
	
	for i in link:
		link_separated = i.split(separator)
		i = link_separated[0]
		link_string += i
		link_string += " "
			
	return link_string





#----------------------------RESPONSES----------------------------
def handle_bot_response(text: str) -> str:
	lower_text = text.lower()
	return start_command_message
	
async def handle_message(update: Update, context: ContextTypes.DEFAULT_TYPE):
	message_type: str = update.message.chat.type
	text: str = update.message.text
	
	chat_history.append(text)
	
	should_download = False
	
	print(f"\nuser ({update.message.chat.id}) in {message_type}: \"{text}\"")
	
	if message_type == "group":
		if BOT_USERNAME in text:
			new_text: str = text.replace(BOT_USERNAME, "").strip()
			response: str = handle_bot_response(new_text)
		else:
			return 
	elif message_type == "private":
		if chat_history[len(chat_history)-2] == "/"+DOWNLOAD_COMMAND_STRING:
			link = re.findall(regex, chat_history[len(chat_history)-1])
			if len(link) == 0:
				response: str = handle_bot_response(text)
			else:
				response: str = download_command_message_after_link
				print(f"\nBOT: {response}")
				await update.message.reply_text(response)
				music_directory = download_music(update)
				should_download = True
		else:
			response: str = handle_bot_response(text)
	
	
	if should_download:
		dir_ = pathlib.Path(music_directory)
		
		for child in dir_.iterdir():
			child: str = pathlib.Path(child)
			await update.message.reply_audio(open(child, "rb"))
		
		shutil.rmtree( os.path.join(os.getcwd(), music_directory) )
		await update.message.reply_text("Download finished")
		
		
	else:
		print(f"\nBOT: {response}")
		await update.message.reply_text(response)
		
		
	
	
#----------------------------ERRORS----------------------------
def errors(update: Update, context: ContextTypes.DEFAULT_TYPE):
	print(f"Update {update} caused error: {context.error}")



#----------------------------MAIN----------------------------
def main():
	print("Starting BOT ...")
	app = Application.builder().token(TOKEN).build()
	
	#Commands
	app.add_handler(CommandHandler(START_COMMAND_STRING, start_command))
	app.add_handler(CommandHandler(DOWNLOAD_COMMAND_STRING, download_command))
	
	#Message
	app.add_handler(MessageHandler(filters.TEXT, handle_message))
	
	#Error
	app.add_error_handler(errors)
	
	print("Polling ...")
	app.run_polling(poll_interval = 1)



if __name__ == "__main__":
	main()
