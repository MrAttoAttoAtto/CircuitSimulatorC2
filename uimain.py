import multiprocessing

import ui.main

if __name__ == '__main__':
    multiprocessing.freeze_support()
    ui.main.run()
