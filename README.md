# discord_logging_bot
This Discord bot logs the number of times the "log" command has been called per user, and is able to display line plots of user trends, as well as a leaderboard.

Prefix: `?`

Commands:
* `log`: logs the number of times the `log` command has been called and displays a user specified count for whoever called it.
* `chart`: displays a line plot of user `log` calls in the current week against total `log` calls.
* `leader`: displays leader board of users ordered by number of log calls. Use of the optional `today` argument will filter the leaderboard to the current day.
