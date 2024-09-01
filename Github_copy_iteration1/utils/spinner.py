from tqdm import tqdm
import time

# // Loading bar
def loading_bar(interval):
    for i in tqdm(range(10)):
        time.sleep(interval) #how fast to load the bar, jumps in x seconds