import discord
from discord.ext import commands
import os
import asyncio
import random
import string
import time
import mysql.connector
import requests 


intents = discord.Intents.all()
intents.members = True
bot = commands.Bot(command_prefix='!', intents=intents)


codes_verification = {}


def check_role(ctx):
    role_id = 1214411430112010290  
    role = discord.utils.get(ctx.guild.roles, id=role_id)
    return role is not None and role in ctx.author.roles

@bot.event
async def on_ready():
    print(f'Bot connecté en tant que {bot.user.name}')

@bot.event
async def on_member_join(member):
 
    code = ''.join(random.choices(string.ascii_letters + string.digits, k=8))
    codes_verification[member.id] = code
   
    await member.send(f'Welcome to the server! Your verification code is: {code}')

@bot.event
async def on_message(message):
  
    if message.author == bot.user:
        return

   
    if str(message.channel.id) == '1214420290675941487':
      
        if codes_verification.get(message.author.id) == message.content:
            role = discord.utils.get(message.guild.roles, name='Member')
            await message.author.add_roles(role)
            await message.channel.send('You have been successfully verified and the role Member has been assigned to you! Welcome to the server!')
        else:
            await message.channel.send('Incorrect code, please try again or contact an administrator.')
    await bot.process_commands(message)


def connect_to_mysql():
    return mysql.connector.connect(
        host="localhost",
        user="root",
        password="root",
        database="db1"
    )


@bot.command()
async def utilisateur(ctx, colonne: str, valeur: str):

    colonnes_bloquees = ['ping', 'server', 'endpoint_name']

    try:
 
        if colonne in colonnes_bloquees:
            await ctx.reply(f"La recherche sur la colonne '{colonne}' est bloquée.")
            return


        if len(valeur) < 8:
            await ctx.reply("Recherche trop courte.")
            return

      
        connection = connect_to_mysql()
        cursor = connection.cursor()

       
        cursor.execute("SHOW COLUMNS FROM users LIKE %s", (colonne,))
        if cursor.fetchone() is None:
            await ctx.reply(f"Colonne '{colonne}' introuvable.")
            return


        query = f"SELECT * FROM users WHERE {colonne} LIKE %s"
        cursor.execute(query, ('%' + valeur + '%',))
        results = cursor.fetchall()

        if results:
            for result in results:
                embed = discord.Embed(title="Résultat de la recherche", description="Voici les informations complètes de l'utilisateur recherché :", color=discord.Color.blue())
                for i, column_name in enumerate(cursor.column_names):
                    embed.add_field(name=column_name, value=result[i], inline=False)
                await ctx.reply(embed=embed)
        else:
            await ctx.reply("Aucun résultat trouvé dans la base de données.")

    except mysql.connector.Error as error:
        print("Erreur lors de la connexion à MySQL:", error)

    finally:
       
        if connection.is_connected():
            cursor.close()
            connection.close()









@bot.command()
@commands.check(check_role)
async def chercher(ctx, licence_id):
    
    
    licence_id_bloques = ["", "", "", "", ""]

  
    if licence_id in licence_id_bloques:
        await ctx.send('Recherche interdite. La licence_id est bloqué.')
        return
 
    if len(licence_id) < 10:
        await ctx.send('Recherche trop courte. Veuillez entrer au moins 10 caractères.')
        return

    dossier = "db"
    fichiers_liste = os.listdir(dossier)
    total_fichiers = len(fichiers_liste)

  
    nom_categorie = f'Recherche-{ctx.author.name}'
    categorie_utilisateur = discord.utils.get(ctx.guild.categories, name=nom_categorie)
    if not categorie_utilisateur:
        categorie_utilisateur = await ctx.guild.create_category(nom_categorie)

  
    overwrites = {
        ctx.guild.default_role: discord.PermissionOverwrite(read_messages=False),
        ctx.author: discord.PermissionOverwrite(read_messages=True)
    }
    channel = await ctx.guild.create_text_channel(f'Recherche-{licence_id}', category=categorie_utilisateur, overwrites=overwrites)


    message_recherche = await channel.send('Début de la recherche...')

    try:
        for index, fichier in enumerate(fichiers_liste, start=1):
            chemin_fichier = os.path.join(dossier, fichier)

       
            await message_recherche.edit(content=f'Verification du fichier {index}/{total_fichiers}: {fichier}...')

            if os.path.isfile(chemin_fichier):
                with open(chemin_fichier, 'r', encoding='latin-1') as file:
                    lignes = file.readlines()

                    for numero_ligne, ligne in enumerate(lignes, start=1):
                        if licence_id in ligne:
                            await channel.send(f"```{fichier} - Ligne {numero_ligne}: {ligne.strip()}```")  

          
            await asyncio.sleep(1)

    except asyncio.CancelledError:
     
        await message_recherche.delete()
    except Exception as e:
        print(f'Une erreur est survenue: {e}')
       

   
    await message_recherche.delete()


@chercher.error
async def chercher_error(ctx, error):
    if isinstance(error, commands.CheckFailure):
        await ctx.send("Vous n'avez pas accès à cette commande.")


@bot.command()
@commands.has_permissions(manage_roles=True)
async def vip(ctx, member: discord.Member):

    vip_role = discord.utils.get(ctx.guild.roles, name='VIP')
    

    if vip_role:

        await member.add_roles(vip_role)
        await ctx.send(f'Le rôle VIP a été attribué avec succès à {member.mention} !')
    else:
      
        await ctx.send("Le rôle VIP n'existe pas. Veuillez créer ce rôle avant d'utiliser cette commande.")


@vip.error
async def vip_error(ctx, error):
    if isinstance(error, commands.MissingPermissions):
        await ctx.send("Vous n'avez pas la permission de gérer les rôles.")
        
@bot.command()
async def total(ctx):
    dossier = "db"
    fichiers_liste = os.listdir(dossier)
    total_fichiers = len(fichiers_liste)
    await ctx.send(f'Nombre total de DB enregistré: {total_fichiers}')
    
@bot.command()
async def totaluser(ctx):
 
    connection = connect_to_mysql()
    cursor = connection.cursor()


    cursor.execute("SELECT COUNT(*) FROM users")
    total_lignes = cursor.fetchone()[0] 


    cursor.close()
    connection.close()

    embed = discord.Embed(title="Total des utilisateurs unique", description=f"Nombre total d'utilisateurs unique dans la table 'users': {total_lignes}", color=discord.Color.green())


    await ctx.reply(embed=embed)
    

def get_ipinfo(ip_address):
    try:
        response = requests.get(f"https://ipinfo.io/{ip_address}?token=c1319cb2b6b90b")
        if response.status_code == 200:
            data = response.json()
            info = "\n".join([f"{key.capitalize()}: {value}" for key, value in data.items()])
            return info
        else:
            return "Failed to retrieve information for the provided IP address."
    except Exception as e:
        print("Erreur lors de la récupération des informations IP:", e)
        return "An error occurred while fetching IP information."


@bot.command()
async def ipinfo(ctx, ip_address):
    info = get_ipinfo(ip_address)
    embed = discord.Embed(title="Informations sur l'adresse IP", description=info, color=discord.Color.blue())
    await ctx.reply(embed=embed)




bot.run('token')
