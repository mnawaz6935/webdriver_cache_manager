import csv
import logging
import os
import subprocess
import time
import traceback
import psutil

CSV_FILE_PATH = os.path.join(os.path.expanduser("~"), ".wcm")
os.makedirs(CSV_FILE_PATH, exist_ok=True)
temp_file_path = os.path.join(CSV_FILE_PATH, "temp.csv")
CSV_FILE_PATH = os.path.join(CSV_FILE_PATH, "pids.csv")


def save_pids_to_csv(file_path, chrome_driver_pid, chrome_pid):
    global CSV_FILE_PATH
    with open(CSV_FILE_PATH, 'a+', newline='') as csvfile:
        fieldnames = ['File Path', 'ChromeDriver PID', 'Chrome PID']
        writer = csv.DictWriter(csvfile, fieldnames=fieldnames)
        writer.writerow({'File Path': file_path, 'ChromeDriver PID': chrome_driver_pid, 'Chrome PID': chrome_pid})


def read_pids_from_csv(file_path):
    global CSV_FILE_PATH
    chrome_driver_pid = []
    chrome_pid = []
    try:
        with open(CSV_FILE_PATH, mode='r') as csvfile, open(temp_file_path, mode='w', newline='') as temp_file:
            reader = csv.reader(csvfile)
            writer = csv.writer(temp_file)
            for row in reader:
                print(row)
                if row[0] == file_path:
                    chrome_driver_pid.append(int(row[1]))
                    chrome_pid.append(int(row[2]))
                else:
                    writer.writerow(row)
        os.replace(temp_file_path, CSV_FILE_PATH)
    except:
        time.sleep(2)
        read_pids_from_csv(file_path)
        try:
            with open(temp_file_path, 'w', newline=''):
                pass
        except:
            logging.error('Unable to clear process_ids file.')
        return chrome_driver_pid, chrome_pid
    try:
        with open(temp_file_path, 'w', newline=''):
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


def KillChromeAndDriverCache(file_path):
    chrome_driver_pids, chrome_pids = read_pids_from_csv(file_path)
    if chrome_driver_pids:
        for pid in chrome_driver_pids:
            kill_process_by_pid(pid)
    if chrome_pids:
        for pid in chrome_pids:
            kill_process_by_pid(pid)


def ManageChromeDriverCache(driver, file_path):
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
        KillChromeAndDriverCache(file_path)
        save_pids_to_csv(file_path, chrome_driver_pid, chrome_pid)
    except Exception as e:
        logging.error(traceback.format_exc())
