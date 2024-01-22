import asyncio
import time
from pyrogram import Client, filters
from pyrogram.types import Message
from PIL import Image
import os
import random
import schedule
import threading
from keep_alive import keep_alive

# Créez une instance de client avec votre propre token de bot et votre nom d'utilisateur
app = Client("my_account", bot_token="6813590394:AAFtdbMTylWbr-yFdhqwV1CP2bmTIYoMGUk", api_id="29022005", api_hash="bfd616932410d155a39403b4fac5884b")

# Créez un sémaphore avec une limite de 1
semaphore = asyncio.Semaphore(2)

text_to_replace = "Shar"  # Partie du nom de fichier à remplacer (jusqu'aux 4 dernières lettres)

# Variable pour stocker le nom de l'image de la vignette
thumbnail_image = "img.jpg"

# Ajoutez une commande /rempl pour changer le texte à remplacer et l'image de la vignette
@app.on_message(filters.command("rempl"))
async def rempl(client: Client, message: Message):
    global text_to_replace, thumbnail_image
    command_args = message.text.split()
    text_to_replace = command_args[1]
    if len(command_args) > 2 and command_args[2].startswith('|'):
        thumbnail_image = command_args[3]
    await message.reply_text(f"Le texte à remplacer a été défini sur {text_to_replace} et l'image de la vignette a été définie sur {thumbnail_image}")

# Ajoutez une commande /start
@app.on_message(filters.command("start"))
async def start(client: Client, message: Message):
    await message.reply_text("Bonjour ! Je suis votre bot. Comment puis-je vous aider aujourd'hui ...")

# Filtre pour les commandes
@app.on_message(filters.command(['activer', 'desactiver']))
async def handle_thumbnail_command(client: Client, message: Message):
    global change_thumbnail

    if message.command[0] == 'activer':
        change_thumbnail = True
        await message.reply_text('La fonctionnalité de modification de la vignette a été activée.')
    elif message.command[0] == 'desactiver':
        change_thumbnail = False
        await message.reply_text('La fonctionnalité de modification de la vignette a été désactivée.')


@app.on_message(filters.document)
async def rename_media(client: Client, message: Message):
    global thumbnail_image, text_to_replace

    # Acquérir le sémaphore
    async with semaphore:
        # Vérifiez si la taille du fichier est inférieure à 2 Go (2 * 1024 * 1024 * 1024 octets)
        if message.document.file_size <= 2 * 1024 * 1024 * 1024 :
            # Envoyez un message à l'utilisateur pour lui faire savoir que le fichier a été reçu
            temp_message = await message.reply_text("Fichier reçu, patientez un instant...")

            # Vérifiez si le nom du fichier contient la partie à remplacer
            if text_to_replace in message.document.file_name:
                # Téléchargez le fichier
                file_path = await message.download()

                # Vérifiez si "@" est présent dans le nom du fichier
                if "@" in message.document.file_name:
                    # Si "@" est présent, retirez "@" du nom du fichier
                    message.document.file_name = message.document.file_name.replace("@", "")
                else:
                    message.document.file_name = message.document.file_name

                # Obtenez la partie du nom de fichier à remplacer (jusqu'aux 4 dernières lettres)
                replace_part = message.document.file_name.split(text_to_replace)[1][:-4]

                # Remplacez la partie à remplacer par "@TurboSearch" dans le nom du fichier
                new_file_name = message.document.file_name.replace(text_to_replace + replace_part, "@TurboSearch")

                # Renommez le fichier
                new_file_path = os.path.join(os.path.dirname(file_path), new_file_name)
                os.rename(file_path, new_file_path)

                # change_thumbnail = True
                if change_thumbnail:
                    # Vérifiez si le fichier de l'image de la vignette existe
                    if not os.path.isfile(os.path.join('tools', thumbnail_image)):
                        # Si le fichier n'existe pas, utilisez l'image par défaut
                        thumbnail_image = 'img.jpg'
                    # Ouvrez l'image que vous voulez utiliser comme vignette
                    with Image.open(os.path.join('tools', thumbnail_image)) as img:
                        # Enregistrez l'image en tant que vignette pour le fichier
                        img.save(new_file_path + '.thumbnail', 'JPEG')

                    # Envoyez le fichier renommé avec la nouvelle vignette
                    await message.reply_document(new_file_path, thumb=os.path.join('tools', thumbnail_image))

                    img_thumb = os.path.join(new_file_path + '.thumbnail')

                    os.remove(img_thumb)
                
                else:
                    # Vérifiez si le fichier de l'image de la vignette existe pour le fichier original
                    original_thumbnail = new_file_path + '.thumbnail'
                    if os.path.isfile(original_thumbnail):
                        # Si la vignette existe, envoyez le fichier renommé avec la vignette originale
                        await message.reply_document(new_file_path, thumb=original_thumbnail)
                    else:
                        # Sinon, envoyez le fichier renommé sans vignette
                        await message.reply_document(new_file_path)

                os.remove(new_file_path)

            else:
                await message.reply_document(message.document.file_id)
        else:
            # Si la taille du fichier est supérieure à 2 Go, ignorer le traitement
            await message.reply_text("Le fichier est trop volumineux et ne peut pas être traité.")


        
# Fonction pour envoyer un message aléatoire dans le groupe
async def send_random_message():
    random_messages = [
        "Message aléatoire 1",
        "Message aléatoire 2",
        "Message aléatoire 3",
        # Ajoutez autant de messages aléatoires que nécessaire
    ]
    
    random_message = random.choice(random_messages)
    await app.send_message(-1002054489996, random_message)
# Planifie l'envoi du message aléatoire toutes les 3 minutes
schedule.every(50).seconds.do(lambda: asyncio.run(send_random_message()))

# Fonction pour exécuter périodiquement les tâches planifiées
def run_periodic_tasks():
    while True:
        schedule.run_pending()
        time.sleep(1)  # Pause de 3 minutes

# Démarrer la tâche périodique dans un thread en arrière-plan
threading.Thread(target=run_periodic_tasks, daemon=True).start()

keep_alive()
app.run()
