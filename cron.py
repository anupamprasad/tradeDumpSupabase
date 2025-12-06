from crontab import CronTab

cron = CronTab(user=True)

# Create a new job
job = cron.new(command='python3 /Users/anupamprasad/Documents/Python File/dailyStockDump.py', comment='myCronjob')
job.setall('36 14 * * *')   # every day at 5am

cron.write()
