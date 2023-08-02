import datetime
import discord
from discord.ext import commands
import matplotlib.pyplot as plt
import os
import pandas as pd
import seaborn as sns


# Setup
intents = discord.Intents.default()  # Create instance of Intents class
intents.messages = True
intents.message_content = True
bot = commands.Bot(command_prefix='?', intents=intents)

token = "SOME BOT TOKEN"

log_path = r"\some\logfile\path\log.csv"


@bot.event
async def on_ready():
    """
    Prints message to terminal confirming bot online
    """
    print(f"We have logged in as {bot.user}")


@bot.command(name='log')
async def logme(ctx):
    """
    Counts the number of times the "log" command has been sent in Discord for the given user,
    saves the data to a local CSV, then prints a message in the Discord channel.

    Args:
        ctx: discord Context object
    """
    user_id = ctx.message.author.id
    date = datetime.date.today().strftime('%Y-%m-%d')
    day_of_week = datetime.datetime.utcnow().strftime('%a')

    try:
        log_df = pd.read_csv(log_path)
    except Exception as e:
        log_df = pd.DataFrame(columns=["ID", "Count", "Total", "HomesOwned", "Day", "Date"])

    if date not in log_df['Date'].values or user_id not in log_df.loc[log_df['Date'] == date, 'ID'].values:
        # Add the new date to the DataFrame
        new_row = pd.DataFrame({"ID": [user_id], "Count": [0], "Total": [0], "HomesOwned": [0], "Day": [day_of_week], "Date": [date]})
        log_df = pd.concat([log_df, new_row]).reset_index(drop=True)

    # Increment the count for the given date and user_id
    log_df.loc[(log_df['Date'] == date) & (log_df['ID'] == user_id), 'Count'] += 1

    total_count = log_df.loc[log_df['ID'] == user_id, 'Count'].sum()
    log_df.loc[(log_df['Date'] == date) & (log_df['ID'] == user_id), 'Total'] = total_count

    weight = 128/453.592 # average weight of building material using grams (lbs)
    density = 1 # average density of building material (g/ml)
    volume = 960 # average volume of a standard brick (ml)
    house_bricks = 7800 # number of bricks needed to build 4 walls for a 1500 sq/ft house
    number_of_houses = (total_count * weight) / (density * volume * house_bricks)
    percent_houses = round(number_of_houses * 100, 1)

    log_df.loc[(log_df['Date'] == date) & (log_df['ID'] == user_id), 'HomesOwned'] = number_of_houses

    log_df.to_csv(log_path, index=False)

    await ctx.send(f"Hi {ctx.author.mention}, you have logged {total_count} entries and are %{percent_houses} of the way to home ownership!")


@bot.command(name='chart')
async def chartme(ctx):
    """
    Creates a lineplot of the users "log" command calls in the current week vs all time,
    then uploads a PNG of the plot to the Discord channel

    Args:
        ctx: discord Context object
    """
    user_id = ctx.message.author.id
    if os.path.isfile(log_path):
        log_df = pd.read_csv(log_path)

        user_df = log_df.loc[log_df['ID'] == user_id]
        user_total_df = user_df.groupby('Day')['Count'].sum().reset_index()
        user_total_df['Data Range'] = 'Total History'

        today = datetime.date.today()

        # Calculate the start and end of the current week
        start_week = today - datetime.timedelta(days=today.weekday())
        end_week = start_week + datetime.timedelta(days=6)

        # Filter the DataFrame for the date range
        user_df['Date'] = pd.to_datetime(user_df['Date']) # convert 'Date' to datetime
        # Filter the DataFrame for the date range
        user_week_df = user_df[(user_df['Date'] >= pd.to_datetime(start_week)) & (user_df['Date'] <= pd.to_datetime(end_week))]
        user_week_total_df = user_week_df.groupby('Day')['Count'].mean().reset_index()
        user_week_total_df['Data Range'] = 'Current Week'

        user_history_df = pd.concat([user_week_total_df, user_total_df])
        print(user_history_df)

        sns.lineplot(data=user_history_df, x="Day", y="Count", hue="Data Range")

        plt.tight_layout()
        plt.savefig("chart.png")

        await ctx.send(file=discord.File("chart.png"))
        
        os.remove("chart.png")  # delete the file after sending it
        plt.clf()
    else:
        await ctx.send(f"I'm sorry; there is no data yet for {ctx.author.mention}.")


@bot.command(name='leader')
async def leaderboard(ctx, today: str = None):
    """
    Establishes a leaderboard based on the current day or all time,
    then sends it as a message in Discord to the current channel
    
    Args:
        ctx: discord Context object
        today: string of "today" to toggle leaderboard filtered to just the current date
    """
    if os.path.isfile(log_path):
        log_df = pd.read_csv(log_path)
        log_df['ID'] = log_df['ID'].astype('str')

        if today and today.lower() == 'today':
            today = datetime.date.today().strftime('%Y-%m-%d')

            leader_df = log_df.loc[log_df['Date'] == today].groupby('ID').agg({'Count': 'sum', 'HomesOwned': 'max'}).reset_index()
        else:
            leader_df = log_df.groupby('ID').agg({'Count': 'sum', 'HomesOwned': 'max'}).reset_index()

        if len(leader_df) < 1:
            await ctx.send(f"I'm sorry; there is no data for today yet.")
        else:
            leader_df = leader_df.sort_values(by='Count', ascending=False)

            message = f""
            for idx, row in leader_df.iterrows():
                user = await bot.fetch_user(row.ID)
                text = f"{idx + 1}) {user.name}   |   {row.Count} entries   |   {round(row.HomesOwned, 3)} homes built\n"
                message = message + text
        
        await ctx.send(message)
    else:
        await ctx.send(f"I'm sorry; there is no data yet.")


bot.run(token)
