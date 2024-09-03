from typing import Any, Optional
import discord
from discord import ui, app_commands
import os
from discord.interactions import Interaction
from discord.utils import MISSING
from dotenv import load_dotenv
import repos

load_dotenv()
BOT_TOKEN = os.getenv('DISCORD_TOKEN')
GUILD_ID = int(os.getenv('GUILD_ID'))
intents = discord.Intents.all()

SQL_SERVER = os.getenv('SQL_SERVER')
SQL_DATABASE = os.getenv('SQL_DATABASE')
SQL_USER = os.getenv('SQL_USER')
SQL_PASS = os.getenv('SQL_PASS')

class Client(discord.Client):
    def __init__(self, intents) -> None:
        super().__init__(intents=intents)
        self.synced=False

    async def on_ready(self):
        await self.wait_until_ready()
        if not self.synced:
            await tree.sync(guild=discord.Object(GUILD_ID))
            self.synced=True
        print("Discord bot is ready!")

client = Client(intents)
tree = app_commands.CommandTree(client)

@tree.command(guild=discord.Object(GUILD_ID), name="ping", description="For testing")
async def ping(interaction):
    await interaction.response.send_message("PONG", ephemeral=True)

###################################################################
############################# QUESTS ##############################
###################################################################
def quest_status_to_btncolor(status):
    if status=="COMPLETED":
        return discord.ButtonStyle.green
    elif status=="INPROGRESS":
        return discord.ButtonStyle.gray
    elif status=="FAILED":
        return discord.ButtonStyle.red
    else:
        raise ValueError("Invalid status, was given " + status)
def quest_status_to_embedcolor(status):
    if status=="COMPLETED":
        return discord.Color.green()
    elif status=="INPROGRESS":
        return discord.Color.dark_gray()
    elif status=="FAILED":
        return discord.Color.red()
    else:
        raise ValueError("Invalid status, was given " + status)
def make_quest_embed(quest):
    players_names = []
    for p in quest["players"]:
        players_names.append(p["player_name"])
    print(players_names)
    print(', '.join(players_names))
    embed = discord.Embed(
        title=quest['title'],
        description=f"""
            **Status:** {quest['status']}
            **Players:** {', '.join(players_names)}
            **Log:**
            {quest['content']}
        """,
        color=quest_status_to_embedcolor(quest["status"])
    )
    return embed
class PickQuestsButtonView(discord.ui.View):
    def __init__(self, quests, callback):
        super().__init__()
        self.add_buttons(quests, callback) # Remember to add this line to call the add_buttons() function
    def add_buttons(self, quests, callback):
        for q in quests:
            btn = discord.ui.Button(label=f'{q["title"]} {"" if q["status"] != "COMPLETED" else " (completed)"}', custom_id=f'{q["id"]}', style=quest_status_to_btncolor(q["status"]))
            self.add_item(btn)
            btn.callback = callback
@tree.command(guild=discord.Object(GUILD_ID), name="showquest", description="Shows all the quests in the database")
async def showquest(interaction):
    async def buttoncallback(interaction: discord.Interaction):
        quest_id = int(interaction.data['custom_id']) # gets the log id
        db = repos.QuestDatabase(SQL_SERVER, SQL_DATABASE, SQL_USER, SQL_PASS)
        log = db.get_quest_by_id(quest_id)
        await interaction.response.send_message(embed=make_quest_embed(log), ephemeral=True)
    db = repos.QuestDatabase(SQL_SERVER, SQL_DATABASE, SQL_USER, SQL_PASS)
    quests = db.get_all_quest(interaction.user.name)
    await interaction.response.send_message("Pick a quest!", view=PickQuestsButtonView(quests, buttoncallback), ephemeral=True)

class AddQuestModal(ui.Modal, title="Add quest"):
    def __init__(self) -> None:
        super().__init__() 
        questtitle = ui.TextInput(label="Quest title", style=discord.TextStyle.short, required=True, placeholder="Put quest title here....", max_length=200)
        partywide = ui.TextInput(label="Is it party wide? (Yes/No)", default="Yes", style=discord.TextStyle.short, required=True, placeholder="(Yes/No)", max_length=20)
        content = ui.TextInput(label="Quest log", style=discord.TextStyle.paragraph, required=True, placeholder="Put quest content, events, and details here....", max_length=4000)

        self.add_item(questtitle)
        self.questtitle = questtitle
        self.add_item(partywide)
        self.partywide = partywide
        self.add_item(content)
        self.content = content
    async def on_submit(self, interaction: Interaction) -> None:

        # Checks for user input
        yesno = self.partywide.value.lower().strip()
        if yesno != 'yes' and yesno != 'no':
            await interaction.response.send_message("Invalid option if the quest is party wide. Please use YES or NO. Try again.", ephemeral=True)
            return
        
        # Gets the player info
        db = repos.PlayerDatabase(SQL_SERVER, SQL_DATABASE, SQL_USER, SQL_PASS)
        if yesno == 'yes':
            # adds all the players
            players = db.get_all_players()
        else:
            # gets the player and the DM
            players = db.get_all_dms()
            curr_player = db.get_player_by_name(interaction.user.name)
            # Only adds if they are a player
            if curr_player['role'] == "player":
                players.append(curr_player)

        # Gets the ids
        playerids = []
        for player in players:
            playerids.append(player["id"])

        # Saves to the db
        db = repos.QuestDatabase(SQL_SERVER, SQL_DATABASE, SQL_USER, SQL_PASS)
        db.add_quest(self.questtitle.value, self.content.value, playerids)
        await interaction.response.send_message("Quest added!", ephemeral=True)
@tree.command(guild=discord.Object(GUILD_ID), name="addquest", description="Adds a quest")
async def addquest(interaction):
    await interaction.response.send_modal(AddQuestModal())

class EditQuestModal(ui.Modal, title="Edit quest"):
    def __init__(self, quest) -> None:
        super().__init__() 
        questtitle = ui.TextInput(label="Quest title", default=quest["title"], style=discord.TextStyle.short, required=True, placeholder="Put quest title here....", max_length=200)
        content = ui.TextInput(label="Quest log", default=quest["content"], style=discord.TextStyle.paragraph, required=True, placeholder="Put quest content, events, and details here....", max_length=4000)

        self.quest = quest
        self.add_item(questtitle)
        self.questtitle = questtitle
        self.add_item(content)
        self.content = content
    async def on_submit(self, interaction: Interaction) -> None:
        # Saves to the db
        db = repos.QuestDatabase(SQL_SERVER, SQL_DATABASE, SQL_USER, SQL_PASS)
        db.edit_quest(self.quest["id"], self.questtitle.value, self.content.value)
        await interaction.response.send_message("Quest edited!", ephemeral=True)
@tree.command(guild=discord.Object(GUILD_ID), name="editquest", description="Edits a quest")
async def editquest(interaction):
    async def buttoncallback(interaction: discord.Interaction):
        quest_id = int(interaction.data['custom_id']) # gets the log id
        db = repos.QuestDatabase(SQL_SERVER, SQL_DATABASE, SQL_USER, SQL_PASS)
        quest = db.get_quest_by_id(quest_id)
        await interaction.response.send_modal(EditQuestModal(quest))
    db = repos.QuestDatabase(SQL_SERVER, SQL_DATABASE, SQL_USER, SQL_PASS)
    quests = db.get_all_quest(interaction.user.name)
    await interaction.response.send_message("Pick a quest!", view=PickQuestsButtonView(quests, buttoncallback), ephemeral=True)

@tree.command(guild=discord.Object(GUILD_ID), name="completequest", description="Sets that the quest has been completed")
async def completequest(interaction):
    async def buttoncallback(interaction: discord.Interaction):
        quest_id = int(interaction.data['custom_id']) # gets the log id
        db = repos.QuestDatabase(SQL_SERVER, SQL_DATABASE, SQL_USER, SQL_PASS)
        db.edit_quest(quest_id, new_status="COMPLETED")
        await interaction.response.send_message("Completed quest!", ephemeral=True)
    db = repos.QuestDatabase(SQL_SERVER, SQL_DATABASE, SQL_USER, SQL_PASS)
    quests = db.get_all_quest(interaction.user.name)
    await interaction.response.send_message("Pick a quest!", view=PickQuestsButtonView(quests, buttoncallback), ephemeral=True)

@tree.command(guild=discord.Object(GUILD_ID), name="failquest", description="Sets that the quest has failed")
async def failquest(interaction):
    async def buttoncallback(interaction: discord.Interaction):
        quest_id = int(interaction.data['custom_id']) # gets the log id
        db = repos.QuestDatabase(SQL_SERVER, SQL_DATABASE, SQL_USER, SQL_PASS)
        db.edit_quest(quest_id, new_status="FAILED")
        await interaction.response.send_message("Failed quest!", ephemeral=True)
    db = repos.QuestDatabase(SQL_SERVER, SQL_DATABASE, SQL_USER, SQL_PASS)
    quests = db.get_all_quest(interaction.user.name)
    await interaction.response.send_message("Pick a quest!", view=PickQuestsButtonView(quests, buttoncallback), ephemeral=True)

@tree.command(guild=discord.Object(GUILD_ID), name="setquesttoinprogress", description="Set the quest to inprogress")
async def setquesttoinprogress(interaction):
    async def buttoncallback(interaction: discord.Interaction):
        quest_id = int(interaction.data['custom_id']) # gets the log id
        db = repos.QuestDatabase(SQL_SERVER, SQL_DATABASE, SQL_USER, SQL_PASS)
        db.edit_quest(quest_id, new_status="INPROGRESS")
        await interaction.response.send_message("Set quest to inprogress!", ephemeral=True)
    db = repos.QuestDatabase(SQL_SERVER, SQL_DATABASE, SQL_USER, SQL_PASS)
    quests = db.get_all_quest(interaction.user.name)
    await interaction.response.send_message("Pick a quest!", view=PickQuestsButtonView(quests, buttoncallback), ephemeral=True)

@tree.command(guild=discord.Object(GUILD_ID), name="deletequest", description="Deletes a quest")
async def deletequest(interaction):
    async def buttoncallback(interaction: discord.Interaction):
        quest_id = int(interaction.data['custom_id']) # gets the log id
        db = repos.QuestDatabase(SQL_SERVER, SQL_DATABASE, SQL_USER, SQL_PASS)
        db.edit_quest(quest_id, new_is_deleted=1)
        await interaction.response.send_message("Deleted quest!", ephemeral=True)
    db = repos.QuestDatabase(SQL_SERVER, SQL_DATABASE, SQL_USER, SQL_PASS)
    quests = db.get_all_quest(interaction.user.name)
    await interaction.response.send_message("Pick a quest!", view=PickQuestsButtonView(quests, buttoncallback), ephemeral=True)

@tree.command(guild=discord.Object(GUILD_ID), name="undeletequest", description="Undeletes a quest")
async def undeletequest(interaction):
    async def buttoncallback(interaction: discord.Interaction):
        quest_id = int(interaction.data['custom_id']) # gets the log id
        db = repos.QuestDatabase(SQL_SERVER, SQL_DATABASE, SQL_USER, SQL_PASS)
        db.edit_quest(quest_id, new_is_deleted=0)
        await interaction.response.send_message("Undeleted quest!", ephemeral=True)
    db = repos.QuestDatabase(SQL_SERVER, SQL_DATABASE, SQL_USER, SQL_PASS)
    quests = db.get_all_deleted_quest(interaction.user.name)
    await interaction.response.send_message("Pick a quest!", view=PickQuestsButtonView(quests, buttoncallback), ephemeral=True)

@tree.command(guild=discord.Object(GUILD_ID), name="showdeletedquest", description="Shows all the deleted quests in the database")
async def showdeletedquest(interaction):
    async def buttoncallback(interaction: discord.Interaction):
        quest_id = int(interaction.data['custom_id']) # gets the log id
        db = repos.QuestDatabase(SQL_SERVER, SQL_DATABASE, SQL_USER, SQL_PASS)
        log = db.get_quest_by_id(quest_id)
        await interaction.response.send_message(embed=make_quest_embed(log), ephemeral=True)
    db = repos.QuestDatabase(SQL_SERVER, SQL_DATABASE, SQL_USER, SQL_PASS)
    quests = db.get_all_deleted_quest(interaction.user.name)
    await interaction.response.send_message("Pick a quest!", view=PickQuestsButtonView(quests, buttoncallback), ephemeral=True)

###################################################################
############################# LOGS ################################
###################################################################
def make_log_embed(log):
    embed = discord.Embed(
        title=f'D&D Session Log #{log["id"]} - {log["date"].strftime("%B %d, %Y")}',
        description=log["content"],
        color=discord.Color.green()
    )
    return embed

class AddLogModal(ui.Modal, title="Add session log"):
    content = ui.TextInput(label="Session log", style=discord.TextStyle.paragraph, required=True, placeholder="Put session log here....", max_length=4000)
    async def on_submit(self, interaction: Interaction) -> None:
        # Saves to the db
        db = repos.LogDatabase(SQL_SERVER, SQL_DATABASE, SQL_USER, SQL_PASS)
        db.add_log(str(self.content), interaction.user.name)
        await interaction.response.send_message("Log submitted!", ephemeral=True)
@tree.command(guild=discord.Object(GUILD_ID), name="addlog", description="To add a log about a D&D session")
async def addlog(interaction):
    await interaction.response.send_modal(AddLogModal())

@tree.command(guild=discord.Object(GUILD_ID), name="recap", description="Shows the log of the previous session")
async def recap(interaction):
    db = repos.LogDatabase(SQL_SERVER, SQL_DATABASE, SQL_USER, SQL_PASS)
    latest_log = db.get_latest_log()
    embed = make_log_embed(latest_log)
    await interaction.response.send_message(embed=embed, ephemeral=True)

class PickLogsButtonView(discord.ui.View):
    def __init__(self, logs, callback):
        super().__init__()
        self.add_buttons(logs, callback) # Remember to add this line to call the add_buttons() function
    def add_buttons(self, logs, callback):
        for log in logs:
            btn = discord.ui.Button(label=log["date"].strftime("%B %d, %Y"), custom_id=f'{log["id"]}')
            self.add_item(btn)
            btn.callback = callback
@tree.command(guild=discord.Object(GUILD_ID), name="showlog", description="Shows all the logs in the database")
async def showlog(interaction):
    async def buttoncallback(interaction: discord.Interaction):
        log_id = int(interaction.data['custom_id']) # gets the log id
        db = repos.LogDatabase(SQL_SERVER, SQL_DATABASE, SQL_USER, SQL_PASS)
        log = db.get_log_by_id(log_id)
        await interaction.response.send_message(embed=make_log_embed(log), ephemeral=True)
    db = repos.PlayerDatabase(SQL_SERVER, SQL_DATABASE, SQL_USER, SQL_PASS)
    player = db.get_player_by_name(interaction.user.name)
    db = repos.LogDatabase(SQL_SERVER, SQL_DATABASE, SQL_USER, SQL_PASS)
    logs = db.get_all_logs_by_role(player['role'])
    await interaction.response.send_message("Pick a session!", view=PickLogsButtonView(logs, buttoncallback), ephemeral=True)

class EditLogModal(ui.Modal, title="Edit session log"):
    def __init__(self, log) -> None:
        super().__init__()
        input = ui.TextInput(label="Session log", default=log['content'], style=discord.TextStyle.paragraph, required=True, placeholder="Put session log here....", max_length=4000)
        self.add_item(input)
        self.input = input
        self.log = log
    async def on_submit(self, interaction: Interaction) -> None:
        # Saves to the db
        db = repos.LogDatabase(SQL_SERVER, SQL_DATABASE, SQL_USER, SQL_PASS)
        db.edit_log(self.log['id'], self.input.value)
        await interaction.response.send_message("Log edited!", ephemeral=True)
@tree.command(guild=discord.Object(GUILD_ID), name="editlog", description="Edit a log in the database")
async def editlog(interaction):
    async def buttoncallback(interaction: discord.Interaction):
        log_id = int(interaction.data['custom_id']) # gets the log id
        db = repos.LogDatabase(SQL_SERVER, SQL_DATABASE, SQL_USER, SQL_PASS)
        log = db.get_log_by_id(log_id)
        await interaction.response.send_modal(EditLogModal(log))
    db = repos.PlayerDatabase(SQL_SERVER, SQL_DATABASE, SQL_USER, SQL_PASS)
    player = db.get_player_by_name(interaction.user.name)
    db = repos.LogDatabase(SQL_SERVER, SQL_DATABASE, SQL_USER, SQL_PASS)
    logs = db.get_all_logs_by_role(player['role'])
    await interaction.response.send_message("Pick a session!", view=PickLogsButtonView(logs, buttoncallback), ephemeral=True)


client.run(BOT_TOKEN)