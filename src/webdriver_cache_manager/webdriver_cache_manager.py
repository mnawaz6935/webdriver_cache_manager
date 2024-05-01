import csv
import logging
import os
import subprocess
import threading
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


def chrome_pid_exists(chrome_pid):
    with open(CSV_FILE_PATH, 'r', newline='') as csvfile:
        reader = csv.reader(csvfile)
        for row in reader:
            if row[2] == str(chrome_pid):
                return True
    return False


def save_pids_list_to_csv(file_path, chrome_driver_pid, chrome_pid_list):
    global CSV_FILE_PATH
    with open(CSV_FILE_PATH, 'a+', newline='') as csvfile:
        fieldnames = ['File Path', 'ChromeDriver PID', 'Chrome PID']
        writer = csv.DictWriter(csvfile, fieldnames=fieldnames)
        for chrome_pid in chrome_pid_list:
            if not chrome_pid_exists(chrome_pid):
                print(f"Found new PID: {chrome_pid}")
                writer.writerow(
                    {'File Path': file_path, 'ChromeDriver PID': chrome_driver_pid, 'Chrome PID': chrome_pid})


def read_pids_from_csv(file_path):
    global CSV_FILE_PATH
    chrome_driver_pid = []
    chrome_pid = []
    if not os.path.exists(CSV_FILE_PATH):
        return chrome_driver_pid, chrome_pid
    try:
        with open(CSV_FILE_PATH, mode='r') as csvfile, open(temp_file_path, mode='a+', newline='') as temp_file:
            reader = csv.reader(csvfile)
            writer = csv.writer(temp_file)
            for row in reader:
                print(f"row={row}")
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


def start_killing_processes(chrome_driver_pids, chrome_pids):
    if chrome_driver_pids:
        for pid in chrome_driver_pids:
            kill_process_by_pid(pid)
    if chrome_pids:
        for pid in chrome_pids:
            kill_process_by_pid(pid)


def KillChromeAndDriverCache(file_path):
    chrome_driver_pids, chrome_pids = read_pids_from_csv(file_path)
    t = threading.Thread(target=start_killing_processes, args=(chrome_driver_pids, chrome_pids,))
    t.start()


linked_pids = set()


def read_stop_flag():
    try:
        with open('stop_flag.txt', 'a+') as file:
            file.seek(0)
            stop_flag = bool(int(file.readline().strip()))
            return stop_flag
    except FileNotFoundError:
        return False


def write_stop_flag(stop_flag):
    with open('stop_flag.txt', 'w') as file:
        file.write(str(int(stop_flag)))


def write_flag_afer_a_minute():
    time.sleep(60)
    print("Writing stop FLAG")
    write_stop_flag(True)


def traverse_process_tree(pid):
    global linked_pids
    try:
        process = psutil.Process(pid)
        children = process.children(recursive=True)
        linked_pids.add(pid)
        for child in children:
            linked_pids.add(child.pid)
            traverse_process_tree(child.pid)
    except psutil.NoSuchProcess:
        pass


stop_event = threading.Event()


def stop_looking_processes():
    write_stop_flag(True)


def is_process_running(pid):
    return psutil.pid_exists(pid)


def keep_looking_processes(file_path, chrome_driver_pid):
    global linked_pids
    while is_process_running(chrome_driver_pid) or not read_stop_flag():
        time.sleep(15)
        print(f"looking for processes as process {chrome_driver_pid} running")
        traverse_process_tree(chrome_driver_pid)
        save_pids_list_to_csv(file_path, chrome_driver_pid, linked_pids)


def ManageChromeDriverCache(driver, file_path):
    global linked_pids, stop_event
    stop_looking_processes()
    try:
        # Get the ChromeDriver process ID
        driver_process_id = driver.service.process.pid
        chrome_driver_pid = driver_process_id
        logging.info(f"ChromeDriver Process ID: {chrome_driver_pid}")

        # Find the PID of the Chrome process opened by the WebDriver 28676
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
            #
            # def traverse_process_tree(pid):
            #     try:
            #         process = psutil.Process(pid)
            #         children = process.children(recursive=True)
            #         linked_pids.add(pid)
            #         for child in children:
            #             linked_pids.add(child.pid)
            #             traverse_process_tree(child.pid)
            #     except psutil.NoSuchProcess:
            #         pass

            traverse_process_tree(chrome_pid)
            print("Linked Process IDs:", linked_pids)
        else:
            logging.info("Chrome process not found for this WebDriver instance.")
        KillChromeAndDriverCache(file_path)
        save_pids_to_csv(file_path, chrome_driver_pid, chrome_pid)
        if linked_pids:
            save_pids_list_to_csv(file_path, chrome_driver_pid, linked_pids)
        stop_event = threading.Event()

        thread = threading.Thread(target=keep_looking_processes, args=(file_path, driver_process_id))
        write_stop_flag(True)
        thread.start()
        # thread2 = threading.Thread(target=write_flag_afer_a_minute,)
        # thread2.start()
    except Exception as e:
        print(f"Exc: {e}")
        logging.error(traceback.format_exc())
