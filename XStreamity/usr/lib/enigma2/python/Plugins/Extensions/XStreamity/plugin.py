#!/usr/bin/python
# -*- coding: utf-8 -*-

from . import _

from Components.config import config, ConfigSubsection, ConfigSelection, ConfigDirectory, ConfigYesNo, ConfigSelectionNumber, ConfigClock, ConfigPIN, ConfigInteger
from enigma import eTimer, getDesktop, addFont
from Plugins.Plugin import PluginDescriptor
from os.path import isdir

import os
import shutil
import sys
import twisted.python.runtime

try:
    from multiprocessing.pool import ThreadPool
    hasMultiprocessing = True
except:
    hasMultiprocessing = False

try:
    from concurrent.futures import ThreadPoolExecutor
    if twisted.python.runtime.platform.supportsThreads():
        hasConcurrent = True
    else:
        hasConcurrent = False
except:
    hasConcurrent = False

pythonFull = float(str(sys.version_info.major) + "." + str(sys.version_info.minor))
pythonVer = sys.version_info.major

isDreambox = False
if os.path.exists("/usr/bin/apt-get"):
    isDreambox = True

with open("/usr/lib/enigma2/python/Plugins/Extensions/XStreamity/version.txt", "r") as f:
    version = f.readline()

screenwidth = getDesktop(0).size()

dir_etc = "/etc/enigma2/xstreamity/"
dir_tmp = "/tmp/xstreamity/"
dir_plugins = "/usr/lib/enigma2/python/Plugins/Extensions/XStreamity/"

if screenwidth.width() == 2560:
    skin_directory = os.path.join(dir_plugins, "skin/uhd/")
elif screenwidth.width() > 1280:
    skin_directory = os.path.join(dir_plugins, "skin/fhd/")
else:
    skin_directory = os.path.join(dir_plugins, "skin/hd/")

folders = os.listdir(skin_directory)
if "common" in folders:
    folders.remove("common")

languages = [
    ("en", "English"),
    ("de", "Deutsch"),
    ("es", "Español"),
    ("fr", "Français"),
    ("it", "Italiano"),
    ("nl", "Nederlands"),
    ("tr", "Türkçe"),
    ("cs", "Český"),
    ("da", "Dansk"),
    ("hr", "Hrvatski"),
    ("hu", "Magyar"),
    ("no", "Norsk"),
    ("pl", "Polski"),
    ("pt", "Português"),
    ("ro", "Română"),
    ("ru", "Pусский"),
    ("sh", "Srpski"),
    ("sk", "Slovenčina"),
    ("fi", "suomi"),
    ("sv", "svenska"),
    ("uk", "Український"),
    ("ar", "العربية"),
    ("bg", "български език"),
    ("el", "ελληνικά"),
    ("sq", "shqip")
]


def defaultMoviePath():
    result = config.usage.default_path.value
    if not isdir(result):
        from Tools import Directories
        return Directories.defaultRecordingLocation(config.usage.default_path.value)
    return result


if not isdir(config.movielist.last_videodir.value):
    try:
        config.movielist.last_videodir.value = defaultMoviePath()
        config.movielist.last_videodir.save()
    except:
        pass

config.plugins.XStreamity = ConfigSubsection()
cfg = config.plugins.XStreamity


live_streamtype_choices = [("1", "DVB(1)"), ("4097", "IPTV(4097)")]
vod_streamtype_choices = [("4097", "IPTV(4097)")]

if os.path.exists("/usr/bin/gstplayer"):
    live_streamtype_choices.append(("5001", "GStreamer(5001)"))
    vod_streamtype_choices.append(("5001", "GStreamer(5001)"))

if os.path.exists("/usr/bin/exteplayer3"):
    live_streamtype_choices.append(("5002", "ExtePlayer(5002)"))
    vod_streamtype_choices.append(("5002", "ExtePlayer(5002)"))

if os.path.exists("/usr/bin/apt-get"):
    live_streamtype_choices.append(("8193", "DreamOS GStreamer(8193)"))
    vod_streamtype_choices.append(("8193", "DreamOS GStreamer(8193)"))

cfg.livetype = ConfigSelection(default="4097", choices=live_streamtype_choices)
cfg.vodtype = ConfigSelection(default="4097", choices=vod_streamtype_choices)
# cfg.downloadlocation = ConfigDirectory(default="/media/hdd/movie/")

cfg.downloadlocation = ConfigDirectory(default=config.movielist.last_videodir.value)
cfg.epglocation = ConfigDirectory(default="/etc/enigma2/xstreamity/epg/")
cfg.location = ConfigDirectory(default=dir_etc)
cfg.main = ConfigYesNo(default=True)
cfg.livepreview = ConfigYesNo(default=False)
cfg.stopstream = ConfigYesNo(default=False)
cfg.skin = ConfigSelection(default="default", choices=folders)
cfg.timeout = ConfigSelectionNumber(1, 20, 1, default=20, wraparound=True)
cfg.TMDB = ConfigYesNo(default=True)
cfg.TMDBLanguage = ConfigSelection(default="en", choices=languages)
cfg.catchupstart = ConfigSelectionNumber(0, 30, 1, default=0, wraparound=True)
cfg.catchupend = ConfigSelectionNumber(0, 30, 1, default=0, wraparound=True)
cfg.subs = ConfigYesNo(default=False)
cfg.skipplaylistsscreen = ConfigYesNo(default=False)
cfg.wakeup = ConfigClock(default=((9 * 60) + 9) * 60)  # 10:09
cfg.adult = ConfigYesNo(default=False)
cfg.adultpin = ConfigPIN(default=0000)
cfg.retries = ConfigSubsection()
cfg.retries.adultpin = ConfigSubsection()
cfg.retries.adultpin.tries = ConfigInteger(default=3)
cfg.retries.adultpin.time = ConfigInteger(default=3)
cfg.locationvalid = ConfigYesNo(default=True)

cfg.channelpicons = ConfigYesNo(default=True)
cfg.infobarpicons = ConfigYesNo(default=True)
cfg.channelcovers = ConfigYesNo(default=True)
cfg.infobarcovers = ConfigYesNo(default=True)

cfg.boot = ConfigYesNo(default=False)

skin_path = os.path.join(skin_directory, cfg.skin.value)
common_path = os.path.join(skin_directory, "common/")
playlists_json = os.path.join(dir_etc, "x-playlists.json")
downloads_json = os.path.join(dir_etc, "downloads2.json")
playlist_file = os.path.join(dir_etc, "playlists.txt")

location = cfg.location.getValue()
if location:
    if os.path.exists(location):
        playlist_file = os.path.join(cfg.location.value, "playlists.txt")
        cfg.locationvalid.setValue(True)
        cfg.save()
    else:
        cfg.location.setValue(dir_etc)
        cfg.locationvalid.setValue(False)
        cfg.save()

font_folder = os.path.join(dir_plugins, "fonts/")

hdr = {'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/109.0.0.0 Safari/537.36'}

# hdr = {"User-Agent": "Enigma2 - XStreamity Plugin"}

# create folder for working files
if not os.path.exists(dir_etc):
    os.makedirs(dir_etc)

# delete temporary folder and contents
if os.path.exists(dir_tmp):
    shutil.rmtree("/tmp/xstreamity")

# create temporary folder for downloaded files
if not os.path.exists(dir_tmp):
    os.makedirs(dir_tmp)

# check if playlists.txt file exists in specified location
if not os.path.isfile(playlist_file):
    with open(playlist_file, "a") as f:
        f.close()

if os.stat(playlist_file).st_size == 0:
    try:
        shutil.copyfile('/home/playlists.txt', playlist_file)
    except:
        pass

else:
    try:
        shutil.copyfile(playlist_file, '/home/playlists.txt')
    except:
        pass

# check if x-playlists.json file exists in specified location
if not os.path.isfile(playlists_json):
    with open(playlists_json, "a") as f:
        f.close()

# check if x-downloads.json file exists in specified location
if not os.path.isfile(downloads_json):
    with open(downloads_json, "a") as f:
        f.close()

# remove dodgy versions of my plugin
if os.path.isdir("/usr/lib/enigma2/python/Plugins/Extensions/XStreamityPro/"):
    try:
        shutil.rmtree("/usr/lib/enigma2/python/Plugins/Extensions/XStreamityPro/")
    except Exception as e:
        print(e)

# try and override epgimport settings
try:
    config.plugins.epgimport.import_onlybouquet.value = False
    config.plugins.epgimport.import_onlybouquet.save()
except Exception as e:
    print(e)


def main(session, **kwargs):
    from . import mainmenu
    session.open(mainmenu.XStreamity_MainMenu)
    return


def mainmenu(menu_id, **kwargs):
    if menu_id == "mainmenu":
        return [(_("XStreamity"), main, "XStreamity", 50)]
    else:
        return []


def extensionsmenu(session, **kwargs):
    from . import mainmenu
    session.open(mainmenu.XStreamity_MainMenu)
    return


autoStartTimer = None


class AutoStartTimer:
    def __init__(self, session):
        self.session = session
        self.timer = eTimer()
        try:
            self.timer_conn = self.timer.timeout.connect(self.onTimer)
        except:
            self.timer.callback.append(self.onTimer)
        self.update()

    def getWakeTime(self):
        import time
        clock = cfg.wakeup.value
        nowt = time.time()
        now = time.localtime(nowt)
        return int(time.mktime((now.tm_year, now.tm_mon, now.tm_mday, clock[0], clock[1], 0, now.tm_wday, now.tm_yday, now.tm_isdst)))

    def update(self, atLeast=0):
        import time
        self.timer.stop()
        wake = self.getWakeTime()
        nowtime = time.time()
        if wake > 0:
            if wake < nowtime + atLeast:
                # Tomorrow.
                wake += 24 * 3600
            next = wake - int(nowtime)
            if next > 3600:
                next = 3600
            if next <= 0:
                next = 60
            self.timer.startLongTimer(next)
        else:
            wake = -1
        return wake

    def onTimer(self):
        import time
        self.timer.stop()
        now = int(time.time())
        wake = self.getWakeTime()
        atLeast = 0
        if abs(wake - now) < 60:
            self.runUpdate()
            atLeast = 60
        self.update(atLeast)

    def runUpdate(self):
        print("\n *********** Updating XStreamity EPG ************ \n")
        from . import update
        update.XStreamity_Update()


def autostart(reason, session=None, **kwargs):
    global autoStartTimer
    if reason == 0:
        if session is not None:
            if autoStartTimer is None:
                autoStartTimer = AutoStartTimer(session)
    return


# auto boot start
glb_session = None
glb_startDelay = None


class StartDelay:
    def __init__(self):
        self.timerboot = eTimer()

    def start(self):
        delay = 2000

        try:
            self.timer_conn = self.timerboot.timeout.connect(self.query)
        except:
            self.timerboot.callback.append(self.query)

        self.timerboot.start(delay, True)

    def query(self):
        from . import playlists
        glb_session.open(playlists.XStreamity_Playlists)
        return


def bootstart(reason, **kwargs):
    print("*** bootstart ***")
    global glb_session
    global glb_startDelay
    if reason == 0 and "session" in kwargs:
        glb_session = kwargs["session"]
        glb_startDelay = StartDelay()
        glb_startDelay.start()


def Plugins(**kwargs):
    addFont(os.path.join(font_folder, "m-plus-rounded-1c-regular.ttf"), "xstreamityregular", 100, 0)
    addFont(os.path.join(font_folder, "m-plus-rounded-1c-medium.ttf"), "xstreamitybold", 100, 0)
    addFont(os.path.join(font_folder, "slyk-medium.ttf"), "slykregular", 100, 0)
    addFont(os.path.join(font_folder, "slyk-bold.ttf"), "slykbold", 100, 0)

    iconFile = "icons/plugin-icon_sd.png"
    if screenwidth.width() > 1280:
        iconFile = "icons/plugin-icon.png"
    description = (_("IPTV Xtream Codes playlists player by KiddaC"))
    pluginname = (_("XStreamity"))

    main_menu = PluginDescriptor(name=pluginname, description=description, where=PluginDescriptor.WHERE_MENU, fnc=mainmenu, needsRestart=True)

    extensions_menu = PluginDescriptor(name=pluginname, description=description, where=PluginDescriptor.WHERE_EXTENSIONSMENU, fnc=extensionsmenu, needsRestart=True)

    boot_start = PluginDescriptor(name=pluginname, description=description, where=[PluginDescriptor.WHERE_AUTOSTART, PluginDescriptor.WHERE_SESSIONSTART], fnc=bootstart, needsRestart=True)

    result = [PluginDescriptor(name=pluginname, description=description, where=[PluginDescriptor.WHERE_AUTOSTART, PluginDescriptor.WHERE_SESSIONSTART], fnc=autostart),
              PluginDescriptor(name=pluginname, description=description, where=PluginDescriptor.WHERE_PLUGINMENU, icon=iconFile, fnc=main)]

    result.append(extensions_menu)

    if cfg.main.getValue():
        result.append(main_menu)

    if cfg.boot.getValue():
        result.append(boot_start)

    return result
