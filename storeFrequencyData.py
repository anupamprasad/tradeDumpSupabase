import schedule
import time
import subprocess


def job():
    subprocess.run(["/Users/anupamprasad/venv/bin/python3", "/Users/anupamprasad/Documents/Python File/dailyStockDump.py"])

# Schedule every 10 minutes
schedule.every(1).hours.do(job)
#schedule.every(10).minutes.do(job)

while True:
    schedule.run_pending()
    time.sleep(30)

