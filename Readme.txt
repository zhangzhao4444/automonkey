1.安装python3.6
  设置python环境变量
  path 增加 C:\Users\zhangzhao\AppData\Local\Programs\Python\Python36
            C:\Users\zhangzhao\AppData\Local\Programs\Python\Python36\Scripts
2.安装pycharm（用于开发 调试，仅使用可略过）
  填pycharm激活码(google)

3.安装py库
  1)pip install lxml
  2)pip install requests
  3)pip install selenium
  4)pip install appium-python-client
  5)pip install pyyaml
  6)pip install xlsxwriter
  7)pip install wheel
down http://www.lfd.uci.edu/~gohlke/pythonlibs/#lxml
scipy-0.18.1-cp34-cp34m-win_amd64.whl
numpy-1.11.3+mkl-cp34-cp34m-win_amd64.whl
pyparsing-2.1.10-py2.py3-none-any.whl
python_dateutil-2.6.0-py2.py3-none-any.whl
pytz-2016.10-py2.py3-none-any.whl
matplotlib-2.0.0rc2-cp34-cp34m-win_amd64.whl
pip install xxx.whl
   8)easy_install Pillow

4.下载androidsdk 
  设置$ANDROID_HOME 环境变量
  ANDROID_HOME 设为 D:\android-sdk

5.下载最新的automonkey

6.下载安装nodejs

7.下载安装appium
  修正appiumdriver.py中startappiumdriver安装目录
如 cmd = 'c:\\program files xxx'

8.安装jdk,配置环境变量
JAVA_HOME C:\Program Files\Java\jdk1.8.0_121
CLASSPATH C:\Program Files\Java\jdk1.8.0_121\lib\dt.jar;C:\Program Files\Java\jdk1.8.0_121\lib\tools.jar
PATH 增加 C:\Program Files\Java\jdk1.8.0_121\bin

9.运行appium-doctor检测appium运行环境
C:\Users\zhangzhao>appium-doctor
Running Android Checks
? ANDROID_HOME is set to "D:\android-sdk"
? JAVA_HOME is set to "C:\Program Files\Java\jdk1.8.0_121."
? ADB exists at D:\android-sdk\platform-tools\adb.exe
? Android exists at D:\android-sdk\tools\android.bat
? Emulator exists at D:\android-sdk\tools\emulator.exe
? Android Checks were successful.
? All Checks were successful

运行：
执行adb devices 获取uuid
进度automonkey目录
python monkey.py -a conf\pandalive.apk -c conf\panda.yml -p android -i X2P0215518002631 -u 4723
-a apk路径
-c 遍历规则文件
-p 平台android/ios
-i 设备uuid
-u appium起始端口号