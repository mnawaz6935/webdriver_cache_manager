import csv
import logging
import subprocess
import traceback

import psutil


def save_pids_to_csv(chrome_driver_pid, chrome_pid):
    with open('pids.csv', 'a+', newline='') as csvfile:
        fieldnames = ['Process', 'PID']
        writer = csv.DictWriter(csvfile, fieldnames=fieldnames)
        writer.writeheader()
        writer.writerow({'Process': 'ChromeDriver', 'PID': chrome_driver_pid})
        writer.writerow({'Process': 'Chrome', 'PID': chrome_pid})


def read_pids_from_csv():
    chrome_driver_pid = []
    chrome_pid = []
    try:
        with open('pids.csv', newline='') as csvfile:
            reader = csv.DictReader(csvfile)
            for row in reader:
                if row['Process'] == 'ChromeDriver':
                    chrome_driver_pid.append(int(row['PID']))
                elif row['Process'] == 'Chrome':
                    chrome_pid.append(int(row['PID']))
    except FileNotFoundError:
        pass
    try:
        with open('pids.csv', 'w', newline=''):
            pass
    except:
        logging.error('Unable to clear process_ids file.')
    return chrome_driver_pid, chrome_pid


def kill_process_by_pid(pid):
    try:
        subprocess.run(['taskkill', '/pid', str(pid), '/f'], check=True)
        logging.info(f"Process with PID {pid} killed successfully.")
    except subprocess.CalledProcessError as e:
        logging.info(f"Failed to kill process with PID {pid}. Error: {e}")


def KillChromeAndDriverCache():
    subprocess.run(['taskkill', '/im', 'chrome.exe', '/f'], check=True)
    subprocess.run(['taskkill', '/im', 'chromedriver.exe', '/f'], check=True)


def ManageChromeDriverCache(driver):
    try:
        # Get the ChromeDriver process ID
        chrome_driver_pid = driver.service.process.pid
        logging.info(f"ChromeDriver Process ID: {chrome_driver_pid}")

        # Find the PID of the Chrome process opened by the WebDriver
        chrome_pid = None
        for process in psutil.process_iter(['pid', 'name']):
            if 'chrome.exe' in process.info['name']:
                try:
                    if chrome_driver_pid == psutil.Process(process.info['pid']).ppid():
                        chrome_pid = process.info['pid']
                        break
                except (psutil.NoSuchProcess, psutil.AccessDenied, psutil.ZombieProcess):
                    pass

        if chrome_pid:
            logging.info(f"Chrome Process ID:{chrome_pid}")
        else:
            logging.info("Chrome process not found for this WebDriver instance.")

        chrome_driver_pids, chrome_pids = read_pids_from_csv()
        save_pids_to_csv(chrome_driver_pid, chrome_pid)
        if chrome_driver_pids:
            for chrome_driver_pid in chrome_driver_pids:
                kill_process_by_pid(chrome_driver_pid)
        if chrome_pids:
            for chrome_pid in chrome_pids:
                kill_process_by_pid(chrome_pid)
    except Exception as e:
        logging.error(traceback.format_exc())
