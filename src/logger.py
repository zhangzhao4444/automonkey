import logging,os
#import ctypes

STD_INPUT_HANDLE = -10
STD_OUTPUT_HANDLE= -11
STD_ERROR_HANDLE = -12
FOREGROUND_WHITE = 0x0007
FOREGROUND_BLUE = 0x01 # text color contains blue.
FOREGROUND_GREEN= 0x02 # text color contains green.
FOREGROUND_RED  = 0x04 # text color contains red.
FOREGROUND_INTENSITY = 0x08 # text color is intensified.
FOREGROUND_YELLOW = FOREGROUND_RED | FOREGROUND_GREEN

# def set_color(color, handle=ctypes.windll.kernel32.GetStdHandle(STD_OUTPUT_HANDLE)):
#     bool = ctypes.windll.kernel32.SetConsoleTextAttribute(handle, color)
#     return bool

class Logger:
    def __init__(self, path):
        self.logger = logging.getLogger(path)
        self.logger.setLevel(logging.DEBUG)
        #fmt = logging.Formatter('[%(asctime)s] [%(levelname)s] %(message)s', '%Y-%m-%d %H:%M:%S')
        fmt = logging.Formatter('[%(asctime)s] [%(levelname)s] %(message)s')
        sh = logging.StreamHandler()
        sh.setFormatter(fmt)
        self.logger.addHandler(sh)
        fh = logging.FileHandler(path)
        fh.setFormatter(fmt)
        self.logger.addHandler(fh)
        self.case_result = True

    def debug(self, *data):
        data = len(data) == 1 and data[0] or ' '.join(map(str, data))
        self.info(data, logging.DEBUG, FOREGROUND_WHITE|FOREGROUND_INTENSITY)

    def error(self, data, color=FOREGROUND_RED):
        self.info(data, logging.ERROR, color|FOREGROUND_INTENSITY)
        self.case_result = False

    def fatal(self, data, color = FOREGROUND_GREEN):
        self.info(data, logging.FATAL)

    def info(self, data, level = logging.INFO, color = FOREGROUND_GREEN):
        #set_color(color|FOREGROUND_INTENSITY)
        try:
            data = data.encode('gbk','replace')
            data = data.decode('gbk')
            self.logger.log(level, data)
        except Exception as e:
            #print(e)
            self.logger.log(level, data)
            pass
        #set_color(FOREGROUND_WHITE)

    def warn(self, data, color=FOREGROUND_YELLOW):
        self.info(data, logging.WARN, color|FOREGROUND_INTENSITY)

logobj = Logger('%s%slog%sdebug.log'%(os.path.split(os.path.realpath(__file__))[0],os.path.sep,os.path.sep))

def testlog():
    logobj.debug('张钊test %s' % '20170126')

if __name__ == "__main__":
    testlog()